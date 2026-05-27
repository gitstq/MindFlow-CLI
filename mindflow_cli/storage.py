"""
SQLite存储引擎 / SQLite Storage Engine

提供知识片段、工作流和标签的持久化存储，使用Python内置sqlite3模块。
Provides persistent storage for knowledge snippets, workflows, and tags
using Python's built-in sqlite3 module.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    KnowledgeSnippet,
    Tag,
    Workflow,
    WorkflowEdge,
    WorkflowNode,
)


class Storage:
    """
    SQLite存储引擎 / SQLite Storage Engine

    管理所有数据的持久化操作，包括自动建表、数据迁移和事务支持。
    Manages all data persistence operations including auto table creation,
    data migration, and transaction support.

    用法 / Usage:
        storage = Storage("/path/to/mindflow.db")
        storage.initialize()
        snippet = storage.create_snippet("标题", "内容", ["标签"])
    """

    # 数据库版本，用于迁移 / Database version for migration
    DB_VERSION = 1

    def __init__(self, db_path: str) -> None:
        """
        初始化存储引擎 / Initialize storage engine

        参数 / Args:
            db_path: 数据库文件路径 / Database file path
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

    def _get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接 / Get database connection

        返回 / Returns:
            SQLite连接对象 / SQLite connection object
        """
        if self._connection is None:
            # 确保数据库目录存在 / Ensure database directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
            # 启用外键约束 / Enable foreign key constraints
            self._connection.execute("PRAGMA foreign_keys = ON")
            # 启用WAL模式以提高并发性能 / Enable WAL mode for better concurrency
            self._connection.execute("PRAGMA journal_mode = WAL")
        return self._connection

    def close(self) -> None:
        """关闭数据库连接 / Close database connection"""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def initialize(self) -> None:
        """
        初始化数据库 / Initialize database

        创建所有必要的表和索引。
        Creates all necessary tables and indexes.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 创建元数据表 / Create metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS _metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # 创建知识片段表 / Create knowledge snippets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snippets (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # 创建标签表 / Create tags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                color TEXT NOT NULL DEFAULT '#3498db',
                count INTEGER NOT NULL DEFAULT 0
            )
        """)

        # 创建知识片段-标签关联表 / Create snippet-tag association table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snippet_tags (
                snippet_id TEXT NOT NULL,
                tag_id TEXT NOT NULL,
                PRIMARY KEY (snippet_id, tag_id),
                FOREIGN KEY (snippet_id) REFERENCES snippets(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)

        # 创建工作流表 / Create workflows table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                nodes_json TEXT NOT NULL DEFAULT '[]',
                edges_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # 创建工作流执行日志表 / Create workflow execution logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL,
                workflow_name TEXT NOT NULL DEFAULT '',
                start_time TEXT NOT NULL,
                end_time TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                log_json TEXT NOT NULL DEFAULT '{}',
                error_message TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
            )
        """)

        # 创建搜索索引表 / Create search index table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_index (
                snippet_id TEXT NOT NULL,
                term TEXT NOT NULL,
                frequency INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (snippet_id, term),
                FOREIGN KEY (snippet_id) REFERENCES snippets(id) ON DELETE CASCADE
            )
        """)

        # 创建索引 / Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_snippets_title ON snippets(title)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_snippets_created ON snippets(created_at)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_snippets_updated ON snippets(updated_at)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_snippet_tags_tag ON snippet_tags(tag_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_search_term ON search_index(term)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_search_snippet ON search_index(snippet_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_workflow_logs_workflow ON workflow_logs(workflow_id)"
        )

        # 设置数据库版本 / Set database version
        cursor.execute(
            "INSERT OR REPLACE INTO _metadata (key, value) VALUES (?, ?)",
            ("db_version", str(self.DB_VERSION)),
        )

        conn.commit()

    def _migrate(self) -> None:
        """
        执行数据库迁移 / Execute database migration

        根据当前版本号执行必要的迁移操作。
        Executes necessary migrations based on current version number.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT value FROM _metadata WHERE key = 'db_version'"
            )
            row = cursor.fetchone()
            current_version = int(row["value"]) if row else 0
        except (sqlite3.OperationalError, TypeError, ValueError):
            current_version = 0

        # 在此处添加迁移逻辑 / Add migration logic here
        # if current_version < 2:
        #     cursor.execute("ALTER TABLE snippets ADD COLUMN ...")
        #     current_version = 2

        cursor.execute(
            "INSERT OR REPLACE INTO _metadata (key, value) VALUES (?, ?)",
            ("db_version", str(self.DB_VERSION)),
        )
        conn.commit()

    # ============================================================
    # 知识片段 CRUD / Knowledge Snippet CRUD
    # ============================================================

    def create_snippet(
        self,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        source: str = "",
    ) -> KnowledgeSnippet:
        """
        创建知识片段 / Create knowledge snippet

        参数 / Args:
            title: 标题 / Title
            content: 内容 / Content
            tags: 标签列表 / List of tags
            source: 来源 / Source

        返回 / Returns:
            创建的知识片段 / Created knowledge snippet
        """
        conn = self._get_connection()
        now = datetime.now().isoformat()

        snippet = KnowledgeSnippet(
            title=title,
            content=content,
            tags=tags or [],
            source=source,
            created_at=now,
            updated_at=now,
        )

        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO snippets (id, title, content, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    snippet.id,
                    snippet.title,
                    snippet.content,
                    snippet.source,
                    snippet.created_at,
                    snippet.updated_at,
                ),
            )

            # 处理标签 / Handle tags
            if snippet.tags:
                for tag_name in snippet.tags:
                    tag = self._get_or_create_tag(tag_name)
                    if tag:
                        cursor.execute(
                            "INSERT OR IGNORE INTO snippet_tags (snippet_id, tag_id) VALUES (?, ?)",
                            (snippet.id, tag.id),
                        )
                        cursor.execute(
                            "UPDATE tags SET count = count + 1 WHERE id = ?",
                            (tag.id,),
                        )

            conn.commit()
            return snippet
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"创建知识片段失败: {e}")

    def get_snippet(self, snippet_id: str) -> Optional[KnowledgeSnippet]:
        """
        根据ID获取知识片段 / Get knowledge snippet by ID

        参数 / Args:
            snippet_id: 知识片段ID / Snippet ID

        返回 / Returns:
            知识片段对象，如果不存在返回None / Snippet object, None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM snippets WHERE id = ?", (snippet_id,))
        row = cursor.fetchone()

        if not row:
            return None

        snippet = KnowledgeSnippet(
            id=row["id"],
            title=row["title"],
            content=row["content"],
            source=row["source"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        snippet.tags = self._get_snippet_tags(snippet_id)
        return snippet

    def update_snippet(
        self,
        snippet_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
    ) -> Optional[KnowledgeSnippet]:
        """
        更新知识片段 / Update knowledge snippet

        参数 / Args:
            snippet_id: 知识片段ID / Snippet ID
            title: 新标题（可选） / New title (optional)
            content: 新内容（可选） / New content (optional)
            tags: 新标签列表（可选） / New tags list (optional)
            source: 新来源（可选） / New source (optional)

        返回 / Returns:
            更新后的知识片段 / Updated knowledge snippet
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 获取现有片段 / Get existing snippet
        cursor.execute("SELECT * FROM snippets WHERE id = ?", (snippet_id,))
        row = cursor.fetchone()
        if not row:
            return None

        now = datetime.now().isoformat()
        new_title = title if title is not None else row["title"]
        new_content = content if content is not None else row["content"]
        new_source = source if source is not None else row["source"]

        try:
            cursor.execute(
                """
                UPDATE snippets
                SET title = ?, content = ?, source = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_title, new_content, new_source, now, snippet_id),
            )

            # 更新标签 / Update tags
            if tags is not None:
                # 移除旧标签关联 / Remove old tag associations
                old_tags = self._get_snippet_tags(snippet_id)
                for tag_name in old_tags:
                    tag = self._get_tag_by_name(tag_name)
                    if tag:
                        cursor.execute(
                            "DELETE FROM snippet_tags WHERE snippet_id = ? AND tag_id = ?",
                            (snippet_id, tag.id),
                        )
                        cursor.execute(
                            "UPDATE tags SET count = MAX(0, count - 1) WHERE id = ?",
                            (tag.id,),
                        )

                # 添加新标签关联 / Add new tag associations
                for tag_name in tags:
                    tag = self._get_or_create_tag(tag_name)
                    if tag:
                        cursor.execute(
                            "INSERT OR IGNORE INTO snippet_tags (snippet_id, tag_id) VALUES (?, ?)",
                            (snippet_id, tag.id),
                        )
                        cursor.execute(
                            "UPDATE tags SET count = count + 1 WHERE id = ?",
                            (tag.id,),
                        )

            conn.commit()

            snippet = KnowledgeSnippet(
                id=snippet_id,
                title=new_title,
                content=new_content,
                tags=tags if tags is not None else self._get_snippet_tags(snippet_id),
                source=new_source,
                created_at=row["created_at"],
                updated_at=now,
            )
            return snippet
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"更新知识片段失败: {e}")

    def delete_snippet(self, snippet_id: str) -> bool:
        """
        删除知识片段 / Delete knowledge snippet

        参数 / Args:
            snippet_id: 知识片段ID / Snippet ID

        返回 / Returns:
            是否成功删除 / Whether successfully deleted
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 先减少标签计数 / Decrease tag counts first
        old_tags = self._get_snippet_tags(snippet_id)
        for tag_name in old_tags:
            tag = self._get_tag_by_name(tag_name)
            if tag:
                cursor.execute(
                    "UPDATE tags SET count = MAX(0, count - 1) WHERE id = ?",
                    (tag.id,),
                )

        try:
            cursor.execute("DELETE FROM snippets WHERE id = ?", (snippet_id,))
            # 清理搜索索引 / Clear search index
            cursor.execute(
                "DELETE FROM search_index WHERE snippet_id = ?",
                (snippet_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"删除知识片段失败: {e}")

    def list_snippets(
        self,
        tag: Optional[str] = None,
        search_query: Optional[str] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[KnowledgeSnippet], int]:
        """
        列出知识片段 / List knowledge snippets

        参数 / Args:
            tag: 按标签过滤 / Filter by tag
            search_query: 搜索关键词 / Search keyword
            sort_by: 排序字段 / Sort field
            sort_order: 排序方向 / Sort order (asc/desc)
            offset: 偏移量 / Offset
            limit: 限制数量 / Limit

        返回 / Returns:
            (知识片段列表, 总数) / (List of snippets, total count)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 构建查询 / Build query
        conditions = []
        params: List[Any] = []

        if tag:
            conditions.append("""
                snippets.id IN (
                    SELECT snippet_id FROM snippet_tags
                    WHERE tag_id IN (SELECT id FROM tags WHERE name = ?)
                )
            """)
            params.append(tag)

        if search_query:
            conditions.append("""
                (snippets.title LIKE ? OR snippets.content LIKE ?)
            """)
            search_pattern = f"%{search_query}%"
            params.extend([search_pattern, search_pattern])

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # 验证排序字段 / Validate sort field
        valid_sort_fields = {"created_at", "updated_at", "title"}
        if sort_by not in valid_sort_fields:
            sort_by = "updated_at"
        if sort_order.lower() not in ("asc", "desc"):
            sort_order = "desc"

        # 获取总数 / Get total count
        count_sql = f"SELECT COUNT(*) as cnt FROM snippets {where_clause}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()["cnt"]

        # 获取数据 / Get data
        data_sql = f"""
            SELECT * FROM snippets {where_clause}
            ORDER BY {sort_by} {sort_order}
            LIMIT ? OFFSET ?
        """
        cursor.execute(data_sql, params + [limit, offset])
        rows = cursor.fetchall()

        snippets = []
        for row in rows:
            snippet = KnowledgeSnippet(
                id=row["id"],
                title=row["title"],
                content=row["content"],
                source=row["source"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            snippet.tags = self._get_snippet_tags(row["id"])
            snippets.append(snippet)

        return snippets, total

    def get_all_snippets(self) -> List[KnowledgeSnippet]:
        """
        获取所有知识片段 / Get all knowledge snippets

        返回 / Returns:
            所有知识片段列表 / List of all knowledge snippets
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM snippets ORDER BY updated_at DESC")
        rows = cursor.fetchall()

        snippets = []
        for row in rows:
            snippet = KnowledgeSnippet(
                id=row["id"],
                title=row["title"],
                content=row["content"],
                source=row["source"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            snippet.tags = self._get_snippet_tags(row["id"])
            snippets.append(snippet)

        return snippets

    def count_snippets(self) -> int:
        """
        获取知识片段总数 / Get total number of knowledge snippets

        返回 / Returns:
            知识片段总数 / Total number of snippets
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM snippets")
        return cursor.fetchone()["cnt"]

    # ============================================================
    # 标签管理 / Tag Management
    # ============================================================

    def _get_or_create_tag(self, name: str, color: str = "#3498db") -> Optional[Tag]:
        """
        获取或创建标签 / Get or create tag

        参数 / Args:
            name: 标签名称 / Tag name
            color: 标签颜色 / Tag color

        返回 / Returns:
            标签对象 / Tag object
        """
        existing = self._get_tag_by_name(name)
        if existing:
            return existing

        conn = self._get_connection()
        cursor = conn.cursor()

        tag = Tag(name=name, color=color)
        try:
            cursor.execute(
                "INSERT INTO tags (id, name, color, count) VALUES (?, ?, ?, 0)",
                (tag.id, tag.name, tag.color),
            )
            conn.commit()
            return tag
        except sqlite3.IntegrityError:
            # 并发创建，重新获取 / Concurrent creation, re-fetch
            return self._get_tag_by_name(name)

    def _get_tag_by_name(self, name: str) -> Optional[Tag]:
        """
        根据名称获取标签 / Get tag by name

        参数 / Args:
            name: 标签名称 / Tag name

        返回 / Returns:
            标签对象，如果不存在返回None / Tag object, None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tags WHERE name = ?", (name,))
        row = cursor.fetchone()

        if not row:
            return None

        return Tag(
            id=row["id"],
            name=row["name"],
            color=row["color"],
            count=row["count"],
        )

    def _get_snippet_tags(self, snippet_id: str) -> List[str]:
        """
        获取知识片段的标签名称列表 / Get tag names for a snippet

        参数 / Args:
            snippet_id: 知识片段ID / Snippet ID

        返回 / Returns:
            标签名称列表 / List of tag names
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT t.name FROM tags t
            INNER JOIN snippet_tags st ON t.id = st.tag_id
            WHERE st.snippet_id = ?
            ORDER BY t.name
            """,
            (snippet_id,),
        )
        return [row["name"] for row in cursor.fetchall()]

    def list_tags(self) -> List[Tag]:
        """
        列出所有标签 / List all tags

        返回 / Returns:
            标签列表 / List of tags
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tags ORDER BY count DESC, name ASC")
        return [
            Tag(
                id=row["id"],
                name=row["name"],
                color=row["color"],
                count=row["count"],
            )
            for row in cursor.fetchall()
        ]

    def delete_tag(self, tag_name: str) -> bool:
        """
        删除标签 / Delete tag

        参数 / Args:
            tag_name: 标签名称 / Tag name

        返回 / Returns:
            是否成功删除 / Whether successfully deleted
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        tag = self._get_tag_by_name(tag_name)
        if not tag:
            return False

        try:
            cursor.execute("DELETE FROM snippet_tags WHERE tag_id = ?", (tag.id,))
            cursor.execute("DELETE FROM tags WHERE id = ?", (tag.id,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"删除标签失败: {e}")

    # ============================================================
    # 工作流持久化 / Workflow Persistence
    # ============================================================

    def save_workflow(self, workflow: Workflow) -> Workflow:
        """
        保存工作流 / Save workflow

        参数 / Args:
            workflow: 工作流对象 / Workflow object

        返回 / Returns:
            保存后的工作流 / Saved workflow
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        nodes_json = json.dumps(
            [n.to_dict() for n in workflow.nodes], ensure_ascii=False
        )
        edges_json = json.dumps(
            [e.to_dict() for e in workflow.edges], ensure_ascii=False
        )

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO workflows
                (id, name, description, nodes_json, edges_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workflow.id,
                    workflow.name,
                    workflow.description,
                    nodes_json,
                    edges_json,
                    workflow.created_at,
                    workflow.updated_at,
                ),
            )
            conn.commit()
            return workflow
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"保存工作流失败: {e}")

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """
        根据ID获取工作流 / Get workflow by ID

        参数 / Args:
            workflow_id: 工作流ID / Workflow ID

        返回 / Returns:
            工作流对象，如果不存在返回None / Workflow object, None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_workflow(row)

    def get_workflow_by_name(self, name: str) -> Optional[Workflow]:
        """
        根据名称获取工作流 / Get workflow by name

        参数 / Args:
            name: 工作流名称 / Workflow name

        返回 / Returns:
            工作流对象，如果不存在返回None / Workflow object, None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM workflows WHERE name = ?", (name,))
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_workflow(row)

    def list_workflows(self) -> List[Workflow]:
        """
        列出所有工作流 / List all workflows

        返回 / Returns:
            工作流列表 / List of workflows
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM workflows ORDER BY updated_at DESC")
        return [self._row_to_workflow(row) for row in cursor.fetchall()]

    def delete_workflow(self, workflow_id: str) -> bool:
        """
        删除工作流 / Delete workflow

        参数 / Args:
            workflow_id: 工作流ID / Workflow ID

        返回 / Returns:
            是否成功删除 / Whether successfully deleted
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"删除工作流失败: {e}")

    def _row_to_workflow(self, row: sqlite3.Row) -> Workflow:
        """
        将数据库行转换为工作流对象 / Convert database row to workflow object

        参数 / Args:
            row: 数据库行 / Database row

        返回 / Returns:
            工作流对象 / Workflow object
        """
        try:
            nodes_data = json.loads(row["nodes_json"])
            nodes = [WorkflowNode.from_dict(n) for n in nodes_data]
        except (json.JSONDecodeError, TypeError):
            nodes = []

        try:
            edges_data = json.loads(row["edges_json"])
            edges = [WorkflowEdge.from_dict(e) for e in edges_data]
        except (json.JSONDecodeError, TypeError):
            edges = []

        return Workflow(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            nodes=nodes,
            edges=edges,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # ============================================================
    # 工作流执行日志 / Workflow Execution Logs
    # ============================================================

    def save_workflow_log(self, log_data: Dict[str, Any]) -> int:
        """
        保存工作流执行日志 / Save workflow execution log

        参数 / Args:
            log_data: 日志数据 / Log data

        返回 / Returns:
            日志ID / Log ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO workflow_logs
                (workflow_id, workflow_name, start_time, end_time, status, log_json, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log_data.get("workflow_id", ""),
                    log_data.get("workflow_name", ""),
                    log_data.get("start_time", ""),
                    log_data.get("end_time", ""),
                    log_data.get("status", "pending"),
                    json.dumps(log_data, ensure_ascii=False),
                    log_data.get("error_message", ""),
                ),
            )
            conn.commit()
            return cursor.lastrowid  # type: ignore
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"保存工作流日志失败: {e}")

    def list_workflow_logs(
        self, workflow_id: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        列出工作流执行日志 / List workflow execution logs

        参数 / Args:
            workflow_id: 工作流ID（可选） / Workflow ID (optional)
            limit: 限制数量 / Limit

        返回 / Returns:
            日志列表 / List of logs
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if workflow_id:
            cursor.execute(
                """
                SELECT * FROM workflow_logs
                WHERE workflow_id = ?
                ORDER BY id DESC LIMIT ?
                """,
                (workflow_id, limit),
            )
        else:
            cursor.execute(
                "SELECT * FROM workflow_logs ORDER BY id DESC LIMIT ?",
                (limit,),
            )

        logs = []
        for row in cursor.fetchall():
            try:
                log_detail = json.loads(row["log_json"])
            except (json.JSONDecodeError, TypeError):
                log_detail = {}

            logs.append({
                "id": row["id"],
                "workflow_id": row["workflow_id"],
                "workflow_name": row["workflow_name"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "status": row["status"],
                "error_message": row["error_message"],
                "detail": log_detail,
            })

        return logs

    # ============================================================
    # 搜索索引 / Search Index
    # ============================================================

    def update_search_index(self, snippet_id: str, terms: Dict[str, int]) -> None:
        """
        更新搜索索引 / Update search index

        参数 / Args:
            snippet_id: 知识片段ID / Snippet ID
            terms: 术语-频率字典 / Term-frequency dictionary
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 清除旧索引 / Clear old index
            cursor.execute(
                "DELETE FROM search_index WHERE snippet_id = ?",
                (snippet_id,),
            )

            # 插入新索引 / Insert new index
            for term, frequency in terms.items():
                if term.strip():
                    cursor.execute(
                        "INSERT INTO search_index (snippet_id, term, frequency) VALUES (?, ?, ?)",
                        (snippet_id, term.lower(), frequency),
                    )

            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"更新搜索索引失败: {e}")

    def get_search_index(self) -> Dict[str, Dict[str, int]]:
        """
        获取完整搜索索引 / Get full search index

        返回 / Returns:
            {snippet_id: {term: frequency}} / {snippet_id: {term: frequency}}
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT snippet_id, term, frequency FROM search_index")
        index: Dict[str, Dict[str, int]] = {}

        for row in cursor.fetchall():
            sid = row["snippet_id"]
            if sid not in index:
                index[sid] = {}
            index[sid][row["term"]] = row["frequency"]

        return index

    def rebuild_search_index(self) -> int:
        """
        重建搜索索引 / Rebuild search index

        返回 / Returns:
            索引的文档数量 / Number of indexed documents
        """
        from .search_engine import SearchEngine

        snippets = self.get_all_snippets()
        engine = SearchEngine()

        for snippet in snippets:
            terms = engine.tokenize_and_count(snippet.title + " " + snippet.content)
            self.update_search_index(snippet.id, terms)

        return len(snippets)

    # ============================================================
    # 统计信息 / Statistics
    # ============================================================

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据库统计信息 / Get database statistics

        返回 / Returns:
            统计信息字典 / Statistics dictionary
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        stats: Dict[str, Any] = {}

        # 知识片段统计 / Snippet statistics
        cursor.execute("SELECT COUNT(*) as cnt FROM snippets")
        stats["total_snippets"] = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM tags")
        stats["total_tags"] = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM workflows")
        stats["total_workflows"] = cursor.fetchone()["cnt"]

        # 最近活动 / Recent activity
        cursor.execute(
            "SELECT updated_at FROM snippets ORDER BY updated_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        stats["last_updated"] = row["updated_at"] if row else None

        # 标签使用统计 / Tag usage statistics
        cursor.execute(
            "SELECT name, count FROM tags ORDER BY count DESC LIMIT 10"
        )
        stats["top_tags"] = [
            {"name": r["name"], "count": r["count"]} for r in cursor.fetchall()
        ]

        # 数据库文件大小 / Database file size
        try:
            db_file = Path(self.db_path)
            stats["db_size"] = db_file.stat().st_size if db_file.exists() else 0
        except OSError:
            stats["db_size"] = 0

        return stats
