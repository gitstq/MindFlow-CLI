"""
数据模型定义 / Data Model Definitions

定义MindFlow-CLI中使用的所有核心数据模型，包括知识片段、工作流、节点、标签和搜索结果。
Defines all core data models used in MindFlow-CLI, including knowledge snippets,
workflows, nodes, tags, and search results.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeType(str, Enum):
    """工作流节点类型 / Workflow node types"""
    LLM = "llm"
    TRANSFORM = "transform"
    FILTER = "filter"
    EXPORT = "export"
    INPUT = "input"
    MERGE = "merge"


class NodeStatus(str, Enum):
    """节点执行状态 / Node execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(str, Enum):
    """工作流执行状态 / Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class LLMProvider(str, Enum):
    """LLM服务提供商 / LLM service providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


@dataclass
class KnowledgeSnippet:
    """
    知识片段模型 / Knowledge Snippet Model

    表示一条知识条目，包含标题、内容、标签和元数据。
    Represents a single knowledge entry with title, content, tags, and metadata.

    属性 / Attributes:
        id: 唯一标识符 / Unique identifier
        title: 标题 / Title
        content: 内容 / Content
        tags: 标签列表 / List of tags
        source: 来源 / Source
        created_at: 创建时间 / Creation time
        updated_at: 更新时间 / Update time
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    tags: List[str] = field(default_factory=list)
    source: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """转换为JSON字符串 / Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> KnowledgeSnippet:
        """从字典创建 / Create from dictionary"""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> KnowledgeSnippet:
        """从JSON字符串创建 / Create from JSON string"""
        return cls.from_dict(json.loads(json_str))

    def update_timestamp(self) -> None:
        """更新时间戳 / Update timestamp"""
        self.updated_at = datetime.now().isoformat()

    def summary(self, max_length: int = 100) -> str:
        """
        获取内容摘要 / Get content summary

        参数 / Args:
            max_length: 最大长度 / Maximum length

        返回 / Returns:
            截断后的内容摘要 / Truncated content summary
        """
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."


@dataclass
class Tag:
    """
    标签模型 / Tag Model

    用于知识片段的分类和组织。
    Used for categorizing and organizing knowledge snippets.

    属性 / Attributes:
        id: 唯一标识符 / Unique identifier
        name: 标签名称 / Tag name
        color: 显示颜色 / Display color
        count: 关联的知识片段数量 / Number of associated knowledge snippets
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    color: str = "#3498db"
    count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """转换为JSON字符串 / Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Tag:
        """从字典创建 / Create from dictionary"""
        return cls(**data)


@dataclass
class WorkflowNode:
    """
    工作流节点模型 / Workflow Node Model

    工作流中的单个执行节点，定义了处理逻辑和配置。
    A single execution node in a workflow, defining processing logic and configuration.

    属性 / Attributes:
        id: 节点唯一标识符 / Node unique identifier
        type: 节点类型 / Node type
        name: 节点名称 / Node name
        config: 节点配置 / Node configuration
        position: 在DAG中的位置 / Position in DAG
        status: 执行状态 / Execution status
        input_data: 输入数据 / Input data
        output_data: 输出数据 / Output data
        error_message: 错误信息 / Error message
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: NodeType = NodeType.TRANSFORM
    name: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, int] = field(default_factory=lambda: {"x": 0, "y": 0})
    status: NodeStatus = NodeStatus.PENDING
    input_data: Any = None
    output_data: Any = None
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        data = asdict(self)
        data["type"] = self.type.value
        data["status"] = self.status.value
        return data

    def to_json(self) -> str:
        """转换为JSON字符串 / Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WorkflowNode:
        """从字典创建 / Create from dictionary"""
        if "type" in data and isinstance(data["type"], str):
            data["type"] = NodeType(data["type"])
        if "status" in data and isinstance(data["status"], str):
            data["status"] = NodeStatus(data["status"])
        return cls(**data)


@dataclass
class WorkflowEdge:
    """
    工作流边模型 / Workflow Edge Model

    定义工作流节点之间的连接关系。
    Defines connections between workflow nodes.

    属性 / Attributes:
        source_id: 源节点ID / Source node ID
        target_id: 目标节点ID / Target node ID
        condition: 条件表达式（可选） / Conditional expression (optional)
    """
    source_id: str = ""
    target_id: str = ""
    condition: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WorkflowEdge:
        """从字典创建 / Create from dictionary"""
        return cls(**data)


@dataclass
class Workflow:
    """
    工作流模型 / Workflow Model

    定义一个完整的知识处理工作流，包含多个节点和边。
    Defines a complete knowledge processing workflow with multiple nodes and edges.

    属性 / Attributes:
        id: 唯一标识符 / Unique identifier
        name: 工作流名称 / Workflow name
        description: 描述 / Description
        nodes: 节点列表 / List of nodes
        edges: 边列表 / List of edges
        created_at: 创建时间 / Creation time
        updated_at: 更新时间 / Update time
        status: 执行状态 / Execution status
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[WorkflowEdge] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: WorkflowStatus = WorkflowStatus.PENDING

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    def to_json(self) -> str:
        """转换为JSON字符串 / Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Workflow:
        """从字典创建 / Create from dictionary"""
        if "nodes" in data:
            data["nodes"] = [WorkflowNode.from_dict(n) for n in data["nodes"]]
        if "edges" in data:
            data["edges"] = [WorkflowEdge.from_dict(e) for e in data["edges"]]
        if "status" in data and isinstance(data["status"], str):
            data["status"] = WorkflowStatus(data["status"])
        return cls(**data)

    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """根据ID获取节点 / Get node by ID"""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_input_nodes(self) -> List[WorkflowNode]:
        """获取所有输入节点 / Get all input nodes"""
        target_ids = {edge.target_id for edge in self.edges}
        return [node for node in self.nodes if node.id not in target_ids]

    def get_downstream_nodes(self, node_id: str) -> List[WorkflowNode]:
        """获取下游节点 / Get downstream nodes"""
        downstream_ids = {
            edge.target_id
            for edge in self.edges
            if edge.source_id == node_id
        }
        return [
            node for node in self.nodes if node.id in downstream_ids
        ]

    def get_upstream_nodes(self, node_id: str) -> List[WorkflowNode]:
        """获取上游节点 / Get upstream nodes"""
        upstream_ids = {
            edge.source_id
            for edge in self.edges
            if edge.target_id == node_id
        }
        return [
            node for node in self.nodes if node.id in upstream_ids
        ]

    def add_node(self, node: WorkflowNode) -> None:
        """添加节点 / Add node"""
        self.nodes.append(node)
        self.updated_at = datetime.now().isoformat()

    def add_edge(self, edge: WorkflowEdge) -> None:
        """添加边 / Add edge"""
        self.edges.append(edge)
        self.updated_at = datetime.now().isoformat()

    def remove_node(self, node_id: str) -> bool:
        """
        移除节点及其关联的边 / Remove node and its associated edges

        返回 / Returns:
            是否成功移除 / Whether successfully removed
        """
        self.nodes = [n for n in self.nodes if n.id != node_id]
        self.edges = [
            e for e in self.edges
            if e.source_id != node_id and e.target_id != node_id
        ]
        self.updated_at = datetime.now().isoformat()
        return True


@dataclass
class SearchResult:
    """
    搜索结果模型 / Search Result Model

    表示一次搜索的结果条目。
    Represents a single search result entry.

    属性 / Attributes:
        snippet: 知识片段 / Knowledge snippet
        score: 相关性分数 / Relevance score
        highlighted_title: 高亮标题 / Highlighted title
        highlighted_content: 高亮内容 / Highlighted content
        matched_terms: 匹配的搜索词 / Matched search terms
    """
    snippet: KnowledgeSnippet = field(default_factory=KnowledgeSnippet)
    score: float = 0.0
    highlighted_title: str = ""
    highlighted_content: str = ""
    matched_terms: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "snippet": self.snippet.to_dict(),
            "score": self.score,
            "highlighted_title": self.highlighted_title,
            "highlighted_content": self.highlighted_content,
            "matched_terms": self.matched_terms,
        }


@dataclass
class WorkflowExecutionLog:
    """
    工作流执行日志 / Workflow Execution Log

    记录工作流执行过程中的详细信息。
    Records detailed information during workflow execution.

    属性 / Attributes:
        workflow_id: 工作流ID / Workflow ID
        workflow_name: 工作流名称 / Workflow name
        start_time: 开始时间 / Start time
        end_time: 结束时间 / End time
        status: 执行状态 / Execution status
        node_logs: 节点执行日志 / Node execution logs
        error_message: 错误信息 / Error message
    """
    workflow_id: str = ""
    workflow_name: str = ""
    start_time: str = ""
    end_time: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    node_logs: List[Dict[str, Any]] = field(default_factory=list)
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status.value,
            "node_logs": self.node_logs,
            "error_message": self.error_message,
        }

    def duration(self) -> float:
        """
        计算执行时长（秒） / Calculate execution duration in seconds

        返回 / Returns:
            执行时长，如果未结束返回0 / Duration in seconds, 0 if not finished
        """
        if not self.start_time or not self.end_time:
            return 0.0
        try:
            start = datetime.fromisoformat(self.start_time)
            end = datetime.fromisoformat(self.end_time)
            return (end - start).total_seconds()
        except (ValueError, TypeError):
            return 0.0
