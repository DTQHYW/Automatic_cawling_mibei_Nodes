#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通知模块（可选）"""

import logging
import smtplib
from email.mime.text import MIMEText
from typing import Any, Dict

import requests


class Notifier:
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger

    def send(self, title: str, message: str) -> None:
        """发送所有已启用的通知"""
        if self.config.get("email", {}).get("enabled"):
            self._send_email(title, message)
        if self.config.get("telegram", {}).get("enabled"):
            self._send_telegram(title, message)
        if self.config.get("wechat", {}).get("enabled"):
            self._send_wechat(title, message)

    def _send_email(self, title: str, message: str) -> None:
        try:
            cfg = self.config["email"]
            msg = MIMEText(message, "plain", "utf-8")
            msg["Subject"] = title
            msg["From"] = cfg["sender"]
            msg["To"] = cfg["recipient"]

            with smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"]) as server:
                server.starttls()
                server.login(cfg["username"], cfg["password"])
                server.sendmail(cfg["sender"], [cfg["recipient"]], msg.as_string())
            self.logger.info("邮件通知发送成功")
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(f"邮件通知发送失败: {exc}")

    def _send_telegram(self, title: str, message: str) -> None:
        try:
            cfg = self.config["telegram"]
            text = f"*{title}*\n\n{message}"
            url = f"https://api.telegram.org/bot{cfg['bot_token']}/sendMessage"
            payload = {
                "chat_id": cfg["chat_id"],
                "text": text,
                "parse_mode": "Markdown",
            }
            requests.post(url, json=payload, timeout=30)
            self.logger.info("Telegram 通知发送成功")
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(f"Telegram 通知发送失败: {exc}")

    def _send_wechat(self, title: str, message: str) -> None:
        try:
            cfg = self.config["wechat"]
            requests.post(
                cfg["webhook_url"],
                json={"msgtype": "text", "text": {"content": f"{title}\n{message}"}},
                timeout=30,
            )
            self.logger.info("微信通知发送成功")
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(f"微信通知发送失败: {exc}")
