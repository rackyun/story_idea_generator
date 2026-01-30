#!/usr/bin/env python3
"""
数据迁移脚本：将 novel_outlines 表中的 JSON 格式大纲迁移到 outline_segments 表
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import json
from datetime import datetime


def migrate_outlines_to_segments(db_path: str = "stories.db", dry_run: bool = False):
    """
    将 novel_outlines 表中的大纲迁移到 outline_segments 表
    
    Args:
        db_path: 数据库路径
        dry_run: 如果为 True，只显示将要迁移的数据，不实际执行
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 60)
    print("大纲数据迁移工具")
    print("=" * 60)
    
    # 1. 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='outline_segments'")
    if not cursor.fetchone():
        print("❌ 错误：outline_segments 表不存在。请先运行应用初始化数据库。")
        conn.close()
        return False
    
    # 2. 获取所有需要迁移的大纲
    cursor.execute("""
        SELECT o.novel_id, o.content, o.created_at, n.title as novel_title
        FROM novel_outlines o
        LEFT JOIN novels n ON o.novel_id = n.id
        WHERE o.is_active = 1
        ORDER BY o.novel_id
    """)
    
    outlines_to_migrate = cursor.fetchall()
    
    if not outlines_to_migrate:
        print("ℹ️  未找到需要迁移的大纲数据。")
        conn.close()
        return True
    
    print(f"\n找到 {len(outlines_to_migrate)} 个小说的大纲需要迁移。\n")
    
    # 3. 逐个迁移
    migrated_count = 0
    skipped_count = 0
    error_count = 0
    
    for outline in outlines_to_migrate:
        novel_id = outline['novel_id']
        novel_title = outline['novel_title'] or f"小说 #{novel_id}"
        content = outline['content']
        created_at = outline['created_at']
        
        print(f"处理：{novel_title} (ID: {novel_id})")
        
        # 检查是否已经迁移过
        cursor.execute("SELECT COUNT(*) FROM outline_segments WHERE novel_id = ?", (novel_id,))
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"  ⏭️  跳过：该小说已有 {existing_count} 个大纲段")
            skipped_count += 1
            continue
        
        # 解析 JSON 大纲
        try:
            outline_data = json.loads(content)
            
            if not isinstance(outline_data, list):
                print(f"  ⚠️  警告：大纲格式不是列表，跳过")
                skipped_count += 1
                continue
            
            if not outline_data:
                print(f"  ⏭️  跳过：大纲为空")
                skipped_count += 1
                continue
            
            print(f"  📋 解析到 {len(outline_data)} 个大纲项")
            
            # 转换为 outline_segments
            segments_created = 0
            
            for idx, item in enumerate(outline_data):
                # 提取字段（兼容不同格式）
                chapter = item.get('chapter', idx + 1)
                title = item.get('title', '')
                summary = item.get('summary', '') or item.get('description', '')
                
                # 处理章节范围（检查是否是范围格式）
                if 'start_chapter' in item and 'end_chapter' in item:
                    start_chapter = item['start_chapter']
                    end_chapter = item['end_chapter']
                else:
                    # 单章模式
                    start_chapter = chapter
                    end_chapter = chapter
                
                segment_order = idx + 1
                
                if dry_run:
                    print(f"    [{segment_order}] 第 {start_chapter}-{end_chapter} 章: {title[:30]}")
                else:
                    cursor.execute("""
                        INSERT INTO outline_segments 
                        (novel_id, segment_order, start_chapter, end_chapter, title, summary, 
                         status, priority, created_at, updated_at, is_deleted)
                        VALUES (?, ?, ?, ?, ?, ?, 'active', 0, ?, ?, 0)
                    """, (novel_id, segment_order, start_chapter, end_chapter, title, summary,
                          created_at, datetime.now()))
                    
                    segments_created += 1
            
            if not dry_run:
                conn.commit()
                print(f"  ✅ 成功迁移 {segments_created} 个大纲段")
                migrated_count += 1
            else:
                print(f"  🔍 (试运行) 将创建 {len(outline_data)} 个大纲段")
            
        except json.JSONDecodeError as e:
            print(f"  ❌ 错误：无法解析 JSON - {str(e)}")
            error_count += 1
        except Exception as e:
            print(f"  ❌ 错误：{str(e)}")
            error_count += 1
        
        print()
    
    # 4. 总结
    print("=" * 60)
    print("迁移完成统计")
    print("=" * 60)
    
    if dry_run:
        print(f"🔍 试运行模式（未实际修改数据库）")
    
    print(f"✅ 成功迁移：{migrated_count} 个小说")
    print(f"⏭️  跳过：{skipped_count} 个小说")
    print(f"❌ 失败：{error_count} 个小说")
    print()
    
    if dry_run:
        print("💡 提示：如果确认无误，请运行 'python migrate_outline_to_segments.py --execute' 执行实际迁移")
    else:
        print("✨ 迁移已完成！")
        print("📝 注意：旧的 novel_outlines 表数据已保留，可以在确认无误后手动清理。")
    
    conn.close()
    return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='迁移大纲数据到新的段式结构')
    parser.add_argument('--execute', action='store_true', 
                       help='执行实际迁移（默认为试运行模式）')
    parser.add_argument('--db', type=str, default='stories.db',
                       help='数据库文件路径（默认：stories.db）')
    
    args = parser.parse_args()
    
    dry_run = not args.execute
    
    if dry_run:
        print("\n🔍 运行模式：试运行（不会修改数据库）")
        print("   使用 --execute 参数执行实际迁移\n")
    else:
        print("\n⚠️  警告：即将执行实际数据迁移！")
        response = input("确认继续？(y/N): ")
        if response.lower() != 'y':
            print("已取消。")
            return
        print()
    
    success = migrate_outlines_to_segments(args.db, dry_run)
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
