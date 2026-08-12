package com.coraz.clarityime

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.inputmethodservice.InputMethodService
import android.inputmethodservice.Keyboard
import android.inputmethodservice.KeyboardView
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.inputmethod.InputConnection
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.recyclerview.widget.RecyclerView
import androidx.viewpager2.widget.ViewPager2

/**
 * ClarityIME — voice clarity INSIDE the keyboard (InputMethodService).
 */
class ClarityInputMethodService : InputMethodService(), RecognitionListener,
    KeyboardView.OnKeyboardActionListener {

    private var speech: SpeechRecognizer? = null
    private var lastRaw: String = ""
    private var lastNbest: List<String> = emptyList()
    private var lastCandidates: List<Pair<String, String>> = emptyList()
    private var mode: String = "default"
    private var contact: String? = null

    private var candidateStrip: LinearLayout? = null
    private var candidateStatusRow: View? = null
    private var candidatePagerRow: View? = null
    private var candidateRawLabel: TextView? = null
    private var candidatePager: ViewPager2? = null
    private var btnNoneFit: Button? = null
    private var keyboardView: KeyboardView? = null
    private var btnMode: Button? = null

    override fun onCreate() {
        super.onCreate()
        ClarifyClient.appContext = applicationContext
        reloadPrefs()
        if (SpeechRecognizer.isRecognitionAvailable(this)) {
            speech = SpeechRecognizer.createSpeechRecognizer(this).also {
                it.setRecognitionListener(this)
            }
        }
    }

    override fun onCreateInputView(): View {
        reloadPrefs()
        val root = layoutInflater.inflate(R.layout.keyboard, null)
        candidateStrip = root.findViewById(R.id.candidate_strip)
        candidateStatusRow = root.findViewById(R.id.candidate_status_row)
        candidatePagerRow = root.findViewById(R.id.candidate_pager_row)
        candidateRawLabel = root.findViewById(R.id.candidate_raw_label)
        candidatePager = root.findViewById(R.id.candidate_pager)
        btnNoneFit = root.findViewById(R.id.btn_none_fit)

        keyboardView = root.findViewById<KeyboardView>(R.id.keyboard_view).also {
            it.keyboard = Keyboard(this, R.xml.keyboard_layout)
            it.setOnKeyboardActionListener(this)
            it.isPreviewEnabled = false
        }

        root.findViewById<Button>(R.id.btn_mic).setOnClickListener { startVoice() }
        btnMode = root.findViewById(R.id.btn_mode)
        btnMode?.setOnClickListener { cycleMode() }
        root.findViewById<Button>(R.id.btn_settings).setOnClickListener {
            startActivity(
                Intent(this, SettingsActivity::class.java)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            )
        }

        setupNoneFitButton()
        maybeLaunchOnboarding()
        updateModeChip()
        return root
    }

    override fun onStartInputView(info: android.view.inputmethod.EditorInfo?, restarting: Boolean) {
        super.onStartInputView(info, restarting)
        maybeLaunchOnboarding()
    }

    private fun maybeLaunchOnboarding() {
        if (onboardingLaunchedThisSession) return
        if (ClarityPrefs.isOnboardingDone(this)) return
        onboardingLaunchedThisSession = true
        startActivity(
            Intent(this, OnboardingActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        )
    }

    private fun reloadPrefs() {
        val prefs = ClarityPrefs.prefs(this)
        mode = ClarifyRules.normalizeMode(
            prefs.getString(ClarityPrefs.KEY_AUDIENCE_MODE, "default") ?: "default"
        )
        contact = prefs.getString(ClarityPrefs.KEY_DEFAULT_CONTACT, null)?.takeIf { it.isNotEmpty() }
    }

    private fun setupNoneFitButton() {
        btnNoneFit?.setOnLongClickListener {
            showFeedbackDialog()
            true
        }
        btnNoneFit?.setOnClickListener {
            // Short tap: hint that long-press opens feedback
            addChip("长按「都不对…」可反馈")
        }
    }

    private fun showFeedbackDialog() {
        if (lastRaw.isEmpty()) {
            addChip("请先语音清晰化再反馈")
            return
        }
        val input = EditText(this).apply {
            hint = "例如：太正式 / 丢了我原来的语气 / 对象搞错了…"
            minLines = 3
            setPadding(48, 32, 48, 16)
        }
        AlertDialog.Builder(this)
            .setTitle("反馈 — 为什么不对？")
            .setMessage("原文: $lastRaw")
            .setView(input)
            .setPositiveButton("记录反馈") { _, _ ->
                val note = input.text.toString().trim()
                if (note.isNotEmpty()) {
                    Thread {
                        val url = ClarifyClient.feedback(
                            lastRaw,
                            "[user_feedback] $note",
                            lastNbest,
                            lastCandidates,
                            mode,
                        )
                        runOnUiThread {
                            if (!url.isNullOrEmpty()) {
                                val cm = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                                cm.setPrimaryClip(ClipData.newPlainText("bundle", url))
                                addChip("反馈已记录 · bundle 已复制")
                            } else {
                                addChip("反馈已记录")
                            }
                        }
                    }.start()
                }
                hideCandidatePager()
            }
            .setNegativeButton("取消", null)
            .show()
    }

    private fun updateModeChip() {
        hideCandidatePager()
        candidateStrip?.removeAllViews()
        val modeLabel = when (ClarifyRules.normalizeMode(mode)) {
            "contact" -> "联系人 · ${contact ?: "请在设置中选择"}"
            "structured" -> "结构化"
            else -> "通用"
        }
        val core = if (ClarifyClient.health()) " · 已连接" else " · 离线规则"
        addChip("ClarityIME$core · $modeLabel")
        btnMode?.text = modeLabel
    }

    override fun onKey(primaryCode: Int, keyCodes: IntArray?) {
        val ic: InputConnection = currentInputConnection ?: return
        when (primaryCode) {
            Keyboard.KEYCODE_DELETE -> ic.deleteSurroundingText(1, 0)
            Keyboard.KEYCODE_DONE -> ic.sendKeyEvent(
                android.view.KeyEvent(
                    android.view.KeyEvent.ACTION_DOWN,
                    android.view.KeyEvent.KEYCODE_ENTER
                )
            )
            32 -> ic.commitText(" ", 1)
            in 97..122 -> ic.commitText(primaryCode.toChar().toString(), 1)
        }
    }

    override fun onPress(primaryCode: Int) {}
    override fun onRelease(primaryCode: Int) {}
    override fun onText(text: CharSequence?) {
        text?.let { currentInputConnection?.commitText(it, 1) }
    }
    override fun swipeDown() {}
    override fun swipeLeft() {}
    override fun swipeRight() {}
    override fun swipeUp() {}

    private fun cycleMode() {
        mode = when (ClarifyRules.normalizeMode(mode)) {
            "default" -> "structured"
            "structured" -> "contact"
            else -> "default"
        }
        ClarityPrefs.prefs(this).edit()
            .putString(ClarityPrefs.KEY_AUDIENCE_MODE, mode)
            .apply()
        if (mode == "contact" && contact.isNullOrEmpty()) {
            addChip("联系人模式：请先在设置里选择联系人")
        }
        updateModeChip()
    }

    private fun startVoice() {
        if (mode == "contact" && contact.isNullOrEmpty()) {
            addChip("请先在设置中选择联系人")
            return
        }
        if (speech == null) {
            addChip("Speech not available on this device")
            return
        }
        val prefs = ClarityPrefs.prefs(this)
        val lang = prefs.getString(ClarityPrefs.KEY_ASR_LANGUAGE, "auto") ?: "auto"
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 5)
            if (lang.isNotEmpty() && lang != "auto") {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang)
            }
        }
        speech?.startListening(intent)
        hideCandidatePager()
        candidateStrip?.removeAllViews()
        addChip("正在聆听…")
    }

    private fun addChip(label: String) {
        showStatusRow()
        candidateStrip?.addView(TextView(this).apply {
            text = label
            setPadding(24, 12, 24, 12)
        })
    }

    private fun showStatusRow() {
        candidateStatusRow?.visibility = View.VISIBLE
        candidatePagerRow?.visibility = View.GONE
    }

    private fun hideCandidatePager() {
        candidatePagerRow?.visibility = View.GONE
        candidateStatusRow?.visibility = View.VISIBLE
        candidatePager?.adapter = null
    }

    private fun showCandidates(raw: String, options: List<Pair<String, String>>, nbest: List<String> = emptyList()) {
        lastRaw = raw
        lastNbest = nbest
        lastCandidates = options
        candidateStrip?.removeAllViews()

        if (options.isEmpty()) {
            addChip("Raw: $raw · no candidates")
            return
        }

        val autoTop = ClarityPrefs.prefs(this).getBoolean(ClarityPrefs.KEY_AUTO_APPLY_TOP, false)
        if (autoTop) {
            commitClarified(options[0].first)
            return
        }

        candidateStatusRow?.visibility = View.GONE
        candidatePagerRow?.visibility = View.VISIBLE
        candidateRawLabel?.text = "原文 · $raw"

        candidatePager?.adapter = CandidatePagerAdapter(options) { text ->
            commitClarified(text)
        }
        candidatePager?.setCurrentItem(0, false)
    }

    private fun commitClarified(text: String) {
        currentInputConnection?.commitText(text, 1)
        lastRaw = ""
        updateModeChip()
    }

    override fun onResults(results: Bundle?) {
        val list = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION) ?: return
        val raw = list.firstOrNull() ?: return
        showCandidates(raw, ClarifyClient.candidates(raw, mode, contact, list), list)
    }

    override fun onPartialResults(partialResults: Bundle?) {}
    override fun onReadyForSpeech(params: Bundle?) {}
    override fun onBeginningOfSpeech() {}
    override fun onRmsChanged(rmsdB: Float) {}
    override fun onBufferReceived(buffer: ByteArray?) {}
    override fun onEndOfSpeech() {}
    override fun onError(error: Int) {
        addChip("ASR error: $error")
    }
    override fun onEvent(eventType: Int, params: Bundle?) {}

    private inner class CandidatePagerAdapter(
        private val options: List<Pair<String, String>>,
        private val onSelect: (String) -> Unit,
    ) : RecyclerView.Adapter<CandidatePagerAdapter.Holder>() {

        inner class Holder(view: View) : RecyclerView.ViewHolder(view) {
            val label: TextView = view.findViewById(R.id.candidate_label)
            val action: Button = view.findViewById(R.id.candidate_action)
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Holder {
            val view = LayoutInflater.from(parent.context)
                .inflate(R.layout.candidate_page, parent, false)
            return Holder(view)
        }

        override fun onBindViewHolder(holder: Holder, position: Int) {
            val (text, label) = options[position]
            val isTop = position == 0
            holder.label.text = if (isTop) {
                "推荐 · [$label] · 点发送"
            } else {
                "备选 ${position + 1} · [$label]"
            }
            holder.action.text = if (isTop) {
                "发送推荐\n$text"
            } else {
                text
            }
            if (isTop) {
                holder.action.setBackgroundColor(0xFFEDF6EF.toInt())
            } else {
                holder.action.setBackgroundColor(0xFFFFFFFF.toInt())
            }
            holder.action.setOnClickListener { onSelect(text) }
        }

        override fun getItemCount(): Int = options.size
    }
}
