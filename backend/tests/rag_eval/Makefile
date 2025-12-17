# 日常使用流程
# ！！！需要灌入主项目环境变量
#！！！需要在当前目录执行

# 改动了清洗/检索/生成任意环节 →
# 本地 make eval  →
# 5 分钟后看终端：
# 三指标绿色 ↑ 放心合并
# 红色 ↓ 打开 eval/snapshot/shap.png 一眼定位是 parsing 还是 retrieval 还是 generation 短板 → 针对性优化
# push 自动触发 CI，下降即失败，强制修完才能合并 MR。

.PHONY: eval
eval:
	@echo == Step1 灌黄金数据（仅第一次） ==
	python _1_prep_gold.py
	@echo == Step2 跑分 ==
	python _2_run_eval.py
	#@echo" == Step3 生成 SHAP 图 == "
	#python 3_shap.py
	#@echo" == Step4 pytest snapshot 对比 == "
	#pytest eval/test_rag.py --snapshot-update -q
	#@echo"完成，3 指标 + SHAP 图在 eval/snapshot/"

