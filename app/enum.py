from enum import Enum as PyEnum

# -------------------------------------------------
# ENUMS
# -------------------------------------------------
class CaptionType(str, PyEnum):
    social_media = "social media"
    product_description = "product description"
    travel = "travel"
    food = "food"
    # receipt = "receipt"

class SubscriptionStatus(PyEnum):
    FREE = "FREE"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
