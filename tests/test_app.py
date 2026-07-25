import unittest

from core import available_resolutions, format_selector, validate_youtube_url


class UrlValidationTests(unittest.TestCase):
    def test_accepts_and_cleans_youtube_urls(self):
        self.assertEqual(
            validate_youtube_url("https://www.youtube.com/watch?v=abc123&list=PL1&index=2"),
            "https://www.youtube.com/watch?v=abc123",
        )
        self.assertEqual(
            validate_youtube_url("https://youtu.be/abc123"),
            "https://youtu.be/abc123",
        )

    def test_rejects_non_youtube_urls(self):
        with self.assertRaises(ValueError):
            validate_youtube_url("https://example.com/video")
        with self.assertRaises(ValueError):
            validate_youtube_url("file:///etc/passwd")


class FormatTests(unittest.TestCase):
    def test_selector_matches_desktop_program(self):
        selector = format_selector("720")
        self.assertIn("height<=720", selector)
        self.assertIn("bestvideo", selector)
        self.assertEqual(
            format_selector("best"),
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        )

    def test_resolutions_are_unique_and_descending(self):
        info = {
            "formats": [
                {"height": 720, "vcodec": "avc1", "tbr": 1000, "fps": 30},
                {"height": 720, "vcodec": "vp9", "tbr": 1500, "fps": 60},
                {"height": 1080, "vcodec": "vp9", "tbr": 1800, "fps": 30},
                {"height": None, "vcodec": "none", "tbr": 128},
            ]
        }
        result = available_resolutions(info)
        self.assertEqual([item["height"] for item in result], [1080, 720])
        self.assertEqual(result[1]["fps"], 60)


if __name__ == "__main__":
    unittest.main()
