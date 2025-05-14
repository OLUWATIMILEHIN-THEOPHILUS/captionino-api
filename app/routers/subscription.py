# Subscription logic here.

from fastapi import APIRouter, Request, status, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, utils
import json

router = APIRouter(
    prefix="/subscription",
    tags=["Subscription"]
)

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def subscription_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()

    utils.verify_signature(request, body)

    # Parse payload
    payload = json.loads(body)
    event_type = payload.get("meta", {}).get("event_name")
    subscription_data = payload.get("data", {}).get("attributes", {})

    subscription_id = subscription_data.get("id")
    customer_id = subscription_data.get("customer_id")
    customer_email = subscription_data.get("user_email")
    status = subscription_data.get("status")

    print(f"[Webhook] Event: {event_type}, Email: {customer_email}, Status: {status}, Customer ID: {customer_id}")

    # Try matching user by email first, fallback to customer_id
    user = (
        db.query(models.User)
        .filter(
            (models.User.email == customer_email) |
            (models.User.lemonsqueezy_customer_id == str(customer_id))
        )
        .first()
    )

    if not user:
        print("User not found for email or customer ID:", customer_email, customer_id)
        return {"message": "User not found"}

    # Update user based on event type
    if event_type == "subscription_created":
        user.subscription_status = "ACTIVE"
        user.lemonsqueezy_subscription_id = str(subscription_id)
        user.lemonsqueezy_customer_id = str(customer_id)

    elif event_type == "subscription_cancelled":
        user.subscription_status = "CANCELLED"

    elif event_type == "subscription_expired":
        user.subscription_status = "EXPIRED"

    elif event_type == "subscription_paused":
        user.subscription_status = "PAUSED"

    elif event_type == "subscription_resumed":
        user.subscription_status = "ACTIVE"

    db.commit()
    print("User subscription status updated.")

    return {"message": "Success"}


# For cron-job (next is on cron-job.org)

# @router.get("/reset-usage-daily", include_in_schema=False)
# def reset_usage_task(db: Session = Depends(get_db)):
#     now_utc = datetime.now(timezone.utc)
#     users = db.query(models.User).all()

#     for user in users:
#         user_tz = ZoneInfo(user.timezone or "Africa/Lagos")
#         local_time = now_utc.astimezone(user_tz)

#         if local_time.hour == 0:
#             user.daily_usage = 0
#             db.commit()

#     return {"status": "reset complete"}
