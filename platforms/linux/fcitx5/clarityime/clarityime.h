/*
 * ClarityIME — Fcitx5 voice clarify input method
 * SPDX-License-Identifier: MIT
 */
#ifndef CLARITYIME_FCITX5_CLARITYIME_H_
#define CLARITYIME_FCITX5_CLARITYIME_H_

#include <fcitx/addonfactory.h>
#include <fcitx/candidatelist.h>
#include <fcitx/inputcontextproperty.h>
#include <fcitx/inputmethodengine.h>
#include <fcitx/instance.h>
#include <fcitx/text.h>

#include <memory>
#include <string>
#include <utility>
#include <vector>

class ClarityEngine;

class ClarityState {
public:
    ClarityState(ClarityEngine *engine, fcitx::InputContext *ic);

    void keyEvent(fcitx::KeyEvent &keyEvent);
    void reset();
    void runVoicePipeline();
    void showCandidates(const std::string &raw,
                        const std::vector<std::string> &nbest = {});
    void applyCandidate(std::size_t index);
    void clearLookup();

    fcitx::InputContext *inputContext() const { return ic_; }

private:
    ClarityEngine *engine_;
    fcitx::InputContext *ic_;
    std::string mode_ = "default";
    std::string pendingRaw_;
    std::vector<std::pair<std::string, std::string>> pendingOptions_;
};

class ClarityCandidateWord : public fcitx::CandidateWord {
public:
    ClarityCandidateWord(ClarityState *state, std::string commitText,
                         std::string label, std::size_t index, bool isTop);

    void select(fcitx::InputContext *inputContext) override;

private:
    ClarityState *state_;
    std::size_t index_;
};

struct VoiceCaptureResult {
    std::string raw;
    std::vector<std::string> nbest;
};

class ClarityEngine : public fcitx::InputMethodEngineV2 {
public:
    explicit ClarityEngine(fcitx::Instance *instance);

    void keyEvent(const fcitx::InputMethodEntry &entry,
                  fcitx::KeyEvent &keyEvent) override;
    void reset(const fcitx::InputMethodEntry &entry,
               fcitx::InputContextEvent &event) override;

    std::string runEnginePy(const std::vector<std::string> &args) const;
    std::vector<std::pair<std::string, std::string>>
    fetchCandidates(const std::string &raw, const std::string &mode,
                    const std::vector<std::string> &nbest) const;
    VoiceCaptureResult captureVoice() const;
    bool isAutoApplyTop() const;

private:
    fcitx::Instance *instance_;
    fcitx::FactoryFor<ClarityState> factory_;
    std::string enginePyPath_;
};

class ClarityEngineFactory : public fcitx::AddonFactory {
    fcitx::AddonInstance *create(fcitx::AddonManager *manager) override;
};

#endif
