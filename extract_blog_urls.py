#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
从CSDN博客列表HTML文件中提取博客URL并保存为配置文件
'''

import os
import re
import sys
from bs4 import BeautifulSoup
import unicodedata

def extract_blog_urls(html_file):
    """从HTML文件中提取博客URL和标题"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        blog_entries = []
        
        # 查找所有博客文章条目
        articles = soup.find_all('article', class_='blog-list-box')
        
        for article in articles:
            # 查找链接和标题
            link_tag = article.find('a')
            if link_tag and 'href' in link_tag.attrs:
                url = link_tag['href']
                
                # 查找标题
                title_tag = article.find('h4')
                if title_tag:
                    title = title_tag.text.strip()
                    blog_entries.append((title, url))
        
        return blog_entries
    except Exception as e:
        print(f"提取博客URL时出错: {e}")
        return []

def normalize_filename(title):
    """将标题转换为合适的文件名"""
    # 移除标题中的特殊字符
    title = title.strip()
    
    # 将全角字符转换为半角字符
    title = unicodedata.normalize('NFKC', title)
    
    # 替换不适合作为文件名的字符
    title = re.sub(r'[\\/:*?"<>|]', '_', title)
    title = re.sub(r'\s+', '_', title)  # 将空白字符替换为下划线
    
    # 限制文件名长度
    if len(title) > 50:
        title = title[:50]
    
    return title

def save_to_config(blog_entries, output_file):
    """将博客条目保存为配置文件"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 从CSDN博客列表自动提取的URL配置文件\n")
            f.write("# 格式：文件名=URL\n\n")
            
            for title, url in blog_entries:
                filename = normalize_filename(title)
                f.write(f"{filename}={url}\n")
        
        print(f"已成功提取 {len(blog_entries)} 个博客URL并保存到 {output_file}")
        return True
    except Exception as e:
        print(f"保存配置文件时出错: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        html_file = "/Volumes/evo2T/src/myblog/navlist.txt"  # 默认HTML文件路径
        output_file = "/Volumes/evo2T/src/myblog/urls.txt"  # 默认输出文件路径
    else:
        html_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "/Volumes/evo2T/src/myblog/urls.txt"
    
    if not os.path.exists(html_file):
        print(f"错误: HTML文件 '{html_file}' 不存在")
        return
    
    blog_entries = extract_blog_urls(html_file)
    if blog_entries:
        save_to_config(blog_entries, output_file)
    else:
        print("未找到博客条目")

if __name__ == "__main__":
    main()