"""
企划书生成服务

负责企划书 Crew 的创建和执行，将页面层的企划书生成逻辑移至服务层。
"""

from typing import Dict, Any
import signal
from database import DatabaseManager
from logic import HistoryManager


class ProposalService:
    """企划书生成服务类"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.history_manager = HistoryManager()

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

        try:
            from crewai.utilities.events import EventsBus
            if hasattr(EventsBus, 'disable'):
                EventsBus.disable()
        except (ImportError, AttributeError):
            pass

    def generate_proposal(
        self,
        topic: str,
        target_word_count: str,
        brainstorm_rounds: int = 3
    ) -> Dict[str, Any]:
        """
        生成企划书
        
        Args:
            topic: 小说主题/核心创意
            target_word_count: 目标字数范围
            brainstorm_rounds: 脑暴迭代轮次
        
        Returns:
            {
                'story_id': int,
                'content': str,
                'success': bool,
                'error': str
            }
        """
        try:
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

            # 实例化企划书 Crew 所需的 Agents
            market_analyst = agents.market_analyst()
            creative_director = agents.creative_director()
            world_builder = agents.world_builder()
            idea_stormer = agents.idea_stormer()
            plot_weaver = agents.plot_weaver()
            character_builder = agents.character_builder()
            scene_painter = agents.scene_painter()
            climax_optimizer = agents.climax_optimizer()
            naming_expert = agents.naming_expert()
            consistency_checker = agents.consistency_checker()

            # 创建任务流
            # 阶段1：市场分析
            task_market = tasks.market_analysis_task(market_analyst, topic)

            # 阶段2：脑暴创意
            task_brainstorm = tasks.brainstorm_task(idea_stormer, topic, rounds=brainstorm_rounds)

            # 阶段3：剧情大纲
            task_plot = tasks.plot_development_task(
                plot_weaver,
                context_idea=task_brainstorm,
                target_word_count=target_word_count
            )

            # 阶段4：角色、场景、高潮设计（可并发）
            task_character = tasks.character_design_task(character_builder, context_plot=task_plot)
            task_character.async_execution = True

            task_scene = tasks.scene_enhancement_task(scene_painter, context_plot=task_plot)
            task_scene.async_execution = True

            task_climax = tasks.climax_optimization_task(climax_optimizer, context_plot=task_plot)
            task_climax.async_execution = True

            # 阶段5：整合企划书
            full_context = [task_market, task_brainstorm, task_plot, task_character, task_scene, task_climax]
            task_proposal = tasks.proposal_writing_task(
                creative_director,
                context_tasks=full_context
            )

            # 阶段6：命名审查（在最终审核之前）
            task_naming = tasks.naming_review_task(
                naming_expert,
                context_proposal=task_proposal
            )

            # 阶段7：最终审核
            task_review = tasks.final_review_task(
                consistency_checker,
                full_context=[task_naming],  # 使用命名审查后的版本
                target_word_count=target_word_count
            )

            # 组建 Crew
            crew = Crew(
                agents=[
                    market_analyst,
                    creative_director,
                    world_builder,
                    idea_stormer,
                    plot_weaver,
                    character_builder,
                    scene_painter,
                    climax_optimizer,
                    naming_expert,
                    consistency_checker
                ],
                tasks=[
                    task_market,
                    task_brainstorm,
                    task_plot,
                    task_character,
                    task_scene,
                    task_climax,
                    task_proposal,
                    task_naming,
                    task_review
                ],
                process=Process.sequential,
                verbose=True
            )

            # 执行
            result = crew.kickoff()

            # 提取内容
            if hasattr(result, 'raw'):
                content = str(result.raw)
            elif hasattr(result, 'content'):
                content = str(result.content)
            else:
                content = str(result)

            # 保存到数据库
            story_id = self.history_manager.save_record(
                {"topic": topic, "type": "crew_ai"},
                content
            )

            return {
                'story_id': story_id,
                'content': content,
                'success': True,
                'error': ''
            }

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {
                'story_id': None,
                'content': '',
                'success': False,
                'error': f"{str(e)}\n\n{error_detail}"
            }
