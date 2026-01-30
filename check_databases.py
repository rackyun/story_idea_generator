"""
检查三个数据库的内容和结构
"""
import sqlite3
import os

db_files = ['stories.db', 'story_data.db', 'dice_options.db']

for db_file in db_files:
    if not os.path.exists(db_file):
        print(f"\n❌ {db_file} 不存在")
        continue

    print(f"\n{'='*80}")
    print(f"数据库: {db_file}")
    print(f"{'='*80}")

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print(f"\n表列表: {[t[0] for t in tables]}")

    for table in tables:
        table_name = table[0]
        print(f"\n--- 表: {table_name} ---")

        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"字段: {[col[1] for col in columns]}")

        # 获取记录数
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"记录数: {count}")

        # 如果是 stories 表，显示前几条记录的 ID
        if table_name == 'stories' and count > 0:
            cursor.execute(f"SELECT id, type, title FROM {table_name} WHERE is_deleted = 0 LIMIT 5")
            rows = cursor.fetchall()
            print(f"前5条记录:")
            for row in rows:
                print(f"  ID: {row[0]}, 类型: {row[1]}, 标题: {row[2][:50]}...")

        # 如果是 novels 表，显示前几条记录的 ID
        elif table_name == 'novels' and count > 0:
            cursor.execute(f"SELECT id, title FROM {table_name} WHERE is_deleted = 0 LIMIT 5")
            rows = cursor.fetchall()
            print(f"前5条记录:")
            for row in rows:
                print(f"  ID: {row[0]}, 标题: {row[1][:50]}...")

    conn.close()
