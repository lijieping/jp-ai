import requests
import json

from app.infra.ocr import buyan_ocr_parse, easy_ocr_parse

"""
api文档，卟言大神自研ocr的api， 准确率比easyocr要高
https://qaqbuyan.com:88/api/
"""
# 接口地址
url = "https://qaqbuyan.com:88/api/ocr/"

# 待识别的图片路径
image_path = "E:\\dev_env_repo\\file\\kb\\3\\聊天记录.png"

print(buyan_ocr_parse(image_path))
print(easy_ocr_parse(image_path))