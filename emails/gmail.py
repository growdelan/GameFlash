"""Wysyłka maili"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import html
import re
import smtplib
import ssl

SEPARATOR = "################################"
TITLE_RE = re.compile(r"^Tytu[łl]:\s*(.+)$", re.MULTILINE)
SUMMARY_RE = re.compile(r"Podsumowanie:\s*(.+?)(?:\n\s*\nLink:|\nLink:|\Z)", re.DOTALL)
LINK_RE = re.compile(r"^Link:\s*(\S+)\s*$", re.MULTILINE)


def _normalize_news_entry(news_entry: str) -> str:
    """Usuwa techniczne separatory i porzadkuje biale znaki."""
    cleaned = str(news_entry).replace(SEPARATOR, "").strip()
    return cleaned


def _parse_news_entry(news_entry: str) -> dict:
    """Wyciaga tytul, podsumowanie i link z pojedynczego wpisu."""
    cleaned = _normalize_news_entry(news_entry)

    title_match = TITLE_RE.search(cleaned)
    summary_match = SUMMARY_RE.search(cleaned)
    link_match = LINK_RE.search(cleaned)

    return {
        "title": title_match.group(1).strip() if title_match else "Nowy news gamingowy",
        "summary": summary_match.group(1).strip() if summary_match else cleaned,
        "link": link_match.group(1).strip() if link_match else "",
    }


def build_plain_text_body(news_to_send: list) -> str:
    """Buduje fallback tekstowy dla klientow bez wsparcia HTML."""
    normalized_entries = []
    for news_entry in news_to_send:
        cleaned = _normalize_news_entry(news_entry)
        if cleaned:
            normalized_entries.append(cleaned)

    return "\n\n" + ("\n\n---\n\n".join(normalized_entries) if normalized_entries else "")


def _format_html_text(value: str) -> str:
    """Escapuje tekst i zachowuje podzial na akapity."""
    return "<br>".join(html.escape(value).splitlines())


def build_email_html(news_to_send: list) -> str:
    """Buduje stylowany e-mail HTML dla newsow gamingowych."""
    news_items = [_parse_news_entry(news_entry) for news_entry in news_to_send]

    cards = []
    for item in news_items:
        title_html = html.escape(item["title"])
        summary_html = _format_html_text(item["summary"])
        cta_html = ""
        if item["link"]:
            escaped_link = html.escape(item["link"], quote=True)
            cta_html = (
                f'<a class="button" href="{escaped_link}" target="_blank" '
                f'rel="noopener noreferrer">Czytaj pełny artykuł</a>'
            )

        cards.append(
            f"""
            <tr>
              <td class="card">
                <p class="eyebrow">GameFlash News</p>
                <h2>{title_html}</h2>
                <p class="summary">{summary_html}</p>
                {cta_html}
              </td>
            </tr>
            """
        )

    if not cards:
        cards.append(
            """
            <tr>
              <td class="card">
                <p class="eyebrow">GameFlash News</p>
                <h2>Brak nowych newsow</h2>
                <p class="summary">W tym przebiegu nie przygotowano zadnych nowych podsumowan do wysylki.</p>
              </td>
            </tr>
            """
        )

    cards_html = "\n".join(cards)

    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GameFlash - podsumowanie newsow</title>
<style type="text/css">
  body {{ margin: 0; padding: 0; background: #08111f; font-family: Arial, Helvetica, sans-serif; color: #d9e7ff; }}
  a {{ color: #6cf2ff; }}
  .wrapper {{ width: 100%; table-layout: fixed; padding: 24px 12px; background:
    radial-gradient(circle at top, #13233f 0%, #08111f 55%, #050a13 100%); }}
  .main {{ width: 100%; max-width: 680px; margin: 0 auto; border-collapse: collapse; }}
  .hero {{ padding: 32px 28px 24px; background: linear-gradient(135deg, #111c31 0%, #0f2c44 45%, #0a3f54 100%); border: 1px solid #1d3556; border-radius: 20px 20px 0 0; }}
  .hero h1 {{ margin: 0 0 10px; font-size: 30px; line-height: 1.1; color: #ffffff; }}
  .hero p {{ margin: 0; font-size: 15px; line-height: 1.6; color: #b7cbed; }}
  .accent {{ color: #7bf7c7; }}
  .card {{ padding: 24px 28px; background: #0d1728; border-left: 1px solid #1d3556; border-right: 1px solid #1d3556; border-bottom: 1px solid #1d3556; }}
  .eyebrow {{ margin: 0 0 10px; font-size: 11px; font-weight: bold; letter-spacing: 0.12em; text-transform: uppercase; color: #6cf2ff; }}
  .card h2 {{ margin: 0 0 12px; font-size: 22px; line-height: 1.3; color: #ffffff; }}
  .summary {{ margin: 0 0 18px; font-size: 15px; line-height: 1.7; color: #d9e7ff; }}
  .button {{ display: inline-block; padding: 12px 20px; border-radius: 999px; background: linear-gradient(135deg, #00d4ff 0%, #2af598 100%); color: #04111f !important; font-size: 13px; font-weight: bold; text-decoration: none; }}
  .footer {{ padding: 18px 28px 28px; background: #0d1728; border-left: 1px solid #1d3556; border-right: 1px solid #1d3556; border-bottom: 1px solid #1d3556; border-radius: 0 0 20px 20px; font-size: 12px; line-height: 1.6; color: #8ca4c7; text-align: center; }}
  @media only screen and (max-width: 620px) {{
    .wrapper {{ padding: 16px 8px; }}
    .hero {{ padding: 24px 20px 20px; }}
    .hero h1 {{ font-size: 24px !important; }}
    .card {{ padding: 20px; }}
    .card h2 {{ font-size: 20px !important; }}
    .summary {{ font-size: 14px !important; }}
    .button {{ display: block; text-align: center; }}
  }}
</style>
</head>
<body>
  <center class="wrapper">
    <table class="main" role="presentation" cellpadding="0" cellspacing="0">
      <tr>
        <td class="hero">
          <p class="eyebrow">Gaming Brief</p>
          <h1>GameFlash <span class="accent">Level Up</span></h1>
          <p>Najnowsze newsy ze swiata gier w bardziej czytelnej, nowoczesnej formie.</p>
        </td>
      </tr>
      {cards_html}
      <tr>
        <td class="footer">Wiadomosc wygenerowana automatycznie przez GameFlash. Otworz link w karcie, aby przejsc do pelnego artykulu.</td>
      </tr>
    </table>
  </center>
</body>
</html>
"""


def send_email(
    recipients: list,
    news_to_send: list,
    sender_mail: str,
    smtp_server: str,
    sender_pass: str,
):
    """Wysyłka maili"""
    plain_body = build_plain_text_body(news_to_send)
    html_body = build_email_html(news_to_send)

    msg = MIMEMultipart("alternative")
    msg["From"] = sender_mail
    msg["Subject"] = "Podsumowanie newsow z GameFlash"
    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    msg["Bcc"] = ", ".join(recipients)

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, 587) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender_mail, sender_pass)
        server.sendmail(sender_mail, recipients, msg.as_string())
