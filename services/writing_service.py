"""
AI 写作业务服务

处理 AI 写作相关的业务逻辑，包括小说生成、章节续写、大纲扩充等。
"""

from typing import Dict, List, Optional, Any
import json
import re
import signal
from database import (
    DatabaseManager, NovelManager, ChapterManager,
    NovelStatsManager, OutlineManager
)
from logic import load_config
from utils.novel_length_config import get_category_by_name


class WritingService:
    """AI 写作业务服务类"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.novel_manager = NovelManager()
        self.chapter_manager = ChapterManager()
        self.stats_manager = NovelStatsManager()
        self.outline_manager = OutlineManager()

    @staticmethod
    def _extract_novel_title_from_content(content: str, fallback_title: str = "未命名小说") -> str:
        """
        从企划书内容中提取小说名称
        
        Args:
            content: 企划书内容
            fallback_title: 如果无法提取则使用的默认标题
            
        Returns:
            提取的小说名称
        """
        if not content:
            return fallback_title
        
        import re
        
        # 尝试从内容中提取书名
        # 模式1: 《书名》格式
        pattern1 = r'《([^》]+)》'
        match1 = re.search(pattern1, content[:500])  # 只在前500字中搜索
        if match1:
            title = match1.group(1).strip()
            if 2 <= len(title) <= 30:  # 合理的书名长度
                return title
        
        # 模式2: "书名"格式
        pattern2 = r'["""]([^"""]{2,30})["""]'
        match2 = re.search(pattern2, content[:500])
        if match2:
            title = match2.group(1).strip()
            if 2 <= len(title) <= 30:
                return title
        
        # 模式3: 标题行（通常在第一行或前几行）
        lines = content.split('\n')[:5]  # 检查前5行
        for line in lines:
            line = line.strip()
            # 移除 Markdown 标题标记
            line = re.sub(r'^#+\s*', '', line)
            # 移除其他标记
            line = re.sub(r'^[《》【】\[\]()（）]', '', line)
            line = re.sub(r'[《》【】\[\]()（）]$', '', line)
            
            # 检查是否是合理的书名（长度、不含太多标点）
            if 2 <= len(line) <= 30 and line.count('。') < 2 and line.count('，') < 3:
                # 排除明显不是书名的内容
                if not any(keyword in line for keyword in ['企划书', '大纲', '灵感', '主题', '题材']):
                    return line
        
        # 模式4: 从"小说名称"、"书名"等关键词后提取
        pattern4 = r'(?:小说名称|书名|标题)[：:]\s*([^\n]{2,30})'
        match4 = re.search(pattern4, content[:500])
        if match4:
            title = match4.group(1).strip()
            title = re.sub(r'^[《》【】\[\]()（）]', '', title)
            title = re.sub(r'[《》【】\[\]()（）]$', '', title)
            if 2 <= len(title) <= 30:
                return title
        
        return fallback_title

    def _generate_novel_title(
        self,
        story_title: str,
        story_topic: str,
        novel_length: str,
        content: str = "",
        is_outline_only: bool = True,
        exclude_novel_id: Optional[int] = None
    ) -> str:
        """
        生成小说标题（带重名检查）
        
        Args:
            story_title: 源故事标题
            story_topic: 故事主题
            novel_length: 小说篇幅
            content: 企划书/大纲内容（可选，用于提取书名）
            is_outline_only: 是否只是大纲
            exclude_novel_id: 排除的小说ID（用于更新时避免与自身冲突）
            
        Returns:
            生成的小说标题（如果重名会自动添加序号）
        """
        # 优先从内容中提取书名
        base_title = ""
        if content:
            extracted_title = WritingService._extract_novel_title_from_content(content, "")
            if extracted_title and extracted_title != "未命名小说":
                base_title = extracted_title
                if is_outline_only:
                    base_title = f"{extracted_title} ({novel_length})"
        
        # 如果无法提取，使用源标题
        if not base_title:
            if story_title and story_title != "未知标题" and story_title != "未命名":
                # 清理标题（移除可能的"企划书 -"前缀）
                clean_title = story_title.replace("企划书 - ", "").replace("灵感 - ", "").strip()
                if clean_title:
                    base_title = f"{clean_title} ({novel_length})" if is_outline_only else clean_title
        
        # 使用主题作为标题
        if not base_title:
            if story_topic:
                topic_clean = story_topic[:30].strip()
                if topic_clean:
                    base_title = f"{topic_clean} ({novel_length})" if is_outline_only else topic_clean
        
        # 最后的默认值
        if not base_title:
            base_title = f"未命名小说 ({novel_length})" if is_outline_only else "未命名小说"
        
        # 检查重名并添加序号
        final_title = base_title
        counter = 1
        max_attempts = 100  # 防止无限循环
        
        while counter <= max_attempts:
            # 查询所有小说，然后精确匹配标题
            all_novels, _ = self.novel_manager.list_novels(page_size=1000)  # 获取足够多的记录
            # 过滤掉被排除的小说ID
            if exclude_novel_id:
                all_novels = [n for n in all_novels if n['id'] != exclude_novel_id]
            
            # 检查是否有完全匹配的标题
            has_duplicate = any(n['title'] == final_title for n in all_novels)
            
            if not has_duplicate:
                break
            
            # 如果有重名，添加序号
            counter += 1
            if is_outline_only and f"({novel_length})" in base_title:
                # 如果标题包含篇幅，在篇幅前添加序号
                final_title = base_title.replace(f"({novel_length})", f"({counter}) ({novel_length})")
            else:
                # 在标题末尾添加序号
                final_title = f"{base_title} ({counter})"
        
        return final_title

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
        
        # 方法1: 设置 CrewAI 事件相关的日志级别为 ERROR，减少输出
        try:
            crewai_events_logger = logging.getLogger("crewai.utilities.events")
            crewai_events_logger.setLevel(logging.ERROR)
            # 也设置 CrewAI 主日志记录器
            crewai_logger = logging.getLogger("crewai")
            crewai_logger.setLevel(logging.WARNING)
        except Exception:
            pass
        
        # 方法2: 使用警告过滤器忽略相关警告
        warnings.filterwarnings("ignore", message=".*Text.append.*")
        warnings.filterwarnings("ignore", message=".*CrewAIEventsBus.*")
        
        # 方法3: 尝试禁用 CrewAI 的事件总线（如果可能）
        try:
            from crewai.utilities.events import EventsBus
            # 如果事件总线有禁用方法，调用它
            if hasattr(EventsBus, 'disable'):
                EventsBus.disable()
        except (ImportError, AttributeError):
            pass

    @staticmethod
    def num_to_chinese(num: int) -> str:
        """
        将数字转换为汉字数字（支持1-99）

        Args:
            num: 数字

        Returns:
            汉字数字字符串
        """
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


    def continue_writing_chapters(
        self,
        novel_id: int,
        num_chapters: int,
        start_chapter: int = None,
        outline_content: str = None
    ) -> int:
        """
        智能续写章节（重构版：调用 ChapterWritingService）

        Args:
            novel_id: 小说ID
            num_chapters: 续写章节数
            start_chapter: 起始章节号（可选，如果不填则自动接续）
            outline_content: 指定的大纲内容（可选，如果不填则从数据库读取）

        Returns:
            成功续写的章节数
        """
        from services.chapter_writing_service import ChapterWritingService
        
        chapter_service = ChapterWritingService()
        result = chapter_service.write_chapters(
            novel_id=novel_id,
            num_chapters=num_chapters,
            start_chapter=start_chapter,
            outline_content=outline_content
        )
        
        if not result['success']:
            raise RuntimeError(result['error'])
        
        return result['chapters_written']
        self._disable_crewai_events_errors()

        from crew_agents import StoryAgents
        from crew_tasks import StoryTasks
        from crewai import Crew, Process

        # 召集写作团队
        agents = StoryAgents()
        tasks = StoryTasks()

        chief_editor = agents.chief_editor()
        character_builder = agents.character_builder()
        scene_painter = agents.scene_painter()
        punchline_king = agents.punchline_king()
        story_writer = agents.story_writer()
        consistency_checker = agents.consistency_checker()
        format_editor = agents.format_editor()

        # 创建任务流 - 使用大纲分析任务（已有大纲，不需要生成）
        task_plan = tasks.outline_analysis_task(
            chief_editor,
            outline_content=outline_text,
            previous_chapter_content=last_chapter_content,
            num_chapters=num_chapters,
            story_context=story_context
        )

        task_char = tasks.character_enrichment_task(character_builder, context_outline=task_plan)
        
        # 场景丰富和爆梗金句可以并发执行（都只依赖 task_plan）
        task_scene = tasks.scene_enrichment_task(scene_painter, context_outline=task_plan)
        # task_scene.async_execution = True  # 标记为异步执行，但在 sequential 模式下如果后续任务依赖它，必须同步等待
        
        task_punchline = tasks.punchline_injection_task(punchline_king, context_outline=task_plan)
        # task_punchline.async_execution = True  # 标记为异步执行，同上

        task_writing = tasks.full_story_writing_task(
            story_writer,
            context_materials=[task_plan, task_char, task_scene, task_punchline],
            num_chapters=num_chapters,
            chapter_start_num=next_chapter_num,
            use_chinese_numerals=True
        )

        task_edit = tasks.copy_editing_task(
            consistency_checker,
            context_draft=task_writing,
            num_chapters=num_chapters,
            chapter_start_num=next_chapter_num,
            use_chinese_numerals=True
        )

        # 格式编辑任务（在编辑润色之后）
        task_format = tasks.format_editing_task(
            format_editor,
            context_draft=task_edit,
            num_chapters=num_chapters,
            chapter_start_num=next_chapter_num,
            use_chinese_numerals=True
        )

        # 组建 Crew
        writing_crew = Crew(
            agents=[chief_editor, character_builder, scene_painter, punchline_king, story_writer, consistency_checker, format_editor],
            tasks=[task_plan, task_char, task_scene, task_punchline, task_writing, task_edit, task_format],
            process=Process.sequential,
            verbose=True
        )

        result = writing_crew.kickoff()

        # 处理结果 - 优先使用格式编辑后的输出
        generated_content = self._extract_content_from_result(result, task_format)
        
        # 如果格式编辑输出无效，回退到编辑润色的输出
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
                ch_outline_str = matching_segment['summary'] if matching_segment else ''

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
            outline_str = target_segments[0]['summary'] if target_segments else ''
            self.chapter_manager.create_chapter(
                novel_id=novel_id,
                chapter_number=next_chapter_num,
                chapter_title=f"第{self.num_to_chinese(next_chapter_num)}章 (待整理)",
                content=generated_content,
                outline=outline_str,
                status='draft'
            )
            count = 1

        return count

    def _extract_content_from_result(self, result: Any, task_writing: Any) -> str:
        """从 CrewAI 结果中提取内容"""
        generated_content = ""

        # 无效内容的标识（编辑代理没有正确接收到正文时会输出这些）
        invalid_markers = [
            "（见上）", "见上", "Please see above", "see above",
            "缺少输入文本", "未找到小说正文", "上下文中未找到",
            "missing input", "no content found", "context is empty"
        ]

        # 优先使用最终结果（编辑代理的输出）
        if hasattr(result, 'raw'):
            result_content = str(result.raw)
        elif hasattr(result, 'content'):
            result_content = str(result.content)
        else:
            result_content = str(result)

        # 检查编辑代理的输出是否有效
        is_valid = True

        # 检查是否包含无效标识
        for marker in invalid_markers:
            if marker.lower() in result_content.lower():
                is_valid = False
                print(f"检测到编辑代理输出无效标识: {marker}")
                break

        # 检查是否有有效的章节内容（必须包含 ## 第X章 格式）
        if is_valid:
            chapter_pattern = r'##\s*第[一二三四五六七八九十\d]+章'
            if not re.search(chapter_pattern, result_content):
                is_valid = False
                print("编辑代理输出未检测到有效章节格式")

        # 检查内容长度
        if is_valid and len(result_content.strip()) < 500:
            is_valid = False
            print(f"编辑代理输出长度不足: {len(result_content.strip())} 字符")

        if is_valid:
            generated_content = result_content

        # 如果编辑代理输出无效，回退到核心写手的输出
        if not generated_content or len(generated_content.strip()) < 500:
            print("编辑代理输出无效，尝试使用核心写手的输出")
            try:
                if hasattr(task_writing, 'output') and task_writing.output:
                    writing_output = str(task_writing.output)
                    if len(writing_output.strip()) > 500:
                        # 再次验证核心写手的输出
                        chapter_pattern = r'##\s*第[一二三四五六七八九十\d]+章'
                        if re.search(chapter_pattern, writing_output):
                            generated_content = writing_output
                            print("成功回退到核心写手的输出")
                        else:
                            print("核心写手的输出也未检测到有效章节格式")
            except Exception as e:
                print(f"获取核心写手输出时出错: {str(e)}")

        # 如果还是无效，使用最终结果（可能需要后续手动处理）
        if not generated_content:
            generated_content = result_content if result_content else ""
            print("警告：未能获取有效的章节内容，使用原始结果")

        return generated_content

    def _process_chapter_title(
        self,
        chapter_title: str,
        matching_segment: Optional[Dict],
        content: str,
        chapter_num: int
    ) -> str:
        """处理章节标题，确保包含章节编号"""
        chinese_num = self.num_to_chinese(chapter_num)
        chapter_prefix = f"第{chinese_num}章"
        
        # 如果标题为空或无效，尝试从其他地方获取
        if not chapter_title or chapter_title == '正文' or len(chapter_title.strip()) < 2:
            # 尝试从大纲段获取标题
            if matching_segment and matching_segment.get('title'):
                title = matching_segment['title']
                # 如果标题不包含章节编号，添加它
                if not title.startswith('第') or '章' not in title:
                    return f"{chapter_prefix} {title}"
                return title
            # 或者从内容第一行提取
            elif content:
                first_line = content.split('\n')[0].strip()
                first_line = re.sub(r'^[#\s]+', '', first_line)
                # 检查是否包含章节编号
                if first_line and 5 <= len(first_line) <= 50:
                    if not first_line.startswith('第') or '章' not in first_line:
                        return f"{chapter_prefix} {first_line}"
                    return first_line
                else:
                    return chapter_prefix
            else:
                return chapter_prefix
        
        # 如果标题不包含章节编号，添加它
        if not chapter_title.startswith('第') or '章' not in chapter_title:
            return f"{chapter_prefix} {chapter_title}"
        
        return chapter_title

    def expand_outline(
        self,
        novel_id: int,
        num_chapters: int = None,
        chapters_per_block: int = 5,
        start_chapter: int = None,
        end_chapter: int = None,
        custom_prompt: str = None
    ) -> int:
        """
        智能扩充大纲（重构版：调用 DetailedOutlineService）

        Args:
            novel_id: 小说ID
            num_chapters: 总扩充章节数（如果指定了 start_chapter 和 end_chapter，此参数将被忽略）
            chapters_per_block: 每几章一段
            start_chapter: 起始章节号（可选，如果指定则必须同时指定 end_chapter）
            end_chapter: 结束章节号（可选，如果指定则必须同时指定 start_chapter）

        Returns:
            成功生成的大纲段数
        """
        from services.detailed_outline_service import DetailedOutlineService
        
        # 参数验证和处理
        if start_chapter is not None and end_chapter is not None:
            if start_chapter > end_chapter:
                raise ValueError("起始章节不能大于结束章节")
            if start_chapter < 1:
                raise ValueError("起始章节必须大于0")
            chapter_range = (start_chapter, end_chapter)
        elif start_chapter is not None or end_chapter is not None:
            raise ValueError("起始章节和结束章节必须同时指定")
        else:
            # 使用传统模式：从最后一章之后开始
            if num_chapters is None:
                raise ValueError("必须指定扩充章节数或起止章节")
            
            # 计算下一个章节号
            current_segments = self.outline_manager.list_outline_segments(novel_id)
            next_chapter = 1
            if current_segments:
                next_chapter = max(seg['end_chapter'] for seg in current_segments) + 1
            
            chapter_range = (next_chapter, next_chapter + num_chapters - 1)
        
        # 调用细纲服务
        detailed_outline_service = DetailedOutlineService()
        result = detailed_outline_service.generate_detailed_outline(
            novel_id=novel_id,
            chapter_range=chapter_range,
            chapters_per_block=chapters_per_block,
            custom_prompt=custom_prompt
        )
        
        if not result['success']:
            raise RuntimeError(result['error'])
        
        return result['segments_created']

    def _parse_and_create_outline_segments(
        self,
        generated_content: str,
        novel_id: int,
        next_chapter: int,
        num_chapters: int,
        chapters_per_block: int
    ) -> int:
        """解析并创建大纲段"""
        segments_created = 0

        try:
            json_content = generated_content
            if "```json" in json_content:
                json_content = json_content.split("```json")[1].split("```")[0]
            elif "```" in json_content:
                json_content = json_content.split("```")[1].split("```")[0]

            json_match = re.search(r'\[.*\]', json_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    json_data = json.loads(json_str)
                except json.JSONDecodeError:
                    import ast
                    json_data = ast.literal_eval(json_str)

                if isinstance(json_data, list):
                    for item in json_data:
                        # 支持范围格式
                        if 'chapter_start' in item and 'chapter_end' in item:
                            start_ch = int(item['chapter_start'])
                            end_ch = int(item['chapter_end'])
                        elif 'start_chapter' in item and 'end_chapter' in item:
                            start_ch = int(item['start_chapter'])
                            end_ch = int(item['end_chapter'])
                        else:
                            start_ch = next_chapter + segments_created * chapters_per_block
                            end_ch = start_ch + chapters_per_block - 1

                        title = item.get('title', f'大纲段 {segments_created + 1}')
                        summary = item.get('summary', '') or item.get('description', '')

                        self.outline_manager.create_outline_segment(
                            novel_id=novel_id,
                            start_chapter=start_ch,
                            end_chapter=end_ch,
                            title=title,
                            summary=summary,
                            status='active',
                            priority=0
                        )
                        segments_created += 1
        except Exception:
            pass

        # 如果解析失败，创建一个默认段
        if segments_created == 0:
            self.outline_manager.create_outline_segment(
                novel_id=novel_id,
                start_chapter=next_chapter,
                end_chapter=next_chapter + num_chapters - 1,
                title="智能生成大纲 (待整理)",
                summary=generated_content[:500],
                status='draft',
                priority=0
            )
            segments_created = 1

        return segments_created
