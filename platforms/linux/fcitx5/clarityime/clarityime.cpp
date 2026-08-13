/*
 * ClarityIME — Fcitx5 voice clarify input method
 * SPDX-License-Identifier: MIT
 */
#include "clarityime.h"

#include <fcitx-utils/keysym.h>
#include <fcitx-utils/log.h>
#include <fcitx/inputpanel.h>
#include <fcitx/userinterfacemanager.h>

#include <array>
#include <cstdlib>
#include <fstream>
#include <sstream>

namespace {

std::string shellQuote(const std::string &value) {
    std::string out = "'";
    for (char ch : value) {
        if (ch == '\'') {
            out += "'\\''";
        } else {
            out += ch;
        }
    }
    out += "'";
    return out;
}

std::string trim(const std::string &text) {
    const auto start = text.find_first_not_of(" \t\r\n");
    if (start == std::string::npos) {
        return {};
    }
    const auto end = text.find_last_not_of(" \t\r\n");
    return text.substr(start, end - start + 1);
}

std::string resolveEnginePyPath() {
    if (const char *env = std::getenv("CLARITYIME_FCITX5_ENGINE")) {
        if (*env) {
            return env;
        }
    }
    if (const char *home = std::getenv("HOME")) {
        const auto fromInstall =
            std::string(home) + "/.local/share/clarityime/fcitx5/engine.py";
        std::ifstream probe(fromInstall);
        if (probe) {
            return fromInstall;
        }
    }
    return "/usr/local/share/clarityime/fcitx5/engine.py";
}

} // namespace

ClarityCandidateWord::ClarityCandidateWord(ClarityState *state,
                                           std::string commitText,
                                           std::string label,
                                           std::size_t index, bool isTop)
    : fcitx::CandidateWord(fcitx::Text()), state_(state), index_(index) {
    fcitx::Text display;
    if (isTop) {
        display.append("★ 推荐");
        display.append(" · [");
        display.append(label);
        display.append("] ");
        display.append(commitText);
        display.append("  (Enter/1)");
    } else {
        display.append(std::to_string(index + 1));
        display.append(". [");
        display.append(label);
        display.append("] ");
        display.append(commitText);
    }
    setText(std::move(display));
}

void ClarityCandidateWord::select(fcitx::InputContext *inputContext) {
    FCITX_UNUSED(inputContext);
    if (state_) {
        state_->applyCandidate(index_);
    }
}

ClarityState::ClarityState(ClarityEngine *engine, fcitx::InputContext *ic)
    : engine_(engine), ic_(ic) {}

void ClarityState::reset() { clearLookup(); }

void ClarityState::clearLookup() {
    pendingRaw_.clear();
    pendingOptions_.clear();
    ic_->inputPanel().setCandidateList(nullptr);
    ic_->updateUserInterface(fcitx::UserInterfaceComponent::InputPanel);
}

void ClarityState::applyCandidate(std::size_t index) {
    if (pendingOptions_.empty() || index >= pendingOptions_.size()) {
        clearLookup();
        return;
    }
    const auto &[text, label] = pendingOptions_[index];
    FCITX_UNUSED(label);
    ic_->commitString(text);
    if (text != pendingRaw_) {
        std::vector<std::string> args = {"feedback", "--raw", pendingRaw_,
                                         "--preferred", text};
        engine_->runEnginePy(args);
    }
    clearLookup();
}

void ClarityState::showCandidates(const std::string &raw,
                                  const std::vector<std::string> &nbest) {
    pendingRaw_ = raw;
    pendingOptions_ = engine_->fetchCandidates(raw, mode_, nbest);
    if (pendingOptions_.empty()) {
        clearLookup();
        return;
    }
    if (engine_->isAutoApplyTop() || pendingOptions_.size() == 1) {
        applyCandidate(0);
        return;
    }

    auto list = std::make_unique<fcitx::CommonCandidateList>();
    list->setPageSize(9);
    list->setLayoutHint(fcitx::CandidateLayoutHint::Vertical);
    for (std::size_t i = 0; i < pendingOptions_.size() && i < 9; ++i) {
        const auto &[text, label] = pendingOptions_[i];
        list->insert(
            static_cast<int>(i),
            std::make_unique<ClarityCandidateWord>(this, text, label, i, i == 0));
    }
    ic_->inputPanel().setCandidateList(std::move(list));
    ic_->updateUserInterface(fcitx::UserInterfaceComponent::InputPanel);
}

void ClarityState::runVoicePipeline() {
    const auto captured = engine_->captureVoice();
    if (captured.raw.empty()) {
        return;
    }
    showCandidates(captured.raw, captured.nbest);
}

void ClarityState::keyEvent(fcitx::KeyEvent &keyEvent) {
    if (keyEvent.isRelease()) {
        return;
    }

    const auto sym = keyEvent.key().sym();
    const auto states = keyEvent.key().states();

    if (sym == FcitxKey_F9 && !states) {
        keyEvent.filterAndAccept();
        runVoicePipeline();
        return;
    }

    if ((sym == FcitxKey_v || sym == FcitxKey_V) &&
        (states & fcitx::KeyState::Control) &&
        (states & fcitx::KeyState::Shift)) {
        keyEvent.filterAndAccept();
        runVoicePipeline();
        return;
    }

    if (!pendingOptions_.empty()) {
        if (sym == FcitxKey_Return || sym == FcitxKey_KP_Enter ||
            sym == FcitxKey_space) {
            keyEvent.filterAndAccept();
            applyCandidate(0);
            return;
        }
        if (sym == FcitxKey_semicolon) {
            keyEvent.filterAndAccept();
            clearLookup();
            return;
        }
        if (sym >= FcitxKey_1 && sym <= FcitxKey_9) {
            const auto index = static_cast<std::size_t>(sym - FcitxKey_1);
            if (index < pendingOptions_.size()) {
                keyEvent.filterAndAccept();
                applyCandidate(index);
            }
        }
    }
}

ClarityEngine::ClarityEngine(fcitx::Instance *instance)
    : instance_(instance),
      factory_([this](fcitx::InputContext &ic) {
          return new ClarityState(this, &ic);
      }),
      enginePyPath_(resolveEnginePyPath()) {
    instance_->inputContextManager().registerProperty("clarityimeState",
                                                      &factory_);
}

void ClarityEngine::reset(const fcitx::InputMethodEntry &entry,
                          fcitx::InputContextEvent &event) {
    FCITX_UNUSED(entry);
    auto *state = event.inputContext()->propertyFor(&factory_);
    if (state) {
        state->reset();
    }
}

void ClarityEngine::keyEvent(const fcitx::InputMethodEntry &entry,
                             fcitx::KeyEvent &keyEvent) {
    FCITX_UNUSED(entry);
    if (keyEvent.isRelease()) {
        return;
    }
    auto *state = keyEvent.inputContext()->propertyFor(&factory_);
    if (!state) {
        return;
    }
    state->keyEvent(keyEvent);
}

std::string ClarityEngine::runEnginePy(
    const std::vector<std::string> &args) const {
    std::ostringstream cmd;
    cmd << "python3 " << shellQuote(enginePyPath_);
    for (const auto &arg : args) {
        cmd << ' ' << shellQuote(arg);
    }
    cmd << " 2>/dev/null";
    std::array<char, 4096> buffer{};
    std::string output;
    if (FILE *pipe = popen(cmd.str().c_str(), "r")) {
        while (fgets(buffer.data(), static_cast<int>(buffer.size()), pipe)) {
            output += buffer.data();
        }
        pclose(pipe);
    }
    return trim(output);
}

std::vector<std::pair<std::string, std::string>>
ClarityEngine::fetchCandidates(const std::string &raw, const std::string &mode,
                               const std::vector<std::string> &nbest) const {
    std::vector<std::string> args = {"candidates", "--text", raw, "--mode", mode};
    if (!nbest.empty()) {
        std::ostringstream nbestJson;
        nbestJson << '[';
        for (std::size_t i = 0; i < nbest.size(); ++i) {
            if (i) {
                nbestJson << ',';
            }
            nbestJson << '"';
            for (char ch : nbest[i]) {
                if (ch == '"' || ch == '\\') {
                    nbestJson << '\\';
                }
                nbestJson << ch;
            }
            nbestJson << '"';
        }
        nbestJson << ']';
        args.push_back("--nbest");
        args.push_back(nbestJson.str());
    }
    const auto jsonText = runEnginePy(args);
    std::vector<std::pair<std::string, std::string>> out;
    if (jsonText.empty() || jsonText.front() != '[') {
        return out;
    }
    // Minimal JSON parse for [{"text":"..","label":".."}, ...]
    std::size_t pos = 0;
    while ((pos = jsonText.find("\"text\"", pos)) != std::string::npos) {
        pos = jsonText.find(':', pos);
        if (pos == std::string::npos) {
            break;
        }
        pos = jsonText.find('"', pos + 1);
        if (pos == std::string::npos) {
            break;
        }
        const auto textStart = pos + 1;
        const auto textEnd = jsonText.find('"', textStart);
        if (textEnd == std::string::npos) {
            break;
        }
        const auto text = jsonText.substr(textStart, textEnd - textStart);
        std::string label = "option";
        const auto labelPos = jsonText.find("\"label\"", textEnd);
        if (labelPos != std::string::npos) {
            auto lStart = jsonText.find('"', labelPos + 7);
            if (lStart != std::string::npos) {
                lStart += 1;
                const auto lEnd = jsonText.find('"', lStart);
                if (lEnd != std::string::npos) {
                    label = jsonText.substr(lStart, lEnd - lStart);
                }
            }
        }
        out.emplace_back(text, label);
        pos = textEnd + 1;
    }
    return out;
}

VoiceCaptureResult ClarityEngine::captureVoice() const {
    VoiceCaptureResult out;
    const auto jsonText = runEnginePy({"capture"});
    const auto rawPos = jsonText.find("\"raw\"");
    if (rawPos == std::string::npos) {
        return out;
    }
    auto valueStart = jsonText.find('"', rawPos + 5);
    if (valueStart == std::string::npos) {
        return out;
    }
    valueStart += 1;
    const auto valueEnd = jsonText.find('"', valueStart);
    if (valueEnd == std::string::npos) {
        return out;
    }
    out.raw = jsonText.substr(valueStart, valueEnd - valueStart);

    const auto nbestPos = jsonText.find("\"nbest\"");
    if (nbestPos != std::string::npos) {
        auto arrStart = jsonText.find('[', nbestPos);
        const auto arrEnd =
            arrStart == std::string::npos ? std::string::npos
                                          : jsonText.find(']', arrStart);
        if (arrStart != std::string::npos && arrEnd != std::string::npos) {
            std::size_t pos = arrStart + 1;
            while (pos < arrEnd) {
                pos = jsonText.find('"', pos);
                if (pos == std::string::npos || pos >= arrEnd) {
                    break;
                }
                const auto sStart = pos + 1;
                const auto sEnd = jsonText.find('"', sStart);
                if (sEnd == std::string::npos || sEnd > arrEnd) {
                    break;
                }
                const auto item = jsonText.substr(sStart, sEnd - sStart);
                if (!item.empty()) {
                    out.nbest.push_back(item);
                }
                pos = sEnd + 1;
            }
        }
    }
    if (out.nbest.empty() && !out.raw.empty()) {
        out.nbest.push_back(out.raw);
    }
    return out;
}

bool ClarityEngine::isAutoApplyTop() const {
    const auto flag = trim(runEnginePy({"auto-apply-top"}));
    return flag == "true";
}

fcitx::AddonInstance *ClarityEngineFactory::create(fcitx::AddonManager *manager) {
    return new ClarityEngine(manager->instance());
}

FCITX_ADDON_FACTORY(ClarityEngineFactory);
