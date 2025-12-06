import os
import hashlib
from pathlib import Path
from typing import BinaryIO, Tuple

from app.infra.settings import SETTINGS


def local_file_save(file:BinaryIO, relative_path: str, file_name: str) -> Tuple[str, int, str]:
    file_bytes: bytes = file.read()
    # 准备目录
    store_path = Path(SETTINGS.FILE_STORE_PATH)
    upload_dir = store_path / relative_path
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 计算文件哈希并保存文件
    file_size = len(file_bytes)
    # 计算 hash
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    saved_path = upload_dir / file_name

    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    # 统一返回 / 分隔路径
    file_url = str(saved_path).replace(os.sep, "/")
    return file_url, file_size, file_hash

def local_file_delete(file_url:str):
    path = Path(file_url)
    if path.exists():
        path.unlink()

