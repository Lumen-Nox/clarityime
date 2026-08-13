"""Tag-driven adaptation: build people out of tags, watch the output change."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clarityime.cerome.listener_presets import PRESETS
from clarityime.cerome.tag_registry import FAMILIES, REGISTRY, catalog
from clarityime.cerome.tags import describe, listener_tags, parse_tags
from clarityime.clarify.listener_adapt import adapt_with_report
from clarityime.clarify.local_rules import preserve_original

LANG = sys.argv[1] if len(sys.argv) > 1 else "zh"

RAW = "嗯那个，就是这个接口老是超时，所以我们先把表格填好，然后发给老师，最后开黑的时候再说"

#: Same base personality, different declared facts about the person.
PEOPLE = {
    "只知道 MBTI": ["mbti_intj"],
    "MBTI + 打游戏": ["mbti_intj", "hobby_gaming"],
    "MBTI + 写代码 + 打游戏": ["mbti_intj", "hobby_coding", "hobby_gaming"],
    "不熟的人（全解释）": ["mbti_intj", "hobby_coding", "rel_stranger"],
    "尽责性高（步骤分行）": ["mbti_intj", "conscientious_high"],
    "小红书上学的（要具体）": ["mbti_infp", "src_social_media"],
}


def main() -> None:
    sep = "、" if LANG.startswith("zh") else ", "
    print(f"## 标签库：{len(REGISTRY)} 个，{len(FAMILIES)} 族  (lang={LANG})")
    for fam in FAMILIES:
        rows = catalog(LANG, fam)
        preview = sep.join(r["label"] for r in rows[:5])
        print(f"  {fam:11} {len(rows):>3}  {preview}{' …' if len(rows) > 5 else ''}")

    original, _ = preserve_original(RAW)
    print("\n" + "=" * 74)
    print(f"RAW      {RAW}")
    print(f"ORIGINAL {original}\n")

    for name, tags in PEOPLE.items():
        profile = replace(PRESETS["d_type"], tags=tags)
        res = adapt_with_report(original, profile)
        resolved = listener_tags(profile)
        print(f"--- {name}")
        for line in describe(parse_tags(tags), LANG):
            print(f"    {line}")
        print(f"    → 生效操作 {'+'.join(res.plan.tags())}")
        print(f"    → 已拥有词汇 {','.join(sorted(resolved.domains())) or '（无）'}")
        for line in res.text.split("\n"):
            print(f"      {line}")
        if res.substitutions:
            print("      swaps: " + " ".join(f"{s.src}→{s.dst}" for s in res.substitutions))
        print()


if __name__ == "__main__":
    main()
