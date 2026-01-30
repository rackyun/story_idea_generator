"""
章节编辑业务服务

处理章节编辑相关的业务逻辑。
"""

from typing import Dict, List, Optional
from database import ChapterManager, NovelStatsManager
from utils.stats import StatsHelper


class ChapterService:
    """章节编辑业务服务类"""

    def __init__(self):
        self.chapter_manager = ChapterManager()
        self.stats_manager = NovelStatsManager()

    def get_chapter_detail(self, chapter_id: int) -> Optional[Dict]:
        """
        获取章节详情

        Args:
            chapter_id: 章节ID

        Returns:
            章节详情字典，不存在返回 None
        """
        return self.chapter_manager.get_chapter(chapter_id)

    def update_chapter_content(
        self,
        chapter_id: int,
        chapter_title: Optional[str] = None,
        outline: Optional[str] = None,
        content: Optional[str] = None,
        status: Optional[str] = None
    ) -> bool:
        """
        更新章节内容

        Args:
            chapter_id: 章节ID
            chapter_title: 新标题
            outline: 新大纲
            content: 新内容
            status: 新状态

        Returns:
            是否成功
        """
        # 构建更新字典
        updates = {}

        if chapter_title is not None:
            updates['chapter_title'] = chapter_title

        if outline is not None:
            updates['outline'] = outline

        if content is not None:
            updates['content'] = content

        if status is not None:
            updates['status'] = status

        if not updates:
            return False

        # 更新章节
        success = self.chapter_manager.update_chapter(chapter_id, **updates)

        if success:
            # 更新小说元数据
            chapter = self.chapter_manager.get_chapter(chapter_id)
            if chapter:
                self.stats_manager.update_novel_metadata(chapter['novel_id'])

        return success

    def get_adjacent_chapters(
        self,
        chapter_id: int
    ) -> Dict[str, Optional[Dict]]:
        """
        获取相邻章节

        Args:
            chapter_id: 当前章节ID

        Returns:
            {'prev': 上一章, 'next': 下一章}
        """
        chapter = self.chapter_manager.get_chapter(chapter_id)
        if not chapter:
            return {'prev': None, 'next': None}

        all_chapters = self.chapter_manager.list_chapters(chapter['novel_id'])
        current_index = next(
            (i for i, ch in enumerate(all_chapters) if ch['id'] == chapter_id),
            None
        )

        result = {'prev': None, 'next': None}

        if current_index is not None:
            if current_index > 0:
                result['prev'] = all_chapters[current_index - 1]
            if current_index < len(all_chapters) - 1:
                result['next'] = all_chapters[current_index + 1]

        return result

    def format_word_count(self, word_count: int) -> str:
        """
        格式化字数显示

        Args:
            word_count: 字数

        Returns:
            格式化后的字符串
        """
        return StatsHelper.format_word_count(word_count)
