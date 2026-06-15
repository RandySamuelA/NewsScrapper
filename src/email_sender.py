"""
email_sender.py
Kirim email daily news digest via Gmail SMTP (gratis).
Email dikirim dalam format HTML yang rapi dan mobile-friendly.
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from configparser import ConfigParser
from datetime import datetime
from jinja2 import Template

from src.news_fetcher import Article

logger = logging.getLogger("NewsScrapper")

# ─── HTML Template ────────────────────────────────────────────────────────────

EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>News Digest</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background-color: #f4f6f9;
      color: #333;
      line-height: 1.6;
    }
    .container {
      max-width: 680px;
      margin: 0 auto;
      background: #ffffff;
    }
    .header {
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      color: #ffffff;
      padding: 32px 28px;
      text-align: center;
    }
    .header .logo {
      font-size: 13px;
      letter-spacing: 3px;
      text-transform: uppercase;
      color: #e94560;
      margin-bottom: 8px;
    }
    .header h1 {
      font-size: 28px;
      font-weight: 700;
      margin-bottom: 6px;
    }
    .header .date {
      font-size: 14px;
      color: #a0aec0;
    }
    .stats-bar {
      background: #f7fafc;
      border-bottom: 1px solid #e2e8f0;
      padding: 14px 28px;
      display: flex;
      gap: 24px;
      font-size: 13px;
      color: #718096;
    }
    .stats-bar span strong {
      color: #2d3748;
    }
    .category-section {
      padding: 0;
    }
    .category-header {
      background: #f7fafc;
      border-left: 4px solid #e94560;
      padding: 12px 28px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 2px;
      text-transform: uppercase;
      color: #4a5568;
      border-top: 1px solid #e2e8f0;
    }
    .article-card {
      padding: 20px 28px;
      border-bottom: 1px solid #f0f4f8;
      transition: background 0.2s;
    }
    .article-card:hover {
      background: #f7fafc;
    }
    .article-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
    }
    .source-badge {
      background: #e94560;
      color: white;
      font-size: 10px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 20px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .article-date {
      font-size: 12px;
      color: #a0aec0;
    }
    .article-title {
      font-size: 17px;
      font-weight: 700;
      color: #1a202c;
      margin-bottom: 8px;
      line-height: 1.4;
    }
    .article-title a {
      color: #1a202c;
      text-decoration: none;
    }
    .article-title a:hover {
      color: #e94560;
    }
    .article-summary {
      font-size: 14px;
      color: #4a5568;
      line-height: 1.7;
      margin-bottom: 10px;
    }
    .read-more {
      display: inline-block;
      font-size: 12px;
      color: #e94560;
      font-weight: 600;
      text-decoration: none;
    }
    .read-more:hover {
      text-decoration: underline;
    }
    .footer {
      background: #1a1a2e;
      color: #718096;
      text-align: center;
      padding: 24px 28px;
      font-size: 12px;
      line-height: 1.8;
    }
    .footer a {
      color: #e94560;
      text-decoration: none;
    }
    @media (max-width: 600px) {
      .header h1 { font-size: 22px; }
      .article-card { padding: 16px 18px; }
      .stats-bar { flex-direction: column; gap: 6px; }
    }
  </style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="header">
    <div class="logo">📰 News Digest</div>
    <h1>Rangkuman Berita Pagi</h1>
    <div class="date">{{ date }}, {{ time }} WIB</div>
  </div>

  <!-- Stats bar -->
  <div class="stats-bar">
    <span>📄 <strong>{{ total_articles }}</strong> artikel</span>
    <span>🗂️ <strong>{{ total_categories }}</strong> kategori</span>
    <span>📡 <strong>{{ total_sources }}</strong> sumber</span>
  </div>

  <!-- Articles by category -->
  {% for category, articles in categories.items() %}
  <div class="category-section">
    <div class="category-header">{{ category }}</div>
    {% for article in articles %}
    <div class="article-card">
      <div class="article-meta">
        <span class="source-badge">{{ article.source }}</span>
        <span class="article-date">{{ article.published }}</span>
      </div>
      <div class="article-title">
        <a href="{{ article.url }}" target="_blank">{{ article.title }}</a>
      </div>
      {% if article.summary %}
      <div class="article-summary">{{ article.summary }}</div>
      {% endif %}
      <a href="{{ article.url }}" class="read-more" target="_blank">Baca selengkapnya →</a>
    </div>
    {% endfor %}
  </div>
  {% endfor %}

  <!-- Footer -->
  <div class="footer">
    <p>Email ini dikirim otomatis oleh <strong>NewsScrapper</strong></p>
    <p>Dibuat dengan 💻 Python + RSS Feeds gratis</p>
    <p style="margin-top: 8px; font-size: 11px; color: #4a5568;">
      Sumber: {{ sources_list }}
    </p>
  </div>

</div>
</body>
</html>
"""


def _group_by_category(articles: list[Article]) -> dict[str, list[Article]]:
    """Kelompokkan artikel berdasarkan kategori."""
    categories: dict[str, list[Article]] = {}
    for article in articles:
        cat = article.category
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(article)
    return categories


def build_html_email(articles: list[Article]) -> str:
    """Render HTML email dari template Jinja2."""
    now = datetime.now()
    categories = _group_by_category(articles)
    sources = list({a.source for a in articles})

    template = Template(EMAIL_TEMPLATE)
    return template.render(
        date=now.strftime("%A, %d %B %Y"),
        time=now.strftime("%H:%M"),
        total_articles=len(articles),
        total_categories=len(categories),
        total_sources=len(sources),
        categories=categories,
        sources_list=", ".join(sources),
    )


def send_email(articles: list[Article], config: ConfigParser) -> bool:
    """
    Kirim email digest berita via Gmail SMTP.
    Returns True jika berhasil, False jika gagal.
    """
    smtp_host = config.get("email", "smtp_host", fallback="smtp.gmail.com")
    smtp_port = config.getint("email", "smtp_port", fallback=587)
    email_user = config.get("email", "email_user")
    email_password = config.get("email", "email_password")
    recipient = config.get("email", "recipient_email")

    now = datetime.now()
    subject = f"📰 News Digest — {now.strftime('%A, %d %B %Y')}"

    html_body = build_html_email(articles)

    # Buat pesan email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"NewsScrapper <{email_user}>"
    msg["To"] = recipient

    # Plain text fallback
    plain_text = f"News Digest - {now.strftime('%d %B %Y')}\n\n"
    plain_text += f"Total: {len(articles)} artikel\n\n"
    for article in articles:
        plain_text += f"[{article.source}] {article.title}\n"
        plain_text += f"{article.url}\n"
        if article.summary:
            plain_text += f"{article.summary}\n"
        plain_text += "\n"

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        logger.info(f"Mengirim email ke {recipient}...")
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(email_user, email_password)
            server.sendmail(email_user, recipient, msg.as_string())

        logger.info(f"✅ Email berhasil dikirim ke {recipient}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("❌ Autentikasi Gmail gagal. Pastikan App Password sudah benar.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"❌ SMTP error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error kirim email: {e}")
        return False
