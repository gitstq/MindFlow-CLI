"""
配置管理模块 / Configuration Management Module

管理MindFlow-CLI的全局配置，包括LLM API设置、搜索参数和通用选项。
使用JSON格式存储配置文件，不依赖外部YAML库。
Manages MindFlow-CLI global configuration including LLM API settings,
search parameters, and general options. Uses JSON format for config files.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


# 默认配置目录名 / Default config directory name
CONFIG_DIR_NAME = ".mindflow"
CONFIG_FILE_NAME = "config.json"
DATABASE_FILE_NAME = "mindflow.db"
EXPORTS_DIR_NAME = "exports"
TEMPLATES_DIR_NAME = "templates"


class Config:
    """
    配置管理器 / Configuration Manager

    负责加载、保存和管理MindFlow-CLI的所有配置项。
    Responsible for loading, saving, and managing all MindFlow-CLI configuration items.

    属性 / Attributes:
        config_dir: 配置目录路径 / Config directory path
        config_path: 配置文件路径 / Config file path
        database_path: 数据库文件路径 / Database file path
        exports_dir: 导出目录路径 / Exports directory path
        templates_dir: 模板目录路径 / Templates directory path
    """

    def __init__(self, config_dir: Optional[str] = None) -> None:
        """
        初始化配置管理器 / Initialize configuration manager

        参数 / Args:
            config_dir: 自定义配置目录路径 / Custom config directory path
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / CONFIG_DIR_NAME

        self.config_path = self.config_dir / CONFIG_FILE_NAME
        self.database_path = self.config_dir / DATABASE_FILE_NAME
        self.exports_dir = self.config_dir / EXPORTS_DIR_NAME
        self.templates_dir = self.config_dir / TEMPLATES_DIR_NAME

        self._data: Dict[str, Any] = {}
        self._load()

    def _get_defaults(self) -> Dict[str, Any]:
        """
        获取默认配置 / Get default configuration

        返回 / Returns:
            默认配置字典 / Default configuration dictionary
        """
        return {
            "version": "1.0.0",
            "general": {
                "language": "zh-CN",
                "editor": "",
                "default_export_format": "markdown",
                "max_snippet_length": 100000,
                "auto_save": True,
                "log_level": "INFO",
            },
            "llm": {
                "default_provider": "ollama",
                "openai": {
                    "api_key": "",
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "timeout": 60,
                },
                "anthropic": {
                    "api_key": "",
                    "base_url": "https://api.anthropic.com/v1",
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "timeout": 60,
                },
                "ollama": {
                    "base_url": "http://localhost:11434",
                    "model": "llama3",
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "timeout": 120,
                },
            },
            "search": {
                "algorithm": "bm25",
                "min_score": 0.1,
                "max_results": 20,
                "chinese_ngram_size": 2,
                "enable_stemming": False,
                "highlight_matches": True,
            },
            "workflow": {
                "max_parallel": 4,
                "retry_count": 3,
                "retry_delay": 5,
                "timeout": 300,
                "log_execution": True,
            },
            "tui": {
                "theme": "default",
                "keybinding": "default",
                "refresh_interval": 1,
            },
        }

    def _load(self) -> None:
        """
        从文件加载配置 / Load configuration from file

        如果配置文件不存在，使用默认配置。
        Uses default configuration if config file doesn't exist.
        """
        self._data = self._get_defaults()

        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                self._deep_merge(self._data, user_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"警告: 配置文件加载失败，使用默认配置: {e}")

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """
        深度合并字典 / Deep merge dictionaries

        参数 / Args:
            base: 基础字典 / Base dictionary
            override: 覆盖字典 / Override dictionary

        返回 / Returns:
            合并后的字典 / Merged dictionary
        """
        for key, value in override.items():
            if (
                key in base
                and isinstance(base[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def save(self) -> None:
        """
        保存配置到文件 / Save configuration to file

        确保配置目录存在后再写入。
        Ensures config directory exists before writing.
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise RuntimeError(f"配置文件保存失败: {e}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值 / Get configuration value

        支持点号分隔的嵌套路径，如 "llm.openai.api_key"。
        Supports dot-separated nested paths, e.g. "llm.openai.api_key".

        参数 / Args:
            key_path: 配置键路径 / Configuration key path
            default: 默认值 / Default value

        返回 / Returns:
            配置值 / Configuration value
        """
        keys = key_path.split(".")
        value = self._data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path: str, value: Any) -> None:
        """
        设置配置值 / Set configuration value

        参数 / Args:
            key_path: 配置键路径 / Configuration key path
            value: 配置值 / Configuration value
        """
        keys = key_path.split(".")
        data = self._data
        for key in keys[:-1]:
            if key not in data or not isinstance(data[key], dict):
                data[key] = {}
            data = data[key]
        data[keys[-1]] = value

    def delete(self, key_path: str) -> bool:
        """
        删除配置项 / Delete configuration item

        参数 / Args:
            key_path: 配置键路径 / Configuration key path

        返回 / Returns:
            是否成功删除 / Whether successfully deleted
        """
        keys = key_path.split(".")
        data = self._data
        for key in keys[:-1]:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return False

        if isinstance(data, dict) and keys[-1] in data:
            del data[keys[-1]]
            return True
        return False

    def is_initialized(self) -> bool:
        """
        检查是否已初始化 / Check if initialized

        返回 / Returns:
            配置目录和数据库是否存在 / Whether config dir and database exist
        """
        return self.config_dir.exists() and self.database_path.exists()

    def initialize(self) -> None:
        """
        初始化项目 / Initialize project

        创建配置目录、导出目录、模板目录和默认配置文件。
        Creates config directory, exports directory, templates directory,
        and default configuration file.
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.save()

    # ============================================================
    # LLM配置快捷方法 / LLM Configuration Shortcuts
    # ============================================================

    def get_llm_provider(self) -> str:
        """获取默认LLM提供商 / Get default LLM provider"""
        return self.get("llm.default_provider", "ollama")

    def get_llm_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        获取LLM配置 / Get LLM configuration

        参数 / Args:
            provider: 提供商名称（可选） / Provider name (optional)

        返回 / Returns:
            LLM配置字典 / LLM configuration dictionary
        """
        provider = provider or self.get_llm_provider()
        return self.get(f"llm.{provider}", {})

    def set_llm_api_key(self, provider: str, api_key: str) -> None:
        """
        设置LLM API密钥 / Set LLM API key

        参数 / Args:
            provider: 提供商名称 / Provider name
            api_key: API密钥 / API key
        """
        self.set(f"llm.{provider}.api_key", api_key)

    def set_llm_model(self, provider: str, model: str) -> None:
        """
        设置LLM模型 / Set LLM model

        参数 / Args:
            provider: 提供商名称 / Provider name
            model: 模型名称 / Model name
        """
        self.set(f"llm.{provider}.model", model)

    def set_llm_base_url(self, provider: str, base_url: str) -> None:
        """
        设置LLM API基础URL / Set LLM API base URL

        参数 / Args:
            provider: 提供商名称 / Provider name
            base_url: 基础URL / Base URL
        """
        self.set(f"llm.{provider}.base_url", base_url)

    # ============================================================
    # 搜索配置快捷方法 / Search Configuration Shortcuts
    # ============================================================

    def get_search_config(self) -> Dict[str, Any]:
        """获取搜索配置 / Get search configuration"""
        return self.get("search", {})

    def get_max_search_results(self) -> int:
        """获取最大搜索结果数 / Get max search results"""
        return self.get("search.max_results", 20)

    # ============================================================
    # 工作流配置快捷方法 / Workflow Configuration Shortcuts
    # ============================================================

    def get_workflow_config(self) -> Dict[str, Any]:
        """获取工作流配置 / Get workflow configuration"""
        return self.get("workflow", {})

    # ============================================================
    # 导出 / Export
    # ============================================================

    def to_dict(self) -> Dict[str, Any]:
        """导出完整配置为字典 / Export full configuration as dictionary"""
        return dict(self._data)

    def __repr__(self) -> str:
        return f"Config(config_dir='{self.config_dir}')"
