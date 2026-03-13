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

def draw_pinyin_grid(c, x, y, width, height):
    """绘制拼音格子（用于手写拼音）"""
    c.saveState()
    
    # 设置线条样式
    c.setLineWidth(0.5)
    c.setStrokeColor(settings.PINYIN_GRID_COLOR)  # 使用配置的拼音格颜色
    
    # 画外框
    c.rect(x, y, width, height)
    
    # 画两条水平参考线（分三个区域，用于声调标记）
    line_height = height / 3
    c.setLineWidth(0.2)
    for i in range(1, 3):
        line_y = y + i * line_height
        c.line(x, line_y, x + width, line_y)
    
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
    
    # 副标题和日期
    c.setFont(font_name, 12)
    # 计算右边距，与田字格对齐
    total_grid_width = settings.GRID_COUNT_PER_ROW * settings.GRID_SIZE
    margin_x = (page_width - total_grid_width) / 2
    right_align_x = page_width - margin_x
    left_align_x = margin_x
    subtitle_y = page_height - 26 * mm
    
    # 显示副标题（左对齐）
    if hasattr(settings, 'SUBTITLE') and settings.SUBTITLE:
        c.drawString(left_align_x, subtitle_y, settings.SUBTITLE)
    
    # 获取日期文本
    date_text = "________年____月______日"
    if hasattr(settings, 'DATE_TEXT'):
        if settings.DATE_TEXT == 'today':
            now = datetime.datetime.now()
            date_text = now.strftime("%Y年%m月%d日")
        elif settings.DATE_TEXT:
            date_text = settings.DATE_TEXT

    c.drawRightString(right_align_x, subtitle_y, date_text)
    
    c.restoreState()

def draw_page_number(c, page_num, page_width, subtitle="", font_name="Helvetica"):
    """绘制页码（格式：副标题 - 页码）"""
    c.saveState()
    # 如果副标题包含中文，使用中文字体；否则使用 Helvetica
    if subtitle and any('\u4e00' <= char <= '\u9fff' for char in subtitle):
        c.setFont(font_name, 10)  # 使用可支持中文的字体
    else:
        c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    
    # 构建页码文本
    if subtitle:
        page_text = f"{subtitle}  -  {page_num}"
    else:
        page_text = f"- {page_num}"
    
    c.drawCentredString(page_width / 2, 10 * mm, page_text)
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
    # 需要为笔顺、拼音格、间距预留足够空间
    start_y = page_height - settings.HEADER_HEIGHT
    if settings.SHOW_STROKE_ORDER:
        start_y -= (settings.STROKE_ORDER_HEIGHT + settings.ROW_SPACING)
    start_y -= (settings.PINYIN_GRID_HEIGHT + settings.PINYIN_SPACING + settings.GRID_SIZE)
    current_y = start_y
    
    # 绘制第一页标题
    draw_header(c, page_width, page_height, font_name)
    
    # 页码计数
    page_num = 1
    
    # 初始化笔顺管理器
    stroke_manager = None
    if settings.SHOW_STROKE_ORDER:
        stroke_manager = StrokeManager()

    # 初始化子标签（用于页码显示）
    subtitle_text = getattr(settings, 'SUBTITLE', '')

    for index, char in enumerate(settings.CHAR_LIST):
        # 检查是否需要换页
        # 预估需要的空间：(笔顺行 + 间距) + (拼音格 + 间距 + 田字格 + 间距)
        # 注意：拼音格和田字格之间有 PINYIN_SPACING 间距
        
        needed_space = settings.GRID_SIZE + settings.PINYIN_GRID_HEIGHT + settings.PINYIN_SPACING + settings.ROW_SPACING
        if settings.SHOW_STROKE_ORDER:
            needed_space += settings.STROKE_ORDER_HEIGHT + settings.ROW_SPACING
            
        if current_y < settings.BOTTOM_MARGIN:
            # 绘制当前页页码
            draw_page_number(c, page_num, page_width, subtitle_text, font_name)
            
            c.showPage()
            page_num += 1
            
            # 新页面不再绘制标题，使用较小的顶部边距
            # 假设顶部边距与底部边距相同
            top_margin = settings.BOTTOM_MARGIN
            
            # 重置 Y（与第一页相同的布局）
            current_y = page_height - top_margin
            if settings.SHOW_STROKE_ORDER:
                current_y -= (settings.STROKE_ORDER_HEIGHT + settings.ROW_SPACING)
            current_y -= (settings.PINYIN_GRID_HEIGHT + settings.PINYIN_SPACING + settings.GRID_SIZE)
        
        # 1. 绘制笔顺行 (如果开启)
        if settings.SHOW_STROKE_ORDER and stroke_manager:
            # 笔顺行布局：拼音-字 + 间距 + 笔画 + 间距 + 组词（水平对齐，字体大小统一）
            stroke_y = current_y + settings.GRID_SIZE + settings.PINYIN_SPACING + settings.PINYIN_GRID_HEIGHT + settings.ROW_SPACING/2
            
            c.saveState()
            
            # 统一的字体大小和颜色
            font_size = 14
            c.setFont(font_name, font_size)
            c.setFillColor(colors.black)
            
            # 统一的Y坐标（底部对齐）
            text_y = stroke_y + settings.STROKE_ORDER_HEIGHT * 0.15
            
            # 1a. 绘制拼音-字组合（如：yu-语）
            pinyin = stroke_manager.get_pinyin(char)
            current_x = margin_x
            
            # 组合显示拼音-字
            if pinyin:
                label_text = f"{pinyin}-{char}"
                c.drawString(current_x, text_y, label_text)
                # 计算该文本的宽度
                text_width = c.stringWidth(label_text, font_name, font_size)
                current_x += text_width + 5 * mm
            else:
                c.drawString(current_x, text_y, char)
                text_width = c.stringWidth(char, font_name, font_size)
                current_x += text_width + 5 * mm
            
            c.restoreState()
            
            # 1b. 绘制笔顺序列（从current_x开始）
            stroke_manager.draw_stroke_order_at(c, char, current_x, stroke_y, settings.STROKE_ORDER_HEIGHT, font_name)

        # 2. 绘制拼音格子行 (在田字格上方)
        # 拼音格的底部与田字格顶部之间留出间距
        pinyin_y = current_y + settings.GRID_SIZE + settings.PINYIN_SPACING
        for i in range(settings.GRID_COUNT_PER_ROW):
            x = margin_x + i * settings.GRID_SIZE
            draw_pinyin_grid(c, x, pinyin_y, settings.GRID_SIZE, settings.PINYIN_GRID_HEIGHT)

        # 3. 绘制田字格行
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
        # 下移量 = 拼音格高度 + 拼音间距 + 格子高度 + 行间距 + (笔顺高度 + 行间距 if enabled)
        step = settings.GRID_SIZE + settings.PINYIN_GRID_HEIGHT + settings.PINYIN_SPACING + settings.ROW_SPACING
        if settings.SHOW_STROKE_ORDER:
            step += settings.STROKE_ORDER_HEIGHT + settings.ROW_SPACING
            
        current_y -= step
        
    # 最后一页页码
    draw_page_number(c, page_num, page_width, subtitle_text, font_name)
    
    c.save()
    print(f"成功生成文件: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    create_practice_pdf()
