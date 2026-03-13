import os
import json
import requests
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg
from reportlab.lib.units import mm
from io import BytesIO
import sys
from reportlab.graphics.shapes import Drawing, Group
from reportlab.lib import colors
import time
from openai import OpenAI

# 尝试导入配置
try:
    from config import settings
except ImportError:
    # 如果作为脚本直接运行，可能找不到 config
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config.settings as settings

# 尝试导入拼音库
try:
    from pypinyin import lazy_pinyin, Style
    HAS_PYPINYIN = True
except ImportError:
    HAS_PYPINYIN = False

class StrokeManager:
    def __init__(self):
        self.data_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'graphics.txt')
        self.data_url = "https://raw.githubusercontent.com/skishore/makemeahanzi/master/graphics.txt"
        self.char_data = {}
        # 使用缓存文件来存储已生成的词语，避免重复调用 AI
        self.cache_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', '.words_cache.json')
        self.words_cache = {}
        
        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            base_url=settings.OPENAI_BASE_URL,
            api_key=settings.OPENAI_API_KEY
        )
        self.model = settings.OPENAI_MODEL
        
        self._load_data()
        self._load_cache()
        print("AI 词语生成系统已就绪")


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

    def _load_cache(self):
        """加载或创建组词缓存"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.words_cache = json.load(f)
                print(f"加载缓存数据完成，共 {len(self.words_cache)} 个汉字。")
            except Exception as e:
                print(f"加载缓存失败: {e}")
                self.words_cache = {}
        else:
            self.words_cache = {}

    def _save_cache(self):
        """保存组词缓存"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.words_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass  # 缓存保存失败不影响主流程

    def get_pinyin(self, char):
        """获取汉字的拼音"""
        if HAS_PYPINYIN:
            try:
                result = lazy_pinyin(char, style=Style.NORMAL)
                if result and result[0]:
                    return result[0]
            except Exception:
                pass
        # 如果没有pypinyin库或获取失败，返回空字符串
        return ""

    def _generate_words_by_ai(self, char):
        """使用 AI 生成包含该汉字的常见词语"""
        try:
            print(f"正在为 '{char}' 生成词语...")
            
            prompt = f"""请为汉字"{char}"生成3个常见的组词。要求：
1. 每个词语必须包含这个汉字
2. 词语小学生新课标需要掌握的日常词语
3. 每个词语长度2-4个汉字
4. 用逗号分隔

直接返回词语列表，例如：词语1,词语2,词语3"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            # 解析 AI 响应
            content = response.choices[0].message.content.strip()
            
            # 提取词语
            words = [w.strip() for w in content.replace('，', ',').split(',') if w.strip()]
            
            # 验证词语
            valid_words = []
            for word in words:
                # 确保词语包含目标汉字且长度合理
                if char in word and 2 <= len(word) <= 4:
                    valid_words.append(word)
            
            # 如果没有有效词语，返回空列表
            if not valid_words:
                print(f"未能为 '{char}' 生成有效词语")
                return []
            
            print(f"成功生成词语: {', '.join(valid_words)}")
            return valid_words[:3]  # 最多返回3个
            
        except Exception as e:
            print(f"AI 生成词语失败: {e}")
            return []

    def get_strokes(self, char):
        """获取汉字的笔画路径列表"""
        if char in self.char_data:
            return self.char_data[char]['strokes']
        return None

    def get_words(self, char):
        """获取汉字的相关组词（2-3个）
        
        优先级：缓存 > AI 生成
        """
        # 1. 检查缓存
        if char in self.words_cache:
            return self.words_cache[char]
        
        # 2. 使用 AI 生成词语
        words = self._generate_words_by_ai(char)
        
        # 保存到缓存
        self.words_cache[char] = words
        self._save_cache()
        
        return words

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

    def draw_stroke_order(self, c, char, x, y, height, font_name=None):
        """
        在 Canvas 上绘制汉字的笔顺序列和相关组词
        :param c: Canvas 对象
        :param char: 汉字
        :param x: 起始 X 坐标
        :param y: 起始 Y 坐标 (底部)
        :param height: 笔顺行高度
        :param font_name: 中文字体名称（用于显示组词）
        """
        self.draw_stroke_order_at(c, char, x, y, height, font_name)

    def draw_stroke_order_at(self, c, char, x, y, height, font_name=None):
        """
        在 Canvas 上从指定位置绘制汉字的笔顺序列和相关组词
        :param c: Canvas 对象
        :param char: 汉字
        :param x: 起始 X 坐标
        :param y: 起始 Y 坐标 (底部)
        :param height: 笔顺行高度
        :param font_name: 中文字体名称（用于显示组词）
        """
        drawings = self.get_stroke_drawings(char, size=height)
        if not drawings:
            return

        # 绘制每一个步骤
        current_x = x
        spacing = height * 0.2 # 间距为高度的 20%
        
        for drawing in drawings:
            # ReportLab 的 Drawing 绘制时，(0,0) 是左下角
            renderPDF.draw(drawing, c, current_x, y)
            current_x += height + spacing

        # 绘制组词（如果有）
        words = self.get_words(char)
        if words:
            # 组词显示在笔顺序列右边，与拼音-字保持对齐
            words_x = current_x + height * 0.3
            # 调整Y坐标使其与开头的拼音-字对齐（高度中部）
            words_y = y + height * 0.15
            
            c.saveState()
            # 使用统一的字体大小11号，与拼音-字对齐
            if font_name:
                c.setFont(font_name, 11)
            else:
                c.setFont("Helvetica", 11)
            
            c.setFillColor(colors.black)  # 黑色
            
            # 组词用斜杠分隔
            words_text = " / ".join(words[:3])
            
            # 绘制为单行文本
            c.drawString(words_x, words_y, words_text)
            
            c.restoreState()

if __name__ == "__main__":
    # 测试
    sm = StrokeManager()
    drawings = sm.get_stroke_drawings("我")
    print(f"生成的笔顺图数量: {len(drawings)}")
