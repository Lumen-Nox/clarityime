package com.coraz.clarityime

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

/** Talks to `clarityime serve` on device (127.0.0.1:17800) when core is running. */
object ClarifyClient {
    private const val BASE = "http://127.0.0.1:17800"

    /** Set from Application / IME service so token can be read from SharedPreferences. */
    @Volatile
    var appContext: android.content.Context? = null

    data class ContactRow(
        val id: String,
        val name: String,
        val relationship: String,
        val styleNotes: String = "",
        val comprehensionNotes: String = "",
        val ceromeSummary: String = "",
    )

    fun health(): Boolean = try {
        val c = URL("$BASE/v1/health").openConnection() as HttpURLConnection
        c.connectTimeout = 400
        c.readTimeout = 400
        c.inputStream.bufferedReader().readText().contains("ok")
    } catch (_: Exception) {
        false
    }

    fun listContacts(): List<ContactRow> {
        if (!health()) return emptyList()
        return try {
            val c = URL("$BASE/v1/contacts").openConnection() as HttpURLConnection
            c.connectTimeout = 800
            c.readTimeout = 800
            val resp = c.inputStream.bufferedReader().readText()
            val arr = JSONObject(resp).getJSONArray("contacts")
            (0 until arr.length()).map { i ->
                val o = arr.getJSONObject(i)
                ContactRow(
                    id = o.get("id").toString(),
                    name = o.getString("name"),
                    relationship = o.optString("relationship", ""),
                    styleNotes = o.optString("style_notes", ""),
                    comprehensionNotes = o.optString("comprehension_notes", ""),
                    ceromeSummary = summarizeCerome(o.optJSONObject("cerome")),
                )
            }
        } catch (_: Exception) {
            emptyList()
        }
    }

    fun saveContact(
        name: String,
        relationship: String,
        styleNotes: String,
        comprehensionNotes: String,
        ceromeL2: Map<String, Double>? = null,
        ceromeMood: String? = null,
    ): Boolean {
        if (!health()) return false
        return try {
            val cerome = ceromeL2?.let { l2 ->
                JSONObject()
                    .put("L2", JSONObject().apply {
                        l2.forEach { (k, v) -> put(k, v) }
                    })
                    .put("L4", JSONObject().put("formality", if (relationship in listOf("老师", "教授", "上级", "老板", "mentor")) 0.7 else 0.45))
                    .put("L5", JSONObject().put("label", ceromeMood ?: "steady"))
            } ?: ceromeFromLegacy(styleNotes, comprehensionNotes, relationship)
            val body = JSONObject()
                .put("name", name)
                .put("relationship", relationship)
                .put("style_notes", styleNotes)
                .put("comprehension_notes", comprehensionNotes)
                .put("comprehension", comprehensionNotes)
                .put("cerome", cerome)
            postJson("$BASE/v1/contacts", body.toString()) != null
        } catch (_: Exception) {
            false
        }
    }

    data class ConsentState(
        val cloudSync: Boolean = false,
        val aggregateResearch: Boolean = false,
    )

    fun getConsent(): ConsentState? {
        if (!health()) return null
        return try {
            val c = URL("$BASE/v1/consent").openConnection() as HttpURLConnection
            c.connectTimeout = 800
            c.readTimeout = 800
            val resp = c.inputStream.bufferedReader().readText()
            val o = JSONObject(resp)
            ConsentState(
                cloudSync = o.optBoolean("cloud_sync", false),
                aggregateResearch = o.optBoolean("aggregate_research", false),
            )
        } catch (_: Exception) {
            null
        }
    }

    fun saveConsent(cloudSync: Boolean, aggregateResearch: Boolean): Boolean {
        if (!health()) return false
        return try {
            val body = JSONObject()
                .put("cloud_sync", cloudSync)
                .put("aggregate_research", aggregateResearch)
            postJson("$BASE/v1/consent", body.toString()) != null
        } catch (_: Exception) {
            false
        }
    }

    fun deleteContact(name: String): Boolean {
        if (!health()) return false
        return try {
            val encoded = URLEncoder.encode(name, Charsets.UTF_8.name())
            val c = URL("$BASE/v1/contacts?name=$encoded").openConnection() as HttpURLConnection
            c.requestMethod = "DELETE"
            applyAuth(c)
            c.connectTimeout = 800
            c.readTimeout = 800
            c.responseCode in 200..299
        } catch (_: Exception) {
            false
        }
    }

    fun exportContactBundle(name: String): String? {
        if (!health()) return null
        return try {
            val encoded = URLEncoder.encode(name, Charsets.UTF_8.name())
            val c = URL("$BASE/v1/contacts/export?name=$encoded").openConnection() as HttpURLConnection
            c.connectTimeout = 800
            c.readTimeout = 800
            if (c.responseCode !in 200..299) return null
            c.inputStream.bufferedReader().readText()
        } catch (_: Exception) {
            null
        }
    }

    fun importContactBundle(json: String): Boolean {
        if (!health()) return false
        return postJson("$BASE/v1/contacts/import", json) != null
    }

    fun candidates(text: String, mode: String, contact: String?, nbest: List<String>? = null): List<Pair<String, String>> {
        if (!health()) return ClarifyRules.candidates(text, mode)
        return try {
            val body = JSONObject()
                .put("text", text)
                .put("mode", mode)
            if (contact != null) body.put("contact", contact)
            if (!nbest.isNullOrEmpty()) {
                val arr = org.json.JSONArray()
                nbest.forEach { arr.put(it) }
                body.put("nbest", arr)
            }
            val resp = postJson("$BASE/v1/candidates", body.toString()) ?: return ClarifyRules.candidates(text, mode)
            val arr = JSONObject(resp).getJSONArray("candidates")
            (0 until arr.length()).map { i ->
                val o = arr.getJSONObject(i)
                o.getString("text") to o.getString("label")
            }
        } catch (_: Exception) {
            ClarifyRules.candidates(text, mode)
        }
    }

    fun feedback(
        raw: String,
        preferred: String,
        nbest: List<String>? = null,
        candidates: List<Pair<String, String>>? = null,
        mode: String? = null,
    ): String? {
        return try {
            val body = JSONObject()
                .put("raw", raw)
                .put("preferred", preferred)
            if (!nbest.isNullOrEmpty()) {
                val arr = org.json.JSONArray()
                nbest.forEach { arr.put(it) }
                body.put("nbest", arr)
            }
            if (!candidates.isNullOrEmpty()) {
                val arr = org.json.JSONArray()
                candidates.forEach { (text, label) ->
                    arr.put(JSONObject().put("text", text).put("label", label))
                }
                body.put("candidates", arr)
            }
            if (!mode.isNullOrEmpty()) body.put("mode", mode)
            val resp = postJson("$BASE/v1/feedback", body.toString()) ?: return null
            JSONObject(resp).optString("bundle_url").takeIf { it.isNotEmpty() }
        } catch (_: Exception) {
            null
        }
    }

    private fun postJson(url: String, json: String): String? {
        val c = URL(url).openConnection() as HttpURLConnection
        c.requestMethod = "POST"
        c.doOutput = true
        c.connectTimeout = 800
        c.readTimeout = 800
        c.setRequestProperty("Content-Type", "application/json")
        applyAuth(c)
        c.outputStream.use { it.write(json.toByteArray()) }
        if (c.responseCode !in 200..299) return null
        return c.inputStream.bufferedReader().readText()
    }

    private fun applyAuth(c: HttpURLConnection) {
        LocalApiAuth.token(appContext)?.let { c.setRequestProperty("X-ClarityIME-Token", it) }
    }

    private fun summarizeCerome(cerome: org.json.JSONObject?): String {
        if (cerome == null) return ""
        val l5 = cerome.optJSONObject("L5")?.optString("label")?.takeIf { it.isNotEmpty() }
        val l2 = cerome.optJSONObject("L2") ?: return l5 ?: ""
        val ranked = listOf("clarity", "warmth", "efficiency", "precision", "humor")
            .mapNotNull { key ->
                if (!l2.has(key)) null else key to l2.optDouble(key, 0.0)
            }
            .sortedByDescending { it.second }
            .take(2)
            .map { it.first }
        return listOfNotNull(l5, ranked.joinToString(",").takeIf { it.isNotEmpty() })
            .joinToString(" · ")
    }

    /** Mirror server-side Cerome infer for explicit POST tags. */
    private fun ceromeFromLegacy(
        style: String,
        comprehension: String,
        relationship: String,
    ): JSONObject {
        val formalRel = relationship in listOf("老师", "教授", "上级", "老板", "mentor")
        val warmth = if (style.contains("温和")) 0.65 else 0.45
        val efficiency = if (style.contains("简短") || style.contains("口语")) 0.7 else 0.5
        val precision = if (style.contains("精确")) 0.7 else 0.5
        val clarity = if (comprehension.isNotEmpty()) 0.75 else 0.65
        val l2 = JSONObject()
            .put("clarity", clarity)
            .put("warmth", warmth)
            .put("efficiency", efficiency)
            .put("precision", precision)
            .put("humor", 0.35)
        val l4 = JSONObject().put("formality", if (formalRel) 0.7 else 0.45)
        return JSONObject()
            .put("L2", l2)
            .put("L4", l4)
            .put("L5", JSONObject().put("label", "steady"))
    }
}
