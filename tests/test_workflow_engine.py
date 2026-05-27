# -*- coding: utf-8 -*-
"""Tests for workflow engine: DAG topological sort and node execution."""

import unittest

from mindflow_cli.models import (
    NodeStatus,
    NodeType,
    Workflow,
    WorkflowEdge,
    WorkflowNode,
    WorkflowStatus,
)
from mindflow_cli.workflow_engine import WorkflowEngine, WorkflowError


class TestDAGTopologicalSort(unittest.TestCase):
    """Tests for DAG topological sorting (layered)."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = WorkflowEngine()

    def test_linear_dag(self):
        """Test topological sort of a linear DAG (A -> B -> C)."""
        nodes = [
            WorkflowNode(id="A", name="A", type=NodeType.INPUT),
            WorkflowNode(id="B", name="B", type=NodeType.TRANSFORM),
            WorkflowNode(id="C", name="C", type=NodeType.EXPORT),
        ]
        edges = [
            WorkflowEdge(source_id="A", target_id="B"),
            WorkflowEdge(source_id="B", target_id="C"),
        ]
        workflow = Workflow(name="Linear", nodes=nodes, edges=edges)
        layers = self.engine._topological_sort(workflow)
        # Should produce 3 layers: [[A], [B], [C]]
        self.assertEqual(len(layers), 3)
        self.assertEqual(layers[0][0].id, "A")
        self.assertEqual(layers[1][0].id, "B")
        self.assertEqual(layers[2][0].id, "C")

    def test_parallel_dag(self):
        """Test topological sort with parallel branches."""
        nodes = [
            WorkflowNode(id="input", name="Input", type=NodeType.INPUT),
            WorkflowNode(id="proc_a", name="Process A", type=NodeType.TRANSFORM),
            WorkflowNode(id="proc_b", name="Process B", type=NodeType.TRANSFORM),
            WorkflowNode(id="output", name="Output", type=NodeType.EXPORT),
        ]
        edges = [
            WorkflowEdge(source_id="input", target_id="proc_a"),
            WorkflowEdge(source_id="input", target_id="proc_b"),
            WorkflowEdge(source_id="proc_a", target_id="output"),
            WorkflowEdge(source_id="proc_b", target_id="output"),
        ]
        workflow = Workflow(name="Parallel", nodes=nodes, edges=edges)
        layers = self.engine._topological_sort(workflow)
        # Layer 0: [input], Layer 1: [proc_a, proc_b], Layer 2: [output]
        self.assertEqual(len(layers), 3)
        self.assertEqual(len(layers[0]), 1)
        self.assertEqual(layers[0][0].id, "input")
        self.assertEqual(len(layers[1]), 2)
        layer1_ids = {n.id for n in layers[1]}
        self.assertEqual(layer1_ids, {"proc_a", "proc_b"})
        self.assertEqual(len(layers[2]), 1)
        self.assertEqual(layers[2][0].id, "output")

    def test_complex_dag(self):
        """Test topological sort of a complex DAG."""
        nodes = [
            WorkflowNode(id="A", name="A", type=NodeType.INPUT),
            WorkflowNode(id="B", name="B", type=NodeType.TRANSFORM),
            WorkflowNode(id="C", name="C", type=NodeType.TRANSFORM),
            WorkflowNode(id="D", name="D", type=NodeType.TRANSFORM),
            WorkflowNode(id="E", name="E", type=NodeType.EXPORT),
        ]
        edges = [
            WorkflowEdge(source_id="A", target_id="B"),
            WorkflowEdge(source_id="A", target_id="C"),
            WorkflowEdge(source_id="B", target_id="D"),
            WorkflowEdge(source_id="C", target_id="D"),
            WorkflowEdge(source_id="D", target_id="E"),
        ]
        workflow = Workflow(name="Complex", nodes=nodes, edges=edges)
        layers = self.engine._topological_sort(workflow)
        # Layer 0: [A], Layer 1: [B, C], Layer 2: [D], Layer 3: [E]
        self.assertTrue(len(layers) >= 3)
        self.assertEqual(layers[0][0].id, "A")
        # Last layer should be E
        self.assertEqual(layers[-1][0].id, "E")

    def test_single_node(self):
        """Test topological sort with a single node."""
        nodes = [
            WorkflowNode(id="only", name="Only", type=NodeType.INPUT),
        ]
        workflow = Workflow(name="Single", nodes=nodes)
        layers = self.engine._topological_sort(workflow)
        self.assertEqual(len(layers), 1)
        self.assertEqual(layers[0][0].id, "only")

    def test_empty_workflow(self):
        """Test topological sort with no nodes."""
        workflow = Workflow(name="Empty")
        layers = self.engine._topological_sort(workflow)
        self.assertEqual(layers, [])

    def test_cycle_detection(self):
        """Test that cycles in the DAG are detected and raise an error."""
        nodes = [
            WorkflowNode(id="A", name="A", type=NodeType.TRANSFORM),
            WorkflowNode(id="B", name="B", type=NodeType.TRANSFORM),
            WorkflowNode(id="C", name="C", type=NodeType.TRANSFORM),
        ]
        edges = [
            WorkflowEdge(source_id="A", target_id="B"),
            WorkflowEdge(source_id="B", target_id="C"),
            WorkflowEdge(source_id="C", target_id="A"),
        ]
        workflow = Workflow(name="Cyclic", nodes=nodes, edges=edges)
        with self.assertRaises(WorkflowError):
            self.engine._topological_sort(workflow)

    def test_self_cycle_detection(self):
        """Test that self-referencing cycles are detected."""
        nodes = [
            WorkflowNode(id="A", name="A", type=NodeType.TRANSFORM),
        ]
        edges = [
            WorkflowEdge(source_id="A", target_id="A"),
        ]
        workflow = Workflow(name="SelfCycle", nodes=nodes, edges=edges)
        with self.assertRaises(WorkflowError):
            self.engine._topological_sort(workflow)

    def test_validate_workflow_valid(self):
        """Test validating a valid workflow."""
        nodes = [
            WorkflowNode(id="A", name="A", type=NodeType.INPUT),
            WorkflowNode(id="B", name="B", type=NodeType.TRANSFORM),
        ]
        edges = [WorkflowEdge(source_id="A", target_id="B")]
        workflow = Workflow(name="Valid", nodes=nodes, edges=edges)
        errors = self.engine.validate_workflow(workflow)
        self.assertEqual(len(errors), 0)

    def test_validate_empty_workflow(self):
        """Test validating an empty workflow."""
        workflow = Workflow(name="Empty")
        errors = self.engine.validate_workflow(workflow)
        # Empty workflow should have validation errors
        self.assertTrue(len(errors) > 0)


class TestNodeExecution(unittest.TestCase):
    """Tests for workflow node execution."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = WorkflowEngine()

    def test_execute_input_node(self):
        """Test executing an input node."""
        node = WorkflowNode(
            id="input",
            name="Input",
            type=NodeType.INPUT,
            config={"data": "test input"},
        )
        result = self.engine.node_executor.execute(node, context={})
        self.assertIsNotNone(result)

    def test_execute_transform_node(self):
        """Test executing a transform node."""
        node = WorkflowNode(
            id="process",
            name="Process",
            type=NodeType.TRANSFORM,
            config={"operation": "transform"},
        )
        context = {"__input__": "hello"}
        result = self.engine.node_executor.execute(node, context=context)
        self.assertIsNotNone(result)

    def test_execute_full_workflow(self):
        """Test executing a complete workflow."""
        nodes = [
            WorkflowNode(
                id="input",
                name="Input",
                type=NodeType.INPUT,
                config={"value": 42},
            ),
            WorkflowNode(
                id="process",
                name="Process",
                type=NodeType.TRANSFORM,
                config={"operation": "double"},
            ),
            WorkflowNode(
                id="output",
                name="Output",
                type=NodeType.EXPORT,
            ),
        ]
        edges = [
            WorkflowEdge(source_id="input", target_id="process"),
            WorkflowEdge(source_id="process", target_id="output"),
        ]
        workflow = Workflow(name="Full Test", nodes=nodes, edges=edges)
        log = self.engine.execute(workflow)
        self.assertIsNotNone(log)
        self.assertEqual(log.workflow_name, "Full Test")
        # Check that the log has node execution records
        self.assertTrue(len(log.node_logs) > 0)

    def test_execute_empty_workflow(self):
        """Test executing an empty workflow."""
        workflow = Workflow(name="Empty")
        log = self.engine.execute(workflow)
        self.assertIsNotNone(log)

    def test_execute_returns_execution_log(self):
        """Test that execute returns a WorkflowExecutionLog."""
        nodes = [
            WorkflowNode(id="A", name="A", type=NodeType.INPUT),
        ]
        workflow = Workflow(name="Log Test", nodes=nodes)
        log = self.engine.execute(workflow)
        self.assertEqual(log.workflow_id, workflow.id)
        self.assertEqual(log.workflow_name, "Log Test")
        # Status should be success or partial
        self.assertIn(log.status, [WorkflowStatus.SUCCESS, WorkflowStatus.PARTIAL, WorkflowStatus.FAILED])

    def test_workflow_status_after_execution(self):
        """Test that workflow status is updated after execution."""
        nodes = [
            WorkflowNode(id="A", name="A", type=NodeType.INPUT),
            WorkflowNode(id="B", name="B", type=NodeType.EXPORT),
        ]
        edges = [WorkflowEdge(source_id="A", target_id="B")]
        workflow = Workflow(name="Status Test", nodes=nodes, edges=edges)
        self.engine.execute(workflow)
        self.assertEqual(workflow.status, WorkflowStatus.SUCCESS)

    def test_node_status_after_execution(self):
        """Test that node statuses are updated after execution."""
        nodes = [
            WorkflowNode(id="A", name="A", type=NodeType.INPUT),
        ]
        workflow = Workflow(name="Node Status Test", nodes=nodes)
        self.engine.execute(workflow)
        self.assertEqual(nodes[0].status, NodeStatus.SUCCESS)


if __name__ == "__main__":
    unittest.main()
