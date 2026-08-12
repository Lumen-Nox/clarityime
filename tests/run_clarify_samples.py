"""Ad-hoc sample runner — `python tests/run_clarify_samples.py`"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clarityime.clarify.candidates import clarify_candidates
from clarityime.clarify.local_rules import clarify_default, clarify_for_structured, clarify_for_contact
from clarityime.models import AudienceMode, ContactProfile

SAMPLES: list[tuple[str, list[str] | None]] = [
    (
        "嗯那个你好，就是我想问一下这个项目大概什么时候能做完啊",
        [
            "嗯那个你好，就是我想问一下这个项目大概什么时候能做完啊",
            "我想问一下这个项目大概什么时候能做完",
        ],
    ),
    ("对对对然后那个就是我明天可能去不了因为我要去看医生", None),
    ("你知道就是那个API接口它老是超时然后前端就白屏了", None),
    ("呃老师那个我作业可能得晚一天交因为家里有事", None),
    ("就是我觉得这个方案不太行因为成本太高了而且周期也长", None),
    ("就是我觉得这个方案还行，胜算挺高的，而且周期也长", None),
    (
        "嗯我觉得吧这个方向其实还可以就是风险也有点多然后周期比较长但是团队士气还行你要是有空我们可以再聊细一点",
        None,
    ),
    ("Can you like send me the file before tomorrow", None),
    ("嗯我想就是说能不能把deadline延长一下", None),
    (
        "那个啥，我跟你说啊，这个bug它其实不是前端的问题，是后端返回的数据格式不对",
        None,
    ),
]

TEACHER = ContactProfile(
    id=1,
    name="张老师",
    relationship="老师",
    style_notes="温和 正式",
    extra={"cerome": {"L2": {"warmth": 0.75, "clarity": 0.7, "efficiency": 0.5, "precision": 0.6, "humor": 0.3}}},
)

FRIEND = ContactProfile(
    id=2,
    name="小李",
    relationship="朋友",
    style_notes="口语",
)


def main() -> None:
    lines: list[str] = []
    for text, nbest in SAMPLES:
        lines.append("=" * 60)
        lines.append(f"RAW: {text}")
        d, _ = clarify_default(text, nbest or [text])
        s, _ = clarify_for_structured(text, nbest or [text])
        t, _ = clarify_for_contact(text, TEACHER.to_clarify_hints(), nbest or [text])
        f, _ = clarify_for_contact(text, FRIEND.to_clarify_hints(), nbest or [text])
        lines.append(f"DEFAULT:    {d}")
        lines.append(f"STRUCTURED: {s.replace(chr(10), ' | ')}")
        lines.append(f"CONTACT(老师): {t}")
        lines.append(f"CONTACT(朋友): {f}")
        for mode in (AudienceMode.DEFAULT, AudienceMode.STRUCTURED):
            cands = clarify_candidates(text, mode=mode, nbest=nbest or [text])
            lines.append(f"  [{mode.value}]")
            for item in cands:
                tline = item["text"].replace("\n", " | ")
                lines.append(f"    {item['label']:16} {tline}")
        lines.append("")

    out = Path(__file__).with_name("_clarify_samples_out.txt")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
