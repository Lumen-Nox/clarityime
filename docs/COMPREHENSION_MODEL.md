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
| **T2** | **去名词化**：进行一次复盘 → 复盘 | Halliday & Martin 1993 语法隐喻 | ❌ 删空动词 |
| **T3** | **去冗余**：的话／这样子／…的处理 | 外在负荷 | ❌ 删虚词 |

### T1 为什么安全

T1 是**固定本地表**（`clarify/paraphrase.py`，一屏可读完），不是生成。
所以不存在"AI 编了一个意思"——最差情况是表里某一条写错了，而表是人能逐条审的。
每次替换都进 `substitutions` 审计字段返回给 UI。

**听者是圈内人就不替换**（audience design，Clark & Murphy 1982）。
判据是**这个词的领域**是否在**这个人声明的 domain 标签**里 —— 见 §7.3。
Personality presets never carry domain tags: INTJ ≠ knows tech jargon.

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

> Design rule: rules key on **tags**, not free-text descriptions or guesses.
> One tag program per tag family — not one bespoke program per person.

### 7.1 被这条规则杀掉的 bug

早期版本给 `d_type`（INTJ）预设写了 `knows_tech=True`，于是「超时/复盘」对他不翻译。
**This was fabricated.** A personality tag alone never implied tech domain knowledge.
Personality tags describe **how someone processes** information, not **which vocabulary they know** — two families, no cross-inference.

### 7.2 标签库：120 个标签，12 族（`clarityime/cerome/tag_registry.py`）

按**真人自我描述的方式**设计，不是按我方便实现的方式。每个标签中英双语。

| 族 | 数量 | 例子 | 能授予词汇？ | 能影响排版？ |
|---|---|---|---|---|
| **mbti** | 16 | INTJ·建筑师、ENFP·竞选者 | ❌ | ✅ 经八维 |
| **function** 八维 | 8 | Ni 内倾直觉、Te 外倾思考 | ❌ | ✅ |
| **bigfive** | 10 | 尽责性高、宜人性低、神经质高 | ❌ | ✅ |
| **enneagram** 九型 | 9 | 3号·成就型、9号·和平型 | ❌ | ✅ |
| **selfdesc** 怎么描述自己 | 6 | 爱用比喻／爱用数据／爱用故事／爱用标签 | ❌ | ✅ |
| **source** 从哪认识的 | 7 | 网上测过 16personalities／上过心理学课／小红书刷到的／朋友说的 | ✅ | ✅ |
| **hobby** 爱好 | 22 + **26 个具体游戏** | 打游戏 → 第五人格／原神／王者／Minecraft… | ✅ | 少数 ✅ |
| **domain** | 24 | 技术、职场、校园…＋ **11 个游戏子圈**（moba/fps/gacha/asym_horror…） | ✅ | ❌ |
| **register** 他怎么说话 | 8 | 说话很直、爱用「可能/好像」、爱用网络梗 | ❌ | ✅ |
| **relation** | 7 | 老师、同学、好朋友、不熟的人 | ❌ | ✅ |
| **lang** | 3 | 读中文／读英文／中英都行 | ❌ | ❌ |
| **processing** | 11 | 先给结论、步骤分行、先给具体例子、术语一律解释 | — | 就是它本身 |

### 7.2b 唯一允许的跨族推导

```
人格/自评标签  →  PROCESSING   ✅  这正是这些量表测的东西
任何东西       →  DOMAIN       ❌  除了 hobby / domain / source
                                    —— 那三族说的是「他实际在做什么」
```

**你懂哪些词，取决于你在做什么，不取决于你是谁。** 所以只有 hobby / domain / source
带 `grants`。`test_only_doing_families_grant_vocabulary` 遍历全部 120 条来守这一点，
`test_no_personality_tag_grants_vocabulary` 对 43 个人格标签逐个查 `expand()` 结果为空。

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
**这个词的领域**是否在**这个人声明的领域**里。同一个 D，声明 `tech` 前后：

```
D（无 domain 标签）  因为接口老是响应太慢。
D + tech,business    因为接口老是超时。
```

给已经懂「排期」的人翻译成「时间安排」反而更难读（Clark & Murphy 1982 audience design）。

### 7.4 「打游戏」不是一个标签，是 26 个

**Gaming is not one tag — pick the specific title.** Different games use different jargon.

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

**Game → PROCESSING only records exposure facts, not personality.** Competitive shooters/MOBA → `short_chunks`
（习惯短促报点）；P 社/文字冒险 → `long_chunks`（习惯长文本）。这是「他每天读什么
形状的字」，和「他是什么人」无关。多数游戏标签的 `implies` 是空的。

**歧义词一律不收（`AMBIGUOUS_BLOCKLIST`）。** 「毕业」在抽卡圈是练满、在校园是真毕业；
「肝」既是器官也是动词；「屠夫」在第五人格是监管者、在生活里是真屠夫。这类词一旦进表，
系统会在错误语境里**把用户的原话改成另一个意思** —— 那比不翻译严重得多。
`test_no_ambiguous_word_is_ever_substituted` 常驻守这条线。

### 7.5 标签越多，设置必须越简单

Design goal: settings stay simple — usability over exhaustive taxonomy.

| 机制 | 做什么 |
|---|---|
| `common` 标记 | 默认只显示常见的那几个，其余搜索可见 —— Q3 首屏 9 个而不是 48 个 |
| `aliases` 别名 | 打「农药」「吃鸡」「idv」「mc」「lol」都能命中正确的游戏 |
| `parent` 回滚 | 不想挑就点「打游戏」，一样能用 |
| `quick_setup()` | 整个设置页 = **4 个问题**，全部可跳过，一个标签不填也能跑 |

四个问题就是：**他是什么 MBTI（不知道就跳过）／你们什么关系／他平时玩什么／他自己怎么说话。**

HTTP：`GET /v1/tags?q=王者&lang=zh`（搜索）、`GET /v1/tags?all=1`（完整列表）、
`GET /v1/tags/setup?lang=en`（整个设置流程一次拿到）。
演示：`python tests/run_games_demo.py [zh|en]`。

### 7.6 黑话怎么来：爬虫找候选，人审核后才进表（不是 AI 猜）

Public posts/comments are fair game for frequency mining; the hard constraint is **runtime** must not infer meanings — only use human-audited tables.

三段流水线（`clarityime/clarify/glossary_mining.py`）：

```
1. 采集（本模块之外）  只抓公开帖子/评论/话题标签，绝不抓私聊/登录墙内内容
2. 挖掘（本模块）      纯频次统计，零 AI：某词在某圈子里高频、在别的圈子罕见 → 候选
3. 人审                人读候选表，手写白话释义，才真正搬进 JARGON_TABLE
```

Step 2 never guesses "what does this word mean?" — only: "is this term unusually frequent in this community vs others?" (`specificity`).
真正决定"翻译成什么"的，永远是人工审核这一步。

`test_glossary_mining.py::test_mining_is_deterministic` 和
`test_review_queue_never_touches_jargon_table` 守住两条线：同一批语料挖出来的候选
顺序完全一样；候选队列文件只是给人看的，系统本身从不读它、不会自动升级成正式词条。

### 7.7 语言：8 + 1 种新增，架构是「一种语言一张表」

Roadmap: zh/en first; ja/ko/fr/de/es/ar/pt/yue tables follow the same human-review pipeline.

`JARGON_TABLES: dict[lang, dict[词, (白话, 领域)]]`——加一种语言 = 加一个条目，
引擎本身（`simplify_jargon(..., lang=...)`）不用改。听者读哪种语言由
`reads_<code>` 标签决定（`lang` 族现在是 9 个标签：zh/yue/en/ja/ko/fr/de/es/ar/pt），
`ListenerPlan.reading_lang` 从标签里取，多选时取字典序最小的那个，保证确定性。

**目前只有 `zh` 和 `en` 两张表填了真实词条**（`en` 是起步集：deadline/gg/gank/pity 等）。
剩下 8 种语言的标签**已经可以选**（不会报"未知标签"），但对应的 `JARGON_TABLES["ja"]`
等还是空表——选了这些语言的听者会跳过 T1 翻译,不会报错,也不会翻错。
每加一种语言的真实词条，同样走 7.6 的三段流水线：采集该语言的公开语料 → 挖掘 →
人工写白话 → 填进 `JARGON_TABLES[lang]`。

---

## 7bis. 口语化：一个一个判，不是一张黑名单

> Some oral particles are noise; others carry discourse meaning — classify per occurrence.

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

> Meaning is not one vague whole — preserve each detail unit, not just the sentence surface.

`clarityime/clarify/details.py` 把每句拆成带角色的 **detail unit**：
`stance / degree / epistemic / cause / concession / condition / request / negation / affect / sequence / quantity`。

「我觉得还行，不过周期有点长」不是一个意思，是四个：
`stance:我觉得`、`degree:还行`、`concession:不过`、`degree:有点`。

**保全的单位是 detail，不是句子也不是字符集。**
`有点长 → 长` 字符没少几个，但 `degree:有点` 丢了 —— 判定失败，回退原文。
`adapt_with_report` 每次都跑 `detail_diff(reference, adapted)`，丢一个就 fallback。

---

## 7quater. 全平台怎么做到「对方总能看到原句」：链接，不是原生 UI

> Cross-platform requirement: attach a link so recipients can always see the original text.

**先说清楚做不到的部分**：微信/QQ/Discord/Instagram/iMessage/WhatsApp 都不给
第三方 app 在**对方**的聊天气泡里插自定义 UI，它们各自的「翻译」按钮是封闭的
（语言↔语言，不能接第三方 provider）。这不是我们工程能力不够，是平台不开这个口子。
唯一两条真实存在的路：

| 路 | 覆盖 | 现实吗 |
|---|---|---|
| **发送端**：IME 在打字时就替换文本 | 全平台，因为是 OS 输入层，不依赖任何 app 配合 | ✅ **ClarityIME 本来就是这个**，天然全平台 |
| **接收端**：Android AccessibilityService 读屏叠加翻译 | 仅 Android，iOS 无对应能力 | ⚠️ 脆、易随 UI 改版失效、Google Play 对滥用无障碍 API 有政策风险 |

所以「全平台原生 UI」本身不是一个可行选项——但**链接**是，因为链接只是文本，
而所有聊天软件都会把 `https://...` 自动变成可点击的东西。这正是「对方总能看到原句」

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

> Users should not have to manually create an audience object for every recipient — learn from feedback like photo-app face learning (threshold 3, no LLM).

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

1. Recipient receives jargon simplified (e.g. 「ddl」→「截止时间」); sender rates it unnecessary.
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
  `auto_learned_domains` — no manual object setup required.
- **`define_terms` 标签仍然优先于自动学习**——用户显式要求"什么都给我解释"
  时，哪怕系统已经学到这个人懂某个域，也照样翻译，人的显式设置永远压过
  行为推断。
- **确定性**：同一串反馈序列，无论何时重放，结果完全一样（见
  `tests/test_contact_learning.py::test_deterministic_same_sequence_same_outcome`）。

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
