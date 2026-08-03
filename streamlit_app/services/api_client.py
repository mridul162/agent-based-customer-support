import os
from typing import Any

import requests
from config.settings import settings

DEFAULT_API_BASE_URL = settings.DEFAULT_API_BASE_URL


class ApiClientError(RuntimeError):
    pass


class SupportApiClient:
    def __init__(self, base_url: str | None = None, timeout: int = 30) -> None:
        self.base_url = (
            base_url or os.getenv("SUPPORT_API_BASE_URL") or DEFAULT_API_BASE_URL
        ).rstrip("/")
        self.timeout = timeout

    def send_message(self, customer_id: str, message: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/support/message",
            json={"customer_id": customer_id, "message": message},
        )

    def get_conversation(self, customer_id: str) -> dict[str, Any]:
        return self._request("GET", f"/support/conversations/{customer_id}")

    def get_ticket(self, ticket_id: str) -> dict[str, Any]:
        return self._request("GET", f"/support/tickets/{ticket_id}")

    def list_tickets(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._request("GET", "/support/tickets", params={"limit": limit})

    def get_evaluation_summary(self) -> dict[str, Any]:
        return self._request("GET", "/evaluation/summary")

    def get_health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = requests.request(
                method,
                f"{self.base_url}{path}",
                timeout=self.timeout,
                **kwargs,
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            detail = None
            try:
                detail = exc.response.json().get("detail")  # type: ignore
            except Exception:
                detail = exc.response.text if exc.response is not None else None
            raise ApiClientError(detail or str(exc)) from exc
        except requests.RequestException as exc:
            raise ApiClientError(
                f"Could not reach API at {self.base_url}: {exc}"
            ) from exc


def get_api_client() -> SupportApiClient:
    return SupportApiClient()
