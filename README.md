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

集成了 Valine 评论系统、粒子动态背景、毛玻璃侧边栏等现代化交互体验。

## ✨ 特性

- 🚀 **Hexo 静态生成** — 快速、轻量、SEO 友好
- 🎨 **Ayer 主题** — 简洁优雅的卡片式设计
- 🌊 **粒子动态背景** — 鼠标交互连线特效
- 💬 **Valine 评论** — 无需后端的评论系统
- 🔍 **本地搜索** — 支持文章内容检索
- 📱 **响应式布局** — 适配移动端
- 🎵 **APlayer 音乐** — 支持音乐播放
- 🔒 **文章加密** — 支持密码保护
- 🖼️ **PhotoSwipe** — 图片点击放大浏览

## 🛠️ 技术栈

| 技术 | 说明 |
|------|------|
| [Hexo](https://hexo.io/) | 博客框架 v5.4.2 |
| [Ayer](https://github.com/shen-yu/hexo-theme-ayer) | 主题 |
| [Valine](https://valine.js.org/) | 评论系统 |
| [PhotoSwipe](https://photoswipe.com/) | 图片查看器 |
| [Typed.js](https://mattboldt.github.io/typed.js/) | 打字机特效 |
| [Pace.js](https://codebyzach.github.io/pace/) | 加载进度条 |
| [busuanzi](https://busuanzi.ibruce.info/) | 网站统计 |

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
├── index.html           # 首页（已生成静态文件）
├── about/               # 关于我
├── archives/            # 归档
├── categories/          # 分类
├── tags/                # 标签
├── friends/             # 友链
├── guestbook/           # 留言板
├── photos/              # 相册
├── css/
│   └── custom.css       # 自定义样式
├── js/
│   ├── particles.js     # 粒子背景特效
│   └── ...
└── images/              # 图片资源
```

## 🎨 前端特性

- **粒子连接线背景** — 80 个粒子动态运动，鼠标悬停产生连线交互
- **毛玻璃侧边栏** — backdrop-filter 模糊效果，现代感 UI
- **打赏二维码** — 发光边框 + 悬停放大旋转动效
- **自定义滚动条** — 渐变色彩，圆角设计
- **导航动画** — hover 下滑线滑动 + 渐变过渡
- **卡片悬停** — 文章卡片浮起阴影效果
- **页面过渡** — 内容淡入上滑动画
- **爱心心跳** — footer 图标持续心跳动画

## 📄 许可证

[MIT](LICENSE)

---

<div align="center">
  <sub>Built with ❤️ by maojunzc</sub>
</div>
