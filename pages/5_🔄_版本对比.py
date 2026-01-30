"""
版本对比页面 (重构版)

使用 NovelService 实现业务逻辑与页面展示分离。
"""

import streamlit as st
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import NovelService
from utils.version_diff import VersionDiff

# 页面配置
st.set_page_config(
    page_title="版本对比",
    page_icon="🔄",
    layout="wide"
)

# 初始化服务
@st.cache_resource
def get_novel_service():
    return NovelService()

novel_service = get_novel_service()

st.title("🔄 版本对比")

# 检查是否有传入的版本 ID
if 'compare_version_id' not in st.session_state:
    st.warning("请从小说管理页面选择版本进行对比")
    if st.button("⬅️ 返回小说管理"):
        st.switch_page("pages/3_📚_小说管理.py")
    st.stop()

# 获取当前版本
version_id = st.session_state.compare_version_id
current_version = novel_service.get_version_detail(version_id)

if not current_version:
    st.error("版本不存在")
    if st.button("⬅️ 返回小说管理"):
        st.switch_page("pages/3_📚_小说管理.py")
    st.stop()

# 获取该小说的所有版本
novel_id = current_version['novel_id']
all_versions = novel_service.get_version_list(novel_id)

# 选择要对比的两个版本
st.subheader("📋 选择对比版本")

col_v1, col_v2 = st.columns(2)

with col_v1:
    version_options_1 = {f"{v['version_name']} ({v['created_at']})": v['id'] for v in all_versions}
    selected_v1_key = st.selectbox(
        "版本 1",
        options=list(version_options_1.keys()),
        index=list(version_options_1.values()).index(version_id) if version_id in version_options_1.values() else 0
    )
    version1_id = version_options_1[selected_v1_key]

with col_v2:
    version_options_2 = {f"{v['version_name']} ({v['created_at']})": v['id'] for v in all_versions if v['id'] != version1_id}

    if version_options_2:
        selected_v2_key = st.selectbox(
            "版本 2",
            options=list(version_options_2.keys())
        )
        version2_id = version_options_2[selected_v2_key]
    else:
        st.warning("没有其他版本可供对比")
        version2_id = None

# 开始对比
if version2_id and st.button("🔍 开始对比", type="primary"):
    st.session_state.comparing = True
    st.session_state.compare_v1 = version1_id
    st.session_state.compare_v2 = version2_id

# 显示对比结果
if st.session_state.get('comparing', False):
    v1_id = st.session_state.compare_v1
    v2_id = st.session_state.compare_v2

    v1 = novel_service.get_version_detail(v1_id)
    v2 = novel_service.get_version_detail(v2_id)

    if v1 and v2:
        st.markdown("---")
        st.subheader("📊 对比结果")

        # 获取版本内容
        content1 = v1['snapshot_data'].get('content', '')
        content2 = v2['snapshot_data'].get('content', '')

        # 计算差异摘要
        summary = VersionDiff.get_change_summary(content1, content2)

        # 显示摘要
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)

        with col_s1:
            st.metric("新增行数", summary['added'], delta=summary['added'] if summary['added'] > 0 else None)

        with col_s2:
            st.metric("删除行数", summary['deleted'], delta=-summary['deleted'] if summary['deleted'] > 0 else None, delta_color="inverse")

        with col_s3:
            st.metric("修改行数", summary['modified'])

        with col_s4:
            similarity = VersionDiff.calculate_similarity(content1, content2)
            st.metric("相似度", f"{similarity * 100:.1f}%")

        st.markdown("---")

        # 对比模式选择
        compare_mode = st.radio(
            "对比模式",
            options=["统一差异", "HTML 对比"],
            horizontal=True
        )

        if compare_mode == "统一差异":
            st.subheader("📝 统一差异格式")

            diff = VersionDiff.generate_unified_diff(
                content1, content2,
                name1=v1['version_name'],
                name2=v2['version_name']
            )

            formatted_diff = VersionDiff.format_diff_for_display(diff)

            # 使用 code block 显示
            st.code(formatted_diff, language="diff")

        elif compare_mode == "HTML 对比":
            st.subheader("🌐 HTML 对比视图")

            html_diff = VersionDiff.generate_html_diff(
                content1, content2,
                name1=v1['version_name'],
                name2=v2['version_name']
            )

            st.components.v1.html(html_diff, height=600, scrolling=True)

# 底部操作
st.markdown("---")

col_back = st.columns([1, 3])

with col_back[0]:
    if st.button("⬅️ 返回小说管理"):
        if 'comparing' in st.session_state:
            del st.session_state.comparing
        if 'compare_version_id' in st.session_state:
            del st.session_state.compare_version_id
        st.switch_page("pages/3_📚_小说管理.py")
