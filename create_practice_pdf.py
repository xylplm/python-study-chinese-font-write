import os
import sys
import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from utils.stroke_manager import StrokeManager

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
    c.drawCentredString(page_width / 2, page_height - 18 * mm, "渤仔生字专项练习")
    
    # 姓名和日期
    c.setFont(font_name, 12)
    # 计算右边距，与田字格对齐
    total_grid_width = settings.GRID_COUNT_PER_ROW * settings.GRID_SIZE
    margin_x = (page_width - total_grid_width) / 2
    right_align_x = page_width - margin_x
    
    # 获取日期文本
    date_text = "________年____月______日"
    if hasattr(settings, 'DATE_TEXT'):
        if settings.DATE_TEXT == 'today':
            now = datetime.datetime.now()
            date_text = now.strftime("%Y年%m月%d日")
        elif settings.DATE_TEXT:
            date_text = settings.DATE_TEXT

    c.drawRightString(right_align_x, page_height - 26 * mm, date_text)
    
    c.restoreState()

def draw_page_number(c, page_num, page_width):
    """绘制页码"""
    c.saveState()
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawCentredString(page_width / 2, 10 * mm, f"- {page_num} -")
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
    
    # 页码计数
    page_num = 1
    
    # 初始化笔顺管理器
    stroke_manager = None
    if settings.SHOW_STROKE_ORDER:
        stroke_manager = StrokeManager()

    print(f"开始生成 PDF，共 {len(settings.CHAR_LIST)} 个字...")
    
    # 调整初始 Y 坐标，如果第一行有笔顺，需要预留空间
    # 但为了简单，我们在循环里处理 Y 的移动
    # 只是要注意第一页的 start_y 是否足够高？
    # 原始 start_y = page_height - HEADER - GRID_SIZE
    # 这意味着第一行格子的顶部是 page_height - HEADER
    # 如果有笔顺，笔顺应该在格子上面。
    # 所以我们需要把 start_y 下移？或者把笔顺画在 start_y 上面？
    # 如果画在上面，会和 Header 重叠。
    # 所以我们需要下移 start_y。
    
    if settings.SHOW_STROKE_ORDER:
        # 为第一行的笔顺留出空间
        start_y -= (settings.STROKE_ORDER_HEIGHT + settings.ROW_SPACING/2)
        current_y = start_y

    for index, char in enumerate(settings.CHAR_LIST):
        # 检查是否需要换页
        # 预估需要的空间：(笔顺行 + 间距) + (田字格行 + 间距)
        # 注意：current_y 已经是当前行的底部（如果是笔顺行，就是笔顺行的底部？不对，current_y 应该是格子的底部）
        
        # 让我们统一逻辑：
        # 每次循环，先检查空间。
        # 需要的空间 = 格子高度 + (笔顺高度 if enabled) + 间距
        
        needed_space = settings.GRID_SIZE + settings.ROW_SPACING
        if settings.SHOW_STROKE_ORDER:
            needed_space += settings.STROKE_ORDER_HEIGHT + settings.ROW_SPACING/2
            
        if current_y < settings.BOTTOM_MARGIN:
            # 绘制当前页页码
            draw_page_number(c, page_num, page_width)
            
            c.showPage()
            page_num += 1
            
            # 新页面不再绘制标题，使用较小的顶部边距
            # 假设顶部边距与底部边距相同
            top_margin = settings.BOTTOM_MARGIN
            
            # 重置 Y
            current_y = page_height - top_margin - settings.GRID_SIZE
            if settings.SHOW_STROKE_ORDER:
                current_y -= (settings.STROKE_ORDER_HEIGHT + settings.ROW_SPACING/2)
        
        # 1. 绘制笔顺 (如果开启)
        if settings.SHOW_STROKE_ORDER and stroke_manager:
            # 笔顺画在格子上方
            # 格子顶部 = current_y + GRID_SIZE
            # 笔顺底部 = 格子顶部 + ROW_SPACING/2
            stroke_y = current_y + settings.GRID_SIZE + settings.ROW_SPACING/4
            # 绘制
            stroke_manager.draw_stroke_order(c, char, margin_x, stroke_y, settings.STROKE_ORDER_HEIGHT)

        # 2. 绘制田字格行
        # 第一个字：黑色实体
        draw_tian_grid(c, margin_x, current_y, settings.GRID_SIZE)
        draw_char(c, char, margin_x, current_y, settings.GRID_SIZE, font_name, 'solid')
        
        # 描红字 (根据配置)
        trace_count = getattr(settings, 'TRACE_COUNT', 4) # 默认4个
        start_trace_idx = 1
        # 计算结束索引，确保不超过每行总格子数
        end_trace_idx = min(start_trace_idx + trace_count, settings.GRID_COUNT_PER_ROW)
        
        for i in range(start_trace_idx, end_trace_idx):
            x = margin_x + i * settings.GRID_SIZE
            draw_tian_grid(c, x, current_y, settings.GRID_SIZE)
            draw_char(c, char, x, current_y, settings.GRID_SIZE, font_name, 'dashed')
            
        # 后面的：空白田字格
        for i in range(end_trace_idx, settings.GRID_COUNT_PER_ROW):
            x = margin_x + i * settings.GRID_SIZE
            draw_tian_grid(c, x, current_y, settings.GRID_SIZE)
            
        # 移动到下一行
        # 下移量 = 格子高度 + 间距 + (笔顺高度 + 间距 if enabled)
        step = settings.GRID_SIZE + settings.ROW_SPACING
        if settings.SHOW_STROKE_ORDER:
            step += settings.STROKE_ORDER_HEIGHT + settings.ROW_SPACING/2
            
        current_y -= step
        
    # 最后一页页码
    draw_page_number(c, page_num, page_width)
    
    c.save()
    print(f"成功生成文件: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    create_practice_pdf()
