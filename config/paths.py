"""路径配置"""
import os

# 获取项目根目录（向上查找）
def get_project_root():
    """获取项目根目录"""
    current = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(current)

PROJECT_ROOT = get_project_root()

# 指标结果库路径（支持环境变量覆盖）
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", os.path.join(PROJECT_ROOT, "指标结果库"))

# ETF数据路径（支持环境变量覆盖）
DATA_DIR = os.environ.get("DATA_DIR", r"E:\数据库\ETF跟踪指数量价数据-日度更新\ETF跟踪指数量价数据-日度更新")

# 输出的HTML文件
OUTPUT_FILE = "每日量价跟踪报告.html"
