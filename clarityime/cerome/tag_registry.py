"""Tag registry — the vocabulary people actually use to describe themselves.

Use tags that real people recognize (bilingual labels). Design rules:

1. **A tag never implies a tag from another family**, with exactly one
   documented exception: personality/self-report tags may imply PROCESSING
   tags (how you take information in), because that is what those instruments
   measure. They may **never** imply DOMAIN tags — knowing someone is INTJ
   tells you nothing about whether they know 「排期」.
2. Vocabulary you own comes from what you *do* (HOBBY, DOMAIN, SOURCE), which
   is why those families — and only those — carry ``grants``.
3. Every tag is bilingual. Labels switch; the speaker's words never do.

Families
--------
mbti        16 types — the single most common self-label in CN and US alike
function    八维 / cognitive functions (Ni Ne Si Se Ti Te Fi Fe)
bigfive     OCEAN, high/low — the instrument academics actually trust
enneagram   九型 1–9
selfdesc    how this person describes themselves (metaphor? data? story?)
source      where their self-knowledge came from — predicts their vocabulary
hobby       爱好 — grants real vocabulary domains
domain      professional / study fields
register    how they themselves talk
relation    the tie to the speaker
lang        reading language
processing  derived: how to lay text out for them
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "TagDef",
    "REGISTRY",
    "FAMILIES",
    "MBTI_FUNCTIONS",
    "tag_def",
    "catalog",
    "label",
    "expand",
    "search",
    "quick_setup",
    "SETUP_STEPS",
]


@dataclass(frozen=True)
class TagDef:
    id: str
    family: str
    zh: str
    en: str
    note_zh: str = ""
    note_en: str = ""
    #: PROCESSING tags this one implies. Never a domain.
    implies: tuple[str, ...] = ()
    #: Jargon domains this tag means the person already owns.
    grants: tuple[str, ...] = ()
    #: Roll-up: picking a child also counts as picking the parent.
    parent: str = ""
    #: Show in the short list. Everything else is search-only.
    common: bool = False
    #: What people actually type when looking for this (中文别名/英文缩写/俗称).
    aliases: tuple[str, ...] = ()

    def text(self, lang: str = "zh") -> str:
        return self.zh if lang.startswith("zh") else self.en

    def note(self, lang: str = "zh") -> str:
        return self.note_zh if lang.startswith("zh") else self.note_en

    def haystack(self) -> str:
        return " ".join((self.id, self.zh, self.en, *self.aliases)).lower()


_D: list[TagDef] = []


def _t(*a, **kw) -> None:
    _D.append(TagDef(*a, **kw))


# --------------------------------------------------------------------------- #
# PROCESSING — the only family rules act on directly
# --------------------------------------------------------------------------- #

_t("conclusion_first", "processing", "先给结论", "claim first",
   "先说判断/请求，原因放后面", "state the claim before the reasons")
_t("cause_explicit", "processing", "因果说清", "signal causality",
   "因为/所以/但是 单独成行", "give causal and contrast clauses their own line")
_t("short_chunks", "processing", "短句短块", "short chunks",
   "一次别塞太多信息", "small units, low working-memory load")
_t("long_chunks", "processing", "长句无妨", "long chunks",
   "能一口气读完长句", "tolerates longer units")
_t("tone_visible", "processing", "语气要看得见", "keep tone visible",
   "语气词和对冲词不能删", "particles and hedges stay")
_t("no_padding", "processing", "别绕", "no padding",
   "客套和语气词可以去掉", "drop softeners, keep hedges")
_t("context_first", "processing", "先给背景", "context first",
   "先铺垫再转折", "background before the pivot")
_t("value_order", "processing", "按在意的排序", "order by what they value",
   "支撑句按他在意的维度排", "order supports by what they weigh")
_t("sequence_explicit", "processing", "步骤分行", "number the steps",
   "先/然后/最后 各占一行", "one step per line")
_t("concrete_first", "processing", "先给具体例子", "concrete first",
   "带数字/实例的句子提前", "clauses with numbers or instances lead")
_t("define_terms", "processing", "术语一律解释", "always define terms",
   "不管懂不懂都换成白话", "translate jargon regardless of domain")

# --------------------------------------------------------------------------- #
# FUNCTION — 八维. The mechanism behind the MBTI mapping.
# --------------------------------------------------------------------------- #

_FUNC = {
    "Ni": ("内倾直觉", "Introverted Intuition", ("context_first",),
           "先要整体意思，再看细节", "wants the whole picture before parts"),
    "Ne": ("外倾直觉", "Extraverted Intuition", ("short_chunks",),
           "跳读、发散，短行更好扫", "scans and branches; short lines read faster"),
    "Si": ("内倾感觉", "Introverted Sensing", ("sequence_explicit", "cause_explicit"),
           "按顺序对照过往经验", "checks against remembered sequence"),
    "Se": ("外倾感觉", "Extraverted Sensing", ("concrete_first", "short_chunks"),
           "要具体、当下、看得见的", "wants concrete and immediate"),
    "Ti": ("内倾思考", "Introverted Thinking", ("cause_explicit",),
           "要内部逻辑自洽", "checks internal consistency"),
    "Te": ("外倾思考", "Extraverted Thinking", ("conclusion_first", "no_padding"),
           "先要结论和可执行项", "wants the conclusion and the action"),
    "Fi": ("内倾情感", "Introverted Feeling", ("tone_visible",),
           "语气就是信息本身", "tone is part of the message"),
    "Fe": ("外倾情感", "Extraverted Feeling", ("tone_visible", "context_first"),
           "关注关系和场面", "tracks the relational frame"),
}
for _fid, (_z, _e, _imp, _nz, _ne) in _FUNC.items():
    _t(f"fn_{_fid}", "function", f"{_fid}（{_z}）", f"{_fid} ({_e})", _nz, _ne, implies=_imp)

#: type → (dominant, auxiliary, tertiary, inferior)
MBTI_FUNCTIONS: dict[str, tuple[str, str, str, str]] = {
    "INTJ": ("Ni", "Te", "Fi", "Se"),
    "INTP": ("Ti", "Ne", "Si", "Fe"),
    "ENTJ": ("Te", "Ni", "Se", "Fi"),
    "ENTP": ("Ne", "Ti", "Fe", "Si"),
    "INFJ": ("Ni", "Fe", "Ti", "Se"),
    "INFP": ("Fi", "Ne", "Si", "Te"),
    "ENFJ": ("Fe", "Ni", "Se", "Ti"),
    "ENFP": ("Ne", "Fi", "Te", "Si"),
    "ISTJ": ("Si", "Te", "Fi", "Ne"),
    "ISFJ": ("Si", "Fe", "Ti", "Ne"),
    "ESTJ": ("Te", "Si", "Ne", "Fi"),
    "ESFJ": ("Fe", "Si", "Ne", "Ti"),
    "ISTP": ("Ti", "Se", "Ni", "Fe"),
    "ISFP": ("Fi", "Se", "Ni", "Te"),
    "ESTP": ("Se", "Ti", "Fe", "Ni"),
    "ESFP": ("Se", "Fi", "Te", "Ni"),
}

_MBTI_ZH = {
    "INTJ": "建筑师", "INTP": "逻辑学家", "ENTJ": "指挥官", "ENTP": "辩论家",
    "INFJ": "提倡者", "INFP": "调停者", "ENFJ": "主人公", "ENFP": "竞选者",
    "ISTJ": "物流师", "ISFJ": "守卫者", "ESTJ": "总经理", "ESFJ": "执政官",
    "ISTP": "鉴赏家", "ISFP": "探险家", "ESTP": "企业家", "ESFP": "表演者",
}
_MBTI_EN = {
    "INTJ": "Architect", "INTP": "Logician", "ENTJ": "Commander", "ENTP": "Debater",
    "INFJ": "Advocate", "INFP": "Mediator", "ENFJ": "Protagonist", "ENFP": "Campaigner",
    "ISTJ": "Logistician", "ISFJ": "Defender", "ESTJ": "Executive", "ESFJ": "Consul",
    "ISTP": "Virtuoso", "ISFP": "Adventurer", "ESTP": "Entrepreneur", "ESFP": "Entertainer",
}

for _mb, _stack in MBTI_FUNCTIONS.items():
    # Only dominant + auxiliary drive layout; tertiary/inferior are too weak
    _imp = tuple(dict.fromkeys(_FUNC[_stack[0]][2] + _FUNC[_stack[1]][2]))
    _t(
        f"mbti_{_mb.lower()}", "mbti",
        f"{_mb}·{_MBTI_ZH[_mb]}", f"{_mb} · {_MBTI_EN[_mb]}",
        f"主导 {_stack[0]}，辅助 {_stack[1]}",
        f"dominant {_stack[0]}, auxiliary {_stack[1]}",
        implies=_imp,
        common=True,
        aliases=(_mb.lower(), _MBTI_EN[_mb].lower()),
    )

# --------------------------------------------------------------------------- #
# BIG FIVE — the instrument with the strongest psychometric record
# (Costa & McCrae 1992; John & Srivastava 1999)
# --------------------------------------------------------------------------- #

_BIG5 = [
    ("openness_high", "开放性高", "High openness", ("long_chunks",),
     "接受抽象和新说法", "tolerates abstraction and novelty"),
    ("openness_low", "开放性低", "Low openness", ("concrete_first", "define_terms"),
     "要熟悉的说法和具体例子", "wants familiar wording and concrete cases"),
    ("conscientious_high", "尽责性高", "High conscientiousness",
     ("sequence_explicit", "cause_explicit"),
     "按步骤和依据来读", "reads for steps and justification"),
    ("conscientious_low", "尽责性低", "Low conscientiousness", ("short_chunks",),
     "长清单会放弃", "long lists get abandoned"),
    ("extravert_high", "外向性高", "High extraversion", ("short_chunks",),
     "节奏快，短行更跟得上", "fast pace, short lines keep up"),
    ("extravert_low", "外向性低", "Low extraversion", ("long_chunks",),
     "愿意慢慢读完整段", "will read a full paragraph"),
    ("agreeable_high", "宜人性高", "High agreeableness", ("tone_visible",),
     "语气缺失会读成冷淡", "missing tone reads as coldness"),
    ("agreeable_low", "宜人性低", "Low agreeableness", ("no_padding", "conclusion_first"),
     "客套会被当噪音", "social padding reads as noise"),
    ("neurotic_high", "神经质高", "High neuroticism", ("tone_visible", "short_chunks"),
     "信息量大会焦虑，语气很重要", "load raises anxiety; tone matters"),
    ("neurotic_low", "神经质低", "Low neuroticism", (), "", ""),
]
for _id, _z, _e, _imp, _nz, _ne in _BIG5:
    _t(_id, "bigfive", _z, _e, _nz, _ne, implies=_imp)

# --------------------------------------------------------------------------- #
# ENNEAGRAM — 九型. Very common in CN self-description.
# --------------------------------------------------------------------------- #

_ENNEA = [
    ("1", "完美型", "Reformer", ("cause_explicit",)),
    ("2", "助人型", "Helper", ("tone_visible",)),
    ("3", "成就型", "Achiever", ("conclusion_first", "no_padding")),
    ("4", "自我型", "Individualist", ("tone_visible", "context_first")),
    ("5", "思考型", "Investigator", ("cause_explicit", "long_chunks")),
    ("6", "怀疑型", "Loyalist", ("cause_explicit", "sequence_explicit")),
    ("7", "活跃型", "Enthusiast", ("short_chunks",)),
    ("8", "领袖型", "Challenger", ("conclusion_first", "no_padding")),
    ("9", "和平型", "Peacemaker", ("tone_visible", "context_first")),
]
for _n, _z, _e, _imp in _ENNEA:
    _t(f"ennea_{_n}", "enneagram", f"{_n}号·{_z}", f"Type {_n} · {_e}", implies=_imp)

# --------------------------------------------------------------------------- #
# SELFDESC — 「他们一般会怎么描述自己？用什么方法描述？」
# This predicts what an explanation has to look like to feel convincing.
# --------------------------------------------------------------------------- #

_SELF = [
    ("desc_by_metaphor", "爱用比喻描述自己", "describes self in metaphors",
     ("concrete_first",), "抽象说法要配一个形象", "abstractions need an image"),
    ("desc_by_data", "爱用数据/测评描述自己", "describes self with data",
     ("cause_explicit", "conclusion_first"), "要看到依据和数字", "wants evidence and numbers"),
    ("desc_by_story", "爱用故事经历描述自己", "describes self through stories",
     ("context_first",), "先讲情境才听得进去", "needs the situation first"),
    ("desc_by_label", "爱用标签描述自己", "describes self with labels",
     ("short_chunks",), "习惯短标签，长论述会跳过", "used to short labels"),
    ("desc_by_contrast", "靠「我不是…」描述自己", "defines self by contrast",
     ("cause_explicit",), "对比结构最好懂", "contrast structures land best"),
    ("desc_reluctant", "不太爱描述自己", "reluctant self-describer",
     ("no_padding",), "别逼他表态，信息给足", "give information, not prompts"),
]
for _id, _z, _e, _imp, _nz, _ne in _SELF:
    _t(_id, "selfdesc", _z, _e, _nz, _ne, implies=_imp)

# --------------------------------------------------------------------------- #
# SOURCE — 「他们是从哪里认识到这些的？」
# Where the self-knowledge came from predicts which vocabulary is already theirs.
# --------------------------------------------------------------------------- #

_SOURCE = [
    ("src_test_site", "网上测过 16personalities", "took an online MBTI test",
     (), ("psych_pop",), "认识 MBTI 词汇，不认识学术术语", "knows pop MBTI, not academic terms"),
    ("src_psych_course", "上过心理学课", "studied psychology", (), ("psych_pop", "academic"),
     "能读懂效应量、显著这类词", "can read effect size, significance"),
    ("src_social_media", "小红书/抖音/TikTok 上看的", "learned it on social media",
     ("short_chunks", "concrete_first"), ("psych_pop",),
     "熟悉短平快的说法", "used to short punchy framing"),
    ("src_friends", "朋友聊起来才知道的", "heard it from friends",
     ("define_terms",), (), "术语要解释", "terms need spelling out"),
    ("src_books", "自己读书读到的", "read it in books", ("long_chunks",), ("academic",),
     "读得下长论证", "will follow a long argument"),
    ("src_therapy", "咨询师/测评机构说的", "from a counsellor", ("tone_visible",), ("psych_pop",),
     "对措辞敏感", "sensitive to wording"),
    ("src_none", "没接触过这些", "no exposure", ("define_terms",), (),
     "所有人格术语都要翻译", "translate every personality term"),
]
for _id, _z, _e, _imp, _gr, _nz, _ne in _SOURCE:
    _t(_id, "source", _z, _e, _nz, _ne, implies=_imp, grants=_gr)

# --------------------------------------------------------------------------- #
# HOBBY — 「他们经常有什么爱好？」 Hobbies are where real vocabulary comes from.
# --------------------------------------------------------------------------- #

_HOBBY = [
    # (id, zh, en, grants, common, aliases)
    ("hobby_gaming", "打游戏", "gaming", ("gaming",), True, ("游戏", "game", "玩游戏")),
    ("hobby_esports", "看电竞", "esports", ("gaming",), False, ("电竞", "比赛", "lpl")),
    ("hobby_anime", "二次元/动漫", "anime & manga", ("fandom",), True, ("动漫", "番", "acg")),
    ("hobby_kpop", "追星/饭圈", "fandom & idols", ("fandom",), True, ("追星", "偶像", "idol")),
    ("hobby_coding", "写代码", "coding", ("tech",), True, ("编程", "程序", "dev")),
    ("hobby_hardware", "折腾电脑硬件", "PC building", ("tech",), False, ("装机", "显卡", "pc")),
    ("hobby_photography", "摄影", "photography", ("art",), False, ("拍照", "相机")),
    ("hobby_drawing", "画画", "drawing", ("art",), True, ("绘画", "插画", "art")),
    ("hobby_music_play", "玩乐器", "plays an instrument", ("music",), False, ("吉他", "钢琴")),
    ("hobby_music_listen", "听歌/追专辑", "music listener", ("music",), True, ("听歌", "音乐")),
    ("hobby_reading", "看书", "reading", ("academic",), True, ("阅读", "读书")),
    ("hobby_writing", "写东西", "writing", ("academic",), False, ("写作", "写文")),
    ("hobby_riding", "骑马", "horse riding", ("sports",), False, ("马术",)),
    ("hobby_fitness", "健身", "fitness", ("sports",), True, ("撸铁", "gym")),
    ("hobby_ball_sports", "球类运动", "team sports", ("sports",), False, ("篮球", "足球")),
    ("hobby_boardgame", "桌游/剧本杀", "board games & RPG", ("gaming",), False, ("剧本杀", "跑团", "dnd")),
    ("hobby_cooking", "做饭", "cooking", (), False, ("烹饪", "下厨")),
    ("hobby_travel", "旅行", "travel", (), False, ("旅游",)),
    ("hobby_finance", "研究投资", "investing", ("finance",), False, ("炒股", "理财")),
    ("hobby_debate", "辩论", "debate", ("academic",), False, ("debate",)),
    ("hobby_volunteer", "志愿活动", "volunteering", (), False, ("义工",)),
    ("hobby_film", "看电影/剧", "film & TV", ("art",), True, ("追剧", "电影")),
]
for _id, _z, _e, _gr, _c, _al in _HOBBY:
    _t(_id, "hobby", _z, _e, "该爱好自带的词汇算他懂", "vocabulary from this hobby counts as owned",
       grants=_gr, common=_c, aliases=_al)

# --------------------------------------------------------------------------- #
# GAME — 「打游戏」不够，得知道玩的是哪个。
#
# 为什么必须拆：第五人格的人听得懂「守椅」，原神的人听不懂；原神的人听得懂
# 「保底」，LOL 的人听不懂。粗标签会让系统在两边都判断错。
#
# 为什么还是好设：这些全部 parent = hobby_gaming。用户懒得挑，就点「打游戏」，
# 拿到通用游戏词汇；愿意挑，就搜「王者」「idv」「genshin」直接命中。
#
# implies 只放「读字习惯」这类曝光事实（竞技游戏 = 习惯短促报点；剧情/策略游戏
# = 习惯长文本），不推断 personality traits。
# --------------------------------------------------------------------------- #

_GAME = [
    # (id, zh, en, grants, implies, common, aliases)
    ("game_lol", "英雄联盟", "League of Legends", ("moba",), ("short_chunks",), True,
     ("lol", "撸啊撸", "联盟", "league")),
    ("game_hok", "王者荣耀", "Honor of Kings", ("moba",), ("short_chunks",), True,
     ("王者", "农药", "hok", "kog")),
    ("game_dota", "Dota 2", "Dota 2", ("moba",), (), False, ("dota", "刀塔")),
    ("game_valorant", "无畏契约", "Valorant", ("fps",), ("short_chunks",), True,
     ("valorant", "瓦罗兰特", "val")),
    ("game_csgo", "CS2 / CSGO", "Counter-Strike", ("fps",), ("short_chunks",), False,
     ("cs", "csgo", "cs2", "反恐精英")),
    ("game_pubg", "和平精英 / PUBG", "PUBG", ("fps",), ("short_chunks",), True,
     ("吃鸡", "pubg", "和平精英", "绝地求生")),
    ("game_apex", "Apex 英雄", "Apex Legends", ("fps",), ("short_chunks",), False,
     ("apex", "apex英雄")),
    ("game_overwatch", "守望先锋", "Overwatch", ("fps",), (), False, ("ow", "守望", "overwatch")),
    ("game_genshin", "原神", "Genshin Impact", ("gacha",), (), True,
     ("原神", "genshin", "ys")),
    ("game_hsr", "崩坏：星穹铁道", "Honkai: Star Rail", ("gacha",), (), False,
     ("星铁", "崩铁", "hsr")),
    ("game_arknights", "明日方舟", "Arknights", ("gacha",), ("long_chunks",), False,
     ("方舟", "arknights", "ak")),
    ("game_idv", "第五人格", "Identity V", ("asym_horror",), (), True,
     ("第五", "idv", "identity v", "ivl", "第五人格联赛")),
    ("game_dbd", "黎明杀机", "Dead by Daylight", ("asym_horror",), (), False,
     ("dbd", "黎明杀机")),
    ("game_minecraft", "我的世界", "Minecraft", ("sandbox",), (), True,
     ("mc", "minecraft", "我的世界")),
    ("game_terraria", "泰拉瑞亚", "Terraria", ("sandbox",), (), False, ("terraria", "泰拉")),
    ("game_sims", "模拟人生", "The Sims", ("sim_game",), ("long_chunks",), True,
     ("sims", "模拟人生", "ts4")),
    ("game_stardew", "星露谷物语", "Stardew Valley", ("sim_game",), (), False,
     ("星露谷", "stardew")),
    ("game_animal_crossing", "动物森友会", "Animal Crossing", ("sim_game",), (), False,
     ("动森", "acnh")),
    ("game_rimworld", "环世界", "RimWorld", ("sim_game", "strategy_game"), ("long_chunks",), False,
     ("rimworld", "环世界")),
    ("game_paradox", "P 社游戏（CK3 / EU4 / 群星）", "Paradox grand strategy",
     ("strategy_game",), ("long_chunks", "cause_explicit"), False,
     ("ck3", "eu4", "群星", "stellaris", "p社", "paradox")),
    ("game_civ", "文明", "Civilization", ("strategy_game",), ("long_chunks",), False,
     ("civ", "文明6", "civ6")),
    ("game_eggy", "蛋仔派对", "Eggy Party", ("party_game",), (), False, ("蛋仔", "eggy")),
    ("game_amongus", "Among Us", "Among Us", ("party_game",), (), False, ("狼人杀", "amongus")),
    ("game_rhythm", "音游（osu / ADOFAI 等）", "rhythm games", ("rhythm_game",),
     ("short_chunks",), False, ("音游", "osu", "adofai", "冰与火之舞")),
    ("game_souls", "魂系（法环 / 只狼）", "Soulslike (Elden Ring)", ("souls",), (), False,
     ("法环", "elden", "只狼", "魂系", "soulslike")),
    ("game_galgame", "文字冒险 / galgame", "visual novels", ("narrative_game",),
     ("long_chunks", "tone_visible"), False, ("galgame", "gal", "视觉小说", "文字游戏")),
]
for _id, _z, _e, _gr, _imp, _c, _al in _GAME:
    _t(_id, "hobby", _z, _e, "他懂这个游戏圈的黑话", "owns this game's slang",
       implies=_imp, grants=_gr, parent="hobby_gaming", common=_c, aliases=_al)

# --------------------------------------------------------------------------- #
# DOMAIN — declared knowledge fields. Still the only source of "owns vocabulary".
# --------------------------------------------------------------------------- #

_DOMAIN = [
    ("tech", "技术/互联网", "tech"),
    ("business", "职场/商业", "business"),
    ("academic", "学术", "academic"),
    ("school", "校园", "school life"),
    ("medical", "医学", "medical"),
    ("legal", "法律", "legal"),
    ("finance", "金融", "finance"),
    ("gaming", "游戏", "gaming"),
    ("art", "艺术设计", "art & design"),
    ("music", "音乐", "music"),
    ("sports", "体育", "sports"),
    ("fandom", "饭圈/同人", "fandom"),
    ("psych_pop", "流行心理学", "pop psychology"),
    # 游戏子圈层：每个圈的黑话互相听不懂，所以各占一个 domain
    ("moba", "MOBA（LOL/王者）", "MOBA slang"),
    ("fps", "射击游戏", "shooter slang"),
    ("gacha", "抽卡手游", "gacha slang"),
    ("asym_horror", "非对称对抗（第五人格）", "asymmetric horror slang"),
    ("sandbox", "沙盒建造", "sandbox slang"),
    ("sim_game", "模拟经营", "life-sim slang"),
    ("strategy_game", "策略游戏", "grand strategy slang"),
    ("party_game", "派对游戏", "party game slang"),
    ("rhythm_game", "音游", "rhythm game slang"),
    ("souls", "魂系", "soulslike slang"),
    ("narrative_game", "剧情/文字游戏", "narrative game slang"),
]
for _id, _z, _e in _DOMAIN:
    _t(_id, "domain", _z, _e, "他已经拥有这套词汇", "already owns this vocabulary",
       grants=(_id,))

# --------------------------------------------------------------------------- #
# REGISTER — how they themselves talk (match their usual register).
# --------------------------------------------------------------------------- #

_REG = [
    ("speaks_casual", "说话很口语", "speaks casually", ()),
    ("speaks_formal", "说话偏正式", "speaks formally", ("cause_explicit",)),
    ("speaks_terse", "说话很短", "speaks tersely", ("short_chunks", "no_padding")),
    ("speaks_verbose", "说话很长", "speaks at length", ("long_chunks",)),
    ("speaks_slangy", "爱用网络梗", "uses slang and memes", ()),
    ("speaks_polite", "说话很客气", "very polite", ("tone_visible",)),
    ("speaks_blunt", "说话很直", "blunt", ("no_padding", "conclusion_first")),
    ("speaks_hedgy", "爱用「可能/好像」", "hedges a lot", ("tone_visible",)),
]
for _id, _z, _e, _imp in _REG:
    _t(_id, "register", _z, _e, "他自己的说话方式 = 他最好懂的方式",
       "their own register is what they parse fastest", implies=_imp, common=True)

# --------------------------------------------------------------------------- #
# RELATION & LANG
# --------------------------------------------------------------------------- #

_REL = [
    ("rel_teacher", "老师", "teacher", ("cause_explicit",)),
    ("rel_classmate", "同学", "classmate", ()),
    ("rel_close_friend", "好朋友", "close friend", ("tone_visible",)),
    ("rel_family", "家人", "family", ("tone_visible",)),
    ("rel_senior", "上级/前辈", "senior", ("conclusion_first",)),
    ("rel_stranger", "不熟的人", "stranger", ("define_terms", "cause_explicit")),
    ("rel_club", "社团伙伴", "club member", ()),
]
for _id, _z, _e, _imp in _REL:
    _t(_id, "relation", _z, _e, implies=_imp, common=True)

_LANG = [
    # (id, zh, en, aliases — ISO code + common self-names)
    ("reads_zh", "读中文（普通话）", "reads Chinese (Mandarin)", ("zh", "chinese", "mandarin", "中文")),
    ("reads_yue", "读粤语", "reads Cantonese", ("yue", "cantonese", "粤语", "广东话")),
    ("reads_en", "读英文", "reads English", ("en", "english", "英文")),
    ("reads_ja", "读日语", "reads Japanese", ("ja", "japanese", "日语", "日文")),
    ("reads_ko", "读韩语", "reads Korean", ("ko", "korean", "韩语", "韩文")),
    ("reads_fr", "读法语", "reads French", ("fr", "french", "法语")),
    ("reads_de", "读德语", "reads German", ("de", "german", "德语")),
    ("reads_es", "读西班牙语", "reads Spanish", ("es", "spanish", "西班牙语")),
    ("reads_ar", "读阿拉伯语", "reads Arabic", ("ar", "arabic", "阿拉伯语")),
    ("reads_pt", "读葡萄牙语", "reads Portuguese", ("pt", "portuguese", "葡萄牙语")),
]
for _id, _z, _e, _al in _LANG:
    _t(_id, "lang", _z, _e, common=True, aliases=_al)
# 「中英都行」这类多语能力不是单独一个标签——lang 族本身允许多选（勾几个会读的语言即可），
# 不需要为每一种「两两组合」（中英/中日/英法…）单独造词条。


REGISTRY: dict[str, TagDef] = {d.id: d for d in _D}

FAMILIES: tuple[str, ...] = (
    "mbti", "function", "bigfive", "enneagram", "selfdesc", "source",
    "hobby", "domain", "register", "relation", "lang", "processing",
)


def tag_def(tag_id: str) -> TagDef | None:
    return REGISTRY.get(tag_id)


def label(tag_id: str, lang: str = "zh") -> str:
    d = REGISTRY.get(tag_id)
    return d.text(lang) if d else tag_id


def catalog(lang: str = "zh", family: str | None = None) -> list[dict[str, str]]:
    """Human-readable tag list for the settings UI."""
    rows = []
    for d in REGISTRY.values():
        if family and d.family != family:
            continue
        rows.append(
            {
                "id": d.id,
                "family": d.family,
                "label": d.text(lang),
                "note": d.note(lang),
                "implies": ",".join(d.implies),
                "grants": ",".join(d.grants),
                "parent": d.parent,
                "common": "1" if d.common else "",
            }
        )
    # common first inside a family: 用户一眼看到的是最常见的那几个
    return sorted(
        rows,
        key=lambda r: (FAMILIES.index(r["family"]), not r["common"], r["id"]),
    )


def search(query: str, lang: str = "zh", limit: int = 12) -> list[dict[str, str]]:
    """Find tags by id / label / 别名. 用户打「王者」「idv」「genshin」都要命中。

    Ranking: prefix hit > substring hit, then common-first, then id.
    """
    q = (query or "").strip().lower()
    if not q:
        return [r for r in catalog(lang) if r["common"]][:limit]
    hits: list[tuple[int, int, str, dict[str, str]]] = []
    for d in REGISTRY.values():
        hay = d.haystack()
        if q not in hay:
            continue
        rank = 0 if any(p.startswith(q) for p in hay.split()) else 1
        hits.append((rank, 0 if d.common else 1, d.id, {
            "id": d.id,
            "family": d.family,
            "label": d.text(lang),
            "note": d.note(lang),
        }))
    hits.sort(key=lambda h: h[:3])
    return [h[3] for h in hits[:limit]]


#: 设置页要问的问题，问完就能用。全部可跳过，一个标签不填也能跑。
SETUP_STEPS: tuple[dict[str, object], ...] = (
    {"family": "mbti", "multi": False,
     "zh": "他是什么 MBTI？（不知道就跳过）", "en": "Their MBTI? (skip if unsure)"},
    {"family": "relation", "multi": False,
     "zh": "你们是什么关系？", "en": "How do you know them?"},
    {"family": "hobby", "multi": True,
     "zh": "他平时玩什么、喜欢什么？", "en": "What are they into?"},
    {"family": "register", "multi": True,
     "zh": "他自己说话什么风格？", "en": "How do they talk?"},
)


def quick_setup(lang: str = "zh", full: bool = False) -> list[dict[str, object]]:
    """The whole settings flow: 4 questions, common options only.

    ``full=True`` returns every option in the family (the "更多" list behind
    the search box).
    """
    out: list[dict[str, object]] = []
    for step in SETUP_STEPS:
        opts = [r for r in catalog(lang, str(step["family"]))
                if full or r["common"]]
        out.append({
            "family": step["family"],
            "question": step["zh" if lang.startswith("zh") else "en"],
            "multi": step["multi"],
            "options": opts,
        })
    return out


def expand(declared: set[str]) -> tuple[set[str], set[str]]:
    """Declared tags → (processing tags, owned jargon domains).

    Only ``grants`` produces domains, and only HOBBY / DOMAIN / SOURCE tags
    carry ``grants``. Personality families cannot reach this set.

    Picking a child rolls up to its parent: 选「第五人格」自动也算「打游戏」，
    所以他既懂 ``asym_horror`` 也懂通用的 ``gaming`` 词汇。
    """
    processing: set[str] = set()
    domains: set[str] = set()
    for tid in declared:
        d = REGISTRY.get(tid)
        if not d:
            continue
        chain = [d]
        seen = {d.id}
        while chain[-1].parent and chain[-1].parent not in seen:
            up = REGISTRY.get(chain[-1].parent)
            if not up:
                break
            seen.add(up.id)
            chain.append(up)
        for node in chain:
            processing.update(node.implies)
            domains.update(node.grants)
        if d.family == "mbti":
            stack = MBTI_FUNCTIONS[d.id.split("_")[1].upper()]
            for fn in stack[:2]:
                processing.update(REGISTRY[f"fn_{fn}"].implies)
    return processing, domains
