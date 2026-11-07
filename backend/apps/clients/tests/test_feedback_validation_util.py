# backend/apps/clients/tests/test_feedback_text_util.py

from types import SimpleNamespace
from unittest.mock import patch
from django.test import SimpleTestCase

from backend.common.feedback_keywords import STOPWORDS_DE, STOPWORDS_EN
from backend.apps.clients.utils.feedback.feedback_validation_util import (
    stars_given,
    reached_comment_max_characters,
    feedback_preview,
    is_positive_feedback,
    extract_keywords_en,
    get_generic_keywords,
)


class StarsGivenTest(SimpleTestCase):
    def test_basic_labels_and_clamp(self):
        print("→ stars_given: maps labels and clamps to [1..max_stars]")
        self.assertEqual(stars_given(1), (1, "Bad"))
        self.assertEqual(stars_given(2), (2, "Poor"))
        self.assertEqual(stars_given(3), (3, "Average"))
        self.assertEqual(stars_given(4), (4, "Good"))
        self.assertEqual(stars_given(5), (5, "Excellent"))

        # below 1 → clamp to 1
        self.assertEqual(stars_given(0), (1, "Bad"))
        self.assertEqual(stars_given(-5), (1, "Bad"))

        # above max → clamp to max_stars (label mapped by the dictionary)
        self.assertEqual(stars_given(6), (5, "Excellent"))
        self.assertEqual(stars_given(999), (5, "Excellent"))

    def test_custom_max_stars(self):
        print("→ stars_given: supports a custom max_stars (labels outside 1..5 become 'Unknown')")
        # When max_stars != 5, the label dictionary is still 1..5,
        # so clamping to 7 with max=7 → the label should be 'Unknown'
        s, label = stars_given(7, max_stars=7)
        self.assertEqual(s, 7)
        self.assertEqual(label, "Unknown")


class ReachedCommentMaxCharactersTest(SimpleTestCase):
    def test_exceeds_equal_and_less(self):
        print("→ reached_comment_max_characters: True when it exceeds; False otherwise")
        self.assertFalse(reached_comment_max_characters("abcd", max_lenght=4))   # equal → False
        self.assertTrue(reached_comment_max_characters("abcde", max_lenght=4))  # exceeds → True
        self.assertFalse(reached_comment_max_characters("", max_lenght=4))      # empty → False


class FeedbackPreviewTest(SimpleTestCase):
    def test_preview_trim_and_ellipsis(self):
        print("→ feedback_preview: strips and appends '...' when it exceeds the limit")
        self.assertEqual(feedback_preview("  ok  ", length=5), "ok")  # strip
        self.assertEqual(feedback_preview("abc", length=5), "abc")    # <= limit
        self.assertEqual(feedback_preview("abcdef", length=5), "abcde...")  # > limit


class IsPositiveFeedbackTest(SimpleTestCase):
    def test_threshold(self):
        print("→ is_positive_feedback: >=4 True; <4 False")
        self.assertFalse(is_positive_feedback(1))
        self.assertFalse(is_positive_feedback(3))
        self.assertTrue(is_positive_feedback(4))
        self.assertTrue(is_positive_feedback(5))


class ExtractKeywordsEnTest(SimpleTestCase):
    @patch("backend.common.feedback_keywords.STOPWORDS_EN", {"the", "and", "a", "of", "is"})
    def test_extract_keywords_en_basic(self):
        print("→ extract_keywords_en: aggregates comments, removes stopwords, and counts top-N")

        # feedback_qs can be any iterable with a .comment attribute
        feedback_qs = [
            SimpleNamespace(comment="The product is great and the support is great"),
            SimpleNamespace(comment="Great experience overall, product quality is excellent"),
            SimpleNamespace(comment="Support and response time are great"),
        ]

        # Words expected after normalization/filtering: 'great', 'product', 'support',
        # 'experience', 'overall', 'quality', 'excellent', 'response', 'time'
        # 'the', 'and', 'is' should be removed (stopwords)
        top = extract_keywords_en(feedback_qs, top_n=5)
        # top should come ordered by frequency, e.g. [('great', 4), ('product', 2), ...]
        self.assertIsInstance(top, list)
        self.assertGreaterEqual(len(top), 1)
        # The first one should be 'great'
        self.assertEqual(top[0][0], "great")
        self.assertGreaterEqual(top[0][1], 3)

    @patch("backend.common.feedback_keywords.STOPWORDS_EN", set())
    def test_extract_keywords_en_filters_short_tokens(self):
        print("→ extract_keywords_en: ignores tokens with len <= 2")
        feedback_qs = [SimpleNamespace(comment="ok ok a an be is do go on")]
        top = extract_keywords_en(feedback_qs, top_n=10)
        # every token has <=2 letters → they should be filtered out → empty list
        self.assertEqual(top, [])

    @patch("backend.common.feedback_keywords.STOPWORDS_EN", {"the"})
    def test_extract_keywords_en_top_n_limit(self):
        print("→ extract_keywords_en: respects the top_n limit")
        feedback_qs = [
            SimpleNamespace(comment="alpha beta gamma delta epsilon zeta eta theta iota kappa the the"),
        ]
        top = extract_keywords_en(feedback_qs, top_n=3)
        self.assertEqual(len(top), 3)


class GetGenericKeywordsTest(SimpleTestCase):
    def test_get_generic_keywords_by_lang_real_lists(self):
        print("→ get_generic_keywords: returns the real lists by language (EN/DE) and default = EN")
        # import the real lists for comparison (avoids duplicating strings in the test)
        from backend.common.feedback_keywords import GENERIC_KEYWORDS_EN, GENERIC_KEYWORDS_DE

        # explicit en
        self.assertEqual(get_generic_keywords("en"), GENERIC_KEYWORDS_EN)
        # explicit de
        self.assertEqual(get_generic_keywords("de"), GENERIC_KEYWORDS_DE)
        # default (no lang) should be "en"
        self.assertEqual(get_generic_keywords(), GENERIC_KEYWORDS_EN)

        # useful sanity checks (not strict, but they help catch a coarse regression)
        self.assertIn("excellent service", GENERIC_KEYWORDS_EN)
        self.assertIn("schneller service", GENERIC_KEYWORDS_DE)
        self.assertGreater(len(GENERIC_KEYWORDS_EN), 10)
        self.assertGreater(len(GENERIC_KEYWORDS_DE), 10)
