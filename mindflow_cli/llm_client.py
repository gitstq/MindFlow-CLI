"""
LLM客户端模块 / LLM Client Module

多LLM统一接口，支持OpenAI兼容API、Anthropic API和Ollama本地模型。
使用urllib进行HTTP请求，零外部依赖。
Unified multi-LLM interface supporting OpenAI-compatible API, Anthropic API,
and Ollama local models. Uses urllib for HTTP requests, zero external dependencies.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Generator, List, Optional


class LLMError(Exception):
    """LLM调用错误 / LLM call error"""
    pass


class LLMTimeoutError(LLMError):
    """LLM调用超时 / LLM call timeout"""
    pass


class LLMRateLimitError(LLMError):
    """LLM调用频率限制 / LLM call rate limit"""
    pass


class LLMResponse:
    """
    LLM响应对象 / LLM Response Object

    封装LLM的响应数据，包括内容、使用统计和原始响应。
    Wraps LLM response data including content, usage stats, and raw response.

    属性 / Attributes:
        content: 响应内容 / Response content
        model: 使用的模型 / Model used
        provider: 服务提供商 / Service provider
        usage: 使用统计 / Usage statistics
        raw_response: 原始响应数据 / Raw response data
        finish_reason: 完成原因 / Finish reason
    """

    def __init__(
        self,
        content: str = "",
        model: str = "",
        provider: str = "",
        usage: Optional[Dict[str, int]] = None,
        raw_response: Optional[Dict[str, Any]] = None,
        finish_reason: str = "",
    ) -> None:
        self.content = content
        self.model = model
        self.provider = provider
        self.usage = usage or {}
        self.raw_response = raw_response or {}
        self.finish_reason = finish_reason

    def __repr__(self) -> str:
        return (
            f"LLMResponse(model='{self.model}', "
            f"content_length={len(self.content)}, "
            f"finish_reason='{self.finish_reason}')"
        )


class LLMClient:
    """
    多LLM统一客户端 / Unified Multi-LLM Client

    提供统一的接口调用不同的LLM服务，支持流式响应和重试机制。
    Provides a unified interface to call different LLM services,
    supporting streaming responses and retry mechanisms.

    用法 / Usage:
        client = LLMClient()
        client.configure("openai", api_key="sk-...", model="gpt-3.5-turbo")
        response = client.chat("你好，请介绍一下Python")
        print(response.content)
    """

    def __init__(
        self,
        default_provider: str = "ollama",
        default_timeout: int = 60,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """
        初始化LLM客户端 / Initialize LLM client

        参数 / Args:
            default_provider: 默认提供商 / Default provider
            default_timeout: 默认超时（秒） / Default timeout (seconds)
            max_retries: 最大重试次数 / Maximum retry count
            retry_delay: 重试延迟（秒） / Retry delay (seconds)
        """
        self.default_provider = default_provider
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._providers: Dict[str, Dict[str, Any]] = {}

    def configure(
        self,
        provider: str,
        api_key: str = "",
        base_url: str = "",
        model: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        timeout: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """
        配置LLM提供商 / Configure LLM provider

        参数 / Args:
            provider: 提供商名称 ("openai", "anthropic", "ollama")
            api_key: API密钥 / API key
            base_url: API基础URL / API base URL
            model: 模型名称 / Model name
            max_tokens: 最大token数 / Maximum tokens
            temperature: 温度参数 / Temperature parameter
            timeout: 超时时间 / Timeout
            **kwargs: 其他参数 / Other parameters
        """
        config: Dict[str, Any] = {
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "timeout": timeout or self.default_timeout,
        }
        config.update(kwargs)
        self._providers[provider] = config

    def _get_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        获取提供商配置 / Get provider configuration

        参数 / Args:
            provider: 提供商名称 / Provider name

        返回 / Returns:
            配置字典 / Configuration dictionary
        """
        provider = provider or self.default_provider
        config = self._providers.get(provider, {})
        if not config:
            raise LLMError(f"提供商 '{provider}' 未配置")
        return config

    def _make_request(
        self,
        url: str,
        data: Dict[str, Any],
        headers: Dict[str, str],
        timeout: int,
        method: str = "POST",
    ) -> Dict[str, Any]:
        """
        发送HTTP请求 / Send HTTP request

        参数 / Args:
            url: 请求URL / Request URL
            data: 请求数据 / Request data
            headers: 请求头 / Request headers
            timeout: 超时时间 / Timeout
            method: HTTP方法 / HTTP method

        返回 / Returns:
            响应JSON / Response JSON

        异常 / Raises:
            LLMTimeoutError: 请求超时 / Request timeout
            LLMRateLimitError: 频率限制 / Rate limit
            LLMError: 其他错误 / Other errors
        """
        encoded_data = json.dumps(data).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=encoded_data,
            headers=headers,
            method=method,
        )

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    response_data = response.read().decode("utf-8")
                    return json.loads(response_data)

            except urllib.error.HTTPError as e:
                if e.code == 429:
                    # 频率限制，等待后重试 / Rate limit, wait and retry
                    retry_after = e.headers.get("Retry-After", str(self.retry_delay * (attempt + 1)))
                    try:
                        wait_time = float(retry_after)
                    except ValueError:
                        wait_time = self.retry_delay * (attempt + 1)

                    if attempt < self.max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    raise LLMRateLimitError(
                        f"请求频率受限，请稍后重试 (HTTP {e.code})"
                    )

                error_body = ""
                try:
                    error_body = e.read().decode("utf-8")
                except Exception:
                    pass

                raise LLMError(
                    f"HTTP错误 {e.code}: {e.reason}\n{error_body}"
                )

            except urllib.error.URLError as e:
                if "timed out" in str(e.reason).lower():
                    raise LLMTimeoutError(
                        f"请求超时 ({timeout}秒): {e.reason}"
                    )
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise LLMError(f"网络错误: {e.reason}")

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise LLMError(f"请求失败: {e}")

        raise LLMError(f"请求失败，已重试 {self.max_retries} 次: {last_error}")

    def _make_stream_request(
        self,
        url: str,
        data: Dict[str, Any],
        headers: Dict[str, str],
        timeout: int,
    ) -> Generator[str, None, None]:
        """
        发送流式HTTP请求 / Send streaming HTTP request

        参数 / Args:
            url: 请求URL / Request URL
            data: 请求数据 / Request data
            headers: 请求头 / Request headers
            timeout: 超时时间 / Timeout

        生成 / Yields:
            流式响应文本块 / Streamed response text chunks
        """
        encoded_data = json.dumps(data).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=encoded_data,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                buffer = ""
                while True:
                    chunk = response.read(1)
                    if not chunk:
                        break
                    decoded = chunk.decode("utf-8", errors="replace")
                    buffer += decoded

                    # 处理SSE格式 / Handle SSE format
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()

                        if not line or line.startswith(":"):
                            continue

                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                return

                            try:
                                event_data = json.loads(data_str)
                                content = self._extract_stream_content(event_data)
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue

        except urllib.error.URLError as e:
            if "timed out" in str(e.reason).lower():
                raise LLMTimeoutError(f"流式请求超时: {e.reason}")
            raise LLMError(f"流式请求失败: {e.reason}")

    def _extract_stream_content(self, event_data: Dict[str, Any]) -> str:
        """
        从流式事件中提取内容 / Extract content from stream event

        参数 / Args:
            event_data: 事件数据 / Event data

        返回 / Returns:
            文本内容 / Text content
        """
        # OpenAI格式 / OpenAI format
        if "choices" in event_data:
            choices = event_data["choices"]
            if choices and isinstance(choices, list):
                delta = choices[0].get("delta", {})
                return delta.get("content", "")

        # Anthropic格式 / Anthropic format
        if "type" in event_data:
            if event_data["type"] == "content_block_delta":
                delta = event_data.get("delta", {})
                return delta.get("text", "")
            elif event_data["type"] == "message_delta":
                return ""

        # Ollama格式 / Ollama format
        if "response" in event_data:
            return event_data.get("response", "")

        return ""

    # ============================================================
    # OpenAI兼容API / OpenAI-Compatible API
    # ============================================================

    def _chat_openai(
        self,
        messages: List[Dict[str, str]],
        config: Dict[str, Any],
        stream: bool = False,
    ) -> LLMResponse:
        """
        调用OpenAI兼容API / Call OpenAI-compatible API

        参数 / Args:
            messages: 消息列表 / List of messages
            config: 配置 / Configuration
            stream: 是否流式 / Whether to stream

        返回 / Returns:
            LLM响应 / LLM response
        """
        base_url = config["base_url"].rstrip("/")
        url = f"{base_url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
        }
        if config.get("api_key"):
            headers["Authorization"] = f"Bearer {config['api_key']}"

        payload: Dict[str, Any] = {
            "model": config["model"],
            "messages": messages,
            "max_tokens": config.get("max_tokens", 2048),
            "temperature": config.get("temperature", 0.7),
            "stream": stream,
        }

        if stream:
            full_content = ""
            for chunk in self._make_stream_request(
                url, payload, headers, config["timeout"]
            ):
                full_content += chunk
            return LLMResponse(
                content=full_content,
                model=config["model"],
                provider="openai",
            )

        response_data = self._make_request(
            url, payload, headers, config["timeout"]
        )

        content = ""
        if "choices" in response_data and response_data["choices"]:
            content = response_data["choices"][0].get("message", {}).get("content", "")

        return LLMResponse(
            content=content,
            model=response_data.get("model", config["model"]),
            provider="openai",
            usage=response_data.get("usage", {}),
            raw_response=response_data,
            finish_reason=(
                response_data["choices"][0].get("finish_reason", "")
                if response_data.get("choices")
                else ""
            ),
        )

    # ============================================================
    # Anthropic API / Anthropic API
    # ============================================================

    def _chat_anthropic(
        self,
        messages: List[Dict[str, str]],
        config: Dict[str, Any],
        stream: bool = False,
    ) -> LLMResponse:
        """
        调用Anthropic API / Call Anthropic API

        参数 / Args:
            messages: 消息列表 / List of messages
            config: 配置 / Configuration
            stream: 是否流式 / Whether to stream

        返回 / Returns:
            LLM响应 / LLM response
        """
        base_url = config["base_url"].rstrip("/")
        url = f"{base_url}/messages"

        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        if config.get("api_key"):
            headers["x-api-key"] = config["api_key"]

        # 分离system消息 / Separate system messages
        system_text = ""
        chat_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_text += msg.get("content", "") + "\n"
            else:
                chat_messages.append(msg)

        payload: Dict[str, Any] = {
            "model": config["model"],
            "messages": chat_messages,
            "max_tokens": config.get("max_tokens", 2048),
            "temperature": config.get("temperature", 0.7),
            "stream": stream,
        }

        if system_text.strip():
            payload["system"] = system_text.strip()

        if stream:
            full_content = ""
            for chunk in self._make_stream_request(
                url, payload, headers, config["timeout"]
            ):
                full_content += chunk
            return LLMResponse(
                content=full_content,
                model=config["model"],
                provider="anthropic",
            )

        response_data = self._make_request(
            url, payload, headers, config["timeout"]
        )

        content = ""
        if "content" in response_data and response_data["content"]:
            content = " ".join(
                block.get("text", "")
                for block in response_data["content"]
                if block.get("type") == "text"
            )

        return LLMResponse(
            content=content,
            model=response_data.get("model", config["model"]),
            provider="anthropic",
            usage=response_data.get("usage", {}),
            raw_response=response_data,
            finish_reason=response_data.get("stop_reason", ""),
        )

    # ============================================================
    # Ollama API / Ollama API
    # ============================================================

    def _chat_ollama(
        self,
        messages: List[Dict[str, str]],
        config: Dict[str, Any],
        stream: bool = False,
    ) -> LLMResponse:
        """
        调用Ollama本地模型API / Call Ollama local model API

        参数 / Args:
            messages: 消息列表 / List of messages
            config: 配置 / Configuration
            stream: 是否流式 / Whether to stream

        返回 / Returns:
            LLM响应 / LLM response
        """
        base_url = config["base_url"].rstrip("/")
        url = f"{base_url}/api/chat"

        headers = {
            "Content-Type": "application/json",
        }

        payload: Dict[str, Any] = {
            "model": config["model"],
            "messages": messages,
            "stream": stream,
            "options": {
                "num_predict": config.get("max_tokens", 2048),
                "temperature": config.get("temperature", 0.7),
            },
        }

        if stream:
            full_content = ""
            for chunk in self._make_stream_request(
                url, payload, headers, config["timeout"]
            ):
                full_content += chunk
            return LLMResponse(
                content=full_content,
                model=config["model"],
                provider="ollama",
            )

        response_data = self._make_request(
            url, payload, headers, config["timeout"]
        )

        return LLMResponse(
            content=response_data.get("message", {}).get("content", ""),
            model=response_data.get("model", config["model"]),
            provider="ollama",
            usage={
                "prompt_tokens": response_data.get("prompt_eval_count", 0),
                "completion_tokens": response_data.get("eval_count", 0),
                "total_tokens": (
                    response_data.get("prompt_eval_count", 0)
                    + response_data.get("eval_count", 0)
                ),
            },
            raw_response=response_data,
            finish_reason=response_data.get("done_reason", ""),
        )

    # ============================================================
    # 统一接口 / Unified Interface
    # ============================================================

    def chat(
        self,
        message: str,
        system_prompt: str = "",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> LLMResponse:
        """
        统一聊天接口 / Unified chat interface

        参数 / Args:
            message: 用户消息 / User message
            system_prompt: 系统提示 / System prompt
            provider: 提供商（可选） / Provider (optional)
            model: 模型名称（可选） / Model name (optional)
            temperature: 温度参数（可选） / Temperature (optional)
            max_tokens: 最大token数（可选） / Max tokens (optional)
            stream: 是否流式 / Whether to stream
            conversation_history: 对话历史 / Conversation history

        返回 / Returns:
            LLM响应 / LLM response
        """
        config = dict(self._get_config(provider))

        # 覆盖配置 / Override config
        if model:
            config["model"] = model
        if temperature is not None:
            config["temperature"] = temperature
        if max_tokens is not None:
            config["max_tokens"] = max_tokens

        # 构建消息列表 / Build message list
        messages: List[Dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": message})

        # 根据提供商调用 / Call based on provider
        provider_name = provider or self.default_provider

        if provider_name == "anthropic":
            return self._chat_anthropic(messages, config, stream)
        elif provider_name == "ollama":
            return self._chat_ollama(messages, config, stream)
        else:
            # 默认使用OpenAI兼容接口 / Default to OpenAI-compatible interface
            return self._chat_openai(messages, config, stream)

    def chat_stream(
        self,
        message: str,
        system_prompt: str = "",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Generator[str, None, None]:
        """
        流式聊天接口 / Streaming chat interface

        参数 / Args:
            message: 用户消息 / User message
            system_prompt: 系统提示 / System prompt
            provider: 提供商（可选） / Provider (optional)
            model: 模型名称（可选） / Model name (optional)
            temperature: 温度参数（可选） / Temperature (optional)
            max_tokens: 最大token数（可选） / Max tokens (optional)
            conversation_history: 对话历史 / Conversation history

        生成 / Yields:
            流式响应文本块 / Streamed response text chunks
        """
        config = dict(self._get_config(provider))

        if model:
            config["model"] = model
        if temperature is not None:
            config["temperature"] = temperature
        if max_tokens is not None:
            config["max_tokens"] = max_tokens

        messages: List[Dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": message})

        provider_name = provider or self.default_provider
        base_url = config["base_url"].rstrip("/")

        if provider_name == "anthropic":
            url = f"{base_url}/messages"
            headers = {
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            }
            if config.get("api_key"):
                headers["x-api-key"] = config["api_key"]

            system_text = ""
            chat_messages = []
            for msg in messages:
                if msg.get("role") == "system":
                    system_text += msg.get("content", "") + "\n"
                else:
                    chat_messages.append(msg)

            payload = {
                "model": config["model"],
                "messages": chat_messages,
                "max_tokens": config.get("max_tokens", 2048),
                "temperature": config.get("temperature", 0.7),
                "stream": True,
            }
            if system_text.strip():
                payload["system"] = system_text.strip()

        elif provider_name == "ollama":
            url = f"{base_url}/api/chat"
            headers = {"Content-Type": "application/json"}
            payload = {
                "model": config["model"],
                "messages": messages,
                "stream": True,
                "options": {
                    "num_predict": config.get("max_tokens", 2048),
                    "temperature": config.get("temperature", 0.7),
                },
            }
        else:
            url = f"{base_url}/chat/completions"
            headers = {"Content-Type": "application/json"}
            if config.get("api_key"):
                headers["Authorization"] = f"Bearer {config['api_key']}"
            payload = {
                "model": config["model"],
                "messages": messages,
                "max_tokens": config.get("max_tokens", 2048),
                "temperature": config.get("temperature", 0.7),
                "stream": True,
            }

        for chunk in self._make_stream_request(url, payload, headers, config["timeout"]):
            yield chunk

    def list_models(self, provider: Optional[str] = None) -> List[str]:
        """
        列出可用模型 / List available models

        参数 / Args:
            provider: 提供商名称 / Provider name

        返回 / Returns:
            模型名称列表 / List of model names
        """
        config = self._get_config(provider)
        provider_name = provider or self.default_provider
        base_url = config["base_url"].rstrip("/")

        try:
            if provider_name == "ollama":
                url = f"{base_url}/api/tags"
                headers = {}
                response_data = self._make_request(url, {}, headers, config["timeout"])
                return [m["name"] for m in response_data.get("models", [])]
            elif provider_name == "openai":
                url = f"{base_url}/models"
                headers = {"Content-Type": "application/json"}
                if config.get("api_key"):
                    headers["Authorization"] = f"Bearer {config['api_key']}"
                response_data = self._make_request(
                    url, {}, headers, config["timeout"], method="GET"
                )
                return [m["id"] for m in response_data.get("data", [])]
            else:
                return [config.get("model", "unknown")]
        except LLMError:
            return [config.get("model", "unknown")]

    def is_available(self, provider: Optional[str] = None) -> bool:
        """
        检查LLM服务是否可用 / Check if LLM service is available

        参数 / Args:
            provider: 提供商名称 / Provider name

        返回 / Returns:
            是否可用 / Whether available
        """
        try:
            models = self.list_models(provider)
            return len(models) > 0
        except Exception:
            return False
