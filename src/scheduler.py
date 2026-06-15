"""
scheduler.py
Penjadwal otomatis menggunakan APScheduler.
Menjalankan pipeline setiap hari pada jam yang dikonfigurasi.
"""

import logging
import time
from configparser import ConfigParser
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("NewsScrapper")


def start_scheduler(config: ConfigParser, pipeline_fn) -> None:
    """
    Mulai scheduler yang menjalankan pipeline_fn setiap hari
    pada jam yang dikonfigurasi di config.ini [news] schedule_time.

    Args:
        config: ConfigParser object
        pipeline_fn: fungsi pipeline yang akan dijalankan (callable)
    """
    schedule_time = config.get("news", "schedule_time", fallback="07:00")

    try:
        hour, minute = schedule_time.strip().split(":")
        hour = int(hour)
        minute = int(minute)
    except ValueError:
        logger.warning(f"Format schedule_time '{schedule_time}' tidak valid. Menggunakan 07:00.")
        hour, minute = 7, 0

    scheduler = BlockingScheduler(timezone="Asia/Jakarta")

    scheduler.add_job(
        pipeline_fn,
        trigger=CronTrigger(hour=hour, minute=minute),
        id="daily_news_digest",
        name=f"Daily News Digest [{hour:02d}:{minute:02d}]",
        misfire_grace_time=300,  # Toleransi 5 menit keterlambatan
        replace_existing=True,
    )

    logger.info(f"⏰ Scheduler aktif — Pipeline akan berjalan setiap hari pukul {hour:02d}:{minute:02d} WIB")
    logger.info("   Tekan Ctrl+C untuk menghentikan.")

    # Tampilkan waktu job berikutnya
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        if next_run:
            logger.info(f"   Next run: {next_run.strftime('%A, %d %B %Y %H:%M:%S')}")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler dihentikan oleh user.")
        scheduler.shutdown()
