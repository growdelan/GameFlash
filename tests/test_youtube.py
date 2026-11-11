import unittest
from unittest.mock import patch
import main
from emails import gmail
from scrapers.youtube import extract_video_links


class YouTubeTests(unittest.TestCase):
    def test_embeds_links_dedup_and_article_scope(self):
        source = """<nav><a href="https://youtu.be/aaaaaaaaaaa">outside</a></nav><article>
        <iframe data-src="https://www.youtube-nocookie.com/embed/bbbbbbbbbbb?rel=0"></iframe>
        <a href="https://youtu.be/bbbbbbbbbbb?t=10">duplicate</a>
        <iframe src="//www.youtube.com/embed/ccccccccccc"></iframe>
        <a href="https://youtube.com.evil.test/watch?v=ddddddddddd">bad</a></article>"""
        self.assertEqual(
            [
                "https://www.youtube.com/watch?v=bbbbbbbbbbb",
                "https://www.youtube.com/watch?v=ccccccccccc",
            ],
            extract_video_links(source),
        )

    def test_no_video(self):
        self.assertEqual([], extract_video_links("<article>News.</article>"))

    def test_saved_summary_is_complete_and_renders_clickable_video(self):
        video = "https://www.youtube.com/watch?v=bbbbbbbbbbb"
        with (
            patch("main.jina.fetch_article_text", return_value="article"),
            patch(
                "main.openai_summary.run_openai_model",
                return_value="Tytuł: News\n\nPodsumowanie: Gotowe.",
            ),
            patch("main.youtube.fetch_video_links", return_value=[video]),
        ):
            summary = main.summarize_link(
                {"OPENAI_API_KEY": "test", "OPENAI_MODEL": "test"},
                "https://example.com",
            )
        self.assertTrue(main.is_complete_summary_result(summary))
        entry = summary + "\n\nLink: https://example.com"
        self.assertIn("Wideo: " + video, gmail.build_plain_text_body([entry]))
        self.assertIn('href="' + video + '"', gmail.build_email_html([entry]))
        self.assertEqual("Gotowe.", gmail._parse_news_entry(entry)["summary"])
