APP_NAME = "ThesisX"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "学术论文撰写与表格处理工具"

DEFAULT_FONT_FAMILY = "Microsoft YaHei"
DEFAULT_FONT_SIZE = 11
EDITOR_FONT_FAMILY = "Microsoft YaHei"
EDITOR_FONT_SIZE = 14

PREVIEW_DEBOUNCE_MS = 300

SUPPORTED_FILE_FILTER = (
    "所有支持格式 (*.wtz *.md *.txt);;"
    "ThesisX 文档 (*.wtz);;"
    "Markdown 文件 (*.md);;"
    "文本文件 (*.txt);;"
    "所有文件 (*)"
)
WTZ_FILE_FILTER = "ThesisX 文档 (*.wtz)"
EXPORT_HTML_FILTER = "HTML 文件 (*.html)"
EXPORT_PDF_FILTER = "PDF 文件 (*.pdf)"
EXPORT_DOCX_FILTER = "Word 文档 (*.docx)"
EXPORT_PPTX_FILTER = "PowerPoint 文件 (*.pptx)"

MAX_RECENT_FILES = 10

# Preview style presets
PREVIEW_STYLE_ACADEMIC = "academic"
PREVIEW_STYLE_MODERN = "modern"
PREVIEW_STYLE_CLASSIC = "classic"
PREVIEW_STYLES = [
    (PREVIEW_STYLE_ACADEMIC, "学术"),
    (PREVIEW_STYLE_MODERN, "现代"),
    (PREVIEW_STYLE_CLASSIC, "经典"),
]
