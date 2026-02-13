"""LLM 客户端。

核心业务逻辑，处理与 LLM API 的交互。
"""

import json
from typing import Any, Dict, List, Optional, Union

from src.adapters.base import LLMAdapter, LLMResponse
from src.config.models import OpenAIConfig, QwenConfig, ToolsConfig
from src.core.session import SessionManager
from src.tools.registry import get_registry
from src.utils.logging_web import get_request_logger

_logger = get_request_logger("src.core.client")


class LLMClient:
	"""LLM 客户端。"""

	def __init__(
		self,
		openai_config: Optional[OpenAIConfig] = None,
		tools_config: Optional[ToolsConfig] = None,
		metadata: Dict[str, str] = None,
		adapter: LLMAdapter = None,
		llm_provider: str = "openai",
		qwen_config: Optional[QwenConfig] = None,
	):
		"""初始化客户端。

		Args:
			openai_config: OpenAI 配置
			tools_config: 工具配置
			metadata: 元数据
			adapter: 自定义适配器（优先级最高）
			llm_provider: LLM 提供商名称
			qwen_config: Qwen 配置
		"""
		self.tools_config = tools_config
		self.metadata = metadata or {}

		# 初始化适配器
		if adapter is not None:
			self.adapter = adapter
		elif llm_provider == "qwen" and qwen_config is not None:
			from src.adapters.qwen import QwenClientAdapter
			self.adapter = QwenClientAdapter(qwen_config)
			self.config = qwen_config
		else:
			from src.adapters.openai import OpenAIClientAdapter
			self.adapter = OpenAIClientAdapter(openai_config)
			self.config = openai_config

		# 初始化会话
		system_message = getattr(self.config, 'system_message', 'You are a helpful assistant.')
		self.session = SessionManager(system_message, self.metadata)

		# 工具配置
		self.allowed_tools = set(tools_config.allowed_tools) if tools_config.allowed_tools else set()
		self.show_tool_calls = tools_config.show_tool_calls

	def chat(self, user_message: str) -> str:
		"""发送消息并获取回复（始终使用工具调用）。"""
		self.session.add_user(user_message)
		return self._chat_with_tools(user_message)

	def _chat_with_tools(self, user_message: str) -> str:
		"""带工具调用的对话。"""
		from src.cli.output import print_thinking, print_message, print_tool_call, print_tool_result, print_tool_error,print_error
		registry = get_registry()
		tool_schemas = registry.get_all_schemas()
		max_iterations = self.tools_config.max_tool_calls
		iteration = 0
		final_response = ""
		skill_contexts: Dict[str, Any] = {}

		while iteration < max_iterations:
			iteration += 1

			# 过滤可用工具
			available_schemas = [
				schema for schema in tool_schemas
				if schema['function']['name'] in self.allowed_tools
			]

			messages = self.session.get_messages()

			try:
				response = self.adapter.complete_auto(messages=messages, tools=available_schemas)

				# response 是 LLMResponse 类型
				tool_calls = response.tool_calls
				assistant_content = response.content

				# 获取思考内容并打印
				thinking_content = response.get_thinking_content()
				if thinking_content:
					print_thinking(thinking_content)

				# 处理工具调用响应
				if tool_calls:
					# 添加助手消息（带工具调用）
					self.session.add_assistant(
						assistant_content,
						tool_calls=[
							{
								"id": tc['id'],
								"type": "function",
								"function": {
									"name": tc['function']['name'],
									"arguments": tc['function']['arguments'],
								},
							}
							for tc in tool_calls
						]
					)

					# 执行工具调用
					for tool_call in tool_calls:
						tool_name = tool_call['function']['name']
						tool_args = json.loads(tool_call['function']['arguments'] or "{}")

						if self.show_tool_calls:
							print_tool_call(iteration, tool_name, tool_args)

						try:
							result = registry.execute(tool_name, **tool_args)

							# 处理技能工具
							if tool_name == "skill":
								try:
									result_dict = json.loads(result)
									skill_content = result_dict.get("content", "")
									skill_args = result_dict.get("args", {})
									skill_allowed = result_dict.get("allowed_tools", [])
									skill_name = tool_args.get("skill_name", "unknown")

									skill_contexts[skill_name] = {
										"content": skill_content,
										"allowed_tools": skill_allowed,
									}

									# 合并工具列表
									if skill_allowed:
										self.allowed_tools.update(skill_allowed)

									# 发送成功消息
									self.session.add_tool_result(
										tool_call['id'],
										tool_name,
										f"Skill '{skill_name}' executed successfully with args: {skill_args}"
									)

									# 发送技能内容
									if skill_content:
										self.session.add_user(skill_content)
										if self.show_tool_calls:
											print_tool_result(
												tool_name,
												skill_content[:100] + ('...' if len(skill_content) > 100 else '')
											)

									continue

								except json.JSONDecodeError:
									result_content = f"Failed to parse skill result: {result}"
							else:
								result_content = result

							if self.show_tool_calls:
								print_tool_result(tool_name, result_content)

							self.session.add_tool_result(tool_call['id'], tool_name, result_content)

						except ValueError as e:
							error_msg = f"Tool execution error: {str(e)}"
							if self.show_tool_calls:
								print_tool_error(error_msg)
							self.session.add_tool_result(tool_call['id'], tool_name, error_msg)

					continue

				else:
					# 最终响应
					final_response = assistant_content
					print_message(final_response)
					self.session.add_assistant(final_response)
					break

			except Exception as e:
				final_response = f"Error in chain execution: {str(e)}"
				if self.show_tool_calls:
					print_error(final_response)
				break
		else:
			final_response = "Maximum tool call iterations reached."
			if self.show_tool_calls:
				print_error(final_response)

		print()
		return final_response
