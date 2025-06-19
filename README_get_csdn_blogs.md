# CSDN博客列表获取工具

这个工具用于获取CSDN用户的博客列表数据，通过模拟浏览器请求，可以绕过CSDN的安全验证，获取完整的博客列表。

## 功能特点

- 自动分页获取所有博客数据
- 支持自定义Cookie，可绕过安全验证
- 自动处理请求延迟，避免被识别为爬虫
- 将获取的数据保存为JSON格式，方便后续处理

## 使用方法

### 准备工作

1. 确保已安装Python 3
2. 将Cookie保存到文本文件中（已提供示例文件`cookie.txt`）

### 运行脚本

```bash
python3 get_csdn_blogs.py <用户名> <cookie文件路径> [输出文件名]
```

参数说明：
- `<用户名>`: CSDN用户名，例如 `aerror`
- `<cookie文件路径>`: 包含Cookie的文本文件路径
- `[输出文件名]`: 可选，输出的JSON文件名，默认为 `blog_list.json`

示例：

```bash
python3 get_csdn_blogs.py aerror cookie.txt csdn_blog_list.json
```

### 获取Cookie

1. 使用浏览器登录CSDN
2. 打开开发者工具（F12或右键检查）
3. 切换到Network标签页
4. 刷新页面，找到任意一个请求
5. 在请求头中找到Cookie字段，复制其值
6. 将复制的Cookie值保存到文本文件中

## 输出格式

脚本输出的JSON文件包含博客列表数据，每篇博客的信息包括：

- `articleId`: 文章ID
- `title`: 文章标题
- `description`: 文章描述
- `url`: 文章URL
- `type`: 文章类型
- `viewCount`: 浏览次数
- `commentCount`: 评论数
- `postTime`: 发布时间
- `diggCount`: 点赞数
- `collectCount`: 收藏数
- `tags`: 标签列表
- 等等

## 注意事项

- Cookie有效期有限，如果获取失败，请更新Cookie
- 请合理使用，避免频繁请求对CSDN服务器造成压力
- 获取的数据仅用于个人学习和备份，请勿用于商业用途