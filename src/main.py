"""
main.py
Entry point NewsScrapper.

Cara pakai:
  1. Jalankan sekali (test): python src/main.py --run-now
  2. Mode scheduler       : python src/main.py --schedule
  3. Tes email saja       : python src/main.py --test-email
"""

import argparse
import sys
import os
from configparser import ConfigParser

# Tambahkan root project ke sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.logger import setup_logger
from src.news_fetcher import fetch_articles
from src.summarizer import summarize, ensure_nltk_data
from src.email_sender import send_email
from src.scheduler import start_scheduler


def load_config() -> ConfigParser:
    """
    Load konfigurasi dengan prioritas:
    1. Environment variables (dipakai saat jalan di GitHub Actions / server)
    2. config.ini (dipakai saat jalan di lokal)

    Environment variables yang didukung:
      EMAIL_USER, EMAIL_PASSWORD, RECIPIENT_EMAIL,
      SMTP_HOST, SMTP_PORT
    """
    config = ConfigParser()

    # Coba baca config.ini terlebih dahulu sebagai base
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "config.ini",
    )
    if os.path.exists(config_path):
        config.read(config_path, encoding="utf-8")

    # Override dengan environment variables jika ada
    # Ini yang dipakai saat jalan di GitHub Actions
    env_overrides = {
        ("email", "email_user"):      os.environ.get("EMAIL_USER"),
        ("email", "email_password"):  os.environ.get("EMAIL_PASSWORD"),
        ("email", "recipient_email"): os.environ.get("RECIPIENT_EMAIL"),
        ("email", "smtp_host"):       os.environ.get("SMTP_HOST"),
        ("email", "smtp_port"):       os.environ.get("SMTP_PORT"),
    }

    for (section, key), value in env_overrides.items():
        if value:  # Hanya override jika env var ada dan tidak kosong
            if not config.has_section(section):
                config.add_section(section)
            config.set(section, key, value)

    # Validasi: pastikan kredensial email tersedia
    try:
        config.get("email", "email_user")
        config.get("email", "email_password")
        config.get("email", "recipient_email")
    except Exception:
        raise RuntimeError(
            "Konfigurasi email tidak lengkap. "
            "Set environment variables EMAIL_USER, EMAIL_PASSWORD, RECIPIENT_EMAIL "
            "atau isi config/config.ini."
        )

    return config


def run_pipeline(config: ConfigParser) -> None:
    """
    Jalankan pipeline lengkap:
      1. Fetch artikel dari RSS
      2. Generate summary tiap artikel
      3. Kirim email digest
    """
    logger = setup_logger(config)
    logger.info("=" * 55)
    logger.info("  NewsScrapper Pipeline Dimulai")
    logger.info("=" * 55)

    # 1. Pastikan NLTK data tersedia
    ensure_nltk_data()

    # 2. Fetch semua artikel
    articles = fetch_articles(config)
    if not articles:
        logger.warning("Tidak ada artikel yang berhasil diambil. Pipeline dihentikan.")
        return

    # 3. Generate summary untuk tiap artikel
    logger.info(f"Membuat summary untuk {len(articles)} artikel...")
    for i, article in enumerate(articles, 1):
        logger.debug(f"  Summarizing [{i}/{len(articles)}]: {article.title[:50]}...")
        article.summary = summarize(
            title=article.title,
            description=article.description,
            full_text=article.full_text,
            config=config,
        )

    # 4. Kirim email
    success = send_email(articles, config)

    if success:
        logger.info("=" * 55)
        logger.info("  ✅ Pipeline selesai. Email berhasil dikirim!")
        logger.info("=" * 55)
    else:
        logger.error("=" * 55)
        logger.error("  ❌ Pipeline selesai, tapi email GAGAL dikirim.")
        logger.error("=" * 55)


def run_test_email(config: ConfigParser) -> None:
    """Kirim email test dengan 1 artikel dummy untuk verifikasi konfigurasi."""
    from src.news_fetcher import Article
    logger = setup_logger(config)
    logger.info("Mengirim email test...")

    dummy_articles = [
        Article(
            title="Test Email dari NewsScrapper",
            url="https://example.com",
            source="NewsScrapper",
            published="Hari ini",
            description="Ini adalah email test untuk memverifikasi konfigurasi SMTP sudah benar.",
            summary="Konfigurasi email NewsScrapper berjalan dengan baik. "
                    "Email harian akan dikirim sesuai jadwal yang dikonfigurasi.",
            category="Teknologi",
        )
    ]

    success = send_email(dummy_articles, config)
    if success:
        logger.info("✅ Email test berhasil dikirim! Cek inbox Anda.")
    else:
        logger.error("❌ Email test gagal. Periksa konfigurasi email di config.ini.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NewsScrapper - Rangkuman berita harian otomatis via email",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  python src/main.py --run-now          # Jalankan pipeline sekarang (untuk testing)
  python src/main.py --schedule         # Jalankan scheduler harian otomatis
  python src/main.py --test-email       # Test konfigurasi email
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--run-now",
        action="store_true",
        help="Jalankan pipeline scraping & email sekarang juga.",
    )
    group.add_argument(
        "--schedule",
        action="store_true",
        help="Jalankan scheduler otomatis (jalan terus, kirim email tiap pagi).",
    )
    group.add_argument(
        "--test-email",
        action="store_true",
        help="Kirim email test untuk verifikasi konfigurasi.",
    )

    args = parser.parse_args()
    config = load_config()
    setup_logger(config)

    if args.run_now:
        run_pipeline(config)

    elif args.schedule:
        # Jalankan scheduler, pipeline dieksekusi otomatis sesuai jadwal
        start_scheduler(config, lambda: run_pipeline(config))

    elif args.test_email:
        run_test_email(config)


if __name__ == "__main__":
    main()
