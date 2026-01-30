"""
历史详情页面 (重构版)

使用 StoryService 和 WritingService 实现业务逻辑与页面展示分离。
"""

import streamlit as st
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.novel_length_config import get_display_options
from services import StoryService, WritingService

# 页面配置
st.set_page_config(
    page_title="历史详情",
    page_icon="📖",
    layout="wide"
)

# 初始化服务
@st.cache_resource
def get_services():
    return {
        'story': StoryService(),
        'writing': WritingService()
    }

services = get_services()

# 检查是否有传入的 story_id
if 'view_story_id' not in st.session_state:
    st.warning("请从历史管理页面选择一条记录查看")
    if st.button("⬅️ 返回历史管理"):
        st.switch_page("pages/1_📚_历史管理.py")
    st.stop()

story_id = st.session_state.view_story_id
view_type = st.session_state.get('view_story_type', 'story')

# 确保 story_id 是整数类型
try:
    story_id = int(story_id) if story_id is not None else None
except (ValueError, TypeError):
    st.error(f"无效的故事ID: {story_id}")
    if st.button("⬅️ 返回历史管理"):
        st.switch_page("pages/1_📚_历史管理.py")
    st.stop()

if story_id is None:
    st.error("未提供故事ID")
    if st.button("⬅️ 返回历史管理"):
        st.switch_page("pages/1_📚_历史管理.py")
    st.stop()

# 获取记录详情
story = services['story'].get_story_detail(story_id, view_type)

if not story:
    # 添加调试信息和数据库查询验证
    with st.expander("🔍 调试信息", expanded=False):
        st.write(f"**Story ID**: {story_id} (类型: {type(story_id).__name__})")
        st.write(f"**View Type**: {view_type}")
        st.write(f"**Session State**: {st.session_state.get('view_story_id')}")
        
        # 尝试直接查询数据库验证记录是否存在
        try:
            from database import DatabaseManager
            db_manager = DatabaseManager()
            
            # 查询 stories 表
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # 检查是否存在（包括已删除的）
            cursor.execute("SELECT id, type, title, is_deleted FROM stories WHERE id = ?", (story_id,))
            row_all = cursor.fetchone()
            
            # 检查是否存在且未删除
            cursor.execute("SELECT id, type, title FROM stories WHERE id = ? AND is_deleted = 0", (story_id,))
            row_active = cursor.fetchone()
            
            conn.close()
            
            st.write("**数据库查询结果**：")
            if row_all:
                st.write(f"- 记录存在（包括已删除）: ID={row_all[0]}, Type={row_all[1]}, Title={row_all[2]}, is_deleted={row_all[3]}")
            else:
                st.write("- 记录在 stories 表中不存在")
            
            if row_active:
                st.write(f"- 记录存在且未删除: ID={row_active[0]}, Type={row_active[1]}, Title={row_active[2]}")
            else:
                st.write("- 记录不存在或已被删除")
                
        except Exception as e:
            st.write(f"**数据库查询错误**: {str(e)}")
    
    st.error("记录不存在或已被删除")
    if st.button("⬅️ 返回历史管理"):
        st.switch_page("pages/1_📚_历史管理.py")
    st.stop()

# 显示记录详情
st.title(f"📖 {story.get('title', '未命名')}")

# 基本信息
col_info1, col_info2, col_info3 = st.columns(3)

with col_info1:
    type_name = {"base": "灵感生成", "crew_ai": "企划书", "full_novel": "完整小说"}
    story_type = story.get('type', 'base')
    st.metric("类型", type_name.get(story_type, story_type))

with col_info2:
    st.metric("创建时间", story.get('created_at', '未知'))

with col_info3:
    st.metric("ID", story.get('id', story_id))

st.markdown("---")

# 主题/标题编辑
with st.expander("✏️ 编辑信息", expanded=False):
    col_edit1, col_edit2 = st.columns(2)

    with col_edit1:
        new_title = st.text_input("标题", value=story.get('title', ''))

    with col_edit2:
        new_topic = st.text_input("主题", value=story.get('topic', ''))

    if st.button("💾 保存修改"):
        if new_title != story.get('title'):
            success = services['story'].update_story_info(
                story_id=story_id,
                story_type=story.get('type', 'base'),
                title=new_title
            )

            if success:
                st.success("修改已保存")
                st.rerun()
            else:
                st.error("保存失败")
        else:
            st.info("信息未变更")

# 元数据信息
if story.get('metadata'):
    with st.expander("📋 元数据", expanded=False):
        metadata = story.get('metadata', {})

        if story.get('type') == 'base':
            st.json({
                "题材": metadata.get('genre', ''),
                "主角类型": metadata.get('archetype', ''),
                "方向": metadata.get('direction', ''),
                "基调": metadata.get('tone', ''),
                "场景": metadata.get('setting', ''),
                "关键物品": metadata.get('key_element', ''),
                "反派": metadata.get('antagonist', '')
            })
        else:
            st.json(metadata)

# 内容展示和编辑
st.markdown("### 📝 内容")

# 如果是完整小说，显示提示并链接到小说管理
if story.get('type') == 'full_novel':
    st.info("这是一部完整小说，请前往小说管理页面查看章节详情")

    if st.button("📚 前往小说管理"):
        st.session_state.manage_novel_id = story_id
        st.switch_page("pages/3_📚_小说管理.py")
else:
    # 企划书和灵感可以编辑内容
    with st.expander("✏️ 编辑内容", expanded=False):
        edited_content = st.text_area(
            "企划书内容",
            value=story.get('content', ''),
            height=400,
            key=f"edit_content_{story_id}",
            help="可以直接编辑企划书内容，支持 Markdown 格式"
        )
        
        col_save_content, col_reset_content = st.columns([1, 4])
        with col_save_content:
            if st.button("💾 保存内容", key=f"save_content_{story_id}"):
                if edited_content != story.get('content', ''):
                    success = services['story'].update_story_info(
                        story_id=story_id,
                        story_type=story.get('type', 'base'),
                        content=edited_content
                    )
                    
                    if success:
                        st.session_state['content_save_success'] = True
                        st.rerun()
                    else:
                        st.error("保存失败")
                else:
                    st.info("内容未变更")
        
        with col_reset_content:
            if st.button("🔄 重置", key=f"reset_content_{story_id}"):
                st.rerun()

# 显示保存成功提示
if st.session_state.get('content_save_success', False):
    st.success("✅ 内容已保存")
    del st.session_state['content_save_success']

# 显示内容
content_container = st.container()
with content_container:
    st.markdown(story.get('content', ''))

# 下载按钮
col_download = st.columns([1, 1, 1, 3])

with col_download[0]:
    st.download_button(
        label="📥 下载 Markdown",
        data=story.get('content', ''),
        file_name=f"{story.get('title', 'untitled')}.md",
        mime="text/markdown"
    )

with col_download[1]:
    st.download_button(
        label="📥 下载 TXT",
        data=story.get('content', ''),
        file_name=f"{story.get('title', 'untitled')}.txt",
        mime="text/plain"
    )

st.markdown("---")

# 操作按钮
col_actions = st.columns([1, 1, 1, 1, 2])

with col_actions[0]:
    if st.button("🔄 重新生成"):
        st.session_state.regenerate_story_id = story_id
        st.session_state.regenerate_story_type = story.get('type', 'base')
        st.rerun()

with col_actions[1]:
    if story.get('type') == 'full_novel':
        if st.button("📚 章节管理"):
            st.session_state.manage_novel_id = story_id
            st.switch_page("pages/3_📚_小说管理.py")

with col_actions[2]:
    if st.button("🗑️ 删除记录"):
        if 'confirm_delete' not in st.session_state:
            st.session_state.confirm_delete = False

        st.session_state.confirm_delete = True

with col_actions[3]:
    if st.button("⬅️ 返回"):
        st.switch_page("pages/1_📚_历史管理.py")

# 重新生成企划书
if st.session_state.get('regenerate_story_id') == story_id:
    regenerate_type = st.session_state.get('regenerate_story_type', 'base')
    
    if regenerate_type == 'crew_ai':
        st.markdown("---")
        st.subheader("🔄 重新生成企划书")
        
        # 提取原始主题和创意要素
        original_topic = story.get('topic', '')
        original_content = story.get('content', '')
        metadata = story.get('metadata', {})
        
        # 优先从 metadata 中提取完整的创意要素（如果存在）
        # 检查 metadata 是否包含完整的创意要素（如 genre, archetype 等）
        has_full_elements = any(key in metadata for key in ['genre', 'archetype', 'direction', 'tone', 'setting', 'key_element', 'antagonist'])
        
        if has_full_elements:
            # 从 metadata 构建完整的创意要素格式（与 app.py 中的格式一致）
            crew_topic = (
                f"题材：{metadata.get('genre', '')}\n"
                f"主角：{metadata.get('archetype', '')}\n"
                f"方向：{metadata.get('direction', '')}\n"
                f"基调：{metadata.get('tone', '')}\n"
                f"背景世界：{metadata.get('setting', '')}\n"
                f"物品：{metadata.get('key_element', '')}\n"
                f"反派：{metadata.get('antagonist', '')}"
            )
            original_topic = crew_topic  # 使用完整的创意要素
            st.info("**原始创意要素**（从元数据提取）：")
            st.json({
                "题材": metadata.get('genre', ''),
                "主角": metadata.get('archetype', ''),
                "方向": metadata.get('direction', ''),
                "基调": metadata.get('tone', ''),
                "背景世界": metadata.get('setting', ''),
                "物品": metadata.get('key_element', ''),
                "反派": metadata.get('antagonist', '')
            })
        else:
            # 如果没有完整的创意要素，使用 topic 字段（topic 字段应该就是完整的创意要素文本）
            if not original_topic and original_content:
                # 尝试从 content 中提取第一行或前100字作为主题
                lines = original_content.split('\n')
                original_topic = lines[0][:100] if lines else original_content[:100]
            
            # 检查 topic 是否已经是完整的创意要素格式（包含"题材："、"主角："等关键词）
            if original_topic and any(keyword in original_topic for keyword in ['题材：', '主角：', '方向：', '基调：', '背景世界：', '物品：', '反派：']):
                st.info("**原始创意要素**（从主题字段提取）：")
                # 解析并显示创意要素
                elements_dict = {}
                for line in original_topic.split('\n'):
                    if '：' in line or ':' in line:
                        parts = line.split('：') if '：' in line else line.split(':')
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = parts[1].strip()
                            elements_dict[key] = value
                if elements_dict:
                    st.json(elements_dict)
                else:
                    st.text(original_topic[:500])
            else:
                st.info(f"**原始主题**: {original_topic[:200] if original_topic else '（无主题）'}")
        
        # 参数设置
        col_regen1, col_regen2 = st.columns(2)
        with col_regen1:
            brainstorm_rounds = st.slider(
                "🧠 脑暴迭代轮次",
                min_value=1,
                max_value=10,
                value=3,
                key="regen_brainstorm_rounds",
                help="决定脑洞代理进行自我批判和优化的次数"
            )
        
        with col_regen2:
            from utils.novel_length_config import get_display_options
            target_word_count = st.selectbox(
                "📏 目标字数范围",
                options=get_display_options(),
                index=1,
                key="regen_target_word_count",
                help="指导企划书中每一幕的大致字数规划"
            )
        
        col_regen_btn1, col_regen_btn2 = st.columns([1, 4])
        with col_regen_btn1:
            if st.button("🚀 开始重新生成", type="primary", key="btn_start_regenerate"):
                if not original_topic.strip():
                    st.warning("⚠️ 无法提取原始主题，请手动输入")
                else:
                    try:
                        # Monkeypatch signal.signal to ignore 'main thread' errors
                        import signal
                        _original_signal = signal.signal
                        def _safe_signal(sig, handler):
                            try:
                                return _original_signal(sig, handler)
                            except ValueError as e:
                                if "main thread" in str(e):
                                    return None
                                raise e
                        signal.signal = _safe_signal
                        
                        # 动态导入 CrewAI 相关库
                        from crew_agents import StoryAgents
                        from crew_tasks import StoryTasks
                        from crewai import Crew, Process
                        from logic import load_config
                        
                        config = load_config("config.yaml")
                        if not config:
                            st.error("请先配置 config.yaml")
                        else:
                            from services import ProposalService
                            proposal_service = ProposalService()
                            
                            with st.spinner("AI 写作团队正在重新创作企划书... (这可能需要几分钟)"):
                                result = proposal_service.generate_proposal(
                                    topic=original_topic,
                                    target_word_count=target_word_count,
                                    brainstorm_rounds=brainstorm_rounds
                                )
                                
                                if result['success']:
                                    new_story_id = result['story_id']
                                    
                                    # 创建关联关系
                                    from database import DatabaseManager
                                    db_manager = DatabaseManager()
                                    db_manager.create_relation(
                                        parent_id=story_id,
                                        child_id=new_story_id
                                    )
                                    
                                    st.success(f"✅ 企划书重新生成成功！新记录 ID: {new_story_id}")
                                    st.info("正在跳转到新生成的企划书...")
                                    
                                    # 清除重新生成状态
                                    del st.session_state.regenerate_story_id
                                    del st.session_state.regenerate_story_type
                                    
                                    # 跳转到新生成的记录
                                    st.session_state.view_story_id = new_story_id
                                    st.rerun()
                                else:
                                    st.error(f"重新生成失败: {result['error']}")
                    
                    except Exception as e:
                        st.error(f"重新生成失败: {str(e)}")
                        import traceback
                        with st.expander("查看详细错误信息"):
                            st.code(traceback.format_exc(), language="python")
        
        with col_regen_btn2:
            if st.button("❌ 取消", key="btn_cancel_regenerate"):
                del st.session_state.regenerate_story_id
                del st.session_state.regenerate_story_type
                st.rerun()
    else:
        st.info("当前记录类型不支持重新生成功能")
        if st.button("❌ 取消", key="btn_cancel_regenerate_other"):
            del st.session_state.regenerate_story_id
            del st.session_state.regenerate_story_type
            st.rerun()

# 删除确认
if st.session_state.get('confirm_delete', False):
    st.warning("⚠️ 确定要删除这条记录吗？此操作可以恢复。")
    col_confirm = st.columns([1, 1, 4])

    with col_confirm[0]:
        if st.button("✅ 确认删除"):
            if services['story'].delete_story(story_id):
                st.success("已删除")
                del st.session_state.view_story_id
                del st.session_state.confirm_delete
                st.switch_page("pages/1_📚_历史管理.py")

    with col_confirm[1]:
        if st.button("❌ 取消"):
            st.session_state.confirm_delete = False
            st.rerun()

# 重新生成历史
st.markdown("---")
st.subheader("🔗 重新生成历史")

history_records = [
    item for item in services['story'].get_story_history(story_id)
    if item.get('type') != 'full_novel'
]

if history_records:
    st.caption(f"此记录有 {len(history_records)} 个重新生成的版本")

    for idx, item in enumerate(history_records, 1):
        type_name = {"base": "灵感", "crew_ai": "企划书", "full_novel": "小说"}
        item_type = type_name.get(item.get('type', ''), item.get('type', ''))

        with st.expander(f"版本 {idx} [{item_type}] - {item['created_at']}"):
            st.markdown(f"**标题**: {item['title']}")
            st.caption(f"ID: {item['id']}")

            if st.button(f"查看版本 {idx}", key=f"view_history_{item['id']}"):
                st.session_state.view_story_id = item['id']
                st.rerun()
else:
    st.caption("暂无重新生成的历史记录")

st.markdown("---")

# 创建关联小说记录（仅对企划书和灵感显示）
if story.get('type') in ['base', 'crew_ai']:
    st.subheader("📚 创建关联小说")

    # 添加说明
    st.info("""
    📝 **创建说明**：
    - 创建一个空的小说记录，关联到当前企划书/灵感
    - 创建后可在小说管理页面添加章节、大纲等内容
    - 支持手动编辑或使用 AI 生成内容
    """)

    col_gen1, col_gen2 = st.columns([3, 1])

    with col_gen1:
        novel_length = st.selectbox(
            "选择小说篇幅",
            options=get_display_options(),
            index=0,
            key="detail_novel_length"
        )

    with col_gen2:
        st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)

        if st.button("➕ 创建小说", type="primary", key="btn_create_novel"):
            try:
                from database import NovelManager
                from utils.novel_length_config import get_category_by_name
                from services import WritingService

                # 获取篇幅分类信息
                category = get_category_by_name(novel_length)

                # 使用 WritingService 的命名优化方法生成标题
                writing_service = WritingService()
                story_content = story.get('content', '')
                novel_title = writing_service._generate_novel_title(
                    story_title=story.get('title', '未命名'),
                    story_topic=story.get('topic', ''),
                    novel_length=novel_length,
                    content=story_content,
                    is_outline_only=True,
                    exclude_novel_id=None  # 新建小说，不需要排除
                )

                # 创建小说记录
                novel_manager = NovelManager()
                novel_id = novel_manager.save_novel(
                    title=novel_title,
                    topic=story.get('topic', ''),
                    content="",  # 空内容
                    source_story_id=story_id,
                    metadata={
                        'type': 'outline_only',
                        'topic': story.get('topic', ''),
                        'length': novel_length,
                        'source_id': story_id,
                        'source_type': story.get('type', 'base'),
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

    st.markdown("---")

# 关联小说
st.subheader("📚 关联小说")

novel_records = services['story'].get_related_novels(story_id)

if novel_records:
    st.caption(f"从此记录生成了 {len(novel_records)} 部小说")

    for idx, novel in enumerate(novel_records, 1):
        with st.expander(f"📖 小说 {idx}: {novel['title']}", expanded=False):
            col_novel_info, col_novel_action = st.columns([3, 1])

            with col_novel_info:
                st.markdown(f"**创建时间**: {novel['created_at']}")

                # 显示小说元数据
                if novel.get('metadata'):
                    metadata = novel['metadata']
                    if metadata.get('length'):
                        st.caption(f"篇幅: {metadata['length']}")

                # 内容预览
                preview_text = novel.get('content', '')[:200]
                st.text(preview_text + "..." if len(preview_text) >= 200 else preview_text)

            with col_novel_action:
                if st.button("📖 查看详情", key=f"view_novel_{novel['id']}"):
                    st.session_state.view_story_id = novel['id']
                    st.session_state.view_story_type = 'novel'
                    st.rerun()

                if st.button("📚 小说管理", key=f"manage_novel_{novel['id']}"):
                    st.session_state.manage_novel_id = novel['id']
                    st.switch_page("pages/3_📚_小说管理.py")
else:
    if story.get('type') in ['base', 'crew_ai']:
        st.info('暂无关联小说，点击上方"开始撰写"按钮生成完整小说')
    else:
        st.caption("暂无关联小说")
