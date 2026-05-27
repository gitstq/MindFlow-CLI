# -*- coding: utf-8 -*-
"""Tests for storage layer: database initialization and CRUD operations."""

import json
import os
import sqlite3
import tempfile
import unittest

from mindflow_cli.models import KnowledgeSnippet, NodeType, Tag, Workflow, WorkflowEdge, WorkflowNode
from mindflow_cli.storage import Storage


class TestStorageInitialization(unittest.TestCase):
    """Tests for database initialization."""

    def test_create_storage_with_path(self):
        """Test creating a Storage instance with a specific path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = Storage(db_path=db_path)
            self.assertIsNotNone(storage)
            self.assertEqual(storage.db_path, db_path)
            storage.close()

    def test_database_file_created(self):
        """Test that the database file is created after initialize()."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_init.db")
            storage = Storage(db_path=db_path)
            storage.initialize()
            self.assertTrue(os.path.exists(db_path))
            storage.close()

    def test_tables_created(self):
        """Test that all required tables are created after initialize()."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_tables.db")
            storage = Storage(db_path=db_path)
            storage.initialize()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            self.assertIn("snippets", tables)
            self.assertIn("tags", tables)
            self.assertIn("workflows", tables)
            self.assertIn("snippet_tags", tables)
            self.assertIn("workflow_logs", tables)
            self.assertIn("search_index", tables)
            conn.close()
            storage.close()

    def test_in_memory_storage(self):
        """Test creating an in-memory storage."""
        storage = Storage(db_path=":memory:")
        storage.initialize()
        self.assertIsNotNone(storage)
        storage.close()


class TestSnippetCRUD(unittest.TestCase):
    """Tests for KnowledgeSnippet CRUD operations."""

    def setUp(self):
        """Set up a temporary database for each test."""
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_crud.db")
        self.storage = Storage(db_path=self.db_path)
        self.storage.initialize()

    def tearDown(self):
        """Clean up after each test."""
        self.storage.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.tmpdir)

    def test_create_snippet(self):
        """Test creating a new snippet."""
        snippet = self.storage.create_snippet(
            title="Test Snippet",
            content="Test content for CRUD.",
            source="unit_test",
        )
        self.assertIsNotNone(snippet)
        self.assertIsInstance(snippet, KnowledgeSnippet)
        self.assertTrue(len(snippet.id) > 0)
        self.assertEqual(snippet.title, "Test Snippet")

    def test_read_snippet(self):
        """Test reading a snippet by ID."""
        created = self.storage.create_snippet(
            title="Read Test",
            content="Content to read.",
            source="test",
        )
        snippet = self.storage.get_snippet(created.id)
        self.assertIsNotNone(snippet)
        self.assertEqual(snippet.title, "Read Test")
        self.assertEqual(snippet.content, "Content to read.")
        self.assertEqual(snippet.source, "test")

    def test_read_nonexistent_snippet(self):
        """Test reading a snippet that doesn't exist."""
        snippet = self.storage.get_snippet("nonexistent-id")
        self.assertIsNone(snippet)

    def test_update_snippet(self):
        """Test updating a snippet."""
        created = self.storage.create_snippet(
            title="Original Title",
            content="Original content.",
            source="test",
        )
        updated = self.storage.update_snippet(
            created.id,
            title="Updated Title",
            content="Updated content.",
        )
        self.assertIsNotNone(updated)
        self.assertEqual(updated.title, "Updated Title")
        self.assertEqual(updated.content, "Updated content.")

    def test_delete_snippet(self):
        """Test deleting a snippet."""
        created = self.storage.create_snippet(
            title="To Delete",
            content="Will be deleted.",
            source="test",
        )
        self.storage.delete_snippet(created.id)
        snippet = self.storage.get_snippet(created.id)
        self.assertIsNone(snippet)

    def test_delete_nonexistent_snippet(self):
        """Test deleting a snippet that doesn't exist."""
        result = self.storage.delete_snippet("nonexistent-id")
        self.assertFalse(result)

    def test_list_snippets(self):
        """Test listing all snippets."""
        self.storage.create_snippet(title="Snippet 1", content="Content 1", source="test")
        self.storage.create_snippet(title="Snippet 2", content="Content 2", source="test")
        self.storage.create_snippet(title="Snippet 3", content="Content 3", source="test")
        snippets, total = self.storage.list_snippets()
        self.assertEqual(total, 3)
        self.assertEqual(len(snippets), 3)

    def test_list_snippets_empty(self):
        """Test listing snippets when database is empty."""
        snippets, total = self.storage.list_snippets()
        self.assertEqual(total, 0)
        self.assertEqual(len(snippets), 0)

    def test_search_snippets(self):
        """Test searching snippets by keyword."""
        self.storage.create_snippet(
            title="Python Tutorial",
            content="Learn Python programming basics.",
            source="test",
        )
        self.storage.create_snippet(
            title="Java Guide",
            content="Learn Java programming.",
            source="test",
        )
        snippets, total = self.storage.list_snippets(search_query="Python")
        self.assertTrue(len(snippets) > 0)
        titles = [s.title for s in snippets]
        self.assertIn("Python Tutorial", titles)

    def test_create_snippet_with_tags(self):
        """Test creating a snippet with tags."""
        snippet = self.storage.create_snippet(
            title="Tagged Snippet",
            content="Content with tags.",
            tags=["python", "ai"],
        )
        self.assertEqual(snippet.tags, ["python", "ai"])
        # Verify tags were persisted
        fetched = self.storage.get_snippet(snippet.id)
        self.assertEqual(set(fetched.tags), {"python", "ai"})

    def test_count_snippets(self):
        """Test counting snippets."""
        self.storage.create_snippet(title="S1", content="C1")
        self.storage.create_snippet(title="S2", content="C2")
        count = self.storage.count_snippets()
        self.assertEqual(count, 2)


class TestTagCRUD(unittest.TestCase):
    """Tests for Tag operations."""

    def setUp(self):
        """Set up a temporary database for each test."""
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_tags.db")
        self.storage = Storage(db_path=self.db_path)
        self.storage.initialize()

    def tearDown(self):
        """Clean up after each test."""
        self.storage.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.tmpdir)

    def test_tag_created_via_snippet(self):
        """Test that tags are created when a snippet with tags is created."""
        snippet = self.storage.create_snippet(
            title="Test",
            content="Content",
            tags=["python", "ai"],
        )
        tags = self.storage.list_tags()
        tag_names = {t.name for t in tags}
        self.assertIn("python", tag_names)
        self.assertIn("ai", tag_names)

    def test_list_tags(self):
        """Test listing all tags."""
        self.storage.create_snippet(title="S1", content="C1", tags=["python"])
        self.storage.create_snippet(title="S2", content="C2", tags=["ai"])
        self.storage.create_snippet(title="S3", content="C3", tags=["nlp"])
        tags = self.storage.list_tags()
        self.assertEqual(len(tags), 3)

    def test_delete_tag(self):
        """Test deleting a tag by name."""
        self.storage.create_snippet(title="S1", content="C1", tags=["temp"])
        result = self.storage.delete_tag("temp")
        self.assertTrue(result)
        tags = self.storage.list_tags()
        tag_names = {t.name for t in tags}
        self.assertNotIn("temp", tag_names)

    def test_delete_nonexistent_tag(self):
        """Test deleting a tag that doesn't exist."""
        result = self.storage.delete_tag("nonexistent")
        self.assertFalse(result)

    def test_tag_count_increments(self):
        """Test that tag count increments when snippets are created."""
        self.storage.create_snippet(title="S1", content="C1", tags=["python"])
        self.storage.create_snippet(title="S2", content="C2", tags=["python"])
        tags = self.storage.list_tags()
        python_tag = next(t for t in tags if t.name == "python")
        self.assertEqual(python_tag.count, 2)


class TestWorkflowCRUD(unittest.TestCase):
    """Tests for Workflow CRUD operations."""

    def setUp(self):
        """Set up a temporary database for each test."""
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_wf.db")
        self.storage = Storage(db_path=self.db_path)
        self.storage.initialize()

    def tearDown(self):
        """Clean up after each test."""
        self.storage.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.tmpdir)

    def test_save_workflow(self):
        """Test saving a workflow."""
        wf = Workflow(name="Test Workflow", description="A test workflow.")
        saved = self.storage.save_workflow(wf)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.name, "Test Workflow")

    def test_get_workflow(self):
        """Test retrieving a workflow."""
        wf = Workflow(name="Get Test", description="Workflow to retrieve.")
        saved = self.storage.save_workflow(wf)
        fetched = self.storage.get_workflow(saved.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Get Test")

    def test_get_workflow_not_found(self):
        """Test retrieving a workflow that doesn't exist."""
        fetched = self.storage.get_workflow("nonexistent-id")
        self.assertIsNone(fetched)

    def test_delete_workflow(self):
        """Test deleting a workflow."""
        wf = Workflow(name="Delete Me")
        saved = self.storage.save_workflow(wf)
        result = self.storage.delete_workflow(saved.id)
        self.assertTrue(result)
        fetched = self.storage.get_workflow(saved.id)
        self.assertIsNone(fetched)

    def test_delete_nonexistent_workflow(self):
        """Test deleting a workflow that doesn't exist."""
        result = self.storage.delete_workflow("nonexistent-id")
        self.assertFalse(result)

    def test_list_workflows(self):
        """Test listing all workflows."""
        wf1 = Workflow(name="WF 1")
        wf2 = Workflow(name="WF 2")
        self.storage.save_workflow(wf1)
        self.storage.save_workflow(wf2)
        workflows = self.storage.list_workflows()
        self.assertEqual(len(workflows), 2)

    def test_save_workflow_with_nodes_and_edges(self):
        """Test saving a workflow with nodes and edges."""
        nodes = [
            WorkflowNode(id="A", name="Input", type=NodeType.INPUT),
            WorkflowNode(id="B", name="Process", type=NodeType.TRANSFORM),
        ]
        edges = [WorkflowEdge(source_id="A", target_id="B")]
        wf = Workflow(name="Complex WF", nodes=nodes, edges=edges)
        saved = self.storage.save_workflow(wf)
        fetched = self.storage.get_workflow(saved.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(len(fetched.nodes), 2)
        self.assertEqual(len(fetched.edges), 1)
        self.assertEqual(fetched.nodes[0].id, "A")
        self.assertEqual(fetched.edges[0].source_id, "A")


if __name__ == "__main__":
    unittest.main()
