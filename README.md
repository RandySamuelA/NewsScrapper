# 📰 NewsScrapper

Automation scraping berita harian dari berbagai sumber RSS, membuat summary otomatis, dan mengirimkan digest ke email setiap pagi — **100% gratis, tanpa biaya apapun**.

---

## Fitur

- **Scraping berita** dari RSS feeds (BBC, NYT, Reuters, Google News, Kompas, dll)
- **Summary otomatis** menggunakan NLP extractive (sumy) — tanpa API berbayar
- **Opsional**: summary dengan LLM lokal via [Ollama](https://ollama.com/) (gratis, jalan di komputer sendiri)
- **Email HTML** yang rapi dan mobile-friendly via Gmail SMTP
- **Scheduler otomatis** — kirim email setiap pagi di jam yang ditentukan
- **Multi-kategori**: Teknologi, Bisnis, Dunia, Olahraga, Kesehatan, dll
- **Filter kata kunci** opsional untuk fokus pada topik tertentu

---

## Instalasi

### 1. Buat virtual environment
```bash
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/Mac
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi

Edit `config/config.ini`:

```ini
[email]
email_user     = email_kamu@gmail.com
email_password = xxxx xxxx xxxx xxxx   # Gmail App Password
recipient_email = tujuan@gmail.com

[news]
schedule_time = 07:00                  # Jam kirim email (WIB)
max_articles_per_source = 5

[summarizer]
method = extractive                    # extractive (default) atau ollama
```

> **Penting**: `email_password` bukan password Gmail biasa, tapi **App Password**.
> Cara membuat: Google Account → Security → 2-Step Verification → App passwords

---

## Cara Pakai

### Test langsung (jalankan sekali):
```bash
python src/main.py --run-now
```

### Test konfigurasi email:
```bash
python src/main.py --test-email
```

### Jalankan scheduler lokal (laptop harus nyala):
```bash
python src/main.py --schedule
```

---

## Deploy ke GitHub Actions (Gratis, Laptop Bisa Mati)

GitHub Actions menjalankan script di server GitHub — laptop tidak perlu nyala.
Gratis hingga **2.000 menit/bulan** (script ini hanya ~2 menit/hari = 60 menit/bulan).

### Langkah 1 — Push ke GitHub

```bash
git init
git add .
git commit -m "feat: NewsScrapper initial commit"
git remote add origin https://github.com/USERNAME/NewsScrapper.git
git push -u origin main
```

> `config/config.ini` sudah di-exclude oleh `.gitignore` — password tidak akan ikut push.

### Langkah 2 — Tambahkan GitHub Secrets

Di halaman repository GitHub: **Settings → Secrets and variables → Actions → New repository secret**

Tambahkan 3 secrets berikut:

| Secret Name       | Value                          |
|-------------------|--------------------------------|
| `EMAIL_USER`      | `randysamuelboyz@gmail.com`    |
| `EMAIL_PASSWORD`  | `ajpw qyce wfhz tnbt`          |
| `RECIPIENT_EMAIL` | `samuelrandya@gmail.com`       |

### Langkah 3 — Aktifkan Actions

Buka tab **Actions** di repository GitHub → klik **Enable GitHub Actions**.

### Langkah 4 — Test Manual

Buka **Actions → Daily News Digest → Run workflow** untuk test sebelum menunggu jadwal.

### Jadwal Otomatis

Workflow berjalan setiap hari pukul **07:00 WIB** (00:00 UTC).
Untuk mengubah jam, edit baris `cron` di `.github/workflows/daily-news.yml`:

```yaml
# Format: menit jam hari bulan hari-dalam-seminggu (UTC)
- cron: "0 0 * * *"   # 00:00 UTC = 07:00 WIB
- cron: "0 1 * * *"   # 01:00 UTC = 08:00 WIB
- cron: "30 22 * * *" # 22:30 UTC = 05:30 WIB
```

---

## Menambah Sumber Berita

Edit bagian `rss_sources` di `config/config.ini`. Beberapa contoh RSS gratis:

| Sumber | URL RSS |
|--------|---------|
| BBC News | `https://feeds.bbci.co.uk/news/rss.xml` |
| BBC Tech | `https://feeds.bbci.co.uk/news/technology/rss.xml` |
| NYT Tech | `https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml` |
| Reuters Tech | `https://feeds.reuters.com/reuters/technologyNews` |
| Google News ID | `https://news.google.com/rss?hl=id&gl=ID&ceid=ID:id` |
| Kompas | `https://rss.kompas.com/nasional` |
| Detik | `https://rss.detik.com/index.php/detikcom` |
| CNBC Tech | `https://www.cnbc.com/id/19854910/device/rss/rss.html` |
| TechCrunch | `https://techcrunch.com/feed/` |
| The Verge | `https://www.theverge.com/rss/index.xml` |

---

## Menggunakan Ollama (LLM Lokal, Opsional)

Untuk summary yang lebih natural menggunakan AI lokal:

1. Download & install [Ollama](https://ollama.com/)
2. Pull model: `ollama pull llama3.2`
3. Edit config:
   ```ini
   [summarizer]
   method = ollama
   ollama_model = llama3.2
   ```

---

## Struktur Project

```
NewsScrapper/
├── config/
│   └── config.ini          # Konfigurasi (email, RSS, jadwal)
├── data/
│   └── output/             # Output jika diperlukan
├── logs/
│   └── app.log             # Log aplikasi
├── src/
│   ├── main.py             # Entry point
│   ├── news_fetcher.py     # Scraping RSS feeds
│   ├── summarizer.py       # Summary artikel (extractive / ollama)
│   ├── email_sender.py     # Kirim email HTML
│   ├── scheduler.py        # Penjadwal harian
│   └── logger.py           # Setup logging
├── requirements.txt
└── README.md
```

---

## Menjalankan Otomatis saat Startup Windows

Agar berjalan otomatis setiap Windows menyala, buat file `.bat`:

```batch
@echo off
cd C:\path\to\NewsScrapper
call venv\Scripts\activate
python src/main.py --schedule
```

Lalu tambahkan shortcut ke `shell:startup` (Win+R → ketik `shell:startup`).
