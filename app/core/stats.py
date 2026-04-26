import re


class Stats:
    """Text statistics with Chinese character support."""

    @staticmethod
    def count_words(text: str) -> int:
        if not text.strip():
            return 0
        # Count Chinese characters individually
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff\u3400-\u4dbf]", text))
        # Remove Chinese characters, count remaining words
        text_no_chinese = re.sub(r"[\u4e00-\u9fff\u3400-\u4dbf]", " ", text)
        english_words = len(text_no_chinese.split())
        return chinese_chars + english_words

    @staticmethod
    def count_chars(text: str) -> int:
        return len(text.replace("\n", "").replace("\r", ""))

    @staticmethod
    def count_chars_no_spaces(text: str) -> int:
        return len(text.replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", ""))
