#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
from bs4 import BeautifulSoup
import html2text
import glob
import argparse
import logging
from urllib.parse import unquote

def convert_index_html_to_md(html_file, output_dir):
    """
    将索引HTML文件转换为Markdown格式
    
    Args:
        html_file: HTML文件路径
        output_dir: 输出目录路径
    """
    # 读取HTML文件
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 移除HTML中的省略号span元素 - 更全面的匹配
    html_content = re.sub(r'<span[^>]*id="[^"]*_Closed_Text"[^>]*>[^<]*\.\.\.[^<]*</span>', '', html_content)
    html_content = re.sub(r'<span[^>]*id="[^"]*_Open_Text"[^>]*>([^<]*\.\.\.\{[^<]*)</span>', r'\1', html_content)
    html_content = re.sub(r'<span[^>]*id="[^"]*_Open_Image"[^>]*>.*?</span>', '', html_content)
    html_content = re.sub(r'<span[^>]*id="[^"]*_Closed_Image"[^>]*>.*?</span>', '', html_content)
    
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 提取标题
    title = soup.title.string if soup.title else "CSDN博客文章集合"
    
    # 构建Markdown内容
    markdown = f"# {title}\n\n"
    
    # 提取文章列表
    article_items = soup.select('.article-item')
    
    if article_items:
        for item in article_items:
            # 提取文章标题和链接
            title_element = item.select_one('.article-title a')
            if title_element:
                article_title = title_element.get_text().strip()
                article_link = title_element['href']
                
                # 提取文章描述
                desc_element = item.select_one('.article-description')
                article_desc = desc_element.get_text().strip() if desc_element else ""
                
                # 提取文章元数据
                meta_items = item.select('.meta-item')
                meta_data = {}
                for meta in meta_items:
                    meta_text = meta.get_text().strip()
                    if ':' in meta_text:
                        key, value = meta_text.split(':', 1)
                        meta_data[key.strip()] = value.strip()
                
                # 提取文章标签
                tags = [tag.get_text().strip() for tag in item.select('.tag')]
                
                # 添加到Markdown
                markdown += f"## [{article_title}]({article_link})\n\n"
                
                if article_desc:
                    markdown += f"> {article_desc}\n\n"
                
                if meta_data:
                    for key, value in meta_data.items():
                        markdown += f"- **{key}:** {value}\n"
                    markdown += "\n"
                
                if tags:
                    markdown += f"**标签:** {', '.join(tags)}\n\n"
                
                markdown += "---\n\n"
    else:
        # 如果没有找到文章列表，尝试提取其他内容
        content = soup.select_one('body')
        if content:
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.ignore_tables = False
            h.body_width = 0
            markdown += h.handle(str(content))
    
    # 生成输出文件名
    output_file = os.path.join(output_dir, "Home.md")
    
    # 将内部链接的文件扩展名移除，以适应 GitHub Wiki 格式
    # 对于内部链接，GitHub Wiki 使用不带扩展名的格式：https://github.com/username/repo/wiki/pagename
    markdown = re.sub(r'\]\(([^)]+)\.html\)', r'](\1)', markdown)
    markdown = re.sub(r'\]\(([^)]+)\.md\)', r'](\1)', markdown)
    
    # 写入Markdown文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    # 不再打印转换成功信息，由main函数统一处理
    return output_file

def convert_html_to_md(html_file, output_dir):
    """
    将HTML文件转换为Markdown格式
    
    Args:
        html_file: HTML文件路径
        output_dir: 输出目录路径
    """
    # 如果是索引文件，使用专门的转换函数
    if os.path.basename(html_file) == "index.html":
        return convert_index_html_to_md(html_file, output_dir)
    
    # 创建输出目录（如果不存在）
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取HTML文件
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    # 保存原始HTML内容，以便后续处理
    original_html = html_content
    
    # 移除HTML中的省略号span元素和图片元素
    html_content = re.sub(r'<span[^>]*id="[^"]*_Closed_Text"[^>]*>[^<]*\.\.\..*?</span>', '', html_content)
    html_content = re.sub(r'<span[^>]*id="[^"]*_Open_Text"[^>]*>([^<]*\.\.\.\{[^<]*)</span>', r'\1', html_content)
    html_content = re.sub(r'<span[^>]*id="[^"]*_Open_Image"[^>]*>.*?</span>', '', html_content)
    html_content = re.sub(r'<span[^>]*id="[^"]*_Closed_Image"[^>]*>.*?</span>', '', html_content)
    # 移除特殊的省略号图片
    html_content = re.sub(r'<img[^>]*src="[^"]*ellipsis\.png"[^>]*>', '', html_content)
    
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 提取标题
    title_tag = soup.find('h1', class_='title-article')
    title = title_tag.text.strip() if title_tag else (soup.title.string if soup.title else os.path.basename(html_file))
    
    # 提取原文链接
    link_tag = soup.find('link', rel='canonical')
    original_link = link_tag['href'] if link_tag else ''
    
    # 提取元数据（发布时间、浏览量等）
    metadata = []
    span_tags = soup.find_all('span', class_='time')
    for span in span_tags:
        metadata.append(span.text.strip())
    
    # 如果没有找到新格式的元数据，尝试旧格式
    if not metadata:
        meta_data = {}
        meta_items = soup.select('.meta-item')
        for item in meta_items:
            text = item.get_text().strip()
            if ':' in text:
                key, value = text.split(':', 1)
                meta_data[key.strip()] = value.strip()
    
    # 提取标签
    tags = []
    tag_links = soup.find_all('a', class_='tag-link')
    if tag_links:
        for tag in tag_links:
            tags.append(tag.text.strip())
    else:
        # 尝试旧格式的标签
        tag_elements = soup.select('.tag')
        for tag in tag_elements:
            tags.append(tag.get_text().strip())
    
    # 提取描述
    description = ''
    desc_tag = soup.find('meta', attrs={'name': 'description'})
    if desc_tag and 'content' in desc_tag.attrs:
        description = desc_tag['content']
    else:
        desc_element = soup.select_one('.article-description')
        if desc_element:
            description = desc_element.get_text().strip()
    
    # 提取文章内容
    article_content = ''
    article_tag = soup.find('div', id='content_views')
    if article_tag:
        # 处理 [code] 标签
        code_pattern = re.compile(r'\[code\](.*?)\[/code\]', re.DOTALL)
        for code_tag in article_tag.find_all(string=lambda text: isinstance(text, str) and '[code]' in text):
            code_text = str(code_tag)
            matches = code_pattern.findall(code_text)
            for match in matches:
                # 清理代码内容
                cleaned_code = match.strip()
                # 移除多余的 ``` 符号
                cleaned_code = re.sub(r'```\s*```\s*```\s*```', '', cleaned_code)
                cleaned_code = re.sub(r'```\s*```\s*```', '', cleaned_code)
                cleaned_code = re.sub(r'```\s*```', '', cleaned_code)
                # 确保代码有语言标识
                if not cleaned_code.startswith('```'):
                    cleaned_code = f'```\n{cleaned_code}\n```'
                # 替换原始代码块
                code_text = code_text.replace(f'[code]{match}[/code]', cleaned_code)
            # 更新原始文本
            code_tag.replace_with(code_text)
        
        # 处理代码块
        code_blocks = article_tag.find_all(['pre', 'code'])
        for code_block in code_blocks:
            # 尝试确定代码语言
            lang = ''
            if 'class' in code_block.attrs:
                for cls in code_block['class']:
                    if cls.startswith('language-') or cls.startswith('lang-'):
                        lang = cls.split('-')[1]
                        break
            
            # 如果没有找到语言标识，尝试从内容推断
            if not lang:
                if code_block.find('span', style=lambda s: s and 'COLOR: #0000ff' in s):
                    # 如果有蓝色关键字，可能是C/C++/Java等
                    if code_block.find(string=lambda s: s and any(kw in s for kw in ['int', 'char', 'void', 'struct', '#include'])):
                        lang = 'cpp'
                    elif code_block.find(string=lambda s: s and any(kw in s for kw in ['function', 'var', 'const', 'let'])):
                        lang = 'javascript'
                    else:
                        lang = 'csharp'  # 默认C#
            
            # 提取代码内容，移除图片和样式
            code_text = ''
            for element in code_block.descendants:
                if isinstance(element, str) and element.strip():
                    code_text += element
                elif element.name == 'br':
                    code_text += '\n'
                elif element.name == 'span' and element.string and element.string.strip():
                    code_text += element.string
            
            # 清理代码内容中的所有形式的省略号
            # 先处理特殊情况
            code_text = re.sub(r'\s*\.\.\.\{', ' {', code_text)
            code_text = re.sub(r'\s*\.\.\.\s*', ' ', code_text)
            # 清理行首行尾的省略号
            code_text = re.sub(r'^\.\.\.$', '', code_text.lstrip()).lstrip()
            code_text = re.sub(r'\.\.\.$', '', code_text.rstrip()).rstrip()
            # 清理行中的省略号
            code_text = re.sub(r'\.\.\.', '', code_text)
            
            # 替换原始代码块为Markdown格式的代码块
            new_code = f'```{lang}\n{code_text.strip()}\n```'
            # 使用BeautifulSoup创建新的Tag来替换原始代码块
            new_tag = soup.new_tag('pre')
            new_tag.string = new_code
            code_block.replace_with(new_tag)
        
        article_content = str(article_tag)
    
    # 如果没有找到新格式的内容，尝试旧格式
    if not article_content:
        content_element = soup.select_one('.article-content')
        if not content_element:
            content_element = soup.select_one('body')
        article_content = str(content_element)
    
    # 使用html2text转换为Markdown
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.ignore_tables = False
    h.body_width = 0  # 不自动换行
    h.unicode_snob = True  # 保留Unicode字符
    
    article_md = h.handle(article_content)
    
    # 修复可能的代码块问题（移除图片链接和多余的格式）
    
    # 直接从HTML中提取代码块并替换
    # 查找所有可能的代码块
    code_blocks = article_tag.find_all(['pre', 'code']) if article_tag else []
    extracted_code_blocks = []
    
    for code_block in code_blocks:
        # 尝试确定代码语言
        lang = ''
        if 'class' in code_block.attrs:
            for cls in code_block['class']:
                if cls.startswith('language-'):
                    lang = cls.replace('language-', '')
                    break
        
        # 如果没有找到语言标识，尝试从内容推断
        if not lang:
            if code_block.find('span', style=lambda s: s and 'COLOR: #0000ff' in s):
                # 如果有蓝色关键字，可能是C/C++/Java等
                if code_block.find(string=lambda s: s and any(kw in s for kw in ['int', 'char', 'void', 'struct', '#include'])):
                    lang = 'cpp'
                elif code_block.find(string=lambda s: s and any(kw in s for kw in ['function', 'var', 'const', 'let'])):
                    lang = 'javascript'
                else:
                    lang = 'csharp'  # 默认C#
        
        # 提取代码内容，移除图片和样式
        code_text = ''
        for element in code_block.descendants:
            if isinstance(element, str) and element.strip():
                code_text += element
            elif element.name == 'br':
                code_text += '\n'
            elif element.name == 'span' and element.string and element.string.strip():
                code_text += element.string
        
        # 清理代码文本
        code_text = code_text.replace('\r', '')
        # 清理代码内容中的所有形式的省略号
        # 先处理特殊情况
        code_text = re.sub(r'\s*\.\.\.\{', ' {', code_text)
        code_text = re.sub(r'\s*\.\.\.\s*', ' ', code_text)
        # 清理行首行尾的省略号
        code_text = re.sub(r'^\.\.\.$', '', code_text.lstrip()).lstrip()
        code_text = re.sub(r'\.\.\.$', '', code_text.rstrip()).rstrip()
        # 清理行中的省略号
        code_text = re.sub(r'\.\.\.', '', code_text)
        # 移除多余的空行
        code_text = re.sub(r'\n\s*\n', '\n', code_text)
        # 构建Markdown代码块
        md_code_block = f'```{lang}\n{code_text.strip()}\n```'
        extracted_code_blocks.append((code_block, md_code_block))
    
    # 在HTML中替换代码块
    for original, replacement in extracted_code_blocks:
        new_tag = soup.new_tag('pre')
        new_tag.string = replacement
        original.replace_with(new_tag)
    
    article_content = str(article_tag) if article_tag else ''
    
    # 直接处理带颜色的文本
    colored_spans = soup.find_all('span', style=lambda s: s and 'color:' in s.lower())
    for span in colored_spans:
        if span.string and span.string.strip():
            style = span.get('style', '')
            color_match = re.search(r'color:\s*([#\w]+)', style, re.IGNORECASE)
            if color_match:
                color_code = color_match.group(1)
                # 创建新的标签结构
                new_text = f"<font color=\"{color_code}\">{span.string}</font>"
                new_tag = soup.new_tag('span')
                new_tag.string = new_text
                span.replace_with(new_tag)

    
    # 处理图片和视频
    # 查找所有图片元素
    images = soup.find_all('img')
    for img in images:
        if 'src' in img.attrs:
            img_src = img['src']
            img_alt = img.get('alt', '')
            
            # 处理图片路径，使用本地images目录
            if img_src.startswith(('http://', 'https://', '//')):  
                # 提取文件名
                img_filename = os.path.basename(unquote(img_src.split('/')[-1].split('?')[0]))
                # 使用本地路径
                local_img_path = f"images/{img_filename}"
            else:
                # 如果是相对路径，保持相对路径但指向markdown/images目录
                img_filename = os.path.basename(img_src)
                local_img_path = f"images/{img_filename}"
            
            # 创建新的Markdown图片标签
            img_md = f"![{img_alt}]({local_img_path})"
            # 替换原始图片标签
            new_tag = soup.new_tag('p')
            new_tag.string = img_md
            img.replace_with(new_tag)
    
    # 处理视频元素
    videos = soup.find_all(['video', 'iframe'])
    for video in videos:
        video_src = ''
        if video.name == 'video':
            # 尝试从 source 子元素获取 src
            source = video.find('source')
            if source and 'src' in source.attrs:
                video_src = source['src']
            # 如果没有 source 子元素，尝试直接从 video 标签获取 src
            elif 'src' in video.attrs:
                video_src = video['src']
        elif video.name == 'iframe' and 'src' in video.attrs:
            video_src = video['src']
        
        if video_src:
            # 根据视频类型创建适当的HTML嵌入代码
            if video.name == 'video' or video_src.endswith(('.mp4', '.webm', '.ogg')):
                # 视频文件使用video标签
                video_md = f"<video src=\"{video_src}\" controls width=\"100%\" style=\"max-width:100%\"></video>"
            elif video.name == 'iframe' or 'youtube' in video_src or 'bilibili' in video_src:
                # iframe嵌入（YouTube、Bilibili等）
                video_md = f"<iframe src=\"{video_src}\" frameborder=\"0\" allowfullscreen width=\"100%\" style=\"max-width:100%\"></iframe>"
            else:
                # 其他类型，提供链接
                video_md = f"视频链接: [{video_src}]({video_src})"
            
            # 替换原始视频标签
            new_tag = soup.new_tag('p')
            new_tag.string = video_md
            video.replace_with(new_tag)
    
    # 使用html2text转换为Markdown
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.body_width = 0  # 不自动换行
    h.mark_code = True
    h.escape_snob = False  # 不转义特殊字符
    h.unicode_snob = True  # 保留Unicode字符
    h.skip_internal_links = False
    h.inline_links = True
    h.protect_links = True  # 保护链接
    h.images_to_alt = False
    h.images_with_size = False
    h.ignore_images = False
    h.ignore_emphasis = False
    h.ignore_tables = False
    h.single_line_break = True  # 单行换行
    h.emphasis_mark = '*'  # 强调标记
    h.strong_mark = '**'  # 加粗标记
    h.ul_item_mark = '-'  # 无序列表标记
    h.emphasis = True  # 启用强调
    h.google_doc = False
    h.hide_strikethrough = False
    h.ignore_anchors = False
    h.pad_tables = True
    h.wrap_links = False  # 不换行链接
    h.wrap_list_items = False  # 不换行列表项
    h.inline_links = True
    h.protect_links = True
    h.mark_code = True
    # 保留 font 标签
    h.ignore_tags = ['font']
    
    article_md = h.handle(article_content)
    
    # 清理代码块中的多余内容
    def clean_code_block(match):
        block = match.group(0)
        # 移除图片链接
        cleaned = re.sub(r'!\[\]\(images/.*?\)', '', block)
        
        # 处理 [code] 标签和多余的 ``` 符号
        cleaned = re.sub(r'\[code\]\s*', '', cleaned)
        cleaned = re.sub(r'\s*\[/code\]', '', cleaned)
        
        # 修复多余的反引号
        cleaned = re.sub(r'```\s*```\s*```\s*```', '```', cleaned)
        cleaned = re.sub(r'```\s*```\s*```', '```', cleaned)
        cleaned = re.sub(r'```\s*```', '```', cleaned)
        
        # 确保代码块格式正确
        if cleaned.startswith('```') and cleaned.count('```') >= 2:
            # 已经是正确的代码块格式，保持不变
            pass
        elif cleaned.startswith('```') and cleaned.count('```') == 1:
            # 只有开始的 ```，添加结束的 ```
            cleaned = cleaned + '\n```'
        elif cleaned.count('```') == 0 and cleaned.strip():
            # 没有 ```，添加开始和结束的 ```
            lang = ''
            cleaned = f'```{lang}\n{cleaned.strip()}\n```'
        
        # 清理代码内容中的所有形式的省略号 - 更全面的方法
        # 先处理特殊情况
        cleaned = re.sub(r'\s*\.\.\.\{', ' {', cleaned)
        cleaned = re.sub(r'\s*\.\.\.\s*', ' ', cleaned)
        # 清理行首行尾的省略号
        cleaned = re.sub(r'^\.\.\.$', '', cleaned.lstrip()).lstrip()
        cleaned = re.sub(r'\.\.\.$', '', cleaned.rstrip()).rstrip()
        # 清理行中的省略号 - 更彻底的方法
        cleaned = re.sub(r'\.\.\.', '', cleaned)
        # 清理行首的省略号后跟着大括号的情况
        cleaned = re.sub(r'^\s*\.\.\.\s*\{', ' {', cleaned)
        # 清理行中间的省略号
        cleaned = re.sub(r'\s\.\.\.\s', ' ', cleaned)
        # 清理行尾的省略号
        cleaned = re.sub(r'\s\.\.\.\n', '\n', cleaned)
        # 清理独立行的省略号
        cleaned = re.sub(r'^\s*\.\.\.\s*$', '', cleaned, flags=re.MULTILINE)
        
        # 移除多余的空行和格式
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        # 移除可能的HTML标签
        cleaned = re.sub(r'<.*?>', '', cleaned)
        # 移除所有剩余的省略号和Unicode省略号
        cleaned = re.sub(r'\.\.\.|…', '', cleaned)
        
        return cleaned
    
    # 处理 [code] 标签
    def clean_code_tag(match):
        content = match.group(1).strip()
        # 移除多余的 ``` 符号
        content = re.sub(r'```\s*```\s*```\s*```', '', content)
        content = re.sub(r'```\s*```\s*```', '', content)
        content = re.sub(r'```\s*```', '', content)
        # 如果内容已经有 ``` 标记，确保格式正确
        if '```' in content:
            # 确保开始和结束都有 ```
            if content.count('```') % 2 != 0:
                content += '\n```'
        else:
            # 如果没有 ``` 标记，添加
            content = f'```\n{content}\n```'
        return content
    
    # 清理 [code] 标签
    article_md = re.sub(r'\[code\]\s*(.*?)\s*\[/code\]', lambda m: clean_code_tag(m), article_md, flags=re.DOTALL)
    
    # 查找并清理所有代码块
    article_md = re.sub(r'```.*?```', clean_code_block, article_md, flags=re.DOTALL)
    
    # 构建完整的Markdown内容
    markdown = f"# {title}\n\n"
    
    # 添加原文链接
    if original_link:
        markdown += f"原文链接: {original_link}\n\n"
    else:
        source_link = soup.select_one('.source-link')
        if source_link and source_link.a:
            markdown += f"原文链接: {source_link.a['href']}\n\n"
    
    # 添加元数据
    if 'meta_data' in locals() and meta_data:
        markdown += "## 文章信息\n\n"
        for key, value in meta_data.items():
            markdown += f"- {key}: {value}\n"
        markdown += "\n"
    elif metadata:
        markdown += "文章信息：" + " | ".join(metadata) + "\n\n"
    
    # 添加标签
    if tags:
        markdown += f"标签: {', '.join(tags)}\n\n"
    
    # 添加描述
    if description:
        markdown += f"> {description}\n\n"
    
    # 添加内容
    markdown += article_md
    
    # 生成输出文件名
    base_name = os.path.splitext(os.path.basename(html_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}.md")
    
    # 替换 .html 链接为 .md 链接
    markdown = re.sub(r'\]\(([^)]+)\.html\)', r']\(\1.md)', markdown)
    
    # 从原始HTML中提取带颜色的文本，并将其替换回Markdown文件中
    # 注释掉这部分代码，因为它使用了未导入的uuid模块，并且可能导致性能问题
    # soup_original = BeautifulSoup(original_html, 'html.parser')
    # colored_spans = soup_original.find_all('span', style=lambda s: s and 'color:' in s.lower())
    # 
    # for span in colored_spans:
    #     if span.string and span.string.strip():
    #         style = span.get('style', '')
    #         color_match = re.search(r'color:\s*([#\w]+)', style, re.IGNORECASE)
    #         if color_match:
    #             color_code = color_match.group(1)
    #             text = span.string.strip()
    #             # 在Markdown中查找纯文本，并替换为带颜色的文本
    #             if text and text in markdown:
    #                 # 需要导入uuid模块
    #                 # import uuid
    #                 # 创建一个唯一的标记，确保不会与文本内容冲突
    #                 # placeholder = f"COLOR_PLACEHOLDER_{uuid.uuid4().hex}"
    #                 # 先将文本替换为占位符
    #                 # markdown = markdown.replace(text, placeholder)
    #                 # 然后将占位符替换为带颜色的文本
    #                 # markdown = markdown.replace(placeholder, f'<font color="{color_code}">{text}</font>')
    
    # 写入Markdown文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    # 不再打印转换成功信息，由main函数统一处理
    return output_file

def main():
    if len(sys.argv) < 2:
        print("用法: python html_to_md.py <HTML文件或目录> [输出目录]")
        sys.exit(1)
    
    html_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "markdown"
    
    # 创建输出目录（如果不存在）
    os.makedirs(output_dir, exist_ok=True)
    
    # 检查输入路径是文件还是目录
    if os.path.isfile(html_path) and html_path.lower().endswith('.html'):
        # 单个HTML文件
        try:
            output_file = convert_html_to_md(html_path, output_dir)
            print(f"已转换: {html_path} -> {output_file}")
        except Exception as e:
            print(f"转换 {html_path} 时出错: {e}")
            sys.exit(1)
    elif os.path.isdir(html_path):
        # HTML目录
        # 获取所有HTML文件
        html_files = glob.glob(os.path.join(html_path, "*.html"))
        
        if not html_files:
            print(f"错误: 在 {html_path} 中没有找到HTML文件")
            sys.exit(1)
        
        # 创建已处理文件的集合，避免重复处理
        processed_files = set()
        
        # 首先转换index.html（如果存在）
        index_file = os.path.join(html_path, "index.html")
        if os.path.exists(index_file):
            try:
                output_file = convert_html_to_md(index_file, output_dir)
                print(f"已转换: {index_file} -> {output_file}")
                processed_files.add(index_file)
            except Exception as e:
                print(f"转换索引文件时出错: {e}")
        
        # 转换其他HTML文件
        converted_count = len(processed_files)
        for html_file in html_files:
            if html_file not in processed_files:  # 避免重复处理
                try:
                    print(f"开始转换: {html_file} ")

                    output_file = convert_html_to_md(html_file, output_dir)
                    print(f"已转换: {html_file} -> {output_file}")
                    converted_count += 1
                except Exception as e:
                    print(f"转换 {html_file} 时出错: {e}")
        
        print(f"\n共转换 {converted_count} 个文件到 {output_dir} 目录")
    else:
        print(f"错误: 输入路径不是有效的HTML文件或目录 - {html_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()