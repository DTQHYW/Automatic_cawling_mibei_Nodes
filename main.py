#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""米贝节点全自动收割机主程序"""

import argparse
import os
import sys
from typing import Any, Dict, List

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.converter import NodeConverter
from src.notifier import Notifier
from src.parser import NodeParser
from src.utils import now_str, setup_logger


CONFIG_FILE = "config.yaml"


def load_config(path: str = CONFIG_FILE) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def deduplicate_nodes(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """基于协议+地址+端口+凭证去重"""
    seen = set()
    unique = []
    for node in nodes:
        key = (
            node.get("protocol", ""),
            node.get("address", "").lower(),
            str(node.get("port", 0)),
            node.get("id", node.get("password", "")).lower(),
        )
        if key not in seen:
            seen.add(key)
            unique.append(node)
    return unique


def rename_nodes(nodes: List[Dict[str, Any]], suffix: str) -> List[Dict[str, Any]]:
    """统一节点名称"""
    country_counter: Dict[str, int] = {}
    for node in nodes:
        country = ""
        name = node.get("name", "")
        # 尝试从现有名称中提取两位国家代码
        if len(name) >= 2 and name[:2].isalpha():
            country = name[:2].upper()
        if not country:
            country = "UN"

        country_counter[country] = country_counter.get(country, 0) + 1
        node["name"] = f"{country} - {country}{country_counter[country]:02d} - {suffix}"
    return nodes


def run_harvest(config_path: str = CONFIG_FILE) -> Dict[str, Any]:
    """执行一次节点收割"""
    config = load_config(config_path)
    settings = config.get("settings", {})
    output_cfg = config.get("output", {})

    logs_dir = settings.get("logs_dir", "logs")
    logger = setup_logger(logs_dir)

    logger.info("开始执行米贝节点收割任务")

    parser = NodeParser(
        timeout=settings.get("timeout", 30),
        max_retries=settings.get("max_retries", 3),
    )
    converter = NodeConverter(name_suffix=config.get("filter", {}).get("name_suffix", "udptoos.com"))
    notifier = Notifier(config.get("notification", {}), logger)

    all_nodes: List[Dict[str, Any]] = []

    # 遍历所有启用的订阅源
    for source in config.get("sources", []):
        if not source.get("enabled", False):
            continue
        name = source.get("name", "未知")
        url = source.get("url", "")
        source_type = source.get("type", "base64")
        try:
            logger.info(f"正在抓取订阅源: {name} ({url})")
            nodes = parser.parse_source(name, url, source_type)
            logger.info(f"{name} 解析到 {len(nodes)} 个节点")
            all_nodes.extend(nodes)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"{name} 抓取失败: {exc}")

    # 去重
    if config.get("filter", {}).get("deduplicate", True):
        all_nodes = deduplicate_nodes(all_nodes)
        logger.info(f"去重后剩余 {len(all_nodes)} 个节点")

    # 重命名
    all_nodes = rename_nodes(all_nodes, converter.name_suffix)

    # 输出
    os.makedirs(settings.get("output_dir", "subscriptions"), exist_ok=True)

    base64_path = output_cfg.get("base64", "subscriptions/base64.txt")
    clash_path = output_cfg.get("clash", "subscriptions/clash.yaml")

    base64_content = converter.to_base64(all_nodes)
    with open(base64_path, "w", encoding="utf-8") as f:
        f.write(base64_content)
    logger.info(f"已生成 Base64 订阅: {base64_path} ({len(all_nodes)} 个节点)")

    clash_content = converter.to_clash_yaml(all_nodes)
    with open(clash_path, "w", encoding="utf-8") as f:
        f.write(clash_content)
    logger.info(f"已生成 Clash YAML 订阅: {clash_path}")

    # 通知
    title = "米贝节点收割完成"
    message = f"时间: {now_str()}\n成功收割节点: {len(all_nodes)} 个\n文件: {base64_path}, {clash_path}"
    notifier.send(title, message)

    return {
        "status": "success",
        "node_count": len(all_nodes),
        "base64_path": base64_path,
        "clash_path": clash_path,
    }


def main() -> int:
    cli = argparse.ArgumentParser(description="米贝节点全自动收割机")
    cli.add_argument("-c", "--config", default=CONFIG_FILE, help="配置文件路径")
    args = cli.parse_args()

    try:
        result = run_harvest(args.config)
        print(f"收割完成: {result}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"执行失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
