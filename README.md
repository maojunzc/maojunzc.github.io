<div align="center">
  <img src="https://maojunzc.github.io/images/ayer.svg" width="120" alt="maojunzc">
  <h1 align="center">maojunzc.github.io</h1>
  <p align="center">个人博客 · 技术分享 · 资源整合</p>
  <p align="center">
    <a href="https://maojunzc.github.io">🌐 在线访问</a>
    ·
    <a href="https://github.com/maojunzc/maojunzc.github.io">📦 GitHub 仓库</a>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/Hexo-5.4-blue?logo=hexo">
    <img src="https://img.shields.io/badge/Theme-Ayer-ff6b6b">
    <img src="https://img.shields.io/badge/license-MIT-green">
  </p>
</div>

---

## 📖 简介

基于 **Hexo** 构建的个人博客网站，托管于 **GitHub Pages**，使用 [Ayer](https://github.com/shen-yu/hexo-theme-ayer) 主题。

集成了 Waline 评论系统（Vercel + Neon 部署）、粒子动态背景、毛玻璃侧边栏等现代化交互体验。附带 [Blog Manager](#-blog-manager) 桌面工具，支持一键发布文章、图片上传（多图床）、Git 自动管理等。

## ✨ 特性

- 🚀 **Hexo 静态生成** — 快速、轻量、SEO 友好
- 🎨 **Ayer 主题** — 简洁优雅的卡片式设计，深度定制暗色炫酷风格
- 🌊 **粒子动态背景** — 鼠标交互连线特效
- 💬 **Waline 评论** — 自部署评论系统（Vercel + Neon PostgreSQL），支持邮件通知、GitHub 登录管理
- 🔍 **本地搜索** — 支持文章内容检索
- 📱 **响应式布局** — 适配移动端
- 🎵 **APlayer 音乐** — 支持音乐播放
- 🔒 **文章加密** — 支持密码保护
- 🖼️ **PhotoSwipe** — 图片点击放大浏览
- 🖥️ **Blog Manager** — 桌面端博客管理工具，一键发布 + 图片上传

## 🛠️ 技术栈

| 技术 | 说明 |
|------|------|
| [Hexo](https://hexo.io/) | 博客框架 v5.4.2 |
| [Ayer](https://github.com/shen-yu/hexo-theme-ayer) | 主题 |
| [Waline](https://waline.js.org/) | 评论系统（Vercel + Neon） |
| [PhotoSwipe](https://photoswipe.com/) | 图片查看器 |
| [Typed.js](https://mattboldt.github.io/typed.js/) | 打字机特效 |
| [Pace.js](https://codebyzach.github.io/pace/) | 加载进度条 |
| [busuanzi](https://busuanzi.ibruce.info/) | 网站统计 |
| [Particles.js](https://github.com/VincentGarreau/particles.js/) | 粒子背景特效 |
| [Python](https://www.python.org/) | Blog Manager 桌面工具 |

## 🚀 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/maojunzc/maojunzc.github.io.git
cd maojunzc.github.io

# 2. 安装依赖
npm install

# 3. 本地预览
hexo server

# 4. 生成静态文件
hexo generate

# 5. 部署到 GitHub Pages
hexo deploy
```

## 📁 项目结构

```
maojunzc.github.io/
├── source/              # 文章源文件 (.md)
│   └── _posts/
├── _config.yml          # Hexo 配置文件
├── index.html           # 首页
├── about/               # 关于我
├── archives/            # 归档
├── categories/          # 分类
├── tags/                # 标签
├── friends/             # 友链
├── guestbook/           # 留言板
├── photos/              # 相册
├── PMP/                 # PMP 专栏
├── maojunzc/            # 个人标签页
├── blog-manager/        # 📌 Blog Manager 桌面工具
├── css/
│   ├── custom.css       # 自定义样式（完整暗色主题覆盖）
│   └── clipboard.css
├── js/
│   ├── particles.js     # 粒子背景特效
│   ├── dz.js            # 打赏功能
│   ├── clickLove.js     # 点击爱心特效
│   ├── clickBoom1/2.js  # 点击爆炸/粒子特效
│   └── ...
├── dist/
│   └── main.css         # Ayer 主题编译样式
│   └── main.js          # Ayer 主题 JS（sidebar 切换/深色模式等）
├── lib/
│   └── hbe.js           # 文章加密
├── images/              # 图片资源（封面/二维码/素材）
├── search.xml           # 搜索索引
└── atom.xml             # RSS Feed
```

## 🎨 前端特性

- **粒子连接线背景** — 80 个粒子动态运动，鼠标悬停产生连线交互
- **毛玻璃侧边栏** — backdrop-filter 模糊效果，渐变背景
- **打赏二维码** — 发光边框 + 悬停放大旋转动效
- **自定义滚动条** — 渐变色彩，圆角设计
- **导航动画** — hover 下滑线滑动 + 渐变过渡
- **卡片悬浮** — 文章卡片浮起阴影 + 边框高亮动效
- **页面过渡** — 内容淡入上滑动画
- **爱心心跳** — footer 图标持续心跳动画
- **暗色主题** — 全站深色风格，统一视觉体验

## 🖥️ Blog Manager

位于 `blog-manager/` 目录下的桌面端博客管理工具，使用 Python + Tkinter 构建，支持 ttkbootstrap 主题。

**v3.0 零依赖设计** — 内置 Git 操作引擎 (GitPython) 和 Markdown 渲染器，无需安装 Git 命令行、Hexo CLI 或其他任何外部工具。下载 exe 即可直接使用。

### 功能特性

| 功能 | 说明 |
|------|------|
| 📝 **文章管理** | 新建、编辑、导入、删除 Markdown 文章 |
| 🚀 **一键发布** | 自动处理 front-matter、图片上传、Git 提交推送 |
| 🖼️ **多图床支持** | 本地复制 / GitHub / ImgBB / SM.MS 四种模式 |
| 📥 **拖拽导入** | 支持拖拽 .md 文件和图片到窗口 |
| ⚙️ **完整设置** | Git 远程地址、分支、图床密钥、写作模式切换 |
| 🌐 **本地预览** | 一键启动 Hexo server 预览 |
| 🎨 **写作模式** | 经典灰色白底黑字模式，专注写作 |
| 🔌 **零外部依赖** | 内置 Git 和 Markdown 引擎，无需额外安装 |

### 零依赖说明

BlogManager v3.0 已将以下功能内置到 exe 中：

- ✅ **Git 操作** — 使用 GitPython 库（打包在 exe 内），无需安装 Git 命令行
- ✅ **Markdown 渲染** — 使用 Python Markdown 库（打包在 exe 内）
- ✅ **配置管理** — 所有设置在界面上完成，不写死任何默认值
- ✅ **首次引导** — 首次运行弹窗提示配置仓库路径

> 原 v2.x 依赖 Git 命令行和 Hexo CLI，v3.0 已全部内置。

### 打包部署

```bash
cd blog-manager
pip install pyinstaller
python build.py        # 生成单文件 exe（含 UPX 压缩）
```

产物位于 `blog-manager/dist/BlogManager.exe`（约 13.5MB，v3.0 起零外部依赖）。

## 📄 许可证

[MIT](LICENSE)

---

<div align="center">
  <sub>Built with ❤️ by maojunzc</sub>
</div>
