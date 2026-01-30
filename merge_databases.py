"""
合并数据库脚本
将 dice_options.db 的数据合并到 stories.db 中
"""
import sqlite3
import os
import shutil
from datetime import datetime

def merge_databases():
    """合并数据库"""

    # 1. 备份主数据库
    backup_file = f"stories_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    print(f"📦 备份主数据库到: {backup_file}")
    shutil.copy2('stories.db', backup_file)

    # 2. 连接主数据库
    main_conn = sqlite3.connect('stories.db')
    main_cursor = main_conn.cursor()

    # 3. 检查主数据库是否已有 dice_options 表
    main_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dice_options'")
    has_dice_table = main_cursor.fetchone() is not None

    if not has_dice_table:
        print("✅ 在主数据库中创建 dice_options 表")
        main_cursor.execute("""
            CREATE TABLE dice_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL UNIQUE,
                options TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        main_conn.commit()
    else:
        print("ℹ️  主数据库已有 dice_options 表")

    # 4. 从 dice_options.db 复制数据
    if os.path.exists('dice_options.db'):
        print("📥 从 dice_options.db 复制数据...")
        dice_conn = sqlite3.connect('dice_options.db')
        dice_cursor = dice_conn.cursor()

        # 获取所有骰子选项
        dice_cursor.execute("SELECT category, options, updated_at FROM dice_options")
        rows = dice_cursor.fetchall()

        # 插入或更新到主数据库
        for row in rows:
            category, options, updated_at = row
            main_cursor.execute("""
                INSERT OR REPLACE INTO dice_options (category, options, updated_at)
                VALUES (?, ?, ?)
            """, (category, options, updated_at))
            print(f"  ✓ 复制类别: {category}")

        main_conn.commit()
        dice_conn.close()

        print(f"✅ 成功复制 {len(rows)} 条骰子选项记录")
    else:
        print("⚠️  dice_options.db 不存在，跳过")

    # 5. 验证合并结果
    print("\n📊 验证合并结果:")
    main_cursor.execute("SELECT COUNT(*) FROM stories WHERE is_deleted = 0")
    stories_count = main_cursor.fetchone()[0]
    print(f"  stories 表: {stories_count} 条记录")

    main_cursor.execute("SELECT COUNT(*) FROM novels WHERE is_deleted = 0")
    novels_count = main_cursor.fetchone()[0]
    print(f"  novels 表: {novels_count} 条记录")

    main_cursor.execute("SELECT COUNT(*) FROM chapters WHERE is_deleted = 0")
    chapters_count = main_cursor.fetchone()[0]
    print(f"  chapters 表: {chapters_count} 条记录")

    main_cursor.execute("SELECT COUNT(*) FROM dice_options")
    dice_count = main_cursor.fetchone()[0]
    print(f"  dice_options 表: {dice_count} 条记录")

    main_conn.close()

    # 6. 清理旧数据库文件
    print("\n🗑️  清理旧数据库文件:")

    if os.path.exists('story_data.db'):
        # story_data.db 是空的，可以直接删除
        os.remove('story_data.db')
        print("  ✓ 删除 story_data.db (空数据库)")

    if os.path.exists('dice_options.db'):
        # 重命名为备份文件
        dice_backup = f"dice_options_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        os.rename('dice_options.db', dice_backup)
        print(f"  ✓ 备份 dice_options.db 为 {dice_backup}")

    print("\n✅ 数据库合并完成！")
    print(f"📁 主数据库: stories.db")
    print(f"📁 备份文件: {backup_file}")
    print(f"📁 骰子选项备份: {dice_backup if os.path.exists(dice_backup) else '无'}")

    return True

if __name__ == "__main__":
    try:
        merge_databases()
    except Exception as e:
        print(f"\n❌ 合并失败: {str(e)}")
        import traceback
        traceback.print_exc()
