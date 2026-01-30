"""
小说篇幅分类统一配置模块

定义了统一的小说篇幅分类标准和相关工具函数。
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class NovelLengthCategory:
    """小说篇幅分类"""
    key: str  # 分类键名
    name: str  # 显示名称
    min_words: int  # 最小字数
    max_words: Optional[int]  # 最大字数（None 表示无上限）
    description: str  # 描述

    def contains(self, word_count: int) -> bool:
        """判断字数是否属于该分类"""
        if self.max_words is None:
            return word_count >= self.min_words
        return self.min_words <= word_count < self.max_words

    def get_display_name(self) -> str:
        """获取显示名称（带字数范围）"""
        if self.max_words is None:
            return f"{self.name} ({self.min_words//10000}万字以上)"
        elif self.min_words == 0:
            return f"{self.name} ({self.max_words//10000}万字以内)"
        else:
            return f"{self.name} ({self.min_words//10000}-{self.max_words//10000}万字)"


# 统一的小说篇幅分类标准
NOVEL_LENGTH_CATEGORIES = [
    NovelLengthCategory(
        key="micro",
        name="微型小说",
        min_words=0,
        max_words=10000,
        description="1万字以内"
    ),
    NovelLengthCategory(
        key="short",
        name="短篇小说",
        min_words=10000,
        max_words=100000,
        description="1-10万字"
    ),
    NovelLengthCategory(
        key="medium",
        name="中篇小说",
        min_words=100000,
        max_words=500000,
        description="10-50万字"
    ),
    NovelLengthCategory(
        key="long",
        name="长篇小说",
        min_words=500000,
        max_words=2000000,
        description="50-200万字"
    ),
    NovelLengthCategory(
        key="super_long",
        name="超长篇小说",
        min_words=2000000,
        max_words=None,
        description="200万字以上"
    ),
]


# 创建字典映射，方便快速查找
CATEGORY_BY_KEY = {cat.key: cat for cat in NOVEL_LENGTH_CATEGORIES}
CATEGORY_BY_NAME = {cat.name: cat for cat in NOVEL_LENGTH_CATEGORIES}


def get_length_category(word_count: int) -> NovelLengthCategory:
    """
    根据字数获取小说篇幅分类

    Args:
        word_count: 字数

    Returns:
        NovelLengthCategory: 对应的篇幅分类
    """
    for category in NOVEL_LENGTH_CATEGORIES:
        if category.contains(word_count):
            return category
    # 默认返回微型小说
    return NOVEL_LENGTH_CATEGORIES[0]


def get_category_by_key(key: str) -> Optional[NovelLengthCategory]:
    """
    根据键名获取分类

    Args:
        key: 分类键名

    Returns:
        NovelLengthCategory 或 None
    """
    return CATEGORY_BY_KEY.get(key)


def get_category_by_name(name: str) -> Optional[NovelLengthCategory]:
    """
    根据名称获取分类（支持模糊匹配）

    Args:
        name: 分类名称（可以包含字数范围描述）

    Returns:
        NovelLengthCategory 或 None
    """
    # 精确匹配
    if name in CATEGORY_BY_NAME:
        return CATEGORY_BY_NAME[name]

    # 模糊匹配（检查是否包含分类名称）
    for category in NOVEL_LENGTH_CATEGORIES:
        if category.name in name:
            return category

    return None


def get_display_options() -> List[str]:
    """
    获取用于 UI 显示的选项列表

    Returns:
        List[str]: 显示选项列表
    """
    return [cat.get_display_name() for cat in NOVEL_LENGTH_CATEGORIES]


def get_chapter_planning_guide(category_key: str) -> Dict[str, any]:
    """
    获取章节规划指南

    Args:
        category_key: 分类键名

    Returns:
        Dict: 包含章节规划建议的字典
    """
    guides = {
        "micro": {
            "acts": "1-2幕",
            "structure": "简洁紧凑，快速推进",
            "chapters": "1-5章",
            "words_per_chapter": "1500-3000字",
            "total_chapters_range": (1, 5),
            "words_per_chapter_range": (1500, 3000)
        },
        "short": {
            "acts": "3-4幕",
            "structure": "适度展开，单一主线",
            "chapters": "10-50章",
            "words_per_chapter": "2000-3000字",
            "total_chapters_range": (10, 50),
            "words_per_chapter_range": (2000, 3000)
        },
        "medium": {
            "acts": "4-5幕",
            "structure": "充分铺垫，1-2条支线",
            "chapters": "50-200章",
            "words_per_chapter": "2000-3000字",
            "total_chapters_range": (50, 200),
            "words_per_chapter_range": (2000, 3000)
        },
        "long": {
            "acts": "5-6幕",
            "structure": "多条支线，复杂人物关系",
            "chapters": "200-800章",
            "words_per_chapter": "2000-3000字",
            "total_chapters_range": (200, 800),
            "words_per_chapter_range": (2000, 3000)
        },
        "super_long": {
            "acts": "6+幕",
            "structure": "复杂世界观，多重主线",
            "chapters": "800+章",
            "words_per_chapter": "2000-3000字",
            "total_chapters_range": (800, None),
            "words_per_chapter_range": (2000, 3000)
        }
    }

    return guides.get(category_key, guides["micro"])


def format_length_description(word_count: int) -> str:
    """
    格式化字数描述

    Args:
        word_count: 字数

    Returns:
        str: 格式化的描述，如 "微型小说 (0.8万字)"
    """
    category = get_length_category(word_count)

    if word_count < 10000:
        return f"{category.name} ({word_count}字)"
    else:
        wan = word_count / 10000
        return f"{category.name} ({wan:.1f}万字)"


# 导出常用函数和常量
__all__ = [
    'NovelLengthCategory',
    'NOVEL_LENGTH_CATEGORIES',
    'get_length_category',
    'get_category_by_key',
    'get_category_by_name',
    'get_display_options',
    'get_chapter_planning_guide',
    'format_length_description',
]
