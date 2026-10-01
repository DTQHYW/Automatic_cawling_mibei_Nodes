#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用工具函数"""

import logging
import os
from datetime import datetime


def setup_logger(logs_dir: str = "logs") -> logging.Logger:
    """配置并返回日志记录器"""
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, "mibei_harvester.log")

    logger = logging.getLogger("mibei_harvester")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 文件日志
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # 控制台日志
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def now_str() -> str:
    """返回当前时间字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
