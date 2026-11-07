# backend/apps/clients/tests/test_feedback_request_util.py
from django.test import TestCase
from backend.apps.clients.utils.feedback import feedback_request_generation_util as util

class GenerateFeedbackRequestKeyTest(TestCase):
    def test_prefix_and_length(self):
        print("→ generate_feedback_request_key: generates a key with prefix FRL and the correct length")
        key = util.generate_feedback_request_key(14)
        self.assertTrue(key.startswith("FRL"))
        self.assertEqual(len(key), 3 + 14)  # FRL prefix + 14 characters

    def test_randomness_uniqueness(self):
        print("→ generate_feedback_request_key: low chance of collision among many keys")
        keys = {util.generate_feedback_request_key(14) for _ in range(50)}
        self.assertEqual(len(keys), 50)  # all unique

    def test_different_lengths(self):
        print("→ generate_feedback_request_key: supports different lengths")
        k10 = util.generate_feedback_request_key(10)
        k20 = util.generate_feedback_request_key(20)
        self.assertEqual(len(k10), 3 + 10)
        self.assertEqual(len(k20), 3 + 20)


class FeedbackRequestLinkTest(TestCase):
    def test_link_structure(self):
        print("→ feedback_request_link: builds a URL with /feedback/ and a valid key")
        base = "https://example.com"
        link = util.feedback_request_link(base, key_length=12)
        self.assertTrue(link.startswith("https://example.com/feedback/FRL"))
        key = link.split("/")[-1]
        self.assertTrue(key.startswith("FRL"))
        self.assertEqual(len(key), 3 + 12)

    def test_base_url_with_trailing_slash(self):
        print("→ feedback_request_link: normalizes a trailing slash on base_url")
        base = "https://example.com/"
        link1 = util.feedback_request_link(base)
        link2 = util.feedback_request_link(base.rstrip("/"))
        self.assertTrue(link1.startswith("https://example.com/feedback/"))
        self.assertTrue(link2.startswith("https://example.com/feedback/"))

    def test_uniqueness_multiple_links(self):
        print("→ feedback_request_link: each call generates a unique link")
        base = "https://test.com"
        links = {util.feedback_request_link(base) for _ in range(30)}
        self.assertEqual(len(links), 30)
