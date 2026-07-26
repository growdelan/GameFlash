import unittest

import main
from tests.fakes import FakeWorksheet
from storage import google_sheets


HEADERS = ["Links", *google_sheets.STATE_HEADERS]
COMPLETE_SUMMARY = "Tytul: Test\n\nPodsumowanie: To jest kompletne podsumowanie."


def state_row(
    link,
    status,
    attempts=0,
    summary="",
    last_error="",
    discovered_at="2026-07-26T10:00:00+00:00",
    updated_at="2026-07-26T10:00:00+00:00",
):
    return [
        link,
        status,
        str(attempts),
        summary,
        last_error,
        discovered_at,
        updated_at,
    ]


class MilestoneOneNineTests(unittest.TestCase):
    def setUp(self):
        self.original_fetch_article = main.jina.fetch_article_text
        self.original_run_model = main.gemini.run_gemini_model
        self.original_send_email = main.gmail.send_email
        self.config = {
            "GEMINI_API_KEY": "test",
            "GEMINI_MODEL": "model",
            "SMTP_SERVER": "smtp.example.com",
            "SENDER_MAIL": "sender@example.com",
            "SENDER_PASS": "pass",
            "RECIPIENTS": ["receiver@example.com"],
        }

    def tearDown(self):
        main.jina.fetch_article_text = self.original_fetch_article
        main.gemini.run_gemini_model = self.original_run_model
        main.gmail.send_email = self.original_send_email

    def test_third_processing_failure_marks_record_as_failed(self):
        link = "https://www.ppe.pl/news/1/retry.html"
        ws = FakeWorksheet(values=[HEADERS, state_row(link, "pending")])
        main.jina.fetch_article_text = lambda url: (_ for _ in ()).throw(
            RuntimeError("fetch failed")
        )

        for expected_status, expected_attempts in (
            ("pending", "1"),
            ("pending", "2"),
            ("failed", "3"),
        ):
            main.process_pending_news(
                self.config,
                ws,
                google_sheets.read_news_records(ws),
            )
            record = ws.record(link)
            self.assertEqual(expected_status, record["status"])
            self.assertEqual(expected_attempts, record["attempts"])

    def test_successful_retry_persists_summary_and_resets_attempts(self):
        link = "https://www.ppe.pl/news/2/success.html"
        ws = FakeWorksheet(values=[HEADERS, state_row(link, "pending", attempts=2)])
        main.jina.fetch_article_text = lambda url: "article-body"
        main.gemini.run_gemini_model = lambda **kwargs: COMPLETE_SUMMARY

        main.process_pending_news(
            self.config,
            ws,
            google_sheets.read_news_records(ws),
        )

        record = ws.record(link)
        self.assertEqual("ready", record["status"])
        self.assertEqual("0", record["attempts"])
        self.assertEqual(COMPLETE_SUMMARY, record["summary"])
        self.assertEqual("", record["lasterror"])

    def test_smtp_failure_reuses_persisted_summary_on_next_run(self):
        link = "https://www.ppe.pl/news/3/delivery.html"
        ws = FakeWorksheet(
            values=[HEADERS, state_row(link, "ready", summary=COMPLETE_SUMMARY)]
        )
        send_calls = []

        def failing_send(**kwargs):
            send_calls.append(kwargs)
            raise RuntimeError("smtp failed")

        main.gmail.send_email = failing_send
        with self.assertRaisesRegex(RuntimeError, "smtp failed"):
            main.send_ready_news(
                self.config,
                ws,
                google_sheets.read_news_records(ws),
            )

        failed_delivery = ws.record(link)
        self.assertEqual("ready", failed_delivery["status"])
        self.assertEqual("1", failed_delivery["attempts"])
        self.assertEqual(COMPLETE_SUMMARY, failed_delivery["summary"])

        main.jina.fetch_article_text = lambda url: (_ for _ in ()).throw(
            AssertionError("Jina nie powinna byc ponownie wywolywana")
        )
        main.gemini.run_gemini_model = lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("Gemini nie powinno byc ponownie wywolywane")
        )
        main.process_pending_news(
            self.config,
            ws,
            google_sheets.read_news_records(ws),
        )
        main.gmail.send_email = lambda **kwargs: send_calls.append(kwargs)
        main.send_ready_news(
            self.config,
            ws,
            google_sheets.read_news_records(ws),
        )

        self.assertEqual("sent", ws.record(link)["status"])
        self.assertEqual(2, len(send_calls))

    def test_third_smtp_failure_marks_record_as_failed(self):
        link = "https://www.ppe.pl/news/7/delivery-failed.html"
        ws = FakeWorksheet(
            values=[
                HEADERS,
                state_row(link, "ready", attempts=2, summary=COMPLETE_SUMMARY),
            ]
        )
        main.gmail.send_email = lambda **kwargs: (_ for _ in ()).throw(
            RuntimeError("smtp failed")
        )

        with self.assertRaisesRegex(RuntimeError, "smtp failed"):
            main.send_ready_news(
                self.config,
                ws,
                google_sheets.read_news_records(ws),
            )

        record = ws.record(link)
        self.assertEqual("failed", record["status"])
        self.assertEqual("3", record["attempts"])
        self.assertEqual(COMPLETE_SUMMARY, record["summary"])

    def test_ready_without_complete_summary_is_not_sent(self):
        link = "https://www.ppe.pl/news/8/empty-summary.html"
        ws = FakeWorksheet(values=[HEADERS, state_row(link, "ready")])
        send_calls = []
        main.gmail.send_email = lambda **kwargs: send_calls.append(kwargs)

        main.send_ready_news(
            self.config,
            ws,
            google_sheets.read_news_records(ws),
        )

        record = ws.record(link)
        self.assertEqual([], send_calls)
        self.assertEqual("ready", record["status"])
        self.assertEqual("1", record["attempts"])
        self.assertIn("kompletnego podsumowania", record["lasterror"])

    def test_manual_pending_reactivation_resets_exhausted_counter(self):
        link = "https://www.ppe.pl/news/4/manual-processing.html"
        ws = FakeWorksheet(values=[HEADERS, state_row(link, "pending", attempts=3)])
        main.jina.fetch_article_text = lambda url: "article-body"
        main.gemini.run_gemini_model = lambda **kwargs: COMPLETE_SUMMARY

        main.process_pending_news(
            self.config,
            ws,
            google_sheets.read_news_records(ws),
        )

        record = ws.record(link)
        self.assertEqual("ready", record["status"])
        self.assertEqual("0", record["attempts"])

    def test_manual_ready_reactivation_resets_exhausted_counter(self):
        link = "https://www.ppe.pl/news/5/manual-delivery.html"
        ws = FakeWorksheet(
            values=[
                HEADERS,
                state_row(link, "ready", attempts=3, summary=COMPLETE_SUMMARY),
            ]
        )
        main.gmail.send_email = lambda **kwargs: None

        main.send_ready_news(
            self.config,
            ws,
            google_sheets.read_news_records(ws),
        )

        record = ws.record(link)
        self.assertEqual("sent", record["status"])
        self.assertEqual("0", record["attempts"])

    def test_unknown_status_is_skipped(self):
        link = "https://www.ppe.pl/news/6/unknown.html"
        ws = FakeWorksheet(values=[HEADERS, state_row(link, "paused")])
        main.jina.fetch_article_text = lambda url: (_ for _ in ()).throw(
            AssertionError("Nieznany status nie moze byc przetwarzany")
        )
        main.gmail.send_email = lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("Nieznany status nie moze byc wysylany")
        )

        records = google_sheets.read_news_records(ws)
        main.process_pending_news(self.config, ws, records)
        main.send_ready_news(self.config, ws, records)

        self.assertEqual("paused", ws.record(link)["status"])


if __name__ == "__main__":
    unittest.main()
