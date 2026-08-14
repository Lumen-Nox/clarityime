# 什么是「理解」——ClarityIME 的理解模型（设计基准）

> 目标：让**听的人真的懂、并且被原有论点说服**。
> 约束：**不加新内容、不改说话人立场与语气**，只把已经说过的东西「优化、细化、显性化」。

---

## 0. 一句话结论

心理语言学里，**理解不是"读到字"，而是听者在脑内成功搭出一个连贯的心理表征**。
听不懂 = 搭建过程中出现了**断口**，需要额外推理去补。
所以「帮人听懂」= **把断口填上**（用他自己已经说过的材料），而不是把话改短、改甜、改硬。

---

## 1. 理解到底是什么：三层模型

### 1.1 Kintsch 的 CI 模型（Construction–Integration）

| 层 | 名称 | 内容 |
|---|---|---|
| 1 | **表层** (surface) | 逐字的词形 |
| 2 | **命题文本基** (textbase) | 从句子抽出的命题网络 |
| 3 | **情境模型** (situation model) | 听者脑中"这件事到底怎么回事" |

> Kintsch & van Dijk (1978), *Psychological Review* 85(5): 363–394；Kintsch (1988), *Psychological Review* 95(2): 163–182.

**关键机制：argument overlap（论元重叠）。**
两个命题只有共享一个论元（同一个人/物）时，才能在工作记忆里**连成一张网**。
共享不上 → 听者必须做一次**桥接推理**（bridging inference）→ 慢、易错、易放弃。

**对我们的意义**：口语里最常见的断口就是**指代没落地**（"它""这个""那边"）和**主语省略**（零形回指）。

---

### 1.2 Gernsbacher 的结构建构框架（Structure Building Framework）

理解 = 三个动作：

| 动作 | 含义 | 出问题时 |
|---|---|---|
| **Laying a foundation** | 用**最先听到的信息**打地基 | 地基是废话/铺垫 → 整段挂错地方 |
| **Mapping** | 后续信息若连贯，**映射**到当前结构 | 连贯线索缺失 → 映射失败 |
| **Shifting** | 若不连贯，**另起**一个子结构 | 频繁 shifting = 理解崩掉 |

> Gernsbacher (1990), *Language Comprehension as Structure Building*, Erlbaum.
> 首句优势（first-mention advantage）：最先提到的实体在心理表征中可及性最高。

**对我们的意义**：**第一小句决定整段挂在哪**。
如果说话人先说了三句铺垫再说结论，很多听者的地基就打在铺垫上。
把**结论移到最前**（只调顺序、不改词）＝ 换个地基，不是换内容。

---

### 1.3 Given–New 契约（Haviland & Clark）

听者默认：句子里的**已知信息**（given）能在记忆里找到锚点，**新信息**（new）挂上去。
找不到锚点 → 触发 bridging → 阅读时间显著变长。

> Haviland & Clark (1974), *Journal of Verbal Learning and Verbal Behavior* 13(5): 512–521.

---

## 2. 已被实验证明「不加内容也能提升理解」的操作

这一节是本项目**允许的操作集**的来源——每条都有实证，且都**不引入新命题**。

### 2.1 把隐含的指代显性化（最强证据）

Britton & Gülgöz 用 Kintsch 模型定位文本中的 "inference calls"（要求读者自己补的地方），
**只把已有的指代写清楚**，不加任何新信息 → 回忆量大幅提升。

> Britton & Gülgöz (1991), *Journal of Educational Psychology* 83(3): 329–345.

对应操作：`它老是超时` → `API接口老是超时`（"API接口"是**他自己刚说过的**）。

### 2.2 因果关系比并列关系更好懂、更好记

因果连接的句子在线处理更快、回忆更好。

> Sanders & Noordman (2000), *Discourse Processes* 29(1): 37–60.
> Trabasso & van den Broek (1985), *Journal of Memory and Language* 24: 612–630（因果链上的事件回忆率最高）。

对应操作：把 `因为…` 这类**说话人已经说出口的**因果小句，从长串里**切出来单独成行**（signaling，不加词）。

### 2.3 连贯性/衔接（cohesion）可测量，且对低背景知识者收益最大

Coh-Metrix 把「指代衔接」「因果衔接」「连接词密度」做成可计算指标。
McNamara 等人发现：**背景知识低**的读者从高衔接文本获益显著；
背景知识高的读者反而可能因为"太顺"而不深加工（reverse cohesion effect）。

> Graesser, McNamara, Louwerse & Cai (2004), *Behavior Research Methods* 36(2): 193–202.
> McNamara, Kintsch, Songer & Kintsch (1996), *Cognition and Instruction* 14(1): 1–43.

**对我们的意义**：**衔接强度要按听者调**，这正是 Cerome L3（comprehension gaps）该干的事——
不是"所有人都给最顺的版本"。

### 2.4 认知负荷：切块（chunking）

外在负荷（extraneous load）来自呈现方式，不来自内容本身。
工作记忆有效容量约 **4 个组块**（不是 7±2）。

> Sweller (1988), *Cognitive Science* 12(2): 257–285；Sweller, van Merriënboer & Paas (1998), *Educational Psychology Review* 10: 251–296.
> Cowan (2001), *Behavioral and Brain Sciences* 24(1): 87–114.
> Miller (1956), *Psychological Review* 63(2): 81–97.

对应操作：**按意群切行**，单个意群不超过听者容量。切行不改词。

### 2.5 Signaling（信号化）

标题、序号、排版位置等**不增加内容**的信号，能提高被信号化内容的回忆。

> Lorch (1989), *Educational Psychology Review* 1: 209–234.
> Loman & Mayer (1983), *Journal of Educational Psychology* 75(3): 402–412.

### 2.6 中文特有：话题优先结构

中文是**话题—述题**（topic–comment）型语言，话题在前有利于解析；
且**零形回指**（省略主语）极常见，是中文口语最大的理解断口来源。

> Li & Thompson (1981), *Mandarin Chinese: A Functional Reference Grammar*, UC Press.

---

## 3. 「说服」怎么在不加内容的前提下发生

### 3.1 加工流畅性 → 感知真实性

同样的陈述，**更易加工**时被判断为**更可能为真**、更可信、更讨喜。

> Reber & Schwarz (1999), *Consciousness and Cognition* 8(3): 338–342.
> Reber, Schwarz & Winkielman (2004), *Personality and Social Psychology Review* 8(4): 364–382.
> Alter & Oppenheimer (2009), *Personality and Social Psychology Review* 13(3): 219–235.

### 3.2 ELM：降低理解成本 = 提高"能力"，让论点走中心路径

精细加工可能性模型：说服走**中心路径**需要听者**有动机 + 有能力**加工论证。
理解成本高 → 能力不足 → 退回边缘线索（谁说的、语气好不好听）。

> Petty & Cacioppo (1986), *Communication and Persuasion*, Springer.

**所以：把话弄清楚 = 让"原有论点本身"获得应有的权重。**
这与"改语气去讨好"是**相反**的两条路——后者恰恰是边缘路径。

### 3.3 关联理论：我们只压低分母

关联性 = 认知效果 ÷ 加工努力。
我们**不动分子**（不加信息、不改立场），只**压低分母**。

> Sperber & Wilson (1986/1995), *Relevance: Communication and Cognition*, Blackwell.

### 3.4 Grounding：最小协作努力

对话双方会寻求"共同基础"，并倾向**最小协作努力**。

> Clark & Brennan (1991), in *Perspectives on Socially Shared Cognition*, APA: 127–149.

---

## 4. 由此得出的**允许操作集**（硬约束）

| # | 操作 | 依据 | 是否加新内容 |
|---|---|---|---|
| A1 | **指代落地** 它/这个 → 前文已出现的名词 | Britton & Gülgöz 1991; Haviland & Clark 1974 | ❌ 只重复已说过的词 |
| A2 | **补回省略主语**（零形回指） | Li & Thompson 1981; Kintsch argument overlap | ❌ 只重复已说过的词 |
| A3 | **结论前置**（只调顺序） | Gernsbacher 首句优势 | ❌ 词序变，词不变 |
| A4 | **意群切块** | Sweller 1988; Cowan 2001 | ❌ 只加换行 |
| A5 | **因果/转折小句信号化**（独立成行） | Sanders & Noordman 2000; Lorch 1989 | ❌ 只改排版 |
| A6 | **去重复口水**（完全重复的片段） | 外在负荷 | ❌ 只删冗余重复 |
| A7 | **连贯流式**（高共情听者不做分析式切分） | McNamara 1996 逆衔接效应 | ❌ 只改断点位置 |
| A8 | **支撑句按听者在意的维度排序**（同角色之间） | Petty & Cacioppo 1986 中心路径 | ❌ 只调顺序 |
| **T1** | **行话 → 人话**（听者不属于该圈子时） | Rayner & Duffy 1986 词频效应；Crossley 2011 | ❌ 固定审计表，1:1 同义 |
| **T1a** | **跨圈类比**（他圈有对应词时夹「就像 X」） | Gentner 1983 structure-mapping | ❌ 固定审计表；原词保留 |
| **T2** | **去名词化**：进行一次复盘 → 复盘 | Halliday & Martin 1993 语法隐喻 | ❌ 删空动词 |
| **T3** | **去冗余**：的话／这样子／…的处理 | 外在负荷 | ❌ 删虚词 |

### T1 为什么安全

T1 是**固定本地表**（`clarify/paraphrase.py`，一屏可读完），不是生成。
所以不存在"AI 编了一个意思"——最差情况是表里某一条写错了，而表是人能逐条审的。
每次替换都进 `substitutions` 审计字段返回给 UI。

**听者是圈内人就不替换**（audience design，Clark & Murphy 1982）。
判据是**这个词的领域**是否在**这个人声明的 domain 标签**里 —— 见 §7.3。
性格预设一律不带 domain 标签：INTJ 不等于懂技术。

### 禁止操作（会改变说话人）

| ❌ | 为什么禁 |
|---|---|
| 加「不好意思」「麻烦您」 | 说话人没说，属于**新内容**且改立场 |
| 你 → 您 | 改 register，不是帮理解 |
| 删「还行」「可能」「挺」 | **对冲词就是立场本身**，删掉＝改判断强度 |
| 摘要 / 抽要点 | 丢命题，违背 CI 模型的完整表征 |
| 加连接词（原话没有的「所以」） | 添加了原话没有的关系断言 |

---

## 5. 可验证的不变量（写进测试）

```
1. NO_NEW_CONTENT   : 输出的每个内容 token 都必须在输入中出现过
2. NO_LOST_CONTENT  : 输入的每个内容 token（口水词除外）在输出中仍存在
3. HEDGE_PRESERVED  : 还行/可能/挺/觉得/有点… 一个不少
4. POLARITY_STABLE  : 不/没/别 的数量不变
5. DETERMINISTIC    : 同输入 + 同听者 → 同输出（逐字节，跑 20 次比对）
6. DETAIL_PRESERVED : 每个 detail unit（角色+表层）一个不丢 —— 见 §7ter
7. SPEECH_ACT_KEPT  : 问句不能变陈述句（Searle 1969）
8. MEANING_ORAL_KEPT: 判为 MEANING 的口语标记永不删 —— 见 §7bis
```

任何一条不满足 → **回退原文**，宁可不优化也不改说话人。

### 5.1 确定性是结构性的，不是运气

`tests/test_determinism.py` 不只跑 20 次比对输出，它还 **AST 扫描整个
`clarify/` 目录**，禁止出现 `random` / `openai` / `anthropic` / `requests` /
`httpx` / `urllib` 的 import，以及 `random()` `shuffle()` `choice()` `time()`
`now()` `uuid4()` 的调用。**没有模型调用，所以不可能漂。**

---

## 6. 理解成本度量（原文 vs 听懂版，可打分）

| 指标 | 含义 | 越低越好 |
|---|---|---|
| `bridging` | 未落地指代 + 缺主语小句数 | ✅ |
| `foundation_delay` | 主张出现前需要读的字数 | ✅ |
| `max_unit` | 最长意群字数（对比听者容量） | ✅ |
| `overload_units` | 超出听者容量的意群数 | ✅ |
| `unsignaled_causal` | 未被信号化的因果/转折小句 | ✅ |

`comprehension_cost = 2·bridging + 1.5·overload_units + 1·unsignaled_causal + foundation_delay/20`

实现：`clarityime/clarify/comprehension.py`

---

## 7. 标签系统：规则只认标签，不认人、不认描述

> Design rule: tags must be ordinary words a person would actually use.
> 「你不要针对每个人都去开发一段程序，而是要根据标签来开发程序。」

### 7.1 被这条规则杀掉的 bug

早期版本给 `d_type`（INTJ）预设写了 `knows_tech=True`，于是「超时/复盘」对他不翻译。
**这是编的。** A personality preset only records personality. It never said this listener knows tech jargon.
性格标签说的是**他怎么处理信息**，不是**他认识哪些词** —— 这是两个族，不能互推。

### 7.2 标签库：可搜索、双语、17 族（`clarityime/cerome/tag_registry.py`）

按**真人自我描述的方式**设计，不是按我方便实现的方式。每个标签中英双语。
具体作品（番/小说/剧/歌/游戏）几乎全是搜索可见；首屏爱好列表压在 20 个以内。

| 族 | 例子 | 能授予词汇？ | 能影响排版？ |
|---|---|---|---|
| **mbti** | INTJ·建筑师、ENFP·竞选者 | ❌ | ✅ 经八维 |
| **function** 八维 | Ni 内倾直觉、Te 外倾思考 | ❌ | ✅ |
| **bigfive** | 尽责性高、宜人性低 | ❌ | ✅ |
| **enneagram** 九型 | 3号·成就型 | ❌ | ✅ |
| **selfdesc** | 爱用比喻／爱用数据 | ❌ | ✅ |
| **source** | 网上测过／上过心理学课 | ✅ | ✅ |
| **hobby** | 打游戏／二次元／看书／听歌 + 具体作品 | ✅ | 少数 ✅ |
| **domain** | 技术、校园、网文、动漫、影视、饭圈… | ✅ | ❌ |
| **edu** | IGCSE / IB / 本科 / 在学计算机 | ✅ | ❌ |
| **topic** | 关心 AI／心理／计算机 | ✅ | ❌ |
| **age** | 儿童／青少年／成年人 | ❌ | 仅儿童 ✅ |
| **gender** | 女／男／非二元 | ❌ | ❌ 不改他/她 |
| **place** | 中国／美国／日本／韩国… | ❌ | ❌ 不推语言 |
| **register** | 说话很直、爱用网络梗 | ❌ | ✅ |
| **relation** | 老师、同学、不熟的人 | ❌ | ✅ |
| **lang** | 读中文／英文／日／韩 + 搜索更多 | ❌ | ❌（只选词表） |
| **processing** | 先给结论、术语一律解释 | — | 就是它本身 |

### 7.2b 唯一允许的跨族推导

```
人格/自评标签  →  PROCESSING   ✅  这正是这些量表测的东西
任何东西       →  DOMAIN       ❌  除了 hobby / domain / source / edu / topic
                                    —— 这五族说的是「他实际在做什么」
年龄/性别/国家 →  DOMAIN       ❌  永远不推
国家           →  reads_<lang> ❌  住日本 ≠ 读日语
```

**你懂哪些词，取决于你在做什么，不取决于你是谁。** 所以只有 hobby / domain / source / edu / topic
带 `grants`。`test_only_doing_families_grant_vocabulary` 遍历全部标签守这一点。
儿童标签是唯一的人口统计学例外：它只加 PROCESSING（短句、术语全解释、先给具体例子），
因为那是识字负荷，不是猜圈子。青少年不加 `define_terms`。

MBTI → 排版走**八维**，不是硬编码 16 条：取主导 + 辅助功能，各自的 `implies` 求并。
INTJ = Ni + Te → `context_first` + `conclusion_first` + `no_padding`。可审、可解释。

`derive_processing_tags()` 里两句 assert：不许产出 domain 标签，且产出必须全在
PROCESSING 族内。未知标签抛 `UnknownTagError` 并给出拼写建议。

### 7.2c 标签冲突不让先写的那条赢

INFP = Fi（要流畅）+ Ne（要短行），同时声明的 load_sensitivity 又指向长句 ——
`short_chunks` 和 `long_chunks` 同时成立。这时**回落到默认容量 26**，
而不是让代码里先判断的那个分支赢。证据矛盾就是矛盾，不该由书写顺序决定。

### 7.2d 语言切换

`catalog(lang)` / `label(id, lang)` / `describe(tags, lang)` 全部中英可切，
连分隔符都跟着切（中文「、」/ 英文 ", "）。HTTP：`GET /v1/tags?lang=en&family=mbti`。

**切的只有标签和界面文字 —— 说话人的原话永远不翻译。** 翻译原话＝改说话人。

### 7.2e 新增的三个操作（都已实现，不是纸面标签）

| 标签 | 操作 | 做什么 | 依据 |
|---|---|---|---|
| `sequence_explicit` | **A9 步骤分行** | 先/然后/最后 各占一行 | Lorch 1989 文本信号化；Si / 尽责性高 |
| `concrete_first` | A8 变体 | 含数字或实例的支撑句提前 | Paivio 1971 双重编码；Se / 开放性低 |
| `define_terms` | 覆盖 T1 | 不管他懂不懂，术语一律换白话 | 不熟的人 / 没接触过 / 朋友说的 |

### 7.2f Cerome 数值 → PROCESSING（与标签并行的第二条来源）

| 已声明数值 | → PROCESSING 标签 | 依据 |
|---|---|---|
| `L2.efficiency ≥ .7` 或 `L1.pace ≥ .65` | `conclusion_first` → A3 | 首句优势 |
| `L2.precision ≥ .7` 或 `L2.clarity ≥ .75` | `cause_explicit` → A5 | 因果衔接收益 |
| `L1.load_sensitivity ≥ .7` / `≤ .4` | `short_chunks` / `long_chunks` → A4 容量 | 工作记忆 |
| `L2.warmth ≥ .7` 或 `L1.empathy_need ≥ .7` | `tone_visible` → A7 + 保留语气词 | 语气连续性 |
| `L2.efficiency ≥ .8` 且 `L2.warmth ≤ .4` | `no_padding` → 可删语气词 | 低努力偏好 |

**注意 `L3.comprehension_gaps`（自由文本）不再触发任何操作。** 它是描述，不是标签。

### 7.3 T1 改成按词的领域归属

`JARGON_TABLE` 每条是 `词 → (白话, 领域)`。翻不翻译 =
**这个词的领域**是否在**这个人声明的领域**里。同一位 INTJ 听者，声明 `tech` 前后：

```
INTJ（无 domain 标签）  因为接口老是响应太慢。
INTJ + tech,business    因为接口老是超时。
```

给已经懂「排期」的人翻译成「时间安排」反而更难读（Clark & Murphy 1982 audience design）。

### 7.4 「打游戏」不是一个标签，是 26 个

the author 2026-08-13：「你要知道打游戏的话，那具体是什么游戏？不同的游戏，它的性格都不一样。」

**为什么必须拆。** 游戏圈层之间是**互相听不懂**的，粗标签会在两边都判断错：

| 词 | 第五人格玩家 | 原神玩家 | 只点了「打游戏」 |
|---|---|---|---|
| 守椅 | 每天在说 → 保留 | 没听过 → 翻译 | 翻译 |
| 保底 | 没听过 → 翻译 | 每天在说 → 保留 | 翻译 |
| 开黑 | 保留 | 保留 | 保留（通用） |

实测同一句 `监管者一直守椅，我们保底都没抽出来，只能开黑再上分`：

```
只点「打游戏」   追人的一方一直守着倒地的人不走。我们抽够次数一定出都没抽出来。只能开黑再上分。
玩第五人格       监管者一直守椅。我们抽够次数一定出都没抽出来。只能开黑再上分。
玩原神           追人的一方一直守着倒地的人不走。我们保底都没抽出来，只能开黑再上分。
两个都玩         监管者一直守椅，我们保底都没抽出来。只能开黑再上分。
完全不玩         全部翻译，包括 开黑→组队、上分→打排位升段
```

**父子回滚（`parent`）。** 每个游戏标签 `parent = hobby_gaming`。选「第五人格」自动
同时拿到 `asym_horror` + `gaming`，所以他既懂「守椅」也懂「开黑」。反过来只选
「打游戏」就只拿通用词 —— **懒得挑的人不会因此被判断错，只是被判断得保守。**

番 / 小说 / 剧 / 歌同一套：点「二次元」拿 `anime`+`fandom` 通用圈词；搜「鬼灭」「柯南」
才挂到具体作品。网文 → `webnovel`（金手指/穿越），韩剧/美剧 → `film_tv`（彩蛋/烂尾），
韩团 → `idol`（出道/打投）。没有审计过的对应词就不类比，退回白话 T1。

**游戏 → PROCESSING 只放曝光事实，不推性格。** 竞技射击/MOBA → `short_chunks`
（习惯短促报点）；P 社/文字冒险 → `long_chunks`（习惯长文本）。这是「他每天读什么
形状的字」，和「他是什么人」无关。多数游戏标签的 `implies` 是空的。

**歧义词一律不收（`AMBIGUOUS_BLOCKLIST`）。** 「毕业」在抽卡圈是练满、在校园是真毕业；
「肝」既是器官也是动词；「屠夫」在第五人格是监管者、在生活里是真屠夫。这类词一旦进表，
系统会在错误语境里**把用户的原话改成另一个意思** —— 那比不翻译严重得多。
`test_no_ambiguous_word_is_ever_substituted` 常驻守这条线。

### 7.5 标签越多，设置必须越简单

the author 同一段：「不是为了真实性，不是为了专业，而是为了让用户能随时使用，
能够轻易看懂，能够轻易设置。」所以细化的同时加了一层：

| 机制 | 做什么 |
|---|---|
| `common` 标记 | 默认只显示常见的那几个，其余搜索可见 —— 爱好首屏 18 个，不是 88 个 |
| `aliases` 别名 | 打「农药」「吃鸡」「idv」「mc」「lol」都能命中正确的游戏 |
| `parent` 回滚 | 不想挑就点「打游戏」，一样能用 |
| `quick_setup()` | 整个设置页 = **5 个问题**，全部可跳过，一个标签不填也能跑 |

五个问题就是：**MBTI（可跳过）／你们什么关系／他平时玩什么（游戏/番/小说/剧/歌都能搜）／年龄、国家、在读什么、关心什么、会读什么语言／他自己怎么说话。**

HTTP：`GET /v1/tags?q=王者&lang=zh`（搜索）、`GET /v1/tags?all=1`（完整列表）、
`GET /v1/tags/setup?lang=en`（整个设置流程一次拿到）。
演示：`python tests/run_games_demo.py [zh|en]`。

### 7.6 黑话怎么来：爬虫找候选，人审核后才进表（不是 AI 猜）

the author 2026-08-14 纠正：公开数据本来就是给人看的,统计词频做资料是合理用途——之前把
"爬虫"和"确定性可审计"混为一谈是错的,那条硬约束只管**运行时引擎怎么用词表**,
不管**词表里的词最初怎么被发现**。

三段流水线（`clarityime/clarify/glossary_mining.py`）：

```
1. 采集（本模块之外）  只抓公开帖子/评论/话题标签，绝不抓私聊/登录墙内内容
2. 挖掘（本模块）      纯频次统计，零 AI：某词在某圈子里高频、在别的圈子罕见 → 候选
3. 人审                人读候选表，手写白话释义，才真正搬进 JARGON_TABLE
```

第 2 步不判断"这个词是什么意思"——那是推断,是 the author 明确禁止的。它只回答一个事实
问题："这个词在这个圈子里出现的频率，是不是明显高于其他圈子？"（`specificity`）。
真正决定"翻译成什么"的，永远是人工审核这一步。

`test_glossary_mining.py::test_mining_is_deterministic` 和
`test_review_queue_never_touches_jargon_table` 守住两条线：同一批语料挖出来的候选
顺序完全一样；候选队列文件只是给人看的，系统本身从不读它、不会自动升级成正式词条。

### 7.7 语言：架构是「一种语言一张表」

听者读哪种语言由 `reads_<code>` 决定（中/英/日/韩首屏可见，粤语、繁体、法德西阿葡俄意
越泰印尼等靠搜索）。`ListenerPlan.reading_lang` 多选时取字典序最小，保证确定性。

`JARGON_TABLES` 目前填了 **zh / en / ja / ko**。繁体中文和粤语书面语走中文表
（`canonical_jargon_lang`），不是另猜一套翻译。其余语言标签可选、不报错，只是 T1 空转。
加一种语言的真实词条仍走 7.6：公开语料 → 挖掘 → **人写白话** → 进表。不从中文表自动翻译。

---

## 7bis. 口语化：一个一个判，不是一张黑名单

> the author：「有时候口语化可能会有意思，有时候口语化没有意思。」

同样两个字，位置不同就是两个东西。`clarityime/clarify/oral.py` 对**每一次出现**给三种判决：

| 判决 | 含义 | 能删吗 |
|---|---|---|
| `NOISE` | 迟疑、占位 | 删 |
| `MEANING` | 有命题力的话语标记 | **永不删** |
| `TONE` | 语气 / 缓和 | 仅当听者标了 `no_padding` |

| 例子 | 判决 | 理由 |
|---|---|---|
| **就是**我觉得还行 | NOISE | 句首迟疑 |
| 方案还行，**就是**风险有点多 | MEANING | = 只不过，限定性转折 |
| 嗯那个，**就是**我觉得… | NOISE | 前一段全是填充，仍是迟疑 |
| **其实**我不太同意 | MEANING | 反预期标记（Wang & Huang 2006） |
| **那个**功能先关掉 | MEANING | 指示词，不是迟疑 |
| 你先做**吧** | TONE | 句末缓和，删掉就改了语力 |
| 先写完，**然后**交上去，**然后然后**再说 | 第一个 MEANING，其余 NOISE | 首个标真实时序 |

---

## 7ter. 意思要拆到细节，不是整句

> the author：「这个意思不是一个 vague 的意思，不是一个整体的意思，而是很细的
> —— 每个细节可能都有意思，而不是一整个句子的意思。」

`clarityime/clarify/details.py` 把每句拆成带角色的 **detail unit**：
`stance / degree / epistemic / cause / concession / condition / request / negation / affect / sequence / quantity`。

「我觉得还行，不过周期有点长」不是一个意思，是四个：
`stance:我觉得`、`degree:还行`、`concession:不过`、`degree:有点`。

**保全的单位是 detail，不是句子也不是字符集。**
`有点长 → 长` 字符没少几个，但 `degree:有点` 丢了 —— 判定失败，回退原文。
`adapt_with_report` 每次都跑 `detail_diff(reference, adapted)`，丢一个就 fallback。

---

## 7quater. 全平台怎么做到「对方总能看到原句」：链接，不是原生 UI

> the author（2026-08-14）：「我希望全平台都可以支持……有没有其他办法？这些平台有没有
> 什么共用的适配机制……我其实想在每条内容里都附带链接，让对方总能看到原句。」

**先说清楚做不到的部分**：微信/QQ/Discord/Instagram/iMessage/WhatsApp 都不给
第三方 app 在**对方**的聊天气泡里插自定义 UI，它们各自的「翻译」按钮是封闭的
（语言↔语言，不能接第三方 provider）。这不是我们工程能力不够，是平台不开这个口子。
唯一两条真实存在的路：

| 路 | 覆盖 | 现实吗 |
|---|---|---|
| **发送端**：IME 在打字时就替换文本 | 全平台，因为是 OS 输入层，不依赖任何 app 配合 | ✅ **ClarityIME 本来就是这个**，天然全平台 |
| **接收端**：Android AccessibilityService 读屏叠加翻译 | 仅 Android，iOS 无对应能力 | ⚠️ 脆、易随 UI 改版失效、Google Play 对滥用无障碍 API 有政策风险 |

所以「全平台原生 UI」本身不是一个可行选项——但**链接**是，因为链接只是文本，
而所有聊天软件都会把 `https://...` 自动变成可点击的东西。这正好等于 the author 想要的
「对方总能看到原句」，用户不需要装任何 App。

**为什么 payload 放在 URL 的 `#` 后面，而不是存在服务器上**：
`https://clarityime.app/c#<payload>` —— `#` 之后的部分（fragment）浏览器
**不会**放进 HTTP 请求里发给服务器；一个纯静态、无状态的页面在浏览器里用 JS
读 `location.hash` 解码渲染即可。也就是说：分享这条消息**不需要我们运营一个
存储别人聊天内容的云服务**——和这个项目"本地优先、不留痕"的架构前提
（`GET /v1/security/status → loopback_only`）保持一致。

**和已有的 `utterance_bundle.py` 的区别**：那个模块产出
`http://127.0.0.1:17800/...`，只能在**发送者自己这台机器**上打开，专门给
"发送前自己看 N-best 候选"用；本模块（`clarityime/share_link.py`）产出的链接
是给**收信人**点的，两者场景不同，不是重复。

**实现**（`clarityime/share_link.py`）：
- `SharePayload(original, for_listener, listener_tags)` → base64url JSON 编码
  的 fragment，`v` 字段做 schema 版本号，确定性编码（同输入同输出）。
- 损坏的 / 版本不认识的 fragment 直接 `ValueError`，不猜测渲染——和整份文档
  「宁可 fallback 原文，不猜」的一贯原则一致。
- `append_share_link()` 挂在 `clarify()` 里，默认 **on**（`settings.py` 新增
  `attach_original_link: bool = True`），两句话完全一样时不加（没有额外信息
  可看，加了反而是噪音），可在 `/v1/settings` 关掉换成"干净版"。

**还没做的**（部署任务，不是这轮的代码任务）：`clarityime.app/c` 这个静态
查看页面本身需要真的部署上线；`SHARE_VIEWER_BASE` 目前只是一个占位域名，
编码/解码/拼接逻辑已经是真实可跑、有测试（`tests/test_share_link.py`）的。

---

## 7quinquies. 不用每次手动建对象：反馈驱动的自动学习，像相册认脸

> the author（2026-08-14）：「让每个人专门去给对方创建一个对象，有些人可能没有那个
> 耐心……系统可以自动学习对方的喜好和消息风格，就像相册自动识别一样。」

**这是不是在推翻 `cerome/tags.py` 那条「不许从标签推标签」的硬规则？** 不是，
两者回答的是不同问题：

| | 禁止的做法 | 这里做的做法 |
|---|---|---|
| 证据来源 | 人格描述（"他是 INTJ"） | **这个具体的人**给的反馈 |
| 推的方向 | 人格 → 猜他懂什么词汇圈 | 「这句翻译他打了 3 次差评」→ 别再翻这个域了 |
| 类比 | 看星座算命 | 相册被纠正 3 次「这不是爸爸」后不再建议这个标签 |

`cerome/tags.py` 禁止的是**没有证据的猜测**；这里靠的是**这个人自己给的、
带时间戳、可审计的行为证据**——纯计数，不是 AI 推断语义。

**机制**（`clarityime/cerome/contact_learning.py`）：

1. 对方发一条被简化过黑话的消息（比如把「ddl」翻成「截止时间」），the author 觉得
   翻得没必要（对方明明听得懂），打差评。
2. 系统只记一件事：「domain=tech 这一域，又被打了一次差评」。
3. **连续净差评（差评数－好评数）≥ 3 次**（`AUTO_LEARN_THRESHOLD`）→ 自动给
   这个联系人挂上"他懂 tech 域"的标记，下次自动不再翻译这一域。
4. 如果之后又攒够 3 次好评（说明翻了反而合适），**自动撤销**——完全对称，
   跟撞脸后又被纠正回来一样。
5. 每一步都留证据（`domain_feedback_counts` 里的 `evidence` 列表，最近 10 条，
   带时间戳），设置页随时能看到"为什么系统觉得他懂这个词"，也能一键
   `forget_domain()` 手动撤销——**这就是"改标签"，不是删数据**。

**关键设计决定**：

- **只学"域"，不学"人格标签"**——学到的是 `auto_learned_domains`（如
  `tech`、`moba`），而不是反推出"这个人是 INTJ"或"他喜欢打游戏"这类标签。
  这样就不会把一次具体的反馈过度泛化成整个人格画像。
- **联系人可以从空对象开始**——不需要先做 `quick_setup()` 才能用。
  `ContactProfile(id=None, name="小明")` 就能直接收反馈，随对话自然长出
  `auto_learned_domains`，这正是 the author 要的"不用每个人都手动建对象"。
- **`define_terms` 标签仍然优先于自动学习**——用户显式要求"什么都给我解释"
  时，哪怕系统已经学到这个人懂某个域，也照样翻译，人的显式设置永远压过
  行为推断。
- **确定性**：同一串反馈序列，无论何时重放，结果完全一样（见
  `tests/test_contact_learning.py::test_deterministic_same_sequence_same_outcome`）。

**两条路径**（the author 2026-08-14：「默认对象可以给出提示……用户选择是或否之后，系统就会自动创建」）：

| 当前听众 | 跨过阈值时发生什么 |
|---|---|
| **已选定某个对象** | 静默把域挂上这个对象，继续学。不弹窗。 |
| **大众 / 默认对象（没选人）** | **不**偷偷建档。UI 问「要为他建一个新对象吗？」点「是」→ 自动创建 `对象 N`（也可自己起名）；点「否」→ 这次不建，计数清零，攒够新证据会再问一次。 |

`GET /v1/contacts/suggestions` 列出待确认的提示；`POST /v1/feedback` 带 `resolve_suggestion` 回答。点「是」且没填名字时走 `next_auto_object_name()`，和相册「这是同一个人吗？→ 新建人物」一样。

---

## 7sexies. 跨圈类比混进日常输出（不是单独模式）

> the author（2026-08-14）：「可以，混进去。」——听者不必先问「能不能用我那个游戏解释」。
> 社区原话：「我是玩 A 的，能不能用 A 的方式给我解释一下这件事情是怎么发生的？」

**这不是生成一段新解释。** 和 T1 同一条管线、同一套审计表：

| 听者对这个词的域 | 输出 |
|---|---|
| **自己圈的词**（声明了 / 自动学到了） | 原词不动 |
| **外圈，但表里有他圈的对应词** | 原词保留 + 夹一句「就像 X」：`守椅（就像架点）` |
| **外圈，表里没有对应** | 原来的白话 T1：`守椅` → `守着倒地的人不走` |

Gentner (1983) structure-mapping：类比传的是**角色**（守住倒地的人 ≈ 架住一个点），不是宣称两件事是同一个东西。所以原词留着，避免把第五人格说成 CS。

**硬规则（和整份文档一致）**：

- 映射是人手写的 `clarityime/clarify/analogy.py`，**不**从爬虫/AI 自动反推。没有行 = 不类比。
- 多个他圈都有对应时，按 domain id 字母序取一个（与 `reading_lang` 同款确定性）。
- `define_terms` 仍是「全部变白话」，不走类比。
- 不另开模式、不加第二段话、不把原句换成另一句游戏攻略。

---

## 8. 实现现状与平台差距

| 位置 | 状态 |
|---|---|
| `clarityime/clarify/comprehension.py` | A1–A7 全部实现 + 不变量 + 成本度量 |
| `clarityime/clarify/listener_adapt.py` | Cerome → 操作集；违反不变量自动回退原文 |
| STRUCTURED 模式 | 走同一引擎 + `NEUTRAL` 通用听者 |
| CONTACT 模式 | 走同一引擎 + 联系人 Cerome |
| Android / iOS / Windows 离线规则 | **仅有分句分段**，无 A1/A2/A3 —— 属降级路径，联网到本地 server 时以核心为准 |

自查脚本：
- `python tests/run_listener_presets.py` — 每个听者的成本前后 + 不变量
- `python tests/run_benchmark.py` — 6 个真实口语场景的基准

### 当前基准结果（2026-08-12，6 场景 × 4 听者）

| listener | 平均理解成本下降 | 行话消除 |
|---|---|---|
| d_type (INTJ) | **-100%** | 0（圈内人，保留术语） |
| a_type (ENTP) | **-100%** | 0（同上） |
| i_type (INFJ) | **-100%** | 10 |
| s_type (INFP) | **-89.6%** | 10 |

历史：首版（仅换行）d/a/i 约 -83%、s_type 仅 **-14.8%**。
补上 T1–T3 改写 + 无标点 run-on 切分 + flow 也守工作记忆容量后到达上表。

---

## 9. 参考文献

1. Kintsch, W., & van Dijk, T. A. (1978). Toward a model of text comprehension and production. *Psychological Review*, 85(5), 363–394.
2. Kintsch, W. (1988). The role of knowledge in discourse comprehension: A construction-integration model. *Psychological Review*, 95(2), 163–182.
3. Gernsbacher, M. A. (1990). *Language Comprehension as Structure Building*. Erlbaum.
4. Haviland, S. E., & Clark, H. H. (1974). What's new? Acquiring new information as a process in comprehension. *JVLVB*, 13(5), 512–521.
5. Britton, B. K., & Gülgöz, S. (1991). Using Kintsch's computational model to improve instructional text. *Journal of Educational Psychology*, 83(3), 329–345.
6. Graesser, A. C., McNamara, D. S., Louwerse, M. M., & Cai, Z. (2004). Coh-Metrix. *Behavior Research Methods*, 36(2), 193–202.
7. McNamara, D. S., Kintsch, E., Songer, N. B., & Kintsch, W. (1996). Are good texts always better? *Cognition and Instruction*, 14(1), 1–43.
8. Sanders, T., & Noordman, L. (2000). The role of coherence relations and their linguistic markers. *Discourse Processes*, 29(1), 37–60.
9. Trabasso, T., & van den Broek, P. (1985). Causal thinking and the representation of narrative events. *JML*, 24, 612–630.
10. Sweller, J. (1988). Cognitive load during problem solving. *Cognitive Science*, 12(2), 257–285.
11. Cowan, N. (2001). The magical number 4 in short-term memory. *BBS*, 24(1), 87–114.
12. Lorch, R. F. (1989). Text-signaling devices and their effects. *Educational Psychology Review*, 1, 209–234.
13. Reber, R., & Schwarz, N. (1999). Effects of perceptual fluency on judgments of truth. *Consciousness and Cognition*, 8(3), 338–342.
14. Reber, R., Schwarz, N., & Winkielman, P. (2004). Processing fluency and aesthetic pleasure. *PSPR*, 8(4), 364–382.
15. Petty, R. E., & Cacioppo, J. T. (1986). *Communication and Persuasion: Central and Peripheral Routes*. Springer.
16. Sperber, D., & Wilson, D. (1995). *Relevance: Communication and Cognition* (2nd ed.). Blackwell.
17. Clark, H. H., & Brennan, S. E. (1991). Grounding in communication. In *Perspectives on Socially Shared Cognition* (pp. 127–149). APA.
18. Li, C. N., & Thompson, S. A. (1981). *Mandarin Chinese: A Functional Reference Grammar*. UC Press.
19. Zwaan, R. A., & Radvansky, G. A. (1998). Situation models in language comprehension and memory. *Psychological Bulletin*, 123(2), 162–185.
