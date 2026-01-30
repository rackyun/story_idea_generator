"""
章节撰写服务

将 writing_service.py 中的章节撰写 Crew 逻辑独立出来。
"""

from typing import Dict, Any, Optional
import signal
import json
import re
from database import DatabaseManager, NovelManager, ChapterManager, OutlineManager, NovelStatsManager


class ChapterWritingService:
    """章节撰写服务类"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.novel_manager = NovelManager()
        self.chapter_manager = ChapterManager()
        self.outline_manager = OutlineManager()
        self.stats_manager = NovelStatsManager()

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

    def write_chapters(
        self,
        novel_id: int,
        num_chapters: int,
        start_chapter: int = None,
        outline_content: str = None
    ) -> Dict[str, Any]:
        """
        撰写章节
        
        Args:
            novel_id: 小说 ID
            num_chapters: 要撰写的章节数
            start_chapter: 起始章节号（可选，如果不填则自动接续）
            outline_content: 指定的大纲内容（可选，如果不填则从数据库读取）
        
        Returns:
            {
                'chapters_written': int,
                'success': bool,
                'error': str
            }
        """
        try:
            # 获取现有章节，确定下一章节号
            current_chapters = self.chapter_manager.list_chapters(novel_id)
            last_chapter_content = ""

            # 确定起始章节
            if start_chapter:
                next_chapter_num = start_chapter
                # 尝试找到上一章的内容
                if start_chapter > 1:
                    prev_ch = next((c for c in current_chapters if c['chapter_number'] == start_chapter - 1), None)
                    if prev_ch:
                        last_chapter_content = prev_ch.get('content', '')
            else:
                next_chapter_num = 1
                if current_chapters:
                    last_chapter = current_chapters[-1]
                    last_chapter_content = last_chapter.get('content', '')
                    next_chapter_num = last_chapter.get('chapter_number', 0) + 1

            end_chapter_num = next_chapter_num + num_chapters - 1

            # 确定大纲内容
            outline_text = ""
            target_segments = []

            if outline_content:
                # 使用用户手动指定的大纲
                outline_text = outline_content
            else:
                # 查询覆盖目标章节范围的大纲段
                target_segments = self.outline_manager.get_segments_by_chapter_range(
                    novel_id, next_chapter_num, end_chapter_num
                )

                if not target_segments:
                    return {
                        'chapters_written': 0,
                        'success': False,
                        'error': f"未找到第 {next_chapter_num}-{end_chapter_num} 章的大纲规划"
                    }

                # 格式化大纲段
                outline_for_writing = []
                for ch_num in range(next_chapter_num, end_chapter_num + 1):
                    matching_segment = next(
                        (seg for seg in target_segments
                         if seg['start_chapter'] <= ch_num <= seg['end_chapter']),
                        None
                    )
                    if matching_segment:
                        # 避免重复添加相同的段落
                        if not outline_for_writing or outline_for_writing[-1]['title'] != matching_segment['title']:
                            outline_for_writing.append({
                                'start_chapter': matching_segment['start_chapter'],
                                'end_chapter': matching_segment['end_chapter'],
                                'title': matching_segment['title'],
                                'summary': matching_segment['summary']
                            })

                outline_text = json.dumps(outline_for_writing, ensure_ascii=False, indent=2)

            # 获取企划书信息
            novel = self.novel_manager.get_novel(novel_id)
            story_context = ""
            if novel and novel.get('source_story_id'):
                source_story = self.db_manager.get_story(novel['source_story_id'])
                if source_story and source_story.get('content'):
                    story_context = source_story['content']
                    # 截取前3000字
                    if len(story_context) > 3000:
                        story_context = story_context[:3000] + "...\n(内容已截断)"

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

            # 实例化撰写 Crew 所需的 Agents
            chief_editor = agents.chief_editor()
            character_builder = agents.character_builder()
            scene_painter = agents.scene_painter()
            punchline_king = agents.punchline_king()
            story_writer = agents.story_writer()
            creative_critic = agents.creative_critic()
            continuity_coordinator = agents.continuity_coordinator()
            consistency_checker = agents.consistency_checker()
            format_editor = agents.format_editor()

            # 创建任务流
            task_plan = tasks.outline_analysis_task(
                chief_editor,
                outline_content=outline_text,
                previous_chapter_content=last_chapter_content,
                num_chapters=num_chapters,
                story_context=story_context
            )

            task_char = tasks.character_enrichment_task(character_builder, context_outline=task_plan)
            task_scene = tasks.scene_enrichment_task(scene_painter, context_outline=task_plan)
            task_punchline = tasks.punchline_injection_task(punchline_king, context_outline=task_plan)

            # 阶段1：写手撰写初稿
            task_writing = tasks.full_story_writing_task(
                story_writer,
                context_materials=[task_plan, task_char, task_scene, task_punchline],
                num_chapters=num_chapters,
                chapter_start_num=next_chapter_num,
                use_chinese_numerals=True
            )

            # 阶段2：创意批判专家提出意见（盲审同行评审）
            task_critique = tasks.creative_critique_task(
                creative_critic,
                context_draft=task_writing,
                num_chapters=num_chapters,
                chapter_start_num=next_chapter_num,
                use_chinese_numerals=True
            )

            # 阶段3：写手根据意见自行修订（保留独特文风）
            task_revision = tasks.story_revision_task(
                story_writer,
                context_draft=task_writing,
                context_critique=task_critique,
                num_chapters=num_chapters,
                chapter_start_num=next_chapter_num,
                use_chinese_numerals=True
            )

            # 阶段4：编辑润色（逻辑、文风统一）
            task_edit = tasks.copy_editing_task(
                consistency_checker,
                context_draft=task_revision,
                num_chapters=num_chapters,
                chapter_start_num=next_chapter_num,
                use_chinese_numerals=True
            )

            task_format = tasks.format_editing_task(
                format_editor,
                context_draft=task_edit,
                num_chapters=num_chapters,
                chapter_start_num=next_chapter_num,
                use_chinese_numerals=True
            )

            # 组建 Crew
            writing_crew = Crew(
                agents=[
                    chief_editor,
                    character_builder,
                    scene_painter,
                    punchline_king,
                    story_writer,
                    creative_critic,
                    continuity_coordinator,
                    consistency_checker,
                    format_editor
                ],
                tasks=[
                    task_plan,
                    task_char,
                    task_scene,
                    task_punchline,
                    task_writing,
                    task_critique,
                    task_revision,
                    task_edit,
                    task_format
                ],
                process=Process.sequential,
                verbose=True
            )

            # 执行
            result = writing_crew.kickoff()

            # 处理结果
            generated_content = self._extract_content_from_result(result, task_format)

            # 如果格式编辑输出无效，回退到修订后的输出
            if not generated_content or len(generated_content.strip()) < 500:
                generated_content = self._extract_content_from_result(result, task_revision)
            
            # 如果修订输出也无效，回退到编辑润色的输出
            if not generated_content or len(generated_content.strip()) < 500:
                generated_content = self._extract_content_from_result(result, task_edit)

            # 解析并保存章节
            parsed_new_chapters = self.chapter_manager.parse_chapters_from_content(generated_content)

            # 限制章节数量
            if parsed_new_chapters and len(parsed_new_chapters) > num_chapters:
                parsed_new_chapters = parsed_new_chapters[:num_chapters]

            count = 0
            if parsed_new_chapters:
                for ch in parsed_new_chapters:
                    actual_ch_num = next_chapter_num + count

                    # 查找对应的大纲段
                    matching_segment = next(
                        (seg for seg in target_segments
                         if seg['start_chapter'] <= actual_ch_num <= seg['end_chapter']),
                        None
                    )
                    
                    # 生成简要大纲描述（而非细纲的完整内容）
                    # 使用细纲的标题作为大纲描述，或者从内容中提取前200字
                    if matching_segment:
                        ch_outline_str = matching_segment.get('title', '')
                        # 如果标题太短，补充一些摘要信息（限制长度）
                        if len(ch_outline_str) < 10 and matching_segment.get('summary'):
                            summary_preview = matching_segment['summary'][:200].strip()
                            ch_outline_str = f"{ch_outline_str}: {summary_preview}" if ch_outline_str else summary_preview
                    else:
                        ch_outline_str = ''

                    # 处理章节标题
                    chapter_title = self._process_chapter_title(
                        ch.get('chapter_title', ''),
                        matching_segment,
                        ch.get('content', ''),
                        actual_ch_num
                    )

                    self.chapter_manager.create_chapter(
                        novel_id=novel_id,
                        chapter_number=actual_ch_num,
                        chapter_title=chapter_title,
                        content=ch['content'],
                        outline=ch_outline_str,
                        status='published'
                    )
                    count += 1

                self.stats_manager.update_novel_metadata(novel_id)
            else:
                # 未能解析出章节，作为单章保存
                # 使用简要描述而非完整细纲
                if target_segments:
                    outline_str = target_segments[0].get('title', '')
                    if len(outline_str) < 10 and target_segments[0].get('summary'):
                        outline_str = target_segments[0]['summary'][:200].strip()
                else:
                    outline_str = ''
                    
                self.chapter_manager.create_chapter(
                    novel_id=novel_id,
                    chapter_number=next_chapter_num,
                    chapter_title=f"第{self._num_to_chinese(next_chapter_num)}章 (待整理)",
                    content=generated_content,
                    outline=outline_str,
                    status='draft'
                )
                count = 1

            # 更新小说元数据
            if novel:
                metadata = novel.get('metadata', {})
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                
                metadata['workflow_stage'] = 'writing'
                metadata['last_chapter_written'] = next_chapter_num + count - 1
                metadata['last_writing_at'] = self._get_current_timestamp()
                
                self.novel_manager.update_novel(
                    novel_id,
                    metadata=metadata
                )

            return {
                'chapters_written': count,
                'success': True,
                'error': ''
            }

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {
                'chapters_written': 0,
                'success': False,
                'error': f"{str(e)}\n\n{error_detail}"
            }

    def _extract_content_from_result(self, result, task):
        """从 CrewAI 结果中提取内容"""
        generated_content = ""

        # 无效内容的标识
        invalid_markers = [
            "（见上）", "见上", "Please see above", "see above",
            "缺少输入文本", "未找到小说正文", "上下文中未找到",
            "missing input", "no content found", "context is empty"
        ]

        # 优先使用最终结果
        if hasattr(result, 'raw'):
            result_content = str(result.raw)
        elif hasattr(result, 'content'):
            result_content = str(result.content)
        else:
            result_content = str(result)

        # 检查是否有效
        is_valid = True

        for marker in invalid_markers:
            if marker.lower() in result_content.lower():
                is_valid = False
                break

        if is_valid:
            chapter_pattern = r'##\s*第[一二三四五六七八九十\d]+章'
            if not re.search(chapter_pattern, result_content):
                is_valid = False

        if is_valid and len(result_content.strip()) < 500:
            is_valid = False

        if is_valid:
            generated_content = result_content

        # 如果无效，回退到任务输出
        if not generated_content or len(generated_content.strip()) < 500:
            try:
                if hasattr(task, 'output') and task.output:
                    writing_output = str(task.output)
                    if len(writing_output.strip()) > 500:
                        chapter_pattern = r'##\s*第[一二三四五六七八九十\d]+章'
                        if re.search(chapter_pattern, writing_output):
                            generated_content = writing_output
            except Exception:
                pass

        if not generated_content:
            generated_content = result_content if result_content else ""

        return generated_content

    def _process_chapter_title(self, chapter_title, matching_segment, content, chapter_num):
        """处理章节标题，确保包含章节编号"""
        chinese_num = self._num_to_chinese(chapter_num)
        chapter_prefix = f"第{chinese_num}章"

        if not chapter_title or chapter_title == '正文' or len(chapter_title.strip()) < 2:
            if matching_segment and matching_segment.get('title'):
                title = matching_segment['title']
                if not title.startswith('第') or '章' not in title:
                    return f"{chapter_prefix} {title}"
                return title
            elif content:
                first_line = content.split('\n')[0].strip()
                first_line = re.sub(r'^[#\s]+', '', first_line)
                if first_line and 5 <= len(first_line) <= 50:
                    if not first_line.startswith('第') or '章' not in first_line:
                        return f"{chapter_prefix} {first_line}"
                    return first_line
                else:
                    return chapter_prefix
            else:
                return chapter_prefix

        if not chapter_title.startswith('第') or '章' not in chapter_title:
            return f"{chapter_prefix} {chapter_title}"

        return chapter_title

    @staticmethod
    def _num_to_chinese(num: int) -> str:
        """将数字转换为汉字数字"""
        chinese_nums = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
        if num <= 10:
            return chinese_nums[num]
        elif num < 20:
            return '十' + (chinese_nums[num % 10] if num % 10 > 0 else '')
        elif num < 100:
            tens = num // 10
            ones = num % 10
            if ones == 0:
                return chinese_nums[tens] + '十'
            else:
                return chinese_nums[tens] + '十' + chinese_nums[ones]
        else:
            return str(num)

    @staticmethod
    def _get_current_timestamp():
        """获取当前时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
