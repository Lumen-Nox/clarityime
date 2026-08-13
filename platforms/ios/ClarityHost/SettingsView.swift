import SwiftUI
import UIKit

struct SettingsView: View {
    @Environment(\.dismiss) private var dismiss

    @State private var mode = ClarifyRules.normalizeMode(SharedStore.shared.audienceMode)
    @State private var autoApplyTop = SharedStore.shared.autoApplyTop
    @State private var contactName = SharedStore.shared.defaultContact ?? ""
    @State private var asrLanguage = SharedStore.shared.asrLanguage
    @State private var relationship = SharedStore.shared.contactHints.relationship
    @State private var styleHint = SharedStore.shared.contactHints.style
    @State private var ageHint = SharedStore.shared.contactHints.age
    @State private var lexiconMap = SharedStore.shared.contactHints.words
    @State private var coreStatus = "Checking…"
    @State private var showOnboarding = false
    @State private var importJSON = ""
    @State private var contactActionMessage = ""
    @State private var coreContacts: [ContactRow] = []
    @State private var apiToken = SharedStore.shared.localApiToken
    @State private var ceromeClarity = 0.7
    @State private var ceromeWarmth = 0.5
    @State private var ceromeEfficiency = 0.5
    @State private var ceromePrecision = 0.5
    @State private var ceromeHumor = 0.35
    @State private var ceromeMood = "steady"

    private let modes = ["default", "structured", "contact"]
    private let moodOptions = ["steady", "stressed", "upbeat", "tired", "focused"]

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Picker("Mode", selection: $mode) {
                        ForEach(modes, id: \.self) { m in
                            Text(modeLabel(m)).tag(m)
                        }
                    }
                    .pickerStyle(.segmented)

                    VStack(alignment: .leading, spacing: 6) {
                        Text(modeHelpTitle)
                            .font(.subheadline.weight(.semibold))
                        Text(modeHelp)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .padding(.vertical, 4)
                } header: {
                    Text("Audience mode")
                } footer: {
                    Text("同一句话、同一面向对象，结果始终一致。清晰化在本地完成，不调用生成式 AI。")
                        .font(.caption2)
                }

                Section {
                    Toggle("Auto-apply top candidate", isOn: $autoApplyTop)
                    Text("When on, the keyboard sends the top recommendation immediately after clarify — one tap saved. When off, you pick from the green ⏎ button or alternates.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } header: {
                    Text("Candidate UX")
                }

                Section("Contact (placeholder)") {
                    TextField("Name / label", text: $contactName)
                    TextField("Relationship (老师/老板/…)", text: $relationship)
                    TextField("Style hint (简短/口语)", text: $styleHint)
                    TextField("Age (for child simplify)", text: $ageHint)
                        .keyboardType(.numberPad)
                    TextField("Lexicon map (坏->不好)", text: $lexiconMap)
                    if !coreContacts.isEmpty {
                        Text("Core contacts: \(coreContacts.map(\.name).joined(separator: ", "))")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Button("Export contact JSON (clipboard)") {
                        exportContactToClipboard()
                    }
                    .disabled(contactName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    Text("Import bundle JSON (requires core on LAN / Termux)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    TextEditor(text: $importJSON)
                        .frame(minHeight: 80)
                        .font(.system(.caption, design: .monospaced))
                    Button("Import contact from JSON") {
                        importContactFromJSON()
                    }
                    if !contactActionMessage.isEmpty {
                        Text(contactActionMessage)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Text("Full contact sync from desktop `clarityime contacts` — future LAN/core sync.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section("Speech recognition") {
                    TextField("Locale (e.g. zh-CN, en-US)", text: $asrLanguage)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                }

                Section("沟通偏好") {
                    Slider(value: $ceromeClarity, in: 0...1) { Text("清晰") }
                    Slider(value: $ceromeWarmth, in: 0...1) { Text("温和") }
                    Slider(value: $ceromeEfficiency, in: 0...1) { Text("效率") }
                    Slider(value: $ceromePrecision, in: 0...1) { Text("精确") }
                    Slider(value: $ceromeHumor, in: 0...1) { Text("幽默") }
                    Picker("当前状态", selection: $ceromeMood) {
                        ForEach(moodOptions, id: \.self) { Text($0).tag($0) }
                    }
                    Text("配对导出时仅包含 L1/L2/L4/L5，不含 L3 私密词。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section("Core API (optional)") {
                    SecureField("API token (X-ClarityIME-Token)", text: $apiToken)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    HStack {
                        Text("Status")
                        Spacer()
                        Text(coreStatus)
                            .foregroundStyle(.secondary)
                    }
                    Button("Refresh") { refreshCore() }
                    Text("`clarityime serve` on localhost is usually unavailable on iOS. Offline ClarifyRules always apply.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section("Help") {
                    Button("Show onboarding again") {
                        SharedStore.shared.resetOnboarding()
                        showOnboarding = true
                    }
                }
            }
            .navigationTitle("Settings")
            .fullScreenCover(isPresented: $showOnboarding) {
                OnboardingView(isPresented: $showOnboarding)
            }
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { save() }
                }
            }
            .onAppear { refreshCore() }
        }
    }

    private func modeLabel(_ m: String) -> String {
        switch ClarifyRules.normalizeMode(m) {
        case "structured": return "结构化"
        case "contact": return "联系人"
        default: return "通用"
        }
    }

    private var modeHelpTitle: String {
        switch ClarifyRules.normalizeMode(mode) {
        case "structured": return "结构化 — 分段易读，保留语气与细节"
        case "contact": return "联系人 — 按对方理解习惯"
        default: return "通用 — 日常清晰化"
        }
    }

    private var modeHelp: String {
        switch ClarifyRules.normalizeMode(mode) {
        case "structured":
            return "只理清标点和层次，不删内容、不摘要；多句时分段显示。"
        case "contact":
            return "根据联系人档案调整用词与句式（下方可填离线 hint）。"
        default:
            return "去 filler、补标点、拆长句，原意不变。"
        }
    }

    private func refreshCore() {
        DispatchQueue.global(qos: .userInitiated).async {
            let ok = ClarifyClient.health()
            let loaded = ok ? ClarifyClient.listContacts() : []
            DispatchQueue.main.async {
                coreStatus = ok ? "Connected :17800" : "Offline — Swift rules"
                coreContacts = loaded
            }
        }
    }

    private func exportContactToClipboard() {
        let name = contactName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !name.isEmpty else { return }
        DispatchQueue.global(qos: .userInitiated).async {
            let json = ClarifyClient.exportContactBundle(name: name)
            DispatchQueue.main.async {
                guard let json, !json.isEmpty else {
                    contactActionMessage = "Export failed — core offline or contact missing"
                    return
                }
                UIPasteboard.general.string = json
                contactActionMessage = "Exported \(name) → clipboard"
            }
        }
    }

    private func importContactFromJSON() {
        let json = importJSON.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !json.isEmpty else {
            contactActionMessage = "Paste JSON first"
            return
        }
        DispatchQueue.global(qos: .userInitiated).async {
            let ok = ClarifyClient.importContactBundle(json: json)
            let loaded = ok ? ClarifyClient.listContacts() : []
            DispatchQueue.main.async {
                if ok {
                    coreContacts = loaded
                    importJSON = ""
                    contactActionMessage = "Contact imported"
                } else {
                    contactActionMessage = "Import failed — core offline or invalid JSON"
                }
            }
        }
    }

    private func save() {
        let hints = ContactHints(
            name: contactName.trimmingCharacters(in: .whitespacesAndNewlines),
            relationship: relationship.trimmingCharacters(in: .whitespacesAndNewlines),
            style: styleHint.trimmingCharacters(in: .whitespacesAndNewlines),
            age: ageHint.trimmingCharacters(in: .whitespacesAndNewlines),
            words: lexiconMap.trimmingCharacters(in: .whitespacesAndNewlines)
        )
        let contact = contactName.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty
        SharedStore.shared.saveSettings(
            mode: ClarifyRules.normalizeMode(mode),
            contact: contact,
            language: asrLanguage.nilIfEmpty ?? AppGroupConstants.defaultASRLanguage,
            hints: hints,
            autoApplyTop: autoApplyTop,
            localApiToken: apiToken.trimmingCharacters(in: .whitespacesAndNewlines)
        )
        if !contactName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            DispatchQueue.global(qos: .utility).async {
                _ = ClarifyClient.saveContact(
                    name: contactName.trimmingCharacters(in: .whitespacesAndNewlines),
                    relationship: relationship,
                    styleNotes: styleHint,
                    comprehensionNotes: "",
                    ceromeL2: [
                        "clarity": ceromeClarity,
                        "warmth": ceromeWarmth,
                        "efficiency": ceromeEfficiency,
                        "precision": ceromePrecision,
                        "humor": ceromeHumor,
                    ],
                    moodLabel: ceromeMood
                )
            }
        }
        dismiss()
    }
}

private extension String {
    var nilIfEmpty: String? {
        trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : self
    }
}

#Preview {
    SettingsView()
}
