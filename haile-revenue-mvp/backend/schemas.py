"""Strict API and database contracts for the Revenue OS backend."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, StrictStr


class CampaignStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


class CustomerTier(str, Enum):
    REGULAR = "regular"
    FAMILY = "family"
    VIP = "vip"
    PRICE_SENSITIVE = "price-sensitive"


class WeatherSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[StrictInt] = None
    ts: StrictStr
    temp_c: StrictFloat
    feels_like_c: Optional[StrictFloat] = None
    condition: StrictStr
    description: StrictStr
    humidity: Optional[StrictInt] = Field(default=None, ge=0, le=100)


class CampaignRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: StrictInt
    ts: StrictStr
    temp_c: StrictFloat
    condition: StrictStr
    target_segment: StrictStr
    message: StrictStr
    telegram_message_id: Optional[StrictInt] = None
    status: CampaignStatus
    recipients: StrictInt = Field(ge=0)


class StatsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temp_c: Optional[StrictFloat] = None
    condition: Optional[StrictStr] = None
    last_check: Optional[StrictStr] = None
    campaigns_today: StrictInt = Field(default=0, ge=0)
    messages_sent_today: StrictInt = Field(default=0, ge=0)
    total_leads: StrictInt = Field(default=0, ge=0)
    next_check_seconds: StrictInt = Field(ge=0)
    trigger_active: bool = False


class TestCampaignRequest(BaseModel):
    """Explicit request contract for the test campaign write endpoint."""

    model_config = ConfigDict(extra="forbid", strict=True)

    target_segment: StrictStr = Field(default="all-test", min_length=1, max_length=100)


class TestCampaignResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: StrictStr
    telegram_message_id: Optional[StrictInt] = None
    temp_c: StrictFloat
    recipients: StrictInt = Field(ge=0)


class CronRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: StrictStr
    triggered: bool
    campaign_id: Optional[StrictInt] = None
    snapshot: WeatherSnapshot


class LeadCreateRequest(BaseModel):
    """Validated contract retained for the CRM write path."""

    model_config = ConfigDict(extra="forbid", strict=True)

    name: StrictStr = Field(min_length=1, max_length=200)
    tier: CustomerTier = CustomerTier.REGULAR
    telegram_chat_id: Optional[StrictStr] = Field(default=None, max_length=200)


class RetentionTrackerPayload(BaseModel):
    """Stable contract for future retention/engagement events."""

    model_config = ConfigDict(extra="forbid", strict=True)

    customer_id: StrictStr = Field(min_length=1, max_length=100)
    engagement_status: StrictStr = Field(min_length=1, max_length=50)
    occurred_at: StrictStr
    metadata: dict[str, StrictStr] = Field(default_factory=dict)
