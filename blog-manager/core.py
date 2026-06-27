"""
Blog Manager - 核心功能模块
"""

import os
import sys
import json
import shutil
import subprocess
import re
import webbrowser
import threading
import time
from datetime import datetime

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config():
    default = {
        "repo_path": "",
        "remote_url": "",
        "branch": "main",
        "git_name": "maojunzc",
        "git_email": "",
        "typora_path": "",
        "default_tags": "技术,教程,生活",
        "default_categories": "默认",
        "enable_auto_push": True,
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                default.update(json.load(f))
            except json.JSONDecodeError:
                pass
    return default


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def run_git(cmd, cwd):
    """执行 git 命令"""
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        result = type('obj', (object,), {'returncode': 1, 'stdout': '', 'stderr': '超时'})()
        return result
    except FileNotFoundError:
        result = type('obj', (object,), {'returncode': 1, 'stdout': '', 'stderr': 'Git 未安装或不在 PATH 中'})()
        return result


def get_git_status(repo_path):
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        return {"valid": False, "msg": "不是有效的 Git 仓库"}

    result = run_git(["git", "status", "--short"], repo_path)
    untracked = len([l for l in result.stdout.split("\n") if l.strip()]) if result.stdout else 0

    result2 = run_git(["git", "rev-list", "--count", "HEAD"], repo_path)
    commits = result2.stdout.strip() if result2.stdout else "0"

    config = load_config()
    branch = config.get("branch", "main")
    result3 = run_git(["git", "rev-list", "--count", f"HEAD..origin/{branch}"], repo_path)
    unpushed = result3.stdout.strip() if result3.stdout else "0"
    if not unpushed.isdigit():
        unpushed = "?"

    # 获取当前分支名
    result4 = run_git(["git", "branch", "--show-current"], repo_path)
    current_branch = result4.stdout.strip() if result4.stdout else branch

    return {
        "valid": True,
        "untracked": untracked,
        "commits": commits,
        "unpushed": unpushed,
        "branch": current_branch
    }


def get_articles(repo_path):
    posts_dir = os.path.join(repo_path, "source", "_posts")
    articles = []
    if os.path.isdir(posts_dir):
        for f in sorted(os.listdir(posts_dir), reverse=True):
            if f.endswith(".md"):
                fp = os.path.join(posts_dir, f)
                try:
                    stat = os.stat(fp)
                    title = os.path.splitext(f)[0]
                    with open(fp, "r", encoding="utf-8") as fh:
                        for line in fh:
                            if line.startswith("title:"):
                                title = line.split(":", 1)[1].strip()
                                break
                    articles.append({
                        "file": f,
                        "path": fp,
                        "title": title,
                        "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                        "size": stat.st_size
                    })
                except (OSError, UnicodeDecodeError):
                    continue
    return articles


def generate_front_matter(title, tags, categories, date_str=None):
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = ["---"]
    lines.append(f"title: {title}")
    lines.append(f"date: {date_str}")
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    cat_list = [c.strip() for c in categories.split(",") if c.strip()]
    if tag_list:
        lines.append("tags:")
        for t in tag_list:
            lines.append(f"  - {t}")
    if cat_list:
        lines.append("categories:")
        for c in cat_list:
            lines.append(f"  - {c}")
    lines.append("---")
    return "\n".join(lines)


def publish_article(file_path, repo_path, remote_url, branch, git_name, git_email):
    """发布文章"""
    posts_dir = os.path.join(repo_path, "source", "_posts")
    os.makedirs(posts_dir, exist_ok=True)

    post_name = os.path.splitext(os.path.basename(file_path))[0]
    post_asset_dir = os.path.join(posts_dir, post_name)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 处理本地图片
    img_pattern = r'(!\[.*?\]\()([^)]+)\)'
    def replace_img(m):
        prefix = m.group(1)
        img_path = m.group(2)
        if img_path.startswith("http"):
            return m.group(0)
        abs_path = img_path if os.path.isabs(img_path) else os.path.join(os.path.dirname(file_path), img_path)
        if os.path.exists(abs_path):
            os.makedirs(post_asset_dir, exist_ok=True)
            shutil.copy2(abs_path, os.path.join(post_asset_dir, os.path.basename(img_path)))
            return f'{prefix}{post_name}/{os.path.basename(img_path)})'
        return m.group(0)
    content = re.sub(img_pattern, replace_img, content)

    # 写入目标
    dest = os.path.join(posts_dir, os.path.basename(file_path))
    with open(dest, "w", encoding="utf-8") as f:
        f.write(content)

    # Git 操作
    if git_name:
        run_git(["git", "config", "user.name", git_name], repo_path)
    if git_email:
        run_git(["git", "config", "user.email", git_email], repo_path)

    # 先 add 再 commit
    r1 = run_git(["git", "add", "-A"], repo_path)
    if r1.returncode != 0:
        return False, f"Git add 失败: {r1.stderr[:200]}"

    r2 = run_git(["git", "commit", "-m", f"Post: {post_name}"], repo_path)
    if r2.returncode != 0:
        return False, f"Git commit 失败: {r2.stderr[:200]}"

    # 检查是否有远程仓库再 push
    r3 = run_git(["git", "remote", "-v"], repo_path)
    if r3.stdout.strip() and remote_url:
        r4 = run_git(["git", "push", "origin", branch], repo_path)
        if r4.returncode != 0:
            return False, f"Git push 失败: {r4.stderr[:200]}"

    return True, dest


def delete_article(article, repo_path):
    """删除文章"""
    posts_dir = os.path.join(repo_path, "source", "_posts")
    md_path = os.path.join(posts_dir, article["file"])
    asset_dir = os.path.join(posts_dir, os.path.splitext(article["file"])[0])

    deleted = False
    if os.path.exists(md_path):
        os.remove(md_path)
        deleted = True
    if os.path.isdir(asset_dir):
        shutil.rmtree(asset_dir, ignore_errors=True)

    if deleted:
        title = article["title"]
        run_git(["git", "add", "-A"], repo_path)
        run_git(["git", "commit", "-m", f"Remove: {title}"], repo_path)
    return deleted
