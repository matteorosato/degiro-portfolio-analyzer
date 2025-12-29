"""Scheduled tasks for the application."""
from apscheduler.schedulers.background import BackgroundScheduler
from backend.app.shared.logger import scheduler_logger

# TODO check if this module is needed
scheduler = BackgroundScheduler()


def scheduled_portfolio_job():
    """Scheduled portfolio calculation job."""
    scheduler_logger.info("Running scheduled portfolio calculation...")
    try:
        # Import here to avoid circular imports
        from backend.app.routers.portfolio.services import calc_portfolio
        calc_portfolio()
        scheduler_logger.info("Portfolio calculation completed successfully.")
    except Exception as e:
        scheduler_logger.exception(f"Portfolio calculation failed: {e}")


def scheduled_db_refresh_job():
    """Scheduled database refresh job."""
    scheduler_logger.info("Running scheduled DB refresh...")
    try:
        # Import here to avoid circular imports
        from backend.services.db_refresh import db_refresh
        db_refresh()
        scheduler_logger.info("DB refresh completed successfully.")
    except Exception as e:
        scheduler_logger.exception(f"DB refresh failed: {e}")


def start_scheduled_tasks():
    """Start all scheduled tasks."""
    scheduler.add_job(
        scheduled_db_refresh_job,
        trigger='cron',
        hour=3,
        minute=0,
        id='daily_db_refresh'
    )
    scheduler.add_job(
        scheduled_portfolio_job,
        trigger='interval',
        hours=1,
        id='portfolio_every_1h'
    )
    scheduler_logger.info(
        "Scheduler started with 2 jobs (daily db refresh and hourly portfolio calc)."
    )
    scheduler.start()
