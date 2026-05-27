"""
CLI入口模块 / CLI Entry Module

提供 `python -m mindflow_cli` 命令的入口点。
Provides the entry point for `python -m mindflow_cli` command.
"""

from .cli import main


if __name__ == "__main__":
    import sys
    sys.exit(main())
