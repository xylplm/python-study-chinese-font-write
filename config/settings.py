from reportlab.lib.units import mm
from reportlab.lib import colors
import os

# ================= 配置区域 =================

# 1. 要练习的文字数组
# 你可以在这里修改要练习的汉字
CHAR_LIST = [
    "天", "地", "人", "你", "我", "他", 
    "上", "学", "校", "书", "写", "字"
]

# 2. 输出设置
OUTPUT_DIR = "output"
OUTPUT_FILENAME = "hanzi_practice.pdf"

# 3. 字体路径 (Windows 默认楷体路径)
# 如果是 Mac 或 Linux，请修改为对应的字体路径
FONT_PATH = r"C:\Windows\Fonts\simkai.ttf"

# 4. 样式设置
GRID_SIZE = 16 * mm          # 田字格大小
GRID_COUNT_PER_ROW = 10      # 每行格子数
ROW_SPACING = 4 * mm         # 行间距
GRID_COLOR = colors.red      # 田字格颜色 (通常为红色或绿色)
TEXT_COLOR_SOLID = colors.black # 实心字颜色
TEXT_COLOR_DASHED = colors.lightgrey # 虚线/描红字颜色 (浅灰色最适合描红)

# 页面布局设置
HEADER_HEIGHT = 40 * mm      # 顶部标题区域高度
BOTTOM_MARGIN = 20 * mm      # 底部留白
