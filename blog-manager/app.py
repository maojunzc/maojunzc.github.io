"""
Blog Manager GUI - Windows 桌面应用
"""

import os
import sys
import json
import subprocess
import threading
import webbrowser
from datetime import datetime

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# 尝试加载 ttkbootstrap（现代化主题），如果没有则用 tkinter
try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import *
    HAS_TTB = True
except ImportError:
    HAS_TTB = False

from core import *

# ============ 全局 ============
config = load_config()
APP_NAME = "Blog Manager"
APP_VERSION = "1.0.0"
BG_DARK = "#1a1a2e"
BG_CARD = "#16213e"
BG_INPUT = "#0f3460"
ACCENT = "#e94560"
TEXT_COLOR = "#eee"

class BlogManagerApp:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.articles = []
        self.hexo_process = None
        
        self.setup_window()
        self.build_ui()
        self.refresh_all()
    
    def setup_window(self):
        self.root.title(f"{APP_NAME} v{APP_VERSION} - 博客管理器")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)
        
        # 设置图标
        try:
            self.root.iconbitmap(default="")
        except:
            pass
        
        # 样式
        if HAS_TTB:
            self.root.style = tb.Style(theme="darkly")
        
        self.root.configure(bg=BG_DARK)
    
    def build_ui(self):
        """构建主界面"""
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # === 主容器 ===
        main_frame = tk.Frame(self.root, bg=BG_DARK)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_rowconfigure(0, weight=0)  # toolbar
        main_frame.grid_rowconfigure(1, weight=1)  # content
        main_frame.grid_columnconfigure(0, weight=1)
        
        # === 顶部工具栏 ===
        self.build_toolbar(main_frame)
        
        # === 内容区域 (左右分栏) ===
        content_frame = tk.Frame(main_frame, bg=BG_DARK)
        content_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # 左侧 - 文章列表
        self.build_article_panel(content_frame)
        
        # 右侧 - 操作面板
        self.build_action_panel(content_frame)
        
        # === 底部状态栏 ===
        self.build_statusbar(main_frame)
    
    def build_toolbar(self, parent):
        toolbar = tk.Frame(parent, bg=BG_CARD, height=50)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        toolbar.grid_columnconfigure(2, weight=1)
        
        # Logo / 标题
        title_label = tk.Label(
            toolbar, text="📝 Blog Manager", 
            bg=BG_CARD, fg=ACCENT, font=("Segoe UI", 14, "bold")
        )
        title_label.grid(row=0, column=0, padx=(15, 0), pady=10)
        
        # 刷新按钮
        self.btn_refresh = self.make_btn(toolbar, "🔄 刷新", self.refresh_all, 1, 10)
        
        # 仓库路径
        self.path_var = tk.StringVar(value=self.config.get("repo_path", ""))
        path_entry = tk.Entry(
            toolbar, textvariable=self.path_var, bg=BG_INPUT, fg=TEXT_COLOR,
            insertbackground="white", relief="flat", font=("Segoe UI", 9),
            width=40
        )
        path_entry.grid(row=0, column=2, padx=10, sticky="ew")
        
        # 设置按钮
        self.make_btn(toolbar, "⚙️ 设置", self.open_settings, 3, 5)
    
    def build_article_panel(self, parent):
        left = tk.Frame(parent, bg=BG_DARK)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)
        
        # 标题
        tk.Label(left, text="📋 文章列表", bg=BG_DARK, fg=TEXT_COLOR,
                 font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # 列表框架
        list_frame = tk.Frame(left, bg=BG_CARD)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        # Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=BG_CARD, foreground=TEXT_COLOR, 
                       fieldbackground=BG_CARD, rowheight=30, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=BG_INPUT, foreground=TEXT_COLOR,
                       font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", ACCENT)])
        
        self.tree = ttk.Treeview(list_frame, columns=("title", "time", "size"), show="tree headings", height=15)
        self.tree.heading("#0", text="文件名")
        self.tree.heading("title", text="标题")
        self.tree.heading("time", text="修改时间")
        self.tree.heading("size", text="大小")
        self.tree.column("#0", width=150, minwidth=100)
        self.tree.column("title", width=200, minwidth=100)
        self.tree.column("time", width=130, minwidth=80)
        self.tree.column("size", width=60, minwidth=50)
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        vsb.grid(row=0, column=1, sticky="ns", pady=5)
        
        self.tree.bind("<Double-1>", lambda e: self.edit_article())
        
        # 操作按钮
        btn_frame = tk.Frame(left, bg=BG_DARK)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=5)
        for i in range(4):
            btn_frame.grid_columnconfigure(i, weight=1)
        
        self.make_btn(btn_frame, "📄 新建", self.new_article, 0, 2)
        self.make_btn(btn_frame, "✏️ 编辑", self.edit_article, 1, 2)
        self.make_btn(btn_frame, "📥 导入", self.import_article, 2, 2)
        self.make_btn(btn_frame, "🗑️ 删除", self.delete_article, 3, 2)
    
    def build_action_panel(self, parent):
        right = tk.Frame(parent, bg=BG_DARK)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        
        row = 0
        
        # === 发布面板 ===
        pub_frame = tk.Frame(right, bg=BG_CARD)
        pub_frame.grid(row=row, column=0, sticky="ew", pady=(0, 5))
        pub_frame.grid_columnconfigure(1, weight=1)
        row += 1
        
        tk.Label(pub_frame, text="📤 快速发布", bg=BG_CARD, fg=TEXT_COLOR,
                 font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=8)
        
        tk.Label(pub_frame, text="选择 .md 文件:", bg=BG_CARD, fg=TEXT_COLOR,
                 font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", padx=10)
        
        self.pub_path_var = tk.StringVar()
        tk.Entry(pub_frame, textvariable=self.pub_path_var, bg=BG_INPUT, fg=TEXT_COLOR,
                insertbackground="white", relief="flat").grid(row=1, column=1, sticky="ew", padx=5)
        
        self.make_btn(pub_frame, "浏览", self.browse_file, 2, 2)
        self.make_btn(pub_frame, "🚀 一键发布", self.publish, 3, 5)
        
        # Front-matter 预览
        tk.Label(pub_frame, text="Front-matter 预览:", bg=BG_CARD, fg=TEXT_COLOR,
                 font=("Segoe UI", 9)).grid(row=3, column=0, columnspan=3, sticky="w", padx=10, pady=(8, 0))
        
        self.fm_text = scrolledtext.ScrolledText(
            pub_frame, height=6, bg=BG_INPUT, fg=TEXT_COLOR,
            insertbackground="white", relief="flat", font=("Consolas", 9)
        )
        self.fm_text.grid(row=4, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
        
        # === 仓库状态 ===
        row += 1
        stat_frame = tk.Frame(right, bg=BG_CARD)
        stat_frame.grid(row=row, column=0, sticky="ew", pady=(0, 5))
        stat_frame.grid_columnconfigure(1, weight=1)
        row += 1
        
        tk.Label(stat_frame, text="📊 仓库状态", bg=BG_CARD, fg=TEXT_COLOR,
                 font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=8)
        
        labels = [
            ("提交数:", "commits_label"), ("未推送:", "unpushed_label"),
            ("未跟踪:", "untracked_label"), ("分支:", "branch_label")
        ]
        for i, (text, attr) in enumerate(labels):
            col = i % 2
            r = 1 + i // 2
            tk.Label(stat_frame, text=text, bg=BG_CARD, fg="#aaa",
                    font=("Segoe UI", 9)).grid(row=r, column=col*2, sticky="w", padx=(10, 2), pady=2)
            lbl = tk.Label(stat_frame, text="-", bg=BG_CARD, fg=ACCENT,
                         font=("Segoe UI", 9, "bold"))
            lbl.grid(row=r, column=col*2+1, sticky="w", padx=(0, 15), pady=2)
            setattr(self, attr, lbl)
        
        self.make_btn(stat_frame, "🔄 刷新状态", self.refresh_status, 3, 10)
        self.make_btn(stat_frame, "🌐 打开博客", self.open_blog, 3, 10)
        self.make_btn(stat_frame, "▶️ 本地预览", self.preview_site, 3, 10)
        
        # === 日志 ===
        row += 1
        log_frame = tk.Frame(right, bg=BG_CARD)
        log_frame.grid(row=row, column=0, sticky="nsew", pady=(0, 0))
        right.grid_rowconfigure(row, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)
        
        tk.Label(log_frame, text="📝 操作日志", bg=BG_CARD, fg=TEXT_COLOR,
                 font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=8)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=6, bg=BG_INPUT, fg=TEXT_COLOR,
            insertbackground="white", relief="flat", font=("Consolas", 9)
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
    
    def build_statusbar(self, parent):
        bar = tk.Frame(parent, bg=BG_CARD, height=25)
        bar.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        bar.grid_columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="就绪")
        tk.Label(bar, textvariable=self.status_var, bg=BG_CARD, fg="#888",
                font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", padx=10)
        
        self.article_count_var = tk.StringVar(value="文章: 0")
        tk.Label(bar, textvariable=self.article_count_var, bg=BG_CARD, fg="#888",
                font=("Segoe UI", 9)).grid(row=0, column=1, sticky="e", padx=10)
    
    # ============ 工具方法 ============
    
    def make_btn(self, parent, text, command, col, padx=5):
        """创建统一样式的按钮"""
        if HAS_TTB:
            btn = tb.Button(parent, text=text, command=command, bootstyle="danger-outline")
        else:
            btn = tk.Button(parent, text=text, command=command,
                          bg=ACCENT, fg="white", relief="flat", padx=10,
                          font=("Segoe UI", 9))
        btn.grid(row=0, column=col, padx=padx, pady=5, sticky="ew")
        return btn
    
    def log(self, msg):
        """写入日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {msg}\n")
        self.log_text.see("end")
        self.root.update_idletasks()
    
    def set_status(self, msg):
        self.status_var.set(msg)
        self.root.update_idletasks()
    
    def refresh_all(self):
        self.refresh_articles()
        self.refresh_status()
        self.log("已刷新")
    
    # ============ 文章操作 ============
    
    def refresh_articles(self):
        repo = self.config.get("repo_path", "")
        self.articles = get_articles(repo) if repo else []
        
        # 清空 tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for a in self.articles:
            size_str = f"{a['size']/1024:.1f}KB" if a['size'] > 1024 else f"{a['size']}B"
            self.tree.insert("", "end", text=a["file"], 
                           values=(a["title"], a["mtime"], size_str))
        
        self.article_count_var.set(f"文章: {len(self.articles)}")
    
    def refresh_status(self):
        repo = self.config.get("repo_path", "")
        if not repo:
            return
        status = get_git_status(repo)
        if status["valid"]:
            self.commits_label.config(text=status["commits"])
            self.unpushed_label.config(text=str(status["unpushed"]))
            self.untracked_label.config(text=str(status["untracked"]))
            branch = self.config.get("branch", "main")
            self.branch_label.config(text=branch)
    
    def new_article(self):
        """新建文章"""
        win = tk.Toplevel(self.root)
        win.title("新建文章")
        win.geometry("500x400")
        win.configure(bg=BG_DARK)
        
        fields = {}
        row = 0
        
        for label, key in [("标题:", "title"), ("标签(逗号分隔):", "tags"),
                          ("分类(逗号分隔):", "categories")]:
            tk.Label(win, text=label, bg=BG_DARK, fg=TEXT_COLOR,
                    font=("Segoe UI", 9)).grid(row=row, column=0, sticky="w", padx=15, pady=5)
            var = tk.StringVar()
            if key == "tags":
                var.set(self.config.get("default_tags", ""))
            elif key == "categories":
                var.set(self.config.get("default_categories", ""))
            entry = tk.Entry(win, textvariable=var, bg=BG_INPUT, fg=TEXT_COLOR,
                           insertbackground="white", relief="flat", width=50)
            entry.grid(row=row, column=1, padx=15, pady=5)
            fields[key] = var
            row += 1
        
        # 内容编辑
        tk.Label(win, text="内容:", bg=BG_DARK, fg=TEXT_COLOR,
                font=("Segoe UI", 9)).grid(row=row, column=0, sticky="nw", padx=15, pady=5)
        text = scrolledtext.ScrolledText(win, bg=BG_INPUT, fg=TEXT_COLOR,
                                        insertbackground="white", relief="flat",
                                        font=("Consolas", 10), height=10)
        text.grid(row=row, column=1, padx=15, pady=5, sticky="nsew")
        win.grid_rowconfigure(row, weight=1)
        win.grid_columnconfigure(1, weight=1)
        fields["content"] = text
        
        def do_create():
            title = fields["title"].get().strip()
            if not title:
                messagebox.showwarning("提示", "请输入标题")
                return
            tags = fields["tags"].get().strip()
            cats = fields["categories"].get().strip()
            content = fields["content"].get("1.0", "end").strip()
            
            fm = generate_front_matter(title, tags, cats)
            full_content = fm + "\n\n" + content
            
            # 写入文件
            posts_dir = os.path.join(self.config["repo_path"], "source", "_posts")
            os.makedirs(posts_dir, exist_ok=True)
            file_name = title.replace(" ", "-") + ".md"
            file_path = os.path.join(posts_dir, file_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_content)
            
            self.log(f"✅ 文章已创建: {file_name}")
            self.refresh_articles()
            win.destroy()
        
        tk.Button(win, text="✅ 创建", command=do_create,
                 bg=ACCENT, fg="white", relief="flat", padx=20,
                 font=("Segoe UI", 10)).grid(row=row+1, column=0, columnspan=2, pady=15)
    
    def edit_article(self):
        """编辑文章（用 Typora 打开）"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一篇文章")
            return
        
        item = self.tree.item(sel[0])
        file_name = item["text"]
        
        repo = self.config.get("repo_path", "")
        posts_dir = os.path.join(repo, "source", "_posts")
        file_path = os.path.join(posts_dir, file_name)
        
        if not os.path.exists(file_path):
            messagebox.showerror("错误", "文件不存在")
            return
        
        typora = self.config.get("typora_path", "")
        if typora and os.path.exists(typora):
            os.startfile(file_path)  # Use default .md editor
            self.log(f"✏️ 打开文章: {file_name}")
        else:
            os.startfile(file_path)
            self.log(f"✏️ 打开文章: {file_name}")
    
    def import_article(self):
        """导入 .md 文件"""
        files = filedialog.askopenfilenames(
            title="选择 Markdown 文件",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )
        for f in files:
            # 复制到 posts 目录
            posts_dir = os.path.join(self.config["repo_path"], "source", "_posts")
            os.makedirs(posts_dir, exist_ok=True)
            shutil.copy2(f, os.path.join(posts_dir, os.path.basename(f)))
            self.log(f"📥 导入: {os.path.basename(f)}")
        
        self.refresh_articles()
    
    def delete_article(self):
        """删除文章"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一篇文章")
            return
        
        item = self.tree.item(sel[0])
        file_name = item["text"]
        
        if not messagebox.askyesno("确认", f"确定删除「{item['values'][0]}」？\n此操作将提交Git删除记录。"):
            return
        
        repo = self.config.get("repo_path", "")
        for a in self.articles:
            if a["file"] == file_name:
                delete_article(a, repo)
                self.log(f"🗑️ 已删除: {file_name}")
                break
        
        self.refresh_articles()
        self.refresh_status()
    
    # ============ 发布 ============
    
    def browse_file(self):
        file = filedialog.askopenfilename(
            title="选择要发布的 .md 文件",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )
        if file:
            self.pub_path_var.set(file)
            self.preview_front_matter(file)
    
    def preview_front_matter(self, file_path):
        """预览 Front-matter"""
        title = os.path.splitext(os.path.basename(file_path))[0]
        tags = self.config.get("default_tags", "")
        cats = self.config.get("default_categories", "")
        fm = generate_front_matter(title, tags, cats)
        
        self.fm_text.delete("1.0", "end")
        self.fm_text.insert("1.0", fm)
    
    def publish(self):
        """一键发布"""
        file_path = self.pub_path_var.get().strip()
        if not file_path or not os.path.exists(file_path):
            messagebox.showwarning("提示", "请选择要发布的 .md 文件")
            return
        
        if not file_path.endswith(".md"):
            messagebox.showerror("错误", "请选择 .md 文件")
            return
        
        self.set_status("正在发布...")
        self.log(f"📤 开始发布: {os.path.basename(file_path)}")
        
        def do_publish():
            try:
                success, result = publish_article(
                    file_path,
                    self.config["repo_path"],
                    self.config.get("remote_url", ""),
                    self.config.get("branch", "main"),
                    self.config.get("git_name", ""),
                    self.config.get("git_email", "")
                )
                if success:
                    self.log(f"✅ 发布成功!")
                    self.set_status("发布成功")
                    self.refresh_articles()
                    self.refresh_status()
                else:
                    self.log(f"❌ 发布失败: {result}")
                    self.set_status("发布失败")
            except Exception as e:
                self.log(f"❌ 错误: {str(e)}")
                self.set_status("发布失败")
        
        threading.Thread(target=do_publish, daemon=True).start()
    
    # ============ 运维 ============
    
    def open_blog(self):
        webbrowser.open("https://maojunzc.github.io")
        self.log("🌐 打开博客")
    
    def preview_site(self):
        """本地启动 hexo server"""
        repo = self.config.get("repo_path", "")
        if not repo:
            return
        
        def run():
            self.set_status("启动本地服务器...")
            port = 4000
            cmd = f'start cmd /k "cd /d {repo} && hexo server -p {port}"'
            os.system(cmd)
            time.sleep(2)
            webbrowser.open(f"http://localhost:{port}")
            self.log(f"▶️ 本地预览: http://localhost:{port}")
            self.set_status("本地预览已启动")
        
        threading.Thread(target=run, daemon=True).start()
    
    # ============ 设置 ============
    
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("设置")
        win.geometry("550x480")
        win.configure(bg=BG_DARK)
        win.transient(self.root)
        win.grab_set()
        
        fields = {}
        row = 0
        
        for label, key, wide in [
            ("仓库路径:", "repo_path", True),
            ("远程地址:", "remote_url", True),
            ("分支:", "branch", False),
            ("Git 用户名:", "git_name", False),
            ("Typora 路径:", "typora_path", True),
            ("默认标签:", "default_tags", False),
            ("默认分类:", "default_categories", False),
        ]:
            tk.Label(win, text=label, bg=BG_DARK, fg=TEXT_COLOR,
                    font=("Segoe UI", 9)).grid(row=row, column=0, sticky="w", padx=15, pady=5)
            var = tk.StringVar(value=self.config.get(key, ""))
            w = 50 if wide else 30
            entry = tk.Entry(win, textvariable=var, bg=BG_INPUT, fg=TEXT_COLOR,
                           insertbackground="white", relief="flat", width=w)
            entry.grid(row=row, column=1, padx=15, pady=5, sticky="ew")
            fields[key] = var
            row += 1
        
        win.grid_columnconfigure(1, weight=1)
        
        def save_settings():
            for key, var in fields.items():
                self.config[key] = var.get().strip()
            save_config(self.config)
            self.log("⚙️ 配置已保存")
            messagebox.showinfo("完成", "配置已保存")
            win.destroy()
        
        row += 1
        tk.Button(win, text="💾 保存", command=save_settings,
                 bg=ACCENT, fg="white", relief="flat", padx=30,
                 font=("Segoe UI", 10)).grid(row=row, column=0, columnspan=2, pady=20)


# ============ 启动 ============

def main():
    root = tb.Window(themename="darkly") if HAS_TTB else tk.Tk()
    app = BlogManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
