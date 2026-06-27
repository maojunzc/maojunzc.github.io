"""
Blog Publisher - 一键发布 Markdown 文章到 Hexo 博客
=================================================
功能：
  1. 读取 .md 文件，自动添加 Hexo Front-matter
  2. 处理图片路径（复制到 source/_posts/）
  3. Git add / commit / push
  4. 本地预览
  5. 右键菜单集成

用法：
  python blog_publisher.py <markdown_file>
"""

import os
import sys
import json
import shutil
import subprocess
import re
import webbrowser
from datetime import datetime
from pathlib import Path


# ============ 配置 ============

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    """加载配置文件"""
    default_config = {
        "repo_path": "",
        "remote_url": "",
        "branch": "main",
        "default_tags": [],
        "default_categories": [],
        "author": "maojunzc",
        "git_name": "maojunzc",
        "git_email": "",
        "enable_preview": True
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            default_config.update(config)
    return default_config


# ============ Front-matter 生成 ============

def has_front_matter(content):
    """检查是否已有 Front-matter"""
    return content.strip().startswith("---")


def parse_existing_front_matter(content):
    """解析已存在的 Front-matter (例如 Typora 的)"""
    if not has_front_matter(content):
        return None, content
    
    lines = content.split("\n")
    if len(lines) < 2:
        return None, content
    
    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    
    if end_idx == -1:
        return None, content
    
    fm_text = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1:])
    
    # 提取已有字段
    fm = {}
    for line in fm_text.split("\n"):
        line = line.strip()
        if ":" in line:
            key, value = line.split(":", 1)
            fm[key.strip().lower()] = value.strip()
    
    return fm, body


def generate_front_matter(title, date_str=None, tags=None, categories=None):
    """生成 Hexo Front-matter"""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if tags is None:
        tags = []
    if categories is None:
        categories = []
    
    lines = ["---"]
    lines.append(f"title: {title}")
    lines.append(f"date: {date_str}")
    
    if tags:
        lines.append("tags:")
        for tag in tags:
            lines.append(f"  - {tag}")
    
    if categories:
        lines.append("categories:")
        for cat in categories:
            lines.append(f"  - {cat}")
    
    lines.append("---")
    return "\n".join(lines)


def process_markdown(file_path, config):
    """处理 Markdown 文件，添加/更新 Front-matter"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 提取标题（从文件名或已有 Front-matter）
    basename = os.path.splitext(os.path.basename(file_path))[0]
    
    existing_fm, body = parse_existing_front_matter(content)
    
    if existing_fm:
        # 保留已有信息，补充缺失字段
        title = existing_fm.get("title", basename)
        date_str = existing_fm.get("date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # 解析已有标签
        existing_tags = config.get("default_tags", [])
        if "tags" in existing_fm:
            # tags 可能是单行或多行
            pass  # 保持原样
        
        fm = generate_front_matter(title, date_str, config.get("default_tags", []), config.get("default_categories", []))
    else:
        title = basename
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fm = generate_front_matter(title, date_str, config.get("default_tags", []), config.get("default_categories", []))
    
    # 组合
    result = fm + "\n" + body
    
    return result, title, date_str


# ============ 图片处理 ============

def process_images(content, md_file_path, source_dir):
    """
    处理文章中的图片引用：
    - 如果图片是本地路径，复制到 source/_posts/<post_name>/ 下
    """
    post_name = os.path.splitext(os.path.basename(md_file_path))[0]
    post_asset_dir = os.path.join(source_dir, "_posts", post_name)
    
    # 匹配 Markdown 图片 ![](path) 和 HTML 图片 <img src="path">
    img_pattern = r'(!\[.*?\]\()([^)]+)\)'
    html_img_pattern = r'(<img[^>]*src=")([^"]+)("[^>]*>)'
    
    md_updated = content
    images_copied = []
    
    # 处理 Markdown 图片语法
    def replace_md_img(match):
        prefix = match.group(1)
        img_path = match.group(2)
        
        # 跳过网络图片
        if img_path.startswith("http://") or img_path.startswith("https://") or img_path.startswith("//"):
            return match.group(0)
        
        if os.path.isabs(img_path):
            abs_path = img_path
        else:
            abs_path = os.path.join(os.path.dirname(md_file_path), img_path)
        
        if os.path.exists(abs_path):
            os.makedirs(post_asset_dir, exist_ok=True)
            target = os.path.join(post_asset_dir, os.path.basename(img_path))
            shutil.copy2(abs_path, target)
            images_copied.append((abs_path, target))
            # 返回相对路径
            return f'{prefix}{post_name}/{os.path.basename(img_path)})'
        
        return match.group(0)
    
    md_updated = re.sub(img_pattern, replace_md_img, md_updated)
    
    # 处理 HTML 图片语法
    def replace_html_img(match):
        prefix = match.group(1)
        img_path = match.group(2)
        suffix = match.group(3)
        
        if img_path.startswith("http://") or img_path.startswith("https://") or img_path.startswith("//"):
            return match.group(0)
        
        if os.path.isabs(img_path):
            abs_path = img_path
        else:
            abs_path = os.path.join(os.path.dirname(md_file_path), img_path)
        
        if os.path.exists(abs_path):
            os.makedirs(post_asset_dir, exist_ok=True)
            target = os.path.join(post_asset_dir, os.path.basename(img_path))
            shutil.copy2(abs_path, target)
            images_copied.append((abs_path, target))
            return f'{prefix}{post_name}/{os.path.basename(img_path)}"{suffix}'
        
        return match.group(0)
    
    md_updated = re.sub(html_img_pattern, replace_html_img, md_updated)
    
    return md_updated, images_copied


# ============ Git 操作 ============

def git_operation(repo_path, md_file_path, title, remote_url, branch, git_name="", git_email=""):
    """执行 Git add / commit / push"""
    os.chdir(repo_path)
    
    # 检查是否是 git 仓库
    if not os.path.exists(os.path.join(repo_path, ".git")):
        subprocess.run(["git", "init"], check=True)
        if remote_url:
            subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
    
    # 设置 git 用户信息
    if git_name:
        subprocess.run(["git", "config", "user.name", git_name], capture_output=True)
    if git_email:
        subprocess.run(["git", "config", "user.email", git_email], capture_output=True)
    
    # 复制 md 文件到 source/_posts/
    source_posts = os.path.join(repo_path, "source", "_posts")
    os.makedirs(source_posts, exist_ok=True)
    
    dest_md = os.path.join(source_posts, os.path.basename(md_file_path))
    shutil.copy2(md_file_path, dest_md)
    
    # Add
    result = subprocess.run(["git", "add", "-A"], capture_output=True, text=True)
    if result.returncode != 0:
        return False, f"Git add 失败: {result.stderr}"
    
    # Commit
    commit_msg = f"Post: {title}"
    result = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
    if result.returncode != 0:
        return False, f"Git commit 失败: {result.stderr}"
    
    # Push
    result = subprocess.run(["git", "push", "origin", branch], capture_output=True, text=True)
    if result.returncode != 0:
        return False, f"Git push 失败: {result.stderr}"
    
    return True, dest_md


# ============ 预览 ============

def preview(repo_path):
    """在浏览器中预览博客"""
    # 尝试 hexo server，如果不行就打开 GitHub Pages
    hexo_path = shutil.which("hexo")
    if hexo_path:
        os.chdir(repo_path)
        subprocess.Popen(["hexo", "server", "--open"], shell=True)
    else:
        # 直接打开 GitHub Pages
        webbrowser.open("https://maojunzc.github.io")


# ============ 主流程 ============

def main():
    if len(sys.argv) < 2:
        print("用法: python blog_publisher.py <markdown_file>")
        print("       python blog_publisher.py install    # 安装右键菜单")
        print("       python blog_publisher.py uninstall  # 卸载右键菜单")
        sys.exit(1)
    
    command = sys.argv[1]
    config = load_config()
    
    if command == "install":
        install_context_menu()
        return
    elif command == "uninstall":
        uninstall_context_menu()
        return
    
    md_file = command
    if not os.path.exists(md_file):
        print(f"错误: 文件不存在 - {md_file}")
        sys.exit(1)
    
    if not md_file.lower().endswith(".md"):
        print("错误: 请选择 .md 文件")
        sys.exit(1)
    
    repo_path = config.get("repo_path", "")
    if not repo_path or not os.path.exists(repo_path):
        print(f"错误: 仓库路径不存在，请在 config.json 中设置 repo_path")
        sys.exit(1)
    
    source_dir = os.path.join(repo_path, "source")
    
    print(f"📄 处理文件: {md_file}")
    
    # 1. 处理 Markdown
    result_content, title, date_str = process_markdown(md_file, config)
    
    # 2. 处理图片
    result_content, images = process_images(result_content, md_file, source_dir)
    
    if images:
        print(f"🖼️  已复制 {len(images)} 张图片")
    
    # 3. 写入处理后的文件
    temp_md = md_file  # 直接覆盖原文件
    with open(temp_md, "w", encoding="utf-8") as f:
        f.write(result_content)
    print(f"✅ Front-matter 已添加")
    
    # 4. Git 操作
    print(f"📤 推送到 GitHub...")
    success, result = git_operation(
        repo_path, temp_md, title,
        config.get("remote_url", ""),
        config.get("branch", "main"),
        config.get("git_name", ""),
        config.get("git_email", "")
    )
    
    if success:
        print(f"✅ 发布成功! 文章已提交到 {config.get('branch', 'main')} 分支")
        print(f"   → {result}")
        
        # 5. 预览
        if config.get("enable_preview", True):
            print(f"🌐 正在打开预览...")
            preview(repo_path)
    else:
        print(f"❌ 发布失败: {result}")
        sys.exit(1)


# ============ 右键菜单 ============

def install_context_menu():
    """注册右键菜单"""
    script_path = os.path.abspath(__file__)
    icon_path = os.path.join(os.path.dirname(script_path), "blog-icon.ico")
    
    reg_content = f"""Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.md\\shell\\BlogPublisher]
@="上传到博客"
"Icon"="\"{icon_path}\""

[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.md\\shell\\BlogPublisher\\command]
@="\\"python\\" \\"{script_path}\\" \\"%1\\""
"""
    reg_file = os.path.join(os.path.dirname(script_path), "install_context_menu.reg")
    with open(reg_file, "w", encoding="utf-16le") as f:
        # reg 文件需要 UTF-16 LE + BOM
        f.write("\ufeff" + reg_content)
    
    print(f"✅ 右键菜单注册表文件已生成: {reg_file}")
    print("请以管理员身份运行该 .reg 文件以注册右键菜单")
    print("或者手动运行: regedit install_context_menu.reg")


def uninstall_context_menu():
    """卸载右键菜单"""
    reg_content = """Windows Registry Editor Version 5.00

[-HKEY_CLASSES_ROOT\\SystemFileAssociations\\.md\\shell\\BlogPublisher]
"""
    reg_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uninstall_context_menu.reg")
    with open(reg_file, "w", encoding="utf-16le") as f:
        f.write("\ufeff" + reg_content)
    
    print(f"✅ 卸载注册表文件已生成: {reg_file}")
    print("请以管理员身份运行该 .reg 文件以卸载右键菜单")


if __name__ == "__main__":
    main()
