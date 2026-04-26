"""AI 写作助手服务

本模块提供 AI 写作助手功能，使用 threading.Thread 处理网络请求以避免 QThread 网络挂起问题。

主要组件：
- AiServiceConfig: AI 服务配置类
- AiWorker: 后台 AI 请求工作线程
- 各种 build_*_messages 函数: 构建不同场景的提示词

Example:
    >>> config = AiServiceConfig(
    ...     api_url="https://api.example.com",
    ...     api_key="your-key",
    ...     model="gpt-4"
    ... )
    >>> messages = build_optimize_messages("需要优化的文本")
    >>> worker = AiWorker(messages, config=config)
    >>> worker.chunk_received.connect(lambda chunk: print(chunk))
    >>> worker.start()
"""

import configparser
import json
import logging
import os
import queue
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import requests
from PyQt6.QtCore import QThread, pyqtSignal

from .exceptions import (
    AiApiError,
    AiConfigError,
    AiServiceError,
    AiTimeoutError,
)

logger = logging.getLogger(__name__)

# 网络配置常量
API_TIMEOUT = 60
API_MAX_RETRIES = 5  # 增加到 5 次，适应 llm.nodai.design 的冷却策略
API_RETRY_BACKOFF = 3  # 增加到 3 秒，给 API 更多冷却时间

# 默认配置
DEFAULT_API_URL = "https://llm.nodai.design/v1/chat/completions"
DEFAULT_MODEL = "gpt-5.3-codex"


@dataclass
class AiServiceConfig:
    """AI 服务配置类

    封装 AI 服务的所有配置参数，避免使用全局变量。

    Attributes:
        api_url: AI API 端点 URL
        api_key: API 密钥
        model: 使用的模型名称
        timeout: 请求超时时间（秒）
        max_retries: 最大重试次数
        retry_backoff: 重试退避时间（秒）

    Example:
        >>> config = AiServiceConfig(
        ...     api_url="https://api.example.com",
        ...     api_key="sk-xxx",
        ...     model="gpt-4"
        ... )
    """

    api_url: str = DEFAULT_API_URL
    api_key: str = ""
    model: str = DEFAULT_MODEL
    timeout: int = API_TIMEOUT
    max_retries: int = API_MAX_RETRIES
    retry_backoff: int = API_RETRY_BACKOFF


# 全局默认配置实例（用于向后兼容）
_default_config = AiServiceConfig()


def configure_ai(api_url: str = "", model: str = "", api_key: Optional[str] = None) -> None:
    """配置全局默认 AI 服务设置（向后兼容接口）

    注意：建议使用 AiServiceConfig 类创建配置对象，而不是使用此全局函数。

    Args:
        api_url: API 端点 URL（可选）
        model: 模型名称（可选）
        api_key: API 密钥（可选，None 表示不修改）

    Example:
        >>> configure_ai(api_url="https://api.example.com", model="gpt-4")
    """
    global _default_config
    if api_url:
        _default_config.api_url = api_url
    if model:
        _default_config.model = model
    if api_key is not None:
        _default_config.api_key = api_key
        if api_key:
            os.environ["WENBIAO_AI_API_KEY"] = api_key
        else:
            os.environ.pop("WENBIAO_AI_API_KEY", None)


def get_ai_api_key() -> str:
    """从环境变量或 config.ini 读取 AI API Key

    按以下优先级查找 API Key：
    1. WENBIAO_AI_API_KEY 环境变量
    2. AI_API_KEY 环境变量
    3. OPENAI_API_KEY 环境变量
    4. config.ini 文件中的 [AI] api_key 配置

    Returns:
        API Key 字符串，如果未找到则返回空字符串

    Example:
        >>> key = get_ai_api_key()
        >>> if not key:
        ...     print("未配置 API Key")
    """
    # 优先从环境变量读取
    key = os.getenv("WENBIAO_AI_API_KEY") or os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if key:
        return key

    # 从 config.ini 读取
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    config_path = os.path.join(base_dir, "config.ini")
    if os.path.isfile(config_path):
        cfg = configparser.ConfigParser()
        try:
            cfg.read(config_path, encoding="utf-8")
            key = cfg.get("AI", "api_key", fallback="").strip()
            if key:
                return key
        except (configparser.Error, UnicodeDecodeError) as e:
            logger.warning(f"读取 config.ini 失败: {e}")

    return ""


class AiWorker(QThread):
    """在后台线程中执行 AI API 调用

    使用 threading.Thread 处理网络请求以避免 QThread 的网络挂起问题。
    通过 PyQt 信号机制实现线程安全的结果传递。

    Signals:
        chunk_received: 接收到内容块时发射 (str)
        reasoning_received: 接收到推理内容时发射 (str)
        finished_ok: 请求成功完成时发射 (str)
        error_occurred: 发生错误时发射 (str)
        status_update: 状态更新时发射 (str)

    Attributes:
        _messages: 对话消息列表
        _config: AI 服务配置
        _max_tokens: 最大生成 token 数
        _temperature: 温度参数（0-1）
        _cancelled: 是否已取消
        _result: 完整响应结果
        _error: 错误信息
        _done: 完成事件
        _chunk_queue: 数据块队列

    Example:
        >>> config = AiServiceConfig(api_key="sk-xxx")
        >>> messages = [{"role": "user", "content": "Hello"}]
        >>> worker = AiWorker(messages, config=config)
        >>> worker.chunk_received.connect(lambda chunk: print(chunk))
        >>> worker.error_occurred.connect(lambda err: print(f"Error: {err}"))
        >>> worker.start()
    """

    chunk_received = pyqtSignal(str)
    reasoning_received = pyqtSignal(str)
    finished_ok = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    status_update = pyqtSignal(str)

    def __init__(
        self,
        messages: List[Dict[str, str]],
        parent=None,
        max_tokens: int = 8192,
        temperature: float = 0.5,
        config: Optional[AiServiceConfig] = None,
    ):
        """初始化 AI 工作线程

        Args:
            messages: 对话消息列表，每个消息包含 role 和 content
            parent: 父对象（可选）
            max_tokens: 最大生成 token 数
            temperature: 温度参数，控制随机性（0-1）
            config: AI 服务配置，如果为 None 则使用全局默认配置
        """
        super().__init__(parent)
        self._messages = messages
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._config = config or _default_config
        self._cancelled = False
        self._result = None
        self._error = None
        self._done = threading.Event()
        self._chunk_queue = queue.Queue()

    def cancel(self) -> None:
        """取消当前请求

        设置取消标志，网络线程会在下一次检查时停止。
        """
        self._cancelled = True

    def _network_thread(self) -> None:
        """在 Python threading.Thread 中执行网络请求

        此方法在独立的 Python 线程中运行，避免 QThread 的网络挂起问题。
        实现了自动重试和指数退避策略。

        Raises:
            不会抛出异常，所有错误都通过 _error 属性传递
        """
        try:
            # 获取 API Key
            api_key = self._config.api_key or get_ai_api_key()
            if not api_key:
                self._error = "未配置 AI API Key"
                self._done.set()
                return

            # 构建请求负载
            payload = {
                "model": self._config.model,
                "messages": self._messages,
                "stream": True,
                "temperature": self._temperature,
                "max_tokens": self._max_tokens,
                "stream_options": {"include_usage": True},
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "Accept": "text/event-stream",
            }

            # 创建会话，禁用代理以避免超时
            session = requests.Session()
            session.trust_env = False

            last_error = None

            # 重试循环
            for attempt in range(1, self._config.max_retries + 1):
                if self._cancelled:
                    self._done.set()
                    return

                try:
                    # 指数退避
                    if attempt > 1:
                        backoff_time = self._config.retry_backoff * (attempt - 1)
                        logger.info(f"重试第 {attempt} 次，等待 {backoff_time} 秒")
                        time.sleep(backoff_time)

                    # 发送请求
                    response = session.post(
                        self._config.api_url,
                        json=payload,
                        headers=headers,
                        timeout=self._config.timeout,
                        stream=True,
                    )
                    response.raise_for_status()

                    # 流式读取响应
                    full_response = []

                    for line_bytes in response.iter_lines():
                        if self._cancelled:
                            break
                        if not line_bytes:
                            continue

                        line = line_bytes.decode("utf-8", errors="replace").strip()
                        if not line or not line.startswith("data: "):
                            continue

                        line = line[6:]  # 移除 "data: " 前缀
                        if line == "[DONE]":
                            break

                        try:
                            chunk_data = json.loads(line)
                            if not isinstance(chunk_data, dict):
                                continue

                            # 提取内容
                            delta = chunk_data.get("choices", [{}])[0].get("delta", {})

                            # 推理内容
                            reasoning = delta.get("reasoning_content") or delta.get("reasoning", "")
                            if reasoning:
                                self._chunk_queue.put(("reasoning", reasoning))

                            # 正文内容
                            content = delta.get("content", "")
                            if content:
                                full_response.append(content)
                                self._chunk_queue.put(("content", content))

                        except (
                            json.JSONDecodeError,
                            IndexError,
                            KeyError,
                            AttributeError,
                            TypeError,
                        ) as e:
                            logger.debug(f"解析响应块失败: {e}")
                            continue

                    # 请求成功
                    self._result = "".join(full_response)
                    self._done.set()
                    return

                except requests.exceptions.HTTPError as e:
                    status_code = e.response.status_code

                    # 特殊处理 429 错误（请求过多）
                    if status_code == 429:
                        # 尝试从响应中获取详细错误信息
                        try:
                            error_detail = e.response.json().get("error", {})
                            error_msg = error_detail.get("message", "")
                        except:
                            error_msg = ""

                        # 判断是否是模型冷却
                        is_cooling = "cooling down" in error_msg.lower()

                        if is_cooling:
                            # 模型冷却期，需要更长的等待时间
                            last_error = (
                                f"模型正在冷却中\n"
                                f"原因：{error_msg}\n"
                                f"这是正常的限流保护机制，请稍候..."
                            )
                            # 冷却期等待时间更长（指数退避 × 3）
                            if attempt < self._config.max_retries:
                                backoff_time = self._config.retry_backoff * attempt * 3
                                logger.info(f"模型冷却中，等待 {backoff_time} 秒后重试")
                                time.sleep(backoff_time)
                        else:
                            # 普通限流
                            last_error = (
                                f"API 请求频率限制 (HTTP 429)\n"
                                f"原因：{error_msg or '请求过于频繁'}\n"
                                f"正在自动重试..."
                            )
                            # 普通限流等待时间（指数退避 × 2）
                            if attempt < self._config.max_retries:
                                backoff_time = self._config.retry_backoff * attempt * 2
                                logger.info(f"429 错误，等待 {backoff_time} 秒后重试")
                                time.sleep(backoff_time)

                        logger.warning(f"{last_error}, 尝试 {attempt}/{self._config.max_retries}")
                    else:
                        last_error = f"API 请求失败 (HTTP {status_code})"
                        logger.warning(f"{last_error}, 尝试 {attempt}/{self._config.max_retries}")

                        # 其他 4xx 错误不重试
                        if 400 <= status_code < 500:
                            break

                except requests.exceptions.Timeout:
                    last_error = f"连接超时（{self._config.timeout}秒）"
                    logger.warning(f"{last_error}, 尝试 {attempt}/{self._config.max_retries}")

                except requests.exceptions.RequestException as e:
                    last_error = f"网络连接失败: {str(e)}"
                    logger.warning(f"{last_error}, 尝试 {attempt}/{self._config.max_retries}")

            # 所有重试都失败
            self._error = last_error or "AI 服务异常"
            self._done.set()

        except Exception as e:
            logger.exception("[AiWorker] 网络线程意外错误")
            self._error = f"AI 服务异常: {str(e)}"
            self._done.set()

    def run(self) -> None:
        """QThread 主循环

        启动网络线程并处理数据块队列，将结果通过信号发送到主线程。
        """
        try:
            # 启动网络线程
            network_thread = threading.Thread(target=self._network_thread, daemon=True)
            network_thread.start()

            # 等待网络线程完成，同时处理队列中的数据块
            while not self._done.is_set():
                if self._cancelled:
                    return

                try:
                    msg_type, data = self._chunk_queue.get(timeout=0.1)
                    if msg_type == "content":
                        self.chunk_received.emit(data)
                    elif msg_type == "reasoning":
                        self.reasoning_received.emit(data)
                except queue.Empty:
                    pass

            # 处理队列中剩余的数据块
            while not self._chunk_queue.empty():
                try:
                    msg_type, data = self._chunk_queue.get_nowait()
                    if msg_type == "content":
                        self.chunk_received.emit(data)
                    elif msg_type == "reasoning":
                        self.reasoning_received.emit(data)
                except queue.Empty:
                    break

            # 发射结果信号
            if self._error:
                self.error_occurred.emit(self._error)
            elif self._result is not None:
                self.finished_ok.emit(self._result)

        except Exception as e:
            logger.exception("[AiWorker] QThread 错误")
            self.error_occurred.emit(f"AI 服务异常: {str(e)}")


# ============================================================================
# Prompt 规则片段和系统提示词
# ============================================================================

# Prompt 规则片段
_IMAGE_SEARCH_RULES = "插图:仅真实物体,![alt](IMAGE_SEARCH:英文3-5词),全文≤3张\n"
_RICH_TEXT_RULES = "富文本(用户要求时):[COLOR:#hex]文[/COLOR] [FONT:SimHei]文[/FONT] [SIZE:16px]文[/SIZE] [STYLE color=# font= size=]文[/STYLE]\n"
_FORMULA_RULES = "数学内容用LaTeX($行内$ $$块级$$)\n"
_ACADEMIC_DEPTH_RULES = "约束:观点→证据→推理;每段含具体信息;仅引真实文献,不编造\n"
_CHART_TYPES_DESC = '图表:[CHART:类型:{"title":"..","labels":[..],"series":[{"name":"..","values":[..]}]}]\n类型:bar/line/pie/area/radar/scatter/grouped/stacked/funnel/gauge/heatmap/donut等\n'

# 系统提示词
SYSTEM_PROMPT_OPTIMIZE = (
    "学术论文助手,Markdown输出。优化文本:"
    "修正语���错字标点,提升学术性,保持原意格式,直接返回无解释\n"
    f"{_ACADEMIC_DEPTH_RULES}"
    f"{_FORMULA_RULES}"
)

SYSTEM_PROMPT_CONTINUE = (
    "学术论文助手,Markdown输出。续写论文:"
    "衔接上文,学术语言,1500-3000字,充分论据,直接输出无提示语,数据用表格,引用真实文献\n"
    f"{_ACADEMIC_DEPTH_RULES}"
    f"{_FORMULA_RULES}"
    f"{_CHART_TYPES_DESC}"
    f"{_IMAGE_SEARCH_RULES}"
)

SYSTEM_PROMPT_CUSTOM_EDIT = (
    "学术论文助手,Markdown输出。按指令修改选中文本:"
    "只返回修改后内容无解释,保留未改部分,润色提升学术性,扩写≥2000字\n"
    f"{_ACADEMIC_DEPTH_RULES}"
    f"{_RICH_TEXT_RULES}"
    f"{_FORMULA_RULES}"
)

SYSTEM_PROMPT_CUSTOM_INSERT = (
    "学术论文助手,Markdown输出。在光标处生成新内容(提供前后上下文):"
    "只输出新内容不重复上下文无解释,2000-3000字,学术深度,论据充分,"
    "术语首现给英文对照,引用真实文献(作者,年份)\n"
    f"{_ACADEMIC_DEPTH_RULES}"
    f"{_FORMULA_RULES}"
    f"{_CHART_TYPES_DESC}"
    f"{_IMAGE_SEARCH_RULES}"
)

# ── 低重复模式 prompt（人性化改写，降 AIGC + 降查重） ──

# 核心理念：让 AI 写的内容具有人类写作的"不完美"特征
_HUMAN_WRITING_RULES = """【人性化写作要求】
- 用口语化学术表达（"笔者认为""从实践来看""值得注意的是""有趣的是"）
- 句子长短不一，避免整齐划一（有的句子15字，有的50字）
- 适当使用设问句、反问句增加互动感
- 加入主观评述词（"显然""不难发现""遗憾的是""令人欣慰的是"）
- 数据表述多样化（百分比↔分数、约数↔精确数、"近半数"↔"47%"）
- 主动被动灵活切换，不要全是被动句
- 禁止使用"首先、其次、最后""一方面、另一方面"等模板连接词
- 禁止每段开头都用相同句式
- 禁止堆砌形容词和同义词
"""

SYSTEM_PROMPT_CONTINUE_LOW_DUP = f"""学术论文助手,Markdown输出。续写论文，【核心目标】让内容像人写的，能通过AIGC检测，同时降低查重率。

{_HUMAN_WRITING_RULES}

【内容要求】
- 1500-3000字，论据充分，引用真实文献
- 用具体数据、案例、对比分析替代空泛概括
- 每段有明确论点，避免车轱辘话

{_ACADEMIC_DEPTH_RULES}
{_FORMULA_RULES}
{_CHART_TYPES_DESC}
{_IMAGE_SEARCH_RULES}"""

SYSTEM_PROMPT_OPTIMIZE_LOW_DUP = f"""学术论文降重专家,Markdown输出。对文本进行深度改写，目标：
1. 通过AIGC检测（让文本像人写的）
2. 大幅降低查重率（与原文表述完全不同）

{_HUMAN_WRITING_RULES}

【改写策略】
- 完全重组句子结构，不是简单换词
- 长句拆短、短句合并，打破原有节奏
- 换种角度表述同一观点
- 保持原意，关键数据不能改

直接返回改写结果，无解释，不用代码块。
{_ACADEMIC_DEPTH_RULES}
{_FORMULA_RULES}"""

SYSTEM_PROMPT_OPTIMIZE_SELECTED = f"""学术论文降重专家,Markdown输出。对选中文本进行深度改写（提供上下文参考）。

【核心目标】
1. 让改写后的文本100%像人写的，通过任何AIGC检测
2. 与原文表述完全不同，降低查重率到最低

{_HUMAN_WRITING_RULES}

【改写策略】
- 彻底重组句子，不是简单同义词替换
- 换种表达方式说同样的意思
- 加入作者视角（"笔者认为""本研究发现"）
- 适当使用转折词（"然而""不过""当然"）
- 保持原意，关键信息不能丢

仅返回改写后的选中文本，直接输出无解释，不用代码块。
{_ACADEMIC_DEPTH_RULES}
{_FORMULA_RULES}"""

SYSTEM_PROMPT_SMART_INSERT = (
    "学术论文助手,Markdown输出。在光标处插入新内容返回完整文档:"
    "直接输出完整文档无解释,光标前后内容不变,新增1500-3000字,"
    "引用真实文献不编造,不用代码块\n"
    f"{_ACADEMIC_DEPTH_RULES}"
    f"{_FORMULA_RULES}"
    f"{_CHART_TYPES_DESC}"
    f"{_IMAGE_SEARCH_RULES}"
)

SYSTEM_PROMPT_CUSTOM_SMART = (
    "学术论文助手,Markdown输出。按指令修改返回完整文档:"
    "直接输出无解释,未改部分不变,新增≥2000字学术深度,"
    "不用代码块,引用真实文献,数据用表格图表\n"
    f"{_ACADEMIC_DEPTH_RULES}"
    f"{_FORMULA_RULES}"
    f"{_CHART_TYPES_DESC}"
)

# 章节级编辑
SYSTEM_PROMPT_SECTION_EDIT = (
    "学术论文助手,Markdown输出。修改章节返回完整章节:"
    "只返回章节无解释,标题层级不变,未涉及段落保原文,"
    "修改后≥原文长度,不用代码块\n"
    f"{_ACADEMIC_DEPTH_RULES}"
    f"{_FORMULA_RULES}"
)

SYSTEM_PROMPT_HIGH_QUALITY_REWRITE = (
    "顶级学术润色专家,Markdown输出。高质量重写提质不改核心结论:"
    "强化观点-证据-论证,提升信息密度,学术精确表达替代口语化,"
    "避免模板句,保留结构无解释不用代码块\n"
    f"{_ACADEMIC_DEPTH_RULES}"
)


# ============================================================================
# 场景推荐参数
# ============================================================================

# 推荐的 max_tokens 值
MAX_TOKENS_OPTIMIZE = 4096
MAX_TOKENS_CONTINUE = 8192
MAX_TOKENS_EDIT = 8192
MAX_TOKENS_SECTION = 4096
MAX_TOKENS_REWRITE = 4096

# 推荐的 temperature 值
TEMP_CONTINUE = 0.7
TEMP_OPTIMIZE = 0.3
TEMP_EDIT = 0.4
TEMP_SECTION_EDIT = 0.35
TEMP_REWRITE = 0.3
TEMP_INSERT = 0.65
TEMP_DEFAULT = 0.5


# ============================================================================
# 消息构建函数
# ============================================================================


def _get_skills_context() -> str:
    """获取 Skills 集群记忆内容

    使用缓存机制避免重复解析文件，提升 AI 响应速度。

    Returns:
        合并后的技能内容，如果没有技能则返回空字符串
    """
    try:
        from app.core.skills_cache import get_skills_content

        return get_skills_content()
    except Exception as e:
        logger.warning(f"加载 Skills 内容失败: {e}")
        return ""


def _build_system_message(base_prompt: str) -> str:
    """构建包含 Skills 的系统消息

    Args:
        base_prompt: 基础系统提示词

    Returns:
        包含 Skills 内容的完整系统提示词
    """
    skills_content = _get_skills_context()
    if skills_content:
        return f"{base_prompt}\n\n# Skills 集群记忆\n\n以下是用户提供的技能文件内容，请在处理请求时参考这些信息：\n\n{skills_content}"
    return base_prompt


def build_optimize_messages(text: str, low_dup: bool = False) -> List[Dict[str, str]]:
    """构建文本优化的消息列表

    用于优化和润色已有文本，修正语法错误、提升学术性。

    Args:
        text: 需要优化的文本内容
        low_dup: 是否启用低重复率模式（降重）

    Returns:
        包含系统提示词和用户消息的列表

    Example:
        >>> messages = build_optimize_messages("这是一段需要优化的文本")
        >>> worker = AiWorker(messages, max_tokens=MAX_TOKENS_OPTIMIZE,
        ...                   temperature=TEMP_OPTIMIZE)
    """
    base_prompt = SYSTEM_PROMPT_OPTIMIZE_LOW_DUP if low_dup else SYSTEM_PROMPT_OPTIMIZE
    system_prompt = _build_system_message(base_prompt)
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请优化以下内容：\n\n{text}"},
    ]


def build_continue_messages(
    context: str, after_context: str = "", low_dup: bool = False
) -> List[Dict[str, str]]:
    """构建论文续写的消息列表

    根据已有内容继续撰写论文，保持风格和逻辑连贯。

    Args:
        context: 光标前的上下文（已有内容）
        after_context: 光标后的内容（可选），用于确保衔接自然
        low_dup: 是否启用低重复率模式

    Returns:
        包含系统提示词和用户消息的列表

    Example:
        >>> messages = build_continue_messages(
        ...     context="第一章 引言\n本研究探讨...",
        ...     after_context="第三章 方法\n..."
        ... )
    """
    # 截取最近的 3000 字符作为上下文
    trimmed = context[-3000:] if len(context) > 3000 else context
    after = ""
    if after_context and after_context.strip():
        after = (
            f"\n\n【注意】续写内容之后的原文如下，"
            f"请确保续写内容能自然衔接：\n{after_context[:500]}"
        )
    base_prompt = SYSTEM_PROMPT_CONTINUE_LOW_DUP if low_dup else SYSTEM_PROMPT_CONTINUE
    system_prompt = _build_system_message(base_prompt)
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请根据以下已有内容继续撰写：\n\n{trimmed}{after}"},
    ]


def build_custom_edit_messages(selected_text: str, instruction: str) -> List[Dict[str, str]]:
    """构建自定义编辑的消息列表

    根据用户指令修改选中的文本。

    Args:
        selected_text: 用户选中的文本
        instruction: 用户的修改指令

    Returns:
        包含系统提示词和用户消息的列表

    Example:
        >>> messages = build_custom_edit_messages(
        ...     selected_text="这是一段文本",
        ...     instruction="扩写为 2000 字，增加具体案例"
        ... )
    """
    system_prompt = _build_system_message(SYSTEM_PROMPT_CUSTOM_EDIT)
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"指令：{instruction}\n\n选中的文本：\n{selected_text}"},
    ]


def build_custom_insert_messages(
    instruction: str, text_before: str, text_after: str = ""
) -> List[Dict[str, str]]:
    """构建自定义插入的消息列表

    在光标位置插入新内容，提供前后上下文。

    Args:
        instruction: 用户的插入指令
        text_before: 光标前的文本
        text_after: 光标后的文本（可选）

    Returns:
        包含系统提示词和用户消息的列表

    Example:
        >>> messages = build_custom_insert_messages(
        ...     instruction="插入一段关于研究方法的内容",
        ...     text_before="第一章 引言...",
        ...     text_after="第三章 结果..."
        ... )
    """
    ctx_parts = []
    if text_before.strip():
        ctx_parts.append(f"【光标前的内容】\n{text_before[-1500:]}")
    if text_after.strip():
        ctx_parts.append(f"【光标后的内容】\n{text_after[:500]}")
    context = "\n\n".join(ctx_parts) if ctx_parts else "（文档为空）"
    system_prompt = _build_system_message(SYSTEM_PROMPT_CUSTOM_INSERT)
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"指令：{instruction}\n\n{context}"},
    ]


def build_custom_smart_messages(full_doc: str, instruction: str) -> List[Dict[str, str]]:
    """构建智能自定义编辑的消息列表

    根据指令修改文档，返回完整文档。

    Args:
        full_doc: 完整文档内容
        instruction: 用户的修改指令

    Returns:
        包含系统提示词和用户消息的列表

    Example:
        >>> messages = build_custom_smart_messages(
        ...     full_doc="完整的论文内容...",
        ...     instruction="在第二章增加文献综述"
        ... )
    """
    system_prompt = _build_system_message(SYSTEM_PROMPT_CUSTOM_SMART)
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"指令：{instruction}\n\n完整文档内容如下：\n{full_doc}"},
    ]


def build_smart_insert_messages(
    full_doc: str,
    instruction: str,
    text_before: str,
    text_after: str,
) -> List[Dict[str, str]]:
    """构建智能插入的消息列表

    在光标位置插入内容，返回完整文档。

    Args:
        full_doc: 完整文档内容
        instruction: 用户的插入指令
        text_before: 光标前的文本
        text_after: 光标后的文本

    Returns:
        包含系统提示词和用户消息的列表

    Example:
        >>> messages = build_smart_insert_messages(
        ...     full_doc="完整文档...",
        ...     instruction="插入研究假设",
        ...     text_before="引言部分...",
        ...     text_after="方法部分..."
        ... )
    """
    cursor_parts = []
    if text_before.strip():
        cursor_parts.append(f"【光标前的文本】\n{text_before[-600:]}")
    if text_after.strip():
        cursor_parts.append(f"【光标后的文本】\n{text_after[:400]}")
    cursor_hint = "\n\n".join(cursor_parts) if cursor_parts else "（光标在文档末尾）"
    system_prompt = _build_system_message(SYSTEM_PROMPT_SMART_INSERT)
    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"指令：{instruction}\n\n" f"{cursor_hint}\n\n" f"完整文档内容如下：\n{full_doc}"
            ),
        },
    ]


def build_optimize_selected_messages(full_doc: str, selected_text: str) -> List[Dict[str, str]]:
    """构建选中文本优化的消息列表

    优化选中的文本，提供周围上下文以保持连贯性。

    Args:
        full_doc: 完整文档内容
        selected_text: 选中的文本

    Returns:
        包含系统提示词和用户消息的列表

    Note:
        为了降低 token 消耗，只发送选区附近的上下文（前后各 1500 字符）

    Example:
        >>> messages = build_optimize_selected_messages(
        ...     full_doc="完整文档...",
        ...     selected_text="需要优化的段落"
        ... )
    """
    # 只发选区附近上下文而非全文，大幅降低输入 token
    pos = full_doc.find(selected_text)
    if pos >= 0:
        start = max(0, pos - 1500)
        end = min(len(full_doc), pos + len(selected_text) + 1500)
        ctx = full_doc[start:end]
    else:
        ctx = full_doc[-3000:] if len(full_doc) > 3000 else full_doc
    system_prompt = _build_system_message(SYSTEM_PROMPT_OPTIMIZE_SELECTED)
    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (f"上下文：\n{ctx}\n\n" f"请优化以下选中文本：\n{selected_text}"),
        },
    ]


def build_section_edit_messages(
    section: str,
    instruction: str,
    section_index: int,
    total_sections: int,
) -> List[Dict[str, str]]:
    """构建章节编辑的消息列表

    修改指定章节的内容。

    Args:
        section: 章节内容
        instruction: 修改指令
        section_index: 章节索引（从 0 开始）
        total_sections: 总章节数

    Returns:
        包含系统提示词和用户消息的列表

    Example:
        >>> messages = build_section_edit_messages(
        ...     section="第二章 文献综述\n...",
        ...     instruction="增加最新研究进展",
        ...     section_index=1,
        ...     total_sections=5
        ... )
    """
    system_prompt = _build_system_message(SYSTEM_PROMPT_SECTION_EDIT)
    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"修改指令：{instruction}\n\n"
                f"以下是第 {section_index + 1} 个章节（共 {total_sections} 个），"
                f"请根据指令修改后返回完整章节：\n\n{section}"
            ),
        },
    ]


def build_section_continue_messages(
    heading: str,
    text_before: str,
    text_after: str = "",
    low_dup: bool = False,
) -> List[Dict[str, str]]:
    """构建章节续写的消息列表

    为指定章节标题续写内容。

    Args:
        heading: 章节标题
        text_before: 该章节之前的完整上下文
        text_after: 该章节之后的内容（可选）
        low_dup: 是否启用低重复率模式

    Returns:
        包含系统提示词和用户消息的列表

    Example:
        >>> messages = build_section_continue_messages(
        ...     heading="第二章 文献综述",
        ...     text_before="第一章 引言\n...",
        ...     text_after="第三章 方法\n..."
        ... )
    """
    before_trimmed = text_before[-2000:] if len(text_before) > 2000 else text_before
    after = ""
    if text_after and text_after.strip():
        after = (
            f"\n\n【注意】该章节之后的原文如下，" f"请确保续写内容能自然衔接：\n{text_after[:400]}"
        )
    base_prompt = SYSTEM_PROMPT_CONTINUE_LOW_DUP if low_dup else SYSTEM_PROMPT_CONTINUE
    system_prompt = _build_system_message(base_prompt)
    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"请为以下章节标题续写详细的论文内容。\n\n"
                f"【需要续写的章节标题】\n{heading}\n\n"
                f"【该章节之前的完整上下文】\n{before_trimmed}{after}"
            ),
        },
    ]


def build_high_quality_rewrite_messages(text: str, task_hint: str = "") -> List[Dict[str, str]]:
    """构建高质量重写的消息列表

    对文本进行高质量重写，提升学术水平和信息密度。

    Args:
        text: 需要重写的文本
        task_hint: 任务场景提示（可选）

    Returns:
        包含系统提示词和用户消息的列表

    Example:
        >>> messages = build_high_quality_rewrite_messages(
        ...     text="原始文本...",
        ...     task_hint="期刊投稿"
        ... )
    """
    hint = f"\n\n任务场景：{task_hint}" if task_hint else ""
    system_prompt = _build_system_message(SYSTEM_PROMPT_HIGH_QUALITY_REWRITE)
    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"请将以下内容重写为更高质量的学术文本，确保严谨、深入、可读：{hint}\n\n{text}"
            ),
        },
    ]
