# CSDN博客获取和抓取工具

这个工具结合了 `get_csdn_blogs.py` 和 `csdn_scraper.py` 的功能，实现了一站式获取CSDN博客列表并抓取博客内容的功能。

## 功能特点

1. 自动获取指定CSDN用户的所有博客文章列表
2. 自动抓取每篇博客的内容，包括文本、代码和图片
3. 生成静态HTML文件，保留原文格式和样式
4. 创建索引页面，方便浏览所有文章

## 使用方法

### 准备工作

1. 确保已安装Python 3.6+
2. 确保已安装所需依赖库：`requests`, `beautifulsoup4`
3. 准备好包含CSDN Cookie的文本文件

### 运行命令

```bash
python fetch_and_scrape.py -u <CSDN用户名> -c <Cookie文件路径> [-o <输出目录>] [-j <JSON文件名>]
```

参数说明：
- `-u, --username`: CSDN用户名（必需）
- `-c, --cookie`: Cookie文件路径（必需）
- `-o, --output`: 输出目录，默认为当前目录下的 "output" 文件夹
- `-j, --json`: 博客列表JSON文件名，默认为 "csdn_blog_list.json"

### 示例

```bash
python fetch_and_scrape.py -u aerror -c cookie.txt -o ./my_blogs
```

## 工作流程

1. 首先调用 `get_csdn_blogs.py` 获取博客列表，保存为JSON文件
2. 然后调用 `csdn_scraper.py` 读取JSON文件，抓取每篇博客的内容
3. 生成HTML文件和索引页面

## 输出结果

- 每篇博客生成一个HTML文件，使用短文件名（如a.html, b.html等）
- 博客中的图片保存在 `images/` 目录下
- CSS文件保存在 `css/` 目录下
- 生成 `index.html` 索引页面，按发布时间倒序排列所有文章

## 注意事项

1. Cookie文件应包含有效的CSDN登录Cookie
2. 抓取过程中会有随机延迟，避免被识别为爬虫
3. 首次运行可能需要较长时间，取决于博客数量和图片多少
4. 后续运行会重用已下载的资源，提高效率

## 单独使用组件

如果需要单独使用各组件：

1. 只获取博客列表：
   ```bash
   python get_csdn_blogs.py <用户名> <cookie文件路径> [输出文件名]
   ```

2. 只抓取博客内容（使用已有的JSON文件）：
   ```bash
   python csdn_scraper.py -j <JSON文件路径> -o <输出目录>
   ```