import SwiftUI

/// First-run onboarding — clarity ≠ polish, audience modes, Host + Keyboard flow.
struct OnboardingView: View {
    @Binding var isPresented: Bool
    @State private var step = 0

    private let totalSteps = 3

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 16) {
                Text(stepTitle)
                    .font(.title2.bold())

                ScrollView {
                    Text(stepBody)
                        .font(.body)
                        .lineSpacing(4)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }

                Spacer(minLength: 0)

                Text("\(step + 1) / \(totalSteps)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity)

                HStack {
                    Spacer()
                    Button("Skip") { finish() }
                        .buttonStyle(.borderless)
                    Button(step < totalSteps - 1 ? "Next" : "Get started") {
                        if step < totalSteps - 1 {
                            step += 1
                        } else {
                            finish()
                        }
                    }
                    .buttonStyle(.borderedProminent)
                }
            }
            .padding(20)
            .navigationTitle("Welcome")
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    private var stepTitle: String {
        switch step {
        case 0: return "清晰化，不是润色"
        case 1: return "三种面向对象"
        default: return "怎么用"
        }
    }

    private var stepBody: String {
        switch step {
        case 0:
            return """
            ClarityIME 保留原意，去掉口语 filler，降低误解。

            不是帮你装专业、换语气 — 是「意思翻译器」。

            说完话后，键盘会给出清晰化选项；推荐项可一键发送。
            """
        case 1:
            return """
            · 通用 — 日常清晰化

            · 联系人 — 按对方理解习惯（在设置里添加）

            · 结构化 — 分段易读，不摘要

            清晰化在本地完成；同一句话 + 同一对象，结果始终一致。

            键盘上可循环切换面向对象。
            """
        default:
            return """
            1. Settings → General → Keyboard → add ClarityIME → enable Full Access

            2. In ClarityHost: tap 🎤 and speak → candidates sync to the keyboard

            3. Switch to ClarityIME keyboard → tap the green ⏎ recommendation or an alternate

            4. If none fit: use feedback (long-press / 「都不对…」 on other platforms)

            Optional: turn on Auto-apply top candidate in Settings to skip the picker.

            Optional: run clarityime serve on a Mac on the same LAN for full core (localhost on device is limited).
            """
        }
    }

    private func finish() {
        SharedStore.shared.markOnboardingCompleted()
        isPresented = false
    }
}

#Preview {
    OnboardingView(isPresented: .constant(true))
}
