"""
调试脚本：检查 stories 表中的数据
"""
import sqlite3
import json

# 连接数据库
conn = sqlite3.connect('stories.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 查询所有未删除的记录
cursor.execute("""
    SELECT id, type, title, topic, created_at, is_deleted
    FROM stories
    WHERE is_deleted = 0
    ORDER BY created_at DESC
    LIMIT 10
""")

rows = cursor.fetchall()

print("=" * 80)
print("Stories 表中的记录：")
print("=" * 80)

if rows:
    for row in rows:
        print(f"\nID: {row['id']}")
        print(f"类型: {row['type']}")
        print(f"标题: {row['title']}")
        print(f"主题: {row['topic'][:50]}...")
        print(f"创建时间: {row['created_at']}")
        print(f"是否删除: {row['is_deleted']}")
        print("-" * 80)
else:
    print("没有找到记录")

# 测试 get_story 查询
print("\n" + "=" * 80)
print("测试 get_story 查询：")
print("=" * 80)

if rows:
    test_id = rows[0]['id']
    print(f"\n测试 ID: {test_id}")

    cursor.execute("""
        SELECT * FROM stories WHERE id = ? AND is_deleted = 0
    """, (test_id,))

    result = cursor.fetchone()
    if result:
        print("✅ 查询成功")
        print(f"返回的记录: {dict(result)}")
    else:
        print("❌ 查询失败")

conn.close()
