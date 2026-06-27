"""
Build script - 打包 Blog Manager 为 Windows 独立 exe
用法: python build.py
"""

import os
import sys
import subprocess
import shutil

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 安装依赖
    deps = ["ttkbootstrap", "pyinstaller"]
    for dep in deps:
        try:
            __import__(dep.replace("-", "_"))
        except ImportError:
            print(f"正在安装 {dep}...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
    
    # 清理旧构建
    for d in ["build", "dist", "__pycache__"]:
        p = os.path.join(script_dir, d)
        if os.path.exists(p):
            shutil.rmtree(p, ignore_errors=True)
    
    # 打包
    print("📦 打包 Blog Manager...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",           # 无控制台窗口
        "--name", "Blog-Manager",
        "--icon", "NONE",
        "--add-data", f"config.json{os.pathsep}.",
        "--hidden-import", "PIL",
        "--hidden-import", "ttkbootstrap",
        "--clean",
        "--noconfirm",
        "app.py"
    ]
    
    result = subprocess.run(cmd, cwd=script_dir)
    if result.returncode != 0:
        print("❌ 打包失败")
        sys.exit(1)
    
    # 复制配置文件到输出目录
    dist_dir = os.path.join(script_dir, "dist")
    exe_path = os.path.join(dist_dir, "Blog-Manager.exe")
    
    if os.path.exists(exe_path):
        shutil.copy2(os.path.join(script_dir, "config.json"), 
                    os.path.join(dist_dir, "config.json"))
        
        size_mb = os.path.getsize(exe_path) / 1024 / 1024
        print(f"\n✅ 打包成功!")
        print(f"   → {exe_path}")
        print(f"   → 大小: {size_mb:.1f} MB")
        print(f"\n📋 使用说明:")
        print(f"  1. 将 dist 目录移到任何你喜欢的位置")
        print(f"  2. 运行 dist/Blog-Manager.exe")
        print(f"  3. 首次运行先在设置中配置仓库路径")
        print(f"\n⚡ 快捷方式:")
        print(f"  可将 Blog-Manager.exe 发送到桌面快捷方式")
    else:
        print("❌ 打包后未找到 exe 文件")

if __name__ == "__main__":
    main()
