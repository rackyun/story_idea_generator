"""
细纲生成服务

负责从大纲生成详细细纲的 Crew 创建和执行。
"""

from typing import Dict, Any, Tuple, Optional
import signal
import json
import re
from database import DatabaseManager, NovelManager, OutlineManager


class DetailedOutlineService:
    """细纲生成服务类"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.novel_manager = NovelManager()
        self.outline_manager = OutlineManager()

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

    def generate_detailed_outline(
        self,
        novel_id: int,
        chapter_range: Tuple[int, int] = None,
        chapters_per_block: int = 5,
        custom_prompt: str = None
    ) -> Dict[str, Any]:
        """
        生成详细细纲
        
        Args:
            novel_id: 小说 ID
            chapter_range: 章节范围 (start, end)，如果为 None 则自动计算
            chapters_per_block: 每几章生成一段
        
        Returns:
            {
                'segments_created': int,
                'success': bool,
                'error': str
            }
        """
        try:
            # 读取大纲和企划书
            novel = self.novel_manager.get_novel(novel_id)
            if not novel:
                return {
                    'segments_created': 0,
                    'success': False,
                    'error': f"未找到 ID 为 {novel_id} 的小说记录"
                }

            outline_content = novel.get('content', '')
            if not outline_content:
                return {
                    'segments_created': 0,
                    'success': False,
                    'error': "大纲内容为空"
                }

            # 获取企划书内容（如果有）
            proposal_content = ""
            if novel.get('source_story_id'):
                source_story = self.db_manager.get_story(novel['source_story_id'])
                if source_story:
                    proposal_content = source_story.get('content', '')
                    # 截取前5000字（增加长度以确保关键信息完整）
                    if len(proposal_content) > 5000:
                        proposal_content = proposal_content[:5000] + "...\n(内容已截断，但请确保遵循企划书的核心设定)"

            # 确定章节范围
            if chapter_range:
                start_chapter, end_chapter = chapter_range
                num_chapters = end_chapter - start_chapter + 1
            else:
                # 自动计算：查看已有的细纲，生成下一段
                existing_segments = self.outline_manager.list_outline_segments(novel_id)
                if existing_segments:
                    # 找到最大的 end_chapter
                    max_end_chapter = max(seg['end_chapter'] for seg in existing_segments)
                    start_chapter = max_end_chapter + 1
                else:
                    start_chapter = 1
                
                # 默认生成 chapters_per_block 章
                end_chapter = start_chapter + chapters_per_block - 1
                num_chapters = chapters_per_block

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

            # 实例化细纲 Crew 所需的 Agents
            narrative_planner = agents.narrative_planner()
            scene_weaver = agents.scene_weaver()

            # 创建任务：为指定章节范围生成细纲
            task_detailed = tasks.detailed_outline_task(
                scene_weaver,
                chapter_range=(start_chapter, end_chapter),
                outline_content=outline_content,
                proposal_content=proposal_content,
                custom_prompt=custom_prompt
            )

            # 组建 Crew
            crew = Crew(
                agents=[
                    narrative_planner,
                    scene_weaver
                ],
                tasks=[
                    task_detailed
                ],
                process=Process.sequential,
                verbose=True
            )

            # 执行
            result = crew.kickoff()

            # 提取细纲内容
            if hasattr(result, 'raw'):
                detailed_content = str(result.raw)
            elif hasattr(result, 'content'):
                detailed_content = str(result.content)
            else:
                detailed_content = str(result)

            # 解析并保存到 outline_segments 表
            segments_created = self._parse_and_save_segments(
                novel_id,
                detailed_content,
                start_chapter,
                end_chapter
            )

            # 更新小说元数据
            metadata = novel.get('metadata', {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            metadata['workflow_stage'] = 'detailed_outline'
            metadata['detailed_outline_generated_at'] = self._get_current_timestamp()
            
            self.novel_manager.update_novel(
                novel_id,
                metadata=metadata
            )

            return {
                'segments_created': segments_created,
                'success': True,
                'error': ''
            }

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {
                'segments_created': 0,
                'success': False,
                'error': f"{str(e)}\n\n{error_detail}"
            }

    def _parse_and_save_segments(
        self,
        novel_id: int,
        detailed_content: str,
        start_chapter: int,
        end_chapter: int
    ) -> int:
        """解析细纲内容并保存为 segments"""
        segments_created = 0

        try:
            # 尝试按章节拆分（假设格式为 ### 第X章）
            chapter_pattern = r'###\s*第([一二三四五六七八九十\d]+)章\s*(.+?)(?=###\s*第[一二三四五六七八九十\d]+章|$)'
            matches = re.findall(chapter_pattern, detailed_content, re.DOTALL)

            if matches:
                # 按章节保存
                for chapter_num_str, chapter_content in matches:
                    # 转换汉字数字到阿拉伯数字
                    chapter_num = self._chinese_to_num(chapter_num_str)
                    if start_chapter <= chapter_num <= end_chapter:
                        # 提取标题
                        title_match = re.search(r'第.+?章\s*[：:-]?\s*(.+?)(?:\n|$)', chapter_content)
                        title = title_match.group(1).strip() if title_match else f"第{chapter_num}章"

                        self.outline_manager.create_outline_segment(
                            novel_id=novel_id,
                            start_chapter=chapter_num,
                            end_chapter=chapter_num,
                            title=title,
                            summary=chapter_content.strip(),
                            status='active',
                            priority=0
                        )
                        segments_created += 1
            else:
                # 如果无法按章节拆分，创建一个整体段
                self.outline_manager.create_outline_segment(
                    novel_id=novel_id,
                    start_chapter=start_chapter,
                    end_chapter=end_chapter,
                    title=f"第{start_chapter}-{end_chapter}章细纲",
                    summary=detailed_content[:2000],  # 截取前2000字
                    status='active',
                    priority=0
                )
                segments_created = 1

        except Exception as e:
            print(f"解析细纲时出错: {str(e)}")
            # 创建一个默认段
            self.outline_manager.create_outline_segment(
                novel_id=novel_id,
                start_chapter=start_chapter,
                end_chapter=end_chapter,
                title=f"第{start_chapter}-{end_chapter}章细纲 (待整理)",
                summary=detailed_content[:2000],
                status='draft',
                priority=0
            )
            segments_created = 1

        return segments_created

    @staticmethod
    def _chinese_to_num(chinese_num_str: str) -> int:
        """将汉字数字转换为阿拉伯数字"""
        # 如果已经是数字，直接返回
        if chinese_num_str.isdigit():
            return int(chinese_num_str)

        chinese_nums = {
            '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
            '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
        }

        if chinese_num_str in chinese_nums:
            return chinese_nums[chinese_num_str]

        # 处理"十一"到"九十九"
        if '十' in chinese_num_str:
            if chinese_num_str == '十':
                return 10
            elif chinese_num_str.startswith('十'):
                return 10 + chinese_nums.get(chinese_num_str[1], 0)
            else:
                parts = chinese_num_str.split('十')
                tens = chinese_nums.get(parts[0], 0) * 10
                ones = chinese_nums.get(parts[1], 0) if len(parts) > 1 and parts[1] else 0
                return tens + ones

        return 1  # 默认返回1

    @staticmethod
    def _get_current_timestamp():
        """获取当前时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
