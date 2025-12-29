"""Scheduled tasks for the application."""
from apscheduler.schedulers.background import BackgroundScheduler
from backend.app.shared.logger import scheduler_logger

scheduler = BackgroundScheduler()


def scheduled_portfolio_job():
    """Scheduled portfolio calculation job."""
    scheduler_logger.info("Running scheduled portfolio calculation...")
    try:
        # Import here to avoid circular imports
        from backend.app.routers.portfolio.services import portfolio_service
        portfolio_service.calc_portfolio()
        scheduler_logger.info("Portfolio calculation completed successfully.")
    except Exception as e:
        scheduler_logger.exception(f"Portfolio calculation failed: {e}")


def start_scheduled_tasks():
    """Start all scheduled tasks."""
    scheduler.add_job(
        scheduled_portfolio_job,
        trigger='interval',
        hours=1,
        id='portfolio_every_1h'
    )
    scheduler_logger.info(
        "Scheduler started with 1 job (hourly portfolio calc)."
    )
    scheduler.start()
