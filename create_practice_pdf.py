import os
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# 导入配置
# 将当前目录添加到 sys.path 以便能找到 config 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from config import settings
except ImportError:
    # 如果直接运行脚本，可能需要这样导入
    import config.settings as settings

# ===========================================

def register_font():
    """注册中文字体"""
    font_name = 'KaiTi'
    try:
        if os.path.exists(settings.FONT_PATH):
            pdfmetrics.registerFont(TTFont(font_name, settings.FONT_PATH))
            return font_name
        else:
            # 尝试备用字体 SimHei
            backup_font = r"C:\Windows\Fonts\simhei.ttf"
            if os.path.exists(backup_font):
                print(f"未找到楷体，使用黑体: {backup_font}")
                pdfmetrics.registerFont(TTFont('SimHei', backup_font))
                return 'SimHei'
            else:
                print("错误：未找到中文字体文件。请检查 config/settings.py 中的 FONT_PATH 设置。")
                return None
    except Exception as e:
        print(f"字体注册失败: {e}")
        return None

def draw_tian_grid(c, x, y, size):
    """绘制单个田字格"""
    # 保存当前状态
    c.saveState()
    
    # 1. 画外框 (实线)
    c.setLineWidth(1)
    c.setStrokeColor(settings.GRID_COLOR)
    c.rect(x, y, size, size)
    
    # 2. 画内部十字 (虚线)
    c.setLineWidth(0.3)
    c.setDash([2, 2], 0) # 虚线样式: 2点实, 2点空
    c.setStrokeColor(settings.GRID_COLOR)
    
    # 横中线
    c.line(x, y + size/2, x + size, y + size/2)
    # 竖中线
    c.line(x + size/2, y, x + size/2, y + size)
    
    # 恢复状态
    c.restoreState()

def draw_char(c, char, x, y, size, font_name, style='solid'):
    """绘制汉字"""
    c.saveState()
    
    font_size = size * 0.85 # 字体大小占格子的 85%
    c.setFont(font_name, font_size)
    
    # 计算居中位置
    # 垂直居中需要根据基线微调，楷体通常基线偏低
    # 简单估算：基线在格子底部向上 15%-20% 处
    text_y = y + (size - font_size) / 2 + font_size * 0.15 
    center_x = x + size / 2
    
    if style == 'solid':
        # 黑色实体字
        c.setFillColor(settings.TEXT_COLOR_SOLID)
        c.drawCentredString(center_x, text_y, char)
        
    elif style == 'dashed':
        # 虚线/描红字
        # 方案 A: 浅灰色填充 (最推荐，适合描红)
        c.setFillColor(settings.TEXT_COLOR_DASHED)
        c.drawCentredString(center_x, text_y, char)
        
    c.restoreState()

def draw_header(c, page_width, page_height, font_name):
    """绘制页面标题"""
    c.saveState()
    
    # 标题
    c.setFont(font_name, 24)
    c.setFillColor(colors.black)
    c.drawCentredString(page_width / 2, page_height - 20 * mm, "渤仔生字专项练习")
    
    # 姓名和日期
    c.setFont(font_name, 12)
    # 计算右边距，与田字格对齐
    total_grid_width = settings.GRID_COUNT_PER_ROW * settings.GRID_SIZE
    margin_x = (page_width - total_grid_width) / 2
    right_align_x = page_width - margin_x
    
    c.drawRightString(right_align_x, page_height - 32 * mm, "________年____月______日")
    
    c.restoreState()

def create_practice_pdf():
    # 确保输出目录存在
    if not os.path.exists(settings.OUTPUT_DIR):
        os.makedirs(settings.OUTPUT_DIR)
        print(f"创建输出目录: {settings.OUTPUT_DIR}")

    output_path = os.path.join(settings.OUTPUT_DIR, settings.OUTPUT_FILENAME)

    # 页面设置
    c = canvas.Canvas(output_path, pagesize=A4)
    c.setTitle("汉字书写练习")
    
    font_name = register_font()
    if not font_name:
        return

    page_width, page_height = A4
    
    # 计算边距以居中
    total_grid_width = settings.GRID_COUNT_PER_ROW * settings.GRID_SIZE
    margin_x = (page_width - total_grid_width) / 2
    
    # 初始 Y 坐标 (顶部留出标题空间)
    start_y = page_height - settings.HEADER_HEIGHT - settings.GRID_SIZE
    current_y = start_y
    
    # 绘制第一页标题
    draw_header(c, page_width, page_height, font_name)
    
    print(f"开始生成 PDF，共 {len(settings.CHAR_LIST)} 个字...")
    
    for index, char in enumerate(settings.CHAR_LIST):
        # 检查是否需要换页
        if current_y < settings.BOTTOM_MARGIN:
            c.showPage()
            # 新页面绘制标题
            draw_header(c, page_width, page_height, font_name)
            current_y = start_y
        
        # 绘制这一行
        # 1. 第一个字：黑色实体
        draw_tian_grid(c, margin_x, current_y, settings.GRID_SIZE)
        draw_char(c, char, margin_x, current_y, settings.GRID_SIZE, font_name, 'solid')
        
        # 2. 第2-5个字：虚线/描红 (索引 1, 2, 3, 4)
        for i in range(1, 5):
            x = margin_x + i * settings.GRID_SIZE
            draw_tian_grid(c, x, current_y, settings.GRID_SIZE)
            draw_char(c, char, x, current_y, settings.GRID_SIZE, font_name, 'dashed')
            
        # 3. 这一行后面的：空白田字格 (索引 5 到 9)
        for i in range(5, settings.GRID_COUNT_PER_ROW):
            x = margin_x + i * settings.GRID_SIZE
            draw_tian_grid(c, x, current_y, settings.GRID_SIZE)
            # 不画字
            
        # 移动到下一行
        current_y -= (settings.GRID_SIZE + settings.ROW_SPACING)
        
    c.save()
    print(f"成功生成文件: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    create_practice_pdf()
