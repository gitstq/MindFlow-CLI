"""
工作流引擎模块 / Workflow Engine Module

实现DAG（有向无环图）工作流引擎，支持条件分支、并行执行和多种节点类型。
Implements DAG (Directed Acyclic Graph) workflow engine with conditional branching,
parallel execution, and multiple node types.
"""

from __future__ import annotations

import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .models import (
    NodeStatus,
    Workflow,
    WorkflowEdge,
    WorkflowExecutionLog,
    WorkflowNode,
    WorkflowStatus,
)
from .utils import format_duration


class WorkflowError(Exception):
    """工作流执行错误 / Workflow execution error"""
    pass


class NodeExecutionError(WorkflowError):
    """节点执行错误 / Node execution error"""

    def __init__(self, node_id: str, node_name: str, message: str) -> None:
        self.node_id = node_id
        self.node_name = node_name
        super().__init__(f"节点 '{node_name}' (ID: {node_id}) 执行失败: {message}")


class NodeExecutor:
    """
    节点执行器 / Node Executor

    负责执行各种类型的工作流节点。
    Responsible for executing various types of workflow nodes.
    """

    def __init__(self, llm_client: Optional[Any] = None) -> None:
        """
        初始化节点执行器 / Initialize node executor

        参数 / Args:
            llm_client: LLM客户端实例 / LLM client instance
        """
        self.llm_client = llm_client
        self._custom_handlers: Dict[str, Callable] = {}

    def register_handler(
        self, node_type: str, handler: Callable
    ) -> None:
        """
        注册自定义节点处理器 / Register custom node handler

        参数 / Args:
            node_type: 节点类型 / Node type
            handler: 处理函数 / Handler function
        """
        self._custom_handlers[node_type] = handler

    def execute(self, node: WorkflowNode, context: Dict[str, Any]) -> Any:
        """
        执行节点 / Execute node

        参数 / Args:
            node: 工作流节点 / Workflow node
            context: 执行上下文 / Execution context

        返回 / Returns:
            节点输出数据 / Node output data
        """
        node.status = NodeStatus.RUNNING
        node.input_data = context.get("input_data")

        try:
            if node.type.value == "llm":
                result = self._execute_llm_node(node, context)
            elif node.type.value == "transform":
                result = self._execute_transform_node(node, context)
            elif node.type.value == "filter":
                result = self._execute_filter_node(node, context)
            elif node.type.value == "export":
                result = self._execute_export_node(node, context)
            elif node.type.value == "input":
                result = self._execute_input_node(node, context)
            elif node.type.value == "merge":
                result = self._execute_merge_node(node, context)
            elif node.type.value in self._custom_handlers:
                result = self._custom_handlers[node.type.value](node, context)
            else:
                raise WorkflowError(f"未知的节点类型: {node.type.value}")

            node.output_data = result
            node.status = NodeStatus.SUCCESS
            return result

        except Exception as e:
            node.status = NodeStatus.FAILED
            node.error_message = str(e)
            raise NodeExecutionError(node.id, node.name, str(e))

    def _execute_llm_node(
        self, node: WorkflowNode, context: Dict[str, Any]
    ) -> str:
        """
        执行LLM节点 / Execute LLM node

        调用LLM API处理输入数据。

        参数 / Args:
            node: 工作流节点 / Workflow node
            context: 执行上下文 / Execution context

        返回 / Returns:
            LLM响应文本 / LLM response text
        """
        config = node.config
        prompt_template = config.get("prompt", "")
        system_prompt = config.get("system_prompt", "")

        # 获取输入 / Get input
        input_data = context.get("input_data", "")
        if isinstance(input_data, list):
            input_data = "\n".join(str(item) for item in input_data)
        elif not isinstance(input_data, str):
            input_data = str(input_data)

        # 替换模板变量 / Replace template variables
        prompt = prompt_template.replace("{{input}}", input_data)
        for key, value in context.get("variables", {}).items():
            prompt = prompt.replace(f"{{{{{key}}}}}", str(value))

        # 调用LLM / Call LLM
        if self.llm_client is None:
            raise WorkflowError("LLM客户端未配置")

        response = self.llm_client.chat(
            message=prompt,
            system_prompt=system_prompt,
            provider=config.get("provider"),
            model=config.get("model"),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 2048),
        )

        return response.content

    def _execute_transform_node(
        self, node: WorkflowNode, context: Dict[str, Any]
    ) -> Any:
        """
        执行数据转换节点 / Execute data transform node

        对输入数据进行转换处理。

        参数 / Args:
            node: 工作流节点 / Workflow node
            context: 执行上下文 / Execution context

        返回 / Returns:
            转换后的数据 / Transformed data
        """
        config = node.config
        transform_type = config.get("transform_type", "text")
        input_data = context.get("input_data", "")

        if transform_type == "text":
            # 文本转换 / Text transformation
            operations = config.get("operations", [])
            result = str(input_data)

            for op in operations:
                op_type = op.get("type", "")

                if op_type == "uppercase":
                    result = result.upper()
                elif op_type == "lowercase":
                    result = result.lower()
                elif op_type == "strip":
                    result = result.strip()
                elif op_type == "replace":
                    result = result.replace(
                        op.get("old", ""), op.get("new", "")
                    )
                elif op_type == "prefix":
                    result = op.get("value", "") + result
                elif op_type == "suffix":
                    result = result + op.get("value", "")
                elif op_type == "template":
                    template = op.get("value", "{{input}}")
                    result = template.replace("{{input}}", result)
                elif op_type == "split":
                    delimiter = op.get("delimiter", "\n")
                    result = result.split(delimiter)
                elif op_type == "join":
                    delimiter = op.get("delimiter", "\n")
                    if isinstance(result, list):
                        result = delimiter.join(str(item) for item in result)
                elif op_type == "extract":
                    # 简单的文本提取 / Simple text extraction
                    import re
                    pattern = op.get("pattern", "")
                    if pattern:
                        matches = re.findall(pattern, result)
                        result = matches if matches else result

            return result

        elif transform_type == "list":
            # 列表操作 / List operations
            operation = config.get("operation", "filter")

            if not isinstance(input_data, list):
                input_data = [input_data]

            if operation == "filter":
                condition = config.get("condition", "")
                if condition == "non_empty":
                    return [item for item in input_data if item]
                elif condition == "unique":
                    seen: Set = set()
                    return [
                        item for item in input_data
                        if str(item) not in seen and not seen.add(str(item))
                    ]
                return input_data

            elif operation == "sort":
                reverse = config.get("reverse", False)
                return sorted(input_data, reverse=reverse)

            elif operation == "slice":
                start = config.get("start", 0)
                end = config.get("end", len(input_data))
                return input_data[start:end]

            elif operation == "map":
                template = config.get("template", "{{item}}")
                return [
                    template.replace("{{item}}", str(item))
                    for item in input_data
                ]

            elif operation == "count":
                return len(input_data)

            return input_data

        elif transform_type == "aggregate":
            # 聚合操作 / Aggregation operations
            if not isinstance(input_data, list):
                input_data = [input_data]

            operation = config.get("operation", "concat")

            if operation == "concat":
                delimiter = config.get("delimiter", "\n")
                return delimiter.join(str(item) for item in input_data)
            elif operation == "sum":
                return sum(
                    float(item) for item in input_data
                    if isinstance(item, (int, float))
                )
            elif operation == "count":
                return len(input_data)

            return input_data

        return input_data

    def _execute_filter_node(
        self, node: WorkflowNode, context: Dict[str, Any]
    ) -> Any:
        """
        执行条件过滤节点 / Execute filter node

        根据条件过滤输入数据。

        参数 / Args:
            node: 工作流节点 / Workflow node
            context: 执行上下文 / Execution context

        返回 / Returns:
            过滤后的数据 / Filtered data
        """
        config = node.config
        input_data = context.get("input_data", "")

        if not isinstance(input_data, list):
            input_data = [input_data]

        condition_type = config.get("condition_type", "contains")
        condition_value = config.get("condition_value", "")

        filtered = []
        for item in input_data:
            item_str = str(item)
            passes = False

            if condition_type == "contains":
                passes = condition_value in item_str
            elif condition_type == "not_contains":
                passes = condition_value not in item_str
            elif condition_type == "equals":
                passes = item_str == condition_value
            elif condition_type == "not_equals":
                passes = item_str != condition_value
            elif condition_type == "starts_with":
                passes = item_str.startswith(condition_value)
            elif condition_type == "ends_with":
                passes = item_str.endswith(condition_value)
            elif condition_type == "length_gt":
                try:
                    passes = len(item_str) > int(condition_value)
                except ValueError:
                    passes = False
            elif condition_type == "length_lt":
                try:
                    passes = len(item_str) < int(condition_value)
                except ValueError:
                    passes = False
            elif condition_type == "regex":
                import re
                try:
                    passes = bool(re.search(condition_value, item_str))
                except re.error:
                    passes = False
            elif condition_type == "non_empty":
                passes = bool(item_str.strip())

            if passes:
                filtered.append(item)

        return filtered

    def _execute_export_node(
        self, node: WorkflowNode, context: Dict[str, Any]
    ) -> str:
        """
        执行导出节点 / Execute export node

        将数据导出为指定格式。

        参数 / Args:
            node: 工作流节点 / Workflow node
            context: 执行上下文 / Execution context

        返回 / Returns:
            导出结果摘要 / Export result summary
        """
        config = node.config
        export_format = config.get("format", "text")
        input_data = context.get("input_data", "")
        output_path = config.get("output_path", "")

        if export_format == "text":
            result = str(input_data)
        elif export_format == "json":
            import json
            result = json.dumps(
                input_data, ensure_ascii=False, indent=2
            )
        elif export_format == "markdown":
            if isinstance(input_data, list):
                result = "\n".join(f"- {item}" for item in input_data)
            else:
                result = str(input_data)
        else:
            result = str(input_data)

        # 如果指定了输出路径，写入文件 / Write to file if output path specified
        if output_path:
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result)
                return f"已导出到: {output_path}"
            except IOError as e:
                raise WorkflowError(f"导出失败: {e}")

        return result

    def _execute_input_node(
        self, node: WorkflowNode, context: Dict[str, Any]
    ) -> Any:
        """
        执行输入节点 / Execute input node

        提供工作流的初始输入数据。

        参数 / Args:
            node: 工作流节点 / Workflow node
            context: 执行上下文 / Execution context

        返回 / Returns:
            输入数据 / Input data
        """
        config = node.config
        input_type = config.get("input_type", "static")
        value = config.get("value", "")

        if input_type == "static":
            return value
        elif input_type == "context":
            key = config.get("context_key", "input")
            return context.get(key, "")
        elif input_type == "query":
            # 从搜索结果获取 / Get from search results
            search_results = context.get("search_results", [])
            return search_results
        elif input_type == "list":
            return config.get("items", [])

        return value

    def _execute_merge_node(
        self, node: WorkflowNode, context: Dict[str, Any]
    ) -> Any:
        """
        执行合并节点 / Execute merge node

        合并多个上游节点的输出。

        参数 / Args:
            node: 工作流节点 / Workflow node
            context: 执行上下文 / Execution context

        返回 / Returns:
            合并后的数据 / Merged data
        """
        config = node.config
        merge_type = config.get("merge_type", "concat")
        upstream_data = context.get("upstream_outputs", [])

        if not upstream_data:
            return None

        if merge_type == "concat":
            delimiter = config.get("delimiter", "\n")
            return delimiter.join(str(item) for item in upstream_data)
        elif merge_type == "list":
            result = []
            for item in upstream_data:
                if isinstance(item, list):
                    result.extend(item)
                else:
                    result.append(item)
            return result
        elif merge_type == "dict":
            result = {}
            for item in upstream_data:
                if isinstance(item, dict):
                    result.update(item)
            return result

        return upstream_data


class WorkflowEngine:
    """
    工作流引擎 / Workflow Engine

    基于DAG的工作流执行引擎，支持拓扑排序、并行执行和错误处理。
    DAG-based workflow execution engine with topological sorting,
    parallel execution, and error handling.

    用法 / Usage:
        engine = WorkflowEngine()
        log = engine.execute(workflow, input_data="输入数据")
        print(log.to_dict())
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        max_parallel: int = 4,
        retry_count: int = 3,
        retry_delay: float = 5.0,
        timeout: float = 300.0,
    ) -> None:
        """
        初始化工作流引擎 / Initialize workflow engine

        参数 / Args:
            llm_client: LLM客户端 / LLM client
            max_parallel: 最大并行数 / Maximum parallel count
            retry_count: 重试次数 / Retry count
            retry_delay: 重试延迟 / Retry delay
            timeout: 超时时间 / Timeout
        """
        self.node_executor = NodeExecutor(llm_client)
        self.max_parallel = max_parallel
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.timeout = timeout
        self._execution_callbacks: List[Callable] = []

    def on_node_complete(self, callback: Callable) -> None:
        """注册节点完成回调 / Register node completion callback"""
        self._execution_callbacks.append(callback)

    def _topological_sort(
        self, workflow: Workflow
    ) -> List[List[WorkflowNode]]:
        """
        拓扑排序（分层） / Topological sort (layered)

        将工作流节点按依赖关系分层，同一层的节点可以并行执行。

        参数 / Args:
            workflow: 工作流 / Workflow

        返回 / Returns:
            分层后的节点列表 / Layered node lists

        异常 / Raises:
            WorkflowError: 存在循环依赖 / Circular dependency exists
        """
        if not workflow.nodes:
            return []

        # 构建邻接表和入度 / Build adjacency list and in-degree
        node_map = {node.id: node for node in workflow.nodes}
        in_degree: Dict[str, int] = {node.id: 0 for node in workflow.nodes}
        adjacency: Dict[str, List[str]] = {node.id: [] for node in workflow.nodes}

        for edge in workflow.edges:
            if edge.source_id in adjacency:
                adjacency[edge.source_id].append(edge.target_id)
            if edge.target_id in in_degree:
                in_degree[edge.target_id] += 1

        # Kahn算法 / Kahn's algorithm
        layers: List[List[WorkflowNode]] = []
        remaining = set(node_map.keys())
        processed = 0

        while remaining:
            # 找到当前入度为0的节点 / Find nodes with in-degree 0
            current_layer = [
                node_map[nid] for nid in remaining if in_degree.get(nid, 0) == 0
            ]

            if not current_layer:
                # 存在循环依赖 / Circular dependency exists
                raise WorkflowError(
                    f"工作流 '{workflow.name}' 存在循环依赖，"
                    f"涉及节点: {remaining}"
                )

            layers.append(current_layer)
            processed += len(current_layer)

            # 更新入度 / Update in-degree
            for node in current_layer:
                remaining.discard(node.id)
                for downstream_id in adjacency.get(node.id, []):
                    in_degree[downstream_id] -= 1

        return layers

    def _evaluate_condition(
        self, condition: Optional[str], context: Dict[str, Any]
    ) -> bool:
        """
        评估条件表达式 / Evaluate condition expression

        参数 / Args:
            condition: 条件表达式 / Condition expression
            context: 执行上下文 / Execution context

        返回 / Returns:
            条件是否满足 / Whether condition is met
        """
        if not condition:
            return True

        # 简单的条件评估 / Simple condition evaluation
        condition = condition.strip()

        # 支持的条件格式 / Supported condition formats:
        # "output contains 'keyword'"
        # "output length > 100"
        # "output is not empty"
        # "variable_name == value"

        output_data = context.get("output_data", "")

        if " contains " in condition:
            parts = condition.split(" contains ", 1)
            value = parts[1].strip().strip("'\"")
            return value in str(output_data)

        elif " not contains " in condition:
            parts = condition.split(" not contains ", 1)
            value = parts[1].strip().strip("'\"")
            return value not in str(output_data)

        elif " length > " in condition:
            parts = condition.split(" length > ", 1)
            try:
                threshold = int(parts[1].strip())
                return len(str(output_data)) > threshold
            except ValueError:
                return False

        elif " length < " in condition:
            parts = condition.split(" length < ", 1)
            try:
                threshold = int(parts[1].strip())
                return len(str(output_data)) < threshold
            except ValueError:
                return False

        elif " is not empty" in condition:
            return bool(output_data)

        elif " is empty" in condition:
            return not bool(output_data)

        elif " == " in condition:
            parts = condition.split(" == ", 1)
            value = parts[1].strip().strip("'\"")
            return str(output_data) == value

        elif " != " in condition:
            parts = condition.split(" != ", 1)
            value = parts[1].strip().strip("'\"")
            return str(output_data) != value

        # 默认返回True / Default to True
        return True

    def execute(
        self,
        workflow: Workflow,
        input_data: Any = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> WorkflowExecutionLog:
        """
        执行工作流 / Execute workflow

        参数 / Args:
            workflow: 工作流对象 / Workflow object
            input_data: 输入数据 / Input data
            variables: 模板变量 / Template variables

        返回 / Returns:
            执行日志 / Execution log
        """
        log = WorkflowExecutionLog(
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            start_time=datetime.now().isoformat(),
            status=WorkflowStatus.RUNNING,
        )

        # 重置节点状态 / Reset node statuses
        for node in workflow.nodes:
            node.status = NodeStatus.PENDING
            node.output_data = None
            node.error_message = ""

        workflow.status = WorkflowStatus.RUNNING

        try:
            # 拓扑排序 / Topological sort
            layers = self._topological_sort(workflow)

            # 节点输出缓存 / Node output cache
            node_outputs: Dict[str, Any] = {}
            if input_data is not None:
                node_outputs["__input__"] = input_data

            # 逐层执行 / Execute layer by layer
            for layer_idx, layer in enumerate(layers):
                # 检查超时 / Check timeout
                elapsed = time.time() - datetime.fromisoformat(log.start_time).timestamp()
                if elapsed > self.timeout:
                    raise WorkflowError(
                        f"工作流执行超时 ({format_duration(self.timeout)})"
                    )

                # 构建执行上下文 / Build execution context
                executed_count = sum(1 for n in workflow.nodes if n.status == NodeStatus.SUCCESS)
                failed_count = sum(1 for n in workflow.nodes if n.status == NodeStatus.FAILED)

                # 并行执行当前层 / Execute current layer in parallel
                if len(layer) > 1 and self.max_parallel > 1:
                    self._execute_layer_parallel(
                        layer, workflow, node_outputs, log, variables
                    )
                else:
                    for node in layer:
                        self._execute_node(
                            node, workflow, node_outputs, log, variables
                        )

            # 统计结果 / Collect results
            success_count = sum(
                1 for n in workflow.nodes if n.status == NodeStatus.SUCCESS
            )
            failed_count = sum(
                1 for n in workflow.nodes if n.status == NodeStatus.FAILED
            )

            if failed_count == 0:
                workflow.status = WorkflowStatus.SUCCESS
                log.status = WorkflowStatus.SUCCESS
            elif success_count > 0:
                workflow.status = WorkflowStatus.PARTIAL
                log.status = WorkflowStatus.PARTIAL
            else:
                workflow.status = WorkflowStatus.FAILED
                log.status = WorkflowStatus.FAILED

        except WorkflowError as e:
            workflow.status = WorkflowStatus.FAILED
            log.status = WorkflowStatus.FAILED
            log.error_message = str(e)
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            log.status = WorkflowStatus.FAILED
            log.error_message = f"未知错误: {str(e)}\n{traceback.format_exc()}"

        log.end_time = datetime.now().isoformat()
        return log

    def _execute_layer_parallel(
        self,
        layer: List[WorkflowNode],
        workflow: Workflow,
        node_outputs: Dict[str, Any],
        log: WorkflowExecutionLog,
        variables: Optional[Dict[str, Any]],
    ) -> None:
        """
        并行执行一层节点 / Execute a layer of nodes in parallel

        参数 / Args:
            layer: 节点列表 / List of nodes
            workflow: 工作流 / Workflow
            node_outputs: 节点输出缓存 / Node output cache
            log: 执行日志 / Execution log
            variables: 模板变量 / Template variables
        """
        with ThreadPoolExecutor(max_workers=min(len(layer), self.max_parallel)) as executor:
            futures = {}
            for node in layer:
                future = executor.submit(
                    self._execute_node,
                    node, workflow, node_outputs, log, variables,
                )
                futures[future] = node

            for future in as_completed(futures):
                node = futures[future]
                try:
                    future.result()
                except Exception as e:
                    node.status = NodeStatus.FAILED
                    node.error_message = str(e)
                    log.node_logs.append({
                        "node_id": node.id,
                        "node_name": node.name,
                        "status": "failed",
                        "error": str(e),
                    })

    def _execute_node(
        self,
        node: WorkflowNode,
        workflow: Workflow,
        node_outputs: Dict[str, Any],
        log: WorkflowExecutionLog,
        variables: Optional[Dict[str, Any]],
    ) -> Any:
        """
        执行单个节点 / Execute a single node

        参数 / Args:
            node: 工作流节点 / Workflow node
            workflow: 工作流 / Workflow
            node_outputs: 节点输出缓存 / Node output cache
            log: 执行日志 / Execution log
            variables: 模板变量 / Template variables

        返回 / Returns:
            节点输出 / Node output
        """
        node_start = time.time()

        # 检查上游条件 / Check upstream conditions
        upstream_nodes = workflow.get_upstream_nodes(node.id)
        for upstream in upstream_nodes:
            edge = next(
                (e for e in workflow.edges
                 if e.source_id == upstream.id and e.target_id == node.id),
                None,
            )
            if edge and edge.condition:
                if not self._evaluate_condition(
                    edge.condition,
                    {"output_data": upstream.output_data},
                ):
                    node.status = NodeStatus.SKIPPED
                    log.node_logs.append({
                        "node_id": node.id,
                        "node_name": node.name,
                        "status": "skipped",
                        "reason": "条件不满足",
                    })
                    return None

            # 如果上游失败，跳过当前节点 / Skip if upstream failed
            if upstream.status == NodeStatus.FAILED:
                node.status = NodeStatus.SKIPPED
                log.node_logs.append({
                    "node_id": node.id,
                    "node_name": node.name,
                    "status": "skipped",
                    "reason": "上游节点失败",
                })
                return None

        # 收集上游输出 / Collect upstream outputs
        upstream_outputs = [
            upstream.output_data
            for upstream in upstream_nodes
            if upstream.output_data is not None
        ]

        # 构建执行上下文 / Build execution context
        context: Dict[str, Any] = {
            "input_data": upstream_outputs[0] if len(upstream_outputs) == 1 else upstream_outputs,
            "upstream_outputs": upstream_outputs,
            "variables": variables or {},
            "node_config": node.config,
            "workflow_id": workflow.id,
        }

        # 如果是输入节点，使用全局输入 / Use global input for input nodes
        if node.type.value == "input":
            context["input_data"] = node_outputs.get("__input__", "")

        # 带重试的执行 / Execute with retries
        last_error: Optional[Exception] = None
        for attempt in range(self.retry_count):
            try:
                result = self.node_executor.execute(node, context)
                node_outputs[node.id] = result

                node_elapsed = time.time() - node_start
                log.node_logs.append({
                    "node_id": node.id,
                    "node_name": node.name,
                    "status": "success",
                    "duration": round(node_elapsed, 3),
                    "attempt": attempt + 1,
                })

                # 触发回调 / Trigger callbacks
                for callback in self._execution_callbacks:
                    try:
                        callback(node, result)
                    except Exception:
                        pass

                return result

            except NodeExecutionError as e:
                last_error = e
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                break

        # 所有重试都失败 / All retries failed
        node.status = NodeStatus.FAILED
        log.node_logs.append({
            "node_id": node.id,
            "node_name": node.name,
            "status": "failed",
            "error": str(last_error),
            "attempts": self.retry_count,
        })

        raise last_error  # type: ignore

    def validate_workflow(self, workflow: Workflow) -> List[str]:
        """
        验证工作流 / Validate workflow

        检查工作流的结构是否合法。

        参数 / Args:
            workflow: 工作流 / Workflow

        返回 / Returns:
            问题列表（空列表表示无问题） / List of issues (empty = no issues)
        """
        issues: List[str] = []

        if not workflow.nodes:
            issues.append("工作流没有节点")
            return issues

        if not workflow.name:
            issues.append("工作流缺少名称")

        # 检查节点ID唯一性 / Check node ID uniqueness
        node_ids = [n.id for n in workflow.nodes]
        if len(node_ids) != len(set(node_ids)):
            issues.append("存在重复的节点ID")

        # 检查边的引用 / Check edge references
        node_id_set = set(node_ids)
        for edge in workflow.edges:
            if edge.source_id not in node_id_set:
                issues.append(
                    f"边引用了不存在的源节点: {edge.source_id}"
                )
            if edge.target_id not in node_id_set:
                issues.append(
                    f"边引用了不存在的目标节点: {edge.target_id}"
                )

        # 检查循环依赖 / Check circular dependencies
        try:
            self._topological_sort(workflow)
        except WorkflowError as e:
            issues.append(str(e))

        # 检查孤立节点 / Check isolated nodes
        connected_nodes = set()
        for edge in workflow.edges:
            connected_nodes.add(edge.source_id)
            connected_nodes.add(edge.target_id)

        for node in workflow.nodes:
            if node.id not in connected_nodes and len(workflow.nodes) > 1:
                issues.append(
                    f"节点 '{node.name}' ({node.id}) 是孤立的"
                )

        return issues
