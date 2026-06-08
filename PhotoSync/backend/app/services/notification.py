import httpx, smtplib
from email.mime.text import MIMEText
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import NotificationConfig

class NotificationService:
    def __init__(self, db: AsyncSession): self.db = db

    async def send_all(self, title: str, message: str, level: str = "info"):
        r = await self.db.execute(select(NotificationConfig).where(NotificationConfig.enabled == True))
        for cfg in r.scalars().all():
            try: await self._send(cfg.type, cfg.config, title, message, level)
            except Exception as e: print(f"[通知] {cfg.type} 发送失败: {e}")

    async def _send(self, t: str, c: dict, title: str, msg: str, level: str):
        if t == "telegram": await self._tg(c, title, msg)
        elif t == "dingtalk": await self._ding(c, title, msg)
        elif t == "wechat": await self._wx(c, title, msg)
        elif t == "email": await self._mail(c, title, msg)
        elif t == "webhook": await self._hook(c, title, msg, level)

    async def _tg(self, c, title, msg):
        bt, ci = c.get("bot_token"), c.get("chat_id")
        if not bt or not ci: return
        async with httpx.AsyncClient() as cl:
            await cl.post(f"https://api.telegram.org/bot{bt}/sendMessage",
                          json={"chat_id": ci, "text": f"*{title}*\n{msg}", "parse_mode": "Markdown"}, timeout=10)

    async def _ding(self, c, title, msg):
        url = c.get("webhook_url")
        if not url: return
        async with httpx.AsyncClient() as cl:
            await cl.post(url, json={"msgtype": "markdown", "markdown": {"title": title, "text": f"## {title}\n{msg}"}}, timeout=10)

    async def _wx(self, c, title, msg):
        url = c.get("webhook_url")
        if not url: return
        async with httpx.AsyncClient() as cl:
            await cl.post(url, json={"msgtype": "markdown", "markdown": {"content": f"## {title}\n{msg}"}}, timeout=10)

    async def _mail(self, c, title, msg):
        h, p, u, pw, to = c.get("smtp_host"), c.get("smtp_port", 587), c.get("username"), c.get("password"), c.get("to_address")
        if not all([h, u, pw, to]): return
        m = MIMEText(msg, "plain", "utf-8"); m["Subject"]=title; m["From"]=u; m["To"]=to
        with smtplib.SMTP(h, p) as s: s.starttls(); s.login(u, pw); s.send_message(m)

    async def _hook(self, c, title, msg, level):
        url = c.get("url")
        if not url: return
        async with httpx.AsyncClient() as cl:
            await cl.post(url, json={"title": title, "message": msg, "level": level}, timeout=10)
