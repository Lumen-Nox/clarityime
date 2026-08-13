"""Comprehension benchmark — how much easier did we actually make it?

Run:  python tests/run_benchmark.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clarityime.cerome.listener_presets import PRESET_META, PRESETS  # noqa: E402
from clarityime.clarify.comprehension import (  # noqa: E402
    comprehension_cost,
    count_jargon,
    split_clauses,
)
from clarityime.clarify.listener_adapt import adapt_with_report  # noqa: E402
from clarityime.clarify.local_rules import preserve_original  # noqa: E402

# Realistic spoken input: run-on, jargon, dropped subjects, nominalizations
CASES: list[tuple[str, str]] = [
    (
        "同学请假",
        "呃老师那个我作业可能得晚一天交因为家里有事然后我会尽量周末补上",
    ),
    (
        "技术同步",
        "你知道就是那个API接口它老是超时然后前端就白屏了我们可能得先做一个降级的处理",
    ),
    (
        "方案评估",
        "嗯我觉得吧这个方向其实还可以就是风险也有点多然后周期比较长但是团队士气还行",
    ),
    (
        "排期沟通",
        "我想说就是这个项目大概什么时候能做完因为要跟别的排期对齐而且ddl快到了",
    ),
    (
        "会议后续",
        "那个啥我跟你说啊这个bug它其实不是前端的问题是后端返回的数据格式不对我们需要进行一次复盘",
    ),
    (
        "推进受阻",
        "就是现在这个需求被产品改了三次然后我们的迭代节奏就乱了我觉得得先对齐一下颗粒度",
    ),
]


def _row(label: str, text: str, capacity: int) -> dict[str, float]:
    cost = comprehension_cost(text, capacity)
    return {
        "label": label,
        "cost": cost.total,
        "bridging": cost.bridging,
        "overload": cost.overload_units,
        "unsignaled": cost.unsignaled_causal,
        "jargon": count_jargon(text),
        "clauses": len(split_clauses(text)),
    }


def main() -> None:
    print("# Comprehension benchmark\n")
    totals: dict[str, list[float]] = {k: [] for k in PRESETS}
    jargon_totals: dict[str, list[int]] = {k: [] for k in PRESETS}

    for name, raw in CASES:
        original, _ = preserve_original(raw)
        print("=" * 70)
        print(f"[{name}]")
        print(f"  RAW : {raw}")
        print(f"  原文 : {original}")
        for key, profile in PRESETS.items():
            adapted, notes, before, after = adapt_with_report(original, profile)
            drop = round(before.total - after.total, 2)
            pct = round(100 * drop / before.total, 1) if before.total else 0.0
            totals[key].append(pct)
            jargon_totals[key].append(count_jargon(original) - count_jargon(adapted))
            print(f"\n  --- {key} ({PRESET_META.get(key)})  {before.total} → {after.total}  (-{pct}%)")
            for line in adapted.split("\n"):
                print(f"      {line}")
            subs = [n for n in notes if n.startswith(("T", "A"))]
            if subs:
                print(f"      · {' '.join(subs)}")
        print()

    print("=" * 70)
    print("## Summary — mean cost reduction & jargon removed\n")
    print(f"{'preset':<10}{'cost -%':>10}{'jargon-':>10}")
    for key in PRESETS:
        mean = round(sum(totals[key]) / len(totals[key]), 1)
        jg = sum(jargon_totals[key])
        print(f"{key:<10}{mean:>10}{jg:>10}")


if __name__ == "__main__":
    main()
