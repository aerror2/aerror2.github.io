#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import json
import sys
import time
import random
import os

def get_blog_list(username, page, size, cookie):
    """使用curl命令获取CSDN博客列表
    
    Args:
        username: CSDN用户名
        page: 页码
        size: 每页条数
        cookie: Cookie字符串
        
    Returns:
        返回获取到的JSON数据
    """
    url = f'https://blog.csdn.net/community/home-api/v1/get-business-list?page={page}&size={size}&businessType=blog&orderby=&noMore=false&year=&month=&username={username}'
    
    # 构建curl命令
    curl_cmd = [
        'curl', url,
        '-X', 'GET',
        '-H', 'Accept: application/json, text/plain, */*',
        '-H', 'Sec-Fetch-Site: same-origin',
        '-H', f'Cookie: {cookie}',
        '-H', 'Referer: https://blog.csdn.net/aerror?type=blog',
        '-H', 'Sec-Fetch-Dest: empty',
        '-H', 'Accept-Language: zh-CN,zh-Hans;q=0.9',
        '-H', 'Sec-Fetch-Mode: cors',
        '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.4 Safari/605.1.15',
        '-H', 'Accept-Encoding: deflate',
        '-H', 'Connection: keep-alive',
        '-H', 'Priority: u=3, i'
    ]
    
    try:
        # 执行curl命令
        result = subprocess.run(curl_cmd, capture_output=True, text=True, check=True)
        
        # 解析JSON响应
        try:
            response_data = json.loads(result.stdout)
            return response_data
        except json.JSONDecodeError:
            print(f"无法解析JSON响应: {result.stdout}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"执行curl命令失败: {e}")
        print(f"错误输出: {e.stderr}")
        return None

def save_to_file(data, filename):
    """将数据保存到文件
    
    Args:
        data: 要保存的数据
        filename: 文件名
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"数据已保存到 {filename}")

def main():
    if len(sys.argv) < 3:
        print("用法: python get_csdn_blogs.py <用户名> <cookie文件路径> [输出文件名]")
        sys.exit(1)
    
    username = sys.argv[1]
    cookie_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else "blog_list.json"
    
    # 读取cookie
    try:
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookie = f.read().strip()
    except Exception as e:
        print(f"读取cookie文件失败: {e}")
        sys.exit(1)
    
    page = 1
    size = 20
    all_blogs = []
    
    while True:
        print(f"正在获取第 {page} 页数据...")
        
        # 添加随机延迟，避免被识别为爬虫
        delay = random.uniform(1, 3)
        print(f"等待 {delay:.2f} 秒...")
        time.sleep(delay)
        
        # 获取博客列表
        response = get_blog_list(username, page, size, cookie)
        
        if not response or 'data' not in response or 'list' not in response['data'] or not response['data']['list']:
            print(f"第 {page} 页没有数据或返回为空，停止获取")
            break
        
        # 添加到总列表
        blogs = response['data']['list']
        all_blogs.extend(blogs)
        print(f"获取到 {len(blogs)} 条博客数据")
        
        # 如果返回的数据少于请求的size，说明已经到最后一页
        if len(blogs) < size:
            print("已到达最后一页，停止获取")
            break
        
        page += 1
    
    print(f"共获取到 {len(all_blogs)} 条博客数据")
    
    # 保存数据
    save_to_file(all_blogs, output_file)

if __name__ == "__main__":
    main()