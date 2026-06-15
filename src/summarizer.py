"""
summarizer.py
Membuat summary artikel berita.

Mendukung dua metode GRATIS:
  1. extractive  - Menggunakan sumy (tidak butuh AI/internet tambahan)
  2. ollama      - Menggunakan LLM lokal via Ollama (gratis, butuh install Ollama)
"""

import logging
import re
import requests
from configparser import ConfigParser

logger = logging.getLogger("NewsScrapper")

# ─── Extractive Summarizer (sumy) ────────────────────────────────────────────

def _extractive_summary(text: str, num_sentences: int = 3) -> str:
    """
    Buat ringkasan extractive menggunakan sumy.
    Ambil kalimat-kalimat paling penting dari teks.
    """
    if not text or len(text.strip()) < 50:
        return text.strip()

    try:
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.summarizers.lsa import LsaSummarizer
        from sumy.nlp.stemmers import Stemmer
        from sumy.utils import get_stop_words

        # Deteksi bahasa (sederhana)
        lang = "english"

        parser = PlaintextParser.from_string(text, Tokenizer(lang))
        stemmer = Stemmer(lang)
        summarizer = LsaSummarizer(stemmer)
        summarizer.stop_words = get_stop_words(lang)

        sentences = summarizer(parser.document, num_sentences)
        result = " ".join(str(s) for s in sentences)
        return result if result.strip() else text[:300] + "..."

    except Exception as e:
        logger.debug(f"Sumy error, fallback ke truncate: {e}")
        return _simple_truncate(text, num_sentences)


def _simple_truncate(text: str, num_sentences: int = 3) -> str:
    """Fallback: ambil N kalimat pertama."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    selected = sentences[:num_sentences]
    return " ".join(selected) if selected else text[:300] + "..."


# ─── Ollama Summarizer (LLM Lokal) ───────────────────────────────────────────

def _ollama_summary(text: str, title: str, config: ConfigParser) -> str:
    """
    Buat summary menggunakan Ollama (LLM lokal, 100% gratis).
    Requires: Ollama installed & running di localhost.
    Download: https://ollama.com/
    """
    ollama_url = config.get("summarizer", "ollama_url", fallback="http://localhost:11434")
    model = config.get("summarizer", "ollama_model", fallback="llama3.2")
    language = config.get("news", "summary_language", fallback="id")

    lang_instruction = (
        "Berikan ringkasan dalam Bahasa Indonesia yang singkat dan jelas."
        if language == "id"
        else "Provide a brief and clear summary in English."
    )

    prompt = f"""Berikut adalah artikel berita dengan judul: "{title}"

Isi artikel:
{text[:2000]}

{lang_instruction} Ringkasan maksimal 3-4 kalimat, fokus pada poin-poin utama."""

    try:
        resp = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 200},
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
    except requests.exceptions.ConnectionError:
        logger.warning("Ollama tidak berjalan. Fallback ke extractive summarizer.")
        return ""
    except Exception as e:
        logger.warning(f"Ollama error: {e}. Fallback ke extractive.")
        return ""


# ─── Public API ──────────────────────────────────────────────────────────────

def summarize(title: str, description: str, full_text: str, config: ConfigParser) -> str:
    """
    Buat summary artikel. Pilih metode berdasarkan config.
    Returns string summary.
    """
    method = config.get("summarizer", "method", fallback="extractive").lower()
    num_sentences = config.getint("summarizer", "extractive_sentences", fallback=3)

    # Tentukan teks sumber untuk di-summarize
    source_text = full_text if len(full_text) > len(description) else description
    if not source_text:
        source_text = description or title

    if method == "ollama":
        result = _ollama_summary(source_text, title, config)
        if result:
            return result
        # Fallback ke extractive jika Ollama gagal
        logger.info("Menggunakan extractive summarizer sebagai fallback.")

    # Extractive (default)
    summary = _extractive_summary(source_text, num_sentences)
    return summary if summary else description[:300] + "..."


def ensure_nltk_data():
    """Download NLTK data yang diperlukan jika belum ada."""
    try:
        import nltk
        for package in ["punkt", "punkt_tab", "stopwords"]:
            try:
                nltk.data.find(f"tokenizers/{package}")
            except LookupError:
                try:
                    nltk.data.find(f"corpora/{package}")
                except LookupError:
                    logger.info(f"Downloading NLTK data: {package}")
                    nltk.download(package, quiet=True)
    except Exception as e:
        logger.debug(f"NLTK setup: {e}")
