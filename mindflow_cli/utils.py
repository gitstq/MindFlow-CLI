"""
工具函数模块 / Utility Functions Module

提供时间格式化、文本处理、终端颜色输出和进度条等通用工具函数。
Provides common utility functions including time formatting, text processing,
terminal color output, and progress bars.
"""

from __future__ import annotations

import math
import os
import re
import sys
import time
from datetime import datetime, timedelta
from typing import List, Optional, Tuple


# ============================================================
# 终端颜色支持 / Terminal Color Support
# ============================================================

class Colors:
    """
    终端颜色常量 / Terminal color constants

    使用ANSI转义码实现跨平台终端颜色输出。
    Uses ANSI escape codes for cross-platform terminal color output.
    """
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"

    # 前景色 / Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    # 背景色 / Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


def supports_color() -> bool:
    """
    检测终端是否支持颜色 / Check if terminal supports color

    返回 / Returns:
        是否支持颜色输出 / Whether color output is supported
    """
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") in ("dumb", ""):
        return False
    if sys.platform == "win32":
        return os.environ.get("ANSICON") is not None or "256color" in os.environ.get("TERM", "")
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def colored(text: str, color: str, bold: bool = False) -> str:
    """
    为文本添加颜色 / Add color to text

    参数 / Args:
        text: 原始文本 / Original text
        color: 颜色代码 / Color code
        bold: 是否加粗 / Whether to use bold

    返回 / Returns:
        带颜色的文本 / Colored text
    """
    if not supports_color():
        return text
    prefix = color
    if bold:
        prefix = Colors.BOLD + color
    return f"{prefix}{text}{Colors.RESET}"


def success(text: str) -> str:
    """成功信息（绿色） / Success message (green)"""
    return colored(text, Colors.GREEN)


def error(text: str) -> str:
    """错误信息（红色） / Error message (red)"""
    return colored(text, Colors.RED)


def warning(text: str) -> str:
    """警告信息（黄色） / Warning message (yellow)"""
    return colored(text, Colors.YELLOW)


def info(text: str) -> str:
    """信息提示（蓝色） / Info message (blue)"""
    return colored(text, Colors.BLUE)


def dim(text: str) -> str:
    """暗淡文本 / Dimmed text"""
    return colored(text, Colors.GRAY)


def bold(text: str) -> str:
    """加粗文本 / Bold text"""
    return colored(text, Colors.WHITE, bold=True)


def print_success(text: str) -> None:
    """打印成功信息 / Print success message"""
    print(f"  {colored('[OK]', Colors.GREEN)} {text}")


def print_error(text: str) -> None:
    """打印错误信息 / Print error message"""
    print(f"  {colored('[ERROR]', Colors.RED)} {text}", file=sys.stderr)


def print_warning(text: str) -> None:
    """打印警告信息 / Print warning message"""
    print(f"  {colored('[WARN]', Colors.YELLOW)} {text}")


def print_info(text: str) -> None:
    """打印信息提示 / Print info message"""
    print(f"  {colored('[INFO]', Colors.BLUE)} {text}")


# ============================================================
# 时间格式化 / Time Formatting
# ============================================================

def format_datetime(dt_str: str) -> str:
    """
    格式化ISO时间字符串为可读格式 / Format ISO datetime string to readable format

    参数 / Args:
        dt_str: ISO格式的时间字符串 / ISO format datetime string

    返回 / Returns:
        格式化后的时间字符串 / Formatted time string
    """
    try:
        dt = datetime.fromisoformat(dt_str)
        now = datetime.now()
        delta = now - dt

        if delta < timedelta(seconds=60):
            return "刚刚"
        elif delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() / 60)
            return f"{minutes}分钟前"
        elif delta < timedelta(days=1):
            hours = int(delta.total_seconds() / 3600)
            return f"{hours}小时前"
        elif delta < timedelta(days=7):
            days = delta.days
            return f"{days}天前"
        else:
            return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return dt_str


def format_duration(seconds: float) -> str:
    """
    格式化时长 / Format duration

    参数 / Args:
        seconds: 秒数 / Number of seconds

    返回 / Returns:
        格式化的时长字符串 / Formatted duration string
    """
    if seconds < 0.001:
        return "0ms"
    elif seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def now_iso() -> str:
    """获取当前时间的ISO格式字符串 / Get current time in ISO format"""
    return datetime.now().isoformat()


# ============================================================
# 文本处理 / Text Processing
# ============================================================

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本 / Truncate text

    参数 / Args:
        text: 原始文本 / Original text
        max_length: 最大长度 / Maximum length
        suffix: 截断后缀 / Truncation suffix

    返回 / Returns:
        截断后的文本 / Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """
    清理文本（去除多余空白） / Clean text (remove extra whitespace)

    参数 / Args:
        text: 原始文本 / Original text

    返回 / Returns:
        清理后的文本 / Cleaned text
    """
    # 替换多个连续空白为单个空格 / Replace multiple whitespace with single space
    text = re.sub(r'[ \t]+', ' ', text)
    # 替换多个连续换行为两个换行 / Replace multiple newlines with two
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def count_words(text: str) -> int:
    """
    统计字数（支持中英文混合） / Count words (supports mixed Chinese and English)

    参数 / Args:
        text: 文本 / Text

    返回 / Returns:
        字数 / Word count
    """
    # 统计中文字符 / Count Chinese characters
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # 统计英文单词 / Count English words
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    return chinese_chars + english_words


def count_lines(text: str) -> int:
    """
    统计行数 / Count lines

    参数 / Args:
        text: 文本 / Text

    返回 / Returns:
        行数 / Line count
    """
    if not text:
        return 0
    return len(text.split('\n'))


def highlight_text(text: str, keywords: List[str]) -> str:
    """
    高亮文本中的关键词 / Highlight keywords in text

    参数 / Args:
        text: 原始文本 / Original text
        keywords: 关键词列表 / List of keywords

    返回 / Returns:
        高亮后的文本 / Highlighted text
    """
    if not keywords or not supports_color():
        return text

    result = text
    for keyword in keywords:
        if keyword:
            pattern = re.compile(
                re.escape(keyword), re.IGNORECASE
            )
            result = pattern.sub(
                lambda m: colored(m.group(), Colors.YELLOW, bold=True),
                result
            )
    return result


def wrap_text(text: str, width: int = 80) -> str:
    """
    文本自动换行 / Text word wrapping

    参数 / Args:
        text: 原始文本 / Original text
        width: 每行最大宽度 / Maximum width per line

    返回 / Returns:
        换行后的文本 / Wrapped text
    """
    if width <= 0:
        return text

    lines = text.split('\n')
    wrapped_lines = []

    for line in lines:
        if len(line) <= width:
            wrapped_lines.append(line)
            continue

        # 处理中文和英文混合换行 / Handle mixed Chinese-English wrapping
        current_line = ""
        for char in line:
            if len(current_line) >= width:
                wrapped_lines.append(current_line)
                current_line = char
            else:
                current_line += char
        if current_line:
            wrapped_lines.append(current_line)

    return '\n'.join(wrapped_lines)


def generate_slug(text: str) -> str:
    """
    生成URL友好的slug / Generate URL-friendly slug

    参数 / Args:
        text: 原始文本 / Original text

    返回 / Returns:
        slug字符串 / Slug string
    """
    # 转小写 / Convert to lowercase
    slug = text.lower()
    # 移除特殊字符 / Remove special characters
    slug = re.sub(r'[^\w\s-]', '', slug)
    # 替换空白为连字符 / Replace whitespace with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    # 移除首尾连字符 / Remove leading/trailing hyphens
    slug = slug.strip('-')
    # 压缩连续连字符 / Compress consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    return slug


# ============================================================
# 进度条 / Progress Bar
# ============================================================

class ProgressBar:
    """
    终端进度条 / Terminal progress bar

    在终端中显示美观的进度条，支持百分比、速度和ETA显示。
    Displays a beautiful progress bar in the terminal with percentage,
    speed, and ETA display.

    用法 / Usage:
        bar = ProgressBar(total=100, description="处理中")
        for i in range(100):
            bar.update(i + 1)
        bar.finish()
    """

    def __init__(
        self,
        total: int = 100,
        description: str = "",
        bar_width: int = 40,
        show_speed: bool = True,
        show_eta: bool = True,
    ) -> None:
        """
        初始化进度条 / Initialize progress bar

        参数 / Args:
            total: 总数量 / Total count
            description: 描述文本 / Description text
            bar_width: 进度条宽度 / Progress bar width
            show_speed: 是否显示速度 / Whether to show speed
            show_eta: 是否显示预计剩余时间 / Whether to show ETA
        """
        self.total = total
        self.description = description
        self.bar_width = bar_width
        self.show_speed = show_speed
        self.show_eta = show_eta
        self.current = 0
        self.start_time = time.time()
        self._last_print_len = 0

    def update(self, current: Optional[int] = None, increment: int = 1) -> None:
        """
        更新进度 / Update progress

        参数 / Args:
            current: 当前值（如果提供则直接设置） / Current value (set directly if provided)
            increment: 增量 / Increment
        """
        if current is not None:
            self.current = current
        else:
            self.current += increment

        self._print_progress()

    def _print_progress(self) -> None:
        """打印进度条 / Print progress bar"""
        if self.total <= 0:
            return

        percentage = min(self.current / self.total, 1.0)
        filled = int(self.bar_width * percentage)
        empty = self.bar_width - filled

        # 进度条字符 / Progress bar characters
        bar = colored("█" * filled, Colors.CYAN) + "░" * empty

        # 百分比 / Percentage
        pct_str = f"{percentage * 100:.1f}%"

        # 计数 / Count
        count_str = f"{self.current}/{self.total}"

        # 速度 / Speed
        elapsed = time.time() - self.start_time
        speed_str = ""
        if self.show_speed and elapsed > 0:
            speed = self.current / elapsed
            if speed >= 1:
                speed_str = f" | {speed:.1f}/s"
            else:
                speed_str = f" | {1/speed:.1f}s/个"

        # ETA / Estimated time of arrival
        eta_str = ""
        if self.show_eta and self.current > 0:
            remaining = (self.total - self.current) / (self.current / elapsed) if elapsed > 0 else 0
            eta_str = f" | ETA: {format_duration(remaining)}"

        # 组装输出 / Assemble output
        desc = f"{self.description} " if self.description else ""
        line = f"\r{desc}[{bar}] {pct_str} ({count_str}){speed_str}{eta_str}"

        # 清除之前的输出 / Clear previous output
        clear = "\r" + " " * self._last_print_len + "\r"
        sys.stdout.write(clear)
        sys.stdout.write(line)
        sys.stdout.flush()
        self._last_print_len = len(line)

    def finish(self) -> None:
        """完成进度条 / Finish progress bar"""
        self.current = self.total
        self._print_progress()
        elapsed = time.time() - self.start_time
        print(f"\n  {success('完成')} 耗时: {format_duration(elapsed)}")

    def reset(self) -> None:
        """重置进度条 / Reset progress bar"""
        self.current = 0
        self.start_time = time.time()
        self._last_print_len = 0


# ============================================================
# 分页工具 / Pagination Utilities
# ============================================================

def paginate(items: List, page: int = 1, per_page: int = 10) -> Tuple[List, dict]:
    """
    对列表进行分页 / Paginate a list

    参数 / Args:
        items: 原始列表 / Original list
        page: 页码（从1开始） / Page number (1-based)
        per_page: 每页数量 / Items per page

    返回 / Returns:
        (当前页数据, 分页信息) / (Current page data, pagination info)
    """
    total = len(items)
    total_pages = max(1, math.ceil(total / per_page))
    page = max(1, min(page, total_pages))

    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]

    pagination_info = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }

    return page_items, pagination_info


def print_table(
    headers: List[str],
    rows: List[List[str]],
    max_col_width: int = 30,
    title: str = "",
) -> None:
    """
    打印格式化表格 / Print formatted table

    参数 / Args:
        headers: 表头列表 / List of headers
        rows: 数据行列表 / List of data rows
        max_col_width: 列最大宽度 / Maximum column width
        title: 表格标题 / Table title
    """
    if not rows:
        print(dim("  (无数据)"))
        return

    # 截断列内容 / Truncate column content
    display_rows = []
    for row in rows:
        display_row = []
        for cell in row:
            cell_str = str(cell)
            if len(cell_str) > max_col_width:
                cell_str = cell_str[:max_col_width - 3] + "..."
            display_row.append(cell_str)
        display_rows.append(display_row)

    # 计算列宽 / Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in display_rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(cell))

    # 打印标题 / Print title
    if title:
        print(f"\n  {bold(title)}")
        print(f"  {'─' * (sum(col_widths) + len(headers) * 3 + 1)}")

    # 打印表头 / Print header
    header_line = "  │ "
    for i, h in enumerate(headers):
        header_line += bold(h.ljust(col_widths[i])) + " │ "
    print(header_line)

    # 打印分隔线 / Print separator
    sep_line = "  ├"
    for w in col_widths:
        sep_line += "─" * (w + 2) + "┼"
    sep_line = sep_line[:-1] + "┤"
    print(sep_line)

    # 打印数据行 / Print data rows
    for row in display_rows:
        row_line = "  │ "
        for i, cell in enumerate(row):
            row_line += cell.ljust(col_widths[i]) + " │ "
        print(row_line)

    # 打印底部边框 / Print bottom border
    bottom_line = "  └"
    for w in col_widths:
        bottom_line += "─" * (w + 2) + "┴"
    bottom_line = bottom_line[:-1] + "┘"
    print(bottom_line)


# ============================================================
# 输入工具 / Input Utilities
# ============================================================

def prompt_input(
    prompt: str,
    default: str = "",
    required: bool = False,
    password: bool = False,
) -> str:
    """
    获取用户输入 / Get user input

    参数 / Args:
        prompt: 提示文本 / Prompt text
        default: 默认值 / Default value
        required: 是否必填 / Whether required
        password: 是否为密码输入 / Whether it's a password input

    返回 / Returns:
        用户输入的值 / User input value
    """
    if default:
        prompt_text = f"  {prompt} [{dim(default)}]: "
    else:
        prompt_text = f"  {prompt}: "

    if password:
        import getpass
        value = getpass.getpass(prompt_text)
    else:
        value = input(prompt_text)

    if not value and default:
        value = default

    if required and not value:
        print_error("此项为必填项")
        return prompt_input(prompt, default, required, password)

    return value


def prompt_confirm(prompt: str, default: bool = False) -> bool:
    """
    确认提示 / Confirmation prompt

    参数 / Args:
        prompt: 提示文本 / Prompt text
        default: 默认值 / Default value

    返回 / Returns:
        用户确认结果 / User confirmation result
    """
    hint = "Y/n" if default else "y/N"
    value = input(f"  {prompt} [{hint}]: ").strip().lower()

    if not value:
        return default
    return value in ("y", "yes", "是")


def prompt_choice(prompt: str, choices: List[str], default: int = 0) -> int:
    """
    选择提示 / Choice prompt

    参数 / Args:
        prompt: 提示文本 / Prompt text
        choices: 选项列表 / List of choices
        default: 默认选项索引 / Default choice index

    返回 / Returns:
        选择的索引 / Selected index
    """
    for i, choice in enumerate(choices):
        marker = ">" if i == default else " "
        print(f"  {marker} {i + 1}. {choice}")

    while True:
        try:
            value = input(f"\n  {prompt} [{default + 1}]: ").strip()
            if not value:
                return default
            idx = int(value) - 1
            if 0 <= idx < len(choices):
                return idx
            print_error(f"请输入 1-{len(choices)} 之间的数字")
        except ValueError:
            print_error("请输入有效的数字")


# ============================================================
# 文件大小格式化 / File Size Formatting
# ============================================================

def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小 / Format file size

    参数 / Args:
        size_bytes: 字节数 / Number of bytes

    返回 / Returns:
        格式化的文件大小 / Formatted file size
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


# ============================================================
# 安全工具 / Security Utilities
# ============================================================

def sanitize_filename(filename: str) -> str:
    """
    清理文件名（移除不安全字符） / Sanitize filename (remove unsafe characters)

    参数 / Args:
        filename: 原始文件名 / Original filename

    返回 / Returns:
        安全的文件名 / Safe filename
    """
    # 移除路径分隔符和其他不安全字符 / Remove path separators and unsafe chars
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    # 移除首尾空白和点 / Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    # 限制长度 / Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    return filename or "untitled"
