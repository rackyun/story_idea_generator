"""
小说管理页面 (重构版) - 完整版

这是合并后的完整版本，包含所有标签页功能。
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import NovelService, WritingService
from database import DatabaseManager

st.set_page_config(page_title="小说管理", page_icon="📚", layout="wide")

@st.cache_resource
def get_services():
    return {'novel': NovelService(), 'writing': WritingService(), 'db': DatabaseManager()}

services = get_services()
st.title("📚 小说管理")

stories, total = services['novel'].get_novel_list(page_size=100)
if not stories:
    st.info("暂无小说记录，请先在主页生成小说。")
    if st.button("⬅️ 返回主页"):
        st.switch_page("app.py")
    st.stop()

with st.sidebar:
    st.header("📖 选择小说")

    # 创建小说选项字典
    novel_options = {f"{s['title']} (ID: {s['id']})": s['id'] for s in stories}

    # 确定默认选中的索引
    default_index = 0
    if 'manage_novel_id' in st.session_state:
        manage_id = st.session_state.manage_novel_id
        if manage_id in novel_options.values():
            # 找到对应的索引
            keys = list(novel_options.keys())
            values = list(novel_options.values())
            default_index = values.index(manage_id)

    # 显示下拉选择框
    selected_novel_key = st.selectbox(
        "选择要管理的小说",
        options=list(novel_options.keys()),
        index=default_index,
        key="novel_selector"
    )

    # 获取选中的小说 ID
    selected_novel_id = novel_options[selected_novel_key]

    # 更新 session state
    st.session_state.manage_novel_id = selected_novel_id

    st.markdown("---")

    # 显示统计信息
    stats = services['novel'].get_novel_stats(selected_novel_id)
    st.metric("总章节数", stats.get('total_chapters', 0) or 0)
    st.metric("总字数", stats.get('total_words', 0) or 0)

current_novel = services['novel'].get_novel_detail(selected_novel_id)
col_title, col_link = st.columns([3, 1])
with col_title:
    st.subheader(current_novel['title'])
with col_link:
    if st.button("📖 查看详情页"):
        st.session_state.view_story_id = selected_novel_id
        st.session_state.view_story_type = 'novel'
        st.switch_page("pages/2_📖_历史详情.py")

# 显示流程状态
st.markdown("---")
from services import CrewOrchestrationService
orchestration = CrewOrchestrationService()
workflow_status = orchestration.get_workflow_status(selected_novel_id)

st.subheader("📊 创作流程状态")
col_progress, col_stage = st.columns([3, 1])
with col_progress:
    st.progress(workflow_status['progress'])
with col_stage:
    stage_names = {
        'proposal': '📝 企划书',
        'outline': '📋 大纲',
        'detailed_outline': '📝 细纲',
        'writing': '✍️ 正文',
        'completed': '✅ 完成'
    }
    current_stage = stage_names.get(workflow_status['current_stage'], '未知')
    st.metric("当前阶段", current_stage)

col_s1, col_s2, col_s3, col_s4 = st.columns(4)
with col_s1:
    st.metric("企划书", "✅" if workflow_status['has_proposal'] else "❌")
with col_s2:
    st.metric("大纲", "✅" if workflow_status['has_outline'] else "❌")
with col_s3:
    st.metric("细纲段数", workflow_status['outline_segment_count'])
with col_s4:
    st.metric("章节数", workflow_status['chapter_count'])

# 分步骤操作按钮
if not workflow_status['has_outline']:
    # 检查是否有企划书源
    source_story_id = current_novel.get('source_story_id')
    if source_story_id and orchestration.can_generate_outline(source_story_id):
        st.info("💡 **下一步操作**：从企划书生成大纲")
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("📋 生成大纲", type="primary", key="btn_gen_outline_top"):
                from services import OutlineService
                outline_service = OutlineService()
                
                with st.spinner("正在生成大纲... (这可能需要几分钟)"):
                    # 获取篇幅信息
                    metadata = current_novel.get('metadata', {})
                    if isinstance(metadata, str):
                        import json
                        try:
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}
                    target_length = metadata.get('length', '短篇小说 (1-10万字)')
                    
                    result = outline_service.generate_outline_from_proposal(
                        story_id=source_story_id,
                        target_word_count=target_length,
                        novel_title=current_novel['title']
                    )
                    
                    if result['success']:
                        st.success("✅ 大纲生成成功！")
                        # 更新当前小说的 content 字段
                        services['novel'].update_novel(selected_novel_id, content=result['outline_content'])
                        st.rerun()
                    else:
                        st.error(f"生成失败: {result['error']}")

elif workflow_status['has_outline'] and not workflow_status['has_detailed_outline']:
    st.info("💡 **下一步操作**：生成详细细纲（场景节拍表）")
    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1, 1, 1, 2])
    with col_btn1:
        detail_start = st.number_input("起始章节", min_value=1, value=1, key="detail_start_top")
    with col_btn2:
        detail_end = st.number_input("结束章节", min_value=1, value=5, key="detail_end_top")
    with col_btn3:
        st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("📝 生成细纲", type="primary", key="btn_gen_detailed_top"):
            if detail_start > detail_end:
                st.error("起始章节不能大于结束章节")
            else:
                from services import DetailedOutlineService
                detailed_outline_service = DetailedOutlineService()
                
                with st.spinner(f"正在生成第 {detail_start}-{detail_end} 章的细纲..."):
                    result = detailed_outline_service.generate_detailed_outline(
                        novel_id=selected_novel_id,
                        chapter_range=(detail_start, detail_end)
                    )
                    
                    if result['success']:
                        st.success(f"✅ 细纲生成成功！共生成 {result['segments_created']} 个段")
                        st.rerun()
                    else:
                        st.error(f"生成失败: {result['error']}")

elif workflow_status['has_detailed_outline'] and workflow_status['chapter_count'] == 0:
    st.info("💡 **下一步操作**：开始撰写正文")
    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1, 1, 1, 2])
    with col_btn1:
        write_start = st.number_input("起始章节", min_value=1, value=1, key="write_start_top")
    with col_btn2:
        write_num = st.number_input("章节数", min_value=1, max_value=5, value=1, key="write_num_top")
    with col_btn3:
        st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("✍️ 撰写正文", type="primary", key="btn_gen_chapter_top"):
            from services import ChapterWritingService
            chapter_service = ChapterWritingService()
            
            with st.spinner(f"正在撰写第 {write_start}-{write_start + write_num - 1} 章..."):
                result = chapter_service.write_chapters(
                    novel_id=selected_novel_id,
                    num_chapters=write_num,
                    start_chapter=write_start
                )
                
                if result['success']:
                    st.success(f"✅ 成功撰写 {result['chapters_written']} 章！")
                    st.rerun()
                else:
                    st.error(f"撰写失败: {result['error']}")

st.markdown("---")

tabs = st.tabs(["📝 章节管理", "📑 大纲管理", "📊 统计分析", "🕐 版本控制", "📥 导出", "⚙️ 设置"])

# Tab 1: 章节管理
with tabs[0]:
    st.header("📝 章节管理")
    
    # 获取最大章节号
    chapters = services['novel'].get_chapter_list(selected_novel_id)
    max_chapter = 0
    if chapters:
        max_chapter = max(c['chapter_number'] for c in chapters)
    
    next_chapter_default = max_chapter + 1

    with st.expander("✍️ 智能续写", expanded=False):
        col_cfg1, col_cfg2 = st.columns(2)
        with col_cfg1:
            start_chapter_input = st.number_input("起始章节号", 1, 9999, next_chapter_default, help="从哪一章开始续写")
        with col_cfg2:
            num_chapters_to_write = st.number_input("续写章节数", 1, 5, 1)
        
        # 自动查找对应的大纲段
        end_chapter_target = start_chapter_input + num_chapters_to_write - 1
        relevant_segments = services['novel'].get_segments_by_chapter_range(selected_novel_id, start_chapter_input, end_chapter_target)
        
        outline_preview = ""
        if relevant_segments:
            # 拼接相关大纲段
            for seg in relevant_segments:
                outline_preview += f"【第{seg['start_chapter']}-{seg['end_chapter']}章 {seg['title']}】\n{seg['summary']}\n\n"
        
        st.caption("本次续写使用的大纲内容（可编辑优化）：")
        manual_outline = st.text_area("大纲指令", value=outline_preview, height=150, help="你可以修改这里的大纲内容，指导本次写作。如果不填写，将自动使用数据库中的大纲。")

        if st.button("🚀 开始智能续写"):
            try:
                with st.spinner("写作团队正在撰写..."):
                    # 传递 manual_outline 和 start_chapter
                    count = services['writing'].continue_writing_chapters(
                        selected_novel_id, 
                        num_chapters_to_write,
                        start_chapter=start_chapter_input,
                        outline_content=manual_outline if manual_outline.strip() else None
                    )
                    st.success(f"成功续写 {count} 章！")
                    st.rerun()
            except Exception as e:
                st.error(f"续写失败: {e}")
                # debug info
                import traceback
                st.code(traceback.format_exc())

    # 连续智能续写功能
    with st.expander("🔄 连续智能续写", expanded=False):
        st.info("💡 自动循环逐章续写，每次续写1章，自动读取对应章节的大纲。适合批量生成多章内容。")
        
        col_cont1, col_cont2 = st.columns(2)
        with col_cont1:
            continuous_start_chapter = st.number_input(
                "起始章节号", 
                1, 9999, 
                next_chapter_default, 
                help="从哪一章开始连续续写",
                key="continuous_start_chapter"
            )
        with col_cont2:
            total_chapters_to_write = st.number_input(
                "总续写章数", 
                1, 50, 
                5, 
                help="总共要续写多少章（将逐章完成）",
                key="continuous_total_chapters"
            )
        
        # 显示预计续写范围
        end_chapter_continuous = continuous_start_chapter + total_chapters_to_write - 1
        st.caption(f"📝 将续写第 {continuous_start_chapter} - {end_chapter_continuous} 章（共 {total_chapters_to_write} 章）")
        
        # 检查是否有足够的大纲
        continuous_segments = services['novel'].get_segments_by_chapter_range(
            selected_novel_id, 
            continuous_start_chapter, 
            end_chapter_continuous
        )
        if not continuous_segments:
            st.warning("⚠️ 未找到对应章节的大纲，续写将使用默认大纲。建议先在大纲管理页面生成大纲。")
        
        if st.button("🚀 开始连续续写", type="primary", key="btn_continuous_writing"):
            try:
                # 创建进度条和状态容器
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                success_count = 0
                failed_chapters = []
                
                # 循环逐章续写
                for i in range(total_chapters_to_write):
                    current_chapter = continuous_start_chapter + i
                    progress = (i + 1) / total_chapters_to_write
                    
                    # 更新进度和状态
                    progress_bar.progress(progress)
                    status_text.info(f"📝 正在续写第 {current_chapter} 章... ({i + 1}/{total_chapters_to_write})")
                    
                    try:
                        # 获取当前章节对应的大纲
                        chapter_segments = services['novel'].get_segments_by_chapter_range(
                            selected_novel_id, 
                            current_chapter, 
                            current_chapter
                        )
                        
                        outline_for_chapter = None
                        if chapter_segments:
                            # 拼接当前章节的大纲
                            for seg in chapter_segments:
                                if seg['start_chapter'] <= current_chapter <= seg['end_chapter']:
                                    outline_for_chapter = f"【第{seg['start_chapter']}-{seg['end_chapter']}章 {seg['title']}】\n{seg['summary']}"
                                    break
                        
                        # 续写1章
                        count = services['writing'].continue_writing_chapters(
                            selected_novel_id,
                            num_chapters=1,  # 每次只续写1章
                            start_chapter=current_chapter,
                            outline_content=outline_for_chapter
                        )
                        
                        if count > 0:
                            success_count += 1
                            status_text.success(f"✅ 第 {current_chapter} 章续写成功！({i + 1}/{total_chapters_to_write})")
                        else:
                            failed_chapters.append(current_chapter)
                            status_text.warning(f"⚠️ 第 {current_chapter} 章续写失败（可能已存在）")
                    
                    except Exception as e:
                        failed_chapters.append(current_chapter)
                        status_text.warning(f"⚠️ 第 {current_chapter} 章续写失败: {str(e)}，继续下一章...")
                        # 自动继续，不中断流程
                        continue
                
                # 完成总结
                progress_bar.progress(1.0)
                if success_count == total_chapters_to_write:
                    status_text.success(f"🎉 全部完成！成功续写 {success_count} 章！")
                elif success_count > 0:
                    status_text.warning(
                        f"⚠️ 部分完成：成功 {success_count} 章，失败 {len(failed_chapters)} 章。"
                        + (f"失败的章节：{failed_chapters}" if failed_chapters else "")
                    )
                else:
                    status_text.error(f"❌ 全部失败！失败的章节：{failed_chapters}")
                
                # 等待3秒后刷新页面
                import time
                time.sleep(2)
                st.rerun()
                
            except Exception as e:
                st.error(f"连续续写失败: {e}")
                import traceback
                with st.expander("查看详细错误信息"):
                    st.code(traceback.format_exc(), language="python")

    st.markdown("---")
    if chapters:
        st.caption(f"共 {len(chapters)} 章")
        for ch in chapters:
            with st.expander(f"📄 {ch['chapter_title']} ({ch['word_count']} 字)"):
                col_info, col_act = st.columns([3, 1])
                with col_info:
                    st.caption(f"#{ch['chapter_number']} | {ch['status']}")
                    if ch.get('outline'): st.text(ch['outline'])
                with col_act:
                    if st.button("✏️", key=f"e{ch['id']}"):
                        st.session_state.edit_chapter_id = ch['id']
                        st.switch_page("pages/4_✏️_章节编辑.py")
                    if st.button("🗑️", key=f"d{ch['id']}"):
                        services['novel'].delete_chapter(ch['id'])
                        st.rerun()

# Tab 2: 大纲管理
with tabs[1]:
    st.header("📑 大纲管理")

    # 检查是否已存在大纲
    existing_segments = services['novel'].get_outline_segments(selected_novel_id)

    # 提示信息
    if not existing_segments:
        st.info("💡 当前小说还没有大纲。请在历史详情页面生成大纲，或使用下方的智能扩充功能。")
    else:
        st.success(f"✅ 当前小说已有 {len(existing_segments)} 段大纲")

    # 智能扩充大纲
    with st.expander("✨ 智能扩充大纲", expanded=not existing_segments):
        st.caption("基于现有大纲和已完成章节，AI 将生成后续章节的剧情规划")

        # 添加模式选择
        expand_mode = st.radio(
            "生成模式",
            options=["从最后一章继续", "指定章节范围"],
            horizontal=True,
            key="expand_mode"
        )

        if expand_mode == "从最后一章继续":
            # 传统模式：指定扩充章节数
            st.markdown("**配置参数**")
            col1, col2 = st.columns(2)
            with col1:
                num_expand = st.number_input(
                    "扩充章节数",
                    min_value=1,
                    max_value=50,
                    value=5,
                    help="要生成的章节数量",
                    key="expand_num_chapters"
                )
            with col2:
                chapters_per_block = st.number_input(
                    "每段章数",
                    min_value=1,
                    max_value=10,
                    value=5,
                    help="每几章生成一段大纲",
                    key="expand_chapters_per_block"
                )

            # 显示预计生成的章节范围
            current_segments = services['novel'].get_outline_segments(selected_novel_id)
            next_chapter = 1
            if current_segments:
                next_chapter = max(seg['end_chapter'] for seg in current_segments) + 1

            st.info(f"📝 将生成第 {next_chapter} - {next_chapter + num_expand - 1} 章的大纲")

            # 自定义prompt输入框
            st.markdown("**💡 自定义提示词（可选）**")
            custom_prompt_auto = st.text_area(
                "追加自定义提示词",
                value="",
                height=100,
                help="可以在这里添加额外的指导，例如：\n- 强调某个剧情方向\n- 指定特定的人物关系发展\n- 要求增加某些元素\n- 调整故事节奏等",
                key="custom_prompt_auto",
                placeholder="例如：请重点突出主角的成长，增加与反派的冲突，节奏要紧凑..."
            )

            if st.button("🚀 开始生成", type="primary", key="btn_expand_outline_auto"):
                try:
                    with st.spinner("AI 正在生成大纲... (这涉及多个智能体协作，请耐心等待)"):
                        count = services['writing'].expand_outline(
                            selected_novel_id,
                            num_chapters=num_expand,
                            chapters_per_block=chapters_per_block,
                            custom_prompt=custom_prompt_auto.strip() if custom_prompt_auto.strip() else None
                        )
                        st.success(f"✅ 成功生成 {count} 段大纲！")
                        st.rerun()
                except Exception as e:
                    st.error(f"生成失败: {str(e)}")
                    import traceback
                    with st.expander("查看详细错误信息"):
                        st.code(traceback.format_exc(), language="python")

        else:
            # 新模式：指定起止章节
            st.markdown("**指定章节范围**")
            col1, col2, col3 = st.columns(3)
            with col1:
                start_chapter = st.number_input(
                    "起始章节",
                    min_value=1,
                    max_value=9999,
                    value=1,
                    help="从第几章开始生成大纲",
                    key="expand_start_chapter"
                )
            with col2:
                end_chapter = st.number_input(
                    "结束章节",
                    min_value=1,
                    max_value=9999,
                    value=10,
                    help="到第几章结束",
                    key="expand_end_chapter"
                )
            with col3:
                chapters_per_block_range = st.number_input(
                    "每段章数",
                    min_value=1,
                    max_value=10,
                    value=5,
                    help="每几章生成一段大纲",
                    key="expand_chapters_per_block_range"
                )

            # 验证和显示信息
            if start_chapter > end_chapter:
                st.error("⚠️ 起始章节不能大于结束章节")
            else:
                total_chapters = end_chapter - start_chapter + 1
                estimated_segments = (total_chapters + chapters_per_block_range - 1) // chapters_per_block_range

                st.info(f"📝 将生成第 {start_chapter} - {end_chapter} 章的大纲（共 {total_chapters} 章，预计 {estimated_segments} 段）")

                # 自定义prompt输入框
                st.markdown("**💡 自定义提示词（可选）**")
                custom_prompt_range = st.text_area(
                    "追加自定义提示词",
                    value="",
                    height=100,
                    help="可以在这里添加额外的指导，例如：\n- 强调某个剧情方向\n- 指定特定的人物关系发展\n- 要求增加某些元素\n- 调整故事节奏等",
                    key="custom_prompt_range",
                    placeholder="例如：请重点突出主角的成长，增加与反派的冲突，节奏要紧凑..."
                )

                if st.button("🚀 开始生成", type="primary", key="btn_expand_outline_range"):
                    try:
                        with st.spinner("AI 正在生成大纲... (这涉及多个智能体协作，请耐心等待)"):
                            count = services['writing'].expand_outline(
                                selected_novel_id,
                                chapters_per_block=chapters_per_block_range,
                                start_chapter=start_chapter,
                                end_chapter=end_chapter,
                                custom_prompt=custom_prompt_range.strip() if custom_prompt_range.strip() else None
                            )
                            st.success(f"✅ 成功生成 {count} 段大纲！")
                            st.rerun()
                    except Exception as e:
                        st.error(f"生成失败: {str(e)}")
                        import traceback
                        with st.expander("查看详细错误信息"):
                            st.code(traceback.format_exc(), language="python")

    # 显示现有大纲
    st.markdown("---")
    st.subheader("📋 现有大纲")
    segments = existing_segments
    if segments:
        for seg in segments:
            with st.container():
                c1, c2, c3 = st.columns([1, 2, 4])
                with c1:
                    new_order = st.number_input("排序", value=seg.get('segment_order', 0) or 0, key=f"ord_{seg['id']}")
                with c2:
                    st.caption(f"第 {seg['start_chapter']} - {seg['end_chapter']} 章")
                    st.text(seg['title'])
                with c3:
                    col_save, col_del = st.columns(2)
                    with col_save:
                        if st.button("💾 保存", key=f"sv_{seg['id']}"):
                            new_summary = st.session_state.get(f"sum_{seg['id']}")
                            services['novel'].update_outline_segment(
                                seg['id'], 
                                segment_order=new_order,
                                summary=new_summary
                            )
                            st.success("已保存")
                            st.rerun()
                    with col_del:
                        if st.button("🗑️ 删除", key=f"ds_{seg['id']}"):
                            services['novel'].delete_outline_segment(seg['id'])
                            st.rerun()
                
                st.text_area(
                    "大纲内容",
                    value=seg['summary'],
                    key=f"sum_{seg['id']}",
                    height=200
                )
                st.markdown("---")

# Tab 3: 统计分析
with tabs[2]:
    st.header("📊 统计分析")
    stats = services['novel'].get_novel_stats(selected_novel_id)
    c1, c2, c3 = st.columns(3)
    c1.metric("总章节", stats['total_chapters'])
    c2.metric("总字数", stats.get('total_words', 0))
    c3.metric("预计阅读", f"{(stats.get('total_words', 0) // 400)} 分钟")

# Tab 4: 版本控制
with tabs[3]:
    st.header("🕐 版本控制")
    with st.expander("📸 创建快照"):
        with st.form("ver"):
            versions = services['novel'].get_version_list(selected_novel_id)
            ver_name = st.text_input("版本名", f"v{len(versions)+1}.0")
            ver_note = st.text_area("说明")
            if st.form_submit_button("💾 创建"):
                vid = services['novel'].create_version_snapshot(selected_novel_id, ver_name, ver_note)
                if vid:
                    st.success("创建成功！")
                    st.rerun()
    versions = services['novel'].get_version_list(selected_novel_id)
    if versions:
        for v in versions:
            with st.expander(f"🏷️ {v['version_name']} - {v['created_at']}"):
                st.text(v.get('version_note', ''))

# Tab 5: 导出
with tabs[4]:
    st.header("📥 导出小说")
    fmt = st.selectbox("格式", ["Markdown (.md)", "纯文本 (.txt)"], key="export_fmt")
    include_outline = st.checkbox("包含大纲", key="export_include_outline")
    if st.button("📥 导出正文"):
        if fmt == "Markdown (.md)":
            content = services['novel'].export_to_markdown(selected_novel_id, include_outline)
            if content:
                st.download_button("📥 下载", content, f"{current_novel['title']}.md", "text/markdown", key="dl_novel_md")
        else:
            content = services['novel'].export_to_txt(selected_novel_id, include_outline)
            if content:
                st.download_button("📥 下载", content, f"{current_novel['title']}.txt", "text/plain", key="dl_novel_txt")

    st.markdown("---")
    st.subheader("📋 大纲导出")
    st.caption("仅导出当前小说的细纲（大纲段），不包含正文。")
    outline_segments = services['novel'].get_outline_segments(selected_novel_id)
    if not outline_segments:
        st.info("当前小说暂无大纲，请先在大纲管理标签中生成大纲后再导出。")
    else:
        outline_fmt = st.selectbox("大纲格式", ["Markdown (.md)", "纯文本 (.txt)"], key="outline_export_fmt")
        outline_content = (
            services['novel'].export_outline_to_markdown(selected_novel_id)
            if outline_fmt == "Markdown (.md)"
            else services['novel'].export_outline_to_txt(selected_novel_id)
        )
        if outline_content:
            ext = "md" if outline_fmt == "Markdown (.md)" else "txt"
            mime = "text/markdown" if ext == "md" else "text/plain"
            st.download_button("📥 下载大纲", outline_content, f"{current_novel['title']}_大纲.{ext}", mime, key="dl_outline")

# Tab 6: 设置
with tabs[5]:
    st.header("⚙️ 设置")
    new_title = st.text_input("标题", current_novel['title'])
    if st.button("💾 保存"):
        if services['novel'].update_novel_info(selected_novel_id, title=new_title):
            st.success("已更新")
            st.rerun()
    st.markdown("---")
    st.subheader("🚨 危险区")
    if st.button("🗑️ 删除整部小说", type="primary"):
        st.session_state.confirm_delete_novel = True
    if st.session_state.get('confirm_delete_novel'):
        st.error(f"确定删除《{current_novel['title']}》?")
        c1, c2 = st.columns([1, 5])
        if c1.button("✅ 确认"):
            services['novel'].delete_novel(selected_novel_id)
            st.success("已删除")
            st.rerun()
        if c2.button("❌ 取消"):
            st.session_state.confirm_delete_novel = False
            st.rerun()

st.markdown("---")
if st.button("⬅️ 返回历史管理"):
    st.switch_page("pages/1_📚_历史管理.py")
