"""
TUI交互式界面模块 / TUI Interactive Interface Module

使用curses实现的终端用户界面，提供仪表盘、知识浏览和工作流执行监控。
Terminal user interface implemented with curses, providing dashboard,
knowledge browsing, and workflow execution monitoring.
"""

from __future__ import annotations

import curses
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from .config import Config
from .models import KnowledgeSnippet, Workflow
from .search_engine import SearchEngine
from .storage import Storage
from .utils import format_datetime, truncate_text


# ============================================================
# 颜色主题 / Color Themes
# ============================================================

class Theme:
    """颜色主题定义 / Color theme definitions"""

    # 颜色对索引 / Color pair indices
    NORMAL = 0
    TITLE = 1
    HIGHLIGHT = 2
    SUCCESS = 3
    WARNING = 4
    ERROR = 5
    DIM = 6
    BORDER = 7
    SELECTED = 8
    HEADER = 9
    TAG = 10
    KEYBINDING = 11
    PROGRESS = 12
    SEARCH_HIGHLIGHT = 13

    @staticmethod
    def init_colors() -> None:
        """初始化curses颜色 / Initialize curses colors"""
        curses.start_color()
        curses.use_default_colors()

        # 基础颜色对 / Basic color pairs
        curses.init_pair(Theme.TITLE, curses.COLOR_CYAN, -1)
        curses.init_pair(Theme.HIGHLIGHT, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(Theme.SUCCESS, curses.COLOR_GREEN, -1)
        curses.init_pair(Theme.WARNING, curses.COLOR_YELLOW, -1)
        curses.init_pair(Theme.ERROR, curses.COLOR_RED, -1)
        curses.init_pair(Theme.DIM, curses.COLOR_GRAY, -1)
        curses.init_pair(Theme.BORDER, curses.COLOR_BLUE, -1)
        curses.init_pair(Theme.SELECTED, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(Theme.HEADER, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(Theme.TAG, curses.COLOR_MAGENTA, -1)
        curses.init_pair(Theme.KEYBINDING, curses.COLOR_YELLOW, -1)
        curses.init_pair(Theme.PROGRESS, curses.COLOR_GREEN, -1)
        curses.init_pair(Theme.SEARCH_HIGHLIGHT, curses.COLOR_YELLOW, curses.COLOR_RED)


# ============================================================
# UI组件 / UI Components
# ============================================================

class Panel:
    """
    面板基类 / Base Panel class

    TUI中的可重用面板组件。
    Reusable panel component in the TUI.
    """

    def __init__(self, name: str = "") -> None:
        self.name = name
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0

    def set_position(self, x: int, y: int, width: int, height: int) -> None:
        """设置面板位置和大小 / Set panel position and size"""
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self, stdscr: Any) -> None:
        """绘制面板 / Draw panel"""
        pass

    def draw_border(self, stdscr: Any, title: str = "") -> None:
        """绘制面板边框 / Draw panel border"""
        if self.width < 3 or self.height < 3:
            return

        # 绘制边框 / Draw border
        stdscr.attron(curses.color_pair(Theme.BORDER))
        stdscr.border(
            0, 0, 0, 0,  # 左上右下 / left top right bottom
            0, 0, 0, 0,
        )
        stdscr.attroff(curses.color_pair(Theme.BORDER))

        # 绘制标题 / Draw title
        if title:
            stdscr.attron(curses.color_pair(Theme.HEADER))
            title_text = f" {title} "
            if len(title_text) > self.width - 4:
                title_text = title_text[:self.width - 5] + " "
            stdscr.addstr(0, 2, title_text)
            stdscr.attroff(curses.color_pair(Theme.HEADER))


class StatusBar(Panel):
    """状态栏组件 / Status bar component"""

    def __init__(self) -> None:
        super().__init__("statusbar")
        self.message = ""
        self.message_type = "info"  # info, success, warning, error

    def set_message(self, message: str, msg_type: str = "info") -> None:
        """设置状态消息 / Set status message"""
        self.message = message
        self.message_type = msg_type

    def draw(self, stdscr: Any) -> None:
        """绘制状态栏 / Draw status bar"""
        if self.height < 1:
            return

        color_map = {
            "info": Theme.TITLE,
            "success": Theme.SUCCESS,
            "warning": Theme.WARNING,
            "error": Theme.ERROR,
        }
        color = color_map.get(self.message_type, Theme.NORMAL)

        # 清除行 / Clear line
        stdscr.move(self.y, self.x)
        stdscr.clrtoeol()

        # 绘制消息 / Draw message
        stdscr.attron(curses.color_pair(color))
        msg = self.message[:self.width - 2]
        stdscr.addstr(self.y, self.x + 1, msg)
        stdscr.attroff(curses.color_pair(color))


class KeyBindingBar(Panel):
    """快捷键提示栏 / Keybinding hint bar"""

    def __init__(self) -> None:
        super().__init__("keybindings")
        self.bindings: List[Tuple[str, str]] = []

    def set_bindings(self, bindings: List[Tuple[str, str]]) -> None:
        """设置快捷键 / Set keybindings"""
        self.bindings = bindings

    def draw(self, stdscr: Any) -> None:
        """绘制快捷键栏 / Draw keybinding bar"""
        if self.height < 1:
            return

        stdscr.move(self.y, self.x)
        stdscr.clrtoeol()

        x_offset = self.x + 1
        for key, desc in self.bindings:
            if x_offset + len(key) + len(desc) + 4 > self.x + self.width:
                break

            # 绘制按键 / Draw key
            stdscr.attron(curses.color_pair(Theme.KEYBINDING))
            stdscr.addstr(self.y, x_offset, f"[{key}]")
            stdscr.attroff(curses.color_pair(Theme.KEYBINDING))

            x_offset += len(key) + 2

            # 绘制描述 / Draw description
            stdscr.addstr(self.y, x_offset, f" {desc}")
            x_offset += len(desc) + 2


# ============================================================
# 视图 / Views
# ============================================================

class DashboardView:
    """仪表盘视图 / Dashboard view"""

    def __init__(self, storage: Storage) -> None:
        self.storage = storage
        self.stats: Dict[str, Any] = {}

    def refresh_data(self) -> None:
        """刷新数据 / Refresh data"""
        self.stats = self.storage.get_statistics()

    def draw(self, stdscr: Any, x: int, y: int, w: int, h: int) -> None:
        """绘制仪表盘 / Draw dashboard"""
        # 标题 / Title
        stdscr.attron(curses.color_pair(Theme.TITLE) | curses.A_BOLD)
        stdscr.addstr(y, x + 2, "MindFlow Dashboard")
        stdscr.attroff(curses.color_pair(Theme.TITLE) | curses.A_BOLD)

        # 统计信息 / Statistics
        cy = y + 2
        stats_items = [
            ("Knowledge Snippets", str(self.stats.get("total_snippets", 0))),
            ("Tags", str(self.stats.get("total_tags", 0))),
            ("Workflows", str(self.stats.get("total_workflows", 0))),
        ]

        for label, value in stats_items:
            if cy >= y + h - 1:
                break
            stdscr.addstr(cy, x + 2, label + ":")
            stdscr.attron(curses.color_pair(Theme.TITLE) | curses.A_BOLD)
            stdscr.addstr(cy, x + w - len(value) - 2, value)
            stdscr.attroff(curses.color_pair(Theme.TITLE) | curses.A_BOLD)
            cy += 1

        # 热门标签 / Top tags
        cy += 1
        stdscr.attron(curses.A_BOLD)
        stdscr.addstr(cy, x + 2, "Top Tags:")
        stdscr.attroff(curses.A_BOLD)
        cy += 1

        for tag_info in self.stats.get("top_tags", [])[:5]:
            if cy >= y + h - 1:
                break
            name = tag_info["name"]
            count = str(tag_info["count"])
            stdscr.addstr(cy, x + 4, name)
            stdscr.attron(curses.color_pair(Theme.TAG))
            stdscr.addstr(cy, x + 4 + len(name), f" ({count})")
            stdscr.attroff(curses.color_pair(Theme.TAG))
            cy += 1


class SnippetListView:
    """知识片段列表视图 / Snippet list view"""

    def __init__(self, storage: Storage) -> None:
        self.storage = storage
        self.snippets: List[KnowledgeSnippet] = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.search_query = ""

    def refresh_data(self) -> None:
        """刷新数据 / Refresh data"""
        if self.search_query:
            engine = SearchEngine()
            engine.add_snippets(self.storage.get_all_snippets())
            results = engine.search(self.search_query, max_results=50)
            self.snippets = [r.snippet for r in results]
        else:
            self.snippets, _ = self.storage.list_snippets(
                sort_by="updated_at",
                sort_order="desc",
                offset=0,
                limit=50,
            )
        self.selected_index = 0
        self.scroll_offset = 0

    def draw(self, stdscr: Any, x: int, y: int, w: int, h: int) -> None:
        """绘制知识片段列表 / Draw snippet list"""
        # 标题 / Title
        title = "Snippets"
        if self.search_query:
            title += f" (Search: {self.search_query})"

        stdscr.attron(curses.color_pair(Theme.TITLE) | curses.A_BOLD)
        stdscr.addstr(y, x + 2, title)
        stdscr.addstr(y, x + w - 15, f"Total: {len(self.snippets)}")
        stdscr.attroff(curses.color_pair(Theme.TITLE) | curses.A_BOLD)

        # 列表区域 / List area
        list_y = y + 2
        list_h = h - 3

        if not self.snippets:
            stdscr.attron(curses.color_pair(Theme.DIM))
            stdscr.addstr(list_y + 2, x + 4, "(No snippets found)")
            stdscr.attroff(curses.color_pair(Theme.DIM))
            return

        # 调整滚动偏移 / Adjust scroll offset
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + list_h:
            self.scroll_offset = self.selected_index - list_h + 1

        # 绘制列表项 / Draw list items
        for i in range(list_h):
            idx = self.scroll_offset + i
            if idx >= len(self.snippets):
                break

            snippet = self.snippets[idx]
            row_y = list_y + i
            is_selected = (idx == self.selected_index)

            # 清除行 / Clear row
            stdscr.move(row_y, x + 1)
            stdscr.clrtoeol()

            if is_selected:
                stdscr.attron(curses.color_pair(Theme.SELECTED))
                stdscr.addstr(row_y, x + 1, " " * (w - 2))
                stdscr.attroff(curses.color_pair(Theme.SELECTED))

            # 标题 / Title
            title_text = truncate_text(snippet.title, w - 20)
            if is_selected:
                stdscr.attron(curses.A_BOLD)
            stdscr.addstr(row_y, x + 3, title_text)
            if is_selected:
                stdscr.attroff(curses.A_BOLD)

            # 标签 / Tags
            if snippet.tags:
                tags_text = ", ".join(snippet.tags[:2])
                if len(snippet.tags) > 2:
                    tags_text += f" +{len(snippet.tags) - 2}"
                stdscr.attron(curses.color_pair(Theme.TAG))
                stdscr.addstr(row_y, x + w - len(tags_text) - 10, tags_text)
                stdscr.attroff(curses.color_pair(Theme.TAG))

            # 时间 / Time
            time_text = format_datetime(snippet.updated_at)
            stdscr.attron(curses.color_pair(Theme.DIM))
            stdscr.addstr(row_y, x + w - 8, time_text[:8])
            stdscr.attroff(curses.color_pair(Theme.DIM))

    def move_up(self) -> None:
        """向上移动选择 / Move selection up"""
        if self.selected_index > 0:
            self.selected_index -= 1

    def move_down(self) -> None:
        """向下移动选择 / Move selection down"""
        if self.selected_index < len(self.snippets) - 1:
            self.selected_index += 1

    def get_selected(self) -> Optional[KnowledgeSnippet]:
        """获取当前选中的知识片段 / Get currently selected snippet"""
        if 0 <= self.selected_index < len(self.snippets):
            return self.snippets[self.selected_index]
        return None


class SnippetDetailView:
    """知识片段详情视图 / Snippet detail view"""

    def __init__(self) -> None:
        self.snippet: Optional[KnowledgeSnippet] = None
        self.content_scroll = 0

    def set_snippet(self, snippet: KnowledgeSnippet) -> None:
        """设置要显示的知识片段 / Set snippet to display"""
        self.snippet = snippet
        self.content_scroll = 0

    def draw(self, stdscr: Any, x: int, y: int, w: int, h: int) -> None:
        """绘制知识片段详情 / Draw snippet detail"""
        if not self.snippet:
            stdscr.attron(curses.color_pair(Theme.DIM))
            stdscr.addstr(y + 2, x + 4, "(Select a snippet to view details)")
            stdscr.attroff(curses.color_pair(Theme.DIM))
            return

        snippet = self.snippet

        # 标题 / Title
        stdscr.attron(curses.color_pair(Theme.TITLE) | curses.A_BOLD)
        title = truncate_text(snippet.title, w - 6)
        stdscr.addstr(y + 1, x + 2, title)
        stdscr.attroff(curses.color_pair(Theme.TITLE) | curses.A_BOLD)

        # 元数据 / Metadata
        cy = y + 3
        meta_items = [
            f"ID: {snippet.id[:12]}...",
            f"Created: {snippet.created_at[:19]}",
            f"Updated: {snippet.updated_at[:19]}",
        ]
        if snippet.source:
            meta_items.append(f"Source: {snippet.source}")
        if snippet.tags:
            meta_items.append(f"Tags: {', '.join(snippet.tags)}")

        for item in meta_items:
            if cy >= y + h - 1:
                break
            stdscr.attron(curses.color_pair(Theme.DIM))
            stdscr.addstr(cy, x + 2, item)
            stdscr.attroff(curses.color_pair(Theme.DIM))
            cy += 1

        # 分隔线 / Separator
        cy += 1
        if cy < y + h - 1:
            stdscr.attron(curses.color_pair(Theme.BORDER))
            stdscr.addstr(cy, x + 2, "-" * (w - 4))
            stdscr.attroff(curses.color_pair(Theme.BORDER))
        cy += 1

        # 内容 / Content
        content_lines = snippet.content.split("\n")
        visible_lines = h - cy + y - 2

        for i in range(visible_lines):
            line_idx = self.content_scroll + i
            if line_idx >= len(content_lines):
                break
            if cy + i >= y + h - 1:
                break

            line = content_lines[line_idx]
            if len(line) > w - 4:
                line = line[:w - 5]
            stdscr.addstr(cy + i, x + 2, line)

    def scroll_up(self) -> None:
        """向上滚动内容 / Scroll content up"""
        if self.content_scroll > 0:
            self.content_scroll -= 1

    def scroll_down(self) -> None:
        """向下滚动内容 / Scroll content down"""
        if self.snippet:
            max_scroll = max(0, len(self.snippet.content.split("\n")) - 10)
            if self.content_scroll < max_scroll:
                self.content_scroll += 1


class WorkflowListView:
    """工作流列表视图 / Workflow list view"""

    def __init__(self, storage: Storage) -> None:
        self.storage = storage
        self.workflows: List[Workflow] = []
        self.selected_index = 0

    def refresh_data(self) -> None:
        """刷新数据 / Refresh data"""
        self.workflows = self.storage.list_workflows()
        self.selected_index = 0

    def draw(self, stdscr: Any, x: int, y: int, w: int, h: int) -> None:
        """绘制工作流列表 / Draw workflow list"""
        stdscr.attron(curses.color_pair(Theme.TITLE) | curses.A_BOLD)
        stdscr.addstr(y, x + 2, "Workflows")
        stdscr.attroff(curses.color_pair(Theme.TITLE) | curses.A_BOLD)

        if not self.workflows:
            stdscr.attron(curses.color_pair(Theme.DIM))
            stdscr.addstr(y + 2, x + 4, "(No workflows)")
            stdscr.attroff(curses.color_pair(Theme.DIM))
            return

        for i, wf in enumerate(self.workflows):
            if y + 2 + i >= y + h - 1:
                break

            is_selected = (i == self.selected_index)
            row_y = y + 2 + i

            if is_selected:
                stdscr.attron(curses.color_pair(Theme.SELECTED))
                stdscr.addstr(row_y, x + 1, " " * (w - 2))
                stdscr.attroff(curses.color_pair(Theme.SELECTED))

            name = truncate_text(wf.name, w - 20)
            if is_selected:
                stdscr.attron(curses.A_BOLD)
            stdscr.addstr(row_y, x + 3, name)
            if is_selected:
                stdscr.attroff(curses.A_BOLD)

            info = f"{len(wf.nodes)} nodes"
            stdscr.attron(curses.color_pair(Theme.DIM))
            stdscr.addstr(row_y, x + w - len(info) - 4, info)
            stdscr.attroff(curses.color_pair(Theme.DIM))

    def move_up(self) -> None:
        if self.selected_index > 0:
            self.selected_index -= 1

    def move_down(self) -> None:
        if self.selected_index < len(self.workflows) - 1:
            self.selected_index += 1

    def get_selected(self) -> Optional[Workflow]:
        if 0 <= self.selected_index < len(self.workflows):
            return self.workflows[self.selected_index]
        return None


# ============================================================
# 主TUI应用 / Main TUI Application
# ============================================================

class MindFlowTUI:
    """
    MindFlow TUI主应用 / MindFlow TUI Main Application

    管理TUI的生命周期、视图切换和用户交互。
    Manages TUI lifecycle, view switching, and user interaction.

    用法 / Usage:
        app = MindFlowTUI(config, storage)
        app.run()
    """

    def __init__(self, config: Config, storage: Storage) -> None:
        """
        初始化TUI应用 / Initialize TUI application

        参数 / Args:
            config: 配置管理器 / Configuration manager
            storage: 存储引擎 / Storage engine
        """
        self.config = config
        self.storage = storage
        self.running = False
        self.current_view = "dashboard"  # dashboard, snippets, workflows
        self.needs_refresh = True

        # 初始化视图 / Initialize views
        self.dashboard = DashboardView(storage)
        self.snippet_list = SnippetListView(storage)
        self.snippet_detail = SnippetDetailView()
        self.workflow_list = WorkflowListView(storage)

        # 初始化组件 / Initialize components
        self.status_bar = StatusBar()
        self.keybinding_bar = KeyBindingBar()

    def run(self) -> None:
        """运行TUI应用 / Run TUI application"""
        self.running = True

        try:
            curses.wrapper(self._main_loop)
        except curses.error as e:
            # 在小终端中可能发生 / May occur in small terminals
            print(f"TUI错误: {e}")
        except KeyboardInterrupt:
            pass

    def _main_loop(self, stdscr: Any) -> None:
        """
        TUI主循环 / TUI main loop

        参数 / Args:
            stdscr: curses标准屏幕 / curses standard screen
        """
        # 初始化curses / Initialize curses
        curses.curs_set(0)  # 隐藏光标 / Hide cursor
        stdscr.nodelay(True)  # 非阻塞输入 / Non-blocking input
        stdscr.timeout(100)  # 输入超时 / Input timeout
        stdscr.keypad(True)  # 启用特殊键 / Enable special keys

        # 初始化颜色 / Initialize colors
        Theme.init_colors()

        # 设置初始状态消息 / Set initial status message
        self.status_bar.set_message(
            "Welcome to MindFlow-CLI | Use arrow keys to navigate",
            "info",
        )

        while self.running:
            # 刷新数据 / Refresh data
            if self.needs_refresh:
                self._refresh_views()
                self.needs_refresh = False

            # 获取屏幕大小 / Get screen size
            max_y, max_x = stdscr.getmaxyx()

            # 清屏 / Clear screen
            stdscr.clear()

            # 绘制标题栏 / Draw title bar
            self._draw_title_bar(stdscr, max_x)

            # 绘制当前视图 / Draw current view
            content_y = 2
            content_h = max_y - 4  # 留出标题栏和底部栏空间

            if self.current_view == "dashboard":
                self.dashboard.draw(stdscr, 0, content_y, max_x, content_h)
            elif self.current_view == "snippets":
                # 左侧列表 / Left panel (list)
                list_w = max_x // 2
                self.snippet_list.draw(
                    stdscr, 0, content_y, list_w, content_h
                )
                # 右侧详情 / Right panel (detail)
                self.snippet_detail.draw(
                    stdscr, list_w, content_y, max_x - list_w, content_h
                )
                # 分隔线 / Separator
                if list_w < max_x:
                    stdscr.attron(curses.color_pair(Theme.BORDER))
                    for row in range(content_y, content_y + content_h):
                        try:
                            stdscr.addch(row, list_w, curses.ACS_VLINE)
                        except curses.error:
                            pass
                    stdscr.attroff(curses.color_pair(Theme.BORDER))
            elif self.current_view == "workflows":
                self.workflow_list.draw(
                    stdscr, 0, content_y, max_x, content_h
                )

            # 绘制状态栏 / Draw status bar
            self.status_bar.set_position(0, max_y - 2, max_x, 1)
            self.status_bar.draw(stdscr)

            # 绘制快捷键栏 / Draw keybinding bar
            self.keybinding_bar.set_bindings(self._get_keybindings())
            self.keybinding_bar.set_position(0, max_y - 1, max_x, 1)
            self.keybinding_bar.draw(stdscr)

            # 刷新屏幕 / Refresh screen
            stdscr.refresh()

            # 处理输入 / Handle input
            self._handle_input(stdscr)

            # 短暂休眠减少CPU占用 / Brief sleep to reduce CPU usage
            time.sleep(0.01)

    def _draw_title_bar(self, stdscr: Any, width: int) -> None:
        """绘制标题栏 / Draw title bar"""
        stdscr.attron(curses.color_pair(Theme.HEADER))
        stdscr.addstr(0, 0, " " * width)
        stdscr.addstr(0, 2, " MindFlow-CLI v1.0.0 ")

        # 当前视图标签 / Current view tab
        view_labels = {
            "dashboard": "[1]Dashboard",
            "snippets": "[2]Snippets",
            "workflows": "[3]Workflows",
        }
        tab_text = view_labels.get(self.current_view, "")
        stdscr.addstr(0, width - len(tab_text) - 2, tab_text)
        stdscr.attroff(curses.color_pair(Theme.HEADER))

    def _get_keybindings(self) -> List[Tuple[str, str]]:
        """获取当前视图的快捷键 / Get keybindings for current view"""
        common = [
            ("1", "Dashboard"),
            ("2", "Snippets"),
            ("3", "Workflows"),
            ("q", "Quit"),
        ]

        if self.current_view == "snippets":
            return [
                ("Up/Down", "Navigate"),
                ("Enter", "View"),
                ("/", "Search"),
                ("n", "New"),
                ("d", "Delete"),
            ] + common
        elif self.current_view == "workflows":
            return [
                ("Up/Down", "Navigate"),
                ("r", "Run"),
            ] + common
        else:
            return common

    def _refresh_views(self) -> None:
        """刷新所有视图数据 / Refresh all view data"""
        try:
            self.dashboard.refresh_data()
            self.snippet_list.refresh_data()
            self.workflow_list.refresh_data()
        except Exception:
            pass

    def _handle_input(self, stdscr: Any) -> None:
        """
        处理用户输入 / Handle user input

        参数 / Args:
            stdscr: curses标准屏幕 / curses standard screen
        """
        try:
            key = stdscr.getch()
        except Exception:
            return

        if key == -1:
            return

        # 全局快捷键 / Global keybindings
        if key == ord("q") or key == ord("Q"):
            self.running = False
            return
        elif key == ord("1"):
            self._switch_view("dashboard")
            return
        elif key == ord("2"):
            self._switch_view("snippets")
            return
        elif key == ord("3"):
            self._switch_view("workflows")
            return

        # 视图特定快捷键 / View-specific keybindings
        if self.current_view == "snippets":
            self._handle_snippet_input(stdscr, key)
        elif self.current_view == "workflows":
            self._handle_workflow_input(stdscr, key)

    def _switch_view(self, view: str) -> None:
        """切换视图 / Switch view"""
        self.current_view = view
        self.needs_refresh = True

        view_names = {
            "dashboard": "Dashboard",
            "snippets": "Snippets",
            "workflows": "Workflows",
        }
        self.status_bar.set_message(
            f"Switched to {view_names.get(view, view)} view",
            "info",
        )

    def _handle_snippet_input(self, stdscr: Any, key: int) -> None:
        """处理知识片段视图输入 / Handle snippet view input"""
        if key == curses.KEY_UP or key == ord("k"):
            self.snippet_list.move_up()
            selected = self.snippet_list.get_selected()
            if selected:
                self.snippet_detail.set_snippet(selected)
        elif key == curses.KEY_DOWN or key == ord("j"):
            self.snippet_list.move_down()
            selected = self.snippet_list.get_selected()
            if selected:
                self.snippet_detail.set_snippet(selected)
        elif key == curses.KEY_PPAGE:
            self.snippet_detail.scroll_up()
        elif key == curses.KEY_NPAGE:
            self.snippet_detail.scroll_down()
        elif key == ord("/"):
            self._show_search_prompt(stdscr)
        elif key == ord("n") or key == ord("N"):
            self.status_bar.set_message(
                "Use 'mindflow add' command to create new snippets",
                "info",
            )
        elif key == ord("d") or key == ord("D"):
            selected = self.snippet_list.get_selected()
            if selected:
                try:
                    self.storage.delete_snippet(selected.id)
                    self.status_bar.set_message(
                        f"Deleted: {selected.title}", "success"
                    )
                    self.needs_refresh = True
                except Exception as e:
                    self.status_bar.set_message(
                        f"Delete failed: {e}", "error"
                    )

    def _handle_workflow_input(self, stdscr: Any, key: int) -> None:
        """处理工作流视图输入 / Handle workflow view input"""
        if key == curses.KEY_UP or key == ord("k"):
            self.workflow_list.move_up()
        elif key == curses.KEY_DOWN or key == ord("j"):
            self.workflow_list.move_down()
        elif key == ord("r") or key == ord("R"):
            wf = self.workflow_list.get_selected()
            if wf:
                self.status_bar.set_message(
                    f"Running workflow: {wf.name}...", "info"
                )
                try:
                    from .workflow_engine import WorkflowEngine
                    engine = WorkflowEngine()
                    log = engine.execute(wf)
                    status = log.status.value
                    self.status_bar.set_message(
                        f"Workflow '{wf.name}': {status}",
                        "success" if status == "success" else "warning",
                    )
                    self.storage.save_workflow_log(log.to_dict())
                except Exception as e:
                    self.status_bar.set_message(
                        f"Workflow failed: {e}", "error"
                    )

    def _show_search_prompt(self, stdscr: Any) -> None:
        """显示搜索提示 / Show search prompt"""
        max_y, max_x = stdscr.getmaxyx()

        # 显示搜索提示 / Show search prompt
        curses.curs_set(1)  # 显示光标 / Show cursor
        stdscr.attron(curses.color_pair(Theme.TITLE))
        stdscr.addstr(max_y - 2, 1, "Search: ")
        stdscr.attroff(curses.color_pair(Theme.TITLE))

        # 读取搜索输入 / Read search input
        search_text = ""
        input_x = max_y - 2
        input_start = 9

        while True:
            stdscr.move(input_x, input_start + len(search_text))
            stdscr.refresh()

            try:
                ch = stdscr.getch()
            except Exception:
                break

            if ch == -1:
                continue
            elif ch == curses.KEY_ENTER or ch == 10:
                break
            elif ch == 27:  # ESC
                search_text = ""
                break
            elif ch == curses.KEY_BACKSPACE or ch == 127:
                if search_text:
                    search_text = search_text[:-1]
                    stdscr.move(input_x, input_start + len(search_text))
                    stdscr.clrtoeol()
            elif 32 <= ch <= 126:
                search_text += chr(ch)
                stdscr.addch(input_x, input_start + len(search_text) - 1, ch)

        curses.curs_set(0)  # 隐藏光标 / Hide cursor

        if search_text:
            self.snippet_list.search_query = search_text
            self.snippet_list.refresh_data()
            self.status_bar.set_message(
                f"Search results for: {search_text}", "info"
            )
        else:
            self.snippet_list.search_query = ""
            self.snippet_list.refresh_data()
            self.status_bar.set_message("Search cleared", "info")
