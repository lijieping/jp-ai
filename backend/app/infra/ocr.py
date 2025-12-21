import time

import requests
import json

from app.infra.log import logger
from app.infra.settings import get_settings

def ocr_parse(image_path:str):
    settings = get_settings()
    if settings.OCR_MODE == "buyan":
        return buyan_ocr_parse(image_path)
    else:
        raise ValueError(f"非法的SETTINGS.OCR_MODE={settings.OCR_MODE}")

def buyan_ocr_parse(image_path:str):
    start = time.perf_counter_ns()  # 纳秒级起点
    url = "https://qaqbuyan.com:88/api/ocr/"
    with open(image_path, "rb") as img:
        try:
            files = {"image": (image_path, img, "application/octet-stream")}
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            resp = requests.post(url, files=files, headers=headers, timeout=30).json()
            if resp['code_code'] != 200:
                raise Exception(f"响应{resp.code}")
            texts = [e['text'] for e in resp['results']]

            logger.debug("识别结果：")
            logger.debug(texts)

            elapsed_ms = (time.perf_counter_ns() - start) / 1e6
            logger.debug(f"buyan ocr耗时 {elapsed_ms:.2f} ms")
            return texts
        except requests.exceptions.RequestException as e:
            logger.debug("请求失败：", e)
        except json.JSONDecodeError:
            logger.debug("返回不是合法 JSON，原文：", resp.text)