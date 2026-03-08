import logging
import signal
import sys
import time
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from send_brief import run_brief

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)


def safe_run_brief():
    logger.info("Scheduled job triggered")
    try:
        run_brief()
        logger.info("Scheduled job completed successfully")
    except Exception:
        logger.exception("Scheduled job failed")


def main():
    timezone = ZoneInfo("Europe/Budapest")
    scheduler = BackgroundScheduler(timezone=timezone)

    scheduler.add_job(
        safe_run_brief,
        trigger=CronTrigger(hour=6, minute=0, timezone=timezone),
        id="daily_stock_brief",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()

    job = scheduler.get_job("daily_stock_brief")
    logger.info("Scheduler started. Daily brief set for 06:00 Europe/Budapest.")
    logger.info("Next run time: %s", job.next_run_time)

    def shutdown(signum, frame):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()