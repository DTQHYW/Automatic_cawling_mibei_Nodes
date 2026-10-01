#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""离线测试脚本：不依赖网络，验证转换与输出逻辑"""

import os

from src.converter import NodeConverter
from src.utils import setup_logger


def main():
    logger = setup_logger("logs")
    logger.info("开始离线测试")

    sample_nodes = [
        {
            "protocol": "vmess",
            "name": "HK-01",
            "address": "192.0.2.1",
            "port": 443,
            "id": "uuid-uuid-uuid-uuid",
            "aid": 0,
            "scy": "auto",
            "net": "ws",
            "type": "none",
            "host": "example.com",
            "path": "/path",
            "tls": "tls",
            "sni": "example.com",
        },
        {
            "protocol": "ss",
            "name": "US-01",
            "address": "192.0.2.2",
            "port": 8388,
            "method": "aes-256-gcm",
            "password": "password123",
        },
        {
            "protocol": "trojan",
            "name": "JP-01",
            "address": "192.0.2.3",
            "port": 443,
            "password": "trojan-password",
            "sni": "trojan.example.com",
        },
    ]

    converter = NodeConverter(name_suffix="test.local")

    os.makedirs("subscriptions", exist_ok=True)
    base64_path = "subscriptions/base64.txt"
    clash_path = "subscriptions/clash.yaml"

    with open(base64_path, "w", encoding="utf-8") as f:
        f.write(converter.to_base64(sample_nodes))
    logger.info(f"已生成 {base64_path}")

    with open(clash_path, "w", encoding="utf-8") as f:
        f.write(converter.to_clash_yaml(sample_nodes))
    logger.info(f"已生成 {clash_path}")

    logger.info("离线测试通过")


if __name__ == "__main__":
    main()
