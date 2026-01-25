from reportlab.lib.units import mm
from reportlab.lib import colors
import os

# ================= 配置区域 =================

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. 要练习的文字
# 在这里输入连续的汉字字符串，程序会自动拆分
INPUT_TEXT = "耳手九五九午去了可东西竹马牙用鸟是女开关先"

# 自动转换为列表 (过滤掉空格和换行)
CHAR_LIST = [c for c in INPUT_TEXT if c.strip()]

# 2. 输出设置
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_FILENAME = "hanzi_practice.pdf"

# 3. 字体路径 (Windows 默认楷体路径)
# 如果是 Mac 或 Linux，请修改为对应的字体路径
FONT_PATH = r"C:\Windows\Fonts\simkai.ttf"

# 4. 笔顺设置
SHOW_STROKE_ORDER = True     # 是否显示笔顺
STROKE_DATA_PATH = os.path.join(BASE_DIR, 'data', 'graphics.txt') # 笔顺数据文件路径
PROXY_URL = "socks5://10.11.11.3:7895" # 下载笔顺数据时的代理，如果不需要请设为 None

# 5. 样式设置
GRID_SIZE = 13 * mm          # 田字格大小
GRID_COUNT_PER_ROW = 12      # 每行格子数
ROW_SPACING = 4 * mm         # 行间距
GRID_COLOR = colors.red      # 田字格颜色 (通常为红色或绿色)
TEXT_COLOR_SOLID = colors.black # 实心字颜色
TEXT_COLOR_DASHED = colors.Color(0.7, 0.7, 0.7) # 虚线/描红字颜色 (比 lightgrey 深一点)
TRACE_COUNT = 6             # 描红字数 (不包含第一个范例字)。如果想整行描红，可以设置一个很大的数，如 100

# 6. 页面内容设置
# 日期显示: 
#   None 或 "" -> 显示下划线 "________年____月______日"
#   "today"    -> 显示当天日期
#   其他字符串  -> 直接显示该字符串
DATE_TEXT = "today"

# 页面布局设置
HEADER_HEIGHT = 26 * mm      # 顶部标题区域高度
BOTTOM_MARGIN = 16 * mm      # 底部留白
STROKE_ORDER_HEIGHT = 5 * mm # 笔顺行高度

# 笔顺设置
SHOW_STROKE_ORDER = True
STROKE_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'graphics.txt')


