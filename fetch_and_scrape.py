#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import argparse

def main():
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='CSDN博客获取和抓取工具')
    parser.add_argument('-u', '--username', help='CSDN用户名', required=True)
    parser.add_argument('-c', '--cookie', help='Cookie文件路径', required=True)
    parser.add_argument('-o', '--output', help='输出目录', default=os.path.join(os.getcwd(), "output"))
    parser.add_argument('-j', '--json', help='博客列表JSON文件名', default="csdn_blog_list.json")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    username = args.username
    cookie_file = args.cookie
    output_dir = args.output
    json_file = args.json
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 步骤1: 使用get_csdn_blogs.py获取博客列表
    print("步骤1: 获取CSDN博客列表...")
    get_blogs_cmd = [
        sys.executable,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "get_csdn_blogs.py"),
        username,
        cookie_file,
        json_file
    ]
    
    try:
        subprocess.run(get_blogs_cmd, check=True)
        print(f"博客列表已保存到 {json_file}")
    except subprocess.CalledProcessError as e:
        print(f"获取博客列表失败: {e}")
        sys.exit(1)
    
    # 步骤2: 使用csdn_scraper.py抓取博客内容
    print("\n步骤2: 抓取博客内容...")
    scrape_cmd = [
        sys.executable,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "csdn_scraper.py"),
        "-j", json_file,
        "-o", output_dir
    ]
    
    try:
        subprocess.run(scrape_cmd, check=True)
        print(f"博客内容已保存到 {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"抓取博客内容失败: {e}")
        sys.exit(1)
    
    print("\n全部完成! 博客内容已成功获取和抓取。")
    print(f"输出目录: {output_dir}")
    print(f"索引页面: {os.path.join(output_dir, 'index.html')}")

if __name__ == "__main__":
    main()