"""
小说管理业务服务

处理小说管理、版本控制、统计分析等业务逻辑。
"""

from typing import Dict, List, Optional, Any, Tuple
from database import (
    NovelManager, ChapterManager, NovelStatsManager,
    NovelVersionManager, OutlineManager
)
from utils.export import ExportManager
from utils.stats import StatsHelper


class NovelService:
    """小说管理业务服务类"""

    def __init__(self):
        self.novel_manager = NovelManager()
        self.chapter_manager = ChapterManager()
        self.stats_manager = NovelStatsManager()
        self.version_manager = NovelVersionManager()
        self.outline_manager = OutlineManager()
        self.export_manager = ExportManager()

    # ========== 小说基本操作 ==========

    def get_novel_list(self, page: int = 1, page_size: int = 100) -> Tuple[List[Dict], int]:
        """获取小说列表"""
        return self.novel_manager.list_novels(page=page, page_size=page_size)

    def get_novel_detail(self, novel_id: int) -> Optional[Dict]:
        """获取小说详情"""
        return self.novel_manager.get_novel(novel_id)

    def update_novel_info(
        self,
        novel_id: int,
        title: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """更新小说基本信息"""
        return self.novel_manager.update_novel(novel_id, title=title, metadata=metadata)

    def delete_novel(self, novel_id: int) -> bool:
        """删除小说"""
        return self.novel_manager.delete_novel(novel_id)

    # ========== 章节管理 ==========

    def get_chapter_list(self, novel_id: int) -> List[Dict]:
        """获取章节列表"""
        return self.chapter_manager.list_chapters(novel_id)

    def get_chapter_detail(self, chapter_id: int) -> Optional[Dict]:
        """获取章节详情"""
        return self.chapter_manager.get_chapter(chapter_id)

    def create_chapter(
        self,
        novel_id: int,
        chapter_number: int,
        chapter_title: str,
        content: str,
        outline: str = "",
        status: str = "draft"
    ) -> Optional[int]:
        """创建章节"""
        chapter_id = self.chapter_manager.create_chapter(
            novel_id=novel_id,
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            content=content,
            outline=outline,
            status=status
        )

        if chapter_id:
            # 更新统计信息
            self.stats_manager.update_novel_metadata(novel_id)

        return chapter_id

    def update_chapter(self, chapter_id: int, **kwargs) -> bool:
        """更新章节"""
        success = self.chapter_manager.update_chapter(chapter_id, **kwargs)

        if success:
            # 获取章节所属小说ID并更新统计
            chapter = self.chapter_manager.get_chapter(chapter_id)
            if chapter:
                self.stats_manager.update_novel_metadata(chapter['novel_id'])

        return success

    def delete_chapter(self, chapter_id: int) -> bool:
        """删除章节"""
        chapter = self.chapter_manager.get_chapter(chapter_id)
        if not chapter:
            return False

        success = self.chapter_manager.delete_chapter(chapter_id)

        if success:
            self.stats_manager.update_novel_metadata(chapter['novel_id'])

        return success

    def parse_chapters_from_content(self, content: str) -> List[Dict]:
        """从内容解析章节"""
        return self.chapter_manager.parse_chapters_from_content(content)

    # ========== 大纲管理 ==========

    def get_outline_segments(self, novel_id: int) -> List[Dict]:
        """获取大纲段列表"""
        return self.outline_manager.list_outline_segments(novel_id)

    def get_outline_segment(self, segment_id: int) -> Optional[Dict]:
        """获取大纲段详情"""
        return self.outline_manager.get_outline_segment(segment_id)

    def create_outline_segment(
        self,
        novel_id: int,
        start_chapter: int,
        end_chapter: int,
        title: str,
        summary: str,
        status: str = "active",
        priority: int = 0
    ) -> Optional[int]:
        """创建大纲段"""
        return self.outline_manager.create_outline_segment(
            novel_id=novel_id,
            start_chapter=start_chapter,
            end_chapter=end_chapter,
            title=title,
            summary=summary,
            status=status,
            priority=priority
        )

    def update_outline_segment(self, segment_id: int, **kwargs) -> bool:
        """更新大纲段"""
        return self.outline_manager.update_outline_segment(segment_id, **kwargs)

    def delete_outline_segment(self, segment_id: int) -> bool:
        """删除大纲段"""
        return self.outline_manager.delete_outline_segment(segment_id)

    def get_segments_by_chapter_range(
        self,
        novel_id: int,
        start_chapter: int,
        end_chapter: int
    ) -> List[Dict]:
        """按章节范围查询大纲段"""
        return self.outline_manager.get_segments_by_chapter_range(
            novel_id, start_chapter, end_chapter
        )

    # ========== 统计分析 ==========

    def get_novel_stats(self, novel_id: int) -> Dict[str, Any]:
        """获取小说统计信息"""
        return self.stats_manager.calculate_novel_stats(novel_id)

    def get_word_count_chart(self, novel_id: int) -> Dict[str, List]:
        """获取字数统计图表数据"""
        return self.stats_manager.get_word_count_chart(novel_id)

    def get_writing_timeline(self, novel_id: int) -> List[Dict]:
        """获取写作时间线"""
        return self.stats_manager.get_writing_timeline(novel_id)

    def update_novel_metadata(self, novel_id: int) -> bool:
        """更新小说元数据"""
        return self.stats_manager.update_novel_metadata(novel_id)

    # ========== 版本控制 ==========

    def get_version_list(self, novel_id: int) -> List[Dict]:
        """获取版本列表"""
        return self.version_manager.list_versions(novel_id)

    def get_version_detail(self, version_id: int) -> Optional[Dict]:
        """获取版本详情"""
        return self.version_manager.get_version(version_id)

    def create_version_snapshot(
        self,
        novel_id: int,
        version_name: str,
        version_note: str = ""
    ) -> Optional[int]:
        """创建版本快照"""
        # 获取小说和章节数据
        novel = self.novel_manager.get_novel(novel_id)
        if not novel:
            return None

        chapters = self.chapter_manager.list_chapters(novel_id)

        # 准备快照数据
        snapshot_data = {
            'novel_id': novel_id,
            'title': novel['title'],
            'content': novel['content'],
            'chapters': [
                {
                    'id': ch['id'],
                    'chapter_number': ch['chapter_number'],
                    'chapter_title': ch['chapter_title'],
                    'content': ch['content'],
                    'word_count': ch['word_count']
                }
                for ch in chapters
            ]
        }

        return self.version_manager.create_version(
            novel_id=novel_id,
            version_name=version_name,
            version_note=version_note,
            snapshot_data=snapshot_data
        )

    # ========== 导出功能 ==========

    def export_to_markdown(
        self,
        novel_id: int,
        include_outline: bool = False
    ) -> Optional[str]:
        """导出为 Markdown"""
        novel = self.novel_manager.get_novel(novel_id)
        if not novel:
            return None

        chapters = self.chapter_manager.list_chapters(novel_id)

        metadata = {
            'id': novel_id,
            'created_at': novel['created_at'],
            'tags': []
        }

        return self.export_manager.export_to_markdown(
            title=novel['title'],
            chapters=chapters,
            include_outline=include_outline,
            metadata=metadata
        )

    def export_to_txt(
        self,
        novel_id: int,
        include_outline: bool = False
    ) -> Optional[str]:
        """导出为纯文本"""
        novel = self.novel_manager.get_novel(novel_id)
        if not novel:
            return None

        chapters = self.chapter_manager.list_chapters(novel_id)

        return self.export_manager.export_to_txt(
            title=novel['title'],
            chapters=chapters,
            include_outline=include_outline
        )

    def export_outline_to_markdown(self, novel_id: int) -> Optional[str]:
        """仅导出大纲为 Markdown。无大纲时返回 None。"""
        novel = self.novel_manager.get_novel(novel_id)
        if not novel:
            return None
        segments = self.outline_manager.list_outline_segments(novel_id)
        if not segments:
            return None
        from utils.export import _outline_segments_to_lines
        return "\n".join(_outline_segments_to_lines(novel["title"], segments, as_markdown=True))

    def export_outline_to_txt(self, novel_id: int) -> Optional[str]:
        """仅导出大纲为纯文本。无大纲时返回 None。"""
        novel = self.novel_manager.get_novel(novel_id)
        if not novel:
            return None
        segments = self.outline_manager.list_outline_segments(novel_id)
        if not segments:
            return None
        from utils.export import _outline_segments_to_lines
        return "\n".join(_outline_segments_to_lines(novel["title"], segments, as_markdown=False))
