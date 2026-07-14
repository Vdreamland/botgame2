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

    # =========================================================================
    # 1. AKUN & PROFIL ENDPOINTS
    # =========================================================================

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

    def redeem_code(self, code: str) -> Dict[str, Any]:
        resp = self.session.post(f"{self.BASE_URL}/api/redeem", json={"code": code})
        resp.raise_for_status()
        return resp.json()

    # =========================================================================
    # 2. LOADOUT ENDPOINTS
    # =========================================================================

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

    # =========================================================================
    # 3. SHOP & REFORGE ENDPOINTS
    # =========================================================================

    def get_shop_inventory_status(self) -> Dict[str, Any]:
        resp = self.session.get(f"{self.BASE_URL}/api/shop/inventory-status")
        resp.raise_for_status()
        return resp.json()

    def purchase_shop_item(self, listing_id: str, quantity: int = 1) -> Dict[str, Any]:
        payload = {"listingId": listing_id, "quantity": quantity}
        resp = self.session.post(f"{self.BASE_URL}/api/shop/purchase", json=payload)
        resp.raise_for_status()
        return resp.json()

    def reforge_item(self, relic_instance_id: Optional[str] = None, pack_instance_id: Optional[str] = None) -> Dict[str, Any]:
        payload = {}
        if relic_instance_id:
            payload["relicInstanceId"] = relic_instance_id
        elif pack_instance_id:
            payload["packInstanceId"] = pack_instance_id
        resp = self.session.post(f"{self.BASE_URL}/api/reforge", json=payload)
        resp.raise_for_status()
        return resp.json()

    # =========================================================================
    # 4. PRESEASON 1 QUEST ENDPOINTS
    # =========================================================================

    def claim_stepped_quest(self, key: str, tier: int) -> Dict[str, Any]:
        resp = self.session.post(f"{self.BASE_URL}/api/preseason1/quests/{key}/claim/{tier}")
        resp.raise_for_status()
        return resp.json()

    def claim_daily_quest(self, key: str) -> Dict[str, Any]:
        resp = self.session.post(f"{self.BASE_URL}/api/preseason1/daily-quests/{key}/claim")
        resp.raise_for_status()
        return resp.json()

    # =========================================================================
    # 5. P2P MARKETPLACE ENDPOINTS
    # =========================================================================

    def get_marketplace_listings(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        resp = self.session.get(f"{self.BASE_URL}/api/marketplace/listings", params=params)
        resp.raise_for_status()
        return resp.json()

    def buy_marketplace_listing(self, listing_id: str, quantity: int = 1, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        resp = self.session.post(
            f"{self.BASE_URL}/api/marketplace/listings/{listing_id}/buy", 
            json={"quantity": quantity}, 
            headers=headers
        )
        resp.raise_for_status()
        return resp.json()

    def create_marketplace_listing(self, payload: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        resp = self.session.post(
            f"{self.BASE_URL}/api/marketplace/listings", 
            json=payload, 
            headers=headers
        )
        resp.raise_for_status()
        return resp.json()

    def cancel_marketplace_listing(self, listing_id: str) -> Dict[str, Any]:
        resp = self.session.delete(f"{self.BASE_URL}/api/marketplace/listings/{listing_id}")
        resp.raise_for_status()
        return resp.json()

    # =========================================================================
    # 6. IN-APP NOTIFICATION ENDPOINTS
    # =========================================================================

    def get_notifications(self, unread_only: bool = False, limit: int = 20) -> Dict[str, Any]:
        params = {"unreadOnly": unread_only, "limit": limit}
        resp = self.session.get(f"{self.BASE_URL}/api/notifications", params=params)
        resp.raise_for_status()
        return resp.json()

    def mark_notification_read(self, notification_id: str) -> Dict[str, Any]:
        resp = self.session.post(f"{self.BASE_URL}/api/notifications/{notification_id}/read")
        resp.raise_for_status()
        return resp.json()

    def mark_all_notifications_read(self) -> Dict[str, Any]:
        resp = self.session.post(f"{self.BASE_URL}/api/notifications/read-all")
        resp.raise_for_status()
        return resp.json()

    def delete_notification(self, notification_id: str) -> Dict[str, Any]:
        resp = self.session.delete(f"{self.BASE_URL}/api/notifications/{notification_id}")
        resp.raise_for_status()
        return resp.json()

    def clear_all_notifications(self) -> Dict[str, Any]:
        resp = self.session.post(f"{self.BASE_URL}/api/notifications/clear-all")
        resp.raise_for_status()
        return resp.json()

    # =========================================================================
    # 7. PERFORMANCE DASHBOARD ENDPOINTS (Tanpa {success, data} envelope)
    # =========================================================================

    def get_dashboard_overview(self, window: str = "7d", entry_type: str = "all") -> Dict[str, Any]:
        params = {"window": window, "entryType": entry_type}
        resp = self.session.get(f"{self.BASE_URL}/api/accounts/me/dashboard/overview", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_dashboard_daily(self, window: str = "7d", entry_type: str = "all") -> Dict[str, Any]:
        params = {"window": window, "entryType": entry_type}
        resp = self.session.get(f"{self.BASE_URL}/api/accounts/me/dashboard/daily", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_dashboard_combat(self, window: str = "7d", entry_type: str = "all") -> Dict[str, Any]:
        params = {"window": window, "entryType": entry_type}
        resp = self.session.get(f"{self.BASE_URL}/api/accounts/me/dashboard/combat", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_dashboard_games(self, limit: int = 20, cursor: Optional[str] = None) -> Dict[str, Any]:
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        resp = self.session.get(f"{self.BASE_URL}/api/accounts/me/dashboard/games", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_acquisitions_log(self, limit: int = 20, cursor: Optional[str] = None) -> Dict[str, Any]:
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        resp = self.session.get(f"{self.BASE_URL}/api/accounts/me/acquisitions", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_leaderboard_rank(self, board: str = "smoltz") -> Dict[str, Any]:
        params = {"board": board}
        resp = self.session.get(f"{self.BASE_URL}/api/accounts/me/leaderboard-rank", params=params)
        resp.raise_for_status()
        return resp.json()