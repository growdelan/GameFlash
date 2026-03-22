import email
import unittest

from emails import gmail


class FakeSMTP:
    last_instance = None

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sent_messages = []
        self.logged_in_as = None
        self.started_tls = False
        FakeSMTP.last_instance = self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def ehlo(self):
        return None

    def starttls(self, context=None):
        self.started_tls = True

    def login(self, user, password):
        self.logged_in_as = (user, password)

    def sendmail(self, sender, recipients, raw_message):
        self.sent_messages.append((sender, recipients, raw_message))


class MilestoneOneThreeTests(unittest.TestCase):
    def test_build_email_html_renders_single_news_card(self):
        html_body = gmail.build_email_html(
            [
                "Tytuł: Helldivers 2 dostaje nowy update\n\n"
                "Podsumowanie: Aktualizacja dodaje nowa bron i poprawki balansu.\n\n"
                "Link: https://konsolowe.info/2026/03/helldivers-2-update/\n\n"
                "################################"
            ]
        )

        self.assertIn("GameFlash", html_body)
        self.assertIn("GameFlash News", html_body)
        self.assertIn("Helldivers 2 dostaje nowy update", html_body)
        self.assertIn("Czytaj pełny artykuł", html_body)
        self.assertIn("https://konsolowe.info/2026/03/helldivers-2-update/", html_body)
        self.assertIn("<style type=\"text/css\">", html_body)
        self.assertNotIn("Link:", html_body)

    def test_build_email_html_renders_multiple_news_cards(self):
        html_body = gmail.build_email_html(
            [
                "Tytuł: News One\n\nPodsumowanie: Pierwszy opis.\n\nLink: https://example.com/one\n\n################################",
                "Tytul: News Two\n\nPodsumowanie: Drugi opis.\n\nLink: https://example.com/two\n\n################################",
            ]
        )

        self.assertEqual(2, html_body.count("GameFlash News"))
        self.assertIn("News One", html_body)
        self.assertIn("News Two", html_body)
        self.assertIn("https://example.com/one", html_body)
        self.assertIn("https://example.com/two", html_body)
        self.assertNotIn("Link:", html_body)

    def test_build_plain_text_body_removes_separators_and_keeps_content(self):
        plain_body = gmail.build_plain_text_body(
            [
                "Tytuł: News One\n\nPodsumowanie: Pierwszy opis.\n\nLink: https://example.com/one\n\n################################",
                "Tytul: News Two\n\nPodsumowanie: Drugi opis.\n\nLink: https://example.com/two\n\n################################",
            ]
        )

        self.assertIn("News One", plain_body)
        self.assertIn("News Two", plain_body)
        self.assertIn("https://example.com/one", plain_body)
        self.assertIn("https://example.com/two", plain_body)
        self.assertNotIn("################################", plain_body)

    def test_send_email_builds_multipart_message_with_plain_and_html(self):
        original_smtp = gmail.smtplib.SMTP
        try:
            gmail.smtplib.SMTP = FakeSMTP

            gmail.send_email(
                recipients=["gracz@example.com", "drugi@example.com"],
                news_to_send=[
                    "Tytuł: Clair Obscur robi wrazenie\n\n"
                    "Podsumowanie: Nowy material pokazuje walke i klimat gry.\n\n"
                    "Link: https://example.com/clair-obscur\n\n"
                    "################################"
                ],
                sender_mail="sender@example.com",
                smtp_server="smtp.example.com",
                sender_pass="topsecret",
            )
        finally:
            gmail.smtplib.SMTP = original_smtp

        smtp_instance = FakeSMTP.last_instance
        self.assertIsNotNone(smtp_instance)
        self.assertTrue(smtp_instance.started_tls)
        self.assertEqual(("sender@example.com", "topsecret"), smtp_instance.logged_in_as)
        self.assertEqual(1, len(smtp_instance.sent_messages))

        sender, recipients, raw_message = smtp_instance.sent_messages[0]
        self.assertEqual("sender@example.com", sender)
        self.assertEqual(["gracz@example.com", "drugi@example.com"], recipients)

        parsed_message = email.message_from_string(raw_message)
        self.assertTrue(parsed_message.is_multipart())

        parts = parsed_message.get_payload()
        self.assertEqual(2, len(parts))
        self.assertEqual("text/plain", parts[0].get_content_type())
        self.assertEqual("text/html", parts[1].get_content_type())

        plain_payload = parts[0].get_payload(decode=True).decode("utf-8")
        html_payload = parts[1].get_payload(decode=True).decode("utf-8")

        self.assertIn("Clair Obscur robi wrazenie", plain_payload)
        self.assertIn("https://example.com/clair-obscur", plain_payload)
        self.assertIn("GameFlash", html_payload)
        self.assertIn("Czytaj pełny artykuł", html_payload)
        self.assertIn("https://example.com/clair-obscur", html_payload)
        self.assertNotIn("Link:", html_payload)


if __name__ == "__main__":
    unittest.main()
