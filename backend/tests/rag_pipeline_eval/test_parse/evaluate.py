"""
FileParseHandler 评估脚本
!!!环境变量： ocr模式  SETTINGS.OCR_MODE == "buyan"

针对 RAG Pipeline 中 FileParseHandler 的离线评估
评估指标：
1. 文本提取率 (≥ 95%) - OCR 字数 / 人工标注总字数
2. OCR 字符错误率 (CER ≤ 3%) - 误识字符 / 总字符
3. 表格结构还原率 (≥ 90%) - 成功解析成 HTML/CSV 的表格数 / 视觉可见表格数
"""

import os
import json
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor

import Levenshtein

from tests.test_utils import patch_settings

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    file_name: str
    file_type: str
    extracted_text: str
    gold_text: str
    text_extraction_rate: float
    character_error_rate: float
    table_count: int
    table_success_count: int
    table_fidelity_rate: float
    processing_time: float
    success: bool
    error_message: Optional[str] = None


def calculate_text_metrics(extracted_text: str, gold_text: str):
    """计算文本指标"""
    if not gold_text.strip():
        return 0.0, 0.0

    # 文本提取率
    extracted_chars = len(extracted_text)
    gold_chars = len(gold_text)
    text_extraction_rate = (extracted_chars / gold_chars) * 100

    # 字符错误率 (CER)
    cer = Levenshtein.distance(gold_text, extracted_text) / len(gold_text)
    return text_extraction_rate, cer


def calculate_table_metrics(extracted_text: str, table_info: Dict):
    """计算表格指标"""
    visual_table_count = table_info.get("table_count", 0)

    if visual_table_count == 0:
        return 0, 0, 100.0

    # 检测表格结构
    success_count = 0
    if "<table" in extracted_text.lower() or "|---" in extracted_text:
        success_count = visual_table_count

    fidelity_rate = (success_count / visual_table_count) * 100
    return success_count, visual_table_count, fidelity_rate


def get_gold_text(file_name: str) -> str:
    """获取金标准文本"""
    gold_file = Path("gold_data") / f"{Path(file_name).stem}.txt"
    if gold_file.exists():
        with open(gold_file, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def get_table_info(file_name: str) -> Dict:
    """获取表格信息"""
    table_info_file = Path("gold_data") / f"{Path(file_name).stem}_tables.json"
    if table_info_file.exists():
        with open(table_info_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"table_count": 0, "tables": []}


def process_single_file(file_path: Path, handler) -> EvaluationResult:
    """处理单个文件"""
    with patch_settings():
        from app.service.rag_pipeline_service import Context
        start_time = os.times().elapsed

        try:
            # 读取金标准数据
            gold_text = get_gold_text(file_path.name)
            table_info = get_table_info(file_path.name)

            # 使用 FileParseHandler 处理文件
            ctx = Context(file_url=str(file_path), collection_name="temp")
            handler.process(ctx)

            extracted_text = "".join([doc.page_content for doc in ctx.pages])

            # 计算指标
            text_extraction_rate, character_error_rate = calculate_text_metrics(extracted_text, gold_text)
            table_success_count, table_count, table_fidelity_rate = calculate_table_metrics(extracted_text, table_info)

            processing_time = os.times().elapsed - start_time

            logger.info(f"文件 {file_path.name} 处理成功 - 提取率: {text_extraction_rate:.2f}%, "
                       f"CER: {character_error_rate:.2f}%, 表格保真度: {table_fidelity_rate:.2f}%")

            return EvaluationResult(
                file_name=file_path.name,
                file_type=file_path.suffix,
                extracted_text=extracted_text,
                gold_text=gold_text,
                text_extraction_rate=text_extraction_rate,
                character_error_rate=character_error_rate,
                table_count=table_count,
                table_success_count=table_success_count,
                table_fidelity_rate=table_fidelity_rate,
                processing_time=processing_time,
                success=True
            )

        except Exception as e:
            processing_time = os.times().elapsed - start_time
            logger.error(f"文件 {file_path.name} 处理失败: {str(e)}")

            return EvaluationResult(
                file_name=file_path.name,
                file_type=file_path.suffix,
                extracted_text="",
                gold_text="",
                text_extraction_rate=0.0,
                character_error_rate=0.0,
                table_count=0,
                table_success_count=0,
                table_fidelity_rate=0.0,
                processing_time=processing_time,
                success=False,
                error_message=str(e)
            )


def evaluate_file_parse():
    """执行评估"""
    # Patch settings using the utility function
    with patch_settings():
        from app.service.rag_pipeline_service import FileParseHandler
        # 初始化
        handler = FileParseHandler()

        # 获取测试文件
        test_data_dir = Path("test_data")
        if not test_data_dir.exists():
            print("测试数据目录不存在: test_data")
            return

        # 收集所有支持的文件
        support_exts = FileParseHandler._support_exts
        test_files = []
        for file_type_info in support_exts.values():
            for ext in file_type_info["exts"]:
                test_files.extend(test_data_dir.glob(f"*{ext}"))

        if not test_files:
            print("未找到任何测试文件")
            return

        print(f"找到 {len(test_files)} 个测试文件")

        # 并行处理
        results = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_single_file, file_path, handler) for file_path in test_files]

            for future in futures:
                results.append(future.result())

        # 统计结果
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        if successful_results:
            avg_text_extraction_rate = sum(r.text_extraction_rate for r in successful_results) / len(successful_results)
            avg_character_error_rate = sum(r.character_error_rate for r in successful_results) / len(successful_results)
            avg_table_fidelity_rate = sum(r.table_fidelity_rate for r in successful_results) / len(successful_results)
        else:
            avg_text_extraction_rate = 0.0
            avg_character_error_rate = 0.0
            avg_table_fidelity_rate = 0.0

        # 打印结果
        print("\n" + "=" * 60)
        print("FileParseHandler 评估结果")
        print("=" * 60)
        print(f"总文件数: {len(test_files)}")
        print(f"成功处理: {len(successful_results)}")
        print(f"处理失败: {len(failed_results)}")
        print()
        print("评估指标:")
        print(f"- 平均文本提取率: {avg_text_extraction_rate:.2f}% (目标 ≥ 95%)")
        print(f"- 平均字符错误率: {avg_character_error_rate:.2f}% (目标 ≤ 3%)")
        print(f"- 平均表格保真度: {avg_table_fidelity_rate:.2f}% (目标 ≥ 90%)")
        print()

        # 检查达标情况
        text_extraction达标 = avg_text_extraction_rate >= 95.0
        character_error_rate达标 = avg_character_error_rate <= 3.0
        table_fidelity_rate达标 = avg_table_fidelity_rate >= 90.0

        print("达标情况:")
        print(f"- 文本提取率: {'✓' if text_extraction达标 else '✗'}")
        print(f"- 字符错误率: {'✓' if character_error_rate达标 else '✗'}")
        print(f"- 表格保真度: {'✓' if table_fidelity_rate达标 else '✗'}")
        print()

        # 详细结果
        print("各文件详细结果:")
        for result in results:
            status = "✓ 成功" if result.success else "✗ 失败"
            print(f"- {result.file_name} ({result.file_type}): {status}")
            if result.success:
                print(f"  提取率: {result.text_extraction_rate:.2f}%, "
                      f"CER: {result.character_error_rate:.2f}%, "
                      f"表格保真度: {result.table_fidelity_rate:.2f}%")
            else:
                print(f"  错误: {result.error_message}")
            print()

        # 保存详细结果
        detailed_results_file = Path("detailed_results.json")
        with open(detailed_results_file, 'w', encoding='utf-8') as f:
            json.dump([result.__dict__ for result in results], f, ensure_ascii=False, indent=2)

        print(f"评估结果已保存到: {str(detailed_results_file)}")


if __name__ == "__main__":
    evaluate_file_parse()