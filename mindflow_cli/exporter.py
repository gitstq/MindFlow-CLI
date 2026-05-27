"""
多格式导出模块 / Multi-Format Exporter Module

支持将知识库导出为JSON、Markdown和HTML格式。
Supports exporting the knowledge base to JSON, Markdown, and HTML formats.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import KnowledgeSnippet, Workflow


class Exporter:
    """
    多格式导出器 / Multi-Format Exporter

    将知识片段和工作流导出为各种格式。

    用法 / Usage:
        exporter = Exporter()
        exporter.export_json(snippets, "output.json")
        exporter.export_markdown(snippets, "output.md")
        exporter.export_html(snippets, "output.html")
    """

    def __init__(self, include_metadata: bool = True) -> None:
        """
        初始化导出器 / Initialize exporter

        参数 / Args:
            include_metadata: 是否包含导出元数据 / Whether to include export metadata
        """
        self.include_metadata = include_metadata

    def export(
        self,
        snippets: List[KnowledgeSnippet],
        format_type: str,
        output_path: str,
        workflows: Optional[List[Workflow]] = None,
        title: str = "MindFlow 知识库导出",
    ) -> str:
        """
        导出知识库 / Export knowledge base

        参数 / Args:
            snippets: 知识片段列表 / List of knowledge snippets
            format_type: 导出格式 ("json", "markdown", "html")
            output_path: 输出文件路径 / Output file path
            workflows: 工作流列表（可选） / List of workflows (optional)
            title: 导出标题 / Export title

        返回 / Returns:
            输出文件路径 / Output file path
        """
        format_type = format_type.lower()

        if format_type in ("json", "j"):
            return self.export_json(snippets, output_path, workflows, title)
        elif format_type in ("markdown", "md"):
            return self.export_markdown(snippets, output_path, workflows, title)
        elif format_type in ("html", "htm"):
            return self.export_html(snippets, output_path, workflows, title)
        else:
            raise ValueError(f"不支持的导出格式: {format_type}，支持: json, markdown, html")

    # ============================================================
    # JSON导出 / JSON Export
    # ============================================================

    def export_json(
        self,
        snippets: List[KnowledgeSnippet],
        output_path: str,
        workflows: Optional[List[Workflow]] = None,
        title: str = "MindFlow 知识库导出",
    ) -> str:
        """
        导出为JSON格式 / Export to JSON format

        参数 / Args:
            snippets: 知识片段列表 / List of knowledge snippets
            output_path: 输出文件路径 / Output file path
            workflows: 工作流列表（可选） / List of workflows (optional)
            title: 导出标题 / Export title

        返回 / Returns:
            输出文件路径 / Output file path
        """
        export_data: Dict[str, Any] = {}

        if self.include_metadata:
            export_data["metadata"] = {
                "title": title,
                "exported_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "statistics": {
                    "total_snippets": len(snippets),
                    "total_workflows": len(workflows) if workflows else 0,
                    "total_tags": len(self._collect_all_tags(snippets)),
                },
            }

        export_data["snippets"] = [s.to_dict() for s in snippets]

        if workflows:
            export_data["workflows"] = [w.to_dict() for w in workflows]

        # 确保输出目录存在 / Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        return output_path

    # ============================================================
    # Markdown导出 / Markdown Export
    # ============================================================

    def export_markdown(
        self,
        snippets: List[KnowledgeSnippet],
        output_path: str,
        workflows: Optional[List[Workflow]] = None,
        title: str = "MindFlow 知识库导出",
    ) -> str:
        """
        导出为Markdown格式 / Export to Markdown format

        参数 / Args:
            snippets: 知识片段列表 / List of knowledge snippets
            output_path: 输出文件路径 / Output file path
            workflows: 工作流列表（可选） / List of workflows (optional)
            title: 导出标题 / Export title

        返回 / Returns:
            输出文件路径 / Output file path
        """
        lines: List[str] = []

        # 标题 / Title
        lines.append(f"# {title}")
        lines.append("")

        if self.include_metadata:
            lines.append(f"> 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"> 知识片段数: {len(snippets)}")
            if workflows:
                lines.append(f"> 工作流数: {len(workflows)}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # 目录 / Table of contents
        lines.append("## 目录")
        lines.append("")
        for i, snippet in enumerate(snippets, 1):
            lines.append(f"{i}. [{snippet.title}](#{self._md_anchor(snippet.title)})")
        lines.append("")

        # 知识片段 / Knowledge snippets
        lines.append("## 知识片段")
        lines.append("")

        for i, snippet in enumerate(snippets, 1):
            lines.append(f"### {i}. {snippet.title}")
            lines.append("")

            # 元数据 / Metadata
            meta_items = []
            if snippet.tags:
                meta_items.append(f"**标签**: {', '.join(f'`{tag}`' for tag in snippet.tags)}")
            if snippet.source:
                meta_items.append(f"**来源**: {snippet.source}")
            meta_items.append(f"**创建时间**: {snippet.created_at[:10]}")
            meta_items.append(f"**更新时间**: {snippet.updated_at[:10]}")

            for item in meta_items:
                lines.append(item)
            lines.append("")

            # 内容 / Content
            lines.append(snippet.content)
            lines.append("")
            lines.append("---")
            lines.append("")

        # 工作流 / Workflows
        if workflows:
            lines.append("## 工作流")
            lines.append("")

            for workflow in workflows:
                lines.append(f"### {workflow.name}")
                lines.append("")
                if workflow.description:
                    lines.append(f"> {workflow.description}")
                    lines.append("")

                lines.append(f"- **节点数**: {len(workflow.nodes)}")
                lines.append(f"- **边数**: {len(workflow.edges)}")
                lines.append(f"- **创建时间**: {workflow.created_at[:10]}")
                lines.append("")

                if workflow.nodes:
                    lines.append("#### 节点列表")
                    lines.append("")
                    for node in workflow.nodes:
                        lines.append(f"- **{node.name}** (`{node.type.value}`)")
                    lines.append("")

                lines.append("---")
                lines.append("")

        # 页脚 / Footer
        lines.append("")
        lines.append("*由 MindFlow-CLI v1.0.0 导出*")

        # 写入文件 / Write to file
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        content = "\n".join(lines)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path

    # ============================================================
    # HTML导出 / HTML Export
    # ============================================================

    def export_html(
        self,
        snippets: List[KnowledgeSnippet],
        output_path: str,
        workflows: Optional[List[Workflow]] = None,
        title: str = "MindFlow 知识库导出",
    ) -> str:
        """
        导出为HTML格式 / Export to HTML format

        参数 / Args:
            snippets: 知识片段列表 / List of knowledge snippets
            output_path: 输出文件路径 / Output file path
            workflows: 工作流列表（可选） / List of workflows (optional)
            title: 导出标题 / Export title

        返回 / Returns:
            输出文件路径 / Output file path
        """
        all_tags = self._collect_all_tags(snippets)

        html_parts: List[str] = []

        # HTML头部 / HTML head
        html_parts.append(self._get_html_head(title))

        # 导航栏 / Navigation bar
        html_parts.append(self._get_navbar(title, len(snippets), len(all_tags)))

        # 主内容区 / Main content area
        html_parts.append('<main class="container">')

        # 统计卡片 / Statistics cards
        html_parts.append(self._get_stats_cards(snippets, workflows, all_tags))

        # 标签云 / Tag cloud
        if all_tags:
            html_parts.append(self._get_tag_cloud(all_tags))

        # 知识片段列表 / Knowledge snippets list
        html_parts.append('<section class="snippets-section">')
        html_parts.append('<h2 class="section-title">知识片段</h2>')
        html_parts.append('<div class="snippets-grid">')

        for snippet in snippets:
            html_parts.append(self._snippet_to_html_card(snippet))

        html_parts.append('</div>')
        html_parts.append('</section>')

        # 工作流部分 / Workflows section
        if workflows:
            html_parts.append('<section class="workflows-section">')
            html_parts.append('<h2 class="section-title">工作流</h2>')
            html_parts.append('<div class="workflows-list">')

            for workflow in workflows:
                html_parts.append(self._workflow_to_html_card(workflow))

            html_parts.append('</div>')
            html_parts.append('</section>')

        html_parts.append('</main>')

        # 页脚 / Footer
        html_parts.append(self._get_html_footer())

        # 写入文件 / Write to file
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        content = "\n".join(html_parts)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path

    def _get_html_head(self, title: str) -> str:
        """生成HTML头部 / Generate HTML head"""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape_html(title)}</title>
    <style>
        :root {{
            --primary: #2563eb;
            --primary-light: #3b82f6;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
            --text-secondary: #64748b;
            --border: #e2e8f0;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --tag-bg: #eff6ff;
            --tag-text: #1d4ed8;
            --shadow: 0 1px 3px rgba(0,0,0,0.1);
            --shadow-lg: 0 4px 6px rgba(0,0,0,0.1);
            --radius: 8px;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}
        .navbar {{
            background: var(--primary);
            color: white;
            padding: 1rem 2rem;
            box-shadow: var(--shadow);
        }}
        .navbar h1 {{ font-size: 1.5rem; font-weight: 600; }}
        .navbar .stats {{ font-size: 0.875rem; opacity: 0.9; margin-top: 0.25rem; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .stat-card {{
            background: var(--card-bg);
            border-radius: var(--radius);
            padding: 1.5rem;
            box-shadow: var(--shadow);
            text-align: center;
        }}
        .stat-card .number {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary);
        }}
        .stat-card .label {{
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }}
        .tag-cloud {{
            background: var(--card-bg);
            border-radius: var(--radius);
            padding: 1.5rem;
            box-shadow: var(--shadow);
            margin-bottom: 2rem;
        }}
        .tag-cloud h3 {{ margin-bottom: 1rem; font-size: 1rem; }}
        .tag-cloud .tags {{ display: flex; flex-wrap: wrap; gap: 0.5rem; }}
        .tag {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: var(--tag-bg);
            color: var(--tag-text);
            border-radius: 9999px;
            font-size: 0.8rem;
            text-decoration: none;
        }}
        .section-title {{
            font-size: 1.25rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--primary);
        }}
        .snippets-grid {{
            display: grid;
            gap: 1rem;
        }}
        .snippet-card {{
            background: var(--card-bg);
            border-radius: var(--radius);
            padding: 1.5rem;
            box-shadow: var(--shadow);
            transition: box-shadow 0.2s;
        }}
        .snippet-card:hover {{ box-shadow: var(--shadow-lg); }}
        .snippet-card h3 {{
            font-size: 1.125rem;
            margin-bottom: 0.5rem;
            color: var(--primary);
        }}
        .snippet-card .meta {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 0.75rem;
        }}
        .snippet-card .content {{
            font-size: 0.95rem;
            color: var(--text);
            white-space: pre-wrap;
            word-break: break-word;
            max-height: 200px;
            overflow: hidden;
            position: relative;
        }}
        .snippet-card .content::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 40px;
            background: linear-gradient(transparent, white);
        }}
        .snippet-card .tags {{ margin-top: 0.75rem; }}
        .workflow-card {{
            background: var(--card-bg);
            border-radius: var(--radius);
            padding: 1.5rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }}
        .workflow-card h3 {{
            font-size: 1.125rem;
            margin-bottom: 0.5rem;
        }}
        .workflow-card .description {{
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-bottom: 0.75rem;
        }}
        .workflow-card .info {{
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}
        .footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
            font-size: 0.8rem;
            margin-top: 2rem;
        }}
        @media (max-width: 768px) {{
            .container {{ padding: 1rem; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>"""

    def _get_navbar(
        self, title: str, snippet_count: int, tag_count: int
    ) -> str:
        """生成导航栏 / Generate navbar"""
        return f"""    <nav class="navbar">
        <h1>{self._escape_html(title)}</h1>
        <div class="stats">{snippet_count} 个知识片段 | {tag_count} 个标签</div>
    </nav>"""

    def _get_stats_cards(
        self,
        snippets: List[KnowledgeSnippet],
        workflows: Optional[List[Workflow]],
        tags: Dict[str, int],
    ) -> str:
        """生成统计卡片 / Generate statistics cards"""
        total_words = sum(len(s.content) for s in snippets)
        workflow_count = len(workflows) if workflows else 0

        return f"""    <div class="stats-grid">
        <div class="stat-card">
            <div class="number">{len(snippets)}</div>
            <div class="label">知识片段</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(tags)}</div>
            <div class="label">标签</div>
        </div>
        <div class="stat-card">
            <div class="number">{total_words:,}</div>
            <div class="label">总字数</div>
        </div>
        <div class="stat-card">
            <div class="number">{workflow_count}</div>
            <div class="label">工作流</div>
        </div>
    </div>"""

    def _get_tag_cloud(self, tags: Dict[str, int]) -> str:
        """生成标签云 / Generate tag cloud"""
        tag_links = " ".join(
            f'<span class="tag">{self._escape_html(name)} ({count})</span>'
            for name, count in sorted(tags.items(), key=lambda x: -x[1])
        )
        return f"""    <div class="tag-cloud">
        <h3>标签云</h3>
        <div class="tags">{tag_links}</div>
    </div>"""

    def _snippet_to_html_card(self, snippet: KnowledgeSnippet) -> str:
        """将知识片段转换为HTML卡片 / Convert snippet to HTML card"""
        tags_html = " ".join(
            f'<span class="tag">{self._escape_html(tag)}</span>'
            for tag in snippet.tags
        )

        return f"""        <div class="snippet-card">
            <h3>{self._escape_html(snippet.title)}</h3>
            <div class="meta">
                创建于 {snippet.created_at[:10]} | 更新于 {snippet.updated_at[:10]}
                {f' | 来源: {self._escape_html(snippet.source)}' if snippet.source else ''}
            </div>
            <div class="content">{self._escape_html(snippet.content)}</div>
            {f'<div class="tags">{tags_html}</div>' if tags_html else ''}
        </div>"""

    def _workflow_to_html_card(self, workflow: Workflow) -> str:
        """将工作流转换为HTML卡片 / Convert workflow to HTML card"""
        return f"""        <div class="workflow-card">
            <h3>{self._escape_html(workflow.name)}</h3>
            <div class="description">{self._escape_html(workflow.description)}</div>
            <div class="info">
                {len(workflow.nodes)} 个节点 | {len(workflow.edges)} 条连接 |
                创建于 {workflow.created_at[:10]}
            </div>
        </div>"""

    def _get_html_footer(self) -> str:
        """生成HTML页脚 / Generate HTML footer"""
        return f"""    <footer class="footer">
        <p>由 MindFlow-CLI v1.0.0 导出 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </footer>
</body>
</html>"""

    # ============================================================
    # 辅助方法 / Helper Methods
    # ============================================================

    def _collect_all_tags(
        self, snippets: List[KnowledgeSnippet]
    ) -> Dict[str, int]:
        """
        收集所有标签及其计数 / Collect all tags with counts

        参数 / Args:
            snippets: 知识片段列表 / List of knowledge snippets

        返回 / Returns:
            标签-计数字典 / Tag-count dictionary
        """
        tags: Dict[str, int] = {}
        for snippet in snippets:
            for tag in snippet.tags:
                tags[tag] = tags.get(tag, 0) + 1
        return dict(sorted(tags.items(), key=lambda x: -x[1]))

    def _escape_html(self, text: str) -> str:
        """
        HTML特殊字符转义 / HTML special character escaping

        参数 / Args:
            text: 原始文本 / Original text

        返回 / Returns:
            转义后的文本 / Escaped text
        """
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&#39;")
        return text

    def _md_anchor(self, text: str) -> str:
        """
        生成Markdown锚点 / Generate Markdown anchor

        参数 / Args:
            text: 标题文本 / Title text

        返回 / Returns:
            锚点ID / Anchor ID
        """
        import re
        anchor = text.lower().strip()
        anchor = re.sub(r'[^\w\s-]', '', anchor)
        anchor = re.sub(r'[\s_]+', '-', anchor)
        anchor = re.sub(r'-+', '-', anchor)
        return anchor.strip('-')

    def export_to_string(
        self,
        snippets: List[KnowledgeSnippet],
        format_type: str,
        title: str = "MindFlow 知识库导出",
    ) -> str:
        """
        导出为字符串（不写入文件） / Export to string (no file writing)

        参数 / Args:
            snippets: 知识片段列表 / List of knowledge snippets
            format_type: 导出格式 / Export format
            title: 标题 / Title

        返回 / Returns:
            格式化字符串 / Formatted string
        """
        if format_type == "json":
            data = [s.to_dict() for s in snippets]
            return json.dumps(data, ensure_ascii=False, indent=2)
        elif format_type == "markdown":
            lines = [f"# {title}", ""]
            for i, s in enumerate(snippets, 1):
                lines.append(f"## {i}. {s.title}")
                lines.append("")
                if s.tags:
                    lines.append(f"**标签**: {', '.join(s.tags)}")
                    lines.append("")
                lines.append(s.content)
                lines.append("")
                lines.append("---")
                lines.append("")
            return "\n".join(lines)
        else:
            raise ValueError(f"不支持的格式: {format_type}")
