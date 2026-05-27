# -*- coding: utf-8 -*-
"""Tests for data models: KnowledgeSnippet, Workflow, WorkflowNode, Tag, WorkflowEdge."""

import json
import unittest
from datetime import datetime

from mindflow_cli.models import (
    KnowledgeSnippet,
    NodeStatus,
    NodeType,
    Tag,
    Workflow,
    WorkflowEdge,
    WorkflowNode,
    WorkflowStatus,
)


class TestNodeType(unittest.TestCase):
    """Tests for the NodeType enum."""

    def test_node_type_values(self):
        """Test that NodeType has expected values."""
        self.assertEqual(NodeType.LLM.value, "llm")
        self.assertEqual(NodeType.TRANSFORM.value, "transform")
        self.assertEqual(NodeType.FILTER.value, "filter")
        self.assertEqual(NodeType.EXPORT.value, "export")
        self.assertEqual(NodeType.INPUT.value, "input")
        self.assertEqual(NodeType.MERGE.value, "merge")

    def test_node_type_from_string(self):
        """Test creating NodeType from string value."""
        nt = NodeType("input")
        self.assertEqual(nt, NodeType.INPUT)


class TestNodeStatus(unittest.TestCase):
    """Tests for the NodeStatus enum."""

    def test_node_status_values(self):
        """Test that NodeStatus has expected values."""
        self.assertEqual(NodeStatus.PENDING.value, "pending")
        self.assertEqual(NodeStatus.RUNNING.value, "running")
        self.assertEqual(NodeStatus.SUCCESS.value, "success")
        self.assertEqual(NodeStatus.FAILED.value, "failed")
        self.assertEqual(NodeStatus.SKIPPED.value, "skipped")


class TestWorkflowStatus(unittest.TestCase):
    """Tests for the WorkflowStatus enum."""

    def test_workflow_status_values(self):
        """Test that WorkflowStatus has expected values."""
        self.assertEqual(WorkflowStatus.PENDING.value, "pending")
        self.assertEqual(WorkflowStatus.RUNNING.value, "running")
        self.assertEqual(WorkflowStatus.SUCCESS.value, "success")
        self.assertEqual(WorkflowStatus.FAILED.value, "failed")
        self.assertEqual(WorkflowStatus.PARTIAL.value, "partial")


class TestTag(unittest.TestCase):
    """Tests for the Tag model."""

    def test_tag_creation(self):
        """Test basic Tag creation."""
        tag = Tag(name="python", color="#3572A5")
        self.assertEqual(tag.name, "python")
        self.assertEqual(tag.color, "#3572A5")

    def test_tag_default_color(self):
        """Test Tag with default color."""
        tag = Tag(name="ai")
        self.assertEqual(tag.name, "ai")
        self.assertEqual(tag.color, "#3498db")  # default color

    def test_tag_default_count(self):
        """Test Tag default count is 0."""
        tag = Tag(name="test")
        self.assertEqual(tag.count, 0)

    def test_tag_auto_id(self):
        """Test Tag gets an auto-generated ID."""
        tag = Tag(name="test")
        self.assertIsNotNone(tag.id)
        self.assertTrue(len(tag.id) > 0)

    def test_tag_serialization(self):
        """Test Tag to_dict serialization."""
        tag = Tag(name="nlp", color="#FF6B6B", count=5)
        data = tag.to_dict()
        self.assertEqual(data["name"], "nlp")
        self.assertEqual(data["color"], "#FF6B6B")
        self.assertEqual(data["count"], 5)
        self.assertIn("id", data)

    def test_tag_to_json(self):
        """Test Tag JSON serialization."""
        tag = Tag(name="test", color="#000000")
        json_str = tag.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["name"], "test")
        self.assertEqual(parsed["color"], "#000000")

    def test_tag_from_dict(self):
        """Test Tag deserialization from dict."""
        data = {"id": "tag-001", "name": "demo", "color": "#ABCDEF", "count": 3}
        tag = Tag.from_dict(data)
        self.assertEqual(tag.id, "tag-001")
        self.assertEqual(tag.name, "demo")
        self.assertEqual(tag.color, "#ABCDEF")
        self.assertEqual(tag.count, 3)


class TestKnowledgeSnippet(unittest.TestCase):
    """Tests for the KnowledgeSnippet model."""

    def setUp(self):
        """Set up test fixtures."""
        self.snippet = KnowledgeSnippet(
            title="Test Snippet",
            content="This is test content for knowledge snippet.",
            source="unit_test",
            tags=["test", "example"],
        )

    def test_snippet_creation(self):
        """Test basic KnowledgeSnippet creation."""
        self.assertEqual(self.snippet.title, "Test Snippet")
        self.assertEqual(self.snippet.content, "This is test content for knowledge snippet.")
        self.assertEqual(self.snippet.source, "unit_test")
        self.assertEqual(len(self.snippet.tags), 2)
        self.assertEqual(self.snippet.tags, ["test", "example"])

    def test_snippet_auto_id(self):
        """Test that snippet gets an auto-generated ID."""
        self.assertIsNotNone(self.snippet.id)
        self.assertTrue(len(self.snippet.id) > 0)

    def test_snippet_auto_timestamp(self):
        """Test that snippet gets auto-generated timestamps."""
        self.assertIsNotNone(self.snippet.created_at)
        self.assertIsNotNone(self.snippet.updated_at)

    def test_snippet_serialization(self):
        """Test KnowledgeSnippet to_dict serialization."""
        data = self.snippet.to_dict()
        self.assertEqual(data["title"], "Test Snippet")
        self.assertEqual(data["content"], "This is test content for knowledge snippet.")
        self.assertEqual(data["source"], "unit_test")
        self.assertEqual(len(data["tags"]), 2)
        self.assertIn("id", data)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_snippet_to_json(self):
        """Test KnowledgeSnippet JSON serialization."""
        json_str = self.snippet.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["title"], "Test Snippet")
        self.assertEqual(len(parsed["tags"]), 2)

    def test_snippet_from_dict(self):
        """Test KnowledgeSnippet deserialization from dict."""
        data = {
            "id": "test-id-001",
            "title": "Deserialized Snippet",
            "content": "Content from dict.",
            "source": "test",
            "tags": ["demo"],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        snippet = KnowledgeSnippet.from_dict(data)
        self.assertEqual(snippet.id, "test-id-001")
        self.assertEqual(snippet.title, "Deserialized Snippet")
        self.assertEqual(snippet.content, "Content from dict.")
        self.assertEqual(len(snippet.tags), 1)
        self.assertEqual(snippet.tags[0], "demo")

    def test_snippet_from_json(self):
        """Test KnowledgeSnippet deserialization from JSON string."""
        json_str = '{"id":"j-001","title":"JSON Test","content":"From JSON","tags":[],"source":"","created_at":"2024-01-01T00:00:00","updated_at":"2024-01-01T00:00:00"}'
        snippet = KnowledgeSnippet.from_json(json_str)
        self.assertEqual(snippet.id, "j-001")
        self.assertEqual(snippet.title, "JSON Test")

    def test_snippet_update_timestamp(self):
        """Test update_timestamp method."""
        old_updated = self.snippet.updated_at
        self.snippet.update_timestamp()
        self.assertNotEqual(self.snippet.updated_at, old_updated)

    def test_snippet_summary_short(self):
        """Test summary method with short content."""
        snippet = KnowledgeSnippet(content="Short")
        self.assertEqual(snippet.summary(max_length=100), "Short")

    def test_snippet_summary_truncated(self):
        """Test summary method with long content."""
        long_content = "A" * 200
        snippet = KnowledgeSnippet(content=long_content)
        summary = snippet.summary(max_length=100)
        self.assertEqual(len(summary), 103)  # 100 + "..."
        self.assertTrue(summary.endswith("..."))

    def test_snippet_default_values(self):
        """Test KnowledgeSnippet with default values."""
        snippet = KnowledgeSnippet()
        self.assertEqual(snippet.title, "")
        self.assertEqual(snippet.content, "")
        self.assertEqual(snippet.source, "")
        self.assertEqual(snippet.tags, [])


class TestWorkflowNode(unittest.TestCase):
    """Tests for the WorkflowNode model."""

    def test_node_creation(self):
        """Test basic WorkflowNode creation."""
        node = WorkflowNode(
            id="node-1",
            name="Input Node",
            type=NodeType.INPUT,
            config={"key": "value"},
        )
        self.assertEqual(node.id, "node-1")
        self.assertEqual(node.name, "Input Node")
        self.assertEqual(node.type, NodeType.INPUT)
        self.assertEqual(node.config, {"key": "value"})

    def test_node_auto_id(self):
        """Test that node gets an auto-generated ID if not provided."""
        node = WorkflowNode(name="Auto ID Node")
        self.assertIsNotNone(node.id)
        self.assertTrue(len(node.id) > 0)

    def test_node_default_type(self):
        """Test that default node type is TRANSFORM."""
        node = WorkflowNode(name="Default Type")
        self.assertEqual(node.type, NodeType.TRANSFORM)

    def test_node_default_status(self):
        """Test that default node status is PENDING."""
        node = WorkflowNode(name="Default Status")
        self.assertEqual(node.status, NodeStatus.PENDING)

    def test_node_default_position(self):
        """Test that default position is (0, 0)."""
        node = WorkflowNode(name="Position Test")
        self.assertEqual(node.position, {"x": 0, "y": 0})

    def test_node_serialization(self):
        """Test WorkflowNode to_dict serialization."""
        node = WorkflowNode(
            id="node-3",
            name="Output Node",
            type=NodeType.EXPORT,
            config={"format": "json"},
        )
        data = node.to_dict()
        self.assertEqual(data["id"], "node-3")
        self.assertEqual(data["name"], "Output Node")
        self.assertEqual(data["type"], "export")  # enum value
        self.assertEqual(data["status"], "pending")  # enum value
        self.assertEqual(data["config"], {"format": "json"})

    def test_node_to_json(self):
        """Test WorkflowNode JSON serialization."""
        node = WorkflowNode(id="n1", name="Test", type=NodeType.LLM)
        json_str = node.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["id"], "n1")
        self.assertEqual(parsed["type"], "llm")

    def test_node_from_dict(self):
        """Test WorkflowNode deserialization from dict."""
        data = {
            "id": "n-001",
            "name": "Deserialized Node",
            "type": "input",
            "status": "success",
            "config": {"key": "val"},
        }
        node = WorkflowNode.from_dict(data)
        self.assertEqual(node.id, "n-001")
        self.assertEqual(node.name, "Deserialized Node")
        self.assertEqual(node.type, NodeType.INPUT)
        self.assertEqual(node.status, NodeStatus.SUCCESS)
        self.assertEqual(node.config, {"key": "val"})


class TestWorkflowEdge(unittest.TestCase):
    """Tests for the WorkflowEdge model."""

    def test_edge_creation(self):
        """Test basic WorkflowEdge creation."""
        edge = WorkflowEdge(source_id="A", target_id="B")
        self.assertEqual(edge.source_id, "A")
        self.assertEqual(edge.target_id, "B")

    def test_edge_with_condition(self):
        """Test WorkflowEdge with condition."""
        edge = WorkflowEdge(source_id="A", target_id="B", condition="x > 0")
        self.assertEqual(edge.condition, "x > 0")

    def test_edge_default_condition(self):
        """Test WorkflowEdge default condition is None."""
        edge = WorkflowEdge(source_id="A", target_id="B")
        self.assertIsNone(edge.condition)

    def test_edge_serialization(self):
        """Test WorkflowEdge to_dict serialization."""
        edge = WorkflowEdge(source_id="src", target_id="tgt", condition="flag")
        data = edge.to_dict()
        self.assertEqual(data["source_id"], "src")
        self.assertEqual(data["target_id"], "tgt")
        self.assertEqual(data["condition"], "flag")

    def test_edge_from_dict(self):
        """Test WorkflowEdge deserialization from dict."""
        data = {"source_id": "s1", "target_id": "t1", "condition": "ok"}
        edge = WorkflowEdge.from_dict(data)
        self.assertEqual(edge.source_id, "s1")
        self.assertEqual(edge.target_id, "t1")
        self.assertEqual(edge.condition, "ok")


class TestWorkflow(unittest.TestCase):
    """Tests for the Workflow model."""

    def setUp(self):
        """Set up test fixtures."""
        self.nodes = [
            WorkflowNode(id="input", name="Input", type=NodeType.INPUT),
            WorkflowNode(id="process", name="Process", type=NodeType.TRANSFORM),
            WorkflowNode(id="output", name="Output", type=NodeType.EXPORT),
        ]
        self.edges = [
            WorkflowEdge(source_id="input", target_id="process"),
            WorkflowEdge(source_id="process", target_id="output"),
        ]
        self.workflow = Workflow(
            name="Test Workflow",
            description="A test workflow",
            nodes=self.nodes,
            edges=self.edges,
        )

    def test_workflow_creation(self):
        """Test basic Workflow creation."""
        self.assertEqual(self.workflow.name, "Test Workflow")
        self.assertEqual(self.workflow.description, "A test workflow")
        self.assertEqual(len(self.workflow.nodes), 3)
        self.assertEqual(len(self.workflow.edges), 2)

    def test_workflow_auto_id(self):
        """Test that workflow gets an auto-generated ID."""
        self.assertIsNotNone(self.workflow.id)

    def test_workflow_default_status(self):
        """Test that default workflow status is PENDING."""
        wf = Workflow(name="Status Test")
        self.assertEqual(wf.status, WorkflowStatus.PENDING)

    def test_workflow_serialization(self):
        """Test Workflow to_dict serialization."""
        data = self.workflow.to_dict()
        self.assertEqual(data["name"], "Test Workflow")
        self.assertEqual(data["description"], "A test workflow")
        self.assertEqual(len(data["nodes"]), 3)
        self.assertEqual(len(data["edges"]), 2)
        self.assertEqual(data["status"], "pending")
        self.assertIn("id", data)
        self.assertIn("created_at", data)

    def test_workflow_to_json(self):
        """Test Workflow JSON serialization."""
        json_str = self.workflow.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["name"], "Test Workflow")
        self.assertEqual(len(parsed["nodes"]), 3)
        self.assertEqual(len(parsed["edges"]), 2)

    def test_workflow_empty_nodes(self):
        """Test Workflow with no nodes."""
        wf = Workflow(name="Empty Workflow")
        self.assertEqual(len(wf.nodes), 0)
        self.assertEqual(len(wf.edges), 0)

    def test_workflow_from_dict(self):
        """Test Workflow deserialization from dict."""
        data = {
            "id": "wf-001",
            "name": "Loaded Workflow",
            "description": "Loaded from dict",
            "status": "success",
            "nodes": [
                {
                    "id": "n1",
                    "name": "Node 1",
                    "type": "input",
                    "status": "pending",
                    "config": {},
                    "position": {"x": 0, "y": 0},
                    "input_data": None,
                    "output_data": None,
                    "error_message": "",
                }
            ],
            "edges": [],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        wf = Workflow.from_dict(data)
        self.assertEqual(wf.id, "wf-001")
        self.assertEqual(wf.name, "Loaded Workflow")
        self.assertEqual(len(wf.nodes), 1)
        self.assertEqual(wf.status, WorkflowStatus.SUCCESS)

    def test_workflow_get_node(self):
        """Test get_node method."""
        node = self.workflow.get_node("process")
        self.assertIsNotNone(node)
        self.assertEqual(node.name, "Process")

    def test_workflow_get_node_not_found(self):
        """Test get_node with nonexistent ID."""
        node = self.workflow.get_node("nonexistent")
        self.assertIsNone(node)

    def test_workflow_get_input_nodes(self):
        """Test get_input_nodes returns nodes with no incoming edges."""
        input_nodes = self.workflow.get_input_nodes()
        self.assertEqual(len(input_nodes), 1)
        self.assertEqual(input_nodes[0].id, "input")

    def test_workflow_get_downstream_nodes(self):
        """Test get_downstream_nodes."""
        downstream = self.workflow.get_downstream_nodes("input")
        self.assertEqual(len(downstream), 1)
        self.assertEqual(downstream[0].id, "process")

    def test_workflow_get_upstream_nodes(self):
        """Test get_upstream_nodes."""
        upstream = self.workflow.get_upstream_nodes("output")
        self.assertEqual(len(upstream), 1)
        self.assertEqual(upstream[0].id, "process")

    def test_workflow_add_node(self):
        """Test add_node method."""
        new_node = WorkflowNode(id="extra", name="Extra", type=NodeType.FILTER)
        self.workflow.add_node(new_node)
        self.assertEqual(len(self.workflow.nodes), 4)
        self.assertIsNotNone(self.workflow.get_node("extra"))

    def test_workflow_add_edge(self):
        """Test add_edge method."""
        new_edge = WorkflowEdge(source_id="extra", target_id="output")
        self.workflow.add_edge(new_edge)
        self.assertEqual(len(self.workflow.edges), 3)

    def test_workflow_remove_node(self):
        """Test remove_node method."""
        result = self.workflow.remove_node("process")
        self.assertTrue(result)
        self.assertEqual(len(self.workflow.nodes), 2)
        # Associated edges should also be removed
        self.assertEqual(len(self.workflow.edges), 0)
        self.assertIsNone(self.workflow.get_node("process"))


class TestSearchResult(unittest.TestCase):
    """Tests for the SearchResult model."""

    def test_search_result_creation(self):
        """Test basic SearchResult creation."""
        snippet = KnowledgeSnippet(title="Test", content="Content")
        result = __import__("mindflow_cli.models", fromlist=["SearchResult"]).SearchResult(
            snippet=snippet,
            score=0.95,
            highlighted_title="<b>Test</b>",
            matched_terms=["test"],
        )
        self.assertEqual(result.score, 0.95)
        self.assertEqual(result.matched_terms, ["test"])

    def test_search_result_defaults(self):
        """Test SearchResult default values."""
        SearchResult = __import__("mindflow_cli.models", fromlist=["SearchResult"]).SearchResult
        result = SearchResult()
        self.assertEqual(result.score, 0.0)
        self.assertEqual(result.highlighted_title, "")
        self.assertEqual(result.highlighted_content, "")
        self.assertEqual(result.matched_terms, [])

    def test_search_result_serialization(self):
        """Test SearchResult to_dict serialization."""
        SearchResult = __import__("mindflow_cli.models", fromlist=["SearchResult"]).SearchResult
        snippet = KnowledgeSnippet(title="T", content="C")
        result = SearchResult(snippet=snippet, score=0.5, matched_terms=["t"])
        data = result.to_dict()
        self.assertEqual(data["score"], 0.5)
        self.assertIn("snippet", data)
        self.assertEqual(data["matched_terms"], ["t"])


class TestWorkflowExecutionLog(unittest.TestCase):
    """Tests for the WorkflowExecutionLog model."""

    def test_execution_log_creation(self):
        """Test basic WorkflowExecutionLog creation."""
        WorkflowExecutionLog = __import__(
            "mindflow_cli.models", fromlist=["WorkflowExecutionLog"]
        ).WorkflowExecutionLog
        log = WorkflowExecutionLog(
            workflow_id="wf-1",
            workflow_name="Test",
            status=WorkflowStatus.SUCCESS,
        )
        self.assertEqual(log.workflow_id, "wf-1")
        self.assertEqual(log.workflow_name, "Test")
        self.assertEqual(log.status, WorkflowStatus.SUCCESS)

    def test_execution_log_duration(self):
        """Test duration calculation."""
        WorkflowExecutionLog = __import__(
            "mindflow_cli.models", fromlist=["WorkflowExecutionLog"]
        ).WorkflowExecutionLog
        log = WorkflowExecutionLog(
            start_time="2024-01-01T00:00:00",
            end_time="2024-01-01T00:01:30",
        )
        self.assertAlmostEqual(log.duration(), 90.0)

    def test_execution_log_duration_no_times(self):
        """Test duration returns 0 when times are not set."""
        WorkflowExecutionLog = __import__(
            "mindflow_cli.models", fromlist=["WorkflowExecutionLog"]
        ).WorkflowExecutionLog
        log = WorkflowExecutionLog()
        self.assertEqual(log.duration(), 0.0)


if __name__ == "__main__":
    unittest.main()
