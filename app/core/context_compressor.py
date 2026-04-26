"""智能上下文压缩器

在段落边界截断文本，保持语义完整性。
避免在句子中间截断，提升 AI 理解效果。
"""

import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)


class ContextCompressor:
    """智能上下文压缩器

    在段落或句子边界截断文本，而不是简单的字符截断。

    Example:
        >>> text = "第一段内容...\\n\\n第二段内容...\\n\\n第三段内容..."
        >>> compressed = ContextCompressor.compress(text, 1000, from_end=True)
    """

    # 段落分隔符
    PARAGRAPH_SEPARATORS = ["\n\n", "\r\n\r\n"]

    # 句子结束标记
    SENTENCE_ENDINGS = re.compile(r'[。！？.!?]\s*')

    @classmethod
    def compress(
        cls,
        text: str,
        max_chars: int,
        from_end: bool = True,
        preserve_structure: bool = True
    ) -> str:
        """压缩文本到指定长度

        Args:
            text: 原始文本
            max_chars: 最大字符数
            from_end: True=保留末尾内容, False=保留开头内容
            preserve_structure: 是否保持段落结构

        Returns:
            压缩后的文本
        """
        if not text or len(text) <= max_chars:
            return text

        if preserve_structure:
            return cls._compress_by_paragraphs(text, max_chars, from_end)
        else:
            return cls._compress_by_sentences(text, max_chars, from_end)

    @classmethod
    def _compress_by_paragraphs(cls, text: str, max_chars: int, from_end: bool) -> str:
        """按段落边界压缩"""
        # 分割段落
        paragraphs = cls._split_paragraphs(text)

        if not paragraphs:
            return text[:max_chars] if not from_end else text[-max_chars:]

        if from_end:
            # 从末尾开始累积段落
            result = []
            total = 0
            for p in reversed(paragraphs):
                p_len = len(p) + 2  # 加上段落分隔符长度
                if total + p_len > max_chars:
                    # 如果当前段落太长，尝试按句子截断
                    remaining = max_chars - total
                    if remaining > 100:  # 至少保留100字符
                        partial = cls._compress_by_sentences(p, remaining, from_end=True)
                        if partial:
                            result.insert(0, partial)
                    break
                result.insert(0, p)
                total += p_len

            return "\n\n".join(result)
        else:
            # 从开头开始累积段落
            result = []
            total = 0
            for p in paragraphs:
                p_len = len(p) + 2
                if total + p_len > max_chars:
                    remaining = max_chars - total
                    if remaining > 100:
                        partial = cls._compress_by_sentences(p, remaining, from_end=False)
                        if partial:
                            result.append(partial)
                    break
                result.append(p)
                total += p_len

            return "\n\n".join(result)

    @classmethod
    def _compress_by_sentences(cls, text: str, max_chars: int, from_end: bool) -> str:
        """按句子边界压缩"""
        # 分割句子
        sentences = cls._split_sentences(text)

        if not sentences:
            return text[:max_chars] if not from_end else text[-max_chars:]

        if from_end:
            result = []
            total = 0
            for s in reversed(sentences):
                if total + len(s) > max_chars:
                    break
                result.insert(0, s)
                total += len(s)
            return "".join(result)
        else:
            result = []
            total = 0
            for s in sentences:
                if total + len(s) > max_chars:
                    break
                result.append(s)
                total += len(s)
            return "".join(result)

    @classmethod
    def _split_paragraphs(cls, text: str) -> List[str]:
        """分割段落"""
        # 统一换行符
        text = text.replace("\r\n", "\n")
        # 按双换行分割
        paragraphs = text.split("\n\n")
        # 过滤空段落
        return [p.strip() for p in paragraphs if p.strip()]

    @classmethod
    def _split_sentences(cls, text: str) -> List[str]:
        """分割句子"""
        # 使用正则分割，保留分隔符
        parts = cls.SENTENCE_ENDINGS.split(text)
        delimiters = cls.SENTENCE_ENDINGS.findall(text)

        sentences = []
        for i, part in enumerate(parts):
            if part:
                sentence = part
                if i < len(delimiters):
                    sentence += delimiters[i]
                sentences.append(sentence)

        return sentences

    @classmethod
    def compress_context_pair(
        cls,
        before: str,
        after: str,
        max_before: int = 2000,
        max_after: int = 500
    ) -> Tuple[str, str]:
        """压缩上下文对 (光标前后内容)

        Args:
            before: 光标前的文本
            after: 光标后的文本
            max_before: 前文最大字符数
            max_after: 后文最大字符数

        Returns:
            (压缩后的前文, 压缩后的后文)
        """
        compressed_before = cls.compress(before, max_before, from_end=True)
        compressed_after = cls.compress(after, max_after, from_end=False)
        return compressed_before, compressed_after

    @classmethod
    def smart_truncate(cls, text: str, max_chars: int, ellipsis: str = "...") -> str:
        """智能截断，在词边界截断

        Args:
            text: 原始文本
            max_chars: 最大字符数
            ellipsis: 省略号

        Returns:
            截断后的文本
        """
        if len(text) <= max_chars:
            return text

        # 预留省略号空间
        target_len = max_chars - len(ellipsis)
        if target_len <= 0:
            return ellipsis

        truncated = text[:target_len]

        # 尝试在词边界截断
        # 中文不需要词边界，英文在空格处截断
        last_space = truncated.rfind(" ")
        last_newline = truncated.rfind("\n")
        last_break = max(last_space, last_newline)

        if last_break > target_len * 0.7:  # 至少保留70%内容
            truncated = truncated[:last_break]

        return truncated.rstrip() + ellipsis


def compress_context(text: str, max_chars: int, from_end: bool = True) -> str:
    """便捷函数：压缩上下文"""
    return ContextCompressor.compress(text, max_chars, from_end)


def compress_context_pair(
    before: str,
    after: str,
    max_before: int = 2000,
    max_after: int = 500
) -> Tuple[str, str]:
    """便捷函数：压缩上下文对"""
    return ContextCompressor.compress_context_pair(before, after, max_before, max_after)
