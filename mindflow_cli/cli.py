"""
命令行接口模块 / Command Line Interface Module

使用argparse实现MindFlow-CLI的所有命令行功能。
Implements all MindFlow-CLI command-line functionality using argparse.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import __version__
from .config import Config
from .exporter import Exporter
from .llm_client import LLMClient
from .models import KnowledgeSnippet, Workflow, WorkflowEdge, WorkflowNode, NodeType
from .search_engine import SearchEngine
from .storage import Storage
from .template_manager import TemplateManager
from .utils import (
    Colors,
    ProgressBar,
    bold,
    colored,
    dim,
    error,
    format_datetime,
    format_file_size,
    info,
    paginate,
    print_error,
    print_info,
    print_success,
    print_table,
    print_warning,
    prompt_choice,
    prompt_confirm,
    prompt_input,
    success,
    truncate_text,
    warning,
)


class MindFlowCLI:
    """
    MindFlow命令行接口 / MindFlow Command Line Interface

    主CLI类，负责解析命令行参数并执行相应的操作。
    Main CLI class responsible for parsing command-line arguments
    and executing corresponding operations.
    """

    def __init__(self) -> None:
        """初始化CLI / Initialize CLI"""
        self.config = Config()
        self.storage: Optional[Storage] = None
        self.search_engine: Optional[SearchEngine] = None
        self.llm_client: Optional[LLMClient] = None
        self.template_manager: Optional[TemplateManager] = None
        self.exporter = Exporter()

    def _ensure_initialized(self) -> bool:
        """
        确保项目已初始化 / Ensure project is initialized

        返回 / Returns:
            是否已初始化 / Whether initialized
        """
        if not self.config.is_initialized():
            print_error("项目未初始化，请先运行 'mindflow init'")
            return False

        self.storage = Storage(str(self.config.database_path))
        self.storage.initialize()

        # 初始化搜索引擎 / Initialize search engine
        search_config = self.config.get_search_config()
        self.search_engine = SearchEngine(
            algorithm=search_config.get("algorithm", "bm25"),
            chinese_ngram_size=search_config.get("chinese_ngram_size", 2),
        )
        snippets = self.storage.get_all_snippets()
        self.search_engine.add_snippets(snippets)

        # 初始化LLM客户端 / Initialize LLM client
        self.llm_client = LLMClient(
            default_provider=self.config.get_llm_provider(),
        )
        for provider in ("openai", "anthropic", "ollama"):
            provider_config = self.config.get_llm_config(provider)
            if provider_config.get("api_key") or provider == "ollama":
                self.llm_client.configure(provider, **provider_config)

        # 初始化模板管理器 / Initialize template manager
        self.template_manager = TemplateManager(
            str(self.config.templates_dir)
        )

        return True

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        运行CLI / Run CLI

        参数 / Args:
            args: 命令行参数（可选，默认使用sys.argv） / CLI args (optional)

        返回 / Returns:
            退出码 / Exit code
        """
        parser = self._build_parser()
        parsed = parser.parse_args(args)

        if parsed.version:
            print(f"MindFlow-CLI v{__version__}")
            return 0

        if not hasattr(parsed, "func"):
            parser.print_help()
            return 0

        try:
            return parsed.func(parsed)
        except KeyboardInterrupt:
            print(f"\n{warning('操作已取消')}")
            return 130
        except Exception as e:
            print_error(f"发生错误: {e}")
            if self.config.get("general.log_level", "INFO") == "DEBUG":
                import traceback
                traceback.print_exc()
            return 1

    def _build_parser(self) -> argparse.ArgumentParser:
        """
        构建命令行参数解析器 / Build command-line argument parser

        返回 / Returns:
            ArgumentParser实例 / ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            prog="mindflow",
            description="MindFlow-CLI - 轻量级AI知识工作流自动化引擎",
            epilog="使用 'mindflow <command> --help' 查看子命令帮助",
        )
        parser.add_argument(
            "-v", "--version",
            action="store_true",
            dest="version",
            help="显示版本号 / Show version",
        )

        subparsers = parser.add_subparsers(dest="command", help="可用命令 / Available commands")

        # init 命令 / init command
        init_parser = subparsers.add_parser("init", help="初始化项目 / Initialize project")
        init_parser.set_defaults(func=self._cmd_init)

        # add 命令 / add command
        add_parser = subparsers.add_parser("add", help="添加知识片段 / Add knowledge snippet")
        add_parser.add_argument("-t", "--title", help="标题 / Title")
        add_parser.add_argument("-c", "--content", help="内容 / Content")
        add_parser.add_argument("--tags", help="标签（逗号分隔） / Tags (comma-separated)")
        add_parser.add_argument("-s", "--source", help="来源 / Source")
        add_parser.add_argument("-f", "--file", help="从文件读取内容 / Read content from file")
        add_parser.set_defaults(func=self._cmd_add)

        # list 命令 / list command
        list_parser = subparsers.add_parser("list", help="列出知识片段 / List knowledge snippets")
        list_parser.add_argument("--tag", help="按标签过滤 / Filter by tag")
        list_parser.add_argument("--sort", default="updated_at", help="排序字段 / Sort field")
        list_parser.add_argument("--order", default="desc", choices=["asc", "desc"], help="排序方向 / Sort order")
        list_parser.add_argument("-p", "--page", type=int, default=1, help="页码 / Page number")
        list_parser.add_argument("--per-page", type=int, default=10, help="每页数量 / Items per page")
        list_parser.add_argument("--all", action="store_true", help="显示全部 / Show all")
        list_parser.set_defaults(func=self._cmd_list)

        # search 命令 / search command
        search_parser = subparsers.add_parser("search", help="搜索知识片段 / Search knowledge snippets")
        search_parser.add_argument("query", help="搜索关键词 / Search query")
        search_parser.add_argument("-n", "--max", type=int, default=10, help="最大结果数 / Max results")
        search_parser.set_defaults(func=self._cmd_search)

        # show 命令 / show command
        show_parser = subparsers.add_parser("show", help="显示知识片段详情 / Show snippet detail")
        show_parser.add_argument("id", help="知识片段ID / Snippet ID")
        show_parser.set_defaults(func=self._cmd_show)

        # delete 命令 / delete command
        delete_parser = subparsers.add_parser("delete", help="删除知识片段 / Delete knowledge snippet")
        delete_parser.add_argument("id", help="知识片段ID / Snippet ID")
        delete_parser.add_argument("-y", "--yes", action="store_true", help="跳过确认 / Skip confirmation")
        delete_parser.set_defaults(func=self._cmd_delete)

        # tags 命令 / tags command
        tags_parser = subparsers.add_parser("tags", help="管理标签 / Manage tags")
        tags_parser.set_defaults(func=self._cmd_tags)

        # workflow 子命令 / workflow subcommands
        wf_parser = subparsers.add_parser("workflow", help="工作流管理 / Workflow management")
        wf_subparsers = wf_parser.add_subparsers(dest="wf_command")

        # workflow run
        wf_run = wf_subparsers.add_parser("run", help="执行工作流 / Run workflow")
        wf_run.add_argument("name", help="工作流名称 / Workflow name")
        wf_run.add_argument("--input", help="输入数据 / Input data")
        wf_run.set_defaults(func=self._cmd_workflow_run)

        # workflow list
        wf_list = wf_subparsers.add_parser("list", help="列出工作流 / List workflows")
        wf_list.set_defaults(func=self._cmd_workflow_list)

        # workflow create
        wf_create = wf_subparsers.add_parser("create", help="创建工作流 / Create workflow")
        wf_create.set_defaults(func=self._cmd_workflow_create)

        # workflow show
        wf_show = wf_subparsers.add_parser("show", help="显示工作流详情 / Show workflow detail")
        wf_show.add_argument("name", help="工作流名称 / Workflow name")
        wf_show.set_defaults(func=self._cmd_workflow_show)

        # workflow delete
        wf_del = wf_subparsers.add_parser("delete", help="删除工作流 / Delete workflow")
        wf_del.add_argument("name", help="工作流名称 / Workflow name")
        wf_del.add_argument("-y", "--yes", action="store_true", help="跳过确认 / Skip confirmation")
        wf_del.set_defaults(func=self._cmd_workflow_delete)

        # template 子命令 / template subcommands
        tpl_parser = subparsers.add_parser("template", help="模板管理 / Template management")
        tpl_subparsers = tpl_parser.add_subparsers(dest="tpl_command")

        # template list
        tpl_list = tpl_subparsers.add_parser("list", help="列出模板 / List templates")
        tpl_list.set_defaults(func=self._cmd_template_list)

        # template apply
        tpl_apply = tpl_subparsers.add_parser("apply", help="应用模板 / Apply template")
        tpl_apply.add_argument("name", help="模板名称 / Template name")
        tpl_apply.set_defaults(func=self._cmd_template_apply)

        # template info
        tpl_info = tpl_subparsers.add_parser("info", help="查看模板详情 / View template detail")
        tpl_info.add_argument("name", help="模板名称 / Template name")
        tpl_info.set_defaults(func=self._cmd_template_info)

        # export 命令 / export command
        export_parser = subparsers.add_parser("export", help="导出知识库 / Export knowledge base")
        export_parser.add_argument("format", choices=["json", "markdown", "html"], help="导出格式 / Export format")
        export_parser.add_argument("-o", "--output", help="输出文件路径 / Output file path")
        export_parser.set_defaults(func=self._cmd_export)

        # config 命令 / config command
        config_parser = subparsers.add_parser("config", help="配置管理 / Configuration management")
        config_parser.add_argument("--set", dest="set_key", help="设置配置项 / Set config key")
        config_parser.add_argument("--get", dest="get_key", help="获取配置项 / Get config key")
        config_parser.add_argument("--list", action="store_true", dest="list_all", help="列出所有配置 / List all config")
        config_parser.set_defaults(func=self._cmd_config)

        # tui 命令 / tui command
        tui_parser = subparsers.add_parser("tui", help="启动TUI界面 / Launch TUI interface")
        tui_parser.set_defaults(func=self._cmd_tui)

        # stats 命令 / stats command
        stats_parser = subparsers.add_parser("stats", help="显示统计信息 / Show statistics")
        stats_parser.set_defaults(func=self._cmd_stats)

        return parser

    # ============================================================
    # 命令实现 / Command Implementations
    # ============================================================

    def _cmd_init(self, args: argparse.Namespace) -> int:
        """初始化项目 / Initialize project"""
        print(f"\n  {bold('MindFlow-CLI 项目初始化')}")
        print(f"  {'─' * 40}\n")

        self.config.initialize()
        self.storage = Storage(str(self.config.database_path))
        self.storage.initialize()

        print_success("配置目录已创建")
        print(f"    路径: {self.config.config_dir}")
        print_success("数据库已创建")
        print(f"    路径: {self.config.database_path}")
        print_success("导出目录已创建")
        print(f"    路径: {self.config.exports_dir}")
        print_success("模板目录已创建")
        print(f"    路径: {self.config.templates_dir}")

        print(f"\n  {success('初始化完成!')} 开始使用 MindFlow-CLI:\n")
        print(f"    {info('mindflow add')}       添加知识片段")
        print(f"    {info('mindflow search')}    搜索知识片段")
        print(f"    {info('mindflow tui')}       启动交互界面")
        print(f"    {info('mindflow config')}    配置LLM API\n")

        return 0

    def _cmd_add(self, args: argparse.Namespace) -> int:
        """添加知识片段 / Add knowledge snippet"""
        if not self._ensure_initialized():
            return 1

        print(f"\n  {bold('添加知识片段')}")
        print(f"  {'─' * 40}\n")

        # 获取标题 / Get title
        title = args.title or prompt_input("标题", required=True)

        # 获取内容 / Get content
        content = ""
        if args.file:
            try:
                with open(args.file, "r", encoding="utf-8") as f:
                    content = f.read()
                print_success(f"已从文件读取内容: {args.file}")
            except IOError as e:
                print_error(f"无法读取文件: {e}")
                return 1
        elif args.content:
            content = args.content
        else:
            print(f"  {dim('输入内容（输入空行结束）:')}")
            lines = []
            while True:
                try:
                    line = input("  > ")
                    if line == "":
                        break
                    lines.append(line)
                except EOFError:
                    break
            content = "\n".join(lines)

        if not content.strip():
            print_error("内容不能为空")
            return 1

        # 获取标签 / Get tags
        tags: List[str] = []
        if args.tags:
            tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        else:
            tags_str = prompt_input("标签（逗号分隔）")
            if tags_str:
                tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        # 获取来源 / Get source
        source = args.source or prompt_input("来源")

        # 保存 / Save
        snippet = self.storage.create_snippet(
            title=title,
            content=content,
            tags=tags,
            source=source,
        )

        print_success(f"知识片段已添加")
        print(f"    ID: {snippet.id[:8]}...")
        print(f"    标题: {snippet.title}")
        if snippet.tags:
            print(f"    标签: {', '.join(snippet.tags)}")

        return 0

    def _cmd_list(self, args: argparse.Namespace) -> int:
        """列出知识片段 / List knowledge snippets"""
        if not self._ensure_initialized():
            return 1

        snippets, total = self.storage.list_snippets(
            tag=args.tag,
            sort_by=args.sort,
            sort_order=args.order,
            offset=0 if args.all else (args.page - 1) * args.per_page,
            limit=9999 if args.all else args.per_page,
        )

        if not snippets:
            print(dim("\n  (暂无知识片段)\n"))
            return 0

        if args.tag:
            print(f"\n  {bold(f'知识片段 (标签: {args.tag})')}")
        else:
            print(f"\n  {bold('知识片段')}")
        print(f"  {'─' * 60}\n")

        rows = []
        for s in snippets:
            tags_str = ", ".join(s.tags) if s.tags else "-"
            rows.append([
                s.id[:8],
                truncate_text(s.title, 30),
                tags_str,
                format_datetime(s.updated_at),
            ])

        print_table(
            headers=["ID", "标题", "标签", "更新时间"],
            rows=rows,
            max_col_width=30,
        )

        if not args.all:
            total_pages = max(1, (total + args.per_page - 1) // args.per_page)
            print(f"\n  {dim(f'第 {args.page}/{total_pages} 页 | 共 {total} 条')}")

        return 0

    def _cmd_search(self, args: argparse.Namespace) -> int:
        """搜索知识片段 / Search knowledge snippets"""
        if not self._ensure_initialized():
            return 1

        if not self.search_engine:
            print_error("搜索引擎未初始化")
            return 1

        print(f"\n  {bold(f'搜索: {args.query}')}")
        print(f"  {'─' * 60}\n")

        results = self.search_engine.search(
            query=args.query,
            max_results=args.max,
        )

        if not results:
            print(dim("  (未找到匹配的知识片段)\n"))
            return 0

        print(f"  找到 {len(results)} 个结果:\n")

        for i, result in enumerate(results, 1):
            snippet = result.snippet
            print(f"  {colored(str(i) + '.', Colors.CYAN)} {bold(snippet.title)}")
            print(f"    {dim(f'ID: {snippet.id[:8]} | 相关度: {result.score:.4f}')}")
            if snippet.tags:
                print(f"    标签: {', '.join(colored(t, Colors.BLUE) for t in snippet.tags)}")
            # 显示高亮内容摘要 / Show highlighted content summary
            content_preview = truncate_text(snippet.content, 150)
            print(f"    {dim(content_preview)}")
            print()

        return 0

    def _cmd_show(self, args: argparse.Namespace) -> int:
        """显示知识片段详情 / Show snippet detail"""
        if not self._ensure_initialized():
            return 1

        snippet = self.storage.get_snippet(args.id)
        if not snippet:
            print_error(f"未找到知识片段: {args.id}")
            return 1

        print(f"\n  {bold(snippet.title)}")
        print(f"  {'═' * 50}\n")
        print(f"  ID:     {snippet.id}")
        print(f"  来源:   {snippet.source or '-'}")
        print(f"  创建:   {snippet.created_at}")
        print(f"  更新:   {snippet.updated_at}")
        if snippet.tags:
            print(f"  标签:   {', '.join(colored(t, Colors.BLUE) for t in snippet.tags)}")
        print(f"\n  {'─' * 50}\n")
        print(f"  {snippet.content}\n")

        return 0

    def _cmd_delete(self, args: argparse.Namespace) -> int:
        """删除知识片段 / Delete knowledge snippet"""
        if not self._ensure_initialized():
            return 1

        snippet = self.storage.get_snippet(args.id)
        if not snippet:
            print_error(f"未找到知识片段: {args.id}")
            return 1

        if not args.yes:
            if not prompt_confirm(f"确定要删除 '{snippet.title}' 吗？"):
                print_info("操作已取消")
                return 0

        self.storage.delete_snippet(snippet.id)
        print_success(f"已删除: {snippet.title}")

        return 0

    def _cmd_tags(self, args: argparse.Namespace) -> int:
        """管理标签 / Manage tags"""
        if not self._ensure_initialized():
            return 1

        tags = self.storage.list_tags()

        if not tags:
            print(dim("\n  (暂无标签)\n"))
            return 0

        print(f"\n  {bold('标签列表')}")
        print(f"  {'─' * 40}\n")

        rows = [[t.name, str(t.count), t.color] for t in tags]
        print_table(headers=["标签名", "使用次数", "颜色"], rows=rows)

        return 0

    def _cmd_workflow_run(self, args: argparse.Namespace) -> int:
        """执行工作流 / Run workflow"""
        if not self._ensure_initialized():
            return 1

        workflow = self.storage.get_workflow_by_name(args.name)
        if not workflow:
            print_error(f"未找到工作流: {args.name}")
            return 1

        from .workflow_engine import WorkflowEngine

        print(f"\n  {bold(f'执行工作流: {workflow.name}')}")
        print(f"  {'─' * 50}\n")

        engine = WorkflowEngine(
            llm_client=self.llm_client,
            max_parallel=self.config.get("workflow.max_parallel", 4),
            retry_count=self.config.get("workflow.retry_count", 3),
        )

        input_data = args.input if args.input else None
        log = engine.execute(workflow, input_data=input_data)

        # 显示执行结果 / Show execution results
        print(f"\n  执行结果: ", end="")
        if log.status.value == "success":
            print(success("成功"))
        elif log.status.value == "partial":
            print(warning("部分成功"))
        else:
            print(error("失败"))

        if log.error_message:
            print(f"  错误: {log.error_message}")

        for node_log in log.node_logs:
            status_icon = {
                "success": colored("OK", Colors.GREEN),
                "failed": colored("FAIL", Colors.RED),
                "skipped": colored("SKIP", Colors.YELLOW),
                "running": colored("RUN", Colors.BLUE),
            }.get(node_log.get("status", ""), node_log.get("status", ""))

            duration = node_log.get("duration", 0)
            duration_str = f" ({duration:.1f}s)" if duration else ""

            print(f"    [{status_icon}] {node_log.get('node_name', '')}{duration_str}")
            if node_log.get("error"):
                print(f"           错误: {node_log['error']}")

        # 保存执行日志 / Save execution log
        self.storage.save_workflow_log(log.to_dict())

        return 0 if log.status.value == "success" else 1

    def _cmd_workflow_list(self, args: argparse.Namespace) -> int:
        """列出工作流 / List workflows"""
        if not self._ensure_initialized():
            return 1

        workflows = self.storage.list_workflows()

        if not workflows:
            print(dim("\n  (暂无工作流)\n"))
            return 0

        print(f"\n  {bold('工作流列表')}")
        print(f"  {'─' * 60}\n")

        rows = []
        for w in workflows:
            rows.append([
                w.id[:8],
                w.name,
                str(len(w.nodes)),
                str(len(w.edges)),
                format_datetime(w.updated_at),
            ])

        print_table(
            headers=["ID", "名称", "节点数", "连接数", "更新时间"],
            rows=rows,
        )

        return 0

    def _cmd_workflow_create(self, args: argparse.Namespace) -> int:
        """创建工作流 / Create workflow"""
        if not self._ensure_initialized():
            return 1

        print(f"\n  {bold('创建工作流')}")
        print(f"  {'─' * 40}\n")

        name = prompt_input("工作流名称", required=True)
        description = prompt_input("描述")

        workflow = Workflow(name=name, description=description)

        # 添加节点 / Add nodes
        print(f"\n  {info('添加节点（输入空名称结束）')}\n")

        node_types = ["input", "llm", "transform", "filter", "export", "merge"]
        while True:
            node_name = prompt_input("节点名称")
            if not node_name:
                break

            type_idx = prompt_choice("节点类型", node_types)
            node_type = NodeType(node_types[type_idx])

            node = WorkflowNode(type=node_type, name=node_name)

            # 根据类型配置 / Configure based on type
            if node_type == NodeType.LLM:
                prompt_text = prompt_input("提示模板", default="请处理以下内容:\n{{input}}")
                node.config["prompt"] = prompt_text
                system_prompt = prompt_input("系统提示", default="")
                if system_prompt:
                    node.config["system_prompt"] = system_prompt
            elif node_type == NodeType.TRANSFORM:
                transform_type = prompt_input("转换类型", default="text")
                node.config["transform_type"] = transform_type
            elif node_type == NodeType.FILTER:
                condition_type = prompt_input("条件类型", default="contains")
                condition_value = prompt_input("条件值")
                node.config["condition_type"] = condition_type
                node.config["condition_value"] = condition_value
            elif node_type == NodeType.EXPORT:
                export_format = prompt_input("导出格式", default="markdown")
                node.config["format"] = export_format

            workflow.add_node(node)
            print_success(f"已添加节点: {node_name} ({node_type.value})")

        if len(workflow.nodes) < 2:
            print_warning("工作流至少需要2个节点")
            return 1

        # 添加边（简单顺序连接） / Add edges (simple sequential connection)
        print(f"\n  {info('连接节点')}")
        for i in range(len(workflow.nodes) - 1):
            edge = WorkflowEdge(
                source_id=workflow.nodes[i].id,
                target_id=workflow.nodes[i + 1].id,
            )
            workflow.add_edge(edge)
            print(f"    {workflow.nodes[i].name} -> {workflow.nodes[i + 1].name}")

        # 保存 / Save
        self.storage.save_workflow(workflow)
        print_success(f"\n工作流 '{name}' 已创建")

        return 0

    def _cmd_workflow_show(self, args: argparse.Namespace) -> int:
        """显示工作流详情 / Show workflow detail"""
        if not self._ensure_initialized():
            return 1

        workflow = self.storage.get_workflow_by_name(args.name)
        if not workflow:
            print_error(f"未找到工作流: {args.name}")
            return 1

        print(f"\n  {bold(workflow.name)}")
        print(f"  {'═' * 50}\n")
        print(f"  描述:   {workflow.description or '-'}")
        print(f"  ID:     {workflow.id}")
        print(f"  创建:   {workflow.created_at}")
        print(f"  更新:   {workflow.updated_at}")

        print(f"\n  {bold('节点:')}")
        for node in workflow.nodes:
            print(f"    [{colored(node.type.value, Colors.CYAN)}] {node.name}")

        print(f"\n  {bold('连接:')}")
        for edge in workflow.edges:
            src = workflow.get_node(edge.source_id)
            tgt = workflow.get_node(edge.target_id)
            src_name = src.name if src else edge.source_id[:8]
            tgt_name = tgt.name if tgt else edge.target_id[:8]
            cond = f" [{edge.condition}]" if edge.condition else ""
            print(f"    {src_name} -> {tgt_name}{cond}")

        return 0

    def _cmd_workflow_delete(self, args: argparse.Namespace) -> int:
        """删除工作流 / Delete workflow"""
        if not self._ensure_initialized():
            return 1

        workflow = self.storage.get_workflow_by_name(args.name)
        if not workflow:
            print_error(f"未找到工作流: {args.name}")
            return 1

        if not args.yes:
            if not prompt_confirm(f"确定要删除工作流 '{workflow.name}' 吗？"):
                print_info("操作已取消")
                return 0

        self.storage.delete_workflow(workflow.id)
        print_success(f"已删除工作流: {workflow.name}")

        return 0

    def _cmd_template_list(self, args: argparse.Namespace) -> int:
        """列出模板 / List templates"""
        if not self._ensure_initialized():
            return 1

        if not self.template_manager:
            print_error("模板管理器未初始化")
            return 1

        templates = self.template_manager.list_templates()

        if not templates:
            print(dim("\n  (暂无模板)\n"))
            return 0

        print(f"\n  {bold('模板列表')}")
        print(f"  {'─' * 60}\n")

        rows = []
        for t in templates:
            builtin = colored("内置", Colors.CYAN) if t.is_builtin else colored("自定义", Colors.YELLOW)
            rows.append([
                t.name,
                truncate_text(t.description, 40),
                t.category,
                builtin,
            ])

        print_table(
            headers=["名称", "描述", "分类", "类型"],
            rows=rows,
            max_col_width=40,
        )

        return 0

    def _cmd_template_apply(self, args: argparse.Namespace) -> int:
        """应用模板 / Apply template"""
        if not self._ensure_initialized():
            return 1

        if not self.template_manager:
            print_error("模板管理器未初始化")
            return 1

        template = self.template_manager.get_template(args.name)
        if not template:
            print_error(f"未找到模板: {args.name}")
            return 1

        print(f"\n  {bold(f'应用模板: {template.name}')}")
        print(f"  {dim(template.description)}\n")

        # 收集变量值 / Collect variable values
        variables: dict = {}
        for var in template.variables:
            label = var.get("label", var["name"])
            default = var.get("default", "")
            required = var.get("required", False)

            if var.get("type") == "select":
                options = var.get("options", [])
                if options:
                    idx = prompt_choice(label, options)
                    variables[var["name"]] = options[idx]
                else:
                    variables[var["name"]] = prompt_input(label, default, required)
            else:
                variables[var["name"]] = prompt_input(label, default, required)

        # 创建工作流 / Create workflow
        workflow = self.template_manager.apply(args.name, variables)
        self.storage.save_workflow(workflow)

        print_success(f"工作流 '{workflow.name}' 已从模板创建")
        print_info(f"使用 'mindflow workflow run {workflow.name}' 执行")

        return 0

    def _cmd_template_info(self, args: argparse.Namespace) -> int:
        """查看模板详情 / View template detail"""
        if not self._ensure_initialized():
            return 1

        if not self.template_manager:
            print_error("模板管理器未初始化")
            return 1

        info_data = self.template_manager.get_template_info(args.name)
        if not info_data:
            print_error(f"未找到模板: {args.name}")
            return 1

        print(f"\n  {bold(info_data['name'])}")
        print(f"  {'═' * 50}\n")
        print(f"  描述:     {info_data['description']}")
        print(f"  分类:     {info_data['category']}")
        print(f"  类型:     {'内置' if info_data['is_builtin'] else '自定义'}")
        print(f"  节点数:   {info_data['node_count']}")
        print(f"  连接数:   {info_data['edge_count']}")

        if info_data["variables"]:
            print(f"\n  {bold('变量:')}")
            for var in info_data["variables"]:
                required = colored("必填", Colors.RED) if var.get("required") else "可选"
                default = f" (默认: {var['default']})" if var.get("default") else ""
                print(f"    - {var.get('label', var['name'])} [{required}]{default}")

        return 0

    def _cmd_export(self, args: argparse.Namespace) -> int:
        """导出知识库 / Export knowledge base"""
        if not self._ensure_initialized():
            return 1

        snippets = self.storage.get_all_snippets()
        workflows = self.storage.list_workflows()

        if not snippets:
            print_warning("知识库为空，无内容可导出")
            return 0

        # 确定输出路径 / Determine output path
        if args.output:
            output_path = args.output
        else:
            ext_map = {"json": "json", "markdown": "md", "html": "html"}
            ext = ext_map.get(args.format, args.format)
            output_path = str(
                self.config.exports_dir / f"mindflow_export.{ext}"
            )

        print(f"\n  {bold('导出知识库')}")
        print(f"  格式: {args.format}")
        print(f"  路径: {output_path}\n")

        try:
            actual_path = self.exporter.export(
                snippets=snippets,
                format_type=args.format,
                output_path=output_path,
                workflows=workflows,
            )
            print_success(f"导出完成: {actual_path}")

            # 显示文件大小 / Show file size
            import os
            file_size = os.path.getsize(actual_path)
            print(f"    文件大小: {format_file_size(file_size)}")

        except Exception as e:
            print_error(f"导出失败: {e}")
            return 1

        return 0

    def _cmd_config(self, args: argparse.Namespace) -> int:
        """配置管理 / Configuration management"""
        if args.list_all:
            print(f"\n  {bold('当前配置')}")
            print(f"  {'─' * 50}\n")

            config_data = self.config.to_dict()
            self._print_config_tree(config_data, indent=2)
            return 0

        if args.get_key:
            value = self.config.get(args.get_key)
            if value is None:
                print_warning(f"配置项 '{args.get_key}' 不存在")
            else:
                print(value)
            return 0

        if args.set_key:
            print(f"\n  {bold('配置LLM API')}")
            print(f"  {'─' * 40}\n")

            key_parts = args.set_key.split(".")
            if key_parts[0] == "llm" and len(key_parts) >= 2:
                provider = key_parts[1]
                if provider in ("openai", "anthropic", "ollama"):
                    return self._configure_llm_provider(provider)

            # 通用设置 / Generic setting
            value = prompt_input(f"值")
            self.config.set(args.set_key, value)
            self.config.save()
            print_success(f"已设置 {args.set_key} = {value}")
            return 0

        # 无参数时显示配置向导 / Show config wizard when no args
        print(f"\n  {bold('MindFlow 配置')}")
        print(f"  {'─' * 40}\n")

        print(f"  1. 配置LLM API")
        print(f"  2. 查看当前配置")
        print(f"  3. 重置配置\n")

        choice = prompt_choice("选择操作", ["配置LLM", "查看配置", "重置配置"])

        if choice == 0:
            providers = ["OpenAI", "Anthropic", "Ollama"]
            idx = prompt_choice("选择LLM提供商", providers)
            provider_map = {0: "openai", 1: "anthropic", 2: "ollama"}
            return self._configure_llm_provider(provider_map[idx])
        elif choice == 1:
            config_data = self.config.to_dict()
            self._print_config_tree(config_data, indent=2)
        elif choice == 2:
            if prompt_confirm("确定要重置配置吗？"):
                self.config.initialize()
                print_success("配置已重置")

        return 0

    def _configure_llm_provider(self, provider: str) -> int:
        """
        交互式配置LLM提供商 / Interactively configure LLM provider

        参数 / Args:
            provider: 提供商名称 / Provider name
        """
        print(f"\n  {bold(f'配置 {provider.upper()}')}")

        if provider != "ollama":
            api_key = prompt_input("API Key", password=True)
            if api_key:
                self.config.set_llm_api_key(provider, api_key)

        base_url = prompt_input(
            "API Base URL",
            default=self.config.get(f"llm.{provider}.base_url", ""),
        )
        if base_url:
            self.config.set_llm_base_url(provider, base_url)

        model = prompt_input(
            "模型名称",
            default=self.config.get(f"llm.{provider}.model", ""),
        )
        if model:
            self.config.set_llm_model(provider, model)

        # 设为默认提供商 / Set as default provider
        if prompt_confirm(f"设为默认LLM提供商？", default=True):
            self.config.set("llm.default_provider", provider)

        self.config.save()
        print_success(f"{provider.upper()} 配置已保存")
        return 0

    def _print_config_tree(self, data: dict, indent: int = 0) -> None:
        """打印配置树 / Print config tree"""
        prefix = " " * indent
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"{prefix}{bold(key)}:")
                self._print_config_tree(value, indent + 4)
            else:
                display_value = str(value)
                if len(display_value) > 60:
                    display_value = display_value[:57] + "..."
                # 隐藏API密钥 / Hide API keys
                if "key" in key.lower() and display_value:
                    display_value = display_value[:4] + "****" + display_value[-4:]
                print(f"{prefix}{key}: {dim(display_value)}")

    def _cmd_tui(self, args: argparse.Namespace) -> int:
        """启动TUI界面 / Launch TUI interface"""
        if not self._ensure_initialized():
            return 1

        try:
            from .tui import MindFlowTUI
            app = MindFlowTUI(self.config, self.storage)
            app.run()
        except ImportError as e:
            print_error(f"TUI模块加载失败: {e}")
            return 1
        except Exception as e:
            print_error(f"TUI启动失败: {e}")
            return 1

        return 0

    def _cmd_stats(self, args: argparse.Namespace) -> int:
        """显示统计信息 / Show statistics"""
        if not self._ensure_initialized():
            return 1

        stats = self.storage.get_statistics()

        print(f"\n  {bold('MindFlow 统计信息')}")
        print(f"  {'═' * 50}\n")

        print(f"  知识片段总数:  {bold(str(stats['total_snippets']))}")
        print(f"  标签总数:      {bold(str(stats['total_tags']))}")
        print(f"  工作流总数:    {bold(str(stats['total_workflows']))}")
        print(f"  数据库大小:    {bold(format_file_size(stats['db_size']))}")

        if stats.get("last_updated"):
            print(f"  最后更新:      {format_datetime(stats['last_updated'])}")

        if stats.get("top_tags"):
            print(f"\n  {bold('热门标签:')}")
            for tag_info in stats["top_tags"][:10]:
                name = tag_info["name"]
                count = tag_info["count"]
                bar_len = min(count * 2, 20)
                bar = colored("█" * bar_len, Colors.CYAN)
                print(f"    {name:<15} {bar} {count}")

        return 0


def main(args: Optional[List[str]] = None) -> int:
    """
    CLI入口函数 / CLI entry function

    参数 / Args:
        args: 命令行参数 / Command-line arguments

    返回 / Returns:
        退出码 / Exit code
    """
    cli = MindFlowCLI()
    return cli.run(args)
