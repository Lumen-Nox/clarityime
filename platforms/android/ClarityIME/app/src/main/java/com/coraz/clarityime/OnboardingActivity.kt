package com.coraz.clarityime

import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * First-run onboarding for ClarityIME keyboard.
 * Explains clarity ≠ polish, audience modes, and one-tap top candidate.
 */
class OnboardingActivity : AppCompatActivity() {
    private var step = 0
    private val totalSteps = 3

    private lateinit var titleView: TextView
    private lateinit var bodyView: TextView
    private lateinit var stepIndicator: TextView
    private lateinit var btnNext: Button
    private lateinit var btnSkip: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_onboarding)

        titleView = findViewById(R.id.onboarding_title)
        bodyView = findViewById(R.id.onboarding_body)
        stepIndicator = findViewById(R.id.onboarding_step_indicator)
        btnNext = findViewById(R.id.btn_onboarding_next)
        btnSkip = findViewById(R.id.btn_onboarding_skip)

        btnSkip.setOnClickListener { finishOnboarding() }
        btnNext.setOnClickListener { advance() }

        showStep()
    }

    private fun showStep() {
        stepIndicator.text = "${step + 1} / $totalSteps"
        when (step) {
            0 -> {
                titleView.text = "清晰化，不是润色"
                bodyView.text = """
                    ClarityIME 保留你的原意，去掉口语 filler，降低误解。

                    不是帮你装专业、换语气 — 是「意思翻译器」。

                    说完话后，键盘候选条会给出清晰化选项；推荐项可以一键发送。
                """.trimIndent()
                btnNext.text = "下一步"
            }
            1 -> {
                titleView.text = "三种面向对象"
                bodyView.text = """
                    · 通用 — 日常清晰化

                    · 联系人 — 按对方理解习惯（在设置里添加）

                    · 结构化 — 分段易读，不摘要

                    清晰化在本地完成，同一句话 + 同一对象，结果始终一致。

                    键盘上点「通用/结构化/联系人」可循环切换。
                """.trimIndent()
                btnNext.text = "下一步"
            }
            else -> {
                titleView.text = "怎么用"
                bodyView.text = """
                    1. 系统设置里启用 ClarityIME 输入法

                    2. 任意 app 切换到 ClarityIME（🌐 键）

                    3. 点 🎤 Voice clarify 说话 → 左右滑动候选条看备选 → 点推荐发送

                    4. 若都不对：长按候选条上的「都不对…」反馈原因

                    可选：Settings 里开「One-tap send top recommendation」跳过候选条。

                    可选：Termux 运行 clarityime serve 获得完整 core（127.0.0.1:17800）。
                """.trimIndent()
                btnNext.text = "开始使用"
            }
        }
    }

    private fun advance() {
        if (step < totalSteps - 1) {
            step++
            showStep()
        } else {
            finishOnboarding()
        }
    }

    private fun finishOnboarding() {
        ClarityPrefs.setOnboardingDone(this)
        finish()
    }
}
