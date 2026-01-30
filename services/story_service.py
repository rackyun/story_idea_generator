"""
历史记录业务服务

处理灵感生成、企划书和历史记录相关的业务逻辑。
"""

from typing import Dict, List, Tuple, Optional
from database import DatabaseManager, NovelManager


class StoryService:
    """历史记录业务服务类"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.novel_manager = NovelManager()

    def get_story_list(
        self,
        story_type: Optional[str] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        order_by: str = "created_at DESC"
    ) -> Tuple[List[Dict], int]:
        """
        获取故事列表

        Args:
            story_type: 类型筛选 (base/crew_ai/full_novel)
            search_query: 搜索关键词
            page: 页码
            page_size: 每页数量
            order_by: 排序方式

        Returns:
            (stories, total_count)
        """
        return self.db_manager.list_stories(
            story_type=story_type,
            search_query=search_query,
            page=page,
            page_size=page_size,
            order_by=order_by
        )

    def get_story_detail(self, story_id: int, view_type: str = 'story') -> Optional[Dict]:
        """
        获取故事详情

        Args:
            story_id: 故事ID
            view_type: 查看类型 (story/novel)

        Returns:
            故事详情字典，不存在返回 None
        """
        # 确保 story_id 是整数类型
        try:
            story_id = int(story_id) if story_id is not None else None
        except (ValueError, TypeError):
            return None
        
        if story_id is None:
            return None
        
        story = None

        if view_type == 'novel':
            story = self.novel_manager.get_novel(story_id)
            if story:
                story['type'] = 'full_novel'
        else:
            story = self.db_manager.get_story(story_id)
            # 兼容性处理：尝试在 novels 表中查找
            if not story:
                novel = self.novel_manager.get_novel(story_id)
                if novel:
                    story = novel
                    story['type'] = 'full_novel'

        # 确保返回字典格式
        if story and not isinstance(story, dict):
            try:
                story = dict(story) if hasattr(story, 'keys') else {}
            except Exception:
                return None

        return story

    def update_story_info(
        self,
        story_id: int,
        story_type: str,
        title: Optional[str] = None,
        topic: Optional[str] = None,
        content: Optional[str] = None
    ) -> bool:
        """
        更新故事基本信息

        Args:
            story_id: 故事ID
            story_type: 故事类型
            title: 新标题
            topic: 新主题
            content: 新内容（可选）

        Returns:
            是否成功
        """
        if story_type == 'full_novel':
            return self.novel_manager.update_novel(story_id, title=title)
        else:
            return self.db_manager.update_story(story_id, title=title, content=content)

    def delete_story(self, story_id: int) -> bool:
        """
        删除故事（软删除）

        Args:
            story_id: 故事ID

        Returns:
            是否成功
        """
        return self.db_manager.delete_story(story_id)

    def batch_delete_stories(self, story_ids: List[int]) -> int:
        """
        批量删除故事

        Args:
            story_ids: 故事ID列表

        Returns:
            成功删除的数量
        """
        count = 0
        for story_id in story_ids:
            if self.delete_story(story_id):
                count += 1
        return count

    def get_story_history(self, story_id: int) -> List[Dict]:
        """
        获取故事的重新生成历史

        Args:
            story_id: 故事ID

        Returns:
            历史记录列表
        """
        return self.db_manager.get_story_history(story_id)

    def get_related_novels(self, story_id: int) -> List[Dict]:
        """
        获取关联的小说记录

        Args:
            story_id: 故事ID

        Returns:
            小说记录列表
        """
        history = self.db_manager.get_story_history(story_id)
        novel_records = []

        for item in history:
            if not isinstance(item, dict):
                item = dict(item) if hasattr(item, 'keys') else {}
            if item.get('type') == 'full_novel':
                novel_records.append(item)

        return novel_records

    def get_statistics(self) -> Dict[str, int]:
        """
        获取统计信息

        Returns:
            统计数据字典
        """
        stats = {}

        # 总记录数
        _, total = self.db_manager.list_stories(page_size=1)
        stats['total'] = total

        # 各类型统计
        for story_type, name in [("base", "灵感"), ("crew_ai", "企划"), ("full_novel", "小说")]:
            _, count = self.db_manager.list_stories(story_type=story_type, page_size=1)
            stats[name] = count

        return stats
