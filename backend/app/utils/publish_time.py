import os
from datetime import datetime, timedelta, timezone

# IST timezone
IST = timezone(timedelta(hours=5, minutes=30))

def get_publish_time(now_utc: datetime) -> datetime:
    """
    Returns next publish time in UTC based on IST config
    """

    publish_time_str = os.getenv("YOUTUBE_PUBLISH_TIME", "21:00")

    try:
        hour, minute = map(int, publish_time_str.split(":"))
    except Exception:
        hour, minute = 21, 0

    # Convert current UTC → IST
    now_ist = now_utc.astimezone(IST)

    # Build today's publish time in IST
    publish_ist = now_ist.replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0,
    )

    # If already passed → schedule tomorrow
    if publish_ist <= now_ist:
        publish_ist += timedelta(days=1)

    # Convert back → UTC
    publish_utc = publish_ist.astimezone(timezone.utc)

    return publish_utc