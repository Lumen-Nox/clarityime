package com.coraz.clarityime

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity

class SettingsActivity : AppCompatActivity() {
    private val modeValues = listOf("default", "structured", "contact")
    private val modeLabels = listOf("通用清晰化", "结构化", "联系人")
    private val asrLanguages = listOf("auto", "zh", "en", "ja", "ko")
    private var contactIds: List<String> = emptyList()
    private var contacts: List<ClarifyClient.ContactRow> = emptyList()
    private var pendingExportName: String? = null

    private val importLauncher = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri == null) return@registerForActivityResult
        val json = readUriText(uri)
        if (json.isNullOrBlank()) {
            Toast.makeText(this, "Could not read file", Toast.LENGTH_SHORT).show()
            return@registerForActivityResult
        }
        Thread {
            val ok = ClarifyClient.importContactBundle(json)
            runOnUiThread {
                if (ok) {
                    Toast.makeText(this, "Contact imported", Toast.LENGTH_SHORT).show()
                    refreshCore()
                } else {
                    Toast.makeText(this, "Import failed — is core running?", Toast.LENGTH_SHORT).show()
                }
            }
        }.start()
    }

    private val exportLauncher = registerForActivityResult(ActivityResultContracts.CreateDocument("application/json")) { uri ->
        val name = pendingExportName ?: return@registerForActivityResult
        pendingExportName = null
        if (uri == null) return@registerForActivityResult
        Thread {
            val json = ClarifyClient.exportContactBundle(name)
            runOnUiThread {
                if (json.isNullOrBlank()) {
                    Toast.makeText(this, "Export failed — is core running?", Toast.LENGTH_SHORT).show()
                    return@runOnUiThread
                }
                try {
                    contentResolver.openOutputStream(uri)?.use { it.write(json.toByteArray()) }
                    Toast.makeText(this, "Exported $name", Toast.LENGTH_SHORT).show()
                } catch (_: Exception) {
                    Toast.makeText(this, "Could not write file", Toast.LENGTH_SHORT).show()
                }
            }
        }.start()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        ClarifyClient.appContext = applicationContext
        setContentView(R.layout.settings)

        val prefs = ClarityPrefs.prefs(this)
        val status = findViewById<TextView>(R.id.core_status)
        val spinnerMode = findViewById<Spinner>(R.id.spinner_mode)
        val spinnerContact = findViewById<Spinner>(R.id.spinner_contact)
        val spinnerAsrLang = findViewById<Spinner>(R.id.spinner_asr_lang)
        val contactListContainer = findViewById<LinearLayout>(R.id.contact_list_container)
        val editContactName = findViewById<EditText>(R.id.edit_contact_name)
        val editContactRelation = findViewById<EditText>(R.id.edit_contact_relation)
        val editContactStyle = findViewById<EditText>(R.id.edit_contact_style)
        val editContactComprehension = findViewById<EditText>(R.id.edit_contact_comprehension)
        val seekClarity = findViewById<android.widget.SeekBar>(R.id.seek_cerome_clarity)
        val seekWarmth = findViewById<android.widget.SeekBar>(R.id.seek_cerome_warmth)
        val seekEfficiency = findViewById<android.widget.SeekBar>(R.id.seek_cerome_efficiency)
        val seekPrecision = findViewById<android.widget.SeekBar>(R.id.seek_cerome_precision)
        val seekHumor = findViewById<android.widget.SeekBar>(R.id.seek_cerome_humor)
        val spinnerCeromeMood = findViewById<Spinner>(R.id.spinner_cerome_mood)
        val editApiToken = findViewById<EditText>(R.id.edit_api_token)
        val checkCloudSync = findViewById<CheckBox>(R.id.check_cloud_sync)
        val checkAggregate = findViewById<CheckBox>(R.id.check_aggregate_research)
        val checkAutoApplyTop = findViewById<CheckBox>(R.id.check_auto_apply_top)

        spinnerMode.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, modeLabels)
        spinnerAsrLang.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, asrLanguages)
        spinnerCeromeMood.adapter = ArrayAdapter(
            this,
            android.R.layout.simple_spinner_dropdown_item,
            listOf("steady", "stressed", "upbeat", "tired", "focused"),
        )
        spinnerCeromeMood.setSelection(0)
        editApiToken.setText(prefs.getString(ClarityPrefs.KEY_LOCAL_API_TOKEN, "") ?: "")

        val savedMode = ClarifyRules.normalizeMode(
            prefs.getString(ClarityPrefs.KEY_AUDIENCE_MODE, "default") ?: "default"
        )
        spinnerMode.setSelection(modeValues.indexOf(savedMode).coerceAtLeast(0))

        val savedLang = prefs.getString(ClarityPrefs.KEY_ASR_LANGUAGE, "auto") ?: "auto"
        val langIdx = asrLanguages.indexOf(savedLang).let { if (it >= 0) it else 0 }
        spinnerAsrLang.setSelection(langIdx)
        checkAutoApplyTop.isChecked = prefs.getBoolean(ClarityPrefs.KEY_AUTO_APPLY_TOP, false)

        fun updateContactSpinner(savedContact: String) {
            val labels = mutableListOf("(none)")
            contactIds = mutableListOf("")
            contacts.forEach { c ->
                contactIds.add(c.name)
                labels.add(
                    if (c.relationship.isNotEmpty()) "${c.name} (${c.relationship})"
                    else c.name
                )
            }
            spinnerContact.adapter = ArrayAdapter(
                this,
                android.R.layout.simple_spinner_dropdown_item,
                labels,
            )
            val idx = contactIds.indexOf(savedContact).coerceAtLeast(0)
            spinnerContact.setSelection(idx)
        }

        fun renderContactList() {
            contactListContainer.removeAllViews()
            if (contacts.isEmpty()) {
                val empty = TextView(this).apply {
                    text = "No contacts yet — add one below when core is running."
                    setTextColor(0xFF666666.toInt())
                    textSize = 12f
                }
                contactListContainer.addView(empty)
                return
            }
            val inflater = LayoutInflater.from(this)
            contacts.forEach { contact ->
                val row = inflater.inflate(R.layout.contact_row, contactListContainer, false)
                row.findViewById<TextView>(R.id.contact_name).text = contact.name
                val parts = listOfNotNull(
                    contact.relationship.takeIf { it.isNotEmpty() },
                    contact.styleNotes.takeIf { it.isNotEmpty() },
                    contact.comprehensionNotes.takeIf { it.isNotEmpty() },
                    contact.ceromeSummary.takeIf { it.isNotEmpty() }?.let { "cerome: $it" },
                )
                row.findViewById<TextView>(R.id.contact_details).text =
                    if (parts.isEmpty()) "(no details)" else parts.joinToString(" · ")
                row.findViewById<Button>(R.id.btn_delete_contact).setOnClickListener {
                    AlertDialog.Builder(this)
                        .setTitle("Delete contact")
                        .setMessage("Delete ${contact.name}?")
                        .setPositiveButton("Delete") { _, _ ->
                            Thread {
                                val ok = ClarifyClient.deleteContact(contact.name)
                                runOnUiThread {
                                    if (ok) {
                                        Toast.makeText(this, "Deleted ${contact.name}", Toast.LENGTH_SHORT).show()
                                        refreshCore()
                                    } else {
                                        Toast.makeText(this, "Delete failed — is core running?", Toast.LENGTH_SHORT).show()
                                    }
                                }
                            }.start()
                        }
                        .setNegativeButton("Cancel", null)
                        .show()
                }
                contactListContainer.addView(row)
            }
        }

        fun refreshCore() {
            Thread {
                val ok = ClarifyClient.health()
                val loaded = if (ok) ClarifyClient.listContacts() else emptyList()
                val consent = if (ok) ClarifyClient.getConsent() else null
                runOnUiThread {
                    contacts = loaded
                    status.text = if (ok) {
                        "Core: connected (:17800) · ${contacts.size} contacts"
                    } else {
                        "Core: offline — using offline rules. Run `clarityime serve` in Termux optional."
                    }
                    consent?.let {
                        checkCloudSync.isChecked = it.cloudSync
                        checkAggregate.isChecked = it.aggregateResearch
                    } ?: run {
                        checkCloudSync.isChecked = prefs.getBoolean(ClarityPrefs.KEY_CLOUD_SYNC, false)
                        checkAggregate.isChecked = prefs.getBoolean(ClarityPrefs.KEY_AGGREGATE_RESEARCH, false)
                    }
                    val savedContact = prefs.getString(ClarityPrefs.KEY_DEFAULT_CONTACT, "") ?: ""
                    updateContactSpinner(savedContact)
                    renderContactList()
                }
            }.start()
        }

        findViewById<Button>(R.id.btn_refresh_core).setOnClickListener { refreshCore() }
        findViewById<Button>(R.id.btn_show_onboarding).setOnClickListener {
            startActivity(Intent(this, OnboardingActivity::class.java))
        }
        findViewById<Button>(R.id.btn_export_contact).setOnClickListener { exportSelectedContact() }
        findViewById<Button>(R.id.btn_import_contact).setOnClickListener {
            importLauncher.launch(arrayOf("application/json", "text/plain", "*/*"))
        }
        refreshCore()

        findViewById<Button>(R.id.btn_add_contact).setOnClickListener {
            val name = editContactName.text.toString().trim()
            if (name.isEmpty()) {
                Toast.makeText(this, "Name is required", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            val relation = editContactRelation.text.toString().trim()
            val style = editContactStyle.text.toString().trim()
            val comprehension = editContactComprehension.text.toString().trim()
            findViewById<Button>(R.id.btn_add_contact).isEnabled = false
            Thread {
                val ok = ClarifyClient.saveContact(
                    name,
                    relation,
                    style,
                    comprehension,
                    ceromeL2 = mapOf(
                        "clarity" to seekClarity.progress / 100.0,
                        "warmth" to seekWarmth.progress / 100.0,
                        "efficiency" to seekEfficiency.progress / 100.0,
                        "precision" to seekPrecision.progress / 100.0,
                        "humor" to seekHumor.progress / 100.0,
                    ),
                    ceromeMood = spinnerCeromeMood.selectedItem?.toString(),
                )
                runOnUiThread {
                    findViewById<Button>(R.id.btn_add_contact).isEnabled = true
                    if (ok) {
                        Toast.makeText(this, "Saved $name", Toast.LENGTH_SHORT).show()
                        editContactName.text.clear()
                        editContactRelation.text.clear()
                        editContactStyle.text.clear()
                        editContactComprehension.text.clear()
                        refreshCore()
                    } else {
                        Toast.makeText(this, "Save failed — is core running?", Toast.LENGTH_SHORT).show()
                    }
                }
            }.start()
        }

        findViewById<Button>(R.id.btn_save).setOnClickListener {
            val mode = modeValues[spinnerMode.selectedItemPosition]
            val contact = contactIds.getOrNull(spinnerContact.selectedItemPosition)?.takeIf { it.isNotEmpty() }
            val lang = asrLanguages[spinnerAsrLang.selectedItemPosition]
            val cloudSync = checkCloudSync.isChecked
            val aggregate = checkAggregate.isChecked
            prefs.edit()
                .putString(ClarityPrefs.KEY_AUDIENCE_MODE, mode)
                .putString(ClarityPrefs.KEY_DEFAULT_CONTACT, contact)
                .putString(ClarityPrefs.KEY_ASR_LANGUAGE, lang)
                .putBoolean(ClarityPrefs.KEY_CLOUD_SYNC, cloudSync)
                .putBoolean(ClarityPrefs.KEY_AGGREGATE_RESEARCH, aggregate)
                .putBoolean(ClarityPrefs.KEY_AUTO_APPLY_TOP, checkAutoApplyTop.isChecked)
                .putString(ClarityPrefs.KEY_LOCAL_API_TOKEN, editApiToken.text.toString().trim())
                .apply()
            Thread {
                val consentOk = ClarifyClient.saveConsent(cloudSync, aggregate)
                runOnUiThread {
                    val msg = if (consentOk || !ClarifyClient.health()) {
                        "Saved · mode=$mode"
                    } else {
                        "Saved prefs · consent sync failed (core offline?)"
                    }
                    Toast.makeText(this, msg, Toast.LENGTH_SHORT).show()
                    finish()
                }
            }.start()
        }
    }

    private fun exportSelectedContact() {
        val idx = findViewById<Spinner>(R.id.spinner_contact).selectedItemPosition
        val name = contactIds.getOrNull(idx)?.takeIf { it.isNotEmpty() }
        if (name.isNullOrEmpty()) {
            Toast.makeText(this, "Pick a contact to export", Toast.LENGTH_SHORT).show()
            return
        }
        pendingExportName = name
        exportLauncher.launch("$name-clarityime-contact.json")
    }

    private fun readUriText(uri: Uri): String? = try {
        contentResolver.openInputStream(uri)?.bufferedReader()?.use { it.readText() }
    } catch (_: Exception) {
        null
    }
}
