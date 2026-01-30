"""
历史管理页面 (重构版)

使用 StoryService 实现业务逻辑与页面展示分离。
"""

import streamlit as st
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import StoryService

# 页面配置
st.set_page_config(
    page_title="历史管理",
    page_icon="📚",
    layout="wide"
)

# 初始化服务
@st.cache_resource
def get_story_service():
    return StoryService()

story_service = get_story_service()

# 初始化 session state
if 'selected_records' not in st.session_state:
    st.session_state.selected_records = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

st.title("📚 历史记录管理")
st.markdown("管理所有生成的故事记录，支持搜索、筛选、删除和导出。")

# 侧边栏 - 搜索和筛选
with st.sidebar:
    st.header("🔍 搜索与筛选")

    # 搜索框
    search_query = st.text_input("搜索关键词", placeholder="输入标题、主题或内容...")

    # 类型筛选
    story_type = st.selectbox(
        "类型筛选",
        options=["全部", "灵感生成 (base)", "企划书 (crew_ai)", "完整小说 (full_novel)"]
    )

    # 映射类型
    type_mapping = {
        "全部": None,
        "灵感生成 (base)": "base",
        "企划书 (crew_ai)": "crew_ai",
        "完整小说 (full_novel)": "full_novel"
    }
    selected_type = type_mapping[story_type]

    # 排序选项
    sort_by = st.selectbox(
        "排序方式",
        options=["时间 (最新)", "时间 (最早)", "标题 (A-Z)", "类型"]
    )

    # 映射排序
    sort_mapping = {
        "时间 (最新)": "created_at DESC",
        "时间 (最早)": "created_at ASC",
        "标题 (A-Z)": "title ASC",
        "类型": "type ASC"
    }
    order_by = sort_mapping[sort_by]

    st.markdown("---")

    # 统计信息
    st.subheader("📊 统计")
    stats = story_service.get_statistics()

    st.metric("总记录数", stats['total'])
    st.metric("灵感", stats['灵感'])
    st.metric("企划", stats['企划'])
    st.metric("小说", stats['小说'])

# 主内容区
col_actions, col_page_size = st.columns([3, 1])

with col_actions:
    # 批量操作按钮
    col_del_all = st.columns([1, 1, 1, 3])

    if col_del_all[0].button("🗑️ 删除选中", disabled=len(st.session_state.selected_records) == 0):
        deleted_count = story_service.batch_delete_stories(st.session_state.selected_records)
        st.success(f"已删除 {deleted_count} 条记录")
        st.session_state.selected_records = []
        st.rerun()

    if col_del_all[1].button("📥 导出选中", disabled=len(st.session_state.selected_records) == 0):
        st.info("导出功能开发中...")

with col_page_size:
    page_size = st.selectbox("每页显示", [10, 20, 50, 100], index=1)

# 查询数据
stories, total_count = story_service.get_story_list(
    story_type=selected_type,
    search_query=search_query if search_query else None,
    page=st.session_state.current_page,
    page_size=page_size,
    order_by=order_by
)

# 计算总页数
total_pages = (total_count + page_size - 1) // page_size

# 显示结果
st.markdown(f"### 📝 共找到 {total_count} 条记录")

if stories:
    # 表格展示
    for story in stories:
        with st.container():
            col_check, col_info, col_actions = st.columns([0.5, 6, 2])

            # 复选框
            with col_check:
                is_selected = story['id'] in st.session_state.selected_records
                if st.checkbox("选择", key=f"check_{story['id']}", value=is_selected, label_visibility="hidden"):
                    if story['id'] not in st.session_state.selected_records:
                        st.session_state.selected_records.append(story['id'])
                else:
                    if story['id'] in st.session_state.selected_records:
                        st.session_state.selected_records.remove(story['id'])

            # 记录信息
            with col_info:
                # 类型标签
                type_emoji = {"base": "🎲", "crew_ai": "🤖", "full_novel": "📖"}
                type_name = {"base": "灵感", "crew_ai": "企划书", "full_novel": "小说"}

                emoji = type_emoji.get(story['type'], "📄")
                type_label = type_name.get(story['type'], story['type'])

                st.markdown(f"**{emoji} {story['title']}** `{type_label}` • ID: {story['id']}")
                st.caption(f"📅 {story['created_at']} | 主题: {story['topic'][:100]}")

                # 内容预览
                if story.get('content_preview'):
                    with st.expander("预览"):
                        st.text(story['content_preview'][:300] + "...")

            # 操作按钮
            with col_actions:
                col_view, col_del = st.columns(2)

                if col_view.button("查看", key=f"view_{story['id']}"):
                    # 确保 story_id 是整数类型
                    story_id = int(story['id']) if story.get('id') is not None else None
                    if story_id is not None:
                        st.session_state.view_story_id = story_id
                        st.session_state.view_story_type = 'story'  # 明确设置查看类型
                        st.switch_page("pages/2_📖_历史详情.py")
                    else:
                        st.error("无效的故事ID")

                if col_del.button("删除", key=f"del_{story['id']}"):
                    if story_service.delete_story(story['id']):
                        st.success("已删除")
                        st.rerun()

            st.divider()

    # 分页控件
    if total_pages > 1:
        col_prev, col_page_info, col_next = st.columns([1, 2, 1])

        with col_prev:
            if st.button("⬅️ 上一页", disabled=st.session_state.current_page == 1):
                st.session_state.current_page -= 1
                st.rerun()

        with col_page_info:
            st.markdown(f"<center>第 {st.session_state.current_page} / {total_pages} 页</center>",
                       unsafe_allow_html=True)

        with col_next:
            if st.button("下一页 ➡️", disabled=st.session_state.current_page >= total_pages):
                st.session_state.current_page += 1
                st.rerun()

else:
    st.info("暂无记录")

# 底部操作
st.markdown("---")
col_back = st.columns([1, 3])

with col_back[0]:
    if st.button("⬅️ 返回主页"):
        st.switch_page("app.py")
