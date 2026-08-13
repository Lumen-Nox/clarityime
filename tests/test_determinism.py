"""Same sentence + same person ⇒ byte-identical output. Always. No exceptions.

Same sentence + same audience object must produce identical output — comprehension is deterministic.

This file is the enforcement. It also checks the *reason* determinism holds:
there is no model call anywhere in the clarify path.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ast
import unittest
from dataclasses import replace

from clarityime.cerome.listener_presets import PRESETS
from clarityime.clarify.listener_adapt import adapt_with_report
from clarityime.clarify.local_rules import preserve_original

SAMPLES = [
    "嗯那个，就是我觉得这个方向其实还可以，就是风险也有点多，而且周期比较长",
    "我跟你说啊，其实我对这个方向还挺有感觉的，虽然数据不太够，但是我觉得值得试试",
    "因为接口它老是超时，所以那个功能我们可能得先关掉，不过风险还行",
    "老师我想问一下，这个作业能不能晚一天交，因为我这周有点忙",
]

CLARIFY_DIR = Path(__file__).resolve().parents[1] / "clarityime" / "clarify"

# Anything that could make output vary between two identical calls.
BANNED_CALLS = {"random", "shuffle", "choice", "uuid4", "time", "now", "sample"}
BANNED_MODULES = {"random", "openai", "anthropic", "requests", "httpx", "urllib"}


class DeterminismTests(unittest.TestCase):
    def test_repeated_calls_are_identical(self) -> None:
        for raw in SAMPLES:
            original, _ = preserve_original(raw)
            for key, profile in PRESETS.items():
                runs = [adapt_with_report(original, profile).text for _ in range(20)]
                self.assertEqual(len(set(runs)), 1, f"{key} drifted on {raw!r}")

    def test_same_tags_same_output(self) -> None:
        """The person is their tags. Two profiles with identical tags agree."""
        base = PRESETS["d_type"]
        twin = replace(base, l5=replace(base.l5, label="tired"))  # mood ≠ tags
        for raw in SAMPLES:
            original, _ = preserve_original(raw)
            self.assertEqual(
                adapt_with_report(original, base).text,
                adapt_with_report(original, twin).text,
                raw,
            )

    def test_different_tags_can_differ(self) -> None:
        """Sanity: the tag system actually does something."""
        original, _ = preserve_original(SAMPLES[2])
        outs = {k: adapt_with_report(original, p).text for k, p in PRESETS.items()}
        self.assertGreater(len(set(outs.values())), 1)

    def test_no_model_calls_and_no_randomness_in_clarify(self) -> None:
        """Determinism is structural, not lucky: nothing here can call out."""
        offenders: list[str] = []
        for path in sorted(CLARIFY_DIR.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        if a.name.split(".")[0] in BANNED_MODULES:
                            offenders.append(f"{path.name}: import {a.name}")
                elif isinstance(node, ast.ImportFrom):
                    root = (node.module or "").split(".")[0]
                    if root in BANNED_MODULES:
                        offenders.append(f"{path.name}: from {node.module}")
                elif isinstance(node, ast.Call):
                    fn = node.func
                    name = getattr(fn, "attr", None) or getattr(fn, "id", None)
                    if name in BANNED_CALLS:
                        offenders.append(f"{path.name}: {name}()")
        self.assertEqual(offenders, [], f"non-deterministic surface: {offenders}")


if __name__ == "__main__":
    unittest.main()
