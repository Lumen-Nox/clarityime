"""Tag registry — the vocabulary people actually use to describe themselves.

Design rule: tags must be ordinary words a person would actually use.

Design rules that survive from the previous round:

1. **A tag never implies a tag from another family**, with exactly one
   documented exception: personality/self-report tags may imply PROCESSING
   tags (how you take information in), because that is what those instruments
   measure. They may **never** imply DOMAIN tags — knowing someone is INTJ
   tells you nothing about whether they know 「排期」.
2. Vocabulary you own comes from what you *do* (HOBBY, DOMAIN, SOURCE, EDU,
   TOPIC), which is why those families — and only those — carry ``grants``.
   Age / gender / country never grant vocabulary and never pick a language.
3. Every tag is bilingual. Labels switch; the speaker's words never do.

Families
--------
mbti        16 types — the single most common self-label in CN and US alike
function    八维 / cognitive functions (Ni Ne Si Se Ti Te Fi Fe)
bigfive     OCEAN, high/low — the instrument academics actually trust
enneagram   九型 1–9
selfdesc    how this person describes themselves (metaphor? data? story?)
source      where their self-knowledge came from — predicts their vocabulary
hobby       爱好 + 具体作品（游戏/番/小说/剧/歌）— grants real vocabulary
domain      professional / study / circle fields
edu         在读课程 / 学历路径 — grants study-circle vocabulary
topic       平时关心的话题 — grants the matching circle
age         年龄段 — processing only for young children, never domains
gender      性别 — stored only; we do not rewrite 他/她
place       国家/地区 — stored only; never implies reads_<lang>
register    how they themselves talk
relation    the tie to the speaker
lang        reading language (multi-select; most are search-only)
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
    ("hobby_anime", "二次元/动漫", "anime & manga", ("fandom", "anime"), True, ("动漫", "番", "acg", "二次元")),
    ("hobby_kpop", "追星/饭圈", "fandom & idols", ("fandom", "idol"), True, ("追星", "偶像", "idol")),
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
    ("hobby_film", "看电影/剧", "film & TV", ("film_tv",), True, ("追剧", "电影", "美剧", "韩剧")),
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
# = 习惯长文本），不推断性格。
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

# 动漫 / 小说 / 剧 / 歌：和游戏同一套 —— 粗爱好拿通用词，具体作品才能对上黑话。
# 全部 parent 回滚到 hobby_*，懒得挑不会判错，只是更保守。
# 具体作品几乎全是 search-only（common=False）。点「二次元」拿通用圈词；
# 搜「鬼灭」「三体」「韩剧」才对上更细的圈。首屏爱好列表必须 ≤20。
_ANIME = [
    ("anime_demon_slayer", "鬼灭之刃", "Demon Slayer", ("鬼灭", "kimetsu", "炭治郎")),
    ("anime_onepiece", "海贼王", "One Piece", ("海贼", "one piece", "路飞")),
    ("anime_naruto", "火影忍者", "Naruto", ("火影", "naruto")),
    ("anime_jjk", "咒术回战", "Jujutsu Kaisen", ("咒术", "jjk")),
    ("anime_conan", "名侦探柯南", "Detective Conan", ("柯南", "conan")),
    ("anime_ghibli", "吉卜力 / 宫崎骏", "Studio Ghibli", ("宫崎骏", "千与千寻", "龙猫", "ghibli")),
    ("anime_haikyuu", "排球少年", "Haikyuu", ("排少", "haikyuu")),
    ("anime_spy", "间谍过家家", "Spy x Family", ("spy x family", "阿尼亚")),
    ("anime_aot", "进击的巨人", "Attack on Titan", ("进击", "aot", "利威尔")),
    ("anime_yourname", "你的名字 / 新海诚", "Your Name / Shinkai", ("你的名字", "新海诚", "天气之子")),
    ("anime_eva", "EVA / 新世纪福音战士", "Neon Genesis Evangelion", ("eva", "福音战士", "绫波")),
    ("anime_frieren", "葬送的芙莉莲", "Frieren", ("芙莉莲", "frieren")),
    ("anime_bocchi", "孤独摇滚", "Bocchi the Rock", ("孤独摇滚", "bocchi", "波奇")),
    ("anime_pokemon", "宝可梦", "Pokémon", ("宝可梦", "pokemon", "口袋妖怪")),
    ("anime_db", "龙珠", "Dragon Ball", ("龙珠", "dragon ball", "悟空")),
]
for _id, _z, _e, _al in _ANIME:
    _t(_id, "hobby", _z, _e, "他懂这部番的梗和说法", "owns this title's slang",
       grants=("anime",), parent="hobby_anime", common=False, aliases=_al)

_NOVEL = [
    ("novel_web", "网文 / 网络小说", "web novels", True, ("网文", "起点", "晋江", "番茄", "网络小说")),
    ("novel_xuanhuan", "玄幻", "xuanhuan", False, ("玄幻", "修仙")),
    ("novel_wuxia", "武侠", "wuxia", False, ("武侠", "金庸", "古龙")),
    ("novel_romance", "言情", "romance novels", False, ("言情", "甜宠", "虐文")),
    ("novel_hp", "哈利波特", "Harry Potter", False, ("hp", "哈利波特", "霍格沃茨", "muggle")),
    ("novel_threebody", "三体", "The Three-Body Problem", False, ("三体", "刘慈欣")),
    ("novel_lotr", "魔戒 / 托尔金", "Lord of the Rings", False, ("魔戒", "霍比特人", "tolkien", "lotr")),
    ("novel_danmei", "耽美 / 晋江", "danmei", False, ("耽美", "晋江", "mxtx", "魔道祖师")),
    ("novel_dune", "沙丘", "Dune", False, ("沙丘", "dune")),
    ("novel_classics_cn", "中国古典小说", "Chinese classics", False, ("红楼梦", "西游记", "三国", "水浒")),
]
for _id, _z, _e, _c, _al in _NOVEL:
    _web = _id in ("novel_web", "novel_xuanhuan", "novel_wuxia", "novel_romance", "novel_danmei")
    _t(_id, "hobby", _z, _e, "他懂这类书的说法", "owns this reading-circle slang",
       grants=("webnovel",) if _web else ("fandom",),
       parent="hobby_reading", common=_c, aliases=_al)

_FILM = [
    ("film_marvel", "漫威", "Marvel", ("漫威", "marvel", "复联", "复仇者")),
    ("film_starwars", "星球大战", "Star Wars", ("星战", "star wars", "绝地")),
    ("film_disney", "迪士尼", "Disney", ("迪士尼", "disney", "皮克斯")),
    ("film_ghibli_live", "宫崎骏电影", "Ghibli films", ("千与千寻", "哈尔的移动城堡")),
    ("tv_kdrama", "韩剧", "K-drama", ("韩剧", "kdrama", "韩剧迷")),
    ("tv_cdrama", "国产剧 / 港剧", "C-drama", ("国产剧", "港剧", "电视剧", "甄嬛传")),
    ("tv_jdrama", "日剧", "J-drama", ("日剧", "jdrama")),
    ("tv_us", "英美剧", "US/UK TV", ("美剧", "英剧", "netflix", "权力的游戏", "老友记")),
]
for _id, _z, _e, _al in _FILM:
    _t(_id, "hobby", _z, _e, "他懂这部片/剧的梗", "owns this screen-circle slang",
       grants=("film_tv",), parent="hobby_film", common=False, aliases=_al)

_MUSIC = [
    ("music_c_pop", "华语流行", "C-pop", ("华语", "华语歌", "周杰伦", "汪苏泷", "邓丽君")),
    ("music_kpop_group", "韩团", "K-pop groups", ("韩团", "bts", "blackpink", "twice", "kpop")),
    ("music_jpop", "日本流行", "J-pop", ("jpop", "日推", "j-pop")),
    ("music_western_pop", "欧美流行", "Western pop", ("欧美", "泰勒", "taylor", "swift")),
    ("music_hiphop", "说唱 / 嘻哈", "hip-hop", ("说唱", "rap", "嘻哈")),
    ("music_classical", "古典乐", "classical", ("古典", "交响乐", "莫扎特")),
    ("music_ost", "影视原声", "soundtracks", ("ost", "原声", "配乐")),
]
for _id, _z, _e, _al in _MUSIC:
    extra = ("idol",) if _id == "music_kpop_group" else ()
    _t(_id, "hobby", _z, _e, "他懂这个乐圈的说法", "owns this music-circle slang",
       grants=("music",) + extra, parent="hobby_music_listen", common=False, aliases=_al,
       implies=("long_chunks",) if _id == "music_classical" else ())

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
    ("anime", "动漫/二次元", "anime slang"),
    ("webnovel", "网文", "web-novel slang"),
    ("film_tv", "影视剧", "film & TV slang"),
    ("idol", "饭圈应援", "idol-fandom slang"),
]
for _id, _z, _e in _DOMAIN:
    _t(_id, "domain", _z, _e, "他已经拥有这套词汇", "already owns this vocabulary",
       grants=(_id,))

# --------------------------------------------------------------------------- #
# REGISTER — how they themselves talk. the author: 「参考他平常说话的语气」
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
    # (id, zh, en, common, aliases). 首屏只放中/英/日/韩；其余全靠搜索。
    ("reads_zh", "读中文（普通话）", "reads Chinese (Mandarin)", True,
     ("zh", "chinese", "mandarin", "中文", "普通话")),
    ("reads_zh_hant", "读繁体中文", "reads Traditional Chinese", False,
     ("zh-hant", "繁体", "繁體", "taiwanese chinese")),
    ("reads_yue", "读粤语", "reads Cantonese", False, ("yue", "cantonese", "粤语", "广东话")),
    ("reads_en", "读英文", "reads English", True, ("en", "english", "英文")),
    ("reads_ja", "读日语", "reads Japanese", True, ("ja", "japanese", "日语", "日文")),
    ("reads_ko", "读韩语", "reads Korean", True, ("ko", "korean", "韩语", "韩文")),
    ("reads_fr", "读法语", "reads French", False, ("fr", "french", "法语")),
    ("reads_de", "读德语", "reads German", False, ("de", "german", "德语")),
    ("reads_es", "读西班牙语", "reads Spanish", False, ("es", "spanish", "西班牙语")),
    ("reads_pt", "读葡萄牙语", "reads Portuguese", False, ("pt", "portuguese", "葡萄牙语")),
    ("reads_ar", "读阿拉伯语", "reads Arabic", False, ("ar", "arabic", "阿拉伯语")),
    ("reads_ru", "读俄语", "reads Russian", False, ("ru", "russian", "俄语")),
    ("reads_it", "读意大利语", "reads Italian", False, ("it", "italian", "意大利语")),
    ("reads_vi", "读越南语", "reads Vietnamese", False, ("vi", "vietnamese", "越南语")),
    ("reads_th", "读泰语", "reads Thai", False, ("th", "thai", "泰语")),
    ("reads_id", "读印尼语", "reads Indonesian", False, ("id", "indonesian", "印尼语")),
    ("reads_ms", "读马来语", "reads Malay", False, ("ms", "malay", "马来语")),
    ("reads_hi", "读印地语", "reads Hindi", False, ("hi", "hindi", "印地语")),
    ("reads_bn", "读孟加拉语", "reads Bengali", False, ("bn", "bengali", "孟加拉语")),
    ("reads_ta", "读泰米尔语", "reads Tamil", False, ("ta", "tamil", "泰米尔语")),
    ("reads_ur", "读乌尔都语", "reads Urdu", False, ("ur", "urdu", "乌尔都语")),
    ("reads_nl", "读荷兰语", "reads Dutch", False, ("nl", "dutch", "荷兰语")),
    ("reads_pl", "读波兰语", "reads Polish", False, ("pl", "polish", "波兰语")),
    ("reads_tr", "读土耳其语", "reads Turkish", False, ("tr", "turkish", "土耳其语")),
    ("reads_sv", "读瑞典语", "reads Swedish", False, ("sv", "swedish", "瑞典语")),
    ("reads_uk", "读乌克兰语", "reads Ukrainian", False, ("uk", "ukrainian", "乌克兰语")),
    ("reads_tl", "读菲律宾语", "reads Filipino", False, ("tl", "filipino", "tagalog", "菲律宾语")),
    ("reads_fa", "读波斯语", "reads Persian", False, ("fa", "persian", "farsi", "波斯语")),
    ("reads_he", "读希伯来语", "reads Hebrew", False, ("he", "hebrew", "希伯来语")),
    ("reads_el", "读希腊语", "reads Greek", False, ("el", "greek", "希腊语")),
    ("reads_cs", "读捷克语", "reads Czech", False, ("cs", "czech", "捷克语")),
    ("reads_ro", "读罗马尼亚语", "reads Romanian", False, ("ro", "romanian", "罗马尼亚语")),
    ("reads_hu", "读匈牙利语", "reads Hungarian", False, ("hu", "hungarian", "匈牙利语")),
    ("reads_fi", "读芬兰语", "reads Finnish", False, ("fi", "finnish", "芬兰语")),
    ("reads_no", "读挪威语", "reads Norwegian", False, ("no", "norwegian", "挪威语")),
    ("reads_da", "读丹麦语", "reads Danish", False, ("da", "danish", "丹麦语")),
    ("reads_sw", "读斯瓦希里语", "reads Swahili", False, ("sw", "swahili", "斯瓦希里语")),
    ("reads_my", "读缅甸语", "reads Burmese", False, ("my", "burmese", "缅甸语")),
    ("reads_km", "读高棉语", "reads Khmer", False, ("km", "khmer", "高棉语", "柬埔寨语")),
]
for _id, _z, _e, _c, _al in _LANG:
    _t(_id, "lang", _z, _e, common=_c, aliases=_al)
# 「中英都行」不是单独标签——lang 族允许多选。
# 国家 ≠ 语言：住日本不会自动挂 reads_ja（侨民、国际学校、家里说中文都常见）。

# --------------------------------------------------------------------------- #
# AGE / GENDER / PLACE — 存档用。不授予词汇，不改人称代词，不从国家推语言。
# 唯一例外：很小的孩子需要更短、更具体、术语全解释（曝光事实，不是性格）。
# 青少年不加 define_terms——15 岁听得懂圈子词。
# --------------------------------------------------------------------------- #

_AGE = [
    ("age_child", "儿童（大约 12 岁以下）", "child (about 12 or under)", True,
     ("short_chunks", "define_terms", "concrete_first"),
     ("小孩", "儿童", "kid", "child")),
    ("age_teen", "青少年", "teen", True, (),
     ("青少年", "teen", "teenager", "中学生")),
    ("age_uni", "大学生", "university age", False, (),
     ("大学生", "uni", "college")),
    ("age_adult", "已工作的成年人", "working adult", True, (),
     ("成年人", "adult", "上班")),
    ("age_elder", "长辈", "older adult", False, (),
     ("长辈", "老人", "elder")),
]
for _id, _z, _e, _c, _imp, _al in _AGE:
    _t(_id, "age", _z, _e, implies=_imp, common=_c, aliases=_al)

_GENDER = [
    ("gender_female", "女", "female", True, ("女生", "女", "girl", "woman")),
    ("gender_male", "男", "male", True, ("男生", "男", "boy", "man")),
    ("gender_nb", "非二元 / 不愿标注", "non-binary / unspecified", True,
     ("非二元", "nb", "nonbinary", "不愿说")),
]
for _id, _z, _e, _c, _al in _GENDER:
    _t(_id, "gender", _z, _e, common=_c, aliases=_al)

_PLACE = [
    ("place_cn", "中国大陆", "mainland China", True, ("中国", "大陆", "china", "cn")),
    ("place_us", "美国", "United States", True, ("美国", "usa", "us", "america")),
    ("place_jp", "日本", "Japan", True, ("日本", "japan", "jp")),
    ("place_kr", "韩国", "South Korea", True, ("韩国", "korea", "kr")),
    ("place_uk", "英国", "United Kingdom", False, ("英国", "uk", "britain", "england")),
    ("place_sg", "新加坡", "Singapore", False, ("新加坡", "sg", "singapore")),
    ("place_tw", "台湾", "Taiwan", False, ("台湾", "taiwan", "tw")),
    ("place_hk", "香港", "Hong Kong", False, ("香港", "hong kong", "hk")),
    ("place_ca", "加拿大", "Canada", False, ("加拿大", "canada")),
    ("place_au", "澳大利亚", "Australia", False, ("澳洲", "澳大利亚", "australia")),
    ("place_fr", "法国", "France", False, ("法国", "france")),
    ("place_de", "德国", "Germany", False, ("德国", "germany")),
    ("place_es", "西班牙", "Spain", False, ("西班牙", "spain")),
    ("place_it", "意大利", "Italy", False, ("意大利", "italy")),
    ("place_ru", "俄罗斯", "Russia", False, ("俄罗斯", "russia")),
    ("place_in", "印度", "India", False, ("印度", "india")),
    ("place_th", "泰国", "Thailand", False, ("泰国", "thailand")),
    ("place_vn", "越南", "Vietnam", False, ("越南", "vietnam")),
    ("place_id", "印度尼西亚", "Indonesia", False, ("印尼", "indonesia")),
    ("place_my", "马来西亚", "Malaysia", False, ("马来西亚", "malaysia")),
    ("place_ph", "菲律宾", "Philippines", False, ("菲律宾", "philippines")),
    ("place_br", "巴西", "Brazil", False, ("巴西", "brazil")),
    ("place_mx", "墨西哥", "Mexico", False, ("墨西哥", "mexico")),
    ("place_nz", "新西兰", "New Zealand", False, ("新西兰", "new zealand")),
    ("place_nl", "荷兰", "Netherlands", False, ("荷兰", "netherlands")),
    ("place_tr", "土耳其", "Turkey", False, ("土耳其", "turkey")),
    ("place_ae", "阿联酋", "UAE", False, ("阿联酋", "dubai", "uae")),
    ("place_sa", "沙特阿拉伯", "Saudi Arabia", False, ("沙特", "saudi")),
]
for _id, _z, _e, _c, _al in _PLACE:
    _t(_id, "place", _z, _e, common=_c, aliases=_al)

# --------------------------------------------------------------------------- #
# EDU / TOPIC — 「在读什么 / 关心什么」是正在做的事，所以可以 grants。
# --------------------------------------------------------------------------- #

_EDU = [
    ("edu_myp", "MYP / 国际学校初中", "MYP / middle years", False, ("school",),
     ("myp", "国际学校")),
    ("edu_igcse", "IGCSE", "IGCSE", True, ("school",),
     ("igcse", "ig", "gcse")),
    ("edu_ib", "IB", "IB Diploma", True, ("school", "academic"),
     ("ib", "ibdp", "diploma")),
    ("edu_ap", "AP", "AP courses", False, ("school", "academic"),
     ("ap", "ap课")),
    ("edu_alevel", "A-Level", "A-Level", False, ("school",),
     ("alevel", "a-level", "a level")),
    ("edu_gaokao", "高考", "Gaokao", False, ("school",),
     ("高考", "gaokao")),
    ("edu_undergrad", "大学本科", "undergraduate", True, ("academic",),
     ("本科", "大学", "undergrad", "bachelor")),
    ("edu_grad", "研究生", "graduate school", False, ("academic",),
     ("研究生", "硕士", "博士", "phd")),
    ("course_cs", "在学计算机", "studying CS", False, ("tech",),
     ("计算机课", "cs课", "编程课")),
    ("course_psych", "在学心理", "studying psychology", False, ("psych_pop",),
     ("心理课", "心理学")),
    ("course_math", "在学数学", "studying math", False, ("academic",),
     ("数学课", "math")),
    ("course_physics", "在学物理", "studying physics", False, ("academic",),
     ("物理课", "physics")),
    ("course_chem", "在学化学", "studying chemistry", False, ("academic",),
     ("化学课", "chemistry")),
    ("course_bio", "在学生物", "studying biology", False, ("academic",),
     ("生物课", "biology")),
    ("course_business", "在学商科", "studying business", False, ("business",),
     ("商科", "business课")),
    ("course_art", "在学艺术", "studying art", False, ("art",),
     ("艺术课", "美术")),
    ("course_english", "在学英语文学", "studying English", False, ("academic",),
     ("英语课", "english lit")),
    ("course_history", "在学历史", "studying history", False, ("academic",),
     ("历史课", "history")),
    ("course_drama", "在学戏剧", "studying drama", False, ("art",),
     ("戏剧课", "drama")),
    ("course_music", "在学音乐", "studying music", False, ("music",),
     ("音乐课",)),
]
for _id, _z, _e, _c, _gr, _al in _EDU:
    _t(_id, "edu", _z, _e, "在读这条路径/这门课，相关说法算他懂",
       "studying this, so the circle's vocabulary counts as owned",
       grants=_gr, common=_c, aliases=_al)

_TOPIC = [
    ("topic_ai", "关心 AI", "follows AI", True, ("tech",),
     ("人工智能", "ai", "机器学习")),
    ("topic_cs", "关心计算机", "follows CS", True, ("tech",),
     ("计算机", "编程", "cs")),
    ("topic_psych", "关心心理", "follows psychology", True, ("psych_pop",),
     ("心理", "心理学", "mbti研究")),
    ("topic_finance", "关心财经", "follows finance", False, ("finance",),
     ("财经", "投资", "股市")),
    ("topic_climate", "关心气候/环境", "follows climate", False, ("academic",),
     ("气候", "环境", "climate")),
    ("topic_startups", "关心创业", "follows startups", False, ("business",),
     ("创业", "startup")),
    ("topic_edu", "关心教育", "follows education", False, ("school",),
     ("教育", "升学")),
    ("topic_philosophy", "关心哲学", "follows philosophy", False, ("academic",),
     ("哲学", "philosophy")),
    ("topic_history", "关心历史", "follows history", False, ("academic",),
     ("历史", "history")),
    ("topic_ling", "关心语言", "follows linguistics", False, ("academic",),
     ("语言学", "linguistics")),
    ("topic_neuro", "关心神经科学", "follows neuroscience", False, ("psych_pop",),
     ("神经科学", "neuroscience", "大脑")),
    ("topic_law", "关心法律", "follows law", False, ("legal",),
     ("法律", "law")),
    ("topic_health", "关心健康", "follows health", False, (),
     ("健康", "养生")),  # 聊天关心健康 ≠ 拥有医学黑话
    ("topic_sports", "关心体育", "follows sports", False, ("sports",),
     ("体育", "球赛")),
    ("topic_games", "关心游戏圈新闻", "follows gaming news", False, ("gaming",),
     ("游戏圈", "电竞新闻")),
    ("topic_anime", "关心漫圈新闻", "follows anime news", False, ("anime",),
     ("漫圈", "番剧新闻")),
    ("topic_film", "关心影视新闻", "follows film news", False, ("film_tv",),
     ("影视圈", "电影新闻")),
]
for _id, _z, _e, _c, _gr, _al in _TOPIC:
    _t(_id, "topic", _z, _e, "他在跟这个话题，相关说法算他懂",
       "following this topic, so the circle's vocabulary counts as owned",
       grants=_gr, common=_c, aliases=_al)


REGISTRY: dict[str, TagDef] = {d.id: d for d in _D}

FAMILIES: tuple[str, ...] = (
    "mbti", "function", "bigfive", "enneagram", "selfdesc", "source",
    "hobby", "domain", "edu", "topic", "age", "gender", "place",
    "register", "relation", "lang", "processing",
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
#: 第 4 问把年龄/性别/国家/学历/话题/语言并在一起，免得变成问卷。
SETUP_STEPS: tuple[dict[str, object], ...] = (
    {"family": "mbti", "multi": False,
     "zh": "他是什么 MBTI？（不知道就跳过）", "en": "Their MBTI? (skip if unsure)"},
    {"family": "relation", "multi": False,
     "zh": "你们是什么关系？", "en": "How do you know them?"},
    {"family": "hobby", "multi": True,
     "zh": "他平时玩什么、喜欢什么？（游戏/番/小说/剧/歌都能搜）",
     "en": "What are they into? (games, anime, books, shows, music — search works)"},
    {"family": "life", "families": ("age", "gender", "place", "edu", "topic", "lang"),
     "multi": True,
     "zh": "年龄、国家、在读什么、关心什么、会读什么语言？",
     "en": "Age, country, what they study, what they follow, which languages they read?"},
    {"family": "register", "multi": True,
     "zh": "他自己说话什么风格？", "en": "How do they talk?"},
)


def quick_setup(lang: str = "zh", full: bool = False) -> list[dict[str, object]]:
    """The whole settings flow: 5 questions, common options only.

    ``full=True`` returns every option in the family (the "更多" list behind
    the search box). The life step unions several families so the picker
    stays one screen.
    """
    out: list[dict[str, object]] = []
    for step in SETUP_STEPS:
        fams = step.get("families") or (step["family"],)
        opts: list[dict[str, str]] = []
        seen: set[str] = set()
        for fam in fams:
            for r in catalog(lang, str(fam)):
                if r["id"] in seen:
                    continue
                if full or r["common"]:
                    seen.add(r["id"])
                    opts.append(r)
        out.append({
            "family": step["family"],
            "question": step["zh" if lang.startswith("zh") else "en"],
            "multi": step["multi"],
            "options": opts,
        })
    return out


def expand(declared: set[str]) -> tuple[set[str], set[str]]:
    """Declared tags → (processing tags, owned jargon domains).

    Only ``grants`` produces domains, and only HOBBY / DOMAIN / SOURCE / EDU /
    TOPIC tags carry ``grants``. Personality, age, gender, country, and
    reading-language families cannot reach this set.

    Picking a child rolls up to its parent: 选「第五人格」自动也算「打游戏」，
    所以他既懂 ``asym_horror`` 也懂通用的 ``gaming`` 词汇。番/小说/剧同理。
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
