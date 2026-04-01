from datetime import datetime

import httpx

from app.core.config import settings


class GraphClient:
    def __init__(self):
        self.base = "https://graph.microsoft.com/v1.0"

    async def _get_token(self) -> str:
        url = f"https://login.microsoftonline.com/{settings.graph_tenant_id}/oauth2/v2.0/token"
        data = {
            "client_id": settings.graph_client_id,
            "client_secret": settings.graph_client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, data=data)
            resp.raise_for_status()
            return resp.json()["access_token"]

    async def send_mail(self, to_email: str, subject: str, html_body: str) -> dict:
        token = await self._get_token()
        endpoint = f"{self.base}/users/{settings.graph_mailbox_user}/sendMail"
        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": html_body},
                "toRecipients": [{"emailAddress": {"address": to_email}}],
            },
            "saveToSentItems": True,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(endpoint, headers={"Authorization": f"Bearer {token}"}, json=payload)
            resp.raise_for_status()
        return {"delivery_status": "sent", "sent_at": datetime.utcnow().isoformat()}

    async def fetch_inbound(self, top: int = 20) -> list[dict]:
        token = await self._get_token()
        endpoint = f"{self.base}/users/{settings.graph_mailbox_user}/mailFolders/inbox/messages"
        params = {"$top": top, "$orderby": "receivedDateTime desc"}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(endpoint, headers={"Authorization": f"Bearer {token}"}, params=params)
            resp.raise_for_status()
            return resp.json().get("value", [])
