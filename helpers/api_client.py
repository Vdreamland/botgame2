import requests
from typing import Dict, Any, Optional

class ClawRoyaleAPIClient:
    BASE_URL = "https://cdn.clawroyale.ai/api"

    def __init__(self, api_key: str, version: str, auth_type: str = "mr-auth"):
        self.api_key = api_key
        self.version = version
        self.auth_type = auth_type
        self.session = requests.Session()
        self.session.headers.update(self._build_headers())

    def _build_headers(self) -> Dict[str, str]:
        headers = {"X-Version": self.version}
        if self.auth_type == "mr-auth":
            headers["Authorization"] = f"mr-auth {self.api_key}"
        elif self.auth_type == "Bearer":
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            headers["X-API-Key"] = self.api_key
        return headers

    def update_version(self, new_version: str):
        self.version = new_version
        self.session.headers.update({"X-Version": self.version})

    def get_version(self) -> Dict[str, Any]:
        resp = self.session.get(f"{self.BASE_URL}/version")
        resp.raise_for_status()
        return resp.json()

    def get_profile_me(self) -> Dict[str, Any]:
        resp = self.session.get(f"{self.BASE_URL}/accounts/me")
        resp.raise_for_status()
        return resp.json()

    def get_transaction_history(self, category: str = "all", limit: int = 20, cursor: Optional[str] = None) -> Dict[str, Any]:
        params = {"category": category, "limit": limit}
        if cursor:
            params["cursor"] = cursor
        resp = self.session.get(f"{self.BASE_URL}/accounts/history", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_loadout(self) -> Dict[str, Any]:
        resp = self.session.get(f"{self.BASE_URL}/api/loadout")
        resp.raise_for_status()
        return resp.json()

    def set_loadout_pack(self, pack_instance_id: str) -> Dict[str, Any]:
        resp = self.session.put(f"{self.BASE_URL}/api/loadout/pack", json={"packInstanceId": pack_instance_id})
        resp.raise_for_status()
        return resp.json()

    def set_loadout_sub_pack(self, pack_instance_id: str) -> Dict[str, Any]:
        resp = self.session.put(f"{self.BASE_URL}/api/loadout/sub-pack", json={"packInstanceId": pack_instance_id})
        resp.raise_for_status()
        return resp.json()

    def set_loadout_relic_slot(self, slot_index: int, relic_instance_id: str) -> Dict[str, Any]:
        resp = self.session.put(f"{self.BASE_URL}/api/loadout/slot/{slot_index}", json={"relicInstanceId": relic_instance_id})
        resp.raise_for_status()
        return resp.json()

    def purchase_shop_item(self, listing_id: str, quantity: int = 1) -> Dict[str, Any]:
        payload = {"listingId": listing_id, "quantity": quantity}
        resp = self.session.post(f"{self.BASE_URL}/api/shop/purchase", json=payload)
        resp.raise_for_status()
        return resp.json()

    def claim_stepped_quest(self, key: str, tier: int) -> Dict[str, Any]:
        resp = self.session.post(f"{self.BASE_URL}/api/preseason1/quests/{key}/claim/{tier}")
        resp.raise_for_status()
        return resp.json()

    def claim_daily_quest(self, key: str) -> Dict[str, Any]:
        resp = self.session.post(f"{self.BASE_URL}/api/preseason1/daily-quests/{key}/claim")
        resp.raise_for_status()
        return resp.json()