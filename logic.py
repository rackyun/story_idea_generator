import random
import yaml
import os
from openai import OpenAI
from dice_options_manager import DiceOptionsManager

def load_config(config_path="config.yaml"):
    """加载配置文件"""
    if not os.path.exists(config_path):
        return None
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

class Randomizer:
    """随机元素生成器"""

    # 默认选项（作为后备）
    DEFAULT_GENRES = [
        "科幻 (Sci-Fi)", "奇幻 (Fantasy)", "悬疑 (Mystery)", "赛博朋克 (Cyberpunk)",
        "武侠 (Wuxia)", "校园 (School)", "职场 (Workplace)", "末世 (Post-Apocalyptic)",
        "恐怖 (Horror)", "历史 (Historical)", "穿越 (Isekai)", "都市异能 (Urban Supernatural)"
    ]

    DEFAULT_ARCHETYPES = [
        "孤僻的天才 (Reclusive Genius)", "复仇者 (Avenger)", "被选中的人 (The Chosen One)",
        "落魄贵族 (Fallen Noble)", "神秘的旅行者 (Mysterious Traveler)", "乐观的废柴 (Optimistic Underdog)",
        "双重人格者 (Dual Personality)", "失忆的特工 (Amnesiac Agent)", "最后幸存者 (Last Survivor)"
    ]

    DEFAULT_DIRECTIONS = [
        "寻找失落的真相", "逃离绝境", "复仇之路", "自我救赎",
        "打破既定命运", "建立新的秩序", "守护重要之人", "解开千年谜题",
        "在混乱中生存", "跨越时空的爱恋"
    ]

    DEFAULT_TONES = [
        "黑暗压抑", "轻松幽默", "热血激昂", "唯美治愈", "荒诞讽刺", "悬疑烧脑"
    ]

    DEFAULT_SETTINGS = [
        "废弃的空间站", "繁华的赛博夜市", "古老的魔法图书馆", "被遗忘的地下城",
        "充满迷雾的海岛", "时间循环的列车", "看似平凡的便利店", "没有阳光的极地",
        "由于数据错误生成的虚拟世界", "充满变异生物的森林"
    ]

    DEFAULT_KEY_ELEMENTS = [
        "一只会说话的猫", "一本预言未来的日记", "一块由于辐射发光的怀表",
        "一张通往不存在地点的车票", "一段被加密的神秘代码", "一颗能够通过梦境传递信息的种子",
        "一把只能在雨天使用的伞", "一个永远装不满的背包"
    ]

    DEFAULT_ANTAGONISTS = [
        "拥有自我意识的人工智能", "潜伏在阴影中的远古邪神", "主角的内心阴暗面",
        "试图掌控一切的巨型企业", "来自未来的赏金猎人", "一群狂热的末日信徒",
        "无法解释的自然法则崩坏", "被误解的守护者"
    ]

    # 类变量：骰子选项管理器
    _dice_manager = None

    @classmethod
    def _get_dice_manager(cls):
        """获取骰子选项管理器实例（单例）"""
        if cls._dice_manager is None:
            cls._dice_manager = DiceOptionsManager()
        return cls._dice_manager

    @classmethod
    def _load_options(cls):
        """从数据库加载选项，如果不存在则使用默认选项"""
        manager = cls._get_dice_manager()

        cls.GENRES = manager.get_options_with_fallback("genres", cls.DEFAULT_GENRES)
        cls.ARCHETYPES = manager.get_options_with_fallback("archetypes", cls.DEFAULT_ARCHETYPES)
        cls.DIRECTIONS = manager.get_options_with_fallback("directions", cls.DEFAULT_DIRECTIONS)
        cls.TONES = manager.get_options_with_fallback("tones", cls.DEFAULT_TONES)
        cls.SETTINGS = manager.get_options_with_fallback("settings", cls.DEFAULT_SETTINGS)
        cls.KEY_ELEMENTS = manager.get_options_with_fallback("key_elements", cls.DEFAULT_KEY_ELEMENTS)
        cls.ANTAGONISTS = manager.get_options_with_fallback("antagonists", cls.DEFAULT_ANTAGONISTS)

    @classmethod
    def generate_random_elements(cls):
        """生成随机元素"""
        # 每次生成前重新加载选项（确保使用最新数据）
        cls._load_options()

        return {
            "genre": random.choice(cls.GENRES),
            "archetype": random.choice(cls.ARCHETYPES),
            "direction": random.choice(cls.DIRECTIONS),
            "tone": random.choice(cls.TONES),
            "setting": random.choice(cls.SETTINGS),
            "key_element": random.choice(cls.KEY_ELEMENTS),
            "antagonist": random.choice(cls.ANTAGONISTS)
        }

import json
from datetime import datetime
import glob
from database import DatabaseManager

class HistoryManager:
    """历史记录管理器 - 集成数据库管理，保持向后兼容"""
    
    HISTORY_DIR = "history"

    def __init__(self, use_db: bool = True, db_path: str = "stories.db"):
        """
        初始化历史管理器
        
        Args:
            use_db: 是否使用数据库（默认 True）
            db_path: 数据库路径
        """
        self.use_db = use_db
        
        # 确保历史目录存在（用于备份）
        if not os.path.exists(self.HISTORY_DIR):
            os.makedirs(self.HISTORY_DIR)
        
        # 初始化数据库管理器
        if self.use_db:
            self.db_manager = DatabaseManager(db_path)

    def save_record(self, elements, content):
        """
        保存生成记录
        
        Args:
            elements: 元素字典，包含 type, topic 等信息
            content: 生成的内容
        
        Returns:
            如果使用数据库返回 story_id，否则返回文件名
        """
        if self.use_db:
            # 使用数据库保存
            story_type = elements.get('type', 'base')
            topic = elements.get('topic', '')
            
            # 生成标题
            if story_type == 'crew_ai':
                title = f"企划书 - {topic[:50]}" if topic else "企划书"
            elif story_type == 'full_novel':
                title = f"小说 - {topic[:50]}" if topic else "小说"
            else:
                genre = elements.get('genre', '未知题材')
                title = f"灵感 - {genre}"
                if not topic:
                    topic = f"{genre} - {elements.get('archetype', '')}"
            
            # 保存到数据库
            story_id = self.db_manager.save_story(
                story_type=story_type,
                title=title,
                topic=topic,
                content=content,
                metadata=elements
            )
            
            # 同时保存 JSON 备份
            self._save_json_backup(elements, content)
            
            return story_id
        else:
            # 使用传统 JSON 文件保存
            return self._save_json_backup(elements, content)
    
    def _save_json_backup(self, elements, content):
        """保存 JSON 备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        record = {
            "timestamp": timestamp,
            "elements": elements,
            "content": content
        }
        filename = f"{self.HISTORY_DIR}/story_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        return filename

    def load_all_records(self):
        """
        加载所有历史记录
        
        Returns:
            记录列表，格式兼容旧版
        """
        if self.use_db:
            # 从数据库加载
            stories, _ = self.db_manager.list_stories(page_size=1000)
            
            # 转换为旧格式以保持兼容性
            records = []
            for story in stories:
                record = {
                    'id': story['id'],
                    'timestamp': story['created_at'],
                    'elements': story.get('metadata', {}),
                    'content': story.get('content_preview', story.get('content', '')),
                    'filename': f"db_record_{story['id']}"  # 虚拟文件名
                }
                # 确保 elements 中包含 type
                if 'type' not in record['elements']:
                    record['elements']['type'] = story['type']
                if 'topic' not in record['elements']:
                    record['elements']['topic'] = story.get('topic', '')
                
                records.append(record)
            
            return records
        else:
            # 从 JSON 文件加载
            records = []
            files = glob.glob(f"{self.HISTORY_DIR}/*.json")
            for file in sorted(files, reverse=True):
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        data['filename'] = file
                        records.append(data)
                except Exception as e:
                    print(f"Error loading {file}: {e}")
            return records

    def delete_record(self, filename):
        """
        删除指定记录
        
        Args:
            filename: 文件名或 "db_record_{id}" 格式的数据库记录标识
        
        Returns:
            是否成功删除
        """
        if self.use_db and filename.startswith("db_record_"):
            # 从数据库删除
            story_id = int(filename.replace("db_record_", ""))
            return self.db_manager.delete_story(story_id)
        else:
            # 从文件系统删除
            if os.path.exists(filename):
                os.remove(filename)
                return True
            return False
    
    def get_record_by_id(self, story_id: int):
        """通过 ID 获取记录"""
        if self.use_db:
            return self.db_manager.get_story(story_id)
        return None
    
    def update_record(self, story_id: int, **kwargs):
        """更新记录"""
        if self.use_db:
            return self.db_manager.update_story(story_id, **kwargs)
        return False

class StoryLLM:
    """LLM 交互类"""
    
    def __init__(self, config):
        self.config = config
        llm_config = config.get("llm", {})
        self.client = OpenAI(
            base_url=llm_config.get("base_url"),
            api_key=llm_config.get("api_key")
        )
        self.model = llm_config.get("model", "gpt-3.5-turbo")
        self.history_manager = HistoryManager()

    def generate_story_package(self, elements):
        """生成角色卡和故事梗概"""
        
        prompt = f"""
请根据以下核心要素，为一个短篇小说设计详细的角色卡和故事梗概：

**核心要素**：
- 题材：{elements['genre']}
- 主角类型：{elements['archetype']}
- 故事基调：{elements['tone']}
- 故事核心方向：{elements['direction']}
- 背景世界：{elements['setting']}
- 关键物品/金手指：{elements['key_element']}
- 核心反派/障碍：{elements['antagonist']}

**重要约束**：
- **命名规范**：严禁使用 AI 常用的泛化名称（如：林萧、顾川、A市、光明城、暗影组织、艾莉、杰克等）。请根据题材背景设计具有文化深度或独特音韵的名字。
  - 东方题材：请参考古典诗词或生僻字，避免网文大众脸名字。
  - 西方题材：请参考特定语系（如凯尔特、古拉丁、斯拉夫），避免常见的英语课本名。
  - 地点命名：请结合地理特征和历史典故，避免简单的方位命名（如北境、南城）。
- **拒绝套路**：在设定背景和冲突时，尽量避开“失忆找回记忆”、“单纯为了复仇”等陈词滥调，尝试更复杂的动机。

**输出要求**：
1. **世界观/背景设定 (World Setting)**：
   - 时代/地理背景 (请给出具体且独特的地理名称)
   - 核心规则/异能体系（如有）
   - 社会氛围/矛盾点

2. **角色卡 (Character Card)**：
   - 姓名
   - 年龄/外貌特征
   - 核心性格 (3个关键词)
   - 关键能力/特长
   - 背景简述 (100字以内)

3. **故事梗概 (Story Synopsis)**：
   - 标题 (拟定一个吸引人的标题)
   - 起因 (Inciting Incident)
   - 冲突 (Core Conflict)
   - 高潮暗示 (Climax Hint)
   - 结局走向 (Ending Direction)
   - 300-500字左右

4. **语言风格指南 (Style Guide)**：
   - 叙事视角 (第一/第三人称)
   - 遣词造句建议 (如：冷硬派、华丽辞藻、口语化等)
   - 氛围营造关键词

请使用 Markdown 格式输出，确保结构清晰。
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的创意写作助手，擅长构建引人入胜的小说大纲和鲜活的角色。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8
            )
            content = response.choices[0].message.content
            # 自动保存到历史记录
            self.history_manager.save_record(elements, content)
            return content
        except Exception as e:
            return f"生成失败，错误信息：{str(e)}"
