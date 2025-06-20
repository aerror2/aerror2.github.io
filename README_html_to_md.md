# HTML到Markdown转换工具

这个工具用于将HTML文件转换为Markdown格式，特别适用于将CSDN博客文章的HTML文件转换为Markdown文档。

## 功能特点

- 保留文章标题、原文链接、发布时间等元数据
- 保留文章标签信息
- 保留文章描述
- 正确转换代码块、表格、图片等元素
- 批量转换整个目录中的HTML文件

## 安装依赖

在使用此工具前，请确保安装了所需的Python库：

```bash
pip install beautifulsoup4 html2text
```

## 使用方法

### 基本用法

```bash
python html_to_md.py <HTML目录> [输出目录]
```

参数说明：
- `<HTML目录>`：包含HTML文件的目录路径（必需）
- `[输出目录]`：转换后的Markdown文件保存目录（可选，默认为"markdown"）

### 示例

将output目录中的所有HTML文件转换为Markdown格式，并保存到markdown目录：

```bash
python html_to_md.py output markdown
```

## 注意事项

1. 转换过程中可能会因HTML结构复杂而导致部分格式丢失
2. 对于特殊的HTML元素或样式，可能需要手动调整生成的Markdown文件
3. 确保有足够的磁盘空间存储转换后的文件

## 转换原理

该工具使用BeautifulSoup库解析HTML文件，提取文章的结构和内容，然后使用html2text库将HTML内容转换为Markdown格式。转换过程中会保留原文的标题、元数据、标签、描述和主体内容。