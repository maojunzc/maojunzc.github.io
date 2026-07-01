"""
Blog Manager GUI - 桌面博客管理工具 v3.0
支持: 文章管理、一键发布、图片上传(图床)、拖拽、灰色写作模式
零外部依赖：内置 Git 操作和 Markdown 渲染
"""

import os
import sys
import json
import re
import shutil
import subprocess
import threading
import webbrowser
import time
from datetime import datetime
from tkinter import (
    Tk, Frame, Label, Entry, Button, Text, Scrollbar, Menu, Toplevel,
    StringVar, IntVar, BooleanVar, filedialog, messagebox, scrolledtext, ttk
)

try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import *
    HAS_TTB = True
except ImportError:
    HAS_TTB = False

from core import *


APP_NAME = "Blog Manager"
APP_VERSION = "3.0.0"
BG_DARK = "#1a1a2e"
BG_CARD = "#16213e"
BG_INPUT = "#0f3460"
ACCENT = "#e94560"
TEXT_COLOR = "#eee"
BTN_BG = "#e94560"
WRITING_BG = "#f5f5f5"  # 灰色写作模式背景
WRITING_FG = "#333333"   # 灰色写作模式文字


class BlogManagerApp:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.articles = []
        self.hexo_process = None
        self._log_lock = threading.Lock()
        self._publishing = False
        self._writing_mode = self.config.get("writing_mode", "default") != "default"

        self.setup_window()
        self.build_ui()
        # 首次运行检测（延迟执行，等 UI 渲染完成）
        self.root.after(500, self.first_run_check)
        self.root.after(200, self.refresh_all)

    # ==================== 窗口初始化 ====================

    def setup_window(self):
        self.root.title(f"{APP_NAME} v{APP_VERSION} - 博客管理器")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)

        if HAS_TTB:
            try:
                style = tb.Style(theme="darkly")
                self.root.style = style
            except Exception:
                pass

        self.root.configure(bg=BG_DARK)

        # 拖拽支持（仅 Windows）
        if sys.platform == "win32":
            try:
                from tkinterdnd2 import DND_FILES, TkinterDnD
                self.root.drop_target_register(DND_FILES)
                self.root.dnd_bind('<<Drop>>', self.on_drop)
            except ImportError:
                pass  # 未安装 tkinterdnd2，拖拽功能不可用

    # ==================== UI 构建 ====================

    def build_ui(self):
        """构建主界面布局"""
        # 主网格配置
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # 顶部标题栏
        self.build_titlebar()

        # 主内容区（左右分栏）
        main = Frame(self.root, bg=BG_DARK)
        main.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # 左侧文章列表
        left = Frame(main, bg=BG_DARK)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)
        self.build_article_panel(left)

        # 右侧操作区（Notebook 分页）
        right = Frame(main, bg=BG_DARK)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)
        self.build_action_notebook(right)

        # 底部状态栏
        self.build_statusbar()

    def build_titlebar(self):
        """顶部标题栏"""
        bar = Frame(self.root, bg=BG_CARD, height=44)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_columnconfigure(1, weight=1)

        # Logo / 标题
        logo = Label(bar, text="📝 Blog Manager", bg=BG_CARD, fg=ACCENT,
                     font=("Segoe UI", 13, "bold"))
        logo.grid(row=0, column=0, padx=15, pady=8)

        # 仓库路径
        self.path_var = StringVar(value=self.config.get("repo_path", ""))
        path_entry = Entry(bar, textvariable=self.path_var, bg=BG_INPUT, fg=TEXT_COLOR,
                           insertbackground="white", relief="flat", font=("Consolas", 9))
        path_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

        # 刷新按钮
        btn_refresh = self._make_btn(bar, "🔄 刷新", self.refresh_all, 2)
        btn_refresh.grid(row=0, column=2, padx=2)

        # 设置按钮
        btn_settings = self._make_btn(bar, "⚙️", self.open_settings, 3)
        btn_settings.grid(row=0, column=3, padx=2)

    def build_article_panel(self, parent):
        """左侧文章列表面板"""
        # 搜索栏
        search_frame = Frame(parent, bg=BG_DARK)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        search_frame.grid_columnconfigure(0, weight=1)

        self.search_var = StringVar()
        search_entry = Entry(search_frame, textvariable=self.search_var,
                             bg=BG_INPUT, fg=TEXT_COLOR, insertbackground="white",
                             relief="flat", font=("Segoe UI", 9))
        search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        search_entry.insert(0, "🔍 搜索文章...")
        # 焦点进入时清除 placeholder
        def on_search_focus_in(e):
            if self.search_var.get() == "🔍 搜索文章...":
                search_entry.delete(0, "end")
        def on_search_focus_out(e):
            if not self.search_var.get().strip():
                search_entry.insert(0, "🔍 搜索文章...")
        search_entry.bind("<FocusIn>", on_search_focus_in)
        search_entry.bind("<FocusOut>", on_search_focus_out)
        # 绑定 trace 要放在 insert 之后，避免初始化时触发无意义的刷新
        self.search_var.trace_add("write", lambda *_: self.filter_articles())

        # 文章列表
        list_frame = Frame(parent, bg=BG_CARD)
        list_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=BG_CARD, foreground=TEXT_COLOR,
                        fieldbackground=BG_CARD, rowheight=28, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=BG_INPUT, foreground=TEXT_COLOR,
                        font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", ACCENT)])

        self.tree = ttk.Treeview(
            list_frame,
            columns=("title", "time", "size"),
            show="tree headings",
            height=15,
        )
        self.tree.heading("#0", text="文件名")
        self.tree.heading("title", text="标题")
        self.tree.heading("time", text="修改时间")
        self.tree.heading("size", text="大小")
        self.tree.column("#0", width=120, minwidth=80)
        self.tree.column("title", width=160, minwidth=80)
        self.tree.column("time", width=100, minwidth=70)
        self.tree.column("size", width=55, minwidth=40)

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        vsb.grid(row=0, column=1, sticky="ns", pady=5)

        self.tree.bind("<Double-1>", lambda e: self.edit_article())

        # 操作按钮
        btn_frame = Frame(parent, bg=BG_DARK)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=5)
        for i in range(4):
            btn_frame.grid_columnconfigure(i, weight=1)

        self._make_btn_grid(btn_frame, "📄 新建", self.new_article, 0)
        self._make_btn_grid(btn_frame, "✏️ 编辑", self.edit_article, 1)
        self._make_btn_grid(btn_frame, "📥 导入", self.import_article, 2)
        self._make_btn_grid(btn_frame, "🗑️ 删除", self.delete_article, 3)

        # 拖拽提示
        if sys.platform == "win32":
            try:
                from tkinterdnd2 import DND_FILES
                drop_label = Label(parent, text="📌 拖拽 .md 文件或图片到窗口",
                                   bg=BG_DARK, fg="#666", font=("Segoe UI", 8))
                drop_label.grid(row=3, column=0, sticky="w", pady=(0, 5))
            except ImportError:
                pass

    def build_action_notebook(self, parent):
        """右侧 Notebook 分页（发布 / 图床 / 设置 / 日志）"""
        nb = ttk.Notebook(parent)
        nb.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # --- 发布页 ---
        pub_frame = Frame(nb, bg=BG_CARD)
        nb.add(pub_frame, text="  📤 发布  ")
        pub_frame.grid_columnconfigure(1, weight=1)
        pub_frame.grid_rowconfigure(4, weight=1)

        row = 0
        Label(pub_frame, text="选择文件:", bg=BG_CARD, fg=TEXT_COLOR,
              font=("Segoe UI", 9)).grid(row=row, column=0, sticky="w", padx=12, pady=8)

        self.pub_path_var = StringVar()
        self.pub_entry = Entry(pub_frame, textvariable=self.pub_path_var,
                               bg=BG_INPUT, fg=TEXT_COLOR, insertbackground="white",
                               relief="flat", font=("Consolas", 9))
        self.pub_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=8)

        self._make_btn_grid(pub_frame, "📂 浏览", self.browse_file, 2, row=row)
        row += 1

        # 发布按钮 + 进度条
        btn_frame = Frame(pub_frame, bg=BG_CARD)
        btn_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=12, pady=5)
        btn_frame.grid_columnconfigure(0, weight=1)

        self.pub_btn = self._make_btn(btn_frame, "🚀 一键发布", self.publish, 0)
        self.pub_btn.config(width=18)

        self.progress = ttk.Progressbar(btn_frame, mode="indeterminate", length=200)
        self.progress.grid(row=0, column=1, padx=10, pady=5)
        self.progress.grid_remove()
        row += 1

        # Front-matter 预览
        Label(pub_frame, text="Front-matter 预览:", bg=BG_CARD, fg=TEXT_COLOR,
              font=("Segoe UI", 9)).grid(row=row, column=0, columnspan=3,
                                         sticky="w", padx=12, pady=(10, 0))
        row += 1

        self.fm_text = scrolledtext.ScrolledText(
            pub_frame, height=6, bg=BG_INPUT, fg=TEXT_COLOR,
            insertbackground="white", relief="flat", font=("Consolas", 9)
        )
        self.fm_text.grid(row=row, column=0, columnspan=3, sticky="ew",
                          padx=12, pady=5)
        pub_frame.grid_rowconfigure(row, weight=1)

        # --- 图床页 ---
        img_frame = Frame(nb, bg=BG_CARD)
        nb.add(img_frame, text="  🖼️ 图床  ")
        img_frame.grid_columnconfigure(0, weight=1)
        img_frame.grid_rowconfigure(2, weight=1)

        row = 0
        Label(img_frame, text="图床设置:", bg=BG_CARD, fg=TEXT_COLOR,
              font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky="w",
                                                   padx=12, pady=(10, 5))
        row += 1

        host_frame = Frame(img_frame, bg=BG_CARD)
        host_frame.grid(row=row, column=0, sticky="ew", padx=12, pady=5)

        Label(host_frame, text="存储方式:", bg=BG_CARD, fg=TEXT_COLOR,
              font=("Segoe UI", 9)).pack(side="left")
        self.host_var = StringVar(value=self.config.get("image_host", "local"))
        for opt in [("本地复制", "local"), ("GitHub", "github"),
                     ("ImgBB", "imgbb"), ("SM.MS", "smms")]:
            Radiobutton(host_frame, text=opt[0], variable=self.host_var,
                        value=opt[1], bg=BG_CARD, fg=TEXT_COLOR,
                        selectcolor=BG_INPUT, activebackground=BG_CARD,
                        activeforeground=TEXT_COLOR, font=("Segoe UI", 9),
                        command=self._on_image_host_change).pack(side="left", padx=8)

        row += 1

        # 图床配置区
        self.img_config_frame = Frame(img_frame, bg=BG_CARD)
        self.img_config_frame.grid(row=row, column=0, sticky="ew", padx=12, pady=5)
        self._build_image_host_config()
        row += 1

        # 上传按钮
        upload_frame = Frame(img_frame, bg=BG_CARD)
        upload_frame.grid(row=row, column=0, sticky="ew", padx=12, pady=5)
        self._make_btn_grid(upload_frame, "📤 上传图片", self.upload_image_dialog, 0)
        self._make_btn_grid(upload_frame, "📋 查看图床列表", self.show_image_list, 1)
        row += 1

        Label(img_frame, text="图床日志:", bg=BG_CARD, fg=TEXT_COLOR,
              font=("Segoe UI", 9)).grid(row=row, column=0, sticky="w",
                                         padx=12, pady=(8, 0))
        row += 1

        self.img_log = scrolledtext.ScrolledText(
            img_frame, height=8, bg=BG_INPUT, fg=TEXT_COLOR,
            insertbackground="white", relief="flat", font=("Consolas", 8)
        )
        self.img_log.grid(row=row, column=0, sticky="nsew", padx=12, pady=5)
        img_frame.grid_rowconfigure(row, weight=1)

        # --- 设置页 ---
        settings_frame = Frame(nb, bg=BG_CARD)
        nb.add(settings_frame, text="  ⚙️ 设置  ")
        self.build_settings_panel(settings_frame)

        # --- 日志页 ---
        log_frame = Frame(nb, bg=BG_CARD)
        nb.add(log_frame, text="  📝 日志  ")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, bg=BG_INPUT, fg=TEXT_COLOR,
            insertbackground="white", relief="flat", font=("Consolas", 9)
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # 日志页清空按钮
        btn_clear = self._make_btn(log_frame, "🗑 清空日志",
                                    lambda: self.log_text.delete("1.0", "end"), 0)
        btn_clear.grid(row=1, column=0, sticky="e", padx=10, pady=(0, 10))

        self.notebook = nb

    def _build_image_host_config(self):
        """构建图床配置输入区（根据选择的 host 动态显示）"""
        frame = self.img_config_frame
        for w in frame.winfo_children():
            w.destroy()

        host = self.host_var.get()

        if host == "github":
            fields = [
                ("GitHub User:", "github_user", 30),
                ("GitHub Token:", "github_token", 30),
                ("图片仓库:", "github_image_repo", 30),
                ("图片路径:", "github_image_path", 30),
            ]
        elif host == "imgbb":
            fields = [
                ("ImgBB API Key:", "imgbb_api_key", 40),
            ]
        elif host == "smms":
            fields = [
                ("SM.MS API Key:", "smms_api_key", 40),
            ]
        else:
            Label(frame, text="本地模式：图片将复制到文章资源目录",
                  bg=BG_CARD, fg="#aaa", font=("Segoe UI", 9)).pack(anchor="w")
            return

        for i, (label, key, width) in enumerate(fields):
            row_f = Frame(frame, bg=BG_CARD)
            row_f.pack(fill="x", pady=2)
            Label(row_f, text=label, bg=BG_CARD, fg=TEXT_COLOR,
                  font=("Segoe UI", 9), width=14, anchor="w").pack(side="left")
            var = StringVar(value=self.config.get(key, ""))
            Entry(row_f, textvariable=var, bg=BG_INPUT, fg=TEXT_COLOR,
                  insertbackground="white", relief="flat", width=width,
                  font=("Consolas", 9)).pack(side="left", fill="x", expand=True, padx=5)
            setattr(self, f"_img_{key}_var", var)

    def _on_image_host_change(self):
        """图床类型切换时重建配置区"""
        self._build_image_host_config()
        self.config["image_host"] = self.host_var.get()

    def build_settings_panel(self, parent):
        """设置面板"""
        parent.grid_columnconfigure(1, weight=1)

        entries = [
            ("仓库路径:", "repo_path", True),
            ("远程地址:", "remote_url", True),
            ("Git Token:", "git_token", True),
            ("Git 用户名:", "git_name", False),
            ("Git 邮箱:", "git_email", False),
            ("Typora 路径:", "typora_path", True),
            ("默认标签:", "default_tags", False),
            ("默认分类:", "default_categories", False),
            ("GitHub User:", "github_user", False),
            ("GitHub Token:", "github_token", True),
            ("图片仓库:", "github_image_repo", False),
            ("图片路径:", "github_image_path", False),
            ("ImgBB Key:", "imgbb_api_key", False),
            ("SM.MS Key:", "smms_api_key", False),
            ("预览端口:", "preview_port", False),
        ]

        self._setting_vars = {}
        for i, (label, key, wide) in enumerate(entries):
            row_s = Frame(parent, bg=BG_CARD)
            row_s.grid(row=i, column=0, columnspan=3, sticky="ew",
                       padx=12, pady=3)
            row_s.grid_columnconfigure(1, weight=1)

            Label(row_s, text=label, bg=BG_CARD, fg=TEXT_COLOR,
                  font=("Segoe UI", 9), width=16, anchor="w").grid(row=0, column=0,
                                                                   sticky="w")

            w = 45 if wide else 25
            value = self.config.get(key, "")
            if key == "github_token" and value:
                value = "***"  # 脱敏显示
            var = StringVar(value=value)
            Entry(row_s, textvariable=var, bg=BG_INPUT, fg=TEXT_COLOR,
                  insertbackground="white", relief="flat", width=w,
                  font=("Consolas", 9)).grid(row=0, column=1, sticky="ew",
                                             padx=5)
            self._setting_vars[key] = var

        # 写作模式
        row_m = Frame(parent, bg=BG_CARD)
        row_m.grid(row=len(entries), column=0, columnspan=3, sticky="ew",
                   padx=12, pady=8)
        Label(row_m, text="写作模式:", bg=BG_CARD, fg=TEXT_COLOR,
              font=("Segoe UI", 9), width=16, anchor="w").pack(side="left")
        self.writing_mode_var = BooleanVar(
            value=self.config.get("writing_mode", "default") != "default"
        )
        Checkbutton(row_m, text="经典灰色写作模式（简洁白底黑字）",
                    variable=self.writing_mode_var, bg=BG_CARD, fg=TEXT_COLOR,
                    selectcolor=BG_INPUT, activebackground=BG_CARD,
                    activeforeground=TEXT_COLOR, font=("Segoe UI", 9),
                    command=self._toggle_writing_mode).pack(side="left", padx=5)

        # 自动推送
        row_p = Frame(parent, bg=BG_CARD)
        row_p.grid(row=len(entries) + 1, column=0, columnspan=3, sticky="ew",
                   padx=12, pady=3)
        Label(row_p, text="自动推送:", bg=BG_CARD, fg=TEXT_COLOR,
              font=("Segoe UI", 9), width=16, anchor="w").pack(side="left")
        self.auto_push_var = BooleanVar(
            value=self.config.get("enable_auto_push", True)
        )
        Checkbutton(row_p, text="发布后自动 git push",
                    variable=self.auto_push_var, bg=BG_CARD, fg=TEXT_COLOR,
                    selectcolor=BG_INPUT, activebackground=BG_CARD,
                    activeforeground=TEXT_COLOR, font=("Segoe UI", 9)).pack(
                        side="left", padx=5)

        # 保存按钮
        btn_frame = Frame(parent, bg=BG_CARD)
        btn_frame.grid(row=len(entries) + 2, column=0, columnspan=3,
                       sticky="ew", padx=12, pady=15)
        self._make_btn_grid(btn_frame, "💾 保存设置", self._save_current_settings, 0)

    def build_statusbar(self):
        """底部状态栏"""
        bar = Frame(self.root, bg=BG_CARD, height=28)
        bar.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        bar.grid_columnconfigure(0, weight=1)

        self.status_var = StringVar(value="就绪")
        Label(bar, textvariable=self.status_var, bg=BG_CARD, fg="#888",
              font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", padx=10)

        self.count_var = StringVar(value="文章: 0")
        Label(bar, textvariable=self.count_var, bg=BG_CARD, fg="#888",
              font=("Segoe UI", 9)).grid(row=0, column=1, sticky="e", padx=10)

    # ==================== 首次运行检测 ====================

    def first_run_check(self):
        """首次运行时检测依赖并给出引导"""
        ok, msgs = check_dependencies()

        # 检查是否已配置仓库路径
        if not self.config.get("repo_path"):
            self.log("👋 欢迎使用 Blog Manager v3.0！")
            self.log("📋 首次使用请先在 ⚙️ 设置 中配置仓库路径")
            self.set_status("请先配置仓库路径")
            messagebox.showinfo(
                "欢迎使用 Blog Manager v3.0",
                "感谢使用 Blog Manager！\n\n"
                "首次使用请先配置：\n"
                "1. 点击 ⚙️ 设置 → 填写「仓库路径」\n"
                "2. 配置 Git 远程地址和分支\n"
                "3. 即可开始发布文章\n\n"
                "v3.0 已内置 Git 操作和 Markdown 渲染，\n"
                "无需额外安装任何依赖！",
                parent=self.root
            )

        # 检测日志
        for icon, msg in msgs:
            self.log(f"{icon} {msg}")

    # ==================== 辅助方法 ====================

    def _make_btn(self, parent, text, command, col):
        """创建按钮（ttkbootstrap 优先）"""
        if HAS_TTB:
            btn = tb.Button(parent, text=text, command=command,
                            bootstyle="danger-outline")
        else:
            btn = Button(parent, text=text, command=command,
                         bg=BTN_BG, fg="white", relief="flat",
                         font=("Segoe UI", 9))
        return btn

    def _make_btn_grid(self, parent, text, command, col, row=None, padx=3):
        """创建按钮并 grid 放置"""
        btn = self._make_btn(parent, text, command, col)
        if row is not None:
            btn.grid(row=row, column=col, padx=padx, pady=3, sticky="ew")
        else:
            btn.grid(column=col, padx=padx, pady=3, sticky="ew")
        return btn

    def log(self, msg):
        """线程安全日志"""
        with self._log_lock:
            ts = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert("end", f"[{ts}] {msg}\n")
            self.log_text.see("end")

    def set_status(self, msg):
        self.status_var.set(msg)
        self.root.update_idletasks()

    # ==================== 文章操作 ====================

    def refresh_all(self):
        self.refresh_articles()
        self.refresh_status()
        self.log("已刷新")

    def refresh_articles(self, filter_text=""):
        """刷新文章列表"""
        repo = self.config.get("repo_path", "")
        if not repo or not os.path.isdir(repo):
            self.count_var.set("文章: 0")
            return

        all_articles = get_articles(repo)
        if filter_text:
            ft = filter_text.lower()
            self.articles = [a for a in all_articles
                             if ft in a["title"].lower() or ft in a["file"].lower()]
        else:
            self.articles = all_articles

        # 更新 Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        for a in self.articles:
            size_str = f"{a['size'] / 1024:.1f}KB" if a["size"] > 1024 else f"{a['size']}B"
            self.tree.insert("", "end", text=a["file"],
                             values=(a["title"], a["mtime"], size_str))
        self.count_var.set(f"文章: {len(self.articles)}")

    def filter_articles(self):
        """搜索过滤"""
        text = self.search_var.get().strip()
        if text == "🔍 搜索文章...":
            text = ""
        self.refresh_articles(text)

    def refresh_status(self):
        """刷新仓库状态"""
        repo = self.config.get("repo_path", "")
        if not repo or not os.path.isdir(repo):
            return
        status = get_git_status(repo)
        if status.get("valid"):
            # 这里可以添加状态标签更新，暂简化
            pass

    def new_article(self):
        """新建文章"""
        if not self.config.get("repo_path"):
            messagebox.showwarning("提示", "请先在设置中配置仓库路径")
            return

        win = Toplevel(self.root)
        win.title("新建文章")
        win.geometry("520x420")
        win.configure(bg=BG_DARK)
        win.transient(self.root)
        win.grab_set()
        win.grid_columnconfigure(1, weight=1)
        win.grid_rowconfigure(3, weight=1)

        fields = {}
        rows = [
            ("标题:", "title"),
            ("标签(逗号分隔):", "tags"),
            ("分类(逗号分隔):", "categories"),
        ]
        for i, (label, key) in enumerate(rows):
            Label(win, text=label, bg=BG_DARK, fg=TEXT_COLOR,
                  font=("Segoe UI", 9)).grid(row=i, column=0, sticky="w",
                                             padx=15, pady=5)
            var = StringVar()
            if key == "tags":
                var.set(self.config.get("default_tags", ""))
            elif key == "categories":
                var.set(self.config.get("default_categories", ""))
            Entry(win, textvariable=var, bg=BG_INPUT, fg=TEXT_COLOR,
                  insertbackground="white", relief="flat", width=50
                  ).grid(row=i, column=1, padx=15, pady=5, sticky="ew")
            fields[key] = var

        Label(win, text="内容:", bg=BG_DARK, fg=TEXT_COLOR,
              font=("Segoe UI", 9)).grid(row=3, column=0, sticky="nw",
                                         padx=15, pady=5)
        text_w = scrolledtext.ScrolledText(win, bg=BG_INPUT, fg=TEXT_COLOR,
                                            insertbackground="white",
                                            relief="flat", font=("Consolas", 10),
                                            height=10)
        text_w.grid(row=3, column=1, padx=15, pady=5, sticky="nsew")
        fields["content"] = text_w

        def do_create():
            title = fields["title"].get().strip()
            if not title:
                messagebox.showwarning("提示", "请输入标题")
                return
            tags = fields["tags"].get().strip()
            cats = fields["categories"].get().strip()
            content = fields["content"].get("1.0", "end").strip()

            fm = generate_front_matter(title, tags, cats)
            full = fm + "\n\n" + content

            posts_dir = os.path.join(self.config["repo_path"], "source", "_posts")
            os.makedirs(posts_dir, exist_ok=True)
            # 安全文件名：移除 Windows 非法字符 + 截断长度
            safe_name = title.replace(" ", "-")
            safe_name = re.sub(r'[\\/:*?"<>|]', "", safe_name)
            safe_name = safe_name.strip("-.")[:80] or "untitled"
            # 防重名：如果已存在则添加数字后缀
            file_name = safe_name + ".md"
            file_path = os.path.join(posts_dir, file_name)
            counter = 1
            while os.path.exists(file_path):
                file_name = f"{safe_name}_{counter}.md"
                file_path = os.path.join(posts_dir, file_name)
                counter += 1

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full)

            self.log(f"✅ 文章已创建: {file_name}")
            self.refresh_articles()
            win.destroy()

        btn_create = self._make_btn(win, "✅ 创建", do_create, 0)
        btn_create.grid(row=4, column=0, columnspan=2, pady=12)

    def edit_article(self):
        """编辑文章（用系统关联程序打开）"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一篇文章")
            return

        item = self.tree.item(sel[0])
        file_name = item["text"]

        repo = self.config.get("repo_path", "")
        if not repo:
            messagebox.showwarning("提示", "请先配置仓库路径")
            return
        posts_dir = os.path.join(repo, "source", "_posts")
        file_path = os.path.join(posts_dir, file_name)

        if not os.path.exists(file_path):
            messagebox.showerror("错误", "文件不存在")
            return

        os.startfile(file_path)
        self.log(f"✏️ 打开文章: {file_name}")

    def import_article(self):
        """导入 .md 文件"""
        repo = self.config.get("repo_path", "")
        if not repo:
            messagebox.showwarning("提示", "请先配置仓库路径")
            return

        files = filedialog.askopenfilenames(
            title="选择 Markdown 文件",
            filetypes=[("Markdown 文件", "*.md"), ("所有文件", "*.*")]
        )
        if not files:
            return

        posts_dir = os.path.join(repo, "source", "_posts")
        os.makedirs(posts_dir, exist_ok=True)

        for f in files:
            try:
                shutil.copy2(f, os.path.join(posts_dir, os.path.basename(f)))
                self.log(f"📥 导入: {os.path.basename(f)}")
            except Exception as e:
                self.log(f"❌ 导入失败: {e}")

        self.refresh_articles()

    def delete_article(self):
        """删除文章"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一篇文章")
            return

        item = self.tree.item(sel[0])
        article_title = item["values"][0] if item["values"] else "未命名"
        file_name = item["text"]

        if not messagebox.askyesno("确认删除",
                                   f"确定删除「{article_title}」？\n此操作不可恢复！"):
            return

        # 找到完整文章信息
        article = None
        for a in self.articles:
            if a["file"] == file_name:
                article = a
                break

        if article:
            result = delete_article(article, self.config["repo_path"])
            if len(result) == 3:
                deleted, msg = result[0], result[2]
            else:
                deleted, msg = result
            self.log(f"🗑️ {msg}")
        else:
            self.log(f"❌ 未找到文章信息: {file_name}")

        self.refresh_articles()

    # ==================== 发布 ====================

    def browse_file(self):
        """浏览选择发布文件"""
        file = filedialog.askopenfilename(
            title="选择要发布的 .md 文件",
            filetypes=[("Markdown 文件", "*.md"), ("所有文件", "*.*")]
        )
        if file:
            self.pub_path_var.set(file)
            self.preview_front_matter(file)

    def preview_front_matter(self, file_path):
        """预览文件的 front-matter"""
        existing_fm, _ = parse_front_matter(file_path)
        if existing_fm:
            self.fm_text.delete("1.0", "end")
            self.fm_text.insert("1.0", existing_fm)
        else:
            base = os.path.splitext(os.path.basename(file_path))[0]
            title = base.replace("-", " ").replace("_", " ")
            tags = self.config.get("default_tags", "")
            cats = self.config.get("default_categories", "")
            fm = generate_front_matter(title, tags, cats)
            self.fm_text.delete("1.0", "end")
            self.fm_text.insert("1.0", fm + "\n\n(注: 原文件无 front-matter，将自动生成)")

    def publish(self):
        """一键发布"""
        file_path = self.pub_path_var.get().strip()
        if not file_path or not os.path.exists(file_path):
            messagebox.showwarning("提示", "请选择要发布的 .md 文件")
            return
        if not file_path.lower().endswith(".md"):
            messagebox.showerror("错误", "请选择 .md 文件")
            return
        repo = self.config.get("repo_path", "")
        if not repo:
            messagebox.showwarning("提示", "请先在设置中配置仓库路径")
            return

        if self._publishing:
            messagebox.showinfo("提示", "正在发布中，请稍候...")
            return

        self._publishing = True
        self.pub_btn.config(state="disabled")
        self.progress.grid()
        self.progress.start(10)
        self.set_status("正在发布...")
        self.log(f"📤 开始发布: {os.path.basename(file_path)}")

        def do_publish():
            try:
                success, result, upload_log, target = publish_article(
                    file_path=file_path,
                    repo_path=repo,
                    remote_url=self.config.get("remote_url", ""),
                    branch=self.config.get("branch", "main"),
                    git_name=self.config.get("git_name", ""),
                    git_email=self.config.get("git_email", ""),
                )

                if success:
                    self.log(f"✅ 发布成功!")
                    for ul in upload_log:
                        self.log(f"   {ul}")
                    self.set_status("发布成功")

                    # 自动推送
                    if self.config.get("enable_auto_push", True):
                        self._auto_push(repo)

                    self.refresh_articles()
                    webbrowser.open("https://maojunzc.github.io")
                else:
                    self.log(f"❌ 发布失败: {result}")
                    self.set_status("发布失败")
            except Exception as e:
                self.log(f"❌ 发布异常: {str(e)}")
                self.set_status("发布失败")
            finally:
                self.root.after(0, lambda: self._finish_publish())

        threading.Thread(target=do_publish, daemon=True).start()

    def _finish_publish(self):
        self._publishing = False
        self.pub_btn.config(state="normal")
        self.progress.stop()
        self.progress.grid_remove()

    def _auto_push(self, repo):
        """自动 push"""
        r = run_git(["git", "push", "origin", self.config.get("branch", "main")], repo)
        if r.returncode == 0:
            self.log("📤 已推送到远程")
        else:
            self.log(f"⚠️ 推送失败: {r.stderr[:100]}")

    # ==================== 运维 ====================

    def open_blog(self):
        webbrowser.open("https://maojunzc.github.io")
        self.log("🌐 打开博客")

    def preview_site(self):
        """本地预览"""
        repo = self.config.get("repo_path", "")
        if not repo or not os.path.isdir(repo):
            messagebox.showwarning("提示", "请先配置仓库路径")
            return

        def run():
            port = int(self.config.get("preview_port", 4000))
            self.set_status(f"启动本地服务器 (端口 {port})...")
            try:
                # 使用列表形式避免命令注入，shell=False
                self.hexo_process = subprocess.Popen(
                    ["hexo", "server", "-p", str(port)],
                    cwd=repo,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
                )
                time.sleep(4)
                # 保存进程引用以便后续 kill
                self.preview_port = port
                webbrowser.open(f"http://localhost:{port}")
                self.log(f"▶️ 本地预览: http://localhost:{port}")
                self.set_status("本地预览已启动")
            except FileNotFoundError:
                self.log("❌ 未找到 hexo 命令，请确认已安装 Hexo CLI")
                self.set_status("预览启动失败: hexo 未安装")
            except Exception as e:
                self.log(f"❌ 启动失败: {e}")
                self.set_status("预览启动失败")

        threading.Thread(target=run, daemon=True).start()

    def stop_preview(self):
        """停止 hexo server — 使用保存的进程引用精准 kill"""
        if self.hexo_process:
            try:
                self.hexo_process.terminate()
                self.hexo_process.wait(timeout=5)
                self.hexo_process = None
                self.log("⏹️ 已停止本地预览")
            except Exception as e:
                self.log(f"⚠️ 终止预览进程失败: {e}")
                # 降级：尝试通过端口 kill
                self._kill_by_port()
        else:
            self.log("⚠️ 没有正在运行的预览进程")
    
    def _kill_by_port(self):
        """通过端口号查找并终止进程（降级方案）"""
        port = getattr(self, 'preview_port', 4000)
        try:
            if sys.platform == "win32":
                # 用 netstat 找 PID
                r = subprocess.run(
                    f'netstat -ano | findstr ":{port} "',
                    capture_output=True, text=True, shell=True, timeout=5
                )
                for line in r.stdout.split("\n"):
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.strip().split()
                        pid = parts[-1] if parts else ""
                        if pid.isdigit():
                            subprocess.run(["taskkill", "/f", "/pid", pid],
                                          capture_output=True, timeout=5)
                            self.log(f"⏹️ 已通过 PID={pid} 停止预览")
                            return
            else:
                subprocess.run(["pkill", "-f", f"hexo.*:{port}"],
                              capture_output=True, timeout=5)
                self.log("⏹️ 已停止预览")
        except Exception as e:
            self.log(f"⚠️ 停止预览失败: {e}")

    # ==================== 图片上传 ====================

    def upload_image_dialog(self):
        """上传图片对话框"""
        file = filedialog.askopenfilename(
            title="选择要上传的图片",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.gif *.webp *.bmp"),
                ("所有文件", "*.*"),
            ]
        )
        if not file:
            return

        self.img_log.insert("end", f"上传: {os.path.basename(file)}...\n")
        self.img_log.see("end")

        def do_upload():
            ok, result = upload_image(file, self.config)
            self.root.after(0, lambda: self.img_log.insert(
                "end",
                f"{'✅' if ok else '❌'} {result}\n"
            ))
            self.root.after(0, lambda: self.img_log.see("end"))

        threading.Thread(target=do_upload, daemon=True).start()

    def show_image_list(self):
        """查看图床图片列表（GitHub 模式）"""
        host = self.config.get("image_host", "local")
        if host != "github":
            messagebox.showinfo("提示", "仅 GitHub 图床支持查看列表")
            return

        token = self.config.get("github_token", "")
        if not token:
            messagebox.showwarning("提示", "请先配置 GitHub Token")
            return

        repo = self.config.get("github_image_repo", "maojunzc.github.io")
        path = self.config.get("github_image_path", "images/posts")
        branch = self.config.get("branch", "main")
        user = self.config.get("github_user", "maojunzc")

        api_url = (f"https://api.github.com/repos/{user}/{repo}"
                   f"/contents/{path}?ref={branch}")

        headers = {"Authorization": f"token {token}"}
        req = urllib.request.Request(api_url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if isinstance(data, list):
                    win = Toplevel(self.root)
                    win.title("图床图片列表")
                    win.geometry("500x400")
                    win.configure(bg=BG_DARK)

                    tree = ttk.Treeview(win, columns=("name", "size"), show="headings")
                    tree.heading("name", text="文件名")
                    tree.heading("size", text="大小")
                    tree.column("name", width=350)
                    tree.column("size", width=100)

                    for item in reversed(data):
                        size = f"{item.get('size', 0) / 1024:.1f} KB"
                        tree.insert("", "end", values=(item["name"], size))

                    tree.pack(fill="both", expand=True, padx=10, pady=10)
                else:
                    messagebox.showinfo("提示", "该目录为空或不是目录")
        except Exception as e:
            messagebox.showerror("错误", f"获取列表失败: {str(e)[:200]}")

    # ==================== 拖拽处理 ====================

    def on_drop(self, event):
        """处理拖拽文件事件"""
        files = self.root.tk.splitlist(event.data)
        for f in files:
            # 去掉可能的引号
            f = f.strip('"')
            ok, msg, result = drop_file_handler(f, self.config)
            self.log(f"{'✅' if ok else '❌'} {msg}")
            if ok and result and isinstance(result, str) and result.endswith(".md"):
                self.refresh_articles()

    # ==================== 设置 ====================

    def open_settings(self):
        """设置窗口（使用 Notebook 分多页）"""
        win = Toplevel(self.root)
        win.title("⚙️ 设置")
        win.geometry("620x520")
        win.configure(bg=BG_DARK)
        win.transient(self.root)
        win.grab_set()

        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        # 基础设置页
        basic = Frame(nb, bg=BG_CARD)
        nb.add(basic, text="  基础  ")
        self._build_settings_page(basic)

        # 图床设置页
        img_set = Frame(nb, bg=BG_CARD)
        nb.add(img_set, text="  图床  ")
        self._build_image_host_settings(img_set)

        # 高级设置页
        adv = Frame(nb, bg=BG_CARD)
        nb.add(adv, text="  高级  ")
        self._build_advanced_settings(adv)

        # 保存按钮
        btn_save = self._make_btn(win, "💾 保存设置", self._save_all_settings, 0)
        btn_save.pack(pady=8)

    def _build_settings_page(self, parent):
        """基础设置页"""
        parent.grid_columnconfigure(1, weight=1)

        fields = [
            ("仓库路径:", "repo_path", True, ""),
            ("远程地址:", "remote_url", True, ""),
            ("Git 用户名:", "git_name", False, ""),
            ("Git 邮箱:", "git_email", False, ""),
            ("Typora 路径:", "typora_path", True, ""),
            ("默认标签:", "default_tags", False, ""),
            ("默认分类:", "default_categories", False, ""),
        ]

        self._setting_vars = {}
        for i, (label, key, wide, _) in enumerate(fields):
            row_s = Frame(parent, bg=BG_CARD)
            row_s.grid(row=i, column=0, columnspan=3, sticky="ew", padx=15, pady=4)
            row_s.grid_columnconfigure(1, weight=1)

            Label(row_s, text=label, bg=BG_CARD, fg=TEXT_COLOR,
                  font=("Segoe UI", 9), width=14, anchor="w").grid(row=0, column=0)
            w = 45 if wide else 25
            var = StringVar(value=self.config.get(key, ""))
            Entry(row_s, textvariable=var, bg=BG_INPUT, fg=TEXT_COLOR,
                  insertbackground="white", relief="flat", width=w,
                  font=("Consolas", 9)).grid(row=0, column=1, sticky="ew", padx=5)
            self._setting_vars[key] = var

    def _build_image_host_settings(self, parent):
        """图床设置页"""
        parent.grid_columnconfigure(1, weight=1)

        # host 选择
        row_h = Frame(parent, bg=BG_CARD)
        row_h.grid(row=0, column=0, columnspan=3, sticky="ew", padx=15, pady=10)
        Label(row_h, text="存储方式:", bg=BG_CARD, fg=TEXT_COLOR,
              font=("Segoe UI", 9)).pack(side="left")
        self._set_host_var = StringVar(value=self.config.get("image_host", "local"))
        for label, val in [("本地", "local"), ("GitHub", "github"),
                            ("ImgBB", "imgbb"), ("SM.MS", "smms")]:
            Radiobutton(row_h, text=label, variable=self._set_host_var,
                        value=val, bg=BG_CARD, fg=TEXT_COLOR,
                        selectcolor=BG_INPUT, activebackground=BG_CARD,
                        activeforeground=TEXT_COLOR, font=("Segoe UI", 9)
                        ).pack(side="left", padx=8)

        # GitHub 图床字段
        gh_frame = Frame(parent, bg=BG_CARD)
        gh_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=15, pady=5)
        gh_frame.grid_columnconfigure(1, weight=1)

        gh_fields = [
            ("GitHub User:", "github_user"),
            ("GitHub Token:", "github_token"),
            ("图片仓库:", "github_image_repo"),
            ("图片路径:", "github_image_path"),
        ]
        for i, (label, key) in enumerate(gh_fields):
            Label(gh_frame, text=label, bg=BG_CARD, fg=TEXT_COLOR,
                  font=("Segoe UI", 9), width=14, anchor="w"
                  ).grid(row=i, column=0, sticky="w", pady=2)
            var = StringVar(value=self.config.get(key, ""))
            Entry(gh_frame, textvariable=var, bg=BG_INPUT, fg=TEXT_COLOR,
                  insertbackground="white", relief="flat", width=45,
                  font=("Consolas", 9)).grid(row=i, column=1, sticky="ew",
                                             padx=5, pady=2)
            if not hasattr(self, '_setting_vars'):
                self._setting_vars = {}
            self._setting_vars[key] = var

        # 第三方图床
        third_frame = Frame(parent, bg=BG_CARD)
        third_frame.grid(row=2, column=0, columnspan=3, sticky="ew",
                         padx=15, pady=5)
        third_frame.grid_columnconfigure(1, weight=1)

        third_fields = [
            ("ImgBB Key:", "imgbb_api_key"),
            ("SM.MS Key:", "smms_api_key"),
        ]
        for i, (label, key) in enumerate(third_fields):
            Label(third_frame, text=label, bg=BG_CARD, fg=TEXT_COLOR,
                  font=("Segoe UI", 9), width=14, anchor="w"
                  ).grid(row=i, column=0, sticky="w", pady=2)
            var = StringVar(value=self.config.get(key, ""))
            Entry(third_frame, textvariable=var, bg=BG_INPUT, fg=TEXT_COLOR,
                  insertbackground="white", relief="flat", width=45,
                  font=("Consolas", 9)).grid(row=i, column=1, sticky="ew",
                                             padx=5, pady=2)
            self._setting_vars[key] = var

        # 预览端口
        row_p = Frame(parent, bg=BG_CARD)
        row_p.grid(row=3, column=0, columnspan=3, sticky="ew", padx=15, pady=5)
        Label(row_p, text="预览端口:", bg=BG_CARD, fg=TEXT_COLOR,
              font=("Segoe UI", 9), width=14, anchor="w").pack(side="left")
        var = IntVar(value=self.config.get("preview_port", 4000))
        Entry(row_p, textvariable=var, bg=BG_INPUT, fg=TEXT_COLOR,
              insertbackground="white", relief="flat", width=10,
              font=("Consolas", 9)).pack(side="left", padx=5)
        self._setting_vars["preview_port"] = var

    def _build_advanced_settings(self, parent):
        """高级设置页"""
        parent.grid_columnconfigure(1, weight=1)

        # 写作模式
        row_w = Frame(parent, bg=BG_CARD)
        row_w.grid(row=0, column=0, columnspan=3, sticky="ew", padx=15, pady=10)
        self._adv_writing_var = BooleanVar(
            value=self.config.get("writing_mode", "default") != "default"
        )
        Checkbutton(
            row_w, text="经典灰色写作模式（白底黑字，专注写作）",
            variable=self._adv_writing_var, bg=BG_CARD, fg=TEXT_COLOR,
            selectcolor=BG_INPUT, activebackground=BG_CARD,
            activeforeground=TEXT_COLOR, font=("Segoe UI", 9),
        ).pack(anchor="w")

        # 自动推送
        row_a = Frame(parent, bg=BG_CARD)
        row_a.grid(row=1, column=0, columnspan=3, sticky="ew", padx=15, pady=5)
        self._adv_push_var = BooleanVar(
            value=self.config.get("enable_auto_push", True)
        )
        Checkbutton(
            row_a, text="发布后自动 git push",
            variable=self._adv_push_var, bg=BG_CARD, fg=TEXT_COLOR,
            selectcolor=BG_INPUT, activebackground=BG_CARD,
            activeforeground=TEXT_COLOR, font=("Segoe UI", 9),
        ).pack(anchor="w")

    def _save_current_settings(self):
        """保存当前面板的设置（内置设置页使用）"""
        # 敏感字段：如果显示的是脱敏值则保留原值
        _sensitive_keys = {"github_token", "imgbb_api_key", "smms_api_key", "git_token"}

        for key, var in self._setting_vars.items():
            val = var.get()
            if key in _sensitive_keys and val in ("", "***"):
                continue  # 保持原值不变
            if isinstance(var, IntVar) and key == "preview_port":
                self.config[key] = int(val) if val else 4000
            else:
                self.config[key] = val

        # 写入模式
        self.config["writing_mode"] = "classic" if self.writing_mode_var.get() else "default"
        self.config["enable_auto_push"] = self.auto_push_var.get()

        # image_host（从图床页获取）
        self.config["image_host"] = self.host_var.get()

        save_config(self.config)
        self.path_var.set(self.config.get("repo_path", ""))
        self.log("⚙️ 设置已保存")
        messagebox.showinfo("完成", "设置已保存")

    def _save_all_settings(self):
        """保存所有设置（弹出设置窗口使用）"""
        _sensitive_keys = {"github_token", "imgbb_api_key", "smms_api_key", "git_token"}

        # 基础设置
        for key, var in self._setting_vars.items():
            val = var.get()
            if key in _sensitive_keys and val in ("", "***"):
                continue  # 保持原值不变
            if isinstance(var, IntVar) and key == "preview_port":
                self.config[key] = int(val) if val else 4000
            else:
                self.config[key] = val

        # image_host
        if hasattr(self, '_set_host_var'):
            self.config["image_host"] = self._set_host_var.get()

        # 自动推送
        if hasattr(self, '_adv_push_var'):
            self.config["enable_auto_push"] = self._adv_push_var.get()

        # 写作模式
        if hasattr(self, '_adv_writing_var'):
            self.config["writing_mode"] = "classic" if self._adv_writing_var.get() else "default"

        save_config(self.config)

        # 同步 path_var
        self.path_var.set(self.config.get("repo_path", ""))

        self.log("⚙️ 设置已保存")
        messagebox.showinfo("完成", "设置已保存")

    def _toggle_writing_mode(self):
        """切换写作模式（从设置面板快捷切换）"""
        is_writing = self.writing_mode_var.get()
        self.config["writing_mode"] = "classic" if is_writing else "default"
        self._apply_writing_mode()

    def _apply_writing_mode(self):
        """应用写作模式样式"""
        is_writing = self.config.get("writing_mode", "default") == "classic"
        if is_writing:
            self.root.configure(bg=WRITING_BG)
            self._update_widget_bg(self.root, WRITING_BG)
        else:
            self.root.configure(bg=BG_DARK)
            self._update_widget_bg(self.root, BG_DARK)

    def _update_widget_bg(self, widget, bg):
        """递归更新所有 widget 背景色（跳过 ttk 组件，它们使用 Style 系统）"""
        # 跳过 ttk 组件
        if isinstance(widget, (ttk.Treeview, ttk.Notebook, ttk.Progressbar,
                              ttk.Scrollbar, ttk.Entry, ttk.Combobox)):
            return
        try:
            widget.configure(bg=bg)
        except Exception:
            pass
        try:
            for child in widget.winfo_children():
                self._update_widget_bg(child, bg)
        except Exception:
            pass

    # ==================== 启动 ====================

    def run(self):
        self.root.mainloop()


def main():
    root = Tk()
    app = BlogManagerApp(root)
    app.run()


if __name__ == "__main__":
    main()
