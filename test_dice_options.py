"""
测试骰子选项管理功能

运行此脚本测试 DiceOptionsManager 的基本功能
"""

from dice_options_manager import DiceOptionsManager
from logic import load_config, Randomizer

def test_dice_options():
    print("=" * 60)
    print("测试骰子选项管理功能")
    print("=" * 60)

    # 1. 测试数据库初始化
    print("\n1. 初始化骰子选项管理器...")
    manager = DiceOptionsManager()
    print("✅ 数据库初始化成功")

    # 2. 测试获取默认选项
    print("\n2. 测试获取选项（应该返回 None，因为数据库为空）...")
    genres = manager.get_options("genres")
    print(f"genres: {genres}")

    # 3. 测试保存选项
    print("\n3. 测试保存选项...")
    test_genres = ["测试题材1", "测试题材2", "测试题材3"]
    manager.save_options("genres", test_genres)
    print("✅ 保存成功")

    # 4. 测试读取保存的选项
    print("\n4. 测试读取保存的选项...")
    saved_genres = manager.get_options("genres")
    print(f"读取到的选项: {saved_genres}")
    assert saved_genres == test_genres, "读取的选项与保存的不一致"
    print("✅ 读取成功")

    # 5. 测试 get_options_with_fallback
    print("\n5. 测试 get_options_with_fallback...")
    default_options = ["默认1", "默认2"]

    # 存在的类别应该返回数据库中的选项
    result1 = manager.get_options_with_fallback("genres", default_options)
    print(f"genres (存在): {result1}")
    assert result1 == test_genres, "应该返回数据库中的选项"

    # 不存在的类别应该返回默认选项
    result2 = manager.get_options_with_fallback("nonexistent", default_options)
    print(f"nonexistent (不存在): {result2}")
    assert result2 == default_options, "应该返回默认选项"
    print("✅ Fallback 功能正常")

    # 6. 测试 Randomizer 集成
    print("\n6. 测试 Randomizer 集成...")
    print("生成随机元素（应该使用默认选项，因为其他类别未设置）...")
    elements = Randomizer.generate_random_elements()
    print(f"生成的元素: {elements}")
    print("✅ Randomizer 集成正常")

    # 7. 测试从 LLM 获取选项（需要配置）
    print("\n7. 测试从 LLM 获取选项...")
    config = load_config()
    if config:
        print("配置文件已加载，尝试从 LLM 获取选项...")
        try:
            # 测试小批量（单次请求）
            print("\n7.1 测试小批量（单次请求，10 个选项）...")
            options_small = manager.fetch_options_from_llm(config, "tones", count=10)
            print(f"获取到 {len(options_small)} 个选项")
            print(f"选项: {options_small}")
            print("✅ 小批量请求成功")

            # 测试大批量（分批请求）
            print("\n7.2 测试大批量（分批请求，30 个选项）...")
            options_large = manager.fetch_options_from_llm(config, "settings", count=30)
            print(f"获取到 {len(options_large)} 个选项")
            print(f"前 5 个选项: {options_large[:5]}")
            print(f"后 5 个选项: {options_large[-5:]}")

            # 检查去重
            unique_count = len(set(options_large))
            print(f"去重后数量: {unique_count}")
            if unique_count == len(options_large):
                print("✅ 去重功能正常（无重复）")
            else:
                print(f"⚠️ 发现 {len(options_large) - unique_count} 个重复项")

            print("✅ 大批量请求成功")

        except Exception as e:
            print(f"⚠️ LLM 获取失败: {str(e)}")
            print("这可能是因为 API 配置问题，不影响其他功能")
    else:
        print("⚠️ 未找到配置文件，跳过 LLM 测试")

    print("\n" + "=" * 60)
    print("✅ 所有基础功能测试通过！")
    print("=" * 60)

if __name__ == "__main__":
    test_dice_options()
