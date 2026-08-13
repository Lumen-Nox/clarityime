"""Meaning-preserving rewrites — say the SAME thing in words this listener parses faster.

Every rewrite comes from an **audited local table**. There is no generation, so a
substitution can never invent a claim: the worst case is a table entry being wrong,
and the table is human-reviewable in one screen.

Evidence:
  * Word-frequency effect — high-frequency words are recognised faster and
    comprehended more reliably (Rayner & Duffy, 1986, *Memory & Cognition*).
  * Lexical simplification raises comprehension for readers outside the jargon
    community (Crossley, Allen & McNamara, 2011, *Reading in a Foreign Language*).
  * De-nominalisation ("进行讨论" → "讨论") removes an extra predication step
    (Halliday & Martin, 1993, *Writing Science*, on grammatical metaphor).
  * Audience design: speakers should encode for the addressee's knowledge state
    (Clark & Murphy, 1982; Clark & Brennan, 1991 grounding).

Not allowed here (would change the speaker, not the packaging):
  politeness insertion, register shifts (你→您), hedge removal, stance flips.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = [
    "Substitution",
    "JARGON_TABLE",
    "JARGON_TABLE_EN",
    "JARGON_TABLES",
    "supported_jargon_langs",
    "AMBIGUOUS_BLOCKLIST",
    "JARGON_TERMS",
    "jargon_domains",
    "domain_of",
    "count_jargon",
    "apply_substitutions",
    "simplify_jargon",
    "denominalize",
    "tighten_redundancy",
]


@dataclass(frozen=True)
class Substitution:
    src: str
    dst: str
    kind: str  # jargon | nominal | redundancy | lexicon

    def note(self) -> str:
        prefix = {"jargon": "T1", "nominal": "T2", "redundancy": "T3", "lexicon": "T0"}
        return f"{prefix.get(self.kind, 'T?')}:{self.src}→{self.dst}"


# --------------------------------------------------------------------------- #
# T1 — workplace / tech jargon → everyday equivalent
# Only applied when the listener is NOT marked as sharing that jargon.
# --------------------------------------------------------------------------- #

#: term → (everyday equivalent, domain tag it belongs to).
#: A term is only swapped when the listener has NOT declared that domain tag.
#: Domain membership is a property of the *word*, never inferred from the person.
JARGON_TABLE: dict[str, tuple[str, str]] = {
    # -- tech / 互联网 ------------------------------------------------------
    "ddl": ("截止时间", "tech"),
    "DDL": ("截止时间", "tech"),
    "deadline": ("截止时间", "tech"),
    "Deadline": ("截止时间", "tech"),
    "颗粒度": ("细致程度", "tech"),
    "闭环": ("全流程走通", "tech"),
    "迭代": ("改版", "tech"),
    "上线": ("发布", "tech"),
    "降级": ("临时简化", "tech"),
    "兜底": ("备用方案", "tech"),
    "白屏": ("页面空白", "tech"),
    "超时": ("响应太慢", "tech"),
    "埋点": ("数据记录", "tech"),
    "跑通": ("完整走一遍", "tech"),
    # -- business / 职场黑话 -------------------------------------------------
    "抓手": ("切入点", "business"),
    "赋能": ("支持", "business"),
    "复盘": ("回顾", "business"),
    "对齐": ("统一", "business"),
    "拉齐": ("统一", "business"),
    "排期": ("时间安排", "business"),
    "串联": ("串起来", "business"),
    "抽象": ("归纳", "academic"),
    # -- school / 校园 ------------------------------------------------------
    "内卷": ("大家互相加码", "school"),
    "水课": ("要求不高的课", "school"),
    "刷题": ("反复做练习", "school"),
    "补天": ("赶补作业", "school"),
    "社死": ("很尴尬", "school"),
    "摸鱼": ("偷懒", "school"),
    "跑团": ("组队活动", "school"),
    # -- academic ----------------------------------------------------------
    "范式": ("研究框架", "academic"),
    "证伪": ("验证是不是错的", "academic"),
    "样本量": ("参与人数", "academic"),
    "显著": ("差别明显", "academic"),
    "综述": ("文献回顾", "academic"),
    # -- gaming（通用，所有玩游戏的人都懂）----------------------------------
    "开黑": ("组队", "gaming"),
    "上分": ("打排位升段", "gaming"),
    "掉分": ("排位往下掉", "gaming"),
    "单排": ("一个人玩", "gaming"),
    "上头": ("玩得停不下来", "gaming"),
    # -- moba（LOL / 王者：射击玩家听不懂）----------------------------------
    "打野": ("在野区活动的位置", "moba"),
    "开团": ("发起团战", "moba"),
    "补刀": ("补最后一下拿钱", "moba"),
    "送人头": ("白白被击杀", "moba"),
    # -- fps（射击：MOBA 玩家听不懂）----------------------------------------
    "压枪": ("控制后坐力", "fps"),
    "架点": ("守住一个位置", "fps"),
    "报点": ("说出敌人位置", "fps"),
    "落地成盒": ("刚落地就被淘汰", "fps"),
    # -- gacha（抽卡手游）----------------------------------------------------
    "抽卡": ("随机开角色", "gacha"),
    "氪金": ("花钱", "gacha"),
    "保底": ("抽够次数一定出", "gacha"),
    "十连": ("一次抽十个", "gacha"),
    # -- asym_horror（第五人格 / 黎明杀机）----------------------------------
    "监管者": ("追人的一方", "asym_horror"),
    "求生者": ("逃跑的一方", "asym_horror"),
    "守椅": ("守着倒地的人不走", "asym_horror"),
    "遛鬼": ("拖住追人的那方", "asym_horror"),
    "秒倒": ("很快就被打倒", "asym_horror"),
    "BP阶段": ("赛前禁用角色和地图的环节", "asym_horror"),
    "ban位": ("被禁用的名额", "asym_horror"),
    # -- sandbox / sim / strategy / rhythm ----------------------------------
    "红石": ("游戏里的电路装置", "sandbox"),
    "开荒": ("从零开始建", "sandbox"),
    "科技树": ("升级路线", "strategy_game"),
    "全连": ("一次没断", "rhythm_game"),
}

#: English jargon → (plain English, domain). Same rule as the Chinese table:
#: a term only swaps when the listener's declared domains don't cover it.
#: Starter set — grows the same human-reviewed way as the Chinese table
#: (see glossary_mining.py), not auto-translated from JARGON_TABLE_ZH.
JARGON_TABLE_EN: dict[str, tuple[str, str]] = {
    # -- tech --------------------------------------------------------------
    "deadline": ("the due date", "tech"),
    "sprint": ("work cycle", "tech"),
    "standup": ("daily check-in meeting", "tech"),
    "blocker": ("something stopping progress", "tech"),
    "refactor": ("rewrite for clarity", "tech"),
    "PR": ("a proposed code change", "tech"),
    # -- gaming (general) ----------------------------------------------------
    "gg": ("good game", "gaming"),
    "smurf": ("a strong player on a low-level account", "gaming"),
    "tilted": ("frustrated and playing worse because of it", "gaming"),
    "clutch": ("winning at the last possible moment", "gaming"),
    "throw": ("lose on purpose or by a bad mistake", "gaming"),
    # -- moba ----------------------------------------------------------------
    "jungling": ("playing the neutral-monster area", "moba"),
    "gank": ("ambush someone with extra teammates", "moba"),
    "feeding": ("dying over and over, giving the enemy an advantage", "moba"),
    # -- fps -------------------------------------------------------------
    "camping": ("staying in one spot waiting for enemies", "fps"),
    "spray and pray": ("firing without aiming carefully", "fps"),
    "wallbang": ("shooting an enemy through a wall", "fps"),
    # -- gacha -------------------------------------------------------------
    "pity": ("a guaranteed pull after enough tries", "gacha"),
    "whale": ("someone who spends a lot of money", "gacha"),
    "reroll": ("restart the account for a better first pull", "gacha"),
}

#: Every table currently curated, keyed by reading language (`reads_<code>`
#: minus the prefix). Adding a language means adding one entry here — the
#: engine itself does not need to change.
JARGON_TABLES: dict[str, dict[str, tuple[str, str]]] = {
    "zh": JARGON_TABLE,
    "en": JARGON_TABLE_EN,
}


def supported_jargon_langs() -> tuple[str, ...]:
    return tuple(JARGON_TABLES)

#: 只收「多字、放在日常句子里不会误伤」的词。
#: 反例：「毕业」在抽卡圈=练满，在校园=真的毕业；「肝」既是器官也是动词；
#: 「屠夫」在第五人格是监管者，在生活里是真的屠夫。这类一律不收 —— 一旦收了，
#: 系统会在错误的语境里把用户的原话改成另一个意思，那比不翻译严重得多。
AMBIGUOUS_BLOCKLIST: frozenset[str] = frozenset(
    {"毕业", "肝", "屠夫", "深渊", "宣战", "存档", "判定", "野区", "抽象化"}
)

#: Back-compat flat view (term → plain), Chinese table only.
JARGON_TERMS: dict[str, str] = {k: v[0] for k, v in JARGON_TABLE.items()}

# Longest-first per language so compounds match before their parts.
_JARGON_ORDER: dict[str, list[str]] = {
    lang: sorted(table, key=len, reverse=True) for lang, table in JARGON_TABLES.items()
}
_JARGON_SCAN: dict[str, "re.Pattern[str]"] = {
    lang: re.compile("|".join(re.escape(t) for t in order))
    for lang, order in _JARGON_ORDER.items()
    if order
}


def count_jargon(text: str, lang: str = "zh") -> int:
    scan = _JARGON_SCAN.get(lang)
    return len(scan.findall(text)) if scan else 0


def jargon_domains(lang: str = "zh") -> set[str]:
    table = JARGON_TABLES.get(lang, {})
    return {domain for _, domain in table.values()}


def domain_of(term: str, lang: str = "zh") -> str | None:
    """Which domain a jargon *term* (the ``src`` of a T1 substitution) belongs
    to, for attributing feedback back to a domain. ``None`` if not a jargon
    table entry (e.g. T2/T3 substitutions carry no domain)."""
    table = JARGON_TABLES.get(lang, {})
    entry = table.get(term)
    return entry[1] if entry else None


# --------------------------------------------------------------------------- #
# T2 — de-nominalisation: light verb + noun → plain verb
# --------------------------------------------------------------------------- #

NOMINAL_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"进行(一[次下个]?)?", ""),
    (r"做(一[次下个]?)(?=[\u4e00-\u9fff]{2,})", ""),
    (r"作出", ""),
    (r"予以", ""),
    (r"给予", ""),
    (r"实施", ""),
)

# 「做一个降级的处理」→「降级处理」: strip the empty 的 between N and 处理/方案
REDUNDANT_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"(?<=[\u4e00-\u9fff])的(?=处理|方案|工作|操作)", ""),
    (r"的话(?=[，,。；;]|$)", ""),
    (r"这样子", "这样"),
    (r"什么的(?=[，,。；;]|$)", ""),
)


# --------------------------------------------------------------------------- #
# Application
# --------------------------------------------------------------------------- #


def apply_substitutions(text: str, subs: list[Substitution]) -> str:
    out = text
    for s in subs:
        out = out.replace(s.src, s.dst)
    return out


def simplify_jargon(
    text: str,
    *,
    known_domains: frozenset[str] | set[str] | None = None,
    knows_jargon: bool | None = None,
    lang: str = "zh",
) -> tuple[str, list[Substitution]]:
    """Swap a term only when the listener has NOT declared that term's domain.

    ``known_domains`` comes straight from the listener's declared domain tags.
    A term in a domain they own is left alone (audience design, Clark & Murphy
    1982): translating 「排期」for someone tagged ``business`` makes it *harder*.

    ``lang`` picks which curated table to scan (the speaker's reading
    language, ``reads_<lang>``) — never auto-translated between languages.
    """
    if knows_jargon:  # legacy switch: treat as owning every domain
        return text, []
    table = JARGON_TABLES.get(lang)
    if not table:
        return text, []
    owned = frozenset(known_domains or ())
    subs: list[Substitution] = []
    out = text
    for term in _JARGON_ORDER[lang]:
        dst, domain = table[term]
        if domain in owned or term not in out:
            continue
        out = out.replace(term, dst)
        subs.append(Substitution(term, dst, "jargon"))
    return out, subs


def denominalize(text: str) -> tuple[str, list[Substitution]]:
    """「进行一次复盘」→「复盘」— drop the empty light verb."""
    subs: list[Substitution] = []
    out = text
    for pattern, repl in NOMINAL_PATTERNS:
        for m in list(re.finditer(pattern, out)):
            src = m.group(0)
            if not src:
                continue
            new = out.replace(src, repl, 1)
            if new != out:
                subs.append(Substitution(src, repl, "nominal"))
                out = new
    return out, subs


def tighten_redundancy(text: str) -> tuple[str, list[Substitution]]:
    subs: list[Substitution] = []
    out = text
    for pattern, repl in REDUNDANT_PATTERNS:
        for m in list(re.finditer(pattern, out)):
            src = m.group(0)
            if not src:
                continue
            new = out.replace(src, repl, 1)
            if new != out:
                subs.append(Substitution(src, repl, "redundancy"))
                out = new
    return out, subs
