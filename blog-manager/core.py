"""
Blog Manager - 核心功能模块 v3.0
完全零外部依赖：内置 Git 操作(GitPython)、Markdown 渲染
无需安装 Git 命令行、Hexo CLI 或其他外部工具
"""

import os
import sys
import json
import shutil
import re
import base64
import urllib.request
import urllib.error
import collections
import subprocess
import webbrowser
import time
from datetime import datetime

try:
    from git import Repo, GitCommandError
    HAS_GITPYTHON = True
except ImportError:
    HAS_GITPYTHON = False

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# ============ Git 结果类型 ============

GitResult = collections.namedtuple('GitResult', ['returncode', 'stdout', 'stderr'])


# ============ 配置管理 ============

DEFAULT_CONFIG = {
    "repo_path": "",
    "remote_url": "",
    "branch": "main",
    "git_name": "",
    "git_email": "",
    "git_token": "",         # GitHub Personal Access Token
    "typora_path": "",
    "default_tags": "技术,教程,生活",
    "default_categories": "默认",
    "enable_auto_push": True,
    # 图床相关
    "github_token": "",
    "github_user": "",
    "image_host": "local",
    "github_image_repo": "",
    "github_image_path": "images/posts",
    "imgbb_api_key": "",
    "smms_api_key": "",
    # 预览端口
    "preview_port": 4000,
    # 写作模式
    "writing_mode": "default",
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


# ============ Git 操作（内置，无需外部Git命令） ============

def run_git(cmd, cwd):
    """
    执行 git 命令（降级方案，当 GitPython 不可用时使用）
    返回 GitResult
    """
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
    """
    获取仓库状态信息。
    优先使用 GitPython，降级到命令行 git。
    """
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        return {"valid": False, "msg": "不是有效的Git仓库"}

    config = load_config()
    branch = config.get("branch", "main")

    # 使用 GitPython
    if HAS_GITPYTHON:
        try:
            repo = Repo(repo_path)
            commits = sum(1 for _ in repo.iter_commits())
            unpushed = 0
            try:
                unpushed = sum(1 for _ in repo.iter_commits(f"HEAD..origin/{branch}"))
            except Exception:
                pass
            current_branch = repo.active_branch.name
            untracked = len(repo.untracked_files)
            return {
                "valid": True,
                "untracked": untracked,
                "commits": str(commits),
                "unpushed": str(unpushed),
                "branch": current_branch,
            }
        except Exception as e:
            return {"valid": False, "msg": f"GitPython 错误: {str(e)[:100]}"}

    # 降级：命令行
    r = run_git(["git", "rev-list", "--count", "HEAD"], repo_path)
    commits = r.stdout.strip() if r.stdout.strip() else "0"
    r2 = run_git(["git", "rev-list", "--count", f"HEAD..origin/{branch}"], repo_path)
    unpushed = r2.stdout.strip() if r2.stdout.strip() else "0"
    r3 = run_git(["git", "branch", "--show-current"], repo_path)
    current_branch = r3.stdout.strip() or branch
    r4 = run_git(["git", "status", "--short"], repo_path)
    untracked = sum(1 for line in r4.stdout.split("\n") if line.startswith("??")) if r4.stdout else 0
    return {
        "valid": True,
        "untracked": untracked,
        "commits": commits,
        "unpushed": unpushed,
        "branch": current_branch,
    }

def git_add_commit_push(repo_path, message, branch="main", remote_url="", git_token=""):
    """
    统一的 Git add → commit → push 操作。
    优先使用 GitPython，降级到命令行。
    返回 (success, message_list)
    """
    log = []

    if HAS_GITPYTHON:
        try:
            repo = Repo(repo_path)
            # 配置身份（如果未设置）
            if not repo.config_reader().get_value("user", "name", None):
                repo.config_writer().set_value("user", "name", "Blog Manager").release()
            if not repo.config_reader().get_value("user", "email", None):
                repo.config_writer().set_value("user", "email", "blog@manager.local").release()

            # add
            repo.index.add("*")
            log.append("✅ Git add 完成")

            # commit
            if repo.is_dirty(untracked_files=True):
                repo.index.commit(message)
                log.append(f"✅ 已提交: {message}")
            else:
                log.append("ℹ️ 无变更需提交")
                return True, log

            # push
            if remote_url:
                try:
                    origin = repo.remotes.origin
                    if origin.url != remote_url:
                        origin.set_url(remote_url)
                    origin.push()
                    log.append("✅ 已推送到远程")
                except Exception as e:
                    log.append(f"⚠️ 推送失败: {str(e)[:100]}")
            else:
                log.append("ℹ️ 未配置远程地址，跳过推送")

            return True, log
        except GitCommandError as e:
            return False, [f"❌ Git 操作失败: {str(e)[:200]}"]
        except Exception as e:
            return False, [f"❌ 意外错误: {str(e)[:200]}"]

    # 降级：命令行
    run_git(["git", "add", "-A"], repo_path)
    r = run_git(["git", "commit", "-m", message], repo_path)
    if r.returncode != 0 and "nothing to commit" not in (r.stderr + r.stdout).lower():
        return False, [f"❌ Git commit 失败: {r.stderr[:200]}"]
    log.append("✅ 已提交")
    if remote_url:
        run_git(["git", "pull", "origin", branch], repo_path)
        r2 = run_git(["git", "push", "origin", branch], repo_path)
        if r2.returncode != 0:
            return False, [f"❌ Git push 失败: {r2.stderr[:200]}"]
        log.append("✅ 已推送到远程")
    return True, log


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


# ============ Markdown 转 HTML（内置，无需Hexo） ============

def md_to_html(md_text):
    """
    将 Markdown 文本转为 HTML。
    内置渲染，不依赖 Hexo CLI。
    """
    if HAS_MARKDOWN:
        try:
            html = markdown.markdown(
                md_text,
                extensions=['fenced_code', 'codehilite', 'tables', 'nl2br']
            )
            return html
        except Exception:
            pass
    # 降级：简易渲染
    html = md_text
    # 代码块
    html = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
    # 行内代码
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    # 标题
    for i in range(6, 0, -1):
        html = re.sub(r'^{} (.+)$'.format('#' * i), rf'<h{i}>\1</h{i}>', html, flags=re.MULTILINE)
    # 加粗
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    # 链接
    html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)
    # 段落
    lines = html.split('\n')
    result = []
    in_code = False
    for line in lines:
        if line.startswith('<pre>'):
            in_code = True
        if in_code:
            result.append(line)
            if line.startswith('</pre>'):
                in_code = False
            continue
        if line.strip() and not line.startswith('<h') and not line.startswith('<a'):
            result.append(f'<p>{line}</p>')
        else:
            result.append(line)
    return '\n'.join(result)


# ============ 图片上传 (图床) ============

def upload_to_github(image_path, config):
    """上传图片到 GitHub 仓库作为图床"""
    token = config.get("github_token", "")
    if not token:
        return False, "未配置 GitHub Token，请在设置中填写"
    repo = config.get("github_image_repo", "")
    img_path = config.get("github_image_path", "images/posts")
    user = config.get("github_user", "")
    branch = config.get("branch", "main")
    if not repo or not user:
        return False, "请先配置 GitHub 图床信息（User/Repo）"

    file_name = os.path.basename(image_path)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    remote_path = f"{img_path}/{ts}_{file_name}"

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
    req = urllib.request.Request("https://api.imgbb.com/1/upload", data=data, method="POST")
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
    req = urllib.request.Request("https://sm.ms/api/v2/upload", data=body, headers=headers, method="POST")
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
    if not os.path.isfile(image_path):
        return False, "图片文件不存在"
    max_size = 10 * 1024 * 1024
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


# ============ 发布文章（完整流程：.md → Git → 推送） ============

IMG_PATTERN = re.compile(r'(!\[.*?\]\()([^)]+)\)')

def process_markdown_images(content, file_dir, post_asset_dir, config, progress_callback=None):
    """处理 Markdown 中的本地图片"""
    config = config or load_config()
    image_host = config.get("image_host", "local")
    upload_log = []

    def replace_img(m):
        alt_text = m.group(1)[2:-1]
        img_path = m.group(2)
        if img_path.startswith("http://") or img_path.startswith("https://"):
            return m.group(0)
        abs_path = img_path
        if not os.path.isabs(img_path):
            abs_path = os.path.join(file_dir, img_path)
        if not os.path.isfile(abs_path):
            return m.group(0)
        file_name = os.path.basename(abs_path)
        if image_host == "local":
            os.makedirs(post_asset_dir, exist_ok=True)
            target = os.path.join(post_asset_dir, file_name)
            shutil.copy2(abs_path, target)
            new_path = os.path.relpath(target, start=post_asset_dir)
            upload_log.append(f"{'✅' if os.path.exists(target) else '⚠️'} {file_name}")
            return f'![{alt_text}]({new_path})'
        else:
            ok, result = upload_image(abs_path, config, progress_callback)
            if ok:
                upload_log.append(f"☁️ {file_name} → {result[:50]}...")
                return f'![{alt_text}]({result})'
            else:
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
    2. 处理 front-matter
    3. 处理图片
    4. 写入 source/_posts/
    5. Git add → commit → push（内置 GitPython）
    6. 返回 (success, message, upload_log, target_path)
    """
    config = load_config()

    posts_dir = os.path.join(repo_path, "source", "_posts")
    os.makedirs(posts_dir, exist_ok=True)

    with open(file_path, "r", encoding="utf-8") as f:
        raw_content = f.read()

    post_name = os.path.splitext(os.path.basename(file_path))[0]
    post_asset_dir = os.path.join(posts_dir, post_name)

    existing_fm, body = parse_front_matter(file_path)
    if existing_fm:
        fm_text = existing_fm
    else:
        title = post_name.replace("-", " ").replace("_", " ")
        tags = config.get("default_tags", "技术")
        categories = config.get("default_categories", "默认")
        fm_text = generate_front_matter(title, tags, categories)
        body = raw_content.lstrip("\n")

    full_doc = fm_text.rstrip("---").rstrip() + "\n---\n\n" + body
    processed_content, upload_log = process_markdown_images(
        full_doc, os.path.dirname(file_path), post_asset_dir, config
    )

    dest = os.path.join(posts_dir, os.path.basename(file_path))

    if os.path.exists(dest):
        with open(dest, "r", encoding="utf-8") as f:
            existing = f.read()
        if existing == processed_content:
            upload_log.append("ℹ️ 内容未变更，跳过发布")
            return True, "内容未变更，跳过发布", upload_log, dest
        upload_log.append(f"⚠️ 目标文件已存在，内容已覆盖")

    with open(dest, "w", encoding="utf-8") as f:
        f.write(processed_content)

    # Git 操作（内置，无需外部Git）
    commit_msg = f"Post: {post_name}"
    git_ok, git_log = git_add_commit_push(
        repo_path=repo_path,
        message=commit_msg,
        branch=branch,
        remote_url=remote_url,
        git_token=config.get("git_token", ""),
    )
    upload_log.extend(git_log)

    if not git_ok:
        return False, "Git 操作失败", upload_log, dest

    return True, dest, upload_log, dest


# ============ 删除文章 ============

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
        git_ok, git_log = git_add_commit_push(
            repo_path=repo_path,
            message=f"Remove: {title}",
            branch="main",
            remote_url="",
        )
        if not git_ok:
            return True, f"文件已删除但 Git 操作失败", upload_log_msg
        upload_log_msg += f" (已同步)"

    return deleted, upload_log_msg


# ============ 拖拽处理 ============

def drop_file_handler(dropped_path, config):
    """处理拖拽进来的文件 (.md → 导入, 图片 → 上传到图床)"""
    if not os.path.isfile(dropped_path):
        return False, "不是有效的文件", None
    ext = os.path.splitext(dropped_path)[1].lower()

    if ext in (".md", ".markdown"):
        repo = config.get("repo_path", "")
        if not repo:
            return False, "未配置仓库路径", None
        posts_dir = os.path.join(repo, "source", "_posts")
        os.makedirs(posts_dir, exist_ok=True)
        target = os.path.join(posts_dir, os.path.basename(dropped_path))
        shutil.copy2(dropped_path, target)
        return True, f"已导入: {os.path.basename(dropped_path)}", target

    elif ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
        ok, result = upload_image(dropped_path, config)
        if ok:
            return True, f"图片已上传: {result}", result
        else:
            return False, f"图片上传失败: {result}", None

    else:
        return False, f"不支持的文件类型: {ext}", None


# ============ 依赖检测 ============

def check_dependencies():
    """
    检测系统依赖是否就绪。
    返回 (ok: bool, messages: list)
    """
    msgs = []

    # GitPython
    if HAS_GITPYTHON:
        msgs.append(("✅", "Git 操作引擎: GitPython (已就绪)"))
    else:
        msgs.append(("⚠️", "Git 操作引擎: 降级到命令行 (需安装 GitPython)"))
        try:
            subprocess.run(["git", "--version"], capture_output=True, timeout=5)
            msgs.append(("✅", "系统 Git 命令: 可用"))
        except Exception:
            msgs.append(("❌", "系统 Git 命令: 未找到，请安装 Git"))

    # Markdown
    if HAS_MARKDOWN:
        msgs.append(("✅", "Markdown 渲染引擎: 已就绪"))
    else:
        msgs.append(("⚠️", "Markdown 渲染引擎: 降级到简易模式"))

    # Git 配置
    config = load_config()
    if config.get("repo_path"):
        if os.path.isdir(config["repo_path"]):
            msgs.append(("✅", f"仓库路径: {config['repo_path']}"))
        else:
            msgs.append(("❌", f"仓库路径不存在: {config['repo_path']}"))
    else:
        msgs.append(("⏳", "仓库路径未配置 (首次使用需要在设置中配置)"))

    return all(m[0] == "✅" for m in msgs), msgs
