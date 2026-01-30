import streamlit as st
import os
from logic import load_config, Randomizer, StoryLLM, HistoryManager
from utils.novel_length_config import get_display_options, get_category_by_name
# CrewAI imports only loaded when needed to save startup time
# from crew_agents import StoryAgents
# from crew_tasks import StoryTasks
# from crewai import Crew, Process

# 设置页面配置
st.set_page_config(
    page_title="AI 小说创作助手",
    page_icon="📚",
    layout="wide"
)

# 加载配置和管理器
CONFIG_PATH = "config.yaml"
config = load_config(CONFIG_PATH)
history_manager = HistoryManager()

def init_session_state():
    if 'elements' not in st.session_state:
        st.session_state.elements = {}
    if 'crew_result' not in st.session_state:
        st.session_state.crew_result = ""
    if 'crew_topic_input' not in st.session_state:
        st.session_state.crew_topic_input = ""
    if 'crew_novel_result' not in st.session_state:
        st.session_state.crew_novel_result = ""

init_session_state()

# 侧边栏
with st.sidebar:
    st.header("⚙️ 设置")
    if config:
        st.success("✅ 配置文件已加载")
        with st.expander("查看当前配置 (脱敏)"):
            llm_conf = config.get("llm", {})
            st.write(f"**Base URL**: {llm_conf.get('base_url')}")
            st.write(f"**Model**: {llm_conf.get('model')}")
            key = llm_conf.get('api_key', '')
            masked_key = f"{key[:3]}...{key[-3:]}" if len(key) > 6 else "******"
            st.write(f"**API Key**: {masked_key}")

        # 骰子选项管理
        with st.expander("🎲 骰子选项管理"):
            st.caption("使用 LLM 生成新的骰子选项（超过 20 个会自动分批请求并去重）")
            col_count, col_btn = st.columns([2, 1])
            with col_count:
                option_count = st.number_input("每类选项数量", min_value=8, max_value=50, value=12, step=1)
            with col_btn:
                st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button("🔄 刷新", use_container_width=True, help="使用 LLM 生成新的骰子选项"):
                    from dice_options_manager import DiceOptionsManager

                    with st.spinner("正在使用 LLM 生成新选项..."):
                        try:
                            manager = DiceOptionsManager()
                            results = manager.refresh_all_options(config, count=option_count)

                            success_count = sum(1 for count in results.values() if count > 0)
                            total_count = len(results)

                            if success_count == total_count:
                                st.success(f"✅ 成功刷新所有 {total_count} 个类别的选项！")
                            elif success_count > 0:
                                st.warning(f"⚠️ 成功刷新 {success_count}/{total_count} 个类别")
                            else:
                                st.error("❌ 刷新失败，请检查配置")

                            # 显示详细结果
                            with st.expander("查看详细结果"):
                                for category, count in results.items():
                                    status = "✅" if count > 0 else "❌"
                                    st.write(f"{status} {category}: {count} 个选项")

                        except Exception as e:
                            st.error(f"刷新失败: {str(e)}")

            # 显示当前选项状态
            from dice_options_manager import DiceOptionsManager
            manager = DiceOptionsManager()
            stored_categories = manager.get_all_categories()

            if stored_categories:
                st.caption(f"已存储 {len(stored_categories)} 个类别的自定义选项")
            else:
                st.caption("当前使用默认选项")
    else:
        st.error(f"❌ 未找到配置文件: {CONFIG_PATH}")
        st.info("请在项目根目录下创建 config.yaml 并配置 llm 信息。")

    st.markdown("---")

    # 导航区域
    st.header("📚 功能导航")

    # 使用 button 实现页面跳转
    if st.button("📜 历史管理", use_container_width=True, help="查看、搜索、管理所有历史记录"):
        st.switch_page("pages/1_📚_历史管理.py")

    if st.button("📖 小说管理", use_container_width=True, help="管理长篇小说的章节、版本和导出"):
        st.switch_page("pages/3_📚_小说管理.py")

    st.markdown("---")

    # 快速统计
    st.header("📊 快速统计")
    records = history_manager.load_all_records()

    if records:
        # 统计各类型数量
        type_counts = {"base": 0, "crew_ai": 0, "full_novel": 0}

        for rec in records:
            elements = rec.get("elements", {})
            record_type = elements.get("type", "base")
            type_counts[record_type] = type_counts.get(record_type, 0) + 1

        st.metric("总记录数", len(records))
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("企划书", type_counts.get("crew_ai", 0))
        with col_s2:
            st.metric("小说", type_counts.get("full_novel", 0))
    else:
        st.caption("暂无历史记录")

    st.markdown("---")
    st.markdown("### 关于")
    st.markdown("AI 小说创作助手，支持灵感生成、企划书编写和完整小说创作。")

# 主界面
st.title("🤖 AI 小说创作助手")

# 灵感骰子区域
st.subheader("🎲 灵感骰子")
st.caption("点击骰子按钮随机生成创意要素，或手动输入您的创意")

col_dice, col_input = st.columns([1, 4])

with col_dice:
    st.markdown("<div style='padding-top: 8px;'></div>", unsafe_allow_html=True)
    if st.button("🎲 投掷骰子", use_container_width=True, help="随机生成一组创意要素"):
        elements = Randomizer.generate_random_elements()
        prompt = (
            f"题材：{elements['genre']}\n"
            f"主角：{elements['archetype']}\n"
            f"方向：{elements['direction']}\n"
            f"基调：{elements['tone']}\n"
            f"背景世界：{elements['setting']}\n"
            f"物品：{elements['key_element']}\n"
            f"反派：{elements['antagonist']}"
        )
        st.session_state.crew_topic_input = prompt
        st.session_state.elements = elements

with col_input:
    crew_topic = st.text_area(
        "小说主题/核心创意",
        key="crew_topic_input",
        height=180,
        placeholder="输入您的创意，或点击左侧骰子按钮随机生成..."
    )

# 显示骰子结果（如果有）
if st.session_state.get('elements'):
    elements = st.session_state.elements
    st.markdown("**当前骰子结果：**")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info(f"**题材**\n\n{elements.get('genre')}")
    with col2:
        st.info(f"**主角**\n\n{elements.get('archetype')}")
    with col3:
        st.info(f"**方向**\n\n{elements.get('direction')}")
    with col4:
        st.info(f"**基调**\n\n{elements.get('tone')}")

    col5, col6, col7 = st.columns(3)
    with col5:
        st.success(f"**背景世界**\n\n{elements.get('setting')}")
    with col6:
        st.success(f"**物品**\n\n{elements.get('key_element')}")
    with col7:
        st.error(f"**反派**\n\n{elements.get('antagonist')}")

st.markdown("---")

# 参数设置
col_rounds, col_words = st.columns(2)
with col_rounds:
    brainstorm_rounds = st.slider("🧠 脑暴迭代轮次", min_value=1, max_value=10, value=3, help="决定脑洞代理进行自我批判和优化的次数")
with col_words:
    target_word_count = st.selectbox(
        "📏 目标字数范围",
        options=get_display_options(),
        index=1,
        help="指导企划书中每一幕的大致字数规划"
    )

# 生成企划书
if st.button("🚀 生成企划书", type="primary", use_container_width=True):
    if not config:
        st.error("请先配置 config.yaml")
    elif not crew_topic.strip():
        st.warning("请先输入创意或投掷骰子")
    else:
        from services import ProposalService
        proposal_service = ProposalService()

        with st.spinner("AI 写作团队正在协作创作企划书... (这可能需要几分钟)"):
            result = proposal_service.generate_proposal(
                topic=crew_topic,
                target_word_count=target_word_count,
                brainstorm_rounds=brainstorm_rounds
            )

            if result['success']:
                st.session_state.crew_result = result['content']
                st.session_state.crew_story_id = result['story_id']
                st.success("✅ 企划书生成成功！")
                st.rerun()
            else:
                st.error(f"生成失败: {result['error']}")

# 显示企划书结果
if st.session_state.crew_result:
    st.markdown("---")
    st.markdown("### 📝 企划书")
    
    # 企划书编辑功能
    with st.expander("✏️ 编辑企划书", expanded=False):
        edited_plan = st.text_area(
            "企划书内容",
            value=str(st.session_state.crew_result),
            height=400,
            key="edit_plan_content",
            help="可以直接编辑企划书内容，支持 Markdown 格式。编辑后记得保存。"
        )
        
        col_save_plan, col_reset_plan = st.columns([1, 4])
        with col_save_plan:
            if st.button("💾 保存企划书", key="save_plan", type="primary"):
                # 获取关联的企划书 story_id
                source_story_id = st.session_state.get('crew_story_id', None)
                
                if source_story_id:
                    try:
                        from services import StoryService
                        story_service = StoryService()
                        
                        success = story_service.update_story_info(
                            story_id=source_story_id,
                            story_type="crew_ai",
                            content=edited_plan
                        )
                        
                        if success:
                            st.session_state.crew_result = edited_plan  # 更新显示的内容
                            st.session_state['plan_save_success'] = True
                            st.success("✅ 企划书已保存")
                            st.rerun()
                        else:
                            st.error("保存失败，请重试")
                    except Exception as e:
                        st.error(f"保存失败: {str(e)}")
                else:
                    st.warning("⚠️ 未找到关联的企划书 ID，无法保存。请先生成企划书。")
        
        with col_reset_plan:
            if st.button("🔄 重置", key="reset_plan"):
                st.rerun()
    
    # 显示保存成功提示
    if st.session_state.get('plan_save_success', False):
        st.success("✅ 企划书已保存到历史记录")
        del st.session_state['plan_save_success']
    
    # 显示企划书内容
    st.markdown(st.session_state.crew_result)

    st.download_button(
        label="📥 下载企划书",
        data=str(st.session_state.crew_result),
        file_name="story_plan.md",
        mime="text/markdown"
    )

    st.markdown("---")
    st.subheader("📋 生成大纲")

    # 检查是否可以生成大纲
    if st.session_state.get('crew_story_id'):
        from services import OutlineService, CrewOrchestrationService
        outline_service = OutlineService()
        orchestration = CrewOrchestrationService()

        # 检查是否可以生成大纲
        can_generate = orchestration.can_generate_outline(st.session_state.crew_story_id)

        if can_generate:
            st.info("📝 **下一步**：从企划书生成结构化大纲")

            col_outline_length, col_outline_btn = st.columns([3, 1])
            with col_outline_length:
                outline_length = st.selectbox(
                    "选择小说篇幅",
                    options=get_display_options(),
                    index=1,
                    key="outline_length_select"
                )

            with col_outline_btn:
                st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)

                if st.button("📋 生成大纲", type="primary", key="btn_generate_outline"):
                    with st.spinner("正在生成大纲... (这可能需要几分钟)"):
                        result = outline_service.generate_outline_from_proposal(
                            story_id=st.session_state.crew_story_id,
                            target_word_count=outline_length
                        )

                        if result['success']:
                            st.session_state.current_novel_id = result['novel_id']
                            st.session_state.current_outline = result['outline_content']
                            st.success(f"✅ 大纲生成成功！小说 ID: {result['novel_id']}")
                            st.info("可以继续生成细纲或前往小说管理页面")
                            st.rerun()
                        else:
                            st.error(f"生成失败: {result['error']}")

        # 显示大纲（如果已生成）
        if st.session_state.get('current_outline'):
            st.markdown("---")
            st.markdown("### 📋 生成的大纲")
            with st.expander("查看大纲内容", expanded=True):
                st.markdown(st.session_state.current_outline)

            # 细纲生成区域
            st.markdown("---")
            st.subheader("📝 生成细纲")

            if st.session_state.get('current_novel_id'):
                from services import DetailedOutlineService
                detailed_outline_service = DetailedOutlineService()

                can_generate_detailed = orchestration.can_generate_detailed_outline(st.session_state.current_novel_id)

                if can_generate_detailed:
                    st.info("📝 **下一步**：为指定章节范围生成详细细纲（场景节拍表）")

                    col_range, col_detailed_btn = st.columns([3, 1])
                    with col_range:
                        col_start, col_end = st.columns(2)
                        with col_start:
                            start_ch = st.number_input("起始章节", min_value=1, value=1, key="detailed_start_ch")
                        with col_end:
                            end_ch = st.number_input("结束章节", min_value=1, value=5, key="detailed_end_ch")

                    with col_detailed_btn:
                        st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)

                        if st.button("📝 生成细纲", type="primary", key="btn_generate_detailed"):
                            if start_ch > end_ch:
                                st.error("起始章节不能大于结束章节")
                            else:
                                with st.spinner(f"正在生成第 {start_ch}-{end_ch} 章的细纲... (这可能需要几分钟)"):
                                    result = detailed_outline_service.generate_detailed_outline(
                                        novel_id=st.session_state.current_novel_id,
                                        chapter_range=(start_ch, end_ch)
                                    )

                                    if result['success']:
                                        st.success(f"✅ 细纲生成成功！共生成 {result['segments_created']} 个段")
                                        st.info("可以前往小说管理页面撰写正文")
                                    else:
                                        st.error(f"生成失败: {result['error']}")

    st.markdown("---")
    st.subheader("📚 创建小说记录")

    # 添加说明
    st.info("""
    📝 **创建说明**：
    - 创建一个空的小说记录，关联到当前企划书
    - 创建后可在小说管理页面添加章节、大纲等内容
    - 支持手动编辑或使用 AI 生成内容
    """)

    col_len, col_btn = st.columns([3, 1])
    with col_len:
        novel_length = st.selectbox(
            "选择小说篇幅",
            options=get_display_options(),
            index=0,
            key="app_novel_length"
        )

    with col_btn:
        st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)

        if st.button("➕ 创建小说", type="primary", key="btn_app_create_novel"):
            try:
                # 获取关联的企划书 story_id
                source_story_id = st.session_state.get('crew_story_id', None)

                if source_story_id is None:
                    st.warning("⚠️ 未找到关联的企划书 ID，小说将独立保存")
                
                # 获取企划书信息
                from database import DatabaseManager, NovelManager
                from utils.novel_length_config import get_category_by_name
                from services import WritingService
                
                db_manager = DatabaseManager()
                story = db_manager.get_story(source_story_id) if source_story_id else None
                
                if not story and source_story_id:
                    st.warning("⚠️ 无法找到关联的企划书记录")
                else:
                    # 获取篇幅分类信息
                    category = get_category_by_name(novel_length)

                    # 使用 WritingService 的命名优化方法生成标题
                    writing_service = WritingService()
                    story_content = story.get('content', '') if story else str(st.session_state.crew_result)
                    novel_title = writing_service._generate_novel_title(
                        story_title=story.get('title', '未命名') if story else "企划书",
                        story_topic=story.get('topic', '') if story else "",
                        novel_length=novel_length,
                        content=story_content,
                        is_outline_only=True,
                        exclude_novel_id=None  # 新建小说，不需要排除
                    )

                    # 创建小说记录
                    novel_manager = NovelManager()
                    novel_id = novel_manager.save_novel(
                        title=novel_title,
                        topic=story.get('topic', '') if story else "",
                        content="",  # 空内容
                        source_story_id=source_story_id,
                        metadata={
                            'type': 'outline_only',
                            'topic': story.get('topic', '') if story else "",
                            'length': novel_length,
                            'source_id': source_story_id,
                            'source_type': story.get('type', 'crew_ai') if story else 'crew_ai',
                            'is_outline_only': True,
                            'category_key': category.key if category else 'unknown'
                        }
                    )

                    st.success(f"✅ 小说记录创建成功！ID: {novel_id}")
                    st.info("请前往小说管理页面添加章节和大纲内容")

                    # 跳转到小说管理页面
                    st.session_state.manage_novel_id = novel_id
                    st.switch_page("pages/3_📚_小说管理.py")

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                st.error(f"创建失败: {str(e)}")
                with st.expander("查看详细错误信息"):
                    st.code(error_details, language="python")

# 显示小说正文
if st.session_state.crew_novel_result:
    st.markdown("---")
    st.markdown("### 📖 小说正文")
    st.markdown(st.session_state.crew_novel_result)
    st.download_button(
        label="📥 下载小说正文",
        data=str(st.session_state.crew_novel_result),
        file_name="novel.md",
        mime="text/markdown"
    )
