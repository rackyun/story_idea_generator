"""
章节编辑页面 (重构版)

使用 ChapterService 实现业务逻辑与页面展示分离。
"""

import streamlit as st
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import ChapterService

# 页面配置
st.set_page_config(
    page_title="章节编辑",
    page_icon="✏️",
    layout="wide"
)

# 初始化服务
@st.cache_resource
def get_chapter_service():
    return ChapterService()

chapter_service = get_chapter_service()

# 检查是否有传入的 chapter_id
if 'edit_chapter_id' not in st.session_state:
    st.warning("请从小说管理页面选择一个章节编辑")
    if st.button("⬅️ 返回小说管理"):
        st.switch_page("pages/3_📚_小说管理.py")
    st.stop()

chapter_id = st.session_state.edit_chapter_id

# 获取章节详情
chapter = chapter_service.get_chapter_detail(chapter_id)

if not chapter:
    st.error("章节不存在或已被删除")
    if st.button("⬅️ 返回小说管理"):
        st.switch_page("pages/3_📚_小说管理.py")
    st.stop()

st.title(f"✏️ 编辑章节: {chapter['chapter_title']}")

# 显示保存成功/失败的提示（从 session_state 读取）
if st.session_state.get('chapter_save_success'):
    st.success("✅ 保存成功！")
    # 清除状态，避免重复显示
    del st.session_state['chapter_save_success']

if st.session_state.get('chapter_save_error'):
    st.error("❌ 保存失败，请重试")
    # 清除状态，避免重复显示
    del st.session_state['chapter_save_error']

# 章节信息
col_info1, col_info2, col_info3 = st.columns(3)

with col_info1:
    st.metric("章节序号", f"第 {chapter['chapter_number']} 章")

with col_info2:
    st.metric("字数", chapter_service.format_word_count(chapter['word_count']))

with col_info3:
    st.metric("状态", chapter['status'])

st.markdown("---")

# 编辑表单
with st.form("edit_chapter_form"):
    st.subheader("📝 编辑内容")

    # 章节标题
    new_title = st.text_input("章节标题", value=chapter['chapter_title'])

    # 章节大纲
    new_outline = st.text_area(
        "章节大纲（可选）",
        value=chapter.get('outline', ''),
        height=150,
        help="简要描述本章的主要情节和要点"
    )

    # 章节内容
    new_content = st.text_area(
        "章节内容",
        value=chapter['content'],
        height=400,
        help="编辑章节正文内容"
    )

    # 状态选择
    new_status = st.selectbox(
        "章节状态",
        options=["draft", "published", "archived"],
        index=["draft", "published", "archived"].index(chapter['status']),
        format_func=lambda x: {"draft": "草稿", "published": "已发布", "archived": "已归档"}[x]
    )

    # 保存按钮
    col_submit, col_cancel = st.columns([1, 1])

    with col_submit:
        if st.form_submit_button("💾 保存修改", type="primary"):
            # 检查是否有变更
            has_changes = (
                new_title != chapter['chapter_title'] or
                new_outline != chapter.get('outline', '') or
                new_content != chapter['content'] or
                new_status != chapter['status']
            )

            if has_changes:
                # 使用 service 层更新章节
                success = chapter_service.update_chapter_content(
                    chapter_id=chapter_id,
                    chapter_title=new_title if new_title != chapter['chapter_title'] else None,
                    outline=new_outline if new_outline != chapter.get('outline', '') else None,
                    content=new_content if new_content != chapter['content'] else None,
                    status=new_status if new_status != chapter['status'] else None
                )

                if success:
                    # 使用 session_state 保存保存成功状态，避免 rerun 后提示消失
                    st.session_state['chapter_save_success'] = True
                    st.session_state.edit_chapter_id = chapter_id  # 保持在编辑页面
                    st.rerun()
                else:
                    st.session_state['chapter_save_error'] = True
                    st.rerun()
            else:
                st.info("ℹ️ 没有内容变更")

    with col_cancel:
        if st.form_submit_button("❌ 取消"):
            del st.session_state.edit_chapter_id
            st.switch_page("pages/3_📚_小说管理.py")

st.markdown("---")

# 续写功能
st.subheader("✍️ 章节续写")

with st.expander("🚀 AI 续写（开发中）"):
    st.info("此功能将使用 AI 根据当前章节内容继续写作，开发中...")

    continue_length = st.slider("续写长度（字数）", 500, 5000, 2000, 500)

    context_chapters = st.number_input(
        "参考前几章内容",
        min_value=1,
        max_value=5,
        value=2,
        help="AI 会参考前几章的内容来保持风格一致"
    )

    direction_hint = st.text_area(
        "续写方向提示（可选）",
        placeholder="例如：出现一个新角色，发生意外转折等...",
        height=100
    )

    if st.button("🤖 开始续写", disabled=True):
        st.info("续写功能开发中，敬请期待！")

# 底部导航
st.markdown("---")

col_nav1, col_nav2, col_nav3 = st.columns(3)

with col_nav1:
    # 获取相邻章节
    adjacent = chapter_service.get_adjacent_chapters(chapter_id)
    prev_chapter = adjacent['prev']

    if prev_chapter:
        if st.button(f"⬅️ 上一章: {prev_chapter['chapter_title'][:20]}"):
            st.session_state.edit_chapter_id = prev_chapter['id']
            st.rerun()
    else:
        st.button("⬅️ 上一章", disabled=True)

with col_nav2:
    if st.button("📚 返回小说管理"):
        del st.session_state.edit_chapter_id
        st.switch_page("pages/3_📚_小说管理.py")

with col_nav3:
    next_chapter = adjacent['next']

    if next_chapter:
        if st.button(f"下一章: {next_chapter['chapter_title'][:20]} ➡️"):
            st.session_state.edit_chapter_id = next_chapter['id']
            st.rerun()
    else:
        st.button("下一章 ➡️", disabled=True)
