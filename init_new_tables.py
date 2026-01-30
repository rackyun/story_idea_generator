#!/usr/bin/env python3
"""
初始化新表结构
运行此脚本以在现有数据库中创建新的 outline_segments 表
"""
import sys
from database import DatabaseManager

def main():
    print("初始化数据库新表...")
    
    try:
        db_manager = DatabaseManager()
        print("✅ 数据库初始化完成！")
        print("   新表 outline_segments 已创建（如果不存在）")
        return 0
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
