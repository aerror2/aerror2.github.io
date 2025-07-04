#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import os
import sys
import re
import time
import datetime
import random
import urllib.parse
import hashlib
import shutil
import json
from urllib.parse import urljoin, urlparse

def generate_short_name(index, existing_shortnames=None):
    """生成短文件名（最多三个字符，小写字母和数字）
    
    Args:
        index: 索引值，用于生成短文件名
        existing_shortnames: 已存在的短文件名集合，用于排重
        
    Returns:
        生成的不重复短文件名
    """
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    chars_len = len(chars)
    
    # 如果没有提供已存在的短文件名集合，创建一个空集合
    if existing_shortnames is None:
        existing_shortnames = set()
    
    # 尝试生成短文件名，直到找到一个不在已存在集合中的名称
    while True:
        if index < chars_len:
            short_name = chars[index]
        elif index < chars_len * chars_len:
            # 两位数的命名
            first_char = chars[index // chars_len]
            second_char = chars[index % chars_len]
            short_name = first_char + second_char
        else:
            # 三位数的命名
            first_char = chars[(index // (chars_len * chars_len)) % chars_len]
            second_char = chars[(index // chars_len) % chars_len]
            third_char = chars[index % chars_len]
            short_name = first_char + second_char + third_char
        
        # 检查生成的短文件名是否已存在
        if short_name not in existing_shortnames:
            return short_name
        
        # 如果已存在，增加索引值尝试下一个
        index += 1

def read_urls_from_config(config_file):
    """从配置文件中读取URL列表和对应的文件名
    配置文件格式：文件名=URL
    注意：等号只用于分隔第一个出现的等号，URL中可能包含等号
    返回：(url_map, titles_map) - URL映射到短文件名，URL映射到原始标题
    """
    url_map = {}
    titles_map = {}
    shortname_map = {}
    
    # 标准化URL格式的函数
    def normalize_url(url):
        """标准化URL格式，确保一致性"""
        if not url.startswith(('http://', 'https://')):
            return 'https://' + url
        return url
    
    # 尝试读取持久化的短文件名映射
    shortname_file = os.path.join(os.path.dirname(config_file), "shortname_map.txt")
    if os.path.exists(shortname_file):
        try:
            with open(shortname_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        url, short_name = parts[0].strip(), parts[1].strip()
                        url = normalize_url(url)  # 标准化URL
                        shortname_map[url] = short_name
            print(f"已加载 {len(shortname_map)} 个短文件名映射")
        except Exception as e:
            print(f"读取短文件名映射文件时出错: {e}")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            index = 0
            for line in f:
                line = line.strip()
                # 跳过空行和注释行
                if not line or line.startswith('#'):
                    continue
                
                # 使用第一个等号分隔行内容
                parts = line.split('=', 1)
                if len(parts) == 2:
                    original_title, url = parts[0].strip(), parts[1].strip()
                    # 确保URL是有效的
                    url_match = re.search(r'https?://[^\s]+', url)
                    if url_match:
                        url = url_match.group(0)
                        url = normalize_url(url)  # 标准化URL
                        # 使用已存在的短文件名或生成新的
                        if url in shortname_map:
                            short_name = shortname_map[url]
                        else:
                            # 获取已存在的短文件名集合用于排重
                            existing_shortnames = set(shortname_map.values())
                            short_name = generate_short_name(index, existing_shortnames)
                            shortname_map[url] = short_name
                        url_map[short_name] = url
                        titles_map[url] = original_title
                        index += 1
                else:
                    # 兼容旧格式：直接提取URL
                    url_match = re.search(r'https?://[^\s]+', line)
                    if url_match:
                        url = url_match.group(0)
                        url = normalize_url(url)  # 标准化URL
                        # 使用已存在的短文件名或生成新的
                        if url in shortname_map:
                            short_name = shortname_map[url]
                            
                        else:
                            # 获取已存在的短文件名集合用于排重
                            existing_shortnames = set(shortname_map.values())
                            short_name = generate_short_name(index, existing_shortnames)
                            shortname_map[url] = short_name
                        url_map[short_name] = url
                        # 从URL中提取文章ID作为标题
                        article_id = re.search(r'article/(\w+)', url)
                        if article_id:
                            titles_map[url] = article_id.group(1)
                        else:
                            titles_map[url] = f"文章{index+1}"
                        index += 1
        
        # 保存短文件名映射
        try:
            with open(shortname_file, 'w', encoding='utf-8') as f:
                f.write("# URL=短文件名映射，请勿手动修改\n")
                for url, short_name in shortname_map.items():
                    # 确保URL是标准化的
                    normalized_url = normalize_url(url)
                    f.write(f"{normalized_url}={short_name}\n")
            print(f"已保存 {len(shortname_map)} 个短文件名映射到 {shortname_file}")
        except Exception as e:
            print(f"保存短文件名映射文件时出错: {e}")
    except Exception as e:
        print(f"读取配置文件时出错: {e}")
    return url_map, titles_map

def fetch_html_content(url):
    """获取URL的HTML内容"""
    try:
        # 更完整的请求头，模拟真实浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://blog.csdn.net/'
        }
        
        # 添加随机延迟，避免被识别为爬虫
        time.sleep(random.uniform(1, 3))
        
        # 创建会话对象，保持cookie
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 如果请求不成功则抛出异常
        response.encoding = 'utf-8'  # 确保正确处理中文
        return response.text
    except Exception as e:
        print(f"获取HTML内容时出错: {e}")
        return None

# 全局CSS缓存，用于避免重复下载相同的CSS文件
# 格式: {url: relative_file_path}
css_cache = {}
# 全局CSS内容哈希缓存，避免重复内容
css_content_hash_cache = {}

def download_file(url, output_dir, subdir, file_type='image'):
    """下载文件（图片或CSS）并保存到本地
    
    Args:
        url: 文件URL
        output_dir: 输出目录
        subdir: 子目录名
        file_type: 文件类型，'image'或'css'
        
    Returns:
        本地文件路径（相对于HTML文件）
    """
    try:
        # 处理相对URL
        if url.startswith('//'):
            url = 'https:' + url
        elif url.startswith('/'):
            url = 'https://blog.csdn.net' + url
        
        # 对于CSS文件，检查URL缓存
        if file_type == 'css' and url in css_cache:
            return css_cache[url]
        
        # 创建目录
        file_dir = os.path.join(output_dir, subdir)
        os.makedirs(file_dir, exist_ok=True)
        
        # 添加随机延迟，避免被识别为爬虫
        time.sleep(random.uniform(0.5, 1.5))
        
        # 下载文件
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://blog.csdn.net/'
        }
        
        response = requests.get(url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()
        
        # 对于CSS文件，实现内容哈希缓存
        if file_type == 'css':
            # 读取响应内容
            content = response.content
            # 计算内容哈希值
            content_hash = hashlib.md5(content).hexdigest()
            
            # 检查是否已存在相同内容的CSS文件
            if content_hash in css_content_hash_cache:
                # 如果已存在，直接使用已有文件路径
                css_cache[url] = css_content_hash_cache[content_hash]
                print(f"CSS内容已存在，使用缓存: {url} -> {css_content_hash_cache[content_hash]}")
                return css_content_hash_cache[content_hash]
            
            # 使用内容哈希值作为文件名
            file_name = content_hash + '.css'
            local_file_path = os.path.join(file_dir, file_name)
            relative_file_path = os.path.join(subdir, file_name)
            
            # 保存文件内容
            with open(local_file_path, 'wb') as f:
                f.write(content)
            
            # 更新缓存
            css_cache[url] = relative_file_path
            css_content_hash_cache[content_hash] = relative_file_path
            
            print(f"已下载CSS: {url} -> {local_file_path}")
            return relative_file_path
        else:
            # 处理图片文件
            # 从URL中提取文件名
            file_name = os.path.basename(urllib.parse.urlparse(url).path)
            
            # 如果文件名不包含扩展名或者扩展名不明确，使用URL的哈希值作为文件名
            if not file_name or '.' not in file_name:
                file_name = hashlib.md5(url.encode()).hexdigest() + '.jpg'
            
            # 本地文件路径
            local_file_path = os.path.join(file_dir, file_name)
            relative_file_path = os.path.join(subdir, file_name)
            
            # 如果文件已存在，直接返回路径
            if os.path.exists(local_file_path):
                return relative_file_path
            
            # 保存文件内容
            with open(local_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"已下载图片: {url} -> {local_file_path}")
            return relative_file_path
    except Exception as e:
        print(f"下载{file_type}时出错 {url}: {e}")
        return url  # 如果下载失败，返回原始URL

def download_image(img_url, output_dir, article_dir):
    """下载图片并保存到本地（兼容旧接口）"""
    return download_file(img_url, output_dir, article_dir, 'image')

def extract_css_links(soup, base_url):
    """提取页面中的CSS链接"""
    css_links = []
    
    # 查找所有link标签中的CSS
    for link in soup.find_all('link', rel='stylesheet'):
        if link.get('href'):
            css_url = link['href']
            # 处理相对URL
            if not css_url.startswith(('http://', 'https://')):
                if css_url.startswith('//'):
                    css_url = 'https:' + css_url
                elif css_url.startswith('/'):
                    css_url = urljoin('https://blog.csdn.net', css_url)
                else:
                    css_url = urljoin(base_url, css_url)
            css_links.append(css_url)
    
    # 查找所有style标签中的@import
    for style in soup.find_all('style'):
        if style.string:
            import_urls = re.findall(r'@import\s+[\'"](.*?)[\'"]', style.string)
            for import_url in import_urls:
                if not import_url.startswith(('http://', 'https://')):
                    if import_url.startswith('//'):
                        import_url = 'https:' + import_url
                    elif import_url.startswith('/'):
                        import_url = urljoin('https://blog.csdn.net', import_url)
                    else:
                        import_url = urljoin(base_url, import_url)
                css_links.append(import_url)
    
    return css_links

def extract_inline_styles(soup):
    """提取页面中的内联样式"""
    inline_styles = ""
    
    # 提取所有style标签的内容
    for style in soup.find_all('style'):
        if style.string:
            inline_styles += style.string + "\n"
    
    return inline_styles

def extract_blog_content(html_content, output_dir, article_dir, url):
    """提取blog-content-box div的内容，并下载图片和CSS"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 当使用JSON数据源时，不需要从HTML提取发布时间
        # 返回None作为发布时间，让main函数使用JSON中的postTime字段
        publish_time = None
        

        # 提取CSS链接并下载
        css_links = extract_css_links(soup, url)
        css_paths = []
        
        # 创建公共CSS目录
        common_css_dir = os.path.join(output_dir, "css/common")
        os.makedirs(common_css_dir, exist_ok=True)
        
        # 下载CSS文件到公共目录
        for css_url in css_links:
            # 使用URL的哈希值作为CSS文件名，确保唯一性
            css_hash = hashlib.md5(css_url.encode()).hexdigest()
            css_path = download_file(css_url, output_dir, "css/common", 'css')
            if css_path not in css_paths:
                css_paths.append(css_path)
        
        # 提取内联样式
        inline_styles = extract_inline_styles(soup)
        
        # 保存内联样式到文件
        if inline_styles:
            # 计算内联样式的哈希值，用于去重
            inline_hash = hashlib.md5(inline_styles.encode()).hexdigest()
            inline_css_path = os.path.join(common_css_dir, f"inline_{inline_hash}.css")
            
            # 检查是否已存在相同的内联样式文件
            if not os.path.exists(inline_css_path):
                with open(inline_css_path, 'w', encoding='utf-8') as f:
                    f.write(inline_styles)
                print(f"已保存内联样式: {inline_css_path}")
            
            css_paths.append(f"css/common/inline_{inline_hash}.css")
            
        # 确保保留所有元素的style属性和class属性
        # 这对于保留原文中带颜色的文字非常重要
        
        # 处理带有颜色的文本，确保样式不会丢失
        for element in soup.find_all(['span', 'font', 'p', 'div', 'strong', 'em', 'b', 'i']):
            # 保留style属性
            if element.has_attr('style'):
                # 确保style属性不会被修改或删除
                pass
            
            # 保留color属性（针对font标签）
            if element.name == 'font' and element.has_attr('color'):
                # 确保color属性不会被修改或删除
                pass
            
            # 保留class属性
            if element.has_attr('class'):
                # 确保class属性不会被修改或删除
                pass
        
        content_box = soup.find('div', class_='blog-content-box')
        
        if content_box:
            # 尝试提取文章的主要内容部分
            article_content = content_box.find('div', id='article_content')
            if article_content:
                # 提取文章标题
                title_element = content_box.find('h1', class_='title-article')
                title = title_element.text if title_element else "CSDN文章内容"
                
                # 提取文章内容视图
                content_views = article_content.find('div', id='content_views')
                if content_views:
                    # 处理代码块，添加语言类
                    for pre in content_views.find_all('pre'):
                        code_block = pre.find('code')
                        if code_block:
                            # 检查是否已有语言类
                            has_language_class = False
                            for class_name in code_block.get('class', []):
                                if class_name.startswith('language-'):
                                    has_language_class = True
                                    break
                            
                            # 如果没有语言类，添加默认语言类
                            if not has_language_class:
                                code_block['class'] = code_block.get('class', []) + ['hljs', 'language-javascript']
                            # 确保有hljs类
                            elif 'hljs' not in code_block.get('class', []):
                                code_block['class'] = code_block.get('class', []) + ['hljs']
                    
                    # 下载并替换图片链接
                    for img in content_views.find_all('img'):
                        if img.get('src'):
                            img_url = img['src']
                            local_img_path = download_image(img_url, output_dir, f"images/{article_dir}")
                            img['src'] = local_img_path
                    
                    return title, str(content_views), css_paths, publish_time
                
                # 处理代码块，添加语言类
                for pre in article_content.find_all('pre'):
                    code_block = pre.find('code')
                    if code_block:
                        # 检查是否已有语言类
                        has_language_class = False
                        for class_name in code_block.get('class', []):
                            if class_name.startswith('language-'):
                                has_language_class = True
                                break
                        
                        # 如果没有语言类，添加默认语言类
                        if not has_language_class:
                            code_block['class'] = code_block.get('class', []) + ['language-javascript']
                
                # 下载并替换图片链接
                for img in article_content.find_all('img'):
                    if img.get('src'):
                        img_url = img['src']
                        local_img_path = download_image(img_url, output_dir, f"images/{article_dir}")
                        img['src'] = local_img_path
                
                return title, str(article_content), css_paths, publish_time
            
            # 如果找不到article_content，尝试处理整个content_box
            # 提取文章标题
            title_element = content_box.find('h1', class_='title-article')
            title = title_element.text if title_element else "CSDN文章内容"
            
            # 处理代码块，添加语言类
            for pre in content_box.find_all('pre'):
                code_block = pre.find('code')
                if code_block:
                    # 检查是否已有语言类
                    has_language_class = False
                    for class_name in code_block.get('class', []):
                        if class_name.startswith('language-'):
                            has_language_class = True
                            break
                    
                    # 如果没有语言类，添加默认语言类
                    if not has_language_class:
                        code_block['class'] = code_block.get('class', []) + ['hljs', 'language-javascript']
                    # 确保有hljs类
                    elif 'hljs' not in code_block.get('class', []):
                        code_block['class'] = code_block.get('class', []) + ['hljs']
            
            # 下载并替换图片链接
            for img in content_box.find_all('img'):
                if img.get('src'):
                    img_url = img['src']
                    local_img_path = download_image(img_url, output_dir, f"images/{article_dir}")
                    img['src'] = local_img_path
            
            return title, str(content_box), css_paths, publish_time
        else:
            print("未找到'blog-content-box'内容")
            return None, None, [], None
    except Exception as e:
        print(f"解析HTML内容时出错: {e}")
        return None, None, [], None

def generate_html(title, content, url, output_file, css_paths=None, publish_time=None, view_count=None, comment_count=None, collect_count=None, digg_count=None, tags=None, description=None):
    """生成包含提取内容的HTML文件
    
    Args:
        title: 文章标题
        content: 文章内容
        url: 原文链接
        output_file: 输出文件路径
        css_paths: CSS文件路径列表
        publish_time: 发布时间
        view_count: 浏览量
        comment_count: 评论数
        collect_count: 收藏数
        digg_count: 点赞数
        tags: 标签列表
        description: 文章描述
    """
    try:
        # 构建CSS链接
        css_links = ""
        if css_paths:
            for css_path in css_paths:
                css_links += f'    <link rel="stylesheet" href="{css_path}">' + "\n"
        
        # 添加Prism.js的CSS和JS
        prism_css = "    <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-okaidia.min.css\">\n"
        prism_js = "    <script src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js\"></script>\n"
        prism_js += "    <script src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/autoloader/prism-autoloader.min.js\"></script>\n"
        prism_js += "    <script src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/copy-to-clipboard/prism-copy-to-clipboard.min.js\"></script>\n"
        
        # 添加额外的CSS以确保保留原文中带颜色的文字
        extra_css = """    <style>
        /* 保留CSDN常用的文本颜色类 */
        .text-red, [class*="text-red"] { color: red !important; }
        .text-blue, [class*="text-blue"] { color: blue !important; }
        .text-green, [class*="text-green"] { color: green !important; }
        .text-yellow, [class*="text-yellow"] { color: #FFD700 !important; }
        .text-purple, [class*="text-purple"] { color: purple !important; }
        .text-orange, [class*="text-orange"] { color: orange !important; }
        
        /* 保留常见的CSDN文本样式类 */
        .bold, .strong, [class*="bold"], [class*="strong"] { font-weight: bold !important; }
        .italic, .em, [class*="italic"], [class*="em"] { font-style: italic !important; }
        .underline, [class*="underline"] { text-decoration: underline !important; }
        
        /* 确保内联样式不被覆盖 */
        .article-content * { color: initial; background-color: initial; font-weight: initial; font-style: initial; text-decoration: initial; }
        
        /* 保留font标签的color属性 */
        .article-content font[color="red"] { color: red !important; }
        .article-content font[color="blue"] { color: blue !important; }
        .article-content font[color="green"] { color: green !important; }
        .article-content font[color="yellow"] { color: yellow !important; }
        .article-content font[color="purple"] { color: purple !important; }
        .article-content font[color="orange"] { color: orange !important; }
        .article-content font[color="black"] { color: black !important; }
        .article-content font[color="white"] { color: white !important; }
        .article-content font[color="gray"] { color: gray !important; }
        .article-content font[color="#000000"] { color: #000000 !important; }
        .article-content font[color="#FF0000"] { color: #FF0000 !important; }
        .article-content font[color="#00FF00"] { color: #00FF00 !important; }
        .article-content font[color="#0000FF"] { color: #0000FF !important; }
        .article-content font[color="#FFFF00"] { color: #FFFF00 !important; }
        .article-content font[color="#00FFFF"] { color: #00FFFF !important; }
        .article-content font[color="#FF00FF"] { color: #FF00FF !important; }
    </style>
"""
        
        html_template = f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
{css_links}
{prism_css}
{extra_css}
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 1200px; margin: 0 auto; background-color: #f8f9fa; }}
        img {{ max-width: 100%; height: auto; }}
        pre {{ background-color: #2d2d2d; padding: 10px; border-radius: 5px; overflow-x: auto; margin: 1em 0; }}
        code {{ font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace; }}
        pre[class*="language-"] {{ position: relative; }}
        pre[class*="language-"] .copy-to-clipboard-button {{ position: absolute; top: 5px; right: 5px; background: rgba(0,0,0,0.3); color: white; border: none; border-radius: 3px; padding: 5px 10px; font-size: 0.8em; cursor: pointer; }}
        pre[class*="language-"] .copy-to-clipboard-button:hover {{ background: rgba(0,0,0,0.5); }}
        pre[class*="language-"] code {{ user-select: all; -webkit-user-select: all; -moz-user-select: all; -ms-user-select: all; }}
        pre[class*="language-"]:hover .copy-to-clipboard-button {{ display: block; }}
        pre[class*="language-"] .copy-to-clipboard-button {{ display: none; }}
        .source-link {{ margin-bottom: 15px; color: #666; }}
        h1 {{ font-size: 28px; margin-bottom: 15px; color: #333; }}
        .article-content {{ margin-top: 25px; background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        
        /* 文章元数据样式 */
        .article-meta {{ 
            display: flex; 
            flex-wrap: wrap; 
            gap: 15px; 
            font-size: 14px; 
            color: #666; 
            margin-bottom: 15px; 
        }}
        .meta-item {{ 
            display: flex; 
            align-items: center; 
        }}
        .meta-item i {{ 
            margin-right: 5px; 
            color: #0066cc; 
        }}
        
        /* 标签样式 */
        .article-tags {{ 
            margin-bottom: 15px; 
        }}
        .tag {{ 
            display: inline-block; 
            background-color: #e6f2ff; 
            color: #0066cc; 
            padding: 3px 8px; 
            border-radius: 4px; 
            font-size: 12px; 
            margin-right: 5px; 
        }}
        
        /* 描述样式 */
        .article-description {{ 
            background-color: #f5f5f5; 
            padding: 15px; 
            border-left: 4px solid #0066cc; 
            margin-bottom: 20px; 
            font-style: italic; 
            color: #555; 
        }}
        .token.comment, .token.prolog, .token.doctype, .token.cdata {{ color: #8292a2; }}
        .token.punctuation {{ color: #f8f8f2; }}
        .token.namespace {{ opacity: .7; }}
        .token.property, .token.tag, .token.constant, .token.symbol, .token.deleted {{ color: #f92672; }}
        .token.boolean, .token.number {{ color: #ae81ff; }}
        .token.selector, .token.attr-name, .token.string, .token.char, .token.builtin, .token.inserted {{ color: #a6e22e; }}
        .token.operator, .token.entity, .token.url, .language-css .token.string, .style .token.string, .token.variable {{ color: #f8f8f2; }}
        .token.atrule, .token.attr-value, .token.function, .token.class-name {{ color: #e6db74; }}
        .token.keyword {{ color: #66d9ef; }}
        .token.regex, .token.important {{ color: #fd971f; }}
        .token.important, .token.bold {{ font-weight: bold; }}
        .token.italic {{ font-style: italic; }}
        .token.entity {{ cursor: help; }}
        
        /* 添加header和footer样式 */
        .header {{ 
            padding: 10px 0; 
            margin-bottom: 20px; 
            border-bottom: 1px solid #eee; 
        }}
        .header a {{ 
            text-decoration: none; 
            color: #007bff; 
            font-weight: bold; 
        }}
        .header a:hover {{ 
            text-decoration: underline; 
        }}
        .footer {{ 
            margin-top: 30px; 
            padding-top: 20px; 
            border-top: 1px solid #eee; 
            color: #666; 
            font-size: 0.9em; 
            text-align: center; 
        }}
    </style>
</head>
<body>
    <div class="header">
        <a href="index.html">← 返回目录</a>
    </div>
    
    <h1>{title}</h1>
    <div class="source-link">原文链接: <a href="{url}" target="_blank">{url}</a></div>
    
    <div class="article-meta">
        {f'<div class="meta-item"><i class="far fa-calendar-alt"></i> 发布时间: {publish_time}</div>' if publish_time else ''}
        {f'<div class="meta-item"><i class="far fa-eye"></i> 浏览量: {view_count}</div>' if view_count else ''}
        {f'<div class="meta-item"><i class="far fa-comment"></i> 评论数: {comment_count}</div>' if comment_count else ''}
        {f'<div class="meta-item"><i class="far fa-star"></i> 收藏数: {collect_count}</div>' if collect_count else ''}
        {f'<div class="meta-item"><i class="far fa-thumbs-up"></i> 点赞数: {digg_count}</div>' if digg_count else ''}
    </div>
    
    {f'<div class="article-tags">标签: {", ".join([f"<span class=\"tag\">{tag}</span>" for tag in tags])}</div>' if tags and len(tags) > 0 else ''}
    
    {f'<div class="article-description">{description}</div>' if description else ''}
    
    <div class="article-content">
        {content}
    </div>
    
    <div class="footer">
        <p>版本所有 tdany.com  | 发表时间: {publish_time if publish_time else time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
{prism_js}
    <script>
        // 处理代码块，添加语言类和复制功能
        document.addEventListener('DOMContentLoaded', function() {{            
            // 为没有指定语言的代码块添加默认语言
            document.querySelectorAll('pre code:not([class*="language-"])').forEach(function(block) {{
                block.className = 'hljs language-javascript';
            }});
            
            // 确保所有代码块都有hljs类
            document.querySelectorAll('pre code[class*="language-"]:not([class*="hljs"])').forEach(function(block) {{
                block.className = 'hljs ' + block.className;
            }});
            
            // 为所有代码块添加自定义复制按钮
            document.querySelectorAll('pre').forEach(function(pre) {{
                // 创建复制按钮
                var copyButton = document.createElement('button');
                copyButton.className = 'copy-button';
                copyButton.textContent = '复制';
                copyButton.style.position = 'absolute';
                copyButton.style.top = '5px';
                copyButton.style.right = '5px';
                copyButton.style.background = 'rgba(0,0,0,0.3)';
                copyButton.style.color = 'white';
                copyButton.style.border = 'none';
                copyButton.style.borderRadius = '3px';
                copyButton.style.padding = '5px 10px';
                copyButton.style.fontSize = '0.8em';
                copyButton.style.cursor = 'pointer';
                copyButton.style.display = 'none';
                
                // 鼠标悬停时显示按钮
                pre.addEventListener('mouseenter', function() {{
                    copyButton.style.display = 'block';
                }});
                
                pre.addEventListener('mouseleave', function() {{
                    copyButton.style.display = 'none';
                }});
                
                // 点击复制按钮时复制代码
                copyButton.addEventListener('click', function() {{
                    var code = pre.querySelector('code');
                    var text = code.textContent || code.innerText;
                    
                    // 使用现代的 Clipboard API
                    if (navigator.clipboard && navigator.clipboard.writeText) {{
                        navigator.clipboard.writeText(text)
                            .then(function() {{
                                copyButton.textContent = '已复制!';
                                setTimeout(function() {{
                                    copyButton.textContent = '复制';
                                }}, 2000);
                            }})
                            .catch(function(err) {{
                                console.error('Clipboard API 复制失败:', err);
                                // 如果 Clipboard API 失败，尝试使用传统方法
                                fallbackCopyToClipboard();
                            }});
                    }} else {{
                        // 对于不支持 Clipboard API 的浏览器，使用传统方法
                        fallbackCopyToClipboard();
                    }}
                    
                    // 传统复制方法作为后备
                    function fallbackCopyToClipboard() {{
                        // 创建临时文本区域
                        var textArea = document.createElement('textarea');
                        textArea.value = text;
                        textArea.style.position = 'fixed';
                        textArea.style.left = '-9999px';
                        textArea.style.top = '0';
                        document.body.appendChild(textArea);
                        textArea.focus();
                        textArea.select();
                        
                        try {{
                            var successful = document.execCommand('copy');
                            if (successful) {{
                                copyButton.textContent = '已复制!';
                                setTimeout(function() {{
                                    copyButton.textContent = '复制';
                                }}, 2000);
                            }} else {{
                                copyButton.textContent = '复制失败';
                            }}
                        }} catch (err) {{
                            copyButton.textContent = '复制失败';
                            console.error('传统复制方法失败:', err);
                        }}
                        
                        document.body.removeChild(textArea);
                    }}
                }});
                
                // 添加按钮到代码块
                pre.style.position = 'relative';
                pre.appendChild(copyButton);
            }});
            
            // 确保Prism重新高亮所有代码块
            if (typeof Prism !== 'undefined') {{
                Prism.highlightAll();
            }}
        }});
    </script>
</body>
</html>
'''
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_template)
        print(f"已生成HTML文件: {output_file}")
        return True
    except Exception as e:
        print(f"生成HTML文件时出错: {e}")
        return False

def generate_index_html(output_dir, article_info):
    """生成索引页面，显示文章目录列表及额外信息，点击跳转到对应文章
    
    Args:
        output_dir: 输出目录
        article_info: 文章信息列表，每项包含 {filename, title, url, publish_time, description, viewCount, commentCount, collectCount, diggCount, tags}
    """
    try:
        index_html = f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSDN博客文章集合</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
        body {{  
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
            background-color: #f8f9fa;
        }}
        h1 {{  
            font-size: 28px;
            margin-bottom: 20px;
            text-align: center;
            color: #333;
        }}
        h2 {{  
            font-size: 24px;
            margin-bottom: 20px;
            color: #444;
        }}
        .search-box {{  
            margin-bottom: 20px;
        }}
        .search-box input {{  
            width: 100%;
            max-width: 500px;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
            font-size: 16px;
        }}
        .article-list {{  
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .article-item {{  
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 8px;
            background-color: #fff;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .article-item:hover {{  
            transform: translateY(-3px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        .article-title {{  
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        .article-title a {{  
            text-decoration: none;
            color: #0066cc;
        }}
        .article-title a:hover {{  
            color: #004499;
            text-decoration: underline;
        }}
        .article-description {{  
            color: #555;
            margin-bottom: 10px;
            font-size: 14px;
            line-height: 1.5;
        }}
        .article-meta {{  
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            font-size: 13px;
            color: #666;
        }}
        .meta-item {{  
            display: flex;
            align-items: center;
        }}
        .meta-item i {{  
            margin-right: 5px;
        }}
        .article-tags {{  
            margin-top: 8px;
        }}
        .tag {{  
            display: inline-block;
            background-color: #e6f2ff;
            color: #0066cc;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            margin-right: 5px;
            margin-bottom: 5px;
        }}
        .publish-time {{
            color: #666;
            font-size: 0.85em;
        }}
        .footer {{ 
            margin-top: 30px; 
            padding-top: 20px; 
            border-top: 1px solid #eee; 
            color: #666; 
            font-size: 0.9em; 
            text-align: center; 
        }}
    </style>
</head>
<body>
    <h1>CSDN博客文章集合</h1>
    <h2>文章目录 (共 {len(article_info)} 篇)</h2>
    <div class="search-box">
        <input type="text" id="searchInput" placeholder="搜索文章..." onkeyup="searchArticles()">
    </div>
    <div class="article-list" id="articleList">
'''

        # 添加文章列表
        for article in article_info:
            # 基本信息
            title = article["title"]
            filename = article["filename"]
            publish_time = article.get("publish_time", "")
            
            # 额外信息
            description = article.get("description", "")
            view_count = article.get("viewCount", 0)
            comment_count = article.get("commentCount", 0)
            collect_count = article.get("collectCount", 0)
            digg_count = article.get("diggCount", 0)
            tags = article.get("tags", [])
            
            # 构建文章卡片
            index_html += f'''
        <div class="article-item">
            <div class="article-title"><a href="{filename}.html">{title}</a></div>
'''
            
            # 添加描述（如果有）
            if description:
                # 移除HTML注释 - 使用更严格的正则表达式
                clean_description = re.sub(r'<!--[\s\S]*?-->', '', description)
                # 移除所有HTML标签
                clean_description = re.sub(r'<[^>]*>', '', clean_description)
                # 转义剩余的HTML特殊字符
                import html
                clean_description = html.escape(clean_description)
                index_html += f'            <div class="article-description">{clean_description}</div>\n'
            
            # 添加元数据
            index_html += f'''
            <div class="article-meta">
'''
            
            # 添加发布时间
            if publish_time:
                index_html += f'                <div class="meta-item"><i class="far fa-calendar-alt"></i> {publish_time}</div>\n'
            
            # 添加浏览量
            if view_count:
                index_html += f'                <div class="meta-item"><i class="far fa-eye"></i> 浏览: {view_count}</div>\n'
            
            # 添加评论数
            if comment_count:
                index_html += f'                <div class="meta-item"><i class="far fa-comment"></i> 评论: {comment_count}</div>\n'
            
            # 添加收藏数
            if collect_count:
                index_html += f'                <div class="meta-item"><i class="far fa-star"></i> 收藏: {collect_count}</div>\n'
            
            # 添加点赞数
            if digg_count:
                index_html += f'                <div class="meta-item"><i class="far fa-thumbs-up"></i> 点赞: {digg_count}</div>\n'
            
            index_html += f'            </div>\n'
            
            # 添加标签（如果有）
            if tags and len(tags) > 0:
                index_html += f'            <div class="article-tags">\n'
                for tag in tags:
                    index_html += f'                <span class="tag">{tag}</span>\n'
                index_html += f'            </div>\n'
            
            index_html += f'        </div>\n'

        index_html += f'''
    </div>
    
    <div class="footer">
        <p>版本信息: tdany.com | 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <script>
        function searchArticles() {{
            const input = document.getElementById('searchInput');
            const filter = input.value.toUpperCase();
            const articleList = document.getElementById('articleList');
            const articles = articleList.getElementsByClassName('article-item');
            
            for (let i = 0; i < articles.length; i++) {{
                const article = articles[i];
                const title = article.querySelector('.article-title').textContent;
                const description = article.querySelector('.article-description')?.textContent || '';
                const tags = Array.from(article.querySelectorAll('.tag')).map(tag => tag.textContent).join(' ');
                
                const searchContent = (title + ' ' + description + ' ' + tags).toUpperCase();
                
                if (searchContent.indexOf(filter) > -1) {{
                    article.style.display = "";
                }} else {{
                    article.style.display = "none";
                }}
            }}
        }}
    </script>
</body>
</html>
'''

        # 写入index.html文件
        index_file = os.path.join(output_dir, "index.html")
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_html)
        print(f"已生成索引页面: {index_file}")
        return True
    except Exception as e:
        print(f"生成索引页面时出错: {e}")
        return False

def load_blogs_from_json(json_file):
    """从JSON文件加载博客列表
    
    Args:
        json_file: JSON文件路径
        
    Returns:
        (url_map, titles_map, publish_times_map, blog_info_map) - URL映射到短文件名，URL映射到原始标题，URL映射到发布时间，URL映射到博客额外信息
    """
    url_map = {}
    titles_map = {}
    publish_times_map = {}  # 存储URL到发布时间的映射
    blog_info_map = {}  # 新增：存储URL到博客额外信息的映射
    shortname_map = {}
    
    try:
        # 读取JSON文件
        with open(json_file, 'r', encoding='utf-8') as f:
            blogs = json.load(f)
        
        # 尝试读取持久化的短文件名映射
        shortname_file = os.path.join(os.path.dirname(json_file), "shortname_map.txt")
        if os.path.exists(shortname_file):
            try:
                with open(shortname_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            url, short_name = parts[0].strip(), parts[1].strip()
                            shortname_map[url] = short_name
                print(f"已加载 {len(shortname_map)} 个短文件名映射")
            except Exception as e:
                print(f"读取短文件名映射文件时出错: {e}")
        
        # 处理博客列表
        for index, blog in enumerate(blogs):
            url = blog.get('url')
            title = blog.get('title')
            post_time = blog.get('postTime')  # 从JSON中获取发布时间
            
            if url and title:
                # 使用已存在的短文件名或生成新的
                if url in shortname_map:
                    short_name = shortname_map[url]
                else:
                    # 获取已存在的短文件名集合用于排重
                    existing_shortnames = set(shortname_map.values())
                    short_name = generate_short_name(index, existing_shortnames)
                    shortname_map[url] = short_name
                
                print(f"加入处理列表 {title} 短文件名 {short_name} {url}")
                url_map[short_name] = url
                titles_map[url] = title
                if post_time:  # 如果有发布时间，保存到映射中
                    publish_times_map[url] = post_time
                
                # 提取额外的博客信息
                description = blog.get('description')
                # 如果描述中包含HTML注释或标签，进行清理
                if description:
                    # 移除HTML注释 - 使用更严格的正则表达式
                    description = re.sub(r'<!--[\s\S]*?-->', '', description)
                    # 移除所有HTML标签
                    description = re.sub(r'<[^>]*>', '', description)
                    # 转义剩余的HTML特殊字符
                    import html
                    description = html.escape(description)
                
                blog_info = {
                    'description': description,
                    'viewCount': blog.get('viewCount'),
                    'commentCount': blog.get('commentCount'),
                    'collectCount': blog.get('collectCount'),
                    'diggCount': blog.get('diggCount'),
                    'tags': blog.get('tags')
                }
                blog_info_map[url] = blog_info
        
        # 保存短文件名映射
        try:
            with open(shortname_file, 'w', encoding='utf-8') as f:
                f.write("# URL=短文件名映射，请勿手动修改\n")
                for url, short_name in shortname_map.items():
                    f.write(f"{url}={short_name}\n")
            print(f"已保存 {len(shortname_map)} 个短文件名映射到 {shortname_file}")
        except Exception as e:
            print(f"保存短文件名映射文件时出错: {e}")
            
        return url_map, titles_map, publish_times_map, blog_info_map
    except Exception as e:
        print(f"读取博客列表JSON文件时出错: {e}")
        return {}, {}, {}, {}
# 定义排序和生成索引的函数
def sort_and_generate_index(blog_info_map, url_map, titles_map, publish_times_map, output_directory):
    """按发布时间排序文章列表并生成索引页面
    
        Args:
        blog_info_map: URL到博客额外信息的映射
        url_map: 短文件名到URL的映射
        titles_map: URL到标题的映射
        publish_times_map: URL到发布时间的映射
        output_directory: 输出目录
    """

    articles = []
    
    # 创建URL到短文件名的反向映射
    url_to_short_name = {url: short_name for short_name, url in url_map.items()}
    
    # 先遍历blog_info_map生成articles列表
    for url, blog_info in blog_info_map.items():
        # 检查URL是否在url_map中（通过反向映射）
        if url in url_to_short_name:
            short_name = url_to_short_name[url]
            
            # 收集文章信息用于生成索引页
            article_data = {
                "filename": short_name,
                "title": titles_map.get(url, ""),
                "url": url,
                "publish_time": publish_times_map.get(url),
                "description": blog_info.get("description"),
                "viewCount": blog_info.get("viewCount"),
                "commentCount": blog_info.get("commentCount"),
                "collectCount": blog_info.get("collectCount"),
                "diggCount": blog_info.get("diggCount"),
                "tags": blog_info.get("tags")
            }
            
            articles.append(article_data)
    
    # 处理不在blog_info_map中但在url_map中的URL
    for short_name, url in url_map.items():
        # 如果URL不在blog_info_map中，添加基本信息
        if url not in blog_info_map:
            article_data = {
                "filename": short_name,
                "title": titles_map.get(url, ""),
                "url": url,
                "publish_time": publish_times_map.get(url)
            }
            
            articles.append(article_data)
        
    # 按发布时间排序，如果没有发布时间则放在最后
    # 使用自定义排序函数处理None值
    def sort_by_time(x):
        time = x.get("publish_time")
        return time if time is not None else ""
    
    articles.sort(key=sort_by_time, reverse=True)
    generate_index_html(output_directory, articles)


def main():
    import argparse
    
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='CSDN博客文章抓取工具')
    parser.add_argument('-c', '--config', help='配置文件路径', required=False)
    parser.add_argument('-j', '--json', help='博客列表JSON文件路径', required=False)
    parser.add_argument('-o', '--output', help='输出目录', default=os.path.join(os.getcwd(), "output"))
    parser.add_argument('--only-index', action='store_true', help='只生成索引页面')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 如果没有提供配置文件和JSON文件，生成示例HTML文件
    if  not args.json:
        print("注意: 未提供配置文件或博客列表JSON文件，将自动生成示例HTML文件")
        return
    
    output_dir = args.output
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    
    # 读取URL和文件名映射
    publish_times_map = {}  # 存储URL到发布时间的映射
    blog_info_map = {}  # 存储URL到博客额外信息的映射
 
    # 从JSON文件加载博客列表
    url_map, titles_map, publish_times_map, blog_info_map = load_blogs_from_json(args.json)

    if not url_map:
        print("未找到博客URL")
        return
    
    sort_and_generate_index(blog_info_map, url_map, titles_map, publish_times_map, output_dir)

    # 如果只需要生成索引页面
    if args.only_index:
        return
    
    success = False

    for short_name, url in url_map.items():
        # 确保文件名有.html后缀
        filename_html = f"{short_name}.html"
        output_file = os.path.join(output_dir, filename_html)
        
        # 获取HTML内容
        html_content = fetch_html_content(url)
        if not html_content:
            continue
        
        # 提取博客内容并下载图片和CSS
        title, blog_content, css_paths, html_publish_time = extract_blog_content(html_content, output_dir, short_name, url)
        if not blog_content:
            continue
        
        # 使用原始标题（如果存在）
        original_title = titles_map.get(url, title)
        
        # 优先使用JSON中的发布时间，如果没有则使用从HTML中提取的时间
        publish_time = publish_times_map.get(url, html_publish_time)
        
        # 获取额外的博客信息
        view_count = None
        comment_count = None
        collect_count = None
        digg_count = None
        tags = None
        description = None
        
        if url in blog_info_map:
            blog_info = blog_info_map[url]
            view_count = blog_info.get("viewCount")
            comment_count = blog_info.get("commentCount")
            collect_count = blog_info.get("collectCount")
            digg_count = blog_info.get("diggCount")
            tags = blog_info.get("tags")
            description = blog_info.get("description")
        
        # 生成HTML文件
        generate_html(title, blog_content, url, output_file, css_paths, publish_time,
                        view_count, comment_count, collect_count, digg_count, tags, description)
    

if __name__ == "__main__":
    main()