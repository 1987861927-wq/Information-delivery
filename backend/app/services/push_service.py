class PushService:
    """APNs 推送服务骨架。"""

    async def send_daily_briefing(self, device_token: str, title: str, body: str) -> None:
        # TODO: 接入 APNs token-based authentication。
        _ = (device_token, title, body)


push_service = PushService()
