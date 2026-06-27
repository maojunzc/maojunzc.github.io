"""
打包 blog-publisher 为独立 exe 安装程序
用法: python build.py
"""

import os
import sys
import subprocess
import shutil

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    publisher_script = os.path.join(script_dir, "blog_publisher.py")
    
    # 检查 PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # 创建输出目录
    dist_dir = os.path.join(script_dir, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    
    # 打包
    print("📦 正在打包 blog-publisher...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",           # 单文件 exe
        "--name", "blog-publisher",
        "--distpath", dist_dir,
        "--add-data", f"config.json{os.pathsep}.",  # 包含配置文件
        "--add-data", f"template.md{os.pathsep}.",
        "--hidden-import", "PIL",
        "--console",           # 显示控制台窗口（可以看到输出）
        publisher_script
    ]
    
    result = subprocess.run(cmd, cwd=script_dir)
    if result.returncode != 0:
        print("❌ 打包失败")
        sys.exit(1)
    
    exe_path = os.path.join(dist_dir, "blog-publisher.exe")
    if os.path.exists(exe_path):
        print(f"✅ 打包成功!")
        print(f"   → {exe_path}")
        print(f"   → 大小: {os.path.getsize(exe_path) / 1024 / 1024:.1f} MB")
        
        # 复制配置文件
        shutil.copy2(
            os.path.join(script_dir, "config.json"),
            os.path.join(dist_dir, "config.json")
        )
        print(f"   → 配置文件已复制到输出目录")
        print(f"\n使用方法:")
        print(f"  1. 编辑 dist/config.json 设置你的仓库路径")
        print(f"  2. 运行 blog-publisher.exe install 注册右键菜单")
        print(f"  3. 在 .md 文件上右键 -> 上传到博客")
    else:
        print("❌ 打包后未找到 exe 文件")


if __name__ == "__main__":
    main()
