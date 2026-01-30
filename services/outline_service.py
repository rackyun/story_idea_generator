"""
大纲生成服务

负责从企划书生成大纲的 Crew 创建和执行。
"""

from typing import Dict, Any
import signal
from database import DatabaseManager, NovelManager
from utils.novel_length_config import get_category_by_name


class OutlineService:
    """大纲生成服务类"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.novel_manager = NovelManager()

    @staticmethod
    def _setup_signal_patch():
        """设置 signal 补丁以兼容 Streamlit 多线程环境"""
        _original_signal = signal.signal

        def _safe_signal(sig, handler):
            try:
                return _original_signal(sig, handler)
            except ValueError as e:
                if "main thread" in str(e):
                    return None
                raise e

        signal.signal = _safe_signal

    @staticmethod
    def _disable_crewai_events_errors():
        """禁用 CrewAI 事件总线在 Streamlit 中的错误输出"""
        import logging
        import warnings

        try:
            crewai_events_logger = logging.getLogger("crewai.utilities.events")
            crewai_events_logger.setLevel(logging.ERROR)
            crewai_logger = logging.getLogger("crewai")
            crewai_logger.setLevel(logging.WARNING)
        except Exception:
            pass

        warnings.filterwarnings("ignore", message=".*Text.append.*")
        warnings.filterwarnings("ignore", message=".*CrewAIEventsBus.*")

    def generate_outline_from_proposal(
        self,
        story_id: int,
        target_word_count: str,
        novel_title: str = None
    ) -> Dict[str, Any]:
        """
        从企划书生成大纲
        
        Args:
            story_id: 企划书 ID
            target_word_count: 目标字数范围
            novel_title: 小说标题（可选，如果不提供则自动生成）
        
        Returns:
            {
                'novel_id': int,
                'outline_content': str,
                'success': bool,
                'error': str
            }
        """
        try:
            # 读取企划书内容
            story = self.db_manager.get_story(story_id)
            if not story:
                return {
                    'novel_id': None,
                    'outline_content': '',
                    'success': False,
                    'error': f"未找到 ID 为 {story_id} 的企划书"
                }

            proposal_content = story.get('content', '')
            if not proposal_content:
                return {
                    'novel_id': None,
                    'outline_content': '',
                    'success': False,
                    'error': "企划书内容为空"
                }

            # 设置环境
            self._setup_signal_patch()
            self._disable_crewai_events_errors()

            # 动态导入 CrewAI 相关库
            from crew_agents import StoryAgents
            from crew_tasks import StoryTasks
            from crewai import Crew, Process

            # 创建 Agents 和 Tasks
            agents = StoryAgents()
            tasks = StoryTasks()

            # 实例化大纲 Crew 所需的 Agents
            lead_outliner = agents.lead_outliner()
            character_arc_designer = agents.character_arc_designer()
            logic_validator = agents.logic_validator()
            outline_architect = agents.outline_architect()
            naming_expert = agents.naming_expert()

            # 创建任务流
            # 阶段1：读取理解企划书
            task_reading = tasks.outline_reading_task(lead_outliner, proposal_content)

            # 阶段2：生成分章大纲
            task_structuring = tasks.outline_structuring_task(
                outline_architect,
                context_reading=task_reading,
                target_word_count=target_word_count
            )

            # 阶段3：命名审查（优化大纲中的名称）
            task_naming = tasks.outline_naming_review_task(
                naming_expert,
                context_outline=task_structuring,
                proposal_content=proposal_content
            )

            # 阶段4：人物弧光验证（基于优化后的大纲）
            task_arc_check = tasks.character_enrichment_task(
                character_arc_designer,
                context_outline=task_naming
            )

            # 阶段5：逻辑验证
            # 使用 consistency_checker 作为逻辑验证的执行者
            consistency_checker = agents.consistency_checker()
            # 注意：这里需要一个逻辑验证任务，暂时复用 character_enrichment_task 的结构
            # 或者可以创建一个专门的 logic_validation_task

            # 组建 Crew
            crew = Crew(
                agents=[
                    lead_outliner,
                    outline_architect,
                    naming_expert,
                    character_arc_designer,
                    logic_validator
                ],
                tasks=[
                    task_reading,
                    task_structuring,
                    task_naming,
                    task_arc_check
                ],
                process=Process.sequential,
                verbose=True
            )

            # 执行
            result = crew.kickoff()

            # 提取大纲内容（优先使用命名审查后的版本）
            outline_content = ""
            
            # 优先从命名审查任务中提取
            if hasattr(task_naming, 'output') and task_naming.output:
                naming_output = str(task_naming.output)
                # 检查是否包含大纲内容（通常以 ### 第X章 开头）
                if '### 第' in naming_output or '## 第' in naming_output:
                    # 提取大纲部分（去除名称审查报告）
                    parts = naming_output.split('## 大纲名称审查报告')
                    if parts:
                        outline_content = parts[0].strip()
            
            # 如果命名审查输出无效，回退到结构化任务的输出
            if not outline_content or len(outline_content.strip()) < 500:
                if hasattr(result, 'raw'):
                    outline_content = str(result.raw)
                elif hasattr(result, 'content'):
                    outline_content = str(result.content)
                else:
                    outline_content = str(result)

            # 生成小说标题
            if not novel_title:
                # 从企划书或内容中提取标题
                from services.writing_service import WritingService
                novel_title = WritingService._extract_novel_title_from_content(
                    proposal_content,
                    fallback_title="未命名小说"
                )
                novel_title = f"{novel_title} - 大纲 ({target_word_count})"

            # 获取篇幅分类信息
            category = get_category_by_name(target_word_count)

            # 创建小说记录，content 字段存储大纲
            novel_id = self.novel_manager.save_novel(
                title=novel_title,
                topic=story.get('topic', ''),
                content=outline_content,  # 大纲存储在 content 字段
                source_story_id=story_id,
                metadata={
                    'type': 'outline',
                    'workflow_stage': 'outline',
                    'topic': story.get('topic', ''),
                    'length': target_word_count,
                    'source_id': story_id,
                    'source_type': 'crew_ai',
                    'category_key': category.key if category else 'unknown',
                    'outline_generated_at': self._get_current_timestamp()
                }
            )

            return {
                'novel_id': novel_id,
                'outline_content': outline_content,
                'success': True,
                'error': ''
            }

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {
                'novel_id': None,
                'outline_content': '',
                'success': False,
                'error': f"{str(e)}\n\n{error_detail}"
            }

    @staticmethod
    def _get_current_timestamp():
        """获取当前时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
