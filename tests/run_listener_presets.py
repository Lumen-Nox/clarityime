"""Human-readable check: same propositions, lower comprehension cost per listener.

Run:  python tests/run_listener_presets.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clarityime.cerome.listener_presets import PRESET_META, PRESETS  # noqa: E402
from clarityime.clarify.comprehension import check_invariants  # noqa: E402
from clarityime.clarify.listener_adapt import adapt_with_report, plan_from_cerome  # noqa: E402
from clarityime.clarify.local_rules import preserve_original  # noqa: E402

SAMPLES = [
    "就是我觉得这个方案还行，胜算挺高的，而且周期也长",
    "那个，就是我明天可能去不了，因为家里有事，然后作业我可能得晚一天交",
    "因为API接口它老是超时，所以那个功能我们可能得先关掉，不过风险还行",
    "嗯我想说就是这个项目大概什么时候能做完，因为要跟别的排期对齐",
    "我跟你说啊，其实我对这个方向还挺有感觉的，虽然数据不太够，但是我觉得值得试试",
]


def main() -> None:
    print("# Listener presets — comprehension cost (lower = easier)\n")
    for key, profile in PRESETS.items():
        plan = plan_from_cerome(profile)
        print(f"- **{key}** ({PRESET_META.get(key)}): {profile.l3.comprehension_gaps}")
        print(f"  ops = {'+'.join(plan.tags())}")
    print()

    for raw in SAMPLES:
        original, _ = preserve_original(raw)
        print("=" * 66)
        print(f"RAW  : {raw}")
        print(f"原文  : {original}")
        for key, profile in PRESETS.items():
            adapted, notes, before, after = adapt_with_report(original, profile)
            report = check_invariants(original, adapted)
            flag = "OK " if report.ok else "!! "
            delta = round(after.total - before.total, 2)
            print(f"\n--- {flag}{key} ({PRESET_META.get(key)})  cost {before.total} → {after.total} ({delta:+}) ---")
            for line in adapted.split("\n"):
                print(f"    {line}")
            ops = [n for n in notes if n.startswith(("A1", "A2", "A3", "A4", "A5", "A6", "A7"))]
            if ops:
                print(f"    · {' '.join(ops)}")
            if not report.ok:
                print(f"    !! new={report.new_content} lost={report.lost_content}")
        print()


if __name__ == "__main__":
    main()
