#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""守护进程模式入口

用于本地长期运行，定时执行收割任务。
"""

import argparse
import os
import sys
import time

import yaml

from main import run_harvest
from src.utils import setup_logger


CONFIG_FILE = "config.yaml"


def load_interval(config_path: str) -> int:
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return int(config.get("settings", {}).get("check_interval", 3600))
    except Exception:  # noqa: BLE001
        return 3600


def main() -> int:
    cli = argparse.ArgumentParser(description="守护进程模式")
    cli.add_argument("-c", "--config", default=CONFIG_FILE, help="配置文件路径")
    cli.add_argument("--once", action="store_true", help="只运行一次")
    args = cli.parse_args()

    logger = setup_logger("logs")
    interval = load_interval(args.config)

    if args.once:
        logger.info("单次模式运行")
        try:
            run_harvest(args.config)
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"单次执行失败: {exc}")
        return 0

    logger.info(f"守护进程启动，检查间隔: {interval} 秒")
    while True:
        try:
            run_harvest(args.config)
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"收割任务异常: {exc}")
        logger.info(f"下次收割时间: {interval} 秒后")
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
