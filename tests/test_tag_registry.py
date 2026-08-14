"""Tag registry — vocabulary integrity + the no-cross-family-inference guarantee."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import unittest
from dataclasses import replace

from clarityime.cerome.listener_presets import PRESETS
from clarityime.cerome.tag_registry import (
    FAMILIES,
    MBTI_FUNCTIONS,
    REGISTRY,
    catalog,
    expand,
    label,
    quick_setup,
    search,
)
from clarityime.cerome.tags import (
    ALL_TAGS,
    DOMAIN_TAGS,
    PERSONALITY_TAGS,
    PROCESSING_TAGS,
    UnknownTagError,
    describe,
    listener_tags,
    parse_tags,
    validate,
)
from clarityime.clarify.listener_adapt import adapt_with_report
from clarityime.clarify.local_rules import preserve_original


class RegistryIntegrityTests(unittest.TestCase):
    def test_registry_is_big_enough_to_describe_a_person(self) -> None:
        self.assertGreaterEqual(len(REGISTRY), 100)
        for fam in FAMILIES:
            got = [d for d in REGISTRY.values() if d.family == fam]
            self.assertTrue(got, f"family {fam} is empty")

    def test_every_tag_is_bilingual(self) -> None:
        for tid, d in REGISTRY.items():
            self.assertTrue(d.zh.strip(), tid)
            self.assertTrue(d.en.strip(), tid)
            if d.zh == d.en:
                # Proper nouns with no Chinese name (Dota 2, Among Us) are fine;
                # anything containing CJK must differ.
                self.assertFalse(
                    any("\u4e00" <= c <= "\u9fff" for c in d.zh),
                    f"{tid} has no real translation",
                )

    def test_zh_and_en_are_not_swapped(self) -> None:
        """Catches the positional-argument slip that swapped the lang tags."""
        cjk = lambda s: any("\u4e00" <= c <= "\u9fff" for c in s)
        for tid, d in REGISTRY.items():
            self.assertFalse(
                cjk(d.en) and not cjk(d.zh), f"{tid}: zh/en look swapped ({d.zh!r}/{d.en!r})"
            )
            self.assertFalse(cjk(d.en), f"{tid}: English label contains Chinese: {d.en!r}")

    def test_every_family_is_declared(self) -> None:
        for tid, d in REGISTRY.items():
            self.assertIn(d.family, FAMILIES, tid)

    def test_implications_point_only_at_processing(self) -> None:
        for tid, d in REGISTRY.items():
            for imp in d.implies:
                self.assertIn(imp, PROCESSING_TAGS, f"{tid} implies non-processing {imp}")

    def test_only_doing_families_grant_vocabulary(self) -> None:
        """You own words because of what you DO, not because of who you are."""
        allowed = {"domain", "hobby", "source", "edu", "topic"}
        for tid, d in REGISTRY.items():
            if d.grants:
                self.assertIn(d.family, allowed, f"{tid} ({d.family}) grants vocabulary")

    def test_grants_reference_real_domains(self) -> None:
        for tid, d in REGISTRY.items():
            for g in d.grants:
                self.assertIn(g, DOMAIN_TAGS, f"{tid} grants unknown domain {g}")

    def test_all_sixteen_mbti_types_present(self) -> None:
        self.assertEqual(len(MBTI_FUNCTIONS), 16)
        for mb in MBTI_FUNCTIONS:
            self.assertIn(f"mbti_{mb.lower()}", REGISTRY)


class NoCrossFamilyInferenceTests(unittest.TestCase):
    def test_no_personality_tag_grants_vocabulary(self) -> None:
        """The exact bug: INTJ ⇏ 懂技术. Checked across all 16 + Big Five + 九型."""
        for tid in PERSONALITY_TAGS:
            _processing, domains = expand({tid})
            self.assertEqual(domains, set(), f"{tid} invented domain knowledge {domains}")

    def test_every_mbti_type_yields_zero_domains(self) -> None:
        for mb in MBTI_FUNCTIONS:
            tags = parse_tags([mb])  # bare 'INTJ' also accepted
            self.assertEqual(tags.domains(), frozenset(), mb)

    def test_hobby_does_grant_vocabulary(self) -> None:
        self.assertIn("tech", parse_tags(["hobby_coding"]).domains())
        self.assertIn("music", parse_tags(["hobby_music_play"]).domains())
        self.assertIn("food", parse_tags(["hobby_cooking"]).domains())
        self.assertIn("internet", parse_tags(["topic_memes"]).domains())

    def test_presets_carry_personality_only(self) -> None:
        for key, profile in PRESETS.items():
            self.assertEqual(listener_tags(profile).domains(), frozenset(), key)

    def test_unknown_tag_rejected_with_suggestion(self) -> None:
        with self.assertRaises(UnknownTagError) as ctx:
            validate(["mbti_intz"])
        self.assertIn("mbti_int", str(ctx.exception))


class BehaviourTests(unittest.TestCase):
    def test_hobby_changes_which_terms_get_translated(self) -> None:
        original, _ = preserve_original("这个接口老是超时，我们开黑的时候也卡")
        plain = adapt_with_report(original, replace(PRESETS["d_type"], tags=["mbti_intj"]))
        gamer = adapt_with_report(
            original, replace(PRESETS["d_type"], tags=["mbti_intj", "hobby_gaming"])
        )
        self.assertIn("组队", plain.text)  # 开黑 translated
        self.assertIn("开黑", gamer.text)  # gamer keeps it

    def test_internet_slang_translates_unless_the_listener_follows_memes(self) -> None:
        original, _ = preserve_original("听到这个我破防了")
        outsider = adapt_with_report(original, replace(PRESETS["s_type"], tags=["mbti_infp"]))
        insider = adapt_with_report(
            original, replace(PRESETS["s_type"], tags=["mbti_infp", "topic_memes"])
        )
        self.assertIn("情绪被戳到", outsider.text)
        self.assertIn("破防", insider.text)

    def test_define_terms_overrides_ownership(self) -> None:
        """不熟的人：全部解释，哪怕他懂。"""
        original, _ = preserve_original("这个接口老是超时")
        insider = replace(PRESETS["d_type"], tags=["mbti_intj", "tech"])
        stranger = replace(PRESETS["d_type"], tags=["mbti_intj", "tech", "rel_stranger"])
        self.assertIn("超时", adapt_with_report(original, insider).text)
        self.assertIn("响应太慢", adapt_with_report(original, stranger).text)

    def test_sequence_tag_puts_each_step_on_its_own_line(self) -> None:
        original, _ = preserve_original("先把表格填好，然后发给老师，最后在群里说一声")
        base = replace(PRESETS["s_type"], tags=["mbti_infp"])
        stepwise = replace(PRESETS["s_type"], tags=["mbti_infp", "conscientious_high"])
        self.assertGreater(
            adapt_with_report(original, stepwise).text.count("\n"),
            adapt_with_report(original, base).text.count("\n"),
        )

    def test_conflicting_load_tags_fall_back_to_default(self) -> None:
        from clarityime.clarify.listener_adapt import plan_from_cerome

        both = replace(PRESETS["d_type"], tags=["extravert_high", "extravert_low"])
        self.assertEqual(plan_from_cerome(both).capacity, 26)


class GameGranularityTests(unittest.TestCase):
    """「打游戏」不够 —— 不同游戏的黑话互相听不懂。"""

    LINE = "监管者一直守椅，我们保底都没抽出来，只能开黑再上分"

    def _say(self, *tags: str) -> str:
        original, _ = preserve_original(self.LINE)
        who = replace(PRESETS["a_type"], tags=["mbti_entp", *tags])
        return adapt_with_report(original, who).text

    def test_fps_player_hears_idv_as_an_analogy_not_a_lecture(self) -> None:
        out = self._say("game_valorant")
        self.assertIn("守椅", out)
        self.assertIn("架点", out)
        self.assertIn("就像", out)
        self.assertNotIn("保底", out)

    def test_idv_player_does_not_get_an_analogy_for_their_own_slang(self) -> None:
        out = self._say("game_idv")
        self.assertIn("守椅", out)
        self.assertNotIn("就像", out)

    def test_gacha_player_is_the_mirror_image(self) -> None:
        out = self._say("game_genshin")
        self.assertIn("保底", out)
        self.assertNotIn("守椅", out)

    def test_coarse_gaming_tag_only_grants_the_shared_words(self) -> None:
        out = self._say("hobby_gaming")
        self.assertIn("开黑", out)          # 通用游戏词
        self.assertNotIn("守椅", out)
        self.assertNotIn("保底", out)

    def test_picking_a_game_rolls_up_to_gaming(self) -> None:
        _, domains = expand({"game_idv"})
        self.assertIn("asym_horror", domains)
        self.assertIn("gaming", domains)     # parent roll-up

    def test_a_game_never_grants_a_non_game_domain(self) -> None:
        allowed = {
            "gaming", "moba", "fps", "gacha", "asym_horror", "sandbox",
            "sim_game", "strategy_game", "party_game", "rhythm_game",
            "souls", "narrative_game",
        }
        for tid, d in REGISTRY.items():
            if tid.startswith("game_"):
                _, granted = expand({tid})
                self.assertTrue(granted <= allowed, f"{tid} granted {granted - allowed}")

    def test_no_ambiguous_word_is_ever_substituted(self) -> None:
        """「毕业」在抽卡圈=练满、在校园=真毕业。这种词一旦收进表就会改错意思。"""
        from clarityime.clarify.paraphrase import AMBIGUOUS_BLOCKLIST, JARGON_TABLE

        clash = AMBIGUOUS_BLOCKLIST & set(JARGON_TABLE)
        self.assertEqual(clash, set(), f"ambiguous terms in the table: {clash}")

    def test_every_granted_game_domain_actually_has_words(self) -> None:
        from clarityime.clarify.paraphrase import jargon_domains

        have = jargon_domains()
        for tid in (t for t in REGISTRY if t.startswith("game_")):
            _, granted = expand({tid})
            self.assertTrue(
                granted & have, f"{tid} grants domains with no vocabulary: {granted}"
            )


class MultiLanguageJargonTests(unittest.TestCase):
    """reads_<lang> picks which curated table gets scanned — never mixed."""

    def test_english_reader_gets_english_table_not_chinese(self) -> None:
        original, _ = preserve_original("that gank was a total throw, gg")
        en_reader = replace(PRESETS["a_type"], tags=["mbti_entp", "reads_en"])
        out = adapt_with_report(original, en_reader).text
        self.assertIn("ambush", out.lower())
        self.assertIn("good game", out.lower())

    def test_default_reader_still_gets_chinese_table(self) -> None:
        from clarityime.clarify.listener_adapt import plan_from_cerome

        zh_reader = replace(PRESETS["a_type"], tags=["mbti_entp"])
        self.assertEqual(plan_from_cerome(zh_reader).reading_lang, "zh")

    def test_declaring_a_reading_language_never_grants_a_domain(self) -> None:
        _, domains = expand({"reads_ja", "reads_ko", "reads_fr"})
        self.assertEqual(domains, set())

    def test_eight_new_reading_languages_are_registered(self) -> None:
        for code in ("ja", "ko", "fr", "de", "es", "ar", "pt", "yue"):
            self.assertIn(f"reads_{code}", REGISTRY, f"missing reads_{code}")

    def test_more_reading_languages_are_searchable(self) -> None:
        for code in ("zh_hant", "ru", "it", "vi", "th", "id", "hi", "nl", "tr", "uk"):
            self.assertIn(f"reads_{code}", REGISTRY, f"missing reads_{code}")


class EaseOfUseTests(unittest.TestCase):
    """标签再多，设置也得三步点完。"""

    def test_default_picker_list_stays_short(self) -> None:
        for step in quick_setup("zh"):
            self.assertLessEqual(
                len(step["options"]), 20, f"{step['family']} 默认列表太长了"
            )

    def test_setup_is_five_questions_and_all_optional(self) -> None:
        steps = quick_setup("zh")
        self.assertEqual(len(steps), 5)
        self.assertTrue(all(step["options"] for step in steps))
        # 一个标签都不选也能跑
        blank = replace(PRESETS["d_type"], tags=[])
        original, _ = preserve_original("这个作业能不能晚一天交")
        self.assertTrue(adapt_with_report(original, blank).text)

    def test_search_finds_games_by_nickname(self) -> None:
        for query, want in (
            ("王者", "game_hok"),
            ("农药", "game_hok"),
            ("idv", "game_idv"),
            ("第五", "game_idv"),
            ("genshin", "game_genshin"),
            ("吃鸡", "game_pubg"),
            ("mc", "game_minecraft"),
            ("lol", "game_lol"),
            ("鬼灭", "anime_demon_slayer"),
            ("三体", "novel_threebody"),
            ("韩剧", "tv_kdrama"),
            ("汪苏泷", "music_c_pop"),
            ("igcse", "edu_igcse"),
            ("美国", "place_us"),
            ("越南语", "reads_vi"),
        ):
            ids = [r["id"] for r in search(query)]
            self.assertIn(want, ids, f"搜「{query}」没搜到 {want}")

    def test_empty_search_returns_the_common_starter_set(self) -> None:
        rows = search("")
        self.assertTrue(rows)
        self.assertTrue(all(REGISTRY[r["id"]].common for r in rows))

    def test_full_list_is_reachable_behind_the_short_one(self) -> None:
        short = quick_setup("zh")[2]["options"]
        full = quick_setup("zh", full=True)[2]["options"]
        self.assertGreater(len(full), len(short))

    def test_setup_questions_are_localised(self) -> None:
        self.assertIn("MBTI", quick_setup("en")[0]["question"])
        for step in quick_setup("en", full=True):
            for opt in step["options"]:
                self.assertFalse(
                    any("\u4e00" <= ch <= "\u9fff" for ch in opt["label"]),
                    f"CJK leaked into the English label of {opt['id']}",
                )


class MediaAndLifeTagTests(unittest.TestCase):
    """游戏以外：番/小说/剧/歌/课程/学历/国家/年龄/性别。"""

    def test_anime_title_rolls_up_like_a_game(self) -> None:
        _, domains = expand({"anime_conan"})
        self.assertIn("anime", domains)
        self.assertIn("fandom", domains)  # parent hobby_anime

    def test_webnovel_tag_owns_webnovel_words_not_academic_only(self) -> None:
        _, domains = expand({"novel_web"})
        self.assertIn("webnovel", domains)
        self.assertIn("academic", domains)  # parent hobby_reading

    def test_course_and_topic_grant_the_matching_circle(self) -> None:
        self.assertIn("tech", parse_tags(["course_cs"]).domains())
        self.assertIn("psych_pop", parse_tags(["topic_psych"]).domains())
        self.assertIn("school", parse_tags(["edu_igcse"]).domains())

    def test_age_gender_country_never_grant_vocabulary(self) -> None:
        for tid in (
            "age_child", "age_teen", "age_adult",
            "gender_female", "gender_male", "gender_nb",
            "place_cn", "place_jp", "place_us", "place_kr",
        ):
            _, domains = expand({tid})
            self.assertEqual(domains, set(), f"{tid} invented {domains}")

    def test_japan_does_not_imply_reading_japanese(self) -> None:
        processing, domains = expand({"place_jp"})
        self.assertEqual(domains, set())
        self.assertNotIn("reads_ja", processing)
        self.assertEqual(expand({"place_jp"})[0], set())

    def test_young_child_gets_short_concrete_defined_terms(self) -> None:
        processing, _ = expand({"age_child"})
        self.assertTrue({"short_chunks", "define_terms", "concrete_first"} <= processing)

    def test_teen_is_not_treated_as_a_child(self) -> None:
        processing, domains = expand({"age_teen"})
        self.assertEqual(domains, set())
        self.assertNotIn("define_terms", processing)

    def test_media_domains_actually_have_words(self) -> None:
        from clarityime.clarify.paraphrase import jargon_domains

        have = jargon_domains("zh")
        for domain in ("anime", "webnovel", "film_tv", "idol", "fandom"):
            self.assertIn(domain, have, f"{domain} has no Chinese jargon rows")

    def test_webnovel_reader_hears_isekai_as_an_analogy(self) -> None:
        original, _ = preserve_original("这本是异世界金手指爽文")
        gamer = replace(PRESETS["a_type"], tags=["mbti_entp", "hobby_gaming"])
        out = adapt_with_report(original, gamer).text
        self.assertIn("金手指（就像开挂）", out)

    def test_yue_and_traditional_chinese_use_the_chinese_table(self) -> None:
        from clarityime.clarify.paraphrase import canonical_jargon_lang, simplify_jargon

        self.assertEqual(canonical_jargon_lang("yue"), "zh")
        self.assertEqual(canonical_jargon_lang("zh_hant"), "zh")
        text, _ = simplify_jargon("明天 ddl", known_domains=set(), lang="yue")
        self.assertIn("截止时间", text)


class LocalisationTests(unittest.TestCase):
    def test_labels_switch_language(self) -> None:
        self.assertEqual(label("mbti_intj", "zh"), "INTJ·建筑师")
        self.assertEqual(label("mbti_intj", "en"), "INTJ · Architect")
        self.assertEqual(label("hobby_riding", "en"), "horse riding")

    def test_catalog_covers_registry_and_sorts_by_family(self) -> None:
        rows = catalog("en")
        self.assertEqual(len(rows), len(REGISTRY))
        fams = [r["family"] for r in rows]
        self.assertEqual(fams, sorted(fams, key=FAMILIES.index))

    def test_describe_groups_by_family_in_both_languages(self) -> None:
        tags = parse_tags(["mbti_intj", "hobby_coding", "rel_teacher"])
        zh = "\n".join(describe(tags, "zh"))
        en = "\n".join(describe(tags, "en"))
        self.assertIn("建筑师", zh)
        self.assertIn("Architect", en)
        self.assertIn("hobby", zh)

    def test_unknown_tag_label_falls_back_to_id(self) -> None:
        self.assertEqual(label("not_a_tag", "en"), "not_a_tag")


if __name__ == "__main__":
    unittest.main()
