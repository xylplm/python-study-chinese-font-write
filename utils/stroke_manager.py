import os
import json
import requests
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg
from reportlab.lib.units import mm
from io import BytesIO
import sys
from reportlab.graphics.shapes import Drawing, Group

# 尝试导入配置
try:
    from config import settings
except ImportError:
    # 如果作为脚本直接运行，可能找不到 config
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config.settings as settings

class StrokeManager:
    def __init__(self):
        self.data_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'graphics.txt')
        self.data_url = "https://raw.githubusercontent.com/skishore/makemeahanzi/master/graphics.txt"
        self.char_data = {}
        self._load_data()

    def _load_data(self):
        """加载数据，如果不存在则下载"""
        if not os.path.exists(self.data_file):
            print(f"笔顺数据文件不存在，正在下载... ({self.data_url})")
            try:
                proxies = None
                if hasattr(settings, 'PROXY_URL') and settings.PROXY_URL:
                    proxies = {
                        'http': settings.PROXY_URL,
                        'https': settings.PROXY_URL
                    }
                    print(f"使用代理: {settings.PROXY_URL}")
                
                response = requests.get(self.data_url, proxies=proxies)
                response.raise_for_status()
                with open(self.data_file, 'wb') as f:
                    f.write(response.content)
                print("下载完成！")
            except Exception as e:
                print(f"下载失败: {e}")
                print("请检查网络连接或手动下载 graphics.txt 到 data 目录。")
                return

        print("正在加载笔顺数据...")
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        self.char_data[entry['character']] = entry
                    except json.JSONDecodeError:
                        continue
            print(f"加载完成，共 {len(self.char_data)} 个汉字数据。")
        except Exception as e:
            print(f"加载数据失败: {e}")

    def get_strokes(self, char):
        """获取汉字的笔画路径列表"""
        if char in self.char_data:
            return self.char_data[char]['strokes']
        return None

    def get_stroke_drawings(self, char, size=100):
        """
        获取汉字的分步笔顺 Drawing 对象列表
        """
        strokes = self.get_strokes(char)
        if not strokes:
            return []

        drawings = []
        current_paths = []
        
        print(f"Generating strokes for {char}, size={size}")

        for stroke in strokes:
            current_paths.append(stroke)
            
            # 构建 SVG
            # MakeMeAHanzi 数据通常需要垂直翻转
            svg_content = f'''
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
                <g transform="scale(1, -1) translate(0, -900)">
                    {''.join([f'<path d="{p}" fill="black" />' for p in current_paths])}
                </g>
            </svg>
            '''
            
            try:
                rlg_drawing = svg2rlg(BytesIO(svg_content.encode('utf-8')))
                if rlg_drawing:
                    # 创建一个新的 Drawing 作为容器
                    d = Drawing(size, size)
                    
                    # 计算缩放比例
                    scale_factor = size / 1024.0
                    
                    # 将原始内容放入 Group 并缩放
                    # 注意：rlg_drawing.contents 是一个列表，通常包含一个 Group
                    g = Group(*rlg_drawing.contents)
                    g.scale(scale_factor, scale_factor)
                    
                    d.add(g)
                    drawings.append(d)
            except Exception as e:
                print(f"Error parsing SVG for {char}: {e}")
                
        return drawings

    def draw_stroke_order(self, c, char, x, y, height):
        """
        在 Canvas 上绘制汉字的笔顺序列
        :param c: Canvas 对象
        :param char: 汉字
        :param x: 起始 X 坐标
        :param y: 起始 Y 坐标 (底部)
        :param height: 笔顺图的高度
        """
        drawings = self.get_stroke_drawings(char, size=height)
        if not drawings:
            return

        # 绘制每一个步骤
        current_x = x
        spacing = height * 0.2 # 间距为高度的 20%
        
        for drawing in drawings:
            # 检查是否超出页面宽度 (假设页面宽度已知或传入？这里简单处理)
            # 如果需要换行，这里比较麻烦，因为是在 PDF 生成流程中。
            # 假设一行能画下。
            
            # ReportLab 的 Drawing 绘制时，(0,0) 是左下角
            renderPDF.draw(drawing, c, current_x, y)
            current_x += height + spacing

if __name__ == "__main__":
    # 测试
    sm = StrokeManager()
    drawings = sm.get_stroke_drawings("我")
    print(f"生成的笔顺图数量: {len(drawings)}")
