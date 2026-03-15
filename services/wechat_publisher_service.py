from __future__ import annotations

from services.wechat_mp_service import WechatMPService


class WechatPublisherService(WechatMPService):
    """Backward-compatible alias of WechatMPService."""


__all__ = ["WechatPublisherService"]
