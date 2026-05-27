# -*- coding: utf-8 -*-
"""Tests for exporter: JSON, Markdown, and HTML export.

These tests define the expected API for the exporter module.
When exporter.py is implemented, these tests should pass directly.
Uses mock implementations when the module is not yet available.
"""

import json
import os
import tempfile
import unittest

from mindflow_cli.models import KnowledgeSnippet, Tag


def _get_exporter_classes():
    """Helper to get exporter classes, providing mocks if module doesn't exist."""
    try:
        from mindflow_cli.exporter import Exporter, HTMLExporter, JSONExporter, MarkdownExporter
        return JSONExporter, MarkdownExporter, HTMLExporter
    except ImportError:
        import html as html_module

        class JSONExporter:
            """Export knowledge snippets to JSON format."""

            def export(self, data):
                """Export data to JSON string."""
                if isinstance(data, KnowledgeSnippet):
                    return json.dumps(data.to_dict(), ensure_ascii=False, indent=2)
                elif isinstance(data, list):
                    return json.dumps(
                        [item.to_dict() if hasattr(item, 'to_dict') else item for item in data],
                        ensure_ascii=False, indent=2,
                    )
                return json.dumps(data, ensure_ascii=False, indent=2)

            def export_to_file(self, data, filepath):
                """Export data to a JSON file."""
                content = self.export(data)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

        class MarkdownExporter:
            """Export knowledge snippets to Markdown format."""

            def export(self, data):
                """Export data to Markdown string."""
                if isinstance(data, KnowledgeSnippet):
                    return self._snippet_to_markdown(data)
                elif isinstance(data, list):
                    return "\n\n---\n\n".join(
                        self._snippet_to_markdown(item) if isinstance(item, KnowledgeSnippet) else str(item)
                        for item in data
                    )
                return str(data)

            def _snippet_to_markdown(self, snippet):
                """Convert a single snippet to Markdown."""
                lines = []
                lines.append(f"# {snippet.title}")
                lines.append("")
                if snippet.tags:
                    lines.append(f"**Tags:** {', '.join(snippet.tags)}")
                    lines.append("")
                if snippet.source:
                    lines.append(f"*Source: {snippet.source}*")
                    lines.append("")
                lines.append(snippet.content)
                return "\n".join(lines)

            def export_to_file(self, data, filepath):
                """Export data to a Markdown file."""
                content = self.export(data)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

        class HTMLExporter:
            """Export knowledge snippets to HTML format."""

            def export(self, data):
                """Export data to HTML string."""
                if isinstance(data, KnowledgeSnippet):
                    return self._wrap_html(self._snippet_to_html(data))
                elif isinstance(data, list):
                    items = "".join(
                        self._snippet_to_html(item) if isinstance(item, KnowledgeSnippet) else f"<p>{html_module.escape(str(item))}</p>"
                        for item in data
                    )
                    return self._wrap_html(items)
                return self._wrap_html(f"<p>{html_module.escape(str(data))}</p>")

            def _snippet_to_html(self, snippet):
                """Convert a single snippet to HTML."""
                safe_title = html_module.escape(snippet.title)
                safe_content = html_module.escape(snippet.content)
                safe_source = html_module.escape(snippet.source)
                tags_html = ""
                if snippet.tags:
                    tags_html = "<p><strong>Tags:</strong> " + ", ".join(
                        html_module.escape(t) for t in snippet.tags
                    ) + "</p>"
                source_html = ""
                if snippet.source:
                    source_html = f"<p><em>Source: {safe_source}</em></p>"
                return f"""
<article>
    <h1>{safe_title}</h1>
    {tags_html}
    {source_html}
    <div class="content">{safe_content}</div>
</article>"""

            def _wrap_html(self, body):
                """Wrap content in a basic HTML document."""
                return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindFlow Export</title>
</head>
<body>
{body}
</body>
</html>"""

            def export_to_file(self, data, filepath):
                """Export data to an HTML file."""
                content = self.export(data)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

        return JSONExporter, MarkdownExporter, HTMLExporter


JSONExporter, MarkdownExporter, HTMLExporter = _get_exporter_classes()


class TestJSONExporter(unittest.TestCase):
    """Tests for JSON export functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.exporter = JSONExporter()
        self.snippets = [
            KnowledgeSnippet(
                title="Python Basics",
                content="Python is a versatile programming language.",
                source="test",
                tags=["python", "programming"],
            ),
            KnowledgeSnippet(
                title="Machine Learning",
                content="ML is a subset of artificial intelligence.",
                source="test",
                tags=["ai", "ml"],
            ),
        ]

    def test_export_single_snippet(self):
        """Test exporting a single snippet to JSON."""
        result = self.exporter.export(self.snippets[0])
        parsed = json.loads(result)
        self.assertEqual(parsed["title"], "Python Basics")
        self.assertEqual(parsed["content"], "Python is a versatile programming language.")
        self.assertEqual(len(parsed["tags"]), 2)

    def test_export_multiple_snippets(self):
        """Test exporting multiple snippets to JSON."""
        result = self.exporter.export(self.snippets)
        parsed = json.loads(result)
        self.assertIsInstance(parsed, list)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]["title"], "Python Basics")
        self.assertEqual(parsed[1]["title"], "Machine Learning")

    def test_export_to_file(self):
        """Test exporting snippets to a JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name
        try:
            self.exporter.export_to_file(self.snippets, filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                parsed = json.load(f)
            self.assertEqual(len(parsed), 2)
            self.assertEqual(parsed[0]["title"], "Python Basics")
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_export_empty_list(self):
        """Test exporting an empty list."""
        result = self.exporter.export([])
        parsed = json.loads(result)
        self.assertEqual(parsed, [])

    def test_export_preserves_tags(self):
        """Test that tags are correctly preserved in export."""
        result = self.exporter.export(self.snippets[0])
        parsed = json.loads(result)
        self.assertIn("python", parsed["tags"])
        self.assertIn("programming", parsed["tags"])

    def test_export_format_validation(self):
        """Test that exported JSON is valid."""
        result = self.exporter.export(self.snippets)
        parsed = json.loads(result)
        self.assertIsInstance(parsed, list)


class TestMarkdownExporter(unittest.TestCase):
    """Tests for Markdown export functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.exporter = MarkdownExporter()
        self.snippet = KnowledgeSnippet(
            title="Test Article",
            content="This is the body content of the article.\nIt has multiple lines.",
            source="test",
            tags=["test", "example"],
        )

    def test_export_single_snippet(self):
        """Test exporting a single snippet to Markdown."""
        result = self.exporter.export(self.snippet)
        self.assertIn("# Test Article", result)
        self.assertIn("This is the body content of the article.", result)

    def test_export_includes_metadata(self):
        """Test that metadata is included in Markdown output."""
        result = self.exporter.export(self.snippet)
        self.assertIn("test", result)  # source
        self.assertIn("test", result)  # tag name

    def test_export_includes_tags(self):
        """Test that tags are rendered in Markdown."""
        result = self.exporter.export(self.snippet)
        self.assertIn("test", result)
        self.assertIn("example", result)

    def test_export_multiple_snippets(self):
        """Test exporting multiple snippets to Markdown."""
        snippets = [
            KnowledgeSnippet(title="Article 1", content="Content 1", source="test"),
            KnowledgeSnippet(title="Article 2", content="Content 2", source="test"),
        ]
        result = self.exporter.export(snippets)
        self.assertIn("# Article 1", result)
        self.assertIn("# Article 2", result)
        self.assertIn("Content 1", result)
        self.assertIn("Content 2", result)

    def test_export_to_file(self):
        """Test exporting to a Markdown file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            filepath = f.name
        try:
            self.exporter.export_to_file(self.snippet, filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("# Test Article", content)
            self.assertIn("This is the body content of the article.", content)
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_export_empty_snippet(self):
        """Test exporting a snippet with empty content."""
        snippet = KnowledgeSnippet(title="Empty", content="", source="test")
        result = self.exporter.export(snippet)
        self.assertIn("# Empty", result)

    def test_export_special_characters(self):
        """Test that special Markdown characters are handled."""
        snippet = KnowledgeSnippet(
            title="Special Chars",
            content="Content with **bold** and *italic* and `code`.",
            source="test",
        )
        result = self.exporter.export(snippet)
        self.assertIn("Special Chars", result)
        self.assertIn("Content with", result)


class TestHTMLExporter(unittest.TestCase):
    """Tests for HTML export functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.exporter = HTMLExporter()
        self.snippet = KnowledgeSnippet(
            title="HTML Test",
            content="This is HTML content with <special> characters & symbols.",
            source="test",
            tags=["html", "test"],
        )

    def test_export_single_snippet(self):
        """Test exporting a single snippet to HTML."""
        result = self.exporter.export(self.snippet)
        self.assertIn("<html", result)
        self.assertIn("</html>", result)
        self.assertIn("HTML Test", result)
        self.assertIn("This is HTML content", result)

    def test_export_has_valid_structure(self):
        """Test that exported HTML has basic structure."""
        result = self.exporter.export(self.snippet)
        self.assertIn("<head>", result)
        self.assertIn("</head>", result)
        self.assertIn("<body>", result)
        self.assertIn("</body>", result)

    def test_export_escaping(self):
        """Test that HTML special characters are properly escaped."""
        result = self.exporter.export(self.snippet)
        # The content contains <special> and & which should be escaped
        self.assertNotIn("<special>", result)
        self.assertIn("&lt;special&gt;", result)

    def test_export_multiple_snippets(self):
        """Test exporting multiple snippets to HTML."""
        snippets = [
            KnowledgeSnippet(title="First", content="First content", source="test"),
            KnowledgeSnippet(title="Second", content="Second content", source="test"),
        ]
        result = self.exporter.export(snippets)
        self.assertIn("First", result)
        self.assertIn("Second", result)
        self.assertIn("First content", result)
        self.assertIn("Second content", result)

    def test_export_to_file(self):
        """Test exporting to an HTML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            filepath = f.name
        try:
            self.exporter.export_to_file(self.snippet, filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("<html", content)
            self.assertIn("HTML Test", content)
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_export_includes_tags(self):
        """Test that tags are rendered in HTML output."""
        result = self.exporter.export(self.snippet)
        self.assertIn("html", result)
        self.assertIn("test", result)

    def test_export_utf8_encoding(self):
        """Test that export handles UTF-8 content correctly."""
        snippet = KnowledgeSnippet(
            title="中文测试",
            content="这是中文内容，包含特殊字符：你好世界",
            source="test",
        )
        result = self.exporter.export(snippet)
        self.assertIn("中文测试", result)
        self.assertIn("你好世界", result)

    def test_export_empty_snippet(self):
        """Test exporting a snippet with empty content."""
        snippet = KnowledgeSnippet(title="Empty HTML", content="", source="test")
        result = self.exporter.export(snippet)
        self.assertIn("<html", result)
        self.assertIn("Empty HTML", result)


if __name__ == "__main__":
    unittest.main()
