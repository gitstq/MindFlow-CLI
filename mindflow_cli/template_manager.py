"""
模板管理模块 / Template Manager Module

管理预设模板和自定义模板，支持模板变量替换。
Manages preset and custom templates with variable substitution support.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import Workflow, WorkflowEdge, WorkflowNode, NodeType


class Template:
    """
    模板模型 / Template Model

    定义一个工作流模板，包含元数据和工作流定义。
    Defines a workflow template with metadata and workflow definition.

    属性 / Attributes:
        name: 模板名称 / Template name
        description: 描述 / Description
        category: 分类 / Category
        variables: 模板变量定义 / Template variable definitions
        workflow: 工作流定义 / Workflow definition
        is_builtin: 是否为内置模板 / Whether it's a built-in template
    """

    def __init__(
        self,
        name: str = "",
        description: str = "",
        category: str = "general",
        variables: Optional[List[Dict[str, Any]]] = None,
        workflow: Optional[Dict[str, Any]] = None,
        is_builtin: bool = False,
    ) -> None:
        self.name = name
        self.description = description
        self.category = category
        self.variables = variables or []
        self.workflow = workflow or {}
        self.is_builtin = is_builtin

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "variables": self.variables,
            "workflow": self.workflow,
            "is_builtin": self.is_builtin,
        }

    def to_json(self) -> str:
        """转换为JSON / Convert to JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Template:
        """从字典创建 / Create from dictionary"""
        return cls(**data)


class TemplateManager:
    """
    模板管理器 / Template Manager

    管理预设模板和自定义模板的加载、保存和应用。
    Manages loading, saving, and applying preset and custom templates.

    用法 / Usage:
        manager = TemplateManager(templates_dir="/path/to/templates")
        templates = manager.list_templates()
        workflow = manager.apply("research_summary", {"topic": "AI"})
    """

    def __init__(self, templates_dir: Optional[str] = None) -> None:
        """
        初始化模板管理器 / Initialize template manager

        参数 / Args:
            templates_dir: 自定义模板目录 / Custom templates directory
        """
        self.templates_dir = Path(templates_dir) if templates_dir else Path(".")
        self._builtin_templates: Dict[str, Template] = {}
        self._custom_templates: Dict[str, Template] = {}
        self._load_builtin_templates()
        self._load_custom_templates()

    def _load_builtin_templates(self) -> None:
        """加载内置模板 / Load built-in templates"""
        self._builtin_templates = {
            "research_summary": Template(
                name="研究整理",
                description="自动整理研究资料，提取关键信息并生成摘要",
                category="research",
                variables=[
                    {
                        "name": "topic",
                        "label": "研究主题",
                        "type": "text",
                        "required": True,
                        "default": "",
                    },
                    {
                        "name": "depth",
                        "label": "分析深度",
                        "type": "select",
                        "options": ["浅层", "中层", "深层"],
                        "default": "中层",
                    },
                ],
                workflow={
                    "name": "研究整理工作流",
                    "description": "搜索、分析和整理研究资料",
                    "nodes": [
                        {
                            "id": "node_search",
                            "type": "input",
                            "name": "搜索输入",
                            "config": {
                                "input_type": "query",
                                "context_key": "search_results",
                            },
                            "position": {"x": 0, "y": 0},
                        },
                        {
                            "id": "node_extract",
                            "type": "transform",
                            "name": "提取关键信息",
                            "config": {
                                "transform_type": "text",
                                "operations": [
                                    {"type": "template",
                                     "value": "研究主题: {{topic}}\n分析深度: {{depth}}\n\n相关资料:\n{{input}}"},
                                ],
                            },
                            "position": {"x": 300, "y": 0},
                        },
                        {
                            "id": "node_summarize",
                            "type": "llm",
                            "name": "AI摘要生成",
                            "config": {
                                "prompt": "请根据以下研究资料，生成一份结构化的研究摘要。包括：\n1. 核心观点\n2. 关键发现\n3. 结论与建议\n\n资料内容：\n{{input}}",
                                "system_prompt": "你是一位专业的研究分析师，擅长从大量资料中提取关键信息并生成结构化摘要。",
                            },
                            "position": {"x": 600, "y": 0},
                        },
                        {
                            "id": "node_export",
                            "type": "export",
                            "name": "导出结果",
                            "config": {
                                "format": "markdown",
                            },
                            "position": {"x": 900, "y": 0},
                        },
                    ],
                    "edges": [
                        {"source_id": "node_search", "target_id": "node_extract"},
                        {"source_id": "node_extract", "target_id": "node_summarize"},
                        {"source_id": "node_summarize", "target_id": "node_export"},
                    ],
                },
                is_builtin=True,
            ),
            "meeting_notes": Template(
                name="会议纪要",
                description="将会议记录整理为结构化的会议纪要",
                category="office",
                variables=[
                    {
                        "name": "meeting_title",
                        "label": "会议标题",
                        "type": "text",
                        "required": True,
                        "default": "",
                    },
                    {
                        "name": "participants",
                        "label": "参会人员",
                        "type": "text",
                        "required": False,
                        "default": "",
                    },
                ],
                workflow={
                    "name": "会议纪要工作流",
                    "description": "整理会议记录并生成结构化纪要",
                    "nodes": [
                        {
                            "id": "node_input",
                            "type": "input",
                            "name": "会议记录输入",
                            "config": {"input_type": "static"},
                            "position": {"x": 0, "y": 0},
                        },
                        {
                            "id": "node_format",
                            "type": "transform",
                            "name": "格式化",
                            "config": {
                                "transform_type": "text",
                                "operations": [
                                    {"type": "prefix",
                                     "value": "会议标题: {{meeting_title}}\n参会人员: {{participants}}\n日期: {{date}}\n\n"},
                                ],
                            },
                            "position": {"x": 300, "y": 0},
                        },
                        {
                            "id": "node_process",
                            "type": "llm",
                            "name": "AI整理纪要",
                            "config": {
                                "prompt": "请将以下会议记录整理为结构化的会议纪要，包括：\n1. 会议议题\n2. 讨论要点\n3. 决议事项\n4. 后续行动项（含负责人和截止日期）\n\n会议记录：\n{{input}}",
                                "system_prompt": "你是一位专业的会议秘书，擅长从会议记录中提取关键信息并生成清晰的会议纪要。",
                            },
                            "position": {"x": 600, "y": 0},
                        },
                        {
                            "id": "node_output",
                            "type": "export",
                            "name": "导出纪要",
                            "config": {"format": "markdown"},
                            "position": {"x": 900, "y": 0},
                        },
                    ],
                    "edges": [
                        {"source_id": "node_input", "target_id": "node_format"},
                        {"source_id": "node_format", "target_id": "node_process"},
                        {"source_id": "node_process", "target_id": "node_output"},
                    ],
                },
                is_builtin=True,
            ),
            "study_notes": Template(
                name="学习笔记",
                description="整理学习内容，生成结构化笔记和知识卡片",
                category="learning",
                variables=[
                    {
                        "name": "subject",
                        "label": "学习科目",
                        "type": "text",
                        "required": True,
                        "default": "",
                    },
                    {
                        "name": "note_style",
                        "label": "笔记风格",
                        "type": "select",
                        "options": ["康奈尔笔记法", "思维导图大纲", "费曼学习法"],
                        "default": "康奈尔笔记法",
                    },
                ],
                workflow={
                    "name": "学习笔记工作流",
                    "description": "整理学习内容并生成结构化笔记",
                    "nodes": [
                        {
                            "id": "node_input",
                            "type": "input",
                            "name": "学习内容输入",
                            "config": {"input_type": "static"},
                            "position": {"x": 0, "y": 0},
                        },
                        {
                            "id": "node_organize",
                            "type": "llm",
                            "name": "AI整理笔记",
                            "config": {
                                "prompt": "请使用{{note_style}}将以下学习内容整理为结构化笔记。\n\n学习科目: {{subject}}\n\n学习内容:\n{{input}}",
                                "system_prompt": "你是一位专业的学习顾问，擅长使用各种笔记方法帮助学生整理和巩固知识。",
                            },
                            "position": {"x": 300, "y": 0},
                        },
                        {
                            "id": "node_cards",
                            "type": "llm",
                            "name": "生成知识卡片",
                            "config": {
                                "prompt": "根据以下笔记内容，生成5-10张知识卡片（问答形式），用于复习和记忆。\n\n笔记内容:\n{{input}}",
                                "system_prompt": "你是一位知识管理专家，擅长创建简洁有效的知识卡片。",
                            },
                            "position": {"x": 600, "y": 0},
                        },
                        {
                            "id": "node_export",
                            "type": "export",
                            "name": "导出笔记",
                            "config": {"format": "markdown"},
                            "position": {"x": 900, "y": 0},
                        },
                    ],
                    "edges": [
                        {"source_id": "node_input", "target_id": "node_organize"},
                        {"source_id": "node_organize", "target_id": "node_cards"},
                        {"source_id": "node_cards", "target_id": "node_export"},
                    ],
                },
                is_builtin=True,
            ),
            "project_doc": Template(
                name="项目文档",
                description="从项目信息生成完整的项目文档",
                category="development",
                variables=[
                    {
                        "name": "project_name",
                        "label": "项目名称",
                        "type": "text",
                        "required": True,
                        "default": "",
                    },
                    {
                        "name": "doc_type",
                        "label": "文档类型",
                        "type": "select",
                        "options": ["README", "API文档", "设计文档", "用户手册"],
                        "default": "README",
                    },
                ],
                workflow={
                    "name": "项目文档工作流",
                    "description": "生成项目文档",
                    "nodes": [
                        {
                            "id": "node_input",
                            "type": "input",
                            "name": "项目信息输入",
                            "config": {"input_type": "static"},
                            "position": {"x": 0, "y": 0},
                        },
                        {
                            "id": "node_generate",
                            "type": "llm",
                            "name": "AI生成文档",
                            "config": {
                                "prompt": "请根据以下项目信息，生成一份{{doc_type}}文档。\n\n项目名称: {{project_name}}\n\n项目信息:\n{{input}}",
                                "system_prompt": "你是一位技术文档专家，擅长编写清晰、专业的项目文档。",
                            },
                            "position": {"x": 300, "y": 0},
                        },
                        {
                            "id": "node_export",
                            "type": "export",
                            "name": "导出文档",
                            "config": {"format": "markdown"},
                            "position": {"x": 600, "y": 0},
                        },
                    ],
                    "edges": [
                        {"source_id": "node_input", "target_id": "node_generate"},
                        {"source_id": "node_generate", "target_id": "node_export"},
                    ],
                },
                is_builtin=True,
            ),
            "content_rewrite": Template(
                name="内容改写",
                description="对文本内容进行改写、润色和风格转换",
                category="writing",
                variables=[
                    {
                        "name": "style",
                        "label": "目标风格",
                        "type": "select",
                        "options": ["正式", "口语化", "学术", "简洁", "详细"],
                        "default": "正式",
                    },
                    {
                        "name": "language",
                        "label": "目标语言",
                        "type": "select",
                        "options": ["保持原文", "中文", "英文"],
                        "default": "保持原文",
                    },
                ],
                workflow={
                    "name": "内容改写工作流",
                    "description": "改写和润色文本内容",
                    "nodes": [
                        {
                            "id": "node_input",
                            "type": "input",
                            "name": "原文输入",
                            "config": {"input_type": "static"},
                            "position": {"x": 0, "y": 0},
                        },
                        {
                            "id": "node_rewrite",
                            "type": "llm",
                            "name": "AI改写",
                            "config": {
                                "prompt": "请将以下内容改写为{{style}}风格。{{language_note}}\n\n原文:\n{{input}}",
                                "system_prompt": "你是一位专业的文字编辑，擅长在不同风格之间转换文本。",
                            },
                            "position": {"x": 300, "y": 0},
                        },
                        {
                            "id": "node_export",
                            "type": "export",
                            "name": "导出结果",
                            "config": {"format": "text"},
                            "position": {"x": 600, "y": 0},
                        },
                    ],
                    "edges": [
                        {"source_id": "node_input", "target_id": "node_rewrite"},
                        {"source_id": "node_rewrite", "target_id": "node_export"},
                    ],
                },
                is_builtin=True,
            ),
            "knowledge_qa": Template(
                name="知识问答",
                description="基于知识库内容回答问题",
                category="knowledge",
                variables=[
                    {
                        "name": "question",
                        "label": "问题",
                        "type": "text",
                        "required": True,
                        "default": "",
                    },
                ],
                workflow={
                    "name": "知识问答工作流",
                    "description": "从知识库搜索相关内容并回答问题",
                    "nodes": [
                        {
                            "id": "node_input",
                            "type": "input",
                            "name": "问题输入",
                            "config": {"input_type": "static"},
                            "position": {"x": 0, "y": 0},
                        },
                        {
                            "id": "node_search",
                            "type": "input",
                            "name": "知识库搜索",
                            "config": {"input_type": "query"},
                            "position": {"x": 0, "y": 100},
                        },
                        {
                            "id": "node_merge",
                            "type": "merge",
                            "name": "合并上下文",
                            "config": {"merge_type": "concat"},
                            "position": {"x": 300, "y": 50},
                        },
                        {
                            "id": "node_answer",
                            "type": "llm",
                            "name": "AI回答",
                            "config": {
                                "prompt": "请根据以下参考资料回答问题。如果参考资料中没有相关信息，请说明。\n\n问题: {{question}}\n\n参考资料:\n{{input}}",
                                "system_prompt": "你是一位知识渊博的助手，擅长基于提供的参考资料准确回答问题。如果参考资料不足，请如实说明。",
                            },
                            "position": {"x": 600, "y": 50},
                        },
                    ],
                    "edges": [
                        {"source_id": "node_input", "target_id": "node_merge"},
                        {"source_id": "node_search", "target_id": "node_merge"},
                        {"source_id": "node_merge", "target_id": "node_answer"},
                    ],
                },
                is_builtin=True,
            ),
        }

    def _load_custom_templates(self) -> None:
        """加载自定义模板 / Load custom templates"""
        if not self.templates_dir.exists():
            return

        for file_path in self.templates_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                template = Template.from_dict(data)
                template.is_builtin = False
                self._custom_templates[template.name] = template
            except (json.JSONDecodeError, IOError, KeyError) as e:
                print(f"警告: 加载模板文件 {file_path} 失败: {e}")

    def list_templates(
        self,
        category: Optional[str] = None,
        include_builtin: bool = True,
    ) -> List[Template]:
        """
        列出模板 / List templates

        参数 / Args:
            category: 按分类过滤 / Filter by category
            include_builtin: 是否包含内置模板 / Whether to include built-in templates

        返回 / Returns:
            模板列表 / List of templates
        """
        templates: List[Template] = []

        if include_builtin:
            templates.extend(self._builtin_templates.values())

        templates.extend(self._custom_templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        return sorted(templates, key=lambda t: (not t.is_builtin, t.name))

    def get_template(self, name: str) -> Optional[Template]:
        """
        获取模板 / Get template

        参数 / Args:
            name: 模板名称 / Template name

        返回 / Returns:
            模板对象，如果不存在返回None / Template object, None if not found
        """
        if name in self._builtin_templates:
            return self._builtin_templates[name]
        if name in self._custom_templates:
            return self._custom_templates[name]
        return None

    def apply(
        self,
        template_name: str,
        variables: Optional[Dict[str, str]] = None,
    ) -> Workflow:
        """
        应用模板创建工作流 / Apply template to create workflow

        参数 / Args:
            template_name: 模板名称 / Template name
            variables: 模板变量值 / Template variable values

        返回 / Returns:
            工作流对象 / Workflow object

        异常 / Raises:
            ValueError: 模板不存在 / Template doesn't exist
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"模板 '{template_name}' 不存在")

        variables = variables or {}
        workflow_data = template.workflow

        # 替换模板变量 / Replace template variables
        self._replace_variables(workflow_data, variables)

        # 构建工作流对象 / Build workflow object
        nodes = []
        for node_data in workflow_data.get("nodes", []):
            node = WorkflowNode.from_dict(node_data)
            nodes.append(node)

        edges = []
        for edge_data in workflow_data.get("edges", []):
            edge = WorkflowEdge.from_dict(edge_data)
            edges.append(edge)

        workflow = Workflow(
            name=workflow_data.get("name", template.name),
            description=workflow_data.get("description", template.description),
            nodes=nodes,
            edges=edges,
        )

        return workflow

    def _replace_variables(
        self, data: Any, variables: Dict[str, str]
    ) -> None:
        """
        递归替换数据中的模板变量 / Recursively replace template variables in data

        参数 / Args:
            data: 数据（字典、列表或字符串） / Data (dict, list, or string)
            variables: 变量映射 / Variable mapping
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = self._replace_string_variables(value, variables)
                elif isinstance(value, (dict, list)):
                    self._replace_variables(value, variables)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, str):
                    data[i] = self._replace_string_variables(item, variables)
                elif isinstance(item, (dict, list)):
                    self._replace_variables(item, variables)

    def _replace_string_variables(
        self, text: str, variables: Dict[str, str]
    ) -> str:
        """
        替换字符串中的模板变量 / Replace template variables in string

        参数 / Args:
            text: 原始文本 / Original text
            variables: 变量映射 / Variable mapping

        返回 / Returns:
            替换后的文本 / Replaced text
        """
        # 添加日期变量 / Add date variable
        all_vars = dict(variables)
        all_vars.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
        all_vars.setdefault("datetime", datetime.now().strftime("%Y-%m-%d %H:%M"))

        for key, value in all_vars.items():
            text = text.replace(f"{{{{{key}}}}}", str(value))

        return text

    def save_custom_template(
        self,
        name: str,
        description: str,
        category: str,
        workflow_data: Dict[str, Any],
        variables: Optional[List[Dict[str, Any]]] = None,
    ) -> Template:
        """
        保存自定义模板 / Save custom template

        参数 / Args:
            name: 模板名称 / Template name
            description: 描述 / Description
            category: 分类 / Category
            workflow_data: 工作流数据 / Workflow data
            variables: 变量定义 / Variable definitions

        返回 / Returns:
            保存的模板 / Saved template
        """
        template = Template(
            name=name,
            description=description,
            category=category,
            variables=variables or [],
            workflow=workflow_data,
            is_builtin=False,
        )

        self._custom_templates[name] = template

        # 保存到文件 / Save to file
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.templates_dir / f"{name}.json"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise RuntimeError(f"保存模板失败: {e}")

        return template

    def delete_custom_template(self, name: str) -> bool:
        """
        删除自定义模板 / Delete custom template

        参数 / Args:
            name: 模板名称 / Template name

        返回 / Returns:
            是否成功删除 / Whether successfully deleted
        """
        template = self._custom_templates.get(name)
        if not template:
            return False

        file_path = self.templates_dir / f"{name}.json"
        if file_path.exists():
            try:
                file_path.unlink()
            except IOError:
                pass

        del self._custom_templates[name]
        return True

    def get_categories(self) -> List[str]:
        """
        获取所有模板分类 / Get all template categories

        返回 / Returns:
            分类列表 / List of categories
        """
        all_templates = list(self._builtin_templates.values()) + list(self._custom_templates.values())
        categories = sorted(set(t.category for t in all_templates))
        return categories

    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        获取模板详细信息 / Get template detailed information

        参数 / Args:
            template_name: 模板名称 / Template name

        返回 / Returns:
            模板信息字典 / Template info dictionary
        """
        template = self.get_template(template_name)
        if not template:
            return None

        return {
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "is_builtin": template.is_builtin,
            "variables": template.variables,
            "node_count": len(template.workflow.get("nodes", [])),
            "edge_count": len(template.workflow.get("edges", [])),
        }
