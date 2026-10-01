#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""节点抓取与解析模块

支持协议：vmess、vless、ss、trojan
支持输入：Base64 订阅、Clash YAML、原始 URI 文本
"""

import base64
import json
import re
import urllib.parse
from typing import Any, Dict, List, Optional

import requests
import yaml


class NodeParser:
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries

    def fetch(self, url: str) -> str:
        """拉取远程文本或本地文件，失败时重试"""
        if url.startswith("file://"):
            local_path = url[len("file://") :]
            with open(local_path, "r", encoding="utf-8") as f:
                return f.read()

        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                }
                resp = requests.get(url, headers=headers, timeout=self.timeout)
                resp.raise_for_status()
                return resp.text
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                if attempt == self.max_retries:
                    raise RuntimeError(
                        f"无法下载订阅 ({url})，已重试 {self.max_retries} 次: {last_err}"
                    ) from exc

    @staticmethod
    def safe_b64decode(data: str) -> bytes:
        """兼容性 Base64 解码，自动补 '='"""
        data = data.strip()
        missing = len(data) % 4
        if missing:
            data += "=" * (4 - missing)
        return base64.b64decode(data, validate=False)

    def parse_source(self, name: str, url: str, source_type: str) -> List[Dict[str, Any]]:
        """根据类型解析单个订阅源"""
        raw = self.fetch(url)
        if source_type == "base64":
            return self.parse_base64(raw)
        if source_type == "clash":
            return self.parse_clash_yaml(raw)
        if source_type == "raw_text":
            return self.parse_raw_text(raw)
        raise ValueError(f"不支持的订阅类型: {source_type}")

    def parse_base64(self, raw: str) -> List[Dict[str, Any]]:
        """解析 Base64 订阅文本"""
        raw = raw.strip()
        if not raw:
            return []
        try:
            decoded = self.safe_b64decode(raw).decode("utf-8", errors="ignore")
        except Exception:
            # 可能不是标准 base64，尝试按行解码
            decoded = raw

        nodes = []
        for line in decoded.splitlines():
            line = line.strip()
            if not line:
                continue
            node = self.parse_uri(line)
            if node:
                nodes.append(node)
        return nodes

    def parse_raw_text(self, raw: str) -> List[Dict[str, Any]]:
        """解析每行一个 URI 的原始文本"""
        nodes = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            node = self.parse_uri(line)
            if node:
                nodes.append(node)
        return nodes

    def parse_clash_yaml(self, raw: str) -> List[Dict[str, Any]]:
        """解析 Clash YAML 配置中的 proxies 节点"""
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise ValueError(f"Clash YAML 解析失败: {exc}") from exc

        if not data or "proxies" not in data:
            return []

        nodes = []
        for p in data.get("proxies", []) or []:
            node = self._clash_proxy_to_node(p)
            if node:
                nodes.append(node)
        return nodes

    def parse_uri(self, uri: str) -> Optional[Dict[str, Any]]:
        """解析单个节点 URI"""
        uri = uri.strip()
        if uri.startswith("vmess://"):
            return self._parse_vmess(uri)
        if uri.startswith("vless://"):
            return self._parse_vless(uri)
        if uri.startswith("ss://"):
            return self._parse_ss(uri)
        if uri.startswith("trojan://"):
            return self._parse_trojan(uri)
        return None

    # ------------------------------------------------------------------ #
    # URI 解析器
    # ------------------------------------------------------------------ #

    def _parse_vmess(self, uri: str) -> Optional[Dict[str, Any]]:
        try:
            body = uri[len("vmess://") :]
            decoded = self.safe_b64decode(body).decode("utf-8", errors="ignore")
            cfg = json.loads(decoded)
            return {
                "protocol": "vmess",
                "name": cfg.get("ps", "vmess"),
                "address": cfg.get("add", ""),
                "port": int(cfg.get("port", 0)) if cfg.get("port") else 0,
                "id": cfg.get("id", ""),
                "aid": cfg.get("aid", 0),
                "scy": cfg.get("scy", "auto"),
                "net": cfg.get("net", "tcp"),
                "type": cfg.get("type", "none"),
                "host": cfg.get("host", ""),
                "path": cfg.get("path", ""),
                "tls": cfg.get("tls", ""),
                "sni": cfg.get("sni", ""),
                "raw": cfg,
            }
        except Exception:
            return None

    def _parse_vless(self, uri: str) -> Optional[Dict[str, Any]]:
        try:
            parsed = urllib.parse.urlparse(uri)
            uuid_and = parsed.netloc.split("@", 1)
            if len(uuid_and) != 2:
                return None
            user_info, server = uuid_and
            host, port = self._split_host_port(server)
            query = urllib.parse.parse_qs(parsed.query)
            return {
                "protocol": "vless",
                "name": urllib.parse.unquote(parsed.fragment) or "vless",
                "address": host,
                "port": port,
                "id": urllib.parse.unquote(user_info),
                "flow": query.get("flow", [""])[0],
                "encryption": query.get("encryption", ["none"])[0],
                "security": query.get("security", ["none"])[0],
                "sni": query.get("sni", [""])[0],
                "host": query.get("host", [""])[0],
                "path": query.get("path", [""])[0],
                "type": query.get("type", ["tcp"])[0],
            }
        except Exception:
            return None

    def _parse_ss(self, uri: str) -> Optional[Dict[str, Any]]:
        try:
            parsed = urllib.parse.urlparse(uri)
            user_info = parsed.netloc.split("@", 1)[0]
            try:
                method_pwd = self.safe_b64decode(user_info).decode("utf-8", errors="ignore")
            except Exception:
                method_pwd = user_info
            parts = method_pwd.split(":", 1)
            method = parts[0] if parts else ""
            password = parts[1] if len(parts) > 1 else ""
            host, port = self._split_host_port(parsed.netloc.split("@", 1)[1])
            return {
                "protocol": "ss",
                "name": urllib.parse.unquote(parsed.fragment) or "ss",
                "address": host,
                "port": port,
                "method": method,
                "password": password,
            }
        except Exception:
            return None

    def _parse_trojan(self, uri: str) -> Optional[Dict[str, Any]]:
        try:
            parsed = urllib.parse.urlparse(uri)
            password_and = parsed.netloc.rsplit("@", 1)
            if len(password_and) != 2:
                return None
            password, server = password_and
            host, port = self._split_host_port(server)
            query = urllib.parse.parse_qs(parsed.query)
            return {
                "protocol": "trojan",
                "name": urllib.parse.unquote(parsed.fragment) or "trojan",
                "address": host,
                "port": port,
                "password": urllib.parse.unquote(password),
                "sni": query.get("sni", [""])[0],
                "host": query.get("host", [""])[0],
            }
        except Exception:
            return None

    @staticmethod
    def _split_host_port(server: str) -> tuple:
        """拆分 host:port，兼容 IPv6"""
        if server.startswith("["):
            match = re.match(r"\[(?P<host>.+)\]:(?P<port>\d+)", server)
            if match:
                return match.group("host"), int(match.group("port"))
        if ":" in server:
            host, port = server.rsplit(":", 1)
            return host, int(port)
        return server, 0

    # ------------------------------------------------------------------ #
    # Clash proxy -> 内部节点
    # ------------------------------------------------------------------ #

    def _clash_proxy_to_node(self, p: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        protocol = p.get("type", "").lower()
        name = p.get("name", protocol)
        if protocol == "vmess":
            return {
                "protocol": "vmess",
                "name": name,
                "address": p.get("server", ""),
                "port": int(p.get("port", 0)),
                "id": p.get("uuid", ""),
                "aid": p.get("alterId", 0),
                "scy": p.get("cipher", "auto"),
                "net": p.get("network", "tcp"),
                "type": p.get("network", "tcp"),
                "host": p.get("ws-headers", {}).get("Host", ""),
                "path": p.get("ws-path", ""),
                "tls": "tls" if p.get("tls") else "",
                "sni": p.get("sni", ""),
            }
        if protocol == "ss":
            return {
                "protocol": "ss",
                "name": name,
                "address": p.get("server", ""),
                "port": int(p.get("port", 0)),
                "method": p.get("cipher", ""),
                "password": p.get("password", ""),
            }
        if protocol == "trojan":
            return {
                "protocol": "trojan",
                "name": name,
                "address": p.get("server", ""),
                "port": int(p.get("port", 0)),
                "password": p.get("password", ""),
                "sni": p.get("sni", ""),
            }
        if protocol == "vless":
            return {
                "protocol": "vless",
                "name": name,
                "address": p.get("server", ""),
                "port": int(p.get("port", 0)),
                "id": p.get("uuid", ""),
                "flow": p.get("flow", ""),
                "security": p.get("tls", ""),
                "sni": p.get("sni", ""),
            }
        return None
