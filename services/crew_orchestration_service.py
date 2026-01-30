"""
Crew 编排服务

负责协调四个 Crew 的执行流程，管理流程状态。
"""

from typing import Dict, Any, Optional
import json
from database import DatabaseManager, NovelManager, ChapterManager, OutlineManager
from services.proposal_service import ProposalService
from services.outline_service import OutlineService
from services.detailed_outline_service import DetailedOutlineService
from services.chapter_writing_service import ChapterWritingService


class CrewOrchestrationService:
    """Crew 编排服务类"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.novel_manager = NovelManager()
        self.chapter_manager = ChapterManager()
        self.outline_manager = OutlineManager()
        
        self.proposal_service = ProposalService()
        self.outline_service = OutlineService()
        self.detailed_outline_service = DetailedOutlineService()
        self.chapter_writing_service = ChapterWritingService()

    def get_workflow_status(self, novel_id: int) -> Dict[str, Any]:
        """
        获取工作流状态
        
        Args:
            novel_id: 小说 ID
        
        Returns:
            {
                'current_stage': str,  # proposal/outline/detailed_outline/writing/completed
                'progress': float,  # 0.0-1.0
                'has_proposal': bool,
                'has_outline': bool,
                'has_detailed_outline': bool,
                'has_chapters': bool,
                'chapter_count': int,
                'outline_segment_count': int
            }
        """
        novel = self.novel_manager.get_novel(novel_id)
        if not novel:
            return {
                'current_stage': 'none',
                'progress': 0.0,
                'has_proposal': False,
                'has_outline': False,
                'has_detailed_outline': False,
                'has_chapters': False,
                'chapter_count': 0,
                'outline_segment_count': 0
            }

        # 获取元数据
        metadata = novel.get('metadata', {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}

        # 检查各阶段状态
        has_proposal = bool(novel.get('source_story_id'))
        has_outline = bool(novel.get('content'))  # content 字段存储大纲
        
        outline_segments = self.outline_manager.list_outline_segments(novel_id)
        has_detailed_outline = len(outline_segments) > 0
        
        chapters = self.chapter_manager.list_chapters(novel_id)
        has_chapters = len(chapters) > 0

        # 确定当前阶段
        current_stage = metadata.get('workflow_stage', 'proposal')
        if not current_stage or current_stage == 'proposal':
            if has_chapters:
                current_stage = 'writing'
            elif has_detailed_outline:
                current_stage = 'detailed_outline'
            elif has_outline:
                current_stage = 'outline'
            else:
                current_stage = 'proposal'

        # 计算进度
        progress = 0.0
        if has_proposal:
            progress += 0.25
        if has_outline:
            progress += 0.25
        if has_detailed_outline:
            progress += 0.25
        if has_chapters:
            progress += 0.25

        return {
            'current_stage': current_stage,
            'progress': progress,
            'has_proposal': has_proposal,
            'has_outline': has_outline,
            'has_detailed_outline': has_detailed_outline,
            'has_chapters': has_chapters,
            'chapter_count': len(chapters),
            'outline_segment_count': len(outline_segments)
        }

    def can_generate_outline(self, story_id: int) -> bool:
        """
        检查是否可以生成大纲
        
        Args:
            story_id: 企划书 ID
        
        Returns:
            bool: 是否可以生成大纲
        """
        story = self.db_manager.get_story(story_id)
        if not story:
            return False

        # 检查是否有内容
        content = story.get('content', '')
        return bool(content and len(content) > 100)

    def can_generate_detailed_outline(self, novel_id: int) -> bool:
        """
        检查是否可以生成细纲
        
        Args:
            novel_id: 小说 ID
        
        Returns:
            bool: 是否可以生成细纲
        """
        novel = self.novel_manager.get_novel(novel_id)
        if not novel:
            return False

        # 检查是否有大纲内容
        outline_content = novel.get('content', '')
        return bool(outline_content and len(outline_content) > 100)

    def can_generate_chapters(self, novel_id: int) -> bool:
        """
        检查是否可以撰写正文
        
        Args:
            novel_id: 小说 ID
        
        Returns:
            bool: 是否可以撰写正文
        """
        # 检查是否有细纲
        outline_segments = self.outline_manager.list_outline_segments(novel_id)
        return len(outline_segments) > 0

    def get_next_action(self, novel_id: Optional[int] = None, story_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取下一步应该执行的动作
        
        Args:
            novel_id: 小说 ID（可选）
            story_id: 企划书 ID（可选）
        
        Returns:
            {
                'action': str,  # generate_outline/generate_detailed_outline/generate_chapters/completed
                'message': str,  # 提示信息
                'can_execute': bool
            }
        """
        if novel_id:
            status = self.get_workflow_status(novel_id)
            
            if not status['has_chapters'] and status['has_detailed_outline']:
                return {
                    'action': 'generate_chapters',
                    'message': '细纲已准备就绪，可以开始撰写正文',
                    'can_execute': True
                }
            elif not status['has_detailed_outline'] and status['has_outline']:
                return {
                    'action': 'generate_detailed_outline',
                    'message': '大纲已完成，可以生成详细细纲',
                    'can_execute': True
                }
            elif status['has_chapters']:
                return {
                    'action': 'continue_writing',
                    'message': '已有章节，可以继续撰写',
                    'can_execute': True
                }
            else:
                return {
                    'action': 'none',
                    'message': '请先生成大纲',
                    'can_execute': False
                }
        
        elif story_id:
            if self.can_generate_outline(story_id):
                return {
                    'action': 'generate_outline',
                    'message': '企划书已完成，可以生成大纲',
                    'can_execute': True
                }
            else:
                return {
                    'action': 'none',
                    'message': '企划书内容不足',
                    'can_execute': False
                }
        
        return {
            'action': 'none',
            'message': '无可执行的操作',
            'can_execute': False
        }
