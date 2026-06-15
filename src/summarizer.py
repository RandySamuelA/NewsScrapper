"""
summarizer.py
Pipeline: extractive summary → terjemah ke Bahasa Indonesia.

Alur untuk setiap artikel:
  1. Extractive summary (sumy/LSA) → pilih 3-4 kalimat terpenting
  2. Translate hasil summary ke Bahasa Indonesia (deep-translator, gratis)

Tidak butuh API key apapun.
"""

import logging
import re
import time
from configparser import ConfigParser

logger = logging.getLogger("NewsScrapper")


# ─── Step 1: Extractive Summary ──────────────────────────────────────────────

def _extractive_summary(text: str, num_sentences: int = 4) -> str:
    """
    Pilih N kalimat paling penting dari teks menggunakan algoritma LSA (sumy).
    Bekerja pada teks bahasa apapun — tidak perlu tahu bahasanya.
    """
    if not text or len(text.strip()) < 80:
        return text.strip()

    try:
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.summarizers.lsa import LsaSummarizer
        from sumy.nlp.stemmers import Stemmer
        from sumy.utils import get_stop_words

        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        stemmer = Stemmer("english")
        summarizer = LsaSummarizer(stemmer)
        summarizer.stop_words = get_stop_words("english")

        sentences = summarizer(parser.document, num_sentences)
        result = " ".join(str(s) for s in sentences).strip()
        return result if result else _simple_truncate(text, num_sentences)

    except Exception as e:
        logger.debug(f"Sumy error: {e}, fallback ke truncate")
        return _simple_truncate(text, num_sentences)


def _simple_truncate(text: str, num_sentences: int = 4) -> str:
    """Fallback: ambil N kalimat pertama."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return " ".join(sentences[:num_sentences]) if sentences else text[:400]


# ─── Step 2: Translate ke Bahasa Indonesia ───────────────────────────────────

def _translate_to_indonesian(text: str, retry: int = 2) -> str:
    """
    Terjemahkan teks ke Bahasa Indonesia menggunakan Google Translate
    via deep-translator (gratis, tanpa API key).

    Jika terjemahan gagal, kembalikan teks asli (tetap berguna).
    """
    if not text or len(text.strip()) < 10:
        return text

    for attempt in range(retry + 1):
        try:
            from deep_translator import GoogleTranslator
            translated = GoogleTranslator(source="auto", target="id").translate(text)
            return translated.strip() if translated else text
        except Exception as e:
            if attempt < retry:
                logger.debug(f"Translate gagal (attempt {attempt+1}), retry... Error: {e}")
                time.sleep(1)
            else:
                logger.debug(f"Translate gagal setelah {retry+1} attempt: {e}. Pakai teks asli.")
    return text


def _translate_title(title: str) -> str:
    """Terjemahkan judul artikel ke Bahasa Indonesia."""
    return _translate_to_indonesian(title)


# ─── Public API ──────────────────────────────────────────────────────────────

def summarize_and_translate(
    title: str,
    description: str,
    full_text: str,
    config: ConfigParser,
) -> tuple[str, str]:
    """
    Pipeline lengkap: summary + terjemahan Bahasa Indonesia.

    Returns:
        (translated_title, translated_summary) — keduanya dalam Bahasa Indonesia
    """
    num_sentences = config.getint("summarizer", "extractive_sentences", fallback=4)

    # Pilih sumber teks terbaik untuk disummary
    source_text = full_text if len(full_text) > len(description) else description
    if not source_text:
        source_text = description or title

    # Step 1: Extractive summary (ambil kalimat terpenting)
    raw_summary = _extractive_summary(source_text, num_sentences)
    if not raw_summary:
        raw_summary = source_text[:500]

    # Step 2: Terjemahkan summary & judul ke Bahasa Indonesia
    translated_title   = _translate_to_indonesian(title)
    translated_summary = _translate_to_indonesian(raw_summary)

    return translated_title, translated_summary


# Alias untuk backward compatibility dengan main.py lama
def summarize(title: str, description: str, full_text: str, config: ConfigParser) -> str:
    """Wrapper — hanya kembalikan summary (tanpa translated title)."""
    _, summary = summarize_and_translate(title, description, full_text, config)
    return summary


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
