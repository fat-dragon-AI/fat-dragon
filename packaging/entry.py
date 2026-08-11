"""PyInstaller / 直跑入口（绝对导入）。"""
from lch.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
