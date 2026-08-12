package com.coraz.clarityime

/**
 * Offline clarification — mirrors Python `local_rules.py` (deterministic, no LLM).
 * Preserve detail & tone; never summarize.
 */
object ClarifyRules {
    private val fillers = listOf("嗯", "啊", "呃", "那个", "就是", "然后", "你知道", "怎么说呢", "对对对")
    private val questionMarkers = listOf("吗", "么", "是不是", "能不能", "什么", "怎么", "哪", "谁")
    private val clauseBreakers = listOf("因为", "但是", "所以", "而且", "不过", "然而")
    private val formalRels = setOf("老师", "教授", "上级", "老板")

    fun normalizeMode(mode: String): String = when (mode.trim().lowercase()) {
        "ai" -> "structured"
        else -> mode.trim().lowercase()
    }

    fun clarifyDefault(text: String): String {
        var out = stripFillers(text)
        out = insertClauseBreaks(out)
        out = punctuate(out)
        return out.trim()
    }

    fun clarifyForStructured(text: String): String {
        val out = clarifyDefault(text)
        val sents = out.split(Regex("(?<=[。！？])\\s*")).map { it.trim() }.filter { it.isNotEmpty() }
        return if (sents.size >= 2) sents.joinToString("\n\n") else out
    }

    fun clarifyForContact(text: String, relationship: String = "", style: String = ""): String {
        var out = clarifyDefault(text)
        val warm = style.contains("温和")
        val formal = formalRels.contains(relationship) || style.contains("正式")
        if (formal) {
            out = out.replace("你", "您")
            if (relationship in setOf("老师", "教授") && !out.startsWith("老师") && questionMarkers.any { out.contains(it) }) {
                out = "老师，$out"
            }
        }
        if (warm && (out.contains("去不了") || out.contains("晚一天")) && !out.contains("不好意思")) {
            out = "不好意思，$out"
        }
        return punctuate(out.trimEnd('。', '！', '？'))
    }

    fun candidates(text: String, mode: String): List<Pair<String, String>> {
        val m = normalizeMode(mode)
        val primary = when (m) {
            "structured" -> clarifyForStructured(text)
            else -> clarifyDefault(text)
        }
        return listOf(primary to "standard")
    }

    private fun stripFillers(text: String): String {
        var out = text.trim()
        for (f in fillers) {
            if (out.startsWith(f)) out = out.removePrefix(f)
            out = out.replace(Regex("${Regex.escape(f)}+"), "")
        }
        out = out.replace(Regex("^那个啥[，,、\\s]+"), "")
        out = out.replace(Regex("^我跟你说啊?[，,、\\s]+"), "")
        return out.replace(Regex("\\s+"), " ").trim()
    }

    private fun insertClauseBreaks(text: String): String {
        var out = text
        for (w in clauseBreakers) {
            out = out.replace(Regex("(?<=[^，,；;])$w"), "，$w")
        }
        out = out.replace("，然后", "，")
        return out
    }

    private fun punctuate(text: String): String {
        if (text.isEmpty()) return text
        if (text.last() in "。！？") return text
        return text + if (questionMarkers.any { text.contains(it) }) "？" else "。"
    }
}
