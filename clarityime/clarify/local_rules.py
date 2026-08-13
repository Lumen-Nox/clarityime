"""Local clarification rules — help *understanding*, never summarize.

Design contract:
  - Preserve propositions, hedging, attitude, and detail (还行 / 可能 / 感觉 …).
  - Remove only oral *noise* (嗯、那个啥、like), not meaning-bearing words (其实、比较).
  - Structured mode = readable layout (paragraph / sentence breaks), not bullet summaries.
  - Contact mode = register & emotional fit for *this person*, not shorter text.
"""

from __future__ import annotations

import re

# Pure oral noise — safe to strip (no propositional content)
FILLERS = (
    "嗯",
    "啊",
    "呃",
    "那个",
    "就是",
    "你知道",
    "怎么说呢",
    "对对对",
    " basically",
    " like",
    " um",
    " uh",
    " you know",
)

# Only strip when used as standalone social openers (not mid-sentence 请问)
GREETINGS_SOCIAL = ("你好", "您好", "嗨", "hello", "hi")

ORAL_CLAUSE_JUNK = frozenset(
    {
        "啥",
        "那个啥",
        "嗯",
        "啊",
        "呃",
        "那个",
        "就是",
        "然后",
        "我跟你说",
        "我跟你说啊",
        "你知道吗",
        "你知道",
        "怎么说呢",
        "对对对",
    }
)

CLAUSE_BREAKERS = ("因为", "但是", "所以", "而且", "不过", "然而")

# Attitude / hedging — never remove or flip polarity
HEDGING_MARKERS = (
    "还行",
    "可能",
    "大概",
    "也许",
    "比较",
    "相对",
    "感觉",
    "觉得",
    "挺",
    "稍微",
    "有点",
    "似乎",
    "好像",
    "未必",
    "不一定",
    "kind of",
    "sort of",
    "maybe",
    "probably",
    "might",
)

ENGLISH_FILLER_PATTERN = re.compile(
    r"\b(like|um|uh|you know|i mean)\b",
    re.IGNORECASE,
)

FORMAL_RELATIONSHIPS = frozenset({"老师", "教授", "上级", "老板", "mentor"})
DECLINE_MARKERS = ("去不了", "不能", "没法", "晚一天", "延期", "推迟", "请假", "缺席")
APOLOGY_MARKERS = ("不好意思", "抱歉", "对不起", "打扰")


def _dedupe_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _is_mostly_english(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    ascii_letters = sum(1 for c in letters if ord(c) < 128)
    return ascii_letters / len(letters) >= 0.7


_LEADING_NOISE = re.compile(
    r"^(?:嗯+|啊+|呃+|那个啥|那个|就是|然后|对对对|你知道吗|你知道|怎么说呢"
    r"|我跟你说啊|我跟你说|啥)[，,、\s]*"
)


def _strip_fillers(text: str) -> str:
    out = text.strip()
    if _is_mostly_english(out):
        out = ENGLISH_FILLER_PATTERN.sub(" ", out)
    else:
        # Strip the whole leading noise chain (「那个，就是…」), never mid-sentence.
        while True:
            stripped = _LEADING_NOISE.sub("", out, count=1)
            if stripped == out:
                break
            out = stripped
    out = re.sub(r"^就是说\s*", "", out)
    out = re.sub(r"^我想说(?=能不能|能否|可不可以|是否可以|怎么|什么|哪)", "", out)
    out = re.sub(r"^然后[，,、]?\s*", "", out)
    # 「我想说就是…」→「我想说…」: drop only the filler, keep the speaker's framing
    out = re.sub(r"^(我想说|我想问)就是[，,]?\s*", r"\1", out)
    out = re.sub(r"^我想就是说[，,]?\s*", "", out)
    return _dedupe_spaces(out)


_VOCATIVE = r"(你好|您好|嗨|老师|教授|老板|同学|大家|hello|hi)"
_POST_VOCATIVE_NOISE = re.compile(
    rf"^{_VOCATIVE}[，,、]?\s*(?:那个|就是|嗯|啊|呃)+[，,、]?\s*",
    re.IGNORECASE,
)


def _strip_post_vocative_noise(text: str, notes: list[str]) -> str:
    """「你好，就是我想问…」→「你好，我想问…」— filler after a vocative only."""
    out = _POST_VOCATIVE_NOISE.sub(lambda m: m.group(1) + "，", text)
    if out != text:
        notes.append("drop_oral:post_vocative")
    return out


def _strip_oral_framing(text: str, notes: list[str]) -> str:
    out = text
    patterns = (
        (r"^(那个啥|啥)[，,、\s]+", "drop_oral:啥"),
        (r"^我跟你说啊?[，,、\s]+", "drop_oral:我跟你说"),
        (r"^你知道[，,、]?\s*", "drop_oral:你知道"),
    )
    for pat, note in patterns:
        new = re.sub(pat, "", out)
        if new != out:
            notes.append(note)
            out = new
    return out.strip()


def _strip_social_greeting(text: str, notes: list[str]) -> str:
    """Optional: drop bare greeting prefix only (保留后面全部内容)."""
    out = text
    for g in GREETINGS_SOCIAL:
        if out.lower().startswith(g.lower()):
            out = out[len(g) :].lstrip("，,、. ")
            notes.append(f"drop_social:{g}")
            break
    return out.strip()


def _insert_clause_breaks(text: str, notes: list[str]) -> str:
    out = text
    for word in CLAUSE_BREAKERS:
        out = re.sub(rf"(?<=[^，,；;]){word}", f"，{word}", out)
    out = re.sub(r"(?<=[^，,；;])然后(?=[^，,])", "，然后", out)
    out = re.sub(r"(?<=[^，,；;])就是(?=[^，,])", "，就是", out)
    # 「不是A是B」— mark the correction, it is the whole point of the sentence
    out = re.sub(r"(不是[^，,]{2,12}?)是(?=[^，,])", r"\1，是", out)
    if "，因为" in out or "，但是" in out or "，而且" in out:
        notes.append("clause_breaks")
    out = re.sub(r"，然后", "，", out)
    return out


_SUBJECT_BREAK = re.compile(
    r"(?<=[了对完行吧啊过来去到上下]) *(?=(?:我们|我|你们|你|他们|他|她|它们|它|大家|咱们)"
    r"(?![的和跟给让帮们]))"
)


def _break_before_subject(text: str, notes: list[str]) -> str:
    """ASR run-ons have no commas — restore clause edges before a new subject."""
    if "，" in text and len(text) < 30:
        return text
    out = _SUBJECT_BREAK.sub("，", text)
    out = re.sub(r"，{2,}", "，", out)
    if out != text:
        notes.append("clause_breaks:subject")
    return out


def _trim_redundant_pronouns(text: str, notes: list[str]) -> str:
    out = re.sub(
        r"(接口|系统|服务|页面|模块|功能|项目|bug|Bug|BUG|这个|那个)(它|它们)",
        r"\1",
        text,
        flags=re.IGNORECASE,
    )
    if out != text:
        notes.append("drop_redundant:它")
    return out


def _split_runon(text: str) -> str:
    """Long oral chains → separate sentences; every clause kept."""
    if len(text) < 36:
        return text
    parts = re.split(r"([，,；;])", text)
    if len(parts) < 3:
        return text
    merged: list[str] = []
    buf = ""
    for part in parts:
        buf += part
        if part in "，,；" and len(buf) > 18:
            merged.append(buf.rstrip("，,；; "))
            buf = ""
    if buf:
        merged.append(buf)
    if len(merged) >= 2:
        return "。".join(p.rstrip("。！？") for p in merged if p.strip()) + "。"
    return text


def _punctuate(text: str) -> str:
    t = text.strip()
    if not t:
        return t
    if t[-1] in "。！？.!?":
        return t
    if _is_mostly_english(t):
        lower = t.lower()
        if any(
            lower.startswith(w)
            for w in (
                "can ",
                "could ",
                "would ",
                "do ",
                "did ",
                "is ",
                "are ",
                "what ",
                "how ",
                "when ",
                "where ",
                "why ",
            )
        ) or "?" in t:
            return t + "?"
        return t + "."
    if any(w in t for w in ("吗", "么", "是不是", "能不能", "可不可以", "能否", "什么", "怎么", "哪", "谁")):
        return t + "？"
    return t + "。"


def _merge_nbest(candidates: list[str]) -> str:
    """Prefer the longest n-best when it carries more detail."""
    if not candidates:
        return ""
    primary = candidates[0]
    for alt in candidates[1:]:
        if len(alt) > len(primary) + 6:
            primary = alt
            break
    return primary


def _clarify_core(
    text: str,
    candidates: list[str] | None,
    *,
    drop_greeting: bool,
) -> tuple[str, list[str]]:
    notes: list[str] = []
    base = _merge_nbest(candidates or [text])
    out = _strip_fillers(base)
    out = _strip_post_vocative_noise(out, notes)
    out = _strip_oral_framing(out, notes)
    if drop_greeting:
        out = _strip_social_greeting(out, notes)
    out = _insert_clause_breaks(out, notes)
    out = _break_before_subject(out, notes)
    out = _trim_redundant_pronouns(out, notes)
    out = _split_runon(out)
    out = _punctuate(out)
    notes.append("preserve_detail")
    return out, notes


def _sentences(text: str) -> list[str]:
    body = text.rstrip("。！？.!?")
    if not body:
        return []
    parts = re.split(r"(?<=[。！？!?])\s*", body)
    out = [p.strip() for p in parts if p.strip()]
    if out:
        return out
    return [body]


def paragraph_variant(primary: str) -> str | None:
    """Same words — blank line between sentences for easier parsing."""
    sents = _sentences(primary)
    if len(sents) < 2:
        return None
    joined = "\n\n".join(s.rstrip("。！？.!?") + _terminal_for(s) for s in sents)
    if joined.replace("\n", "") == primary.replace("\n", ""):
        return None
    return joined


def _terminal_for(sentence: str) -> str:
    if not sentence:
        return "。"
    if sentence[-1] in "。！？.!?":
        return ""
    if _is_mostly_english(sentence):
        return "?" if "?" in sentence or sentence.lower().startswith(("can ", "could ", "what ", "how ")) else "."
    return "？" if any(w in sentence for w in ("吗", "么", "能不能", "什么", "怎么", "哪", "谁")) else "。"


def continuous_variant(primary: str) -> str | None:
    """Flatten paragraph layout back to one block — same content."""
    flat = re.sub(r"\n+", "", primary)
    if flat != primary:
        return flat
    return None


def preserve_original(text: str, candidates: list[str] | None = None) -> tuple[str, list[str]]:
    """Speaker faithful line — only ASR/oral cleanup, no register rewrite."""
    out, notes = _clarify_core(text, candidates, drop_greeting=False)
    notes.insert(0, "role:speaker_original")
    return out, notes


def clarify_default(text: str, candidates: list[str] | None = None) -> tuple[str, list[str]]:
    """Alias: speaker original (legacy name)."""
    return preserve_original(text, candidates)


def clarify_for_structured(text: str, candidates: list[str] | None = None) -> tuple[str, list[str]]:
    """Readable layout for a general listener — comprehension ops, no summary."""
    from clarityime.cerome.listener_presets import NEUTRAL
    from clarityime.clarify.listener_adapt import adapt_for_listener

    out, notes = preserve_original(text, candidates)
    notes.insert(0, "clarify:structured")
    adapted, notes_l = adapt_for_listener(out, NEUTRAL)
    return adapted, notes + notes_l


def clarify_for_ai(text: str, candidates: list[str] | None = None) -> tuple[str, list[str]]:
    return clarify_for_structured(text, candidates)


def _has_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(m in text for m in markers)


def _is_decline_statement(text: str) -> bool:
    if any(x in text for x in ("能不能", "可不可以", "是否可以", "能否")):
        return False
    return _has_any(text, DECLINE_MARKERS)


def clarify_dual_for_listener(
    text: str,
    cerome: "CeromeHumanProfile",
    candidates: list[str] | None = None,
    *,
    lexicon: str = "",
) -> tuple[str, str, list[str]]:
    """Return (original, for_listener) — same propositions; listener layout only."""
    from clarityime.cerome.human import CeromeHumanProfile
    from clarityime.clarify.listener_adapt import adapt_for_listener

    assert isinstance(cerome, CeromeHumanProfile)
    original, notes_o = preserve_original(text, candidates)
    for_listener, notes_l = adapt_for_listener(
        original,
        cerome,
        lexicon=lexicon,
    )
    return original, for_listener, notes_o + notes_l


def clarify_for_contact(
    text: str,
    hints: dict[str, str],
    candidates: list[str] | None = None,
) -> tuple[str, list[str]]:
    """Deprecated single-output path — returns for_listener only (use clarify_dual)."""
    from clarityime.cerome.human import CeromeHumanProfile, cerome_from_contact
    from clarityime.models import ContactProfile

    stub = ContactProfile(
        id=None,
        name=hints.get("name", ""),
        relationship=hints.get("relationship", ""),
        style_notes=hints.get("style", ""),
        preferred_words=hints.get("words", ""),
        age_hint=hints.get("age", ""),
        comprehension_notes=hints.get("comprehension", ""),
    )
    cerome = cerome_from_contact(stub)
    _, for_listener, notes = clarify_dual_for_listener(
        text,
        cerome,
        candidates,
        lexicon=hints.get("words", ""),
    )
    notes.insert(0, "clarify:contact")
    return for_listener, notes
