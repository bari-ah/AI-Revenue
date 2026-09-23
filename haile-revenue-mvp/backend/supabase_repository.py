"""Supabase connection and persistence boundary.

The client is created lazily so a missing or temporarily unavailable Supabase
service does not terminate the ASGI process during import or startup.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


class ConfigurationError(RuntimeError):
    """Raised when required production configuration is absent."""


class SupabaseRepository:
    def __init__(self, client: Client) -> None:
        self.client = client

    def latest_weather(self) -> dict[str, Any] | None:
        response = (
            self.client.table("weather_snapshot")
            .select("id,ts,temp_c,feels_like_c,condition,description,humidity")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def insert_weather(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        response = self.client.table("weather_snapshot").insert(snapshot).execute()
        if not response.data:
            raise RuntimeError("Supabase did not return the inserted weather snapshot")
        return response.data[0]

    def recent_campaigns(self, limit: int = 20) -> list[dict[str, Any]]:
        response = (
            self.client.table("campaign")
            .select("id,ts,temp_c,condition,target_segment,message,telegram_message_id,status,recipients")
            .order("id", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data

    def count_campaigns_today(self, day_prefix: str) -> int:
        response = (
            self.client.table("campaign")
            .select("id", count="exact")
            .gte("ts", day_prefix)
            .lt("ts", f"{day_prefix[:-1]}Z")
            .execute()
        )
        return int(response.count or 0)

    def count_leads(self) -> int:
        response = self.client.table("lead").select("id", count="exact").execute()
        return int(response.count or 0)

    def insert_campaign(self, campaign: dict[str, Any]) -> dict[str, Any]:
        response = self.client.table("campaign").insert(campaign).execute()
        if not response.data:
            raise RuntimeError("Supabase did not return the inserted campaign")
        return response.data[0]


@lru_cache(maxsize=1)
def get_repository() -> SupabaseRepository:
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not key:
        raise ConfigurationError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    return SupabaseRepository(create_client(url, key))
