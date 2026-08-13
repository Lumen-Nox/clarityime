import AppKit
import ClarityCore
import InputMethodKit
import Foundation

let kConnectionName = "ClarityIME_Connection"

struct CandidateOption {
    let text: String
    let label: String
}

struct VoiceCaptureResult {
    let raw: String
    let nbest: [String]
}

@objc(ClarityController)
class ClarityController: IMKInputController {
    var mode = "default"
    var contact: String?
    let core = URL(string: "http://127.0.0.1:17800")!

    override func menu() -> NSMenu! {
        let menu = NSMenu(title: "ClarityIME")
        let voiceItem = menu.addItem(
            withTitle: "🎤 Voice clarify",
            action: #selector(voiceClarify(_:)),
            keyEquivalent: ""
        )
        voiceItem.target = self
        menu.addItem(NSMenuItem.separator())
        for m in ["default", "ai", "contact"] {
            let item = menu.addItem(
                withTitle: "Mode: \(m)",
                action: #selector(setMode(_:)),
                keyEquivalent: ""
            )
            item.representedObject = m
            item.state = (mode == m) ? .on : .off
            item.target = self
        }
        return menu
    }

    @objc func setMode(_ sender: NSMenuItem) {
        guard let m = sender.representedObject as? String else { return }
        mode = m
    }

    @objc func voiceClarify(_ sender: Any?) {
        guard let client = self.client() else { return }
        guard let captured = runVoiceCapture(), !captured.raw.isEmpty else { return }

        let options = fetchCandidates(raw: captured.raw, nbest: captured.nbest)
        guard let text = resolveCandidate(
            raw: captured.raw,
            options: options,
            nbest: captured.nbest
        ) else { return }
        client.insertText(text, replacementRange: NSRange(location: NSNotFound, length: 0))
        if text != captured.raw {
            sendFeedback(
                raw: captured.raw,
                preferred: text,
                nbest: captured.nbest,
                candidates: options,
                mode: mode
            )
        }
    }

    func runVoiceCapture() -> VoiceCaptureResult? {
        let root = ProcessInfo.processInfo.environment["CLARITYIME_ROOT"] ?? ""
        let venvPython = root.isEmpty ? "" : "\(root)/.venv/bin/python3"
        let python = (!venvPython.isEmpty && FileManager.default.fileExists(atPath: venvPython))
            ? venvPython
            : "/usr/bin/python3"
        let task = Process()
        task.executableURL = URL(fileURLWithPath: python)
        task.arguments = ["-m", "clarityime.main", "capture", "--seconds", "5"]
        if !root.isEmpty {
            task.currentDirectoryURL = URL(fileURLWithPath: root)
            var env = ProcessInfo.processInfo.environment
            env["CLARITYIME_ROOT"] = root
            task.environment = env
        }
        let pipe = Pipe()
        task.standardOutput = pipe
        try? task.run()
        task.waitUntilExit()
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let raw = json["raw"] as? String, !raw.isEmpty else { return nil }

        var nbest: [String] = []
        if let arr = json["nbest"] as? [Any] {
            nbest = arr.compactMap { item in
                guard let s = item as? String else { return nil }
                let t = s.trimmingCharacters(in: .whitespacesAndNewlines)
                return t.isEmpty ? nil : t
            }
        }
        if nbest.isEmpty { nbest = [raw] }
        return VoiceCaptureResult(raw: raw, nbest: nbest)
    }

    func fetchCandidates(raw: String, nbest: [String]? = nil) -> [CandidateOption] {
        var req = URLRequest(url: core.appendingPathComponent("/v1/candidates"))
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        var body: [String: Any] = ["text": raw, "mode": mode]
        if let c = contact { body["contact"] = c }
        if let nbest, !nbest.isEmpty { body["nbest"] = nbest }
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)
        guard let (data, _) = try? URLSession.shared.syncData(for: req),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let arr = json["candidates"] as? [[String: Any]] else {
            return [CandidateOption(text: ClarityOfflineClarifier.clarify(raw, mode: mode), label: "offline")]
        }
        return arr.compactMap { item in
            guard let t = item["text"] as? String else { return nil }
            return CandidateOption(text: t, label: item["label"] as? String ?? "option")
        }
    }

    func resolveCandidate(raw: String, options: [CandidateOption], nbest: [String]) -> String? {
        guard !options.isEmpty else { return nil }
        if ClaritySettingsLoader.isAutoApplyTopEnabled() {
            return options[0].text
        }
        if options.count == 1 {
            return options[0].text
        }
        return ClarityCandidatePicker.pick(
            raw: raw,
            options: options,
            nbest: nbest,
            mode: mode
        )
    }

    func sendFeedback(
        raw: String,
        preferred: String,
        nbest: [String] = [],
        candidates: [CandidateOption] = [],
        mode: String? = nil
    ) {
        var req = URLRequest(url: core.appendingPathComponent("/v1/feedback"))
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        var body: [String: Any] = ["raw": raw, "preferred": preferred]
        if !nbest.isEmpty { body["nbest"] = nbest }
        if !candidates.isEmpty {
            body["candidates"] = candidates.map { ["text": $0.text, "label": $0.label] }
        }
        if let mode { body["mode"] = mode }
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)
        _ = try? URLSession.shared.syncData(for: req)
    }
}

// MARK: - Settings (auto_apply_top from clarityime data/settings.json)

enum ClaritySettingsLoader {
    static func settingsPath() -> URL? {
        if let root = ProcessInfo.processInfo.environment["CLARITYIME_ROOT"], !root.isEmpty {
            let p = URL(fileURLWithPath: root).appendingPathComponent("data/settings.json")
            if FileManager.default.fileExists(atPath: p.path) { return p }
        }
        for candidate in candidateRoots() {
            let p = candidate.appendingPathComponent("data/settings.json")
            if FileManager.default.fileExists(atPath: p.path) { return p }
        }
        let home = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent(".clarityime/data/settings.json")
        return FileManager.default.fileExists(atPath: home.path) ? home : nil
    }

    private static func candidateRoots() -> [URL] {
        var roots: [URL] = []
        var dir = URL(fileURLWithPath: #file).deletingLastPathComponent()
        for _ in 0..<6 {
            let parent = dir.deletingLastPathComponent()
            if FileManager.default.fileExists(atPath: parent.appendingPathComponent("clarityime/main.py").path) {
                roots.append(parent)
            }
            dir = parent
        }
        return roots
    }

    static func isAutoApplyTopEnabled() -> Bool {
        guard
            let path = settingsPath(),
            let data = try? Data(contentsOf: path),
            let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
            let value = json["auto_apply_top"] as? Bool
        else { return false }
        return value
    }
}

// MARK: - Candidate picker (one-tap top, alts below — matches TSF/Android pattern)

enum ClarityCandidatePicker {
    static func pick(
        raw: String,
        options: [CandidateOption],
        nbest: [String] = [],
        mode: String = "default"
    ) -> String? {
        guard !options.isEmpty else { return nil }

        var pickedIndex: Int?
        var feedbackRequested = false
        var retainedTargets: [BlockTarget] = []
        let panel = NSPanel(
            contentRect: NSRect(x: 0, y: 0, width: 520, height: 380),
            styleMask: [.titled, .closable],
            backing: .buffered,
            defer: false
        )
        panel.title = "ClarityIME — 选清晰化结果"
        panel.isFloatingPanel = true
        panel.level = .floating

        let stack = NSStackView()
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 8
        stack.translatesAutoresizingMaskIntoConstraints = false
        stack.edgeInsets = NSEdgeInsets(top: 12, left: 12, bottom: 12, right: 12)

        let rawLabel = NSTextField(wrappingLabelWithString: "原文 · \(raw)")
        rawLabel.font = NSFont.systemFont(ofSize: 12)
        rawLabel.textColor = .secondaryLabelColor
        stack.addArrangedSubview(rawLabel)

        for (i, opt) in options.enumerated() {
            if i == 1 {
                let hint = NSTextField(labelWithString: "其他选项（点选 · 或按 2/3）")
                hint.font = NSFont.systemFont(ofSize: 11)
                hint.textColor = .secondaryLabelColor
                stack.addArrangedSubview(hint)
            }
            let title = i == 0
                ? "⏎ 发送推荐 · [\(opt.label)]\n\(opt.text)"
                : "\(i + 1). [\(opt.label)] \(opt.text)"
            let btn = NSButton(title: title, target: nil, action: nil)
            btn.setButtonType(.momentaryPushIn)
            btn.bezelStyle = .rounded
            btn.alignment = .left
            btn.lineBreakMode = .byWordWrapping
            if i == 0 {
                btn.contentTintColor = NSColor(calibratedRed: 0.15, green: 0.5, blue: 0.25, alpha: 1)
            }
            let idx = i
            let target = BlockTarget {
                pickedIndex = idx
                panel.close()
            }
            retainedTargets.append(target)
            btn.target = target
            btn.action = #selector(BlockTarget.invoke)
            btn.widthAnchor.constraint(equalToConstant: 496).isActive = true
            stack.addArrangedSubview(btn)
        }

        let cancel = NSButton(title: "取消 (Esc)", target: nil, action: nil)
        let cancelTarget = BlockTarget {
            pickedIndex = nil
            panel.close()
        }
        retainedTargets.append(cancelTarget)
        cancel.target = cancelTarget
        cancel.action = #selector(BlockTarget.invoke)
        stack.addArrangedSubview(cancel)

        let bad = NSButton(title: "都不对…", target: nil, action: nil)
        let badTarget = BlockTarget {
            feedbackRequested = true
            panel.close()
        }
        retainedTargets.append(badTarget)
        bad.target = badTarget
        bad.action = #selector(BlockTarget.invoke)
        stack.addArrangedSubview(bad)

        let content = NSView(frame: panel.contentRect(forFrameRect: panel.frame))
        content.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: content.leadingAnchor),
            stack.trailingAnchor.constraint(equalTo: content.trailingAnchor),
            stack.topAnchor.constraint(equalTo: content.topAnchor),
            stack.bottomAnchor.constraint(lessThanOrEqualTo: content.bottomAnchor),
        ])
        panel.contentView = content

        var monitor: Any?
        monitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { event in
            switch event.keyCode {
            case 36: // Return → top
                pickedIndex = 0
                panel.close()
                return nil
            case 18, 19, 20: // 1, 2, 3
                let idx = Int(event.keyCode - 18)
                if idx < options.count {
                    pickedIndex = idx
                    panel.close()
                }
                return nil
            case 53: // Esc
                pickedIndex = nil
                panel.close()
                return nil
            default:
                return event
            }
        }

        NSApp.activate(ignoringOtherApps: true)
        panel.makeKeyAndOrderFront(nil)
        NSApp.runModal(for: panel)
        if let monitor { NSEvent.removeMonitor(monitor) }

        if feedbackRequested {
            showFeedbackAlert(raw: raw, nbest: nbest, options: options, mode: mode)
            return nil
        }

        guard let idx = pickedIndex, idx >= 0, idx < options.count else { return nil }
        return options[idx].text
    }

    private static func showFeedbackAlert(
        raw: String,
        nbest: [String],
        options: [CandidateOption],
        mode: String
    ) {
        let alert = NSAlert()
        alert.messageText = "反馈 — 为什么不对？"
        alert.informativeText = "原文: \(raw)"
        let input = NSTextField(frame: NSRect(x: 0, y: 0, width: 360, height: 24))
        input.placeholderString = "太正式 / 丢语气 / 对象错了…"
        alert.accessoryView = input
        alert.addButton(withTitle: "记录反馈")
        alert.addButton(withTitle: "取消")
        guard alert.runModal() == .alertFirstButtonReturn else { return }
        let note = input.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !note.isEmpty else { return }
        var req = URLRequest(url: URL(string: "http://127.0.0.1:17800/v1/feedback")!)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        var body: [String: Any] = [
            "raw": raw,
            "preferred": "[user_feedback] \(note)",
            "mode": mode,
        ]
        let hyps = nbest.isEmpty ? [raw] : nbest
        body["nbest"] = hyps
        body["candidates"] = options.map { ["text": $0.text, "label": $0.label] }
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)
        if let (data, _) = try? URLSession.shared.syncData(for: req),
           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let url = json["bundle_url"] as? String {
            NSPasteboard.general.clearContents()
            NSPasteboard.general.setString(url, forType: .string)
            let done = NSAlert()
            done.messageText = "反馈已记录"
            done.informativeText = "N-best bundle 已复制:\n\(url)"
            done.runModal()
        }
    }
}

/// Lightweight target for button actions inside modal panel.
private final class BlockTarget: NSObject {
    private let block: () -> Void
    init(_ block: @escaping () -> Void) { self.block = block }
    @objc func invoke() { block() }
}

extension URLSession {
    func syncData(for request: URLRequest) throws -> (Data, URLResponse) {
        var result: (Data, URLResponse)?
        var err: Error?
        let sem = DispatchSemaphore(value: 0)
        let task = dataTask(with: request) { data, resp, error in
            if let error = error { err = error }
            else if let data = data, let resp = resp { result = (data, resp) }
            sem.signal()
        }
        task.resume()
        sem.wait()
        if let err = err { throw err }
        guard let result = result else {
            throw URLError(.badServerResponse)
        }
        return result
    }
}

@main
class ClarityIMKApp: NSObject, NSApplicationDelegate {
    var server: IMKServer!

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        let bundleId = Bundle.main.bundleIdentifier ?? "com.clarityime"
        server = IMKServer(name: kConnectionName, bundleIdentifier: bundleId)
    }
}
