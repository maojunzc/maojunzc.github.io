"""
Blog Manager - 打包脚本 (PyInstaller + UPX 压缩)
用法: python build.py
"""

import os
import sys
import shutil
import subprocess
import platform

# ============ 配置 ============
APP_NAME = "BlogManager"
ENTRY_FILE = "app.py"
ICON_FILE = "icon.ico"  # 可选图标
DIST_DIR = "dist"
BUILD_DIR = "build"
SPEC_DIR = "."

# PyInstaller 参数
PYINSTALLER_ARGS = [
    "--name", APP_NAME,
    "--onefile",           # 打包成单个 exe
    "--windowed",          # 无控制台窗口
    "--clean",             # 清理临时文件
    "--noconfirm",         # 不确认覆盖
    f"--distpath={DIST_DIR}",
    f"--workpath={BUILD_DIR}",
    f"--specpath={SPEC_DIR}",
    # 排除不需要的模块以减小体积
    "--exclude-module", "matplotlib",
    "--exclude-module", "numpy",
    "--exclude-module", "pandas",
    "--exclude-module", "PIL",
    "--exclude-module", "tkinter.test",
    "--exclude-module", "unittest",
    "--exclude-module", "test",
    "--exclude-module", "setuptools",
    # 隐藏导入
    "--hidden-import", "core",
    "--hidden-import", "tkinter",
    "--hidden-import", "tkinter.ttk",
    "--hidden-import", "tkinter.scrolledtext",
    "--hidden-import", "tkinter.filedialog",
    "--hidden-import", "tkinter.messagebox",
    "--hidden-import", "threading",
    "--hidden-import", "subprocess",
    "--hidden-import", "webbrowser",
    "--hidden-import", "shutil",
    "--hidden-import", "json",
    "--hidden-import", "os",
    "--hidden-import", "sys",
    "--hidden-import", "time",
    "--hidden-import", "datetime",
    "--hidden-import", "platform",
]

# 如果有图标则添加
if os.path.exists(ICON_FILE):
    PYINSTALLER_ARGS.extend(["--icon", ICON_FILE])

# UPX 路径（如果系统 PATH 中有则不需要指定）
UPX_DIR = None  # e.g. "C:/tools/upx"


def check_prerequisites():
    """检查打包依赖"""
    errors = []

    # 检查 Python 版本
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 8):
        errors.append("需要 Python 3.8+")

    # 检查 PyInstaller
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        errors.append("未安装 PyInstaller，请运行: pip install pyinstaller")

    # 检查 UPX
    upx_cmd = "upx"
    if UPX_DIR:
        upx_cmd = os.path.join(UPX_DIR, "upx.exe" if platform.system() == "Windows" else "upx")

    try:
        result = subprocess.run([upx_cmd, "--version"],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            ver = result.stdout.strip().split("\n")[0]
            print(f"✓ UPX: {ver}")
        else:
            errors.append("UPX 不可用，将跳过压缩（可去 https://upx.github.io/ 下载）")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        errors.append("UPX 未安装，将跳过压缩（可从 https://upx.github.io/ 下载）")

    return errors, upx_cmd


def clean_build():
    """清理之前的构建产物"""
    for d in [DIST_DIR, BUILD_DIR]:
        if os.path.isdir(d):
            shutil.rmtree(d)
            print(f"  清理: {d}/")

    # 清理 .spec 文件
    spec_file = f"{APP_NAME}.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)
        print(f"  清理: {spec_file}")


def build_executable():
    """执行 PyInstaller 打包"""
    args = [sys.executable, "-m", "PyInstaller"] + PYINSTALLER_ARGS + [ENTRY_FILE]

    print(f"\n{'='*50}")
    print(f"打包命令: {' '.join(args)}")
    print(f"{'='*50}\n")

    result = subprocess.run(args, capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ 打包失败!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False

    print(result.stdout)
    if result.stderr:
        print("Warnings:", result.stderr)

    return True


def compress_executable(upx_cmd):
    """使用 UPX 压缩 exe"""
    exe_name = f"{APP_NAME}.exe"
    exe_path = os.path.join(DIST_DIR, exe_name)

    if not os.path.exists(exe_path):
        print(f"❌ 未找到 {exe_path}")
        return False

    original_size = os.path.getsize(exe_path)
    print(f"\n原始大小: {original_size / 1024 / 1024:.1f} MB")

    print("正在 UPX 压缩...")
    result = subprocess.run(
        [upx_cmd, "--best", "--lzma", exe_path],
        capture_output=True, text=True, timeout=120
    )

    if result.returncode == 0:
        compressed_size = os.path.getsize(exe_path)
        ratio = (1 - compressed_size / original_size) * 100
        print(f"✓ 压缩完成!")
        print(f"  压缩后: {compressed_size / 1024 / 1024:.1f} MB")
        print(f"  压缩率: {ratio:.1f}%")
        return True
    else:
        print(f"⚠ UPX 压缩失败: {result.stderr}")
        return False


def copy_resources():
    """复制配置文件等到 dist 目录"""
    dist_dir = DIST_DIR
    os.makedirs(dist_dir, exist_ok=True)

    # 复制 config.json 作为示例
    if os.path.exists("config.json"):
        dst = os.path.join(dist_dir, "config.json")
        shutil.copy2("config.json", dst)
        print(f"  复制: config.json → {dst}")


def main():
    print(f"\n{'='*50}")
    print(f"  Blog Manager 打包脚本")
    print(f"{'='*50}\n")

    # 1. 检查依赖
    print("检查依赖...")
    errors, upx_cmd = check_prerequisites()
    if errors:
        print("\n⚠ 问题:")
        for e in errors:
            print(f"  • {e}")

    # 2. 清理
    print("\n清理旧构建...")
    clean_build()

    # 3. 打包
    print("\n开始打包...")
    if not build_executable():
        print("\n❌ 打包失败，请检查错误信息")
        sys.exit(1)

    # 4. 压缩
    upx_ok = True
    try:
        compress_executable(upx_cmd)
    except Exception as e:
        print(f"⚠ 压缩跳过: {e}")
        upx_ok = False

    # 5. 复制资源
    print("\n复制资源文件...")
    copy_resources()

    # 6. 完成
    exe_path = os.path.join(DIST_DIR, f"{APP_NAME}.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / 1024 / 1024
        print(f"\n{'='*50}")
        print(f"  ✓ 打包完成!")
        print(f"  文件: {exe_path}")
        print(f"  大小: {size_mb:.1f} MB")
        print(f"{'='*50}\n")

        if not upx_ok:
            print("提示: 安装 UPX 可进一步减小 exe 体积")
            print("  下载: https://upx.github.io/\n")
    else:
        print(f"\n❌ 未生成 exe: {exe_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
