import UIKit

/// ClarityIME iOS Keyboard Extension — clarify inside keyboard (offline-first + App Group voice sync).
class ClarityKeyboardViewController: UIInputViewController {
    private let store = SharedStore.shared
    private var mode = "default"
    private var contact: String?
    private var contactHints = ContactHints.empty
    private var autoApplyTop = false
    private var lastConsumedSessionID = 0
    private var pendingRaw = ""
    private var pendingNbest: [String] = []
    private var pendingOptions: [(String, String)] = []

    private var candidateStack: UIStackView!
    private var modeBtn: UIButton!
    private var inputField: UITextField!
    private var pollTimer: Timer?

    override func viewDidLoad() {
        super.viewDidLoad()
        loadPrefs()
        buildUI()
        // Start at 0 so an already-pending host voice session still surfaces on first poll.
        lastConsumedSessionID = 0
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        loadPrefs()
        updateModeLabel()
        checkSharedVoiceCandidates()
        startPolling()
    }

    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        pollTimer?.invalidate()
        pollTimer = nil
    }

    // MARK: - UI

    private func buildUI() {
        let stack = UIStackView()
        stack.axis = .vertical
        stack.spacing = 8
        stack.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 8),
            stack.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -8),
            stack.topAnchor.constraint(equalTo: view.topAnchor, constant: 8),
        ])

        inputField = UITextField()
        inputField.placeholder = "粘贴或输入语音原文…"
        inputField.borderStyle = .roundedRect
        stack.addArrangedSubview(inputField)

        let row = UIStackView()
        row.axis = .horizontal
        row.distribution = .fillEqually
        row.spacing = 8

        let clarifyBtn = UIButton(type: .system)
        clarifyBtn.setTitle("清晰化", for: .normal)
        clarifyBtn.addTarget(self, action: #selector(clarifyTapped), for: .touchUpInside)
        row.addArrangedSubview(clarifyBtn)

        modeBtn = UIButton(type: .system)
        modeBtn.addTarget(self, action: #selector(cycleMode), for: .touchUpInside)
        row.addArrangedSubview(modeBtn)
        updateModeLabel()

        let syncBtn = UIButton(type: .system)
        syncBtn.setTitle("↻ Voice", for: .normal)
        syncBtn.addTarget(self, action: #selector(refreshVoiceTapped), for: .touchUpInside)
        row.addArrangedSubview(syncBtn)

        stack.addArrangedSubview(row)

        candidateStack = UIStackView()
        candidateStack.axis = .vertical
        candidateStack.spacing = 4
        stack.addArrangedSubview(candidateStack)
    }

    // MARK: - Prefs

    func loadPrefs() {
        mode = ClarifyRules.normalizeMode(store.audienceMode)
        contact = store.defaultContact
        contactHints = store.contactHints
        autoApplyTop = store.autoApplyTop
    }

    func savePrefs() {
        store.audienceMode = ClarifyRules.normalizeMode(mode)
        store.defaultContact = contact
    }

    func updateModeLabel() {
        let modeName: String
        switch ClarifyRules.normalizeMode(mode) {
        case "structured": modeName = "结构化"
        case "contact": modeName = "联系人"
        default: modeName = "通用"
        }
        let c = contact.map { " · \($0)" } ?? ""
        modeBtn.setTitle("\(modeName)\(c)", for: .normal)
    }

    // MARK: - App Group voice sync

    private func startPolling() {
        pollTimer?.invalidate()
        pollTimer = Timer.scheduledTimer(withTimeInterval: 0.8, repeats: true) { [weak self] _ in
            self?.checkSharedVoiceCandidates()
        }
    }

    @objc private func refreshVoiceTapped() {
        checkSharedVoiceCandidates(force: true)
    }

    private func checkSharedVoiceCandidates(force: Bool = false) {
        let session = store.voiceSessionID
        let pending = store.voicePendingCommit

        if pending {
            updateVoicePendingIndicator(show: true)
        } else if !force {
            updateVoicePendingIndicator(show: false)
            return
        }

        guard force || pending else { return }
        guard force || session != lastConsumedSessionID else { return }

        let raw = store.voiceRawText
        let options = store.voiceCandidates

        if raw.isEmpty || options.isEmpty {
            if pending {
                let status = store.voiceStatusMessage.nilIfEmpty ?? "Waiting for host voice…"
                showChip("🎤 \(status)")
            }
            return
        }

        showCandidates(
            raw: raw,
            options: options.map { ($0.text, $0.label) },
            fromVoiceHost: true,
            nbest: store.voiceNbest
        )
    }

    /// Small banner while host has published candidates awaiting keyboard commit.
    private func updateVoicePendingIndicator(show: Bool) {
        // Re-use candidate stack header area — showCandidates replaces full stack when ready.
        guard show, store.voiceCandidates.isEmpty, store.voiceRawText.isEmpty else { return }
        let status = store.voiceStatusMessage.nilIfEmpty ?? "Voice ready — loading candidates…"
        showChip("🎤 \(status)")
    }

    // MARK: - Actions

    @objc func cycleMode(_ sender: UIButton) {
        switch ClarifyRules.normalizeMode(mode) {
        case "default": mode = "structured"
        case "structured": mode = "contact"
        default: mode = "default"
        }
        savePrefs()
        updateModeLabel()
    }

    @objc func clarifyTapped() {
        guard let raw = inputField.text?.trimmingCharacters(in: .whitespacesAndNewlines), !raw.isEmpty else {
            showChip("Enter or paste text first")
            return
        }
        if mode == "contact" && (contact ?? "").isEmpty {
            showChip("Set contact in host app Settings")
            return
        }
        let options = fetchCandidates(raw: raw)
        showCandidates(raw: raw, options: options, fromVoiceHost: false)
    }

    func fetchCandidates(raw: String, nbest: [String]? = nil) -> [(String, String)] {
        let hypotheses = nbest?.filter { !$0.isEmpty }
        if let remote = ClarifyClient.candidates(
            text: raw,
            mode: mode,
            contact: contact,
            nbest: hypotheses
        ) {
            return remote.map { ($0.text, $0.label) }
        }
        return ClarifyRules.candidates(text: raw, mode: mode, contactHints: contactHints)
            .map { ($0.text, $0.label) }
    }

    func showCandidates(
        raw: String,
        options: [(String, String)],
        fromVoiceHost: Bool,
        nbest: [String] = []
    ) {
        guard !options.isEmpty else {
            showChip("No clarification candidates")
            return
        }

        pendingRaw = raw
        pendingNbest = nbest.isEmpty ? [raw] : nbest
        pendingOptions = options

        if autoApplyTop {
            commitCandidate(text: options[0].0, raw: raw)
            return
        }
        candidateStack.arrangedSubviews.forEach { $0.removeFromSuperview() }

        let header = fromVoiceHost ? "🎤 Host voice" : "Manual"
        let rawLabel = UILabel()
        rawLabel.text = "\(header) · Raw: \(raw)"
        rawLabel.font = .systemFont(ofSize: 12)
        rawLabel.textColor = .secondaryLabel
        rawLabel.numberOfLines = 0
        candidateStack.addArrangedSubview(rawLabel)

        for (i, (text, label)) in options.enumerated() {
            if i == 1 {
                let hint = UILabel()
                hint.text = "其他选项 · 点选发送"
                hint.font = .systemFont(ofSize: 11)
                hint.textColor = .tertiaryLabel
                candidateStack.addArrangedSubview(hint)
            }
            let btn = UIButton(type: .system)
            if i == 0 {
                var cfg = UIButton.Configuration.filled()
                cfg.title = "⏎ 发送推荐 · [\(label)]\n\(text)"
                cfg.baseBackgroundColor = UIColor.systemGreen.withAlphaComponent(0.25)
                cfg.titleAlignment = .leading
                cfg.contentInsets = NSDirectionalEdgeInsets(top: 10, leading: 12, bottom: 10, trailing: 12)
                btn.configuration = cfg
            } else {
                btn.contentHorizontalAlignment = .left
                btn.titleLabel?.numberOfLines = 0
                btn.setTitle("\(i + 1). [\(label)] \(text)", for: .normal)
            }
            btn.addAction(UIAction { [weak self] _ in
                self?.commitCandidate(text: text, raw: raw)
            }, for: .touchUpInside)
            candidateStack.addArrangedSubview(btn)
        }

        let badBtn = UIButton(type: .system)
        badBtn.setTitle("都不对…", for: .normal)
        badBtn.addAction(UIAction { [weak self] _ in
            self?.showFeedbackPrompt()
        }, for: .touchUpInside)
        candidateStack.addArrangedSubview(badBtn)

        if fromVoiceHost {
            let dismiss = UIButton(type: .system)
            dismiss.setTitle("Dismiss", for: .normal)
            dismiss.addAction(UIAction { [weak self] _ in
                self?.dismissVoiceCandidates()
            }, for: .touchUpInside)
            candidateStack.addArrangedSubview(dismiss)
        }
    }

    private func showFeedbackPrompt() {
        guard !pendingRaw.isEmpty else {
            showChip("先说话或 clarify 再反馈")
            return
        }
        let alert = UIAlertController(
            title: "反馈 — 为什么不对？",
            message: "原文: \(pendingRaw)",
            preferredStyle: .alert
        )
        alert.addTextField { field in
            field.placeholder = "太正式 / 丢语气 / 对象错了…"
        }
        alert.addAction(UIAlertAction(title: "取消", style: .cancel))
        alert.addAction(UIAlertAction(title: "记录", style: .default) { [weak self] _ in
            guard let self else { return }
            let note = alert.textFields?.first?.text?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            guard !note.isEmpty else { return }
            let cands = self.pendingOptions.map { ClarifyCandidate(text: $0.0, label: $0.1) }
            DispatchQueue.global(qos: .userInitiated).async {
                let result = FeedbackSync.submit(
                    raw: self.pendingRaw,
                    preferred: "[user_feedback] \(note)",
                    nbest: self.pendingNbest,
                    candidates: cands,
                    mode: self.mode
                )
                DispatchQueue.main.async {
                    switch result {
                    case .sent(let url):
                        UIPasteboard.general.string = url
                        self.showChip("反馈已记录 · bundle 已复制")
                    case .queued:
                        self.showChip("反馈已排队 · Host 联网后同步")
                    }
                    self.dismissVoiceCandidates()
                }
            }
        })
        present(alert, animated: true)
    }

    private func commitCandidate(text: String, raw: String) {
        textDocumentProxy.insertText(text)
        inputField.text = ""
        candidateStack.arrangedSubviews.forEach { $0.removeFromSuperview() }
        lastConsumedSessionID = store.voiceSessionID
        store.clearVoicePending()
        let cands = pendingOptions.map { ClarifyCandidate(text: $0.0, label: $0.1) }
        DispatchQueue.global(qos: .userInitiated).async {
            _ = FeedbackSync.submit(
                raw: raw,
                preferred: text,
                nbest: self.pendingNbest,
                candidates: cands,
                mode: self.mode
            )
        }
        pendingRaw = ""
        pendingNbest = []
        pendingOptions = []
    }

    private func dismissVoiceCandidates() {
        lastConsumedSessionID = store.voiceSessionID
        store.clearVoicePending()
        candidateStack.arrangedSubviews.forEach { $0.removeFromSuperview() }
        pendingRaw = ""
        pendingNbest = []
        pendingOptions = []
        showChip("Voice candidates dismissed")
    }

    func showChip(_ msg: String) {
        candidateStack.arrangedSubviews.forEach { $0.removeFromSuperview() }
        let l = UILabel()
        l.text = msg
        l.font = .systemFont(ofSize: 12)
        l.numberOfLines = 0
        candidateStack.addArrangedSubview(l)
    }
}

private extension String {
    var nilIfEmpty: String? {
        trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : self
    }
}
