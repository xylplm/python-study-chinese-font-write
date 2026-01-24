# 汉字田字格书写练习生成器

这是一个简单的 Python 工具，用于生成 PDF 格式的汉字田字格书写练习纸。

## 功能特点

*   **自定义汉字**：可以自由设置需要练习的汉字列表。
*   **标准排版**：
    *   第一个字为黑色实体（范例）。
    *   第 2-5 个字为浅灰色（描红/临摹）。
    *   后续格子为空白田字格（独立练习）。
*   **自动分页**：支持大量汉字，自动生成多页 PDF。
*   **标题栏**：每页顶部包含标题和姓名/日期填写栏。
*   **配置分离**：所有配置项都在单独的文件中，方便修改。

## 目录结构

```
study-font-write/
├── config/
│   └── settings.py      # 配置文件 (修改汉字、字体、颜色等)
├── output/              # 生成的 PDF 文件存放位置
├── create_practice_pdf.py # 主程序脚本
└── README.md            # 说明文档
```

## 使用方法

### 1. 安装依赖

确保你已经安装了 Python，然后安装 `reportlab` 库：

```bash
pip install reportlab
```

### 2. 修改配置 (可选)

打开 `config/settings.py` 文件，你可以修改以下内容：

*   `CHAR_LIST`: 要练习的汉字列表。
*   `FONT_PATH`: 字体文件路径 (默认使用 Windows 楷体)。
*   `GRID_COLOR`: 田字格颜色。
*   `TEXT_COLOR_DASHED`: 描红字的颜色。
*   其他排版参数...

### 3. 运行程序

在项目根目录下运行：

```bash
python create_practice_pdf.py
```

### 4. 查看结果

生成的 PDF 文件将保存在 `output` 文件夹中，默认文件名为 `hanzi_practice.pdf`。

## 常见问题

*   **找不到字体**：请检查 `config/settings.py` 中的 `FONT_PATH` 是否正确指向了你电脑上的字体文件。
*   **乱码**：确保使用的字体支持中文（推荐使用楷体或黑体）。
