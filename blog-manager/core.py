"""
Blog Manager - 核心功能模块 v2.0
包含: 文章管理、图片上传(图床)、GitHub API、拖拽处理
"""

import os
import sys
import json
import shutil
import subprocess
import re
import webbrowser
import time
import base64
import urllib.request
import urllib.error
import collections
from datetime import datetime
from pathlib import Path

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


# ============ Git 结果类型 ============

GitResult = collections.namedtuple('GitResult', ['returncode', 'stdout', 'stderr'])


# ============ 配置管理 ============

DEFAULT_CONFIG = {
    "repo_path": "",
    "remote_url": "",
    "branch": "main",
    "git_name": "maojunzc",
    "remote_url": "",
    "branch": "main",
    "git_name": "maojunzc",
    "git_email": "",
    "typora_path": "",
    "default_tags": "技术,教程,生活",
    "default_categories": "默认",
    "enable_auto_push": True,
    # GitHub 图床相关（敏感字段默认留空，由用户设置页面填写）
    "github_token": "",
    "github_user": "",
    "image_host": "local",  # local / github / imgbb / smms
    "github_image_repo": "",
    "github_image_path": "images/posts",
    "imgbb_api_key": "",
    "smms_api_key": "",
    # 预览端口
    "preview_port": 4000,
    # 写作模式
    "writing_mode": "default",  # default / classic
}

def load_config():
    """加载配置，合并默认值，处理缺失键"""
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                cfg.update(saved)
        except (json.JSONDecodeError, IOError):
            pass
    return cfg

def save_config(config):
    """保存配置到文件"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ============ Git 操作 ============

def run_git(cmd, cwd):
    """执行 git 命令，返回 GitResult"""
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=60)
        return GitResult(r.returncode, r.stdout, r.stderr)
    except subprocess.TimeoutExpired:
        return GitResult(1, "", "Git命令超时（60秒）")
    except FileNotFoundError:
        return GitResult(1, "", "Git未安装或不在PATH中")
    except Exception as e:
        return GitResult(1, "", f"Git执行失败: {str(e)}")

def get_git_status(repo_path):
    """获取仓库状态信息"""
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        return {"valid": False, "msg": "不是有效的Git仓库"}

    config = load_config()
    branch = config.get("branch", "main")

    # 总提交数
    r = run_git(["git", "rev-list", "--count", "HEAD"], repo_path)
    commits = r.stdout.strip() if r.stdout.strip() else "0"

    # 未推送提交数 (对比 origin/branch)
    r2 = run_git(["git", "rev-list", "--count", f"HEAD..origin/{branch}"], repo_path)
    unpushed = r2.stdout.strip() if r2.stdout.strip() else "0"

    # 当前分支
    r3 = run_git(["git", "branch", "--show-current"], repo_path)
    current_branch = r3.stdout.strip() or branch

    # 未跟踪文件数 (仅 ?? 行)
    r4 = run_git(["git", "status", "--short"], repo_path)
    untracked = 0
    if r4.stdout:
        for line in r4.stdout.split("\n"):
            if line.startswith("??"):
                untracked += 1

    return {
        "valid": True,
        "untracked": untracked,
        "commits": commits,
        "unpushed": unpushed,
        "branch": current_branch,
    }


# ============ 文章管理 ============

def get_articles(repo_path):
    """扫描 source/_posts/ 下的所有 .md 文章"""
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
                        "size": stat.st_size,
                    })
                except Exception:
                    continue
    return articles

def generate_front_matter(title, tags, categories, date_str=None):
    """生成 Hexo YAML front-matter"""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = ["---", f"title: {title}", f"date: {date_str}"]
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

def parse_front_matter(file_path):
    """读取已有 front-matter 内容，返回 (fm_text, body_text)"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return "---" + parts[1] + "---", parts[2]
    return "", content


# ============ 图片上传 (图床) ============

def upload_to_github(image_path, config):
    """上传图片到 GitHub 仓库作为图床"""
    token = config.get("github_token", "")
    if not token:
        return False, "未配置 GitHub Token，请在设置中填写"
    
    repo = config.get("github_image_repo", "maojunzc.github.io")
    img_path = config.get("github_image_path", "images/posts")
    user = config.get("github_user", "maojunzc")
    branch = config.get("branch", "main")
    
    file_name = os.path.basename(image_path)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    remote_path = f"{img_path}/{ts}_{file_name}"
    
    # 读取图片并 base64 编码
    with open(image_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    api_url = f"https://api.github.com/repos/{user}/{repo}/contents/{remote_path}"
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json",
    }
    data = json.dumps({
        "message": f"upload: {file_name}",
        "content": content_b64,
        "branch": branch,
    }).encode("utf-8")
    
    req = urllib.request.Request(api_url, data=data, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{remote_path}"
            return True, raw_url
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")[:300]
        return False, f"GitHub API 错误 ({e.code}): {err_body}"
    except Exception as e:
        return False, f"上传失败: {str(e)[:200]}"

def upload_to_imgbb(image_path, config):
    """上传到 imgbb.com"""
    api_key = config.get("imgbb_api_key", "")
    if not api_key:
        return False, "未配置 ImgBB API Key"
    
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    data = f"key={api_key}&image={img_b64}".encode("utf-8")
    req = urllib.request.Request(
        "https://api.imgbb.com/1/upload",
        data=data,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("success"):
                return True, result["data"]["url"]
            error_msg = result.get("error", {}).get("message", "未知错误")
            return False, f"ImgBB 错误: {error_msg}"
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")[:200]
        return False, f"ImgBB HTTP错误 ({e.code}): {err_body}"
    except Exception as e:
        return False, f"ImgBB 上传失败: {str(e)[:200]}"

def upload_to_smms(image_path, config):
    """上传到 sm.ms v2 API"""
    api_key = config.get("smms_api_key", "")
    if not api_key:
        return False, "未配置 SM.MS API Key"
    
    boundary = "----SmMsBoundary7MA4YWxk"
    file_name = os.path.basename(image_path)
    ext = os.path.splitext(file_name)[1][1:].lower() or "png"
    
    with open(image_path, "rb") as f:
        file_data = f.read()
    
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="smfile"; filename="{file_name}"\r\n'
        f"Content-Type: image/{ext}\r\n\r\n"
    ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")
    
    headers = {
        "Authorization": api_key,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    
    req = urllib.request.Request(
        "https://sm.ms/api/v2/upload",
        data=body,
        headers=headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("success"):
                return True, result["data"]["url"]
            return False, f"SM.MS 错误: {result.get('message', '未知错误')}"
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")[:200]
        return False, f"SM.MS HTTP错误 ({e.code}): {err_body}"
    except Exception as e:
        return False, f"SM.MS 上传失败: {str(e)[:200]}"

def upload_image(image_path, config, progress_callback=None):
    """统一图片上传入口"""
    config = config or load_config()
    host = config.get("image_host", "local")
    
    if progress_callback:
        progress_callback(f"正在上传 ({host})...")
    
    # 检查图片文件有效性
    if not os.path.isfile(image_path):
        return False, "图片文件不存在"
    
    max_size = 10 * 1024 * 1024  # 10MB 限制
    if os.path.getsize(image_path) > max_size:
        return False, f"图片过大 ({os.path.getsize(image_path)/1024/1024:.1f}MB)，建议压缩后再上传"
    
    if host == "github":
        return upload_to_github(image_path, config)
    elif host == "imgbb":
        return upload_to_imgbb(image_path, config)
    elif host == "smms":
        return upload_to_smms(image_path, config)
    else:
        return False, f"未知图床类型: {host}"


# ============ 发布文章 ============

# 修正的正则表达式 — 标准 Markdown 图片语法 ![alt](path)
IMG_PATTERN = re.compile(r'(!\[.*?\]\()([^)]+)\)')

def process_markdown_images(content, file_dir, post_asset_dir, config, progress_callback=None):
    """
    处理 Markdown 中的本地图片
    返回: (处理后内容, 上传日志列表)
    """
    config = config or load_config()
    image_host = config.get("image_host", "local")
    upload_log = []
    
    def replace_img(m):
        alt_text = m.group(1)[2:-1]  # 去掉 ![ 和 ](
        img_path = m.group(2)
        
        # 跳过网络图片（已上传或外链）
        if img_path.startswith("http://") or img_path.startswith("https://"):
            return m.group(0)
        
        # 解析本地图片绝对路径
        abs_path = img_path
        if not os.path.isabs(img_path):
            abs_path = os.path.join(file_dir, img_path)
        
        # 文件不存在则跳过
        if not os.path.isfile(abs_path):
            return m.group(0)
        
        file_name = os.path.basename(abs_path)
        
        if image_host == "local":
            # 本地模式：复制到 post asset 目录
            os.makedirs(post_asset_dir, exist_ok=True)
            target = os.path.join(post_asset_dir, file_name)
            shutil.copy2(abs_path, target)
            new_path = os.path.relpath(target, start=post_asset_dir)
            upload_log.append(f"{'✅' if os.path.exists(target) else '⚠️'} {file_name}")
            return f'![{alt_text}]({new_path})'
        else:
            # 图床模式：上传到远程
            ok, result = upload_image(abs_path, config, progress_callback)
            if ok:
                upload_log.append(f"☁️ {file_name} → {result[:50]}...")
                return f'![{alt_text}]({result})'
            else:
                # 上传失败，回退到本地复制
                os.makedirs(post_asset_dir, exist_ok=True)
                target = os.path.join(post_asset_dir, file_name)
                shutil.copy2(abs_path, target)
                new_path = os.path.relpath(target, start=post_asset_dir)
                upload_log.append(f"⚠️ {file_name} (上传失败，已回退本地): {result[:50]}")
                return f'![{alt_text}]({new_path})'
    
    content = IMG_PATTERN.sub(replace_img, content)
    return content, upload_log

def publish_article(file_path, repo_path, remote_url, branch, git_name, git_email):
    """
    完整发布流程：
    1. 读取 .md 文件
    2. 处理 front-matter（保留已有，缺失则生成）
    3. 处理图片（本地复制或图床上传）
    4. 写入 source/_posts/
    5. Git 操作
    6. 返回 (success, message, upload_log, target_path)
    """
    config = load_config()
    
    # 确保目标目录存在
    posts_dir = os.path.join(repo_path, "source", "_posts")
    os.makedirs(posts_dir, exist_ok=True)
    
    # 读取源文件
    with open(file_path, "r", encoding="utf-8") as f:
        raw_content = f.read()
    
    post_name = os.path.splitext(os.path.basename(file_path))[0]
    post_asset_dir = os.path.join(posts_dir, post_name)
    
    # 解析已有 front-matter
    existing_fm, body = parse_front_matter(file_path)
    if existing_fm:
        # 已有 front-matter，提取关键信息用于检测
        fm_text = existing_fm
    else:
        # 没有 front-matter，用文件名作为标题生成
        title = post_name.replace("-", " ").replace("_", " ")
        tags = config.get("default_tags", "技术")
        categories = config.get("default_categories", "默认")
        fm_text = generate_front_matter(title, tags, categories)
        body = raw_content.lstrip("\n")
    
    # 处理图片
    full_doc = fm_text.rstrip("---").rstrip() + "\n---\n\n" + body
    processed_content, upload_log = process_markdown_images(
        full_doc, os.path.dirname(file_path), post_asset_dir, config
    )
    
    # 写入目标
    dest = os.path.join(posts_dir, os.path.basename(file_path))
    
    # 防重复发布：如果目标已存在且内容相同则跳过
    if os.path.exists(dest):
        with open(dest, "r", encoding="utf-8") as f:
            existing = f.read()
        if existing == processed_content:
            upload_log.append("ℹ️ 内容未变更，跳过发布")
            return True, "内容未变更，跳过发布", upload_log, dest
        # 内容不同，覆盖并记录
        upload_log.append(f"⚠️ 目标文件已存在，内容已覆盖")
    
    with open(dest, "w", encoding="utf-8") as f:
        f.write(processed_content)
    
    # Git 操作
    if git_name:
        run_git(["git", "config", "user.name", git_name], repo_path)
    if git_email:
        run_git(["git", "config", "user.email", git_email], repo_path)
    
    # 先 pull 再 push，避免冲突
    r_pull = run_git(["git", "pull", "origin", branch], repo_path)
    if r_pull.returncode != 0:
        err = r_pull.stderr[:200]
        # 网络错误可以继续，但合并冲突必须中止
        if "merge conflict" in err.lower() or "conflict" in err.lower():
            return False, f"Git pull 冲突: {err}", upload_log, dest
        upload_log.append(f"⚠️ Git pull 警告: {err}")
    
    r1 = run_git(["git", "add", "-A"], repo_path)
    if r1.returncode != 0:
        return False, f"Git add 失败: {r1.stderr[:200]}", upload_log, dest
    
    r2 = run_git(["git", "commit", "-m", f"Post: {post_name}"], repo_path)
    if r2.returncode != 0:
        # 没有变更可提交（如上传失败导致图片回退到本地，但 JS 中已覆盖）
        if "nothing to commit" in r2.stderr.lower() or "nothing to commit" in r2.stdout.lower():
            upload_log.append(f"ℹ️ 无新变更需要提交")
        else:
            return False, f"Git commit 失败: {r2.stderr[:200]}", upload_log, dest
    
    # 推送
    if config.get("enable_auto_push", True):
        r3 = run_git(["git", "remote", "-v"], repo_path)
        push_target = remote_url or ""
        if r3.stdout.strip():
            r4 = run_git(["git", "push", "origin", branch], repo_path)
            if r4.returncode != 0:
                return False, f"Git push 失败: {r4.stderr[:200]}", upload_log, dest
    
    return True, dest, upload_log, dest


def delete_article(article, repo_path):
    """删除文章（.md 文件 + 同名 asset 目录），并 Git 提交"""
    posts_dir = os.path.join(repo_path, "source", "_posts")
    md_path = os.path.join(posts_dir, article["file"])
    asset_dir = os.path.join(posts_dir, os.path.splitext(article["file"])[0])
    
    deleted = False
    try:
        if os.path.exists(md_path):
            os.remove(md_path)
            deleted = True
        if os.path.isdir(asset_dir):
            shutil.rmtree(asset_dir, ignore_errors=True)
            if deleted:
                upload_log_msg = f"已删除 {article['file']} 及其资源目录"
            else:
                upload_log_msg = f"已删除资源目录 (文章文件不存在)"
        else:
            upload_log_msg = f"未找到资源目录" if deleted else f"文件不存在，无需删除"
    except Exception as e:
        return False, f"删除失败: {str(e)[:200]}"

    if deleted:
        title = article["title"]
        r1 = run_git(["git", "add", "-A"], repo_path)
        if r1.returncode != 0:
            return True, f"文件已删除但 Git add 失败: {r1.stderr[:200]}", upload_log_msg

        r2 = run_git(["git", "commit", "-m", f"Remove: {title}"], repo_path)
        if r2.returncode != 0:
            if "nothing to commit" in (r2.stderr + r2.stdout).lower():
                upload_log_msg += " (无变更需提交)"
            else:
                return True, f"文件已删除但 Git commit 失败: {r2.stderr[:200]}", upload_log_msg

        # push 删除
        config = load_config()
        r3 = run_git(["git", "push", "origin", config.get("branch", "main")], repo_path)
        if r3.returncode != 0:
            return True, f"文件已删除但 Git push 失败: {r3.stderr[:200]}", upload_log_msg

        return deleted, upload_log_msg


# ============ 拖拽处理 ============

def drop_file_handler(dropped_path, config):
    """处理拖拽进来的文件 (.md → 导入, 图片 → 上传到图床)"""
    if not os.path.isfile(dropped_path):
        return False, "不是有效的文件", None
    
    ext = os.path.splitext(dropped_path)[1].lower()
    
    if ext in (".md", ".markdown"):
        # 导入 .md 文件
        repo = config.get("repo_path", "")
        if not repo:
            return False, "未配置仓库路径", None
        
        posts_dir = os.path.join(repo, "source", "_posts")
        os.makedirs(posts_dir, exist_ok=True)
        
        target = os.path.join(posts_dir, os.path.basename(dropped_path))
        shutil.copy2(dropped_path, target)
        return True, f"已导入: {os.path.basename(dropped_path)}", target
    
    elif ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
        # 上传图片到图床
        ok, result = upload_image(dropped_path, config)
        if ok:
            return True, f"图片已上传: {result}", result
        else:
            return False, f"图片上传失败: {result}", None
    
    else:
        return False, f"不支持的文件类型: {ext}", None
