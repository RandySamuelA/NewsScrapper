"""
news_fetcher.py
Mengambil berita dari RSS feeds secara gratis.
Mendukung multi-sumber dan filter kata kunci.
"""

import feedparser
import requests
import logging
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from configparser import ConfigParser
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger("NewsScrapper")


@dataclass
class Article:
    """Representasi satu artikel berita."""
    title: str
    url: str
    source: str
    published: str
    description: str = ""
    full_text: str = ""
    summary: str = ""
    category: str = "Umum"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "published": self.published,
            "description": self.description,
            "full_text": self.full_text,
            "summary": self.summary,
            "category": self.category,
        }


def _parse_rss_date(entry) -> str:
    """Konversi tanggal RSS ke string yang readable."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            return dt.strftime("%d %B %Y, %H:%M WIB")
        except Exception:
            pass
    return datetime.now().strftime("%d %B %Y, %H:%M WIB")


def _extract_description(entry) -> str:
    """Ambil deskripsi bersih dari entry RSS."""
    raw = ""
    if hasattr(entry, "summary") and entry.summary:
        raw = entry.summary
    elif hasattr(entry, "description") and entry.description:
        raw = entry.description

    if raw:
        # Strip HTML tags
        soup = BeautifulSoup(raw, "html.parser")
        return soup.get_text(separator=" ").strip()
    return ""


def _detect_source_name(feed_url: str, feed_title: str) -> str:
    """Deteksi nama sumber dari URL atau judul feed."""
    url_lower = feed_url.lower()
    if "bbc" in url_lower:
        return "BBC News"
    elif "nytimes" in url_lower:
        return "New York Times"
    elif "reuters" in url_lower:
        return "Reuters"
    elif "google" in url_lower:
        return "Google News"
    elif "kompas" in url_lower:
        return "Kompas"
    elif "detik" in url_lower:
        return "Detik"
    elif "tempo" in url_lower:
        return "Tempo"
    elif "cnbc" in url_lower:
        return "CNBC"
    elif "techcrunch" in url_lower:
        return "TechCrunch"
    elif "theverge" in url_lower:
        return "The Verge"
    return feed_title or "Unknown Source"


def _detect_category(feed_url: str) -> str:
    """Deteksi kategori dari URL feed."""
    url_lower = feed_url.lower()
    if any(k in url_lower for k in ["tech", "teknologi", "science"]):
        return "Teknologi"
    elif any(k in url_lower for k in ["business", "bisnis", "economy", "ekonomi", "finance"]):
        return "Bisnis"
    elif any(k in url_lower for k in ["sport", "olahraga"]):
        return "Olahraga"
    elif any(k in url_lower for k in ["world", "international", "dunia"]):
        return "Dunia"
    elif any(k in url_lower for k in ["health", "kesehatan"]):
        return "Kesehatan"
    return "Umum"


def _fetch_full_text(url: str, timeout: int = 10) -> str:
    """
    Coba ambil teks lengkap artikel dari URL.
    Fallback ke string kosong jika gagal.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Hapus elemen yang tidak relevan
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        # Cari konten utama artikel
        content_tags = soup.find_all(["article", "main"])
        if content_tags:
            text = " ".join(t.get_text(separator=" ") for t in content_tags)
        else:
            # Fallback ke semua <p>
            paragraphs = soup.find_all("p")
            text = " ".join(p.get_text() for p in paragraphs)

        # Bersihkan whitespace berlebihan
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return " ".join(lines)[:3000]  # Batasi 3000 karakter
    except Exception as e:
        logger.debug(f"Gagal fetch full text dari {url}: {e}")
        return ""


def fetch_articles(config: ConfigParser) -> list[Article]:
    """
    Fetch semua artikel dari semua RSS sumber yang dikonfigurasi.
    Returns list of Article objects.
    """
    rss_raw = config.get("news", "rss_sources", fallback="")
    rss_urls = [url.strip() for url in rss_raw.replace("\n", ",").split(",") if url.strip()]

    max_per_source = config.getint("news", "max_articles_per_source", fallback=5)
    focus_keywords_raw = config.get("news", "focus_keywords", fallback="").strip()
    focus_keywords = [kw.strip().lower() for kw in focus_keywords_raw.split(",") if kw.strip()]

    all_articles: list[Article] = []
    seen_titles: set[str] = set()

    logger.info(f"Fetching berita dari {len(rss_urls)} sumber RSS...")

    for rss_url in rss_urls:
        try:
            logger.debug(f"Parsing RSS: {rss_url}")
            feed = feedparser.parse(rss_url)

            if feed.bozo and not feed.entries:
                logger.warning(f"RSS tidak valid atau kosong: {rss_url}")
                continue

            source_name = _detect_source_name(rss_url, getattr(feed.feed, "title", ""))
            category = _detect_category(rss_url)
            count = 0

            for entry in feed.entries:
                if count >= max_per_source:
                    break

                title = getattr(entry, "title", "").strip()
                url = getattr(entry, "link", "").strip()

                if not title or not url:
                    continue

                # Dedup berdasarkan judul
                if title.lower() in seen_titles:
                    continue

                # Filter kata kunci jika diset
                if focus_keywords:
                    title_lower = title.lower()
                    desc_lower = _extract_description(entry).lower()
                    if not any(kw in title_lower or kw in desc_lower for kw in focus_keywords):
                        continue

                description = _extract_description(entry)
                published = _parse_rss_date(entry)

                # Ambil full text untuk summarization yang lebih baik
                full_text = _fetch_full_text(url) if description else ""

                article = Article(
                    title=title,
                    url=url,
                    source=source_name,
                    published=published,
                    description=description,
                    full_text=full_text,
                    category=category,
                )

                all_articles.append(article)
                seen_titles.add(title.lower())
                count += 1

            logger.info(f"  [{source_name}] {count} artikel berhasil diambil.")

        except Exception as e:
            logger.error(f"Error saat fetch RSS {rss_url}: {e}")

    logger.info(f"Total: {len(all_articles)} artikel dari semua sumber.")
    return all_articles
