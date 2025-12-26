"""子 Agent 包，自动导入所有子模块以触发元类注册"""
import importlib
import pkgutil

# 自动导入所有子模块，触发元类自动注册
_sub_agent_package = importlib.import_module(__name__)
for _importer, _modname, _ispkg in pkgutil.iter_modules(_sub_agent_package.__path__):
    if not _ispkg and not _modname.startswith('_'):
        try:
            importlib.import_module(f'{__name__}.{_modname}')
        except Exception as e:
            # 静默失败，避免影响其他模块
            pass

