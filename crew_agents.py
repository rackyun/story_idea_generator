import os
from crewai import Agent, Task, Crew, Process, LLM
# from langchain_openai import ChatOpenAI
from logic import load_config

# 加载配置
CONFIG_PATH = "config.yaml"
config = load_config(CONFIG_PATH)

def get_llm(model_name=None):
    """
    配置 CrewAI 使用的 LLM
    
    Args:
        model_name: 模型名称，如果为 None 则使用默认模型
    
    Returns:
        LLM: CrewAI LLM 实例
    """
    if not config:
        raise ValueError("Config not loaded")
    
    llm_conf = config.get("llm", {})
    # 使用 CrewAI 原生 LLM 类
    # 显式指定 provider="openai" 以避免 CrewAI 尝试加载 Google GenAI 等其他未安装的 provider
    return LLM(
        model=model_name or llm_conf.get("model", "gpt-3.5-turbo"),
        base_url=llm_conf.get("base_url"),
        api_key=llm_conf.get("api_key"),
        provider="openai"
    )

def get_agent_model(agent_name):
    """
    从配置文件获取指定智能体的模型名称
    
    Args:
        agent_name: 智能体名称（如 'chief_editor', 'idea_stormer' 等）
    
    Returns:
        str: 模型名称，如果未配置则返回默认模型
    """
    if not config:
        return None
    
    # 优先从 agents 配置中读取
    agents_conf = config.get("agents", {})
    if agent_name in agents_conf:
        return agents_conf[agent_name]
    
    # 如果未配置，使用默认模型
    llm_conf = config.get("llm", {})
    return llm_conf.get("model", "gpt-3.5-turbo")

class StoryAgents:
    def __init__(self):
        pass

    def chief_editor(self):
        return Agent(
            role='总编代理 (Chief Editor)',
            goal='统筹小说创作全流程，确保故事连贯、风格统一且爆款潜力十足。',
            backstory='你是一位洞察市场脉搏的金牌网文总编，曾主导多部百万订阅神作。你擅长从大局把控节奏，协调各代理输出，确保每章都勾住读者心弦，同时注入情感张力，让故事不止于情节，更触动人心。',
            llm=get_llm(get_agent_model('chief_editor')),
            verbose=True,
            allow_delegation=False
        )

    def idea_stormer(self):
        return Agent(
            role='脑洞代理 (Idea Stormer)',
            goal='迸发大胆、反套路的创意梗和转折点，点燃故事的惊喜火花。',
            backstory='你是一位天马行空的创意狂人，总能在陈腐套路中撕开裂隙，注入新鲜血脉。你鄙视平庸，追求读者“哇塞”的瞬间，让每个想法都如惊涛骇浪般颠覆预期，同时唤醒深层情感共鸣。',
            llm=get_llm(get_agent_model('idea_stormer')),
            verbose=True
        )

    def plot_weaver(self):
        return Agent(
            role='剧情代理 (Plot Weaver)',
            goal='编织严谨的多线叙事，确保逻辑无懈可击、节奏扣人心弦。',
            backstory='你是一位精密如蛛网的剧情建筑师，精于铺设因果链条和伏笔暗线。你让故事层层递进，高潮迭起，同时注入情感张力，确保每个转折不只惊艳，还直击读者内心。',
            llm=get_llm(get_agent_model('plot_weaver')),
            verbose=True
        )

    def character_builder(self):
        return Agent(
            role='角色代理 (Character Builder)',
            goal='铸造立体、多面且情感丰沛的角色，让他们如活人般呼吸。',
            backstory='你是一位洞察人性的灵魂雕塑家，深挖角色的欲望、恐惧与成长弧光。你通过独特对话和内在冲突展现性格，避免直白讲述，而是用微妙言语和情感波澜，让角色跃然纸上，引发读者强烈共鸣。',
            llm=get_llm(get_agent_model('character_builder')),
            verbose=True
        )

    def scene_painter(self):
        return Agent(
            role='场景代理 (Scene Painter)',
            goal='绘就沉浸式环境氛围，用感官细节唤醒读者想象。',
            backstory='你是一位文字幻术师，能将抽象场景化为五感盛宴。无论霓虹都市的脉动还是仙山云海的缥缈，你都注入情感温度，让环境不只是背景，而是角色内心镜像，增强故事的代入与张力。',
            llm=get_llm(get_agent_model('scene_painter')),
            verbose=True
        )

    def climax_optimizer(self):
        return Agent(
            role='爽点代理 (Climax Optimizer)',
            goal='铸造肾上腺素飙升的高潮桥段，释放读者积蓄的情感张力。',
            backstory='你是一位情绪引爆专家，精于铺垫与爆发。你捕捉读者期待的峰值，在关键节点释放热血或心碎，让高潮不止于情节，而是情感风暴，留下难以忘怀的回响。',
            llm=get_llm(get_agent_model('climax_optimizer')),
            verbose=True
        )

    def punchline_king(self):
        return Agent(
            role='爆梗王 (Punchline King)',
            goal='根据世界观创作贴合背景的幽默金句与反转台词，提升故事趣味性。',
            backstory='你是一位文化融合的幽默大师，将现代智慧转化为故事语境下的锋芒。你让每个梗都根植于世界观，自然融入剧情，不仅逗乐读者，还深化情感表达，避免任何违和感。',
            llm=get_llm(get_agent_model('punchline_king')),
            verbose=True
        )

    def consistency_checker(self):
        return Agent(
            role='编辑代理 (Consistency Checker)',
            goal='严查逻辑漏洞、统一设定文风，确保情感表达连贯自然。',
            backstory='你是一位鹰眼般的质量守护者，无情捕捉任何不协调之处。从设定冲突到情感漂移，你都精准修正，让故事如精密仪器般运转，情感弧线丝丝入扣。',
            llm=get_llm(get_agent_model('consistency_checker')),
            verbose=True
        )

    def story_writer(self):
        return Agent(
            role='核心写手 (Lead Writer)',
            goal='依据大纲创作优美流畅的正文，坚持"展示而非讲述"，注入情感深度。',
            backstory='你是一位笔触细腻的叙事大师，将大纲化为生动画卷。你通过动作、对话与心理交织，推动剧情，同时层层铺陈情感，让读者身临其境，沉浸在角色的喜怒哀乐中。',
            llm=get_llm(get_agent_model('story_writer')),
            verbose=True
        )

    def outline_architect(self):
        return Agent(
            role='大纲架构师 (Outline Architect)',
            goal='基于企划书构建结构严谨、层次分明的小说大纲，确保剧情完整、节奏合理、情感饱满。',
            backstory='你是精通叙事结构的大纲设计大师，擅长将企划书转化为可执行的章节规划。精通三幕式、起承转合结构，懂得设置悬念、高潮、转折，规划伏笔和回收点。每章大纲包含：核心事件、人物动作、情感转折、伏笔提示、前后衔接。输出格式：### 第X章 标题，内容遵循任务要求的具体格式。',
            llm=get_llm(get_agent_model('outline_architect')),
            verbose=True,
            allow_delegation=False
        )

    def format_editor(self):
        return Agent(
            role='格式编辑专家 (Format Editor)',
            goal='统一和美化 Markdown 输出，优化段落长度，确保格式专业、可读性强。',
            backstory='你是专业的 Markdown 格式编辑专家，擅长统一标题层级、优化段落长度（60-140字）、规范对话格式，让小说正文排版美观易读，符合网文手机阅读体验。只处理格式，不修改内容。',
            llm=get_llm(get_agent_model('format_editor')),
            verbose=True,
            allow_delegation=False
        )

    # ==================== 企划书 Crew Agents ====================
    
    def market_analyst(self):
        return Agent(
            role='市场趋势分析师 (Market Analyst)',
            goal='分析畅销书市场数据，评估创意的市场潜力和读者定位。',
            backstory='你是一位对网文市场了如指掌的资深分析师，追踪各大平台的榜单、订阅数据和读者反馈。你能精准判断一个创意是否符合当前热点，是否有爆款潜质，并给出市场定位建议。',
            llm=get_llm(get_agent_model('market_analyst')),
            verbose=True,
            allow_delegation=False
        )

    def creative_director(self):
        return Agent(
            role='创意总监 (Creative Director)',
            goal='整合创意元素，确立书名、Logline（一句话梗概）和核心冲突。',
            backstory='你是一位擅长提炼核心卖点的创意总监，能从杂乱的灵感中抓住最吸引人的部分。你精于打磨书名和Logline，让读者一眼就被吸引，同时明确核心冲突，为后续创作指明方向。',
            llm=get_llm(get_agent_model('creative_director')),
            verbose=True,
            allow_delegation=False
        )

    def world_builder(self):
        return Agent(
            role='世界观架构师 (World Builder)',
            goal='构建详细的世界观设定，包括魔法系统、地理、技术等级、社会结构等。',
            backstory='你是一位世界观构建大师，擅长创造完整、自洽的虚构世界。你能从核心创意出发，系统性地设计世界的运行规则、历史背景、文化特征，让虚构世界真实可信，为故事提供坚实基础。',
            llm=get_llm(get_agent_model('world_builder')),
            verbose=True,
            allow_delegation=False
        )

    def naming_expert(self):
        return Agent(
            role='命名专家 (Naming Expert)',
            goal='审查和优化企划书中的所有名称，确保符合世界观、避免AI常用名、提升真实感和记忆点。',
            backstory='你是一位精通命名艺术的专家，深谙不同文化背景下的命名规律。你能识别AI生成的常见套路名称（如"云逸"、"墨染"、"雪儿"、"林xx"、"傅xx"等），并基于世界观、文化背景、角色性格，创作出独特、自然、有记忆点的名称。你熟悉各种命名风格：古风、现代、奇幻、科幻等，能让每个名称都贴合故事设定，避免违和感。',
            llm=get_llm(get_agent_model('naming_expert')),
            verbose=True,
            allow_delegation=False
        )

    # ==================== 大纲生成 Crew Agents ====================
    
    def lead_outliner(self):
        return Agent(
            role='首席大纲师 (Lead Outliner)',
            goal='生成基于事件的完整故事图谱，确保剧情逻辑严密、节奏合理。',
            backstory='你是一位故事结构专家，精通事件图谱（Event Graph）的设计。你能将企划书中的创意转化为一系列关键事件，明确因果关系和时间线，为整个故事搭建坚实的骨架。',
            llm=get_llm(get_agent_model('lead_outliner')),
            verbose=True,
            allow_delegation=False
        )

    def character_arc_designer(self):
        return Agent(
            role='人物弧光设计师 (Character Arc Designer)',
            goal='设计主要角色的成长路径，确保人物弧光与大纲事件完美匹配。',
            backstory='你是一位人物心理专家，深谙角色成长的规律。你能为每个主要角色设计清晰的弧光（从起点到终点的转变），确保角色在每个关键事件中的表现符合其内在逻辑，让人物成长自然可信。',
            llm=get_llm(get_agent_model('character_arc_designer')),
            verbose=True,
            allow_delegation=False
        )

    def logic_validator(self):
        return Agent(
            role='逻辑校验员 (Logic Validator)',
            goal='严查大纲中的逻辑漏洞和因果问题，确保故事自洽。',
            backstory='你是一位严谨的逻辑审查专家，擅长发现剧情中的矛盾和漏洞。你会反复追问"为什么"，挑战每个事件的合理性，揪出那些经不起推敲的设定，确保故事经得起读者的审视。',
            llm=get_llm(get_agent_model('logic_validator')),
            verbose=True,
            allow_delegation=False
        )

    # ==================== 细纲生成 Crew Agents ====================
    
    def narrative_planner(self):
        return Agent(
            role='叙事规划师 (Narrative Planner)',
            goal='决定每章的详写/略写策略，安排非线性叙事（插叙、倒叙、多线并进）。',
            backstory='你是一位叙事技巧大师，精通各种叙事手法。你能根据剧情需要，决定哪些情节需要详细展开，哪些可以一笔带过，如何通过非线性叙事增强故事张力，让读者始终保持好奇心。',
            llm=get_llm(get_agent_model('narrative_planner')),
            verbose=True,
            allow_delegation=False
        )

    def scene_weaver(self):
        return Agent(
            role='场景设计师 (Scene Weaver)',
            goal='为每章生成详细的场景节拍表，包含感官细节和情绪节点。',
            backstory='你是一位场景构建专家，能将抽象的事件转化为具体的场景序列。你为每个场景设计节拍（Beats），明确每个节拍的视觉、听觉、嗅觉细节，以及情绪起伏点，为写手提供清晰的执行指南。',
            llm=get_llm(get_agent_model('scene_weaver')),
            verbose=True,
            allow_delegation=False
        )

    # ==================== 正文撰写 Crew Agents ====================
    
    def continuity_coordinator(self):
        return Agent(
            role='连续性协调员 (Continuity Coordinator)',
            goal='管理上下文连贯性，压缩历史剧情摘要，检查新内容与前文的一致性。',
            backstory='你是一位记忆管理专家，负责维护故事的连贯性。你会将已写完的章节压缩成摘要，提取关键信息供后续章节参考，同时检查新内容是否与前文设定冲突，确保整个故事前后一致。',
            llm=get_llm(get_agent_model('continuity_coordinator')),
            verbose=True,
            allow_delegation=False
        )

    def creative_critic(self):
        return Agent(
            role='创意批判专家 (Creative Critic)',
            goal='以同行评审的方式提出建设性批评意见，帮助写手改进作品，同时保留其独特的创作风格。',
            backstory='你是一位资深的文学评论家和创意顾问，擅长以客观、专业的视角审视作品。你深谙"盲审同行评审"的原则：只提意见，不改原文。你关注创意独特性、文风一致性、情感深度、节奏把控等核心创作要素，能精准指出问题所在，并提供建设性的改进方向，但绝不越界直接修改，尊重写手的创作自主权和独特文风。',
            llm=get_llm(get_agent_model('creative_critic')),
            verbose=True,
            allow_delegation=False
        )
