"""
数据迁移脚本：将 JSON 历史记录迁移到 SQLite 数据库
"""
import os
import sys
import json
import glob
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager, ChapterManager


def migrate_json_to_db(json_dir: str = "history", db_path: str = "stories.db"):
    """
    将 JSON 文件迁移到数据库
    
    Args:
        json_dir: JSON 文件所在目录
        db_path: 数据库路径
    """
    db_manager = DatabaseManager(db_path)
    chapter_manager = ChapterManager(db_path)
    
    json_files = glob.glob(f"{json_dir}/*.json")
    
    if not json_files:
        print(f"在 {json_dir} 目录中未找到 JSON 文件")
        return
    
    print(f"找到 {len(json_files)} 个 JSON 文件，开始迁移...")
    
    migrated_count = 0
    error_count = 0
    
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            timestamp = data.get('timestamp', '')
            elements = data.get('elements', {})
            content = data.get('content', '')
            
            # 确定记录类型
            record_type = elements.get('type', 'base')
            
            # 生成标题
            if record_type == 'crew_ai':
                title = f"企划书 - {elements.get('topic', '未知主题')[:50]}"
                topic = elements.get('topic', '')
            elif record_type == 'full_novel':
                title = f"小说 - {elements.get('topic', '未知主题')[:50]}"
                topic = elements.get('topic', '')
            else:
                genre = elements.get('genre', '未知题材')
                title = f"灵感 - {genre}"
                topic = f"{genre} - {elements.get('archetype', '')}"
            
            # 保存到数据库
            story_id = db_manager.save_story(
                story_type=record_type,
                title=title,
                topic=topic,
                content=content,
                metadata=elements
            )
            
            # 如果是 full_novel 类型，尝试解析章节
            if record_type == 'full_novel' and content:
                chapters = chapter_manager.parse_chapters_from_content(content)
                
                if len(chapters) > 1:  # 只有当解析出多个章节时才创建章节记录
                    print(f"  解析出 {len(chapters)} 个章节，创建章节记录...")
                    
                    for chapter in chapters:
                        chapter_manager.create_chapter(
                            novel_id=story_id,
                            chapter_number=chapter['chapter_number'],
                            chapter_title=chapter['chapter_title'],
                            content=chapter['content'].strip(),
                            status='published'
                        )
            
            print(f"✓ 已迁移: {os.path.basename(json_file)} -> Story ID: {story_id}")
            migrated_count += 1
            
        except Exception as e:
            print(f"✗ 迁移失败: {os.path.basename(json_file)} - 错误: {str(e)}")
            error_count += 1
    
    print(f"\n迁移完成:")
    print(f"  成功: {migrated_count} 条")
    print(f"  失败: {error_count} 条")
    print(f"  数据库: {db_path}")


def verify_migration(db_path: str = "stories.db"):
    """验证迁移结果"""
    db_manager = DatabaseManager(db_path)
    
    print("\n=== 验证迁移结果 ===")
    
    # 统计各类型记录数
    types = ['base', 'crew_ai', 'full_novel']
    
    for story_type in types:
        stories, total = db_manager.list_stories(story_type=story_type, page_size=1000)
        print(f"{story_type}: {total} 条记录")
    
    # 统计总记录数
    all_stories, total_count = db_manager.list_stories(page_size=1)
    print(f"总计: {total_count} 条记录")
    
    # 检查章节
    chapter_manager = ChapterManager(db_path)
    conn = chapter_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM chapters WHERE is_deleted = 0")
    chapter_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"章节: {chapter_count} 个")


if __name__ == "__main__":
    # 获取脚本所在目录的父目录（项目根目录）
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    print("=== 开始数据迁移 ===\n")
    
    # 执行迁移
    migrate_json_to_db()
    
    # 验证迁移
    verify_migration()
    
    print("\n迁移脚本执行完成！")
