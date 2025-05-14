from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models

def reset_daily_usage():
    db: Session = SessionLocal()
    now_utc = datetime.now(timezone.utc)

    users = db.query(models.User).all()
    for user in users:
        user_tz = ZoneInfo(user.timezone or "Africa/Lagos")
        local_time = now_utc.astimezone(user_tz)

        if local_time.hour == 0:
            user.daily_usage = 0
            db.commit()

    db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        reset_daily_usage,
        trigger=IntervalTrigger(minutes=60),  # runs every hour
        id="daily_usage_reset",
        replace_existing=True,
    )
    scheduler.start()
