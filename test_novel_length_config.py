"""
测试小说篇幅分类配置模块
"""

from utils.novel_length_config import (
    get_length_category,
    get_category_by_name,
    get_display_options,
    get_chapter_planning_guide,
    format_length_description
)


def test_get_length_category():
    """测试根据字数获取分类"""
    print("=" * 50)
    print("测试 get_length_category()")
    print("=" * 50)

    test_cases = [
        (5000, "微型小说"),
        (50000, "短篇小说"),
        (300000, "中篇小说"),
        (1000000, "长篇小说"),
        (2500000, "超长篇小说"),
    ]

    for word_count, expected_name in test_cases:
        category = get_length_category(word_count)
        status = "✅" if category.name == expected_name else "❌"
        print(f"{status} {word_count}字 -> {category.name} (期望: {expected_name})")
    print()


def test_get_category_by_name():
    """测试根据名称获取分类"""
    print("=" * 50)
    print("测试 get_category_by_name()")
    print("=" * 50)

    test_cases = [
        "微型小说",
        "短篇小说",
        "微型小说 (1万字以内)",
        "短篇小说 (1-10万字)",
        "中篇小说试读 (前3章)",
    ]

    for name in test_cases:
        category = get_category_by_name(name)
        if category:
            print(f"✅ '{name}' -> {category.name} ({category.key})")
        else:
            print(f"❌ '{name}' -> None")
    print()


def test_get_display_options():
    """测试获取显示选项"""
    print("=" * 50)
    print("测试 get_display_options()")
    print("=" * 50)

    options = get_display_options()
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    print()


def test_get_chapter_planning_guide():
    """测试获取章节规划指南"""
    print("=" * 50)
    print("测试 get_chapter_planning_guide()")
    print("=" * 50)

    categories = ["micro", "short", "medium", "long", "super_long"]

    for key in categories:
        guide = get_chapter_planning_guide(key)
        print(f"\n{key}:")
        print(f"  幕数: {guide['acts']}")
        print(f"  结构: {guide['structure']}")
        print(f"  章节数: {guide['chapters']}")
        print(f"  每章字数: {guide['words_per_chapter']}")
    print()


def test_format_length_description():
    """测试格式化字数描述"""
    print("=" * 50)
    print("测试 format_length_description()")
    print("=" * 50)

    test_cases = [
        5000,
        8000,
        50000,
        300000,
        1000000,
        2500000,
    ]

    for word_count in test_cases:
        description = format_length_description(word_count)
        print(f"{word_count:>8}字 -> {description}")
    print()


def test_boundary_cases():
    """测试边界情况"""
    print("=" * 50)
    print("测试边界情况")
    print("=" * 50)

    # 测试边界值
    boundary_cases = [
        (0, "微型小说"),
        (9999, "微型小说"),
        (10000, "短篇小说"),
        (99999, "短篇小说"),
        (100000, "中篇小说"),
        (499999, "中篇小说"),
        (500000, "长篇小说"),
        (1999999, "长篇小说"),
        (2000000, "超长篇小说"),
    ]

    for word_count, expected_name in boundary_cases:
        category = get_length_category(word_count)
        status = "✅" if category.name == expected_name else "❌"
        print(f"{status} {word_count:>7}字 -> {category.name:8} (期望: {expected_name})")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("小说篇幅分类配置模块测试")
    print("=" * 50 + "\n")

    test_get_length_category()
    test_get_category_by_name()
    test_get_display_options()
    test_get_chapter_planning_guide()
    test_format_length_description()
    test_boundary_cases()

    print("=" * 50)
    print("测试完成！")
    print("=" * 50)
