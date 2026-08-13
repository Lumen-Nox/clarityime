"""设置有多简单 + 游戏拆细有多必要。

    python tests/run_games_demo.py        # 中文
    python tests/run_games_demo.py en     # English
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clarityime.cerome.listener_presets import PRESETS
from clarityime.cerome.tag_registry import quick_setup, search
from clarityime.cerome.tags import describe, listener_tags
from clarityime.clarify.listener_adapt import adapt_with_report
from clarityime.clarify.local_rules import preserve_original

LANG = (sys.argv[1] if len(sys.argv) > 1 else "zh").lower()
ZH = LANG.startswith("zh")
BAR = "=" * 72


def h(text: str) -> None:
    print(f"\n{BAR}\n{text}\n{BAR}")


# --------------------------------------------------------------------------- #
h("1. 设置流程：四个问题，全部可跳过" if ZH else "1. Setup: four questions, all skippable")

for i, step in enumerate(quick_setup(LANG), 1):
    opts = step["options"]
    kind = ("多选" if step["multi"] else "单选") if ZH else ("multi" if step["multi"] else "single")
    print(f"\nQ{i} [{kind}] {step['question']}")
    print("   " + " / ".join(o["label"] for o in opts[:8]))
    if len(opts) > 8:
        more = f"…还有 {len(opts) - 8} 个，搜索可见" if ZH else f"…{len(opts) - 8} more via search"
        print(f"   {more}")

h("2. 搜索：打俗称就能找到" if ZH else "2. Search: nicknames work")
for q in ("王者", "农药", "idv", "吃鸡", "genshin", "mc", "intj"):
    hits = search(q, LANG, limit=3)
    print(f"  「{q}」 → " + ", ".join(f"{r['label']}" for r in hits))

# --------------------------------------------------------------------------- #
LINE = "监管者一直守椅，我们保底都没抽出来，只能开黑再上分"
original, _ = preserve_original(LINE)

h("3. 同一句话，玩不同游戏的人收到的不一样" if ZH else "3. Same sentence, different players")
print(f"\n原话 / RAW: {LINE}\n")

PEOPLE = [
    ("只点了「打游戏」", ["mbti_entp", "hobby_gaming"]),
    ("玩第五人格", ["mbti_entp", "game_idv"]),
    ("玩原神", ["mbti_entp", "game_genshin"]),
    ("两个都玩", ["mbti_entp", "game_idv", "game_genshin"]),
    ("完全不玩游戏", ["mbti_entp"]),
]

for name, tags in PEOPLE:
    who = replace(PRESETS["a_type"], tags=tags)
    res = adapt_with_report(original, who)
    owned = sorted(listener_tags(who).domains())
    print(f"— {name}")
    print(f"  懂的词汇圈: {', '.join(owned) or '(无)'}")
    for line in res.text.splitlines():
        print(f"  {line}")
    if res.substitutions:
        print("  换掉的词: " + ", ".join(f"{s.src}→{s.dst}" for s in res.substitutions))
    print()

# --------------------------------------------------------------------------- #
h("4. 标签怎么落到这个人身上" if ZH else "4. What the tags resolved to")
who = replace(PRESETS["a_type"], tags=["mbti_entp", "game_idv", "rel_close_friend"])
for line in describe(listener_tags(who), LANG):
    print("  " + line)
