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
| A7 | **连贯流式**（高共情听者不切碎） | McNamara 1996 逆衔接效应 | ❌ 只合并换行 |

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
5. DETERMINISTIC    : 同输入 + 同听者 → 同输出
```

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

## 7. Cerome 听者 → 操作集映射

操作集**由 Cerome 数值推出**，MBTI 只作为填数值的先验，不硬编码。

| Cerome 条件 | 触发操作 | 依据 |
|---|---|---|
| `L2.efficiency ≥ 0.7` 或 `L1.pace ≥ 0.65` | A3 结论前置 | 首句优势 + 低努力偏好 |
| `L2.precision ≥ 0.7` | A5 因果信号化 | 因果衔接收益 |
| `L1.load_sensitivity` 高 | A4 更小意群 | 认知负荷 |
| `L2.warmth ≥ 0.75` 或 `L1.empathy_need ≥ 0.75` | A7 流式（不切碎） | 逆衔接效应 / 语气连续性 |
| `L3.comprehension_gaps` 非空 | A1 + A2 强制 | 低背景知识者获益最大 |

---

## 8. 实现现状与平台差距

| 位置 | 状态 |
|---|---|
| `clarityime/clarify/comprehension.py` | A1–A7 全部实现 + 不变量 + 成本度量 |
| `clarityime/clarify/listener_adapt.py` | Cerome → 操作集；违反不变量自动回退原文 |
| STRUCTURED 模式 | 走同一引擎 + `NEUTRAL` 通用听者 |
| CONTACT 模式 | 走同一引擎 + 联系人 Cerome |
| Android / iOS / Windows 离线规则 | **仅有分句分段**，无 A1/A2/A3 —— 属降级路径，联网到本地 server 时以核心为准 |

自查脚本：`python tests/run_listener_presets.py`（打印每个听者的成本前后对比与不变量结果）。

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
