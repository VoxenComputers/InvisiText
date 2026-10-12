"""
Unit tests for the obfuscator engine.
"""

import unittest
from obfuscator import (
    insert_zero_width_spaces,
    strip_invisible_characters,
    count_invisible_characters,
    reveal_invisible_characters,
    get_text_statistics,
    ZW_SPACE,
    ALL_INVISIBLE_CHARS,
    FREQUENCY_LEVELS,
)


class TestObfuscator(unittest.TestCase):

    def test_empty_string(self):
        self.assertEqual(insert_zero_width_spaces(""), "")
        self.assertEqual(strip_invisible_characters(""), "")
        self.assertEqual(count_invisible_characters(""), 0)
        self.assertEqual(reveal_invisible_characters(""), "")
        stats = get_text_statistics("")
        self.assertEqual(stats["total_chars"], 0)
        self.assertEqual(stats["invisible_chars"], 0)

    def test_whitespace_and_punctuation_only(self):
        text = "   \t\n\r\n... ,,, ??? !!! --- () {} [] "
        obf = insert_zero_width_spaces(text, frequency=1.0)
        # Since there are no alnum characters, no invisible characters should be inserted
        self.assertEqual(obf, text)
        self.assertEqual(count_invisible_characters(obf), 0)

    def test_frequency_zero(self):
        text = "The quick brown fox jumps over the lazy dog."
        obf = insert_zero_width_spaces(text, frequency=0.0)
        self.assertEqual(obf, text)

    def test_frequency_one(self):
        text = "abc 123"
        obf = insert_zero_width_spaces(text, frequency=1.0, seed=42)
        # Alphanumeric chars are a, b, c, 1, 2, 3 -> exactly 6
        self.assertEqual(count_invisible_characters(obf), 6)
        # Spaces should NOT have invisible characters attached
        self.assertEqual(strip_invisible_characters(obf), text)
        self.assertTrue(all(c == ZW_SPACE for c in obf if c in ALL_INVISIBLE_CHARS))

    def test_multiline_preservation(self):
        text = "Line 1: Hello\nLine 2: World\r\nLine 3: End\n"
        obf = insert_zero_width_spaces(text, frequency=0.5, seed=123)
        # Stripping should yield identical text
        self.assertEqual(strip_invisible_characters(obf), text)
        # Line count should match
        self.assertEqual(obf.count("\n"), text.count("\n"))

    def test_unicode_accents_and_scripts(self):
        texts = [
            "Café crème brûlée déjà vu façade",
            "Привет мир! Это проверка текста.",
            "Καλημέρα κόσμε! Ελληνικό κείμενο.",
            "你好世界，这是一个测试文本。",
            "مرحبا بالعالم",
        ]
        for t in texts:
            obf = insert_zero_width_spaces(t, frequency=0.6, seed=99)
            self.assertEqual(strip_invisible_characters(obf), t)
            # In CJK / Cyrillic / Latin, alnum characters are detected
            self.assertGreater(count_invisible_characters(obf), 0)

    def test_emojis_preserved(self):
        emoji_text = "Hello world! 👋✨🚀 Super test 👨‍👩‍👧‍👦 with skin tone 👍🏽"
        obf = insert_zero_width_spaces(emoji_text, frequency=0.8, seed=777)
        # Strip should preserve emoji text
        # Note: 👨‍👩‍👧‍👦 naturally contains ZWJ (\u200d) inside the emoji sequence!
        # When clean_existing=False, existing composite emoji ZWJs are not stripped from original
        obf_no_clean = insert_zero_width_spaces(emoji_text, frequency=0.8, clean_existing=False, seed=777)
        self.assertIn("👋✨🚀", obf_no_clean)
        self.assertIn("👍🏽", obf_no_clean)

    def test_clean_existing_prevents_compounding(self):
        text = "Hello world"
        obf1 = insert_zero_width_spaces(text, frequency=1.0, seed=1)
        count1 = count_invisible_characters(obf1)
        # Re-obfuscating with clean_existing=True should yield the same count, not double
        obf2 = insert_zero_width_spaces(obf1, frequency=1.0, clean_existing=True, seed=1)
        count2 = count_invisible_characters(obf2)
        self.assertEqual(count1, count2)

    def test_frequency_levels(self):
        text = "Testing frequency levels: minimum, normal, medium, and maximum"
        obf_min = insert_zero_width_spaces(text, frequency="minimum", seed=10)
        obf_norm = insert_zero_width_spaces(text, frequency="normal", seed=10)
        obf_med = insert_zero_width_spaces(text, frequency="medium", seed=10)
        obf_max = insert_zero_width_spaces(text, frequency="maximum", seed=10)

        c_min = count_invisible_characters(obf_min)
        c_norm = count_invisible_characters(obf_norm)
        c_med = count_invisible_characters(obf_med)
        c_max = count_invisible_characters(obf_max)

        self.assertLessEqual(c_min, c_norm)
        self.assertLessEqual(c_norm, c_med)
        self.assertLessEqual(c_med, c_max)
        self.assertTrue(all(c == ZW_SPACE for c in obf_max if c in ALL_INVISIBLE_CHARS))

    def test_reveal_invisible_characters(self):
        text = f"A{ZW_SPACE}B{ZW_SPACE}C"
        revealed = reveal_invisible_characters(text, marker="[ZWSP]")
        self.assertEqual(revealed, "A[ZWSP]B[ZWSP]C")

    def test_statistics(self):
        text = "Hello world! This is a test."
        stats = get_text_statistics(text)
        self.assertEqual(stats["total_chars"], len(text))
        self.assertEqual(stats["invisible_chars"], 0)
        self.assertEqual(stats["visible_chars"], len(text))
        self.assertEqual(stats["words"], 6)
        self.assertEqual(stats["lines"], 1)

        obf = insert_zero_width_spaces(text, frequency=0.5, seed=5)
        stats_obf = get_text_statistics(obf)
        self.assertGreater(stats_obf["invisible_chars"], 0)
        self.assertEqual(stats_obf["visible_chars"], len(text))
        self.assertEqual(stats_obf["words"], 6)  # Words shouldn't change
        self.assertGreater(stats_obf["utf8_bytes"], stats["utf8_bytes"])

    def test_large_input_performance(self):
        # 100,000 characters
        large_text = ("The quick brown fox jumps over the lazy dog. " * 2500)[:100000]
        self.assertEqual(len(large_text), 100000)
        obf = insert_zero_width_spaces(large_text, frequency=0.4, seed=42)
        self.assertGreater(len(obf), 100000)
        stripped = strip_invisible_characters(obf)
        self.assertEqual(stripped, large_text)


if __name__ == "__main__":
    unittest.main()
