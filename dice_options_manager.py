"""
骰子选项管理器

管理随机骰子的选项数据，支持从 LLM 获取新选项并存储到 SQLite 数据库。
"""

import sqlite3
import json
from typing import Dict, List, Optional
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed


class DiceOptionsManager:
    """骰子选项管理器"""

    def __init__(self, db_path: str = "stories.db"):
        """
        初始化骰子选项管理器

        Args:
            db_path: 数据库文件路径（默认使用主数据库 stories.db）
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dice_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL UNIQUE,
                options TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def get_options(self, category: str) -> Optional[List[str]]:
        """
        获取指定类别的选项

        Args:
            category: 类别名称（genres, archetypes, directions, tones, settings, key_elements, antagonists）

        Returns:
            选项列表，如果不存在则返回 None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT options FROM dice_options WHERE category = ?",
            (category,)
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            return json.loads(result[0])
        return None

    def save_options(self, category: str, options: List[str]):
        """
        保存选项到数据库

        Args:
            category: 类别名称
            options: 选项列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO dice_options (category, options, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (category, json.dumps(options, ensure_ascii=False)))

        conn.commit()
        conn.close()

    def get_all_categories(self) -> List[str]:
        """
        获取所有已存储的类别

        Returns:
            类别列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT category FROM dice_options")
        results = cursor.fetchall()
        conn.close()

        return [row[0] for row in results]

    def _fetch_single_batch(self, config: Dict, category: str, count: int, batch_index: int = 0) -> List[str]:
        """
        从 LLM 获取单批选项（内部方法）

        Args:
            config: 配置字典
            category: 类别名称
            count: 要生成的选项数量
            batch_index: 批次索引（用于日志）

        Returns:
            选项列表
        """
        llm_config = config.get("llm", {})
        client = OpenAI(
            api_key=llm_config.get("api_key"),
            base_url=llm_config.get("base_url")
        )

        # 优先使用骰子选项专用模型配置，如果没有则使用默认模型
        dice_options_config = config.get("dice_options", {})
        model = dice_options_config.get("model") or llm_config.get("model", "gpt-3.5-turbo")

        # 根据类别生成不同的提示词
        prompts = {
            "genres": f"""请生成 {count} 个适合女频小说创作的题材类型。
要求：
- 偏向女性视角/情感/成长主题，但必须高度多样化，覆盖言情、玄幻、科幻、悬疑、职场、历史、末世、校园等多种领域
- 融入女性向元素如情感纠葛、自我觉醒、逆袭、重生、穿越等，但避免单一甜宠或虐恋重复
- 可以是传统女频类型，也可以是新兴融合（如女强科幻、女性主义仙侠）
- 每行一个，格式严格：中文描述 (英文简译)
- 不要编号、不要解释、不要空行

示例：
重生复仇的古代宫廷权谋 (Reborn Revenge Palace Intrigue)
女主觉醒能力的末日生存 (Apocalyptic Female Awakening Survival)
都市职场与异能恋爱的混合 (Urban Career with Supernatural Romance)
""",

            "archetypes": f"""请生成 {count} 个适合女频小说的主角原型。
要求：
- 以女性为主角，性格/身份/命运鲜明，带有情感深度或成长弧线（如从弱到强、情感独立）
- 多样化，避免纯玛丽苏或小白兔；优先有内在冲突、职业多样、背景多变的角色
- 每行一个，格式严格：中文描述 (英文翻译)
- 不要编号、不要多余文字

示例：
表面高冷实则内心脆弱的商业女强人 (Cold Exterior Fragile Heart Businesswoman)
穿越成炮灰却逆袭成宗门大佬的现代少女 (Transmigrated Cannon Fodder to Sect Leader)
隐藏超能力的单亲妈妈侦探 (Single Mom Detective with Hidden Powers)
重生后拒绝渣男专注事业的文艺女青年 (Reborn Artist Rejecting Ex for Career)
""",

            "directions": f"""请生成 {count} 个极具吸引力的女频故事核心驱动力/主线方向。
要求：
- 自带情感冲突、成长转折或浪漫张力，但多样化，包含复仇、冒险、治愈、探险等多种
- 用简短有力的中文短语概括，避免单一“追夫”“虐心”
- 只输出列表，每行一条，无编号、无前缀

示例：
觉醒前世记忆后颠覆家族阴谋
在虚拟游戏中寻找失散的灵魂伴侣
从底层职员逆袭成行业女王的同时治愈童年创伤
穿越古代发明科技改变女性命运
""",

            "tones": f"""请生成 {count} 个女频小说的整体氛围/情感基调。
要求：
- 用3–6个字的中文意象词组，精准捕捉多样情绪：甜蜜、虐心、励志、悬疑、温馨、黑暗等
- 高度多样化，避免过多重复类似“甜宠”
- 只输出列表，每行一个，无多余文字

示例：
甜蜜中带一丝酸涩
黑暗中绽放的坚韧
治愈般的温暖逆袭
悬疑交织的深情
潇洒不羁的自由
""",

            "settings": f"""请生成 {count} 个独特且完整的世界背景设定，用于女频小说创作。
要求：
- **完整的世界观**：不仅是一个场景，而是包含时代背景、社会结构、文化体系、地理环境、政治制度等要素的完整世界设定
- **多样化类型**：古代宫廷、现代都市、玄幻仙界、科幻未来、末世废墟、校园秘境、异世界、平行时空等
- **女性视角融入**：融入女性视角的世界观元素，如情感纽带、隐秘空间、命运交织、权力结构、社会规则等
- **具体而丰富**：每个设定应包含世界的基本特征、社会结构、文化背景等关键信息
- 用15–25个中文字符的短语描述，能够清晰传达完整的世界观
- 只输出列表，每行一个，无编号

示例：
以情感纽带为纽带的古代宫廷世界，女性通过联姻掌控政治格局
科技高度发达的未来都市，女性觉醒超能力后建立新的社会秩序
灵气复苏的现代校园，隐藏着连接异世界的秘密通道
末世废墟中女性主导的庇护所，重建了以情感为纽带的社区体系
重生后时光倒流的皇宫后院，女性通过预知改变历史走向
""",

            "key_elements": f"""请生成 {count} 个带有神秘/情感/命运色彩的女频核心物件或元素。
要求：
- 必须自带“情感羁绊或成长代价”的叙事张力
- 可以是饰品、秘籍、异能、信物、诅咒等，多样化类型
- 短语控制在8–12字
- 只输出列表，每行一个

示例：
能重温逝去爱人的记忆项链
觉醒女性力量却需牺牲情感的血脉晶石
预知渣男背叛的命运之镜
连接平行世界闺蜜的传音玉佩
治愈创伤但会遗忘过去的忘情丹
""",

            "antagonists": f"""请生成 {count} 个有深度且多样化的女频反派/主要对立方。
要求：
- 以女性视角设计，避免单纯“恶毒女配”；带有情感动机、嫉妒、野心、悲剧等多样特质
- 可以是情敌、家族长辈、系统AI、宿敌等
- 用简洁有力的中文短语
- 只输出列表，每行一个，无多余内容

示例：
嫉妒女主天赋的同门师姐
操控命运却孤独终生的神秘女巫
表面温柔实则心机深沉的闺蜜
为权力牺牲一切的皇室太后
被爱恨扭曲的转世前任
"""
        }

        prompt = prompts.get(category, f"请生成 {count} 个适合小说创作的 {category} 选项。")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的小说创作顾问，擅长提供创意灵感。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9
        )

        content = response.choices[0].message.content.strip()

        # 解析返回的选项列表
        options = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]

        # 过滤掉编号
        import re
        cleaned_options = []
        for option in options:
            # 移除开头的编号（如 1. 2. 1) 等）
            cleaned = re.sub(r'^\d+[\.\)]\s*', '', option)
            if cleaned:
                cleaned_options.append(cleaned)

        return cleaned_options

    def fetch_options_from_llm(self, config: Dict, category: str, count: int = 12, use_parallel: bool = True) -> List[str]:
        """
        从 LLM 获取新的选项，支持大批量请求（自动分批）和并发请求

        Args:
            config: 配置字典（包含 llm 配置）
            category: 类别名称
            count: 要生成的选项数量
            use_parallel: 是否使用并发请求（默认 True）

        Returns:
            去重后的选项列表
        """
        # 如果请求数量 <= 20，直接单次请求
        if count <= 20:
            options = self._fetch_single_batch(config, category, count)
            return options[:count]

        # 如果请求数量 > 20，分批请求
        batch_size = 15  # 每批请求 15 个，留有余地
        num_batches = (count + batch_size - 1) // batch_size  # 向上取整

        # 计算每批的数量
        batch_counts = []
        remaining = count
        for _ in range(num_batches):
            current_batch_size = min(batch_size, remaining)
            batch_counts.append(current_batch_size)
            remaining -= current_batch_size
            if remaining <= 0:
                break

        all_options = []

        if use_parallel and num_batches > 1:
            # 并发请求多个批次
            with ThreadPoolExecutor(max_workers=min(num_batches, 5)) as executor:
                # 提交所有批次任务
                future_to_batch = {
                    executor.submit(self._fetch_single_batch, config, category, batch_count, i): i
                    for i, batch_count in enumerate(batch_counts)
                }

                # 收集结果
                for future in as_completed(future_to_batch):
                    batch_index = future_to_batch[future]
                    try:
                        batch_options = future.result()
                        all_options.extend(batch_options)
                    except Exception as e:
                        print(f"批次 {batch_index} 失败: {str(e)}")
        else:
            # 串行请求（用于调试或避免并发问题）
            for i, batch_count in enumerate(batch_counts):
                try:
                    batch_options = self._fetch_single_batch(config, category, batch_count, i)
                    all_options.extend(batch_options)
                except Exception as e:
                    print(f"批次 {i} 失败: {str(e)}")

        # 去重（保持顺序）
        seen = set()
        unique_options = []
        for option in all_options:
            # 标准化：去除首尾空格，统一大小写比较
            normalized = option.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique_options.append(option)

        # 返回指定数量的选项
        return unique_options[:count]

    def refresh_all_options(self, config: Dict, count: int = 12, use_parallel: bool = True, progress_callback=None) -> Dict[str, int]:
        """
        刷新所有类别的选项，支持并发刷新

        Args:
            config: 配置字典
            count: 每个类别要生成的选项数量
            use_parallel: 是否使用并发刷新所有类别（默认 True）
            progress_callback: 进度回调函数，接收 (category, success, count) 参数

        Returns:
            刷新结果统计 {category: count}
        """
        categories = ["genres", "archetypes", "directions", "tones", "settings", "key_elements", "antagonists"]
        results = {}

        def refresh_category(category: str) -> tuple:
            """刷新单个类别"""
            try:
                options = self.fetch_options_from_llm(config, category, count, use_parallel=True)
                self.save_options(category, options)
                return (category, True, len(options))
            except Exception as e:
                print(f"刷新 {category} 失败: {str(e)}")
                return (category, False, 0)

        if use_parallel:
            # 并发刷新所有类别
            with ThreadPoolExecutor(max_workers=min(len(categories), 4)) as executor:
                future_to_category = {
                    executor.submit(refresh_category, category): category
                    for category in categories
                }

                for future in as_completed(future_to_category):
                    category, success, result_count = future.result()
                    results[category] = result_count
                    if progress_callback:
                        progress_callback(category, success, result_count)
        else:
            # 串行刷新
            for category in categories:
                category_name, success, result_count = refresh_category(category)
                results[category_name] = result_count
                if progress_callback:
                    progress_callback(category_name, success, result_count)

        return results

    def get_options_with_fallback(self, category: str, default_options: List[str]) -> List[str]:
        """
        获取选项，如果数据库中不存在则使用默认选项

        Args:
            category: 类别名称
            default_options: 默认选项列表

        Returns:
            选项列表
        """
        options = self.get_options(category)
        return options if options else default_options


