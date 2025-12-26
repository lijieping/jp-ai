from pathlib import Path


def make_eval():
    """
    Python 版 `make eval` 流程，可以管理环境比拿来那个
    """
    print(" Python 版 make eval 开始")

    # 1) 灌库（等价于 make 的 gold-index 步骤）

    print("Python 版 make eval 完成")

if __name__ == "__main__":
    print(Path.cwd())
    # 1.初始化所有配置和环境变量
    from app.infra.settings import init_settings

    init_settings()

    # 2.初始化日志
    from app.infra import init_logger

    init_logger()

    make_eval()