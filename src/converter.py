#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""节点格式转换模块

支持生成：
  - Base64 通用订阅（base64.txt）
  - Clash YAML 订阅（clash.yaml）
"""

import base64
import json
import urllib.parse
from typing import Any, Dict, List

import yaml


class NodeConverter:
    def __init__(self, name_suffix: str = "udptoos.com"):
        self.name_suffix = name_suffix

    # ------------------------------------------------------------------ #
    # 公共辅助
    # ------------------------------------------------------------------ #

    @staticmethod
    def safe_b64encode(data: str) -> str:
        """Base64 编码"""
        return base64.b64encode(data.encode("utf-8")).decode("utf-8")

    @staticmethod
    def normalize_name(name: str, country: str = "", index: int = 1) -> str:
        """统一节点展示名称"""
        parts = [p for p in [country, name] if p]
        if not parts:
            parts = ["Node"]
        return f"{''.join(parts)} - {index}"

    # ------------------------------------------------------------------ #
    # 节点 -> URI
    # ------------------------------------------------------------------ #

    def node_to_uri(self, node: Dict[str, Any]) -> str:
        """将内部节点转换为订阅 URI"""
        protocol = node.get("protocol", "")
        if protocol == "vmess":
            return self._vmess_to_uri(node)
        if protocol == "vless":
            return self._vless_to_uri(node)
        if protocol == "ss":
            return self._ss_to_uri(node)
        if protocol == "trojan":
            return self._trojan_to_uri(node)
        return ""

    def _vmess_to_uri(self, node: Dict[str, Any]) -> str:
        cfg = {
            "v": "2",
            "ps": node.get("name", "vmess"),
            "add": node.get("address", ""),
            "port": str(node.get("port", "0")),
            "id": node.get("id", ""),
            "aid": str(node.get("aid", 0)),
            "scy": node.get("scy", "auto"),
            "net": node.get("net", "tcp"),
            "type": node.get("type", "none"),
            "host": node.get("host", ""),
            "path": node.get("path", ""),
            "tls": node.get("tls", ""),
            "sni": node.get("sni", ""),
        }
        b64 = base64.b64encode(json.dumps(cfg, ensure_ascii=False).encode("utf-8")).decode("utf-8")
        return f"vmess://{b64}"

    def _vless_to_uri(self, node: Dict[str, Any]) -> str:
        user = urllib.parse.quote(node.get("id", ""))
        host = node.get("address", "")
        port = node.get("port", 0)
        params = {
            "encryption": node.get("encryption", "none"),
            "security": node.get("security", "none"),
            "type": node.get("type", "tcp"),
        }
        if node.get("sni"):
            params["sni"] = node.get("sni")
        if node.get("host"):
            params["host"] = node.get("host")
        if node.get("path"):
            params["path"] = node.get("path")
        if node.get("flow"):
            params["flow"] = node.get("flow")
        query = urllib.parse.urlencode(params)
        name = urllib.parse.quote(node.get("name", "vless"))
        return f"vless://{user}@{host}:{port}?{query}#{name}"

    def _ss_to_uri(self, node: Dict[str, Any]) -> str:
        method_pwd = f"{node.get('method', '')}:{node.get('password', '')}"
        b64 = base64.b64encode(method_pwd.encode("utf-8")).decode("utf-8").rstrip("=")
        name = urllib.parse.quote(node.get("name", "ss"))
        return f"ss://{b64}@{node.get('address', '')}:{node.get('port', 0)}#{name}"

    def _trojan_to_uri(self, node: Dict[str, Any]) -> str:
        password = urllib.parse.quote(node.get("password", ""))
        host = node.get("address", "")
        port = node.get("port", 0)
        params = {}
        if node.get("sni"):
            params["sni"] = node.get("sni")
        if node.get("host"):
            params["host"] = node.get("host")
        query = urllib.parse.urlencode(params)
        name = urllib.parse.quote(node.get("name", "trojan"))
        if query:
            return f"trojan://{password}@{host}:{port}?{query}#{name}"
        return f"trojan://{password}@{host}:{port}#{name}"

    # ------------------------------------------------------------------ #
    # 生成 Base64 订阅
    # ------------------------------------------------------------------ #

    def to_base64(self, nodes: List[Dict[str, Any]]) -> str:
        """将节点列表转换为 Base64 订阅文本"""
        uris = []
        for node in nodes:
            uri = self.node_to_uri(node)
            if uri:
                uris.append(uri)
        combined = "\n".join(uris)
        return base64.b64encode(combined.encode("utf-8")).decode("utf-8")

    # ------------------------------------------------------------------ #
    # 生成 Clash YAML
    # ------------------------------------------------------------------ #

    def to_clash_yaml(self, nodes: List[Dict[str, Any]]) -> str:
        """将节点列表转换为 Clash YAML 配置"""
        proxies = []
        for node in nodes:
            proxy = self._node_to_clash_proxy(node)
            if proxy:
                proxies.append(proxy)

        config = {
            "mixed-port": 7890,
            "allow-lan": False,
            "mode": "rule",
            "log-level": "info",
            "external-controller": "127.0.0.1:9090",
            "dns": {
                "enabled": True,
                "nameserver": ["223.5.5.5", "119.29.29.29"],
            },
            "proxies": proxies,
            "proxy-groups": [
                {
                    "name": "🚀 节点选择",
                    "type": "select",
                    "proxies": ["🎯 全球直连", "♻️ 自动选择"] + [p["name"] for p in proxies],
                },
                {
                    "name": "♻️ 自动选择",
                    "type": "url-test",
                    "url": "http://www.gstatic.com/generate_204",
                    "interval": 300,
                    "proxies": [p["name"] for p in proxies],
                },
                {
                    "name": "🎯 全球直连",
                    "type": "select",
                    "proxies": ["DIRECT"],
                },
            ],
            "rules": [
                "DOMAIN-SUFFIX,local,DIRECT",
                "IP-CIDR,127.0.0.0/8,DIRECT",
                "IP-CIDR,172.16.0.0/12,DIRECT",
                "IP-CIDR,192.168.0.0/16,DIRECT",
                "IP-CIDR,10.0.0.0/8,DIRECT",
                "GEOIP,CN,DIRECT",
                "MATCH,🚀 节点选择",
            ],
        }
        return yaml.safe_dump(config, sort_keys=False, allow_unicode=True)

    def _node_to_clash_proxy(self, node: Dict[str, Any]) -> Dict[str, Any]:
        protocol = node.get("protocol", "")
        if protocol == "vmess":
            return {
                "name": node.get("name", "vmess"),
                "type": "vmess",
                "server": node.get("address", ""),
                "port": int(node.get("port", 0)),
                "uuid": node.get("id", ""),
                "alterId": int(node.get("aid", 0)),
                "cipher": node.get("scy", "auto"),
                "network": node.get("net", "tcp"),
                "tls": bool(node.get("tls")),
                "ws-path": node.get("path", ""),
                "ws-headers": {"Host": node.get("host", "")} if node.get("host") else {},
            }
        if protocol == "vless":
            return {
                "name": node.get("name", "vless"),
                "type": "vless",
                "server": node.get("address", ""),
                "port": int(node.get("port", 0)),
                "uuid": node.get("id", ""),
                "tls": node.get("security", "none") == "tls",
                "network": node.get("type", "tcp"),
                "servername": node.get("sni", ""),
            }
        if protocol == "ss":
            return {
                "name": node.get("name", "ss"),
                "type": "ss",
                "server": node.get("address", ""),
                "port": int(node.get("port", 0)),
                "cipher": node.get("method", ""),
                "password": node.get("password", ""),
            }
        if protocol == "trojan":
            return {
                "name": node.get("name", "trojan"),
                "type": "trojan",
                "server": node.get("address", ""),
                "port": int(node.get("port", 0)),
                "password": node.get("password", ""),
                "sni": node.get("sni", ""),
            }
        return {}
