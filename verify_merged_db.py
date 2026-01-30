"""
验证合并后的数据库
"""
import sqlite3

print("=" * 80)
print("验证合并后的 stories.db")
print("=" * 80)

conn = sqlite3.connect('stories.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. 检查所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]
print(f"\n✅ 数据库包含 {len(tables)} 个表:")
for table in tables:
    print(f"  - {table}")

# 2. 检查各表的记录数
print(f"\n📊 各表记录数:")
for table in tables:
    if table == 'sqlite_sequence':
        continue
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} 条记录")
    except Exception as e:
        print(f"  {table}: 查询失败 - {e}")

# 3. 测试查询 stories 表
print(f"\n🔍 测试查询 stories 表:")
cursor.execute("SELECT id, type, title FROM stories WHERE is_deleted = 0 LIMIT 3")
rows = cursor.fetchall()
for row in rows:
    print(f"  ID: {row['id']}, 类型: {row['type']}, 标题: {row['title'][:50]}...")

# 4. 测试查询 dice_options 表
print(f"\n🎲 测试查询 dice_options 表:")
cursor.execute("SELECT category FROM dice_options")
rows = cursor.fetchall()
for row in rows:
    print(f"  - {row['category']}")

# 5. 测试 DiceOptionsManager
print(f"\n🧪 测试 DiceOptionsManager:")
from dice_options_manager import DiceOptionsManager

manager = DiceOptionsManager()
categories = manager.get_all_categories()
print(f"  获取到 {len(categories)} 个类别: {categories}")

# 测试获取一个类别的选项
if 'genres' in categories:
    options = manager.get_options('genres')
    print(f"  genres 类别有 {len(options) if options else 0} 个选项")

conn.close()

print("\n✅ 验证完成！数据库工作正常。")
