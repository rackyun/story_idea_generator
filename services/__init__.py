"""
业务逻辑层 (Services Layer)

将页面展示逻辑与业务逻辑分离，提供可复用的业务服务。
"""

from .story_service import StoryService
from .novel_service import NovelService
from .chapter_service import ChapterService
from .writing_service import WritingService
from .proposal_service import ProposalService
from .outline_service import OutlineService
from .detailed_outline_service import DetailedOutlineService
from .chapter_writing_service import ChapterWritingService
from .crew_orchestration_service import CrewOrchestrationService

__all__ = [
    'StoryService',
    'NovelService',
    'ChapterService',
    'WritingService',
    'ProposalService',
    'OutlineService',
    'DetailedOutlineService',
    'ChapterWritingService',
    'CrewOrchestrationService',
]
