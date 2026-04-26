"""自定义异常类

本模块定义了 ThesisX 应用程序的异常层次结构。
所有自定义异常都继承自 ThesisXError 基类。

遵循 Google Python 风格指南的异常设计原则：
- 使用具体的异常类型而不是通用的 Exception
- 异常名称应清晰描述错误类型
- 提供有用的错误消息帮助调试
"""


class ThesisXError(Exception):
    """ThesisX 应用程序的基础异常类

    所有自定义异常都应继承此类。这使得捕获所有应用程序特定的
    异常变得容易，同时仍然允许捕获特定的异常类型。

    Example:
        >>> try:
        ...     raise DocumentError("文件不存在")
        ... except ThesisXError as e:
        ...     print(f"应用程序错误: {e}")
        应用程序错误: 文件不存在
    """

    pass


class DocumentError(ThesisXError):
    """文档操作相关异常

    当文档的读取、写入、解析或处理失败时抛出此异常。

    Example:
        >>> raise DocumentError("无法保存文档: 磁盘空间不足")
    """

    pass


class DocumentNotFoundError(DocumentError):
    """文档未找到异常

    当尝试打开不存在的文档时抛出此异常。

    Example:
        >>> raise DocumentNotFoundError("/path/to/missing.md")
    """

    pass


class DocumentSaveError(DocumentError):
    """文档保存失败异常

    当文档保存操作失败时抛出此异常。

    Example:
        >>> raise DocumentSaveError("无法写入文件: 权限被拒绝")
    """

    pass


class ExportError(ThesisXError):
    """文档导出相关异常

    当文档导出为其他格式（DOCX、PDF、PPTX等）失败时抛出此异常。

    Example:
        >>> raise ExportError("DOCX 导出失败: 模板文件损坏")
    """

    pass


class ExportFormatError(ExportError):
    """不支持的导出格式异常

    当请求导出到不支持的格式时抛出此异常。

    Example:
        >>> raise ExportFormatError("不支持的格式: .xyz")
    """

    pass


class AiServiceError(ThesisXError):
    """AI 服务相关异常

    当 AI 服务调用失败时抛出此异常。

    Example:
        >>> raise AiServiceError("AI API 请求失败")
    """

    pass


class AiApiError(AiServiceError):
    """AI API 调用错误

    当 AI API 返回错误响应时抛出此异常。

    Attributes:
        status_code: HTTP 状态码（如果适用）
        response_body: API 响应内容

    Example:
        >>> raise AiApiError("API 返回 429: 请求过于频繁", status_code=429)
    """

    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class AiTimeoutError(AiServiceError):
    """AI 请求超时异常

    当 AI API 请求超时时抛出此异常。

    Example:
        >>> raise AiTimeoutError("AI 请求超时（60秒）")
    """

    pass


class AiConfigError(AiServiceError):
    """AI 配置错误

    当 AI 服务配置无效时抛出此异常（例如缺少 API 密钥）。

    Example:
        >>> raise AiConfigError("未配置 AI API Key")
    """

    pass


class ConfigError(ThesisXError):
    """配置相关异常

    当应用程序配置无效或加载失败时抛出此异常。

    Example:
        >>> raise ConfigError("配置文件格式错误: 无效的 JSON")
    """

    pass


class RenderError(ThesisXError):
    """渲染相关异常

    当 Markdown 渲染、LaTeX 公式渲染或图表渲染失败时抛出此异常。

    Example:
        >>> raise RenderError("LaTeX 公式渲染失败: 语法错误")
    """

    pass


class TableError(ThesisXError):
    """表格操作相关异常

    当表格解析、编辑或导入/导出失败时抛出此异常。

    Example:
        >>> raise TableError("无法解析 Excel 文件: 文件已损坏")
    """

    pass


class ImageError(ThesisXError):
    """图像处理相关异常

    当图像加载、处理或生成失败时抛出此异常。

    Example:
        >>> raise ImageError("无法加载图像: 不支持的格式")
    """

    pass


class ChartError(ThesisXError):
    """图表生成相关异常

    当图表生成或渲染失败时抛出此异常。

    Example:
        >>> raise ChartError("图表数据无效: 缺少必需字段")
    """

    pass


class PlagiarismError(ThesisXError):
    """查重服务相关异常

    当查重服务调用失败时抛出此异常。

    Example:
        >>> raise PlagiarismError("查重服务不可用")
    """

    pass
