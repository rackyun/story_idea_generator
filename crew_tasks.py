from crewai import Task
from textwrap import dedent
from utils.novel_length_config import get_category_by_name, get_chapter_planning_guide

class StoryTasks:
    @staticmethod
    def _ensure_context_list(context_input):
        """确保 context 是列表格式，且只包含 Task 对象"""
        if context_input is None:
            return []
        if isinstance(context_input, list):
            return [t for t in context_input if t is not None]
        return [context_input]

    @staticmethod
    def _to_chinese_num(num):
        """将数字转换为汉字数字"""
        chinese_nums = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
        if num <= 10:
            return chinese_nums[num]
        elif num < 20:
            return '十' + (chinese_nums[num % 10] if num % 10 > 0 else '')
        elif num < 100:
            tens = num // 10
            ones = num % 10
            if ones == 0:
                return chinese_nums[tens] + '十'
            else:
                return chinese_nums[tens] + '十' + chinese_nums[ones]
        else:
            return str(num)

    def brainstorm_task(self, agent, topic, rounds=3):
        return Task(
            description=dedent(f"""
                针对主题 '{topic}' 进行多轮脑暴。
                
                请进行 {rounds} 轮思考迭代：
                0. 尽量贴合主题，不要随意修改主题的元素，如题材、主角、方向、基调、背景世界、物品、反派等。
                1. 提出初步核心创意（Core Idea）。
                2. 自我批判，找出套路化的地方（例如：老套的复仇、无脑爽文逻辑等）。
                3. 提出改进后的反套路创意，思考如何旧瓶装新酒。
                
                输出必须包含：
                - 核心梗概
                - 主要看点/钩子（一句话吸引读者）
                - 潜在的市场卖点（结合当前网文趋势）
                - 核心冲突与预期高潮
            """),
            agent=agent,
            expected_output="一份经过多轮迭代、极具创意的故事核心脑洞方案。"
        )

    def plot_development_task(self, agent, context_idea, target_word_count: str = "短篇小说 (1-10万字)"):
        context_list = self._ensure_context_list(context_idea)
        
        return Task(
            description=dedent(f"""
                基于上下文中的核心创意，构建详细的故事大纲。

                **重要**：请仔细阅读上下文（Context）中的核心创意内容，这是你构建大纲的基础。

                **目标字数范围**: {target_word_count}

                要求：
                0. **严格遵循核心创意**：忠实于原始创意的世界观、人物设定和主题方向，不得偏离或随意修改核心设定。
                1. 设计清晰的起承转合（三幕式或四幕式结构）。
                2. 明确关键转折点（Plot Points），特别是"激励事件"（Inciting Incident）和"中点"（Midpoint）。
                3. 梳理主线任务和至少一条副线。
                4. **根据目标字数范围，合理规划每一幕的篇幅和节奏**：
                   - 微型小说 (1万字以内): 简洁紧凑，1-2幕，快速推进
                   - 短篇小说 (1-10万字): 3-4幕，适度展开，单一主线
                   - 中篇小说 (10-50万字): 4-5幕，充分铺垫，1-2条支线
                   - 长篇小说 (50-200万字): 5-6幕，多条支线，复杂人物关系
                   - 超长篇小说 (200万字以上): 6+幕，复杂世界观，多重主线
                5. 在大纲中标注每一幕的预计字数范围。
            """),
            agent=agent,
            context=context_list,
            expected_output="一份结构严谨、逻辑通顺的分幕式故事大纲，包含每一幕的预计字数。"
        )

    def character_design_task(self, agent, context_plot):
        context_list = self._ensure_context_list(context_plot)
        
        return Task(
            description=dedent(f"""
                基于上下文中的故事大纲，设计主要角色（主角及核心配角）。

                **重要**：请仔细阅读上下文（Context）中的故事大纲内容，这是你设计角色的基础。
                
                要求：
                1. 姓名（符合文化背景，拒绝AI味，参考现实或经典作品命名逻辑）。
                2. 外貌、性格、核心欲望、恐惧。
                3. **独特的说话风格或口头禅**（请为每个主要角色提供3句典型的台词示例）。
                4. 人物关系图谱。
                5. 角色反差萌点或记忆点。
            """),
            agent=agent,
            context=context_list,
            expected_output="包含主角及核心配角的详细人物小传、台词示例和关系图。"
        )

    def scene_enhancement_task(self, agent, context_plot):
        context_list = self._ensure_context_list(context_plot)
        
        return Task(
            description=dedent(f"""
                为上下文中的故事大纲的关键场景添加细节描写。

                **重要**：请仔细阅读上下文（Context）中的故事大纲内容，这是你设计场景的基础。
                
                要求：
                1. 选取3个关键场景。
                2. 进行五感描写（视觉、听觉、嗅觉、触觉、味觉）。
                3. 营造符合剧情基调的氛围。
                4. **提供"展示而非讲述"（Show, Don't Tell）的描写范例**。
            """),
            agent=agent,
            context=context_list,
            expected_output="三个关键场景的沉浸式描写片段。"
        )

    def climax_optimization_task(self, agent, context_plot):
        context_list = self._ensure_context_list(context_plot)
        
        return Task(
            description=dedent(f"""
                分析上下文中的故事大纲，优化高潮部分。

                **重要**：请仔细阅读上下文（Context）中的故事大纲内容，这是你优化高潮的基础。
                
                要求：
                1. 识别故事的高潮段落。
                2. 提出强化情绪冲突的建议。
                3. 设计一个令人印象深刻的“名场面”。
            """),
            agent=agent,
            context=context_list,
            expected_output="针对高潮段落的优化方案及名场面设计。"
        )

    def final_review_task(self, agent, full_context, target_word_count: str = "短篇小说 (1-10万字)"):
        context_list = self._ensure_context_list(full_context)
        
        return Task(
            description=dedent(f"""
                作为总编和质检员，审查上下文中的所有生成内容。

                **重要**：请仔细阅读上下文（Context）中的所有任务输出，包括：
                - 脑洞代理的核心创意
                - 剧情代理的故事大纲
                - 角色代理的角色设计
                - 场景代理的场景描写
                - 爽点代理的高潮设计

                **目标字数范围**: {target_word_count}

                要求：
                1. 检查逻辑是否自洽。
                2. 检查人设是否崩塌。
                3. 统一文风，修正格式。
                4. 输出最终的《小说企划书》。
                5. **根据目标字数范围，给出建议的章节规划和每章字数**：
                   - 微型小说 (1万字以内): 建议1-5章，每章1500-3000字
                   - 短篇小说 (1-10万字): 建议10-50章，每章2000-3000字
                   - 中篇小说 (10-50万字): 建议50-200章，每章2000-3000字
                   - 长篇小说 (50-200万字): 建议200-800章，每章2000-3000字
                   - 超长篇小说 (200万字以上): 建议800+章，每章2000-3000字
                6. 在企划书中明确标注目标字数范围和建议的章节规划。

                **重要限制**：
                - 企划书总字数不得超过 2000 字
                - 请精简内容，突出核心要点
                - 保持结构清晰，避免冗余描述
            """),
            agent=agent,
            context=context_list,
            expected_output="一份格式完美、逻辑自洽的最终版《小说企划书》，包含目标字数和章节规划建议。字数不超过2000字。"
        )

    def chapter_outline_task(self, agent, plan_content, length_type):
        return Task(
            description=dedent(f"""
                基于以下《小说企划书》，制定详细的分章大纲：
                {plan_content}

                目标篇幅：{length_type}

                要求：
                1. 根据目标篇幅规划章节数量（短篇通常1-3章，中篇更多）。
                2. 每一章都需要有：
                   - 章节标题
                   - 核心事件
                   - 出场人物
                   - 情感/剧情转折点
                3. 确保章节之间衔接自然，节奏紧凑。
            """),
            agent=agent,
            expected_output="一份包含所有章节详情的结构化大纲列表。"
        )

    def outline_analysis_task(self, agent, outline_content, previous_chapter_content, num_chapters, story_context=""):
        """
        大纲分析任务 - 分析已有大纲，为后续写作提供指导
        
        Args:
            agent: 总编智能体
            outline_content: 已有的大纲内容
            previous_chapter_content: 上一章内容（用于衔接）
            num_chapters: 要生成的章节数量
            story_context: 企划书/故事背景（可选）
        """
        return Task(
            description=dedent(f"""
                作为总编，分析已有的大纲，为后续写作团队提供清晰的指导。

                **已有大纲**：
                {outline_content}

                **上一章内容**（用于衔接）：
                {previous_chapter_content[:500] if previous_chapter_content else "（这是开篇，无上一章）"}

                **故事背景**（企划书）：
                {story_context if story_context else "（无企划书）"}

                **任务要求**：
                1. **理解大纲**：仔细分析已有大纲，理解每章的核心事件、人物、场景、情感基调
                2. **提取关键信息**：
                   - 章节标题和核心事件
                   - 出场人物及其关系
                   - 场景设置和氛围
                   - 情感转折点和伏笔
                   - 与上一章的衔接点
                3. **写作指导**：
                   - 明确每章的写作重点和注意事项
                   - 指出需要特别注意的细节（人物性格、世界观设定等）
                   - 标注需要回收的伏笔或需要埋下的新伏笔
                4. **确保一致性**：
                   - 与企划书的世界观、人物设定保持一致
                   - 与上一章的内容和风格保持连贯
                   - 确保剧情逻辑合理

                **重要**：
                - 只需要分析已有的大纲，**不要生成新的大纲**
                - 只需要生成 {num_chapters} 章的内容，不要超出范围
                - 为后续的写作团队提供清晰、可执行的指导
                
                **输出格式**：
                必须以 `## [大纲分析]` 开头，便于后续任务识别。
            """),
            agent=agent,
            expected_output=f"以 `## [大纲分析]` 开头的详细分析报告，包含每章的写作指导、关键信息和注意事项，覆盖 {num_chapters} 章内容。"
        )

    def comprehensive_outline_task(self, agent, plan_content, length_type):
        """
        综合大纲生成任务 - 使用大纲架构师生成完整的章节大纲

        Args:
            agent: 大纲架构师智能体
            plan_content: 企划书内容
            length_type: 目标篇幅
        """
        # 检查企划书中是否包含章节信息，如果包含则添加相应指令
        chapter_keywords = ['章节', '第', '章', '章节规划', '章节名称', '章节大纲', '章节标题']
        chapter_instruction = ""
        if any(keyword in plan_content for keyword in chapter_keywords):
            chapter_instruction = """
                
                **重要**：如果企划书中已经包含章节名称、章节规划或章节大纲要求，请：
                1. **优先使用企划书中的章节名称**，保持名称一致
                2. **参照企划书中的章节大纲要求**进行扩充和细化
                3. 在企划书已有章节框架的基础上，补充详细的剧情细节
                4. 如果企划书指定了章节数量或章节分布，请严格遵循"""
        
        return Task(
            description=dedent(f"""
                基于《小说企划书》构建完整的章节大纲。

                **企划书内容**：
                {plan_content}

                **目标篇幅**：{length_type}

                **任务要求**：

                1. **章节规划**（根据目标篇幅）：
                   - 微型小说（1万字以内）：3-5章
                   - 短篇小说（1-10万字）：5-15章
                   - 中篇小说（10-50万字）：15-30章
                   - 长篇小说（50-200万字）：30-100章
                   - 超长篇小说（200万字以上）：100+章
                {chapter_instruction}

                2. **每章大纲格式**：
                   ```
                   ### 第X章 [章节标题]

                   **核心事件**：主要剧情发展
                   **出场人物**：登场的主要角色
                   **场景设置**：时间、地点、氛围
                   **情感基调**：情感色彩
                   **关键台词/动作**：推动剧情的关键表现
                   **伏笔提示**：埋下的伏笔或回收的伏笔
                   **与前后章的衔接**：承接上章，引出下章
                   ```

                3. **质量要求**：
                   - 严格遵循企划书的世界观、人物设定、核心冲突
                   - 确保情感曲线有起伏，每章有明确目标和转折点
                   - 节奏张弛有度，伏笔提前规划

                4. **输出格式**：
                   - Markdown 格式，章节标题使用 ### 第X章 标题
                   - 在大纲开头添加整体结构说明（起承转合的章节分布）
            """),
            agent=agent,
            expected_output=f"""完整的章节大纲（Markdown格式），包含：
1. 整体结构说明（起承转合的章节分布）
2. 每章详细大纲（核心事件、人物、场景、情感、台词/动作、伏笔、衔接）
3. 章节数量符合{length_type}的要求
4. 格式规范，便于解析和后续写作"""
        )


    def character_enrichment_task(self, agent, context_outline=None):
        context_list = self._ensure_context_list(context_outline)
        
        return Task(
            description=dedent(f"""
                基于分章大纲（见上下文），深入挖掘角色在每一章的心理活动：
                
                要求：
                1. 分析主角及主要配角在每一章的心理状态、动机变化和潜台词。
                2. 为后续的写手提供具体的行为或对话建议，以体现人物性格。
                3. 确保人物行为逻辑与大纲剧情一致。
                4. **重点分析"潜台词"（Subtext）**：角色嘴上说的话和心里想的事是否一致？如果不一致，如何表现？
                
                **输出格式**：
                必须以 `## [角色心理]` 开头，便于后续任务识别。
            """),
            agent=agent,
            context=context_list,
            expected_output="以 `## [角色心理]` 开头的针对每一章的角色心理分析和行为建议文档。"
        )

    def scene_enrichment_task(self, agent, context_outline=None):
        context_list = self._ensure_context_list(context_outline)

        return Task(
            description=dedent(f"""
                基于分章大纲（见上下文），为每一章的关键场景添加感官细节：

                要求：
                1. 每章选取1-2个核心场景进行详细的环境描写设定（光影、天气、氛围、气味）。
                2. 提供极具画面感的描述性文字，供后续写手直接引用或改编。
                3. 确保场景氛围符合剧情基调。
                4. **注意环境与人物心情的映射关系**（情景交融）。
                
                **输出格式**：
                必须以 `## [场景素材]` 开头，便于后续任务识别。
            """),
            agent=agent,
            context=context_list,
            expected_output="以 `## [场景素材]` 开头的针对每一章关键场景的详细环境描写素材。"
        )

    def punchline_injection_task(self, agent, context_outline=None):
        context_list = self._ensure_context_list(context_outline)
        
        return Task(
            description=dedent(f"""
                你是爆梗设计专家，专门为小说每一章注入高传播力、高记忆点的金句、反转梗、情绪炸点或幽默台词。

                **核心使命**：
                基于上下文中的【分章大纲】，为每一章精准设计 3–5 个高质量“爆梗点”，让读者忍不住截图、分享、刷弹幕。

                **严格执行要求**：
                1. **必须逐章完整阅读大纲**，不得遗漏任何章节。
                2. 每个梗必须同时满足以下四条铁律：
                - **世界观 100% 适配**：完全融入故事的时代、文化、设定（修仙不能用“yyds”，末世不能用古风诗句）
                - **角色人设 100% 一致**：高冷角色绝不说沙雕梗，逗比角色不能突然深沉
                - **情节自然融入**：梗要像对话/心理/旁白般顺畅出现，不能生硬插入
                - **高情绪价值**：必须制造爽感、扎心、爆笑、泪目、鸡皮疙瘩等其中至少一种强烈情绪
                3. 梗的类型可以包括（但不限于）：
                - 反差式金句（高冷角色突然毒舌）
                - 意料之外的反转台词
                - 扎心/刀子语录（虐心向）
                - 结合设定本土化的网络梗改编
                - 装逼打脸神句
                - 情绪爆发点睛之笔
                - 令人捧腹的黑色幽默/自嘲
                4. **严禁**使用低级、低俗、违和的现代梗直接套用，必须深度改造。

                **输出格式**（必须严格遵守）：
                必须以 `## [爆梗金句]` 开头，然后为每章输出一个独立小节，使用以下结构：

                ## 第X章 [章节标题]

                - **梗1**：【具体台词/句子】  
                植入位置：【具体情境，例如“主角被围攻时反击”】  
                情绪目标：【爽/虐/笑/泪/鸡皮】  
                创作思路：【一句话说明为什么这个梗会爆】

                - **梗2**：...

                （每章 3–5 个，依次列出）

                **最终输出要求**：
                - 只输出以上结构清单，**禁止任何开场白、总结、说明、字数统计**。
                - 完整覆盖上下文中的所有章节。
                - 语言犀利、抓眼球、有记忆点。
            """),
            agent=agent,
            context=context_list,
            expected_output="以 `## [爆梗金句]` 开头的结构化的爆梗设计清单，按章节分隔，每章 3–5 个梗，每个梗包含具体台词/句子、植入情境、情绪目标、创作思路。输出必须干净、直接，仅包含清单内容，无任何多余文字。"
        )

    def full_story_writing_task(self, agent, context_materials=None, num_chapters=1, chapter_start_num=1, use_chinese_numerals=True):
        """
        核心写手任务 - 撰写小说正文
        
        Args:
            agent: 执行任务的 Agent
            context_materials: 上下文材料列表（Task 对象）
            num_chapters: 要生成的章节数量（默认1）
            chapter_start_num: 起始章节号（默认1）
            use_chinese_numerals: 是否使用汉字数字（默认True）
        """
        context_list = self._ensure_context_list(context_materials)
        
        if use_chinese_numerals:
            ch1 = self._to_chinese_num(chapter_start_num)
            chapter_format_example = f"## 第{ch1}章 标题"
            if num_chapters > 1:
                ch2 = self._to_chinese_num(chapter_start_num + 1)
                chapter_format_example += f"\n## 第{ch2}章 标题"
            chapter_format_note = f"**必须使用汉字数字**，例如：{chapter_format_example}"
            chapter_example = f"## 第{ch1}章"
        else:
            chapter_format_example = f"## 第{chapter_start_num}章 标题"
            if num_chapters > 1:
                chapter_format_example += f"\n## 第{chapter_start_num + 1}章 标题"
            chapter_format_note = f"使用阿拉伯数字，例如：{chapter_format_example}"
            chapter_example = f"## 第{chapter_start_num}章"
        
        return Task(
            description=dedent(f"""
                你是核心写手，负责将上下文提供的【分章大纲】、【角色心理分析】、【场景描写素材】、【爆梗金句清单】整合成高质量小说正文。

                **特别注意 - 识别上下文输入**：
                请通过以下标识精准定位上下文中的各类素材：
                - **大纲分析**：查找 `## [大纲分析]` 开头的部分。
                - **角色心理**：查找 `## [角色心理]` 开头的部分。
                - **场景素材**：查找 `## [场景素材]` 开头的部分。
                - **爆梗金句**：查找 `## [爆梗金句]` 开头的部分。

                **最高优先级 - 输出纪律**：
                1. **必须直接输出完整小说正文**，从第一章标题开始，**禁止任何前言、说明、总结、字数统计、分析、备注**。
                2. **严禁使用占位符**，如“（见上）”“如上所述”“上下文已有”等。
                3. 如果上下文未提供完整所需素材，直接输出：
                “错误：上下文缺少必要素材（大纲/角色分析等），无法生成正文。”
                然后停止。
                4. **只生成指定的 {num_chapters} 章**，从第{chapter_start_num}章开始，**绝不多写一章**。

                **章节编号格式**：{chapter_format_note}
                - 必须使用“## 第X章 [标题]”形式，X 为汉字数字（一、二、三……）
                - 标题保持大纲原样，或微调更吸引人但不得大幅改动

                **写作核心原则**（必须严格执行）：
                1. **忠实大纲与企划书**：剧情走向、伏笔、爽点、核心冲突不得改变。
                2. **展示而非讲述**（Show, Don't Tell）：通过动作、对话、感官细节、心理活动、环境互动表现情感与状态，**禁止直接写“他很愤怒/开心/伤心”**。
                3. **外貌与动作描写**（重要，必须严格执行）：
                   - **外貌描写**：
                     * 避免使用俗套词汇（如"倾国倾城"、"剑眉星目"、"肤如凝脂"等）
                     * 通过2-3个独特细节展现角色个性（疤痕、特殊配饰、习惯性表情等）
                     * 结合气质和神态描写，而非单纯罗列五官
                     * 使用比喻和联想增强画面感
                     * 根据角色身份、背景、性格设定合理的外貌特征
                     * 初次登场时提供100-150字的外貌描写，后续可通过细节补充
                   - **动作描写**：
                     * 为每个主要角色设计标志性动作或习惯性小动作
                     * 不同情绪状态下的动作要符合人物性格（紧张、愤怒、喜悦、悲伤等）
                     * 关键场景的动作序列要流畅自然，符合人体力学
                     * 动作要结合心理状态和环境互动
                     * 通过动作展现性格，而非直接说明
                   - **描写原则**：
                     * 描写要生动具体，避免抽象概括
                     * 让读者"看见"人物，而不是"读到"人物
                     * 外貌和动作描写要自然融入剧情，不要生硬插入
                4. **段落长度控制**（网文手机阅读最优体验）：
                - 平均段落长度控制在 **60–140 字**（最优区间 80–110 字）
                - 过长段落（>160 字）必须拆分（按逻辑/动作/心理断点）
                - 过短段落（<40 字，非对话/强调）尽量合并（保持连贯）
                - 对话段可短至 30–80 字，战斗/高潮段可略长至 140–160 字
                - 目标：手机竖屏阅读时每段 3–8 行，避免密密麻麻或过于碎片
                5. **节奏与情绪**：
                - 每章必须有清晰的情绪曲线（铺垫→上升→高潮→回落/钩子）
                - 男频爽文每 800–1200 字至少 1 次小爽点，重要章节要有大爽点
                6. **深度整合素材**：
                   - 自然融入【场景描写素材】和【爆梗金句】
                   - 结合【角色心理分析】让人物行为真实有层次
                   - 命名要符合世界观，保持一致性，避免AI味浓厚的名字
                7. **每章字数**：严格控制在 **2500–3000 字**（±10%）

                **写作前必须完成以下思考（不要输出思考过程）**：
                - 本章核心情绪基调是什么？
                - 情绪曲线如何设计（起伏点在哪）？
                - 主要爽点/钩子位置？
                - 平均段落长度如何控制？

                **输出格式**（必须严格遵守）：
                - 直接开始输出正文
                - 每章以 ## 第X章 [标题] 开头
                - 段落之间空一行
                - **完整输出全部 {num_chapters} 章**，结尾直接结束正文，无任何多余文字
            """),
            agent=agent,
            context=context_list,
            expected_output=f"包含 {num_chapters} 章的完整小说正文（Markdown格式），每章约2500-3000字，使用汉字数字编号。必须直接输出正文内容，禁止输出总结、说明或描述性文字。输出格式：## 第X章 标题，然后是完整的章节正文。"
        )

    def creative_critique_task(self, agent, context_draft=None, num_chapters=1, chapter_start_num=1, use_chinese_numerals=True):
        """
        创意批判任务 - 盲审同行评审，只提意见不改文
        
        Args:
            agent: 创意批判专家 Agent
            context_draft: 初稿任务（Task 对象）
            num_chapters: 章节数量（默认1）
            chapter_start_num: 起始章节号（默认1）
            use_chinese_numerals: 是否使用汉字数字（默认True）
        """
        context_list = self._ensure_context_list(context_draft)
        
        return Task(
            description=dedent(f"""
                作为创意批判专家，对上下文中的小说初稿进行盲审同行评审。

                **核心原则 - 只提意见，不改原文**：
                1. 你必须仔细阅读上下文中的完整小说初稿（{num_chapters}章）
                2. **严禁直接修改原文**，只能提出批评意见和改进建议
                3. 尊重写手的创作风格和独特文风，不要试图统一或改变其风格
                4. 你的目标是帮助写手提升作品质量，而非替代写手创作

                **审查重点**：
                1. **创意独特性**：
                   - 情节是否过于套路化或同质化？
                   - 是否有独特的创意亮点或反套路设计？
                   - 人物行为是否符合其独特性格，避免脸谱化？
                2. **文风一致性**：
                   - 文风是否前后一致？
                   - 是否有突兀的风格转换？
                   - 语言风格是否符合故事基调和世界观？
                3. **情感深度**：
                   - 情感描写是否真实、有层次？
                   - 角色情感变化是否自然？
                   - 是否有效触动读者情感？
                4. **节奏把控**：
                   - 章节节奏是否合理（铺垫、发展、高潮、钩子）？
                   - 是否有拖沓或过于急促的部分？
                   - 爽点/爆点的分布是否合理？
                5. **细节与画面感**：
                   - 描写是否具体生动，有画面感？
                   - 是否有"展示而非讲述"的不足？
                   - 感官细节是否丰富？
                6. **逻辑与连贯性**：
                   - 剧情逻辑是否自洽？
                   - 前后文是否连贯？
                   - 是否有明显的矛盾或漏洞？

                **输出格式**（必须严格遵守）：
                必须以以下格式输出，**禁止输出修改后的正文**：

                ```
                ## 创意批判意见

                ### 总体评价
                [对整体作品的简要评价，突出优点和主要问题]

                ### 分章详细意见

                #### 第X章 [章节标题]
                **优点**：
                - [具体优点1]
                - [具体优点2]

                **需要改进的地方**：
                1. **[问题类型]**：[具体问题描述]
                   - **位置**：[大致位置，如"第X段"或"XX情节处"]
                   - **建议**：[建设性的改进建议，但不要直接写修改后的文字]
                   - **原因**：[为什么需要改进]

                2. **[问题类型]**：[具体问题描述]
                   - **位置**：[大致位置]
                   - **建议**：[改进建议]
                   - **原因**：[原因说明]

                [继续列出其他章节的意见...]

                ### 整体建议
                [针对整体作品的改进建议，如节奏调整、风格统一等]

                ### 保留的独特风格
                [指出写手独特的文风特点，建议保留的部分]
                ```

                **重要约束**：
                - **绝对禁止**输出修改后的正文内容
                - **绝对禁止**使用"修改为"、"改为"等直接修改的表述
                - 只能使用"建议"、"可以考虑"、"可以尝试"等建议性表述
                - 意见要具体、可操作，但不要越界直接改文
            """),
            agent=agent,
            context=context_list,
            expected_output=f"创意批判意见报告（Markdown格式），包含对{num_chapters}章的详细评审意见和改进建议，但绝不包含修改后的正文内容。"
        )

    def story_revision_task(self, agent, context_draft=None, context_critique=None, num_chapters=1, chapter_start_num=1, use_chinese_numerals=True):
        """
        故事修订任务 - 写手根据批判意见自行修改
        
        Args:
            agent: 核心写手 Agent
            context_draft: 初稿任务（Task 对象）
            context_critique: 批判意见任务（Task 对象）
            num_chapters: 章节数量（默认1）
            chapter_start_num: 起始章节号（默认1）
            use_chinese_numerals: 是否使用汉字数字（默认True）
        """
        context_list = self._ensure_context_list([context_draft, context_critique])
        
        if use_chinese_numerals:
            ch1 = self._to_chinese_num(chapter_start_num)
            chapter_format_example = f"## 第{ch1}章 标题"
            chapter_format_note = f"**必须使用汉字数字**，例如：{chapter_format_example}"
        else:
            chapter_format_example = f"## 第{chapter_start_num}章 标题"
            chapter_format_note = f"使用阿拉伯数字，例如：{chapter_format_example}"
        
        return Task(
            description=dedent(f"""
                作为核心写手，根据创意批判专家的意见，对初稿进行修订。

                **上下文说明**：
                1. 上下文中包含你的**初稿**（完整小说正文）
                2. 上下文中包含**创意批判意见**（以 `## 创意批判意见` 开头）
                3. 请仔细阅读批判意见，理解问题所在和改进方向

                **修订原则**：
                1. **保留你的独特文风**：批判意见是为了改进，不是要你改变创作风格
                2. **选择性采纳建议**：不是所有建议都必须采纳，但要认真考虑
                3. **保持创作自主权**：你可以用自己的方式解决问题，不必完全照搬建议
                4. **提升作品质量**：目标是让作品更好，同时保持你的创作特色

                **修订重点**：
                1. 根据批判意见中的具体问题，有针对性地改进
                2. 保留批判意见中提到的"优点"和"独特风格"
                3. 解决逻辑漏洞、节奏问题、情感深度不足等核心问题
                4. 提升画面感和细节描写，但保持你的描写风格
                5. 优化创意独特性，避免套路化，但不要为了反套路而反套路

                **章节编号格式**：{chapter_format_note}

                **输出要求**：
                1. **必须输出完整的修订后小说正文**（{num_chapters}章）
                2. 每章以 ## 第X章 [标题] 开头
                3. 直接输出正文，不要输出修订说明或总结
                4. 保持原有的章节结构和字数要求（每章2500-3000字）

                **修订策略**：
                - 如果批判意见指出某处有问题，仔细思考如何改进
                - 可以调整情节、描写、对话，但要保持整体风格一致
                - 如果批判意见提到某个优点，确保在修订中保留
                - 不要为了迎合意见而失去自己的创作特色
            """),
            agent=agent,
            context=context_list,
            expected_output=f"包含 {num_chapters} 章的修订后小说正文（Markdown格式），每章约2500-3000字，使用汉字数字编号。必须直接输出正文内容，禁止输出修订说明。"
        )

    def copy_editing_task(self, agent, context_draft=None, num_chapters=1, chapter_start_num=1, use_chinese_numerals=True):
        """
        编辑润色任务

        Args:
            agent: 执行任务的 Agent
            context_draft: 初稿任务（Task 对象）
            num_chapters: 章节数量（默认1）
            chapter_start_num: 起始章节号（默认1）
            use_chinese_numerals: 是否使用汉字数字（默认True）
        """
        context_list = self._ensure_context_list(context_draft)

        if use_chinese_numerals:
            ch1 = self._to_chinese_num(chapter_start_num)
            chapter_format_example = f"## 第{ch1}章 标题"
            if num_chapters > 1:
                ch2 = self._to_chinese_num(chapter_start_num + 1)
                chapter_format_example += f"\n## 第{ch2}章 标题"
            chapter_format_note = f"**必须使用汉字数字**，例如：{chapter_format_example}"
        else:
            chapter_format_example = f"## 第{chapter_start_num}章 标题"
            if num_chapters > 1:
                chapter_format_example += f"\n## 第{chapter_start_num + 1}章 标题"
            chapter_format_note = f"使用阿拉伯数字，例如：{chapter_format_example}"

        return Task(
            description=dedent(f"""
                你现在是一位起点/晋江签约级资深责编，对上下文中的小说初稿进行精细打磨与润色。

                **最高优先级 - 必须完整获取初稿**：
                1. 上下文（Context）中包含核心写手输出的完整小说初稿，请务必逐字阅读全部内容。
                2. 小说正文通常以 "## 第X章" 或类似章节标题开头。
                3. **严禁**使用“见上文”“如上”“上下文已有”等任何形式的引用或占位符。
                4. 如果在上下文中找不到完整小说正文，**立即且仅输出**以下一句话后停止：
                “错误：上下文中未找到完整小说正文，请检查上游写手任务是否正确执行。”
                5. **必须完整处理所有章节**，不允许遗漏、截断或只处理部分内容。

                **章节编号格式**：{chapter_format_note}

                **编辑润色核心原则**（严格遵守）：
                1. 修正所有错别字、病句、标点错误、逻辑硬伤。
                2. 优化句式节奏，提升语言流畅度与画面感，杜绝生硬、啰嗦、AI味重的表达。
                3. 强化情感表现力：通过动作、细节、心理活动、环境互动“展示”情绪，而非直接叙述“他很伤心/开心”。
                4. 统一全书人名、地名、术语、称呼、时间线、修为境界等设定，不允许前后矛盾。
                5. 检查并微调人物行为是否符合已定人设，必要时轻微调整（幅度控制在不改变核心剧情的前提下）。
                6. 保持原作爽点、爆点、钩子位置不变，但可增强张力与代入感。
                7. 保留 Markdown 格式，每章以 ## 第X章 开头，段落分明，阅读体验舒适。
                8. **禁止**添加新剧情、删除原有情节、擅自更改大纲走向。

                **输出要求**（必须严格执行）：
                - 直接输出完整润色后的小说正文，从第一章开始到最后一章。
                - 每章以 ## 第X章 [章节标题] 开头（标题保持原样或微调更吸引人，但不得大幅改动）。
                - **完整输出全部 {num_chapters} 章**，不允许省略任何章节。
                - 结尾不要加任何总结、说明、备注，直接以正文结束。

                开始执行：请基于上下文中的小说初稿，输出润色后的完整版本。
            """),
            agent=agent,
            context=context_list,
            expected_output=f"包含 {num_chapters} 章的润色后小说正文（完整内容，使用汉字数字编号，禁止使用任何占位符）。"
        )

    def format_editing_task(self, agent, context_draft=None, num_chapters=1, chapter_start_num=1, use_chinese_numerals=True):
        """
        格式编辑任务 - 统一和美化 Markdown 格式，优化段落长度

        Args:
            agent: 格式编辑专家 Agent
            context_draft: 已润色的初稿任务（Task 对象）
            num_chapters: 章节数量（默认1）
            chapter_start_num: 起始章节号（默认1）
            use_chinese_numerals: 是否使用汉字数字（默认True）
        """
        context_list = self._ensure_context_list(context_draft)

        if use_chinese_numerals:
            ch1 = self._to_chinese_num(chapter_start_num)
            chapter_format_example = f"## 第{ch1}章 标题"
            if num_chapters > 1:
                ch2 = self._to_chinese_num(chapter_start_num + 1)
                chapter_format_example += f"\n## 第{ch2}章 标题"
            chapter_format_note = f"**必须使用汉字数字**，例如：{chapter_format_example}"
        else:
            chapter_format_example = f"## 第{chapter_start_num}章 标题"
            if num_chapters > 1:
                chapter_format_example += f"\n## 第{chapter_start_num + 1}章 标题"
            chapter_format_note = f"使用阿拉伯数字，例如：{chapter_format_example}"

        return Task(
            description=dedent(f"""
                对上下文中的小说正文进行格式美化和段落优化。

                **上下文说明**：上下文中包含已润色的小说正文，以 "## 第X章" 格式开头。如果找不到，输出："错误：上下文中未找到小说正文。"

                **章节编号格式**：{chapter_format_note}

                **格式编辑要求**：
                1. **标题层级**：章节 ##，小节 ###，内心独白 ####
                2. **段落间距**：每段空一行，避免连续空行 > 2
                3. **对话格式**：**角色名：** "对话内容。"
                4. **强调标记**：*斜体*（内心/低语），**粗体**（重点/喊话）
                5. **段落长度优化**（重点）：
                   - 目标：60~140字（约3~8行）
                   - 过长（>160字）：拆分成2~3段
                   - 过短（<40字，非对话/强调）：合并
                   - 特殊豁免：对话（20~30字）、战斗/高潮（140~180字）
                6. **清理美化**：删除多余空行、统一标点、每章末尾加 ---
                7. **重要原则**：只处理格式，不修改内容

                **输出格式**：直接输出格式化后的完整小说正文（{num_chapters}章），禁止输出总结或说明。
            """),
            agent=agent,
            context=context_list,
            expected_output=f"包含 {num_chapters} 章的格式化后小说正文（完整内容，使用汉字数字编号，格式统一美观，段落长度优化，禁止使用任何占位符）。"
        )

    def outline_expansion_task(self, agent, current_outline, completed_chapters_summary, num_chapters, chapters_per_block=1, context_tasks=None):
        """
        智能扩充大纲任务 - 生成按段组织的剧情大纲
        
        Args:
            agent: 执行任务的 Agent
            current_outline: 现有大纲（JSON 字符串或段列表）
            completed_chapters_summary: 已完成章节摘要
            num_chapters: 要生成的章节数
            chapters_per_block: 每几章生成一段（默认1）
            context_tasks: 上下文任务列表（可选），用于多智能体协作
        
        Returns:
            Task: CrewAI 任务对象
        """
        # 处理上下文任务
        context_list = self._ensure_context_list(context_tasks)
        
        task = Task(
            description=dedent(f"""
                基于现有大纲和已完成章节，智能扩充剧情大纲。

                **现有大纲与企划书**：
                {current_outline}

                **已完成章节摘要**：
                {completed_chapters_summary}

                **任务要求**：
                **重要**：如果企划书中已经包含章节名称、章节规划或章节大纲要求，请：
                1. **优先使用企划书中的章节名称**，保持名称一致
                2. **参照企划书中的章节大纲要求**进行扩充和细化
                3. 在企划书已有章节框架的基础上，补充详细的剧情细节
                4. 如果企划书指定了章节数量或章节分布，请严格遵循

                1. 生成 {num_chapters} 个章节的剧情规划（包含起始章节）。
                2. **按段组织大纲**：每 {chapters_per_block} 章生成一段大纲。
                   - 每段覆盖一个章节范围，标题应体现该范围的核心剧情。
                3. **详细的大纲内容要求**：
                   - **章节划分**：明确每一章的核心事件。
                   - **字数指导**：为每一段或每一章提供预估字数范围。
                   - **爆点/钩子**：每一段必须设计至少一个吸引读者的钩子（Hook）或爆点。
                   - **剧情线推进**：
                     - **主线**：明确推动主线剧情发展的具体事件。
                     - **副线**：适当穿插副线情节，丰富故事层次。
                     - **暗线**：埋设伏笔或推进暗线，为后续高潮做铺垫。
                4. 确保新生成的剧情与前文逻辑连贯，伏笔得到回收。
                5. **必须以纯 JSON 数组格式输出**，不要包含 Markdown 代码块标记。
                   **非常重要：JSON 键名必须使用双引号，不能使用单引号。**

                   **输出格式**（支持两种字段名，推荐使用 start_chapter/end_chapter）：
                   [
                     {{
                       "start_chapter": 10,
                       "end_chapter": 14,
                       "title": "章节范围标题",
                       "summary": "这几章的详细剧情走向，包含主线、副线、暗线设计，爆点/钩子，以及字数指导..."
                     }},
                     {{
                       "start_chapter": 15,
                       "end_chapter": 19,
                       "title": "下一段标题",
                       "summary": "后续剧情发展..."
                     }}
                   ]

                   或兼容格式（chapter_start/chapter_end 也可接受）：
                   [{{"chapter_start": 10, "chapter_end": 14, "title": "...", "summary": "..."}}]
            """),
            agent=agent,
            context=context_list if context_list else None,
            expected_output=f"一份包含 {num_chapters} 章的详细剧情大纲（JSON格式），包含章节划分、字数指导、爆点/钩子及剧情线设计。"
        )
        return task

    def batch_chapter_writing_task(self, agent, outline_segment, previous_chapter_content):
        return Task(
            description=dedent(f"""
                基于指定的大纲片段，批量撰写小说章节。
                
                大纲片段：
                {outline_segment}
                
                上一章内容（用于衔接）：
                {previous_chapter_content[-2000:]} (节选)
                
                任务要求：
                1. 严格按照大纲片段的剧情进行撰写。
                2. 确保与上一章的结尾无缝衔接，语气和风格保持一致。
                3. 批量生成大纲中包含的所有章节。
                4. 每章字数控制在 2500-3000 字。
                5. 使用 Markdown 格式，章节之间用 ## 标题 分隔。
            """),
            agent=agent,
            expected_output="包含多个章节的连贯小说正文。"
        )

    def quality_assessment_task(self, agent, generated_content, original_outline):
        return Task(
            description=dedent(f"""
                对新生成的章节进行质量评估。
                
                生成内容：
                {generated_content}
                
                原始大纲要求：
                {original_outline}
                
                任务要求：
                1. 评估剧情是否偏离大纲。
                2. 检查逻辑连贯性和人物行为一致性。
                3. 给出具体的改进建议。
                4. 给出一个 0-100 的质量评分。
            """),
            agent=agent,
            expected_output="一份包含评分、问题分析和改进建议的质量评估报告。"
        )

    # ==================== 企划书 Crew Tasks ====================
    
    def market_analysis_task(self, agent, topic):
        return Task(
            description=dedent(f"""
                分析主题 '{topic}' 的市场潜力和读者定位。
                
                任务要求：
                1. 评估该创意是否符合当前网文市场热点。
                2. 分析潜在读者群体（年龄、性别、阅读偏好）。
                3. 识别类似题材的成功案例。
                4. 提出市场定位建议（如"男频都市爽文"、"女频古言甜宠"等）。
                5. 预测爆款潜力（高/中/低）并说明理由。
                
                输出格式：
                - 市场热度评估
                - 目标读者画像
                - 对标作品
                - 市场定位建议
                - 爆款潜力预测
            """),
            agent=agent,
            expected_output="一份详细的市场分析报告，包含读者定位和爆款潜力评估。"
        )

    def proposal_writing_task(self, agent, context_tasks):
        context_list = self._ensure_context_list(context_tasks)
        
        return Task(
            description=dedent(f"""
                基于上下文中的分析结果，撰写完整的《小说企划书》。
                
                **重要**：请仔细阅读上下文中的市场分析、核心创意、剧情大纲、角色设计等内容。
                
                任务要求：
                1. **书名**：吸引眼球，体现核心卖点。
                2. **Logline（一句话梗概）**：30字以内，概括核心冲突和看点。
                3. **世界观设定**：详细的背景、规则、特色系统。
                4. **主要角色**：主角和核心配角的人物小传。
                5. **核心冲突**：明确主角的目标、障碍和赌注。
                6. **市场定位**：目标读者、对标作品、差异化卖点。
                7. **章节规划建议**：根据目标字数给出章节数和每章字数建议。
                
                **重要限制**：
                - 企划书总字数控制在 1500-2500 字
                - 突出核心要点，避免冗余描述
                - 保持结构清晰，便于后续团队理解
                
                输出格式：使用 Markdown 格式，清晰分段。
            """),
            agent=agent,
            context=context_list,
            expected_output="一份完整、专业的《小说企划书》（Markdown格式），字数1500-2500字。"
        )

    def naming_review_task(self, agent, context_proposal):
        """
        命名审查任务 - 审查和优化企划书中的所有名称
        
        Args:
            agent: 命名专家 Agent
            context_proposal: 企划书草稿任务（Task 对象）
        """
        context_list = self._ensure_context_list(context_proposal)
        
        return Task(
            description=dedent(f"""
                审查上下文中的企划书草稿，对所有名称进行审查、润色和优化。

                **重要**：请仔细阅读上下文中的企划书内容，识别所有需要审查的名称。

                **审查范围**：
                1. **人名**：主角、配角、反派、NPC等所有角色名称
                2. **地名**：城市、国家、地区、山脉、河流、建筑等地理名称
                3. **物品名**：武器、法宝、丹药、道具等物品名称
                4. **功法/技能名**：修炼功法、武技、法术、技能等名称
                5. **书籍/典籍名**：秘籍、经典、史书等文献名称
                6. **组织/势力名**：门派、宗门、商会、国家等组织名称
                7. **其他专有名词**：特殊概念、系统名称等

                **审查标准**：
                1. **避免AI常用名**：
                   - 人名：避免"云逸"、"墨染"、"雪儿"、"清雅"、"若曦"等常见AI生成名
                   - 地名：避免"云海城"、"天元宗"、"万剑山"等套路化名称
                   - 功法：避免"九转神功"、"无极心法"等过于常见的命名
                2. **符合世界观**：
                   - 古风世界：使用符合古代文化的命名风格
                   - 现代都市：使用现代常见的命名习惯
                   - 奇幻/科幻：根据设定调整命名风格
                3. **有记忆点**：
                   - 名称要有特色，避免过于普通或难以记住
                   - 可以结合角色性格、背景、命运等元素
                4. **文化一致性**：
                   - 同一文化背景下的命名风格要统一
                   - 避免混用不同文化的命名习惯
                5. **避免违和感**：
                   - 名称要与角色身份、地位、背景匹配
                   - 避免过于现代的网络用语或流行梗

                **优化原则**：
                1. **保留优秀名称**：如果名称已经很好，符合要求，可以保留
                2. **修改问题名称**：对于AI常用名、违和名称，必须修改
                3. **提供替代方案**：为每个修改的名称提供1-2个备选方案
                4. **说明修改理由**：简要说明为什么需要修改，新名称的优势

                **输出格式**：
                1. 首先输出优化后的完整企划书（Markdown格式）
                2. 然后输出名称修改清单：
                   ```
                   ## 名称审查报告
                   
                   ### 修改的名称
                   - **原名称**：[类型] 原名称 → **新名称**：新名称
                     修改理由：简要说明
                   
                   ### 保留的名称
                   - [类型] 名称：符合要求，保留
                   
                   ### 新增建议
                   - 如果发现某些重要元素缺少名称，可以建议添加
                   ```

                **重要要求**：
                - 必须输出完整的优化后企划书，不能只输出修改清单
                - 企划书结构、内容、字数保持不变，只修改名称
                - 确保所有修改后的名称在企划书中已更新
            """),
            agent=agent,
            context=context_list,
            expected_output="优化后的完整企划书（Markdown格式）+ 名称审查报告，确保所有名称符合要求且已更新到企划书中。"
        )

    # ==================== 大纲生成 Crew Tasks ====================
    
    def outline_reading_task(self, agent, proposal_content):
        return Task(
            description=dedent(f"""
                仔细阅读并理解企划书，提取核心冲突和关键设定。
                
                **企划书内容**：
                {proposal_content[:2000]}{'...(内容已截断)' if len(proposal_content) > 2000 else ''}
                
                任务要求：
                1. 提取核心冲突：主角的目标、面临的障碍、核心赌注。
                2. 识别关键设定：世界观规则、特殊系统、重要背景。
                3. 列出主要角色：主角和核心配角的关键信息。
                4. 明确故事基调：轻松/严肃、热血/温情等。
                5. 确认目标篇幅和章节规划建议。
                
                输出格式：
                - 核心冲突摘要
                - 关键设定清单
                - 主要角色列表
                - 故事基调
                - 章节规划参考
            """),
            agent=agent,
            expected_output="一份企划书解读报告，为大纲生成提供清晰的指引。"
        )

    def outline_structuring_task(self, agent, context_reading, target_word_count: str = "短篇小说 (1-10万字)"):
        context_list = self._ensure_context_list(context_reading)
        
        return Task(
            description=dedent(f"""
                基于企划书解读，生成全书分章大纲。
                
                **重要**：请仔细阅读上下文中的企划书解读报告。
                
                **目标篇幅**: {target_word_count}
                
                任务要求：
                1. **章节数量**：根据目标篇幅合理规划。
                2. **事件图谱**：明确每章的核心事件和因果关系。
                3. **节奏控制**：合理分配铺垫、发展、高潮、结局篇幅。
                4. **伏笔设计**：标注需要埋下的伏笔和回收点。
                5. **人物弧光**：跟踪主要角色在每章的成长变化。
                
                输出格式（Markdown）：
                ```
                ### 第X章 [章节标题]
                
                **核心事件**：本章发生的主要事件
                **人物动作**：主要角色的行为和反应
                **情感转折**：情绪变化和冲突升级
                **伏笔/回收**：需要埋下或回收的伏笔
                **与前后章衔接**：如何承上启下
                ```
                
                **关键要求**：
                - 确保每章有明确的目标和进展
                - 避免平铺直叙，设置悬念和转折
                - 保持逻辑严密，因果关系清晰
            """),
            agent=agent,
            context=context_list,
            expected_output=f"完整的分章大纲（Markdown格式），章节数量符合{target_word_count}的要求。"
        )

    def outline_naming_review_task(self, agent, context_outline, proposal_content=""):
        """
        大纲命名审查任务 - 审查和优化大纲中的所有名称
        
        Args:
            agent: 命名专家 Agent
            context_outline: 大纲任务（Task 对象）
            proposal_content: 企划书内容（可选，用于参考世界观）
        """
        context_list = self._ensure_context_list(context_outline)
        
        return Task(
            description=dedent(f"""
                审查上下文中的分章大纲，对所有名称进行审查、润色和优化。

                **重要**：请仔细阅读上下文中的分章大纲内容，识别所有需要审查的名称。

                **企划书参考**（世界观设定）：
                {proposal_content[:1000] if proposal_content else '（无企划书）'}

                **审查范围**：
                1. **章节标题中的名称**：章节标题中提到的地点、人物、物品等
                2. **人物名称**：大纲中提到的所有角色名称（主角、配角、反派等）
                3. **地名**：城市、国家、地区、山脉、河流、建筑等地理名称
                4. **物品名**：武器、法宝、丹药、道具等物品名称
                5. **功法/技能名**：修炼功法、武技、法术、技能等名称
                6. **书籍/典籍名**：秘籍、经典、史书等文献名称
                7. **组织/势力名**：门派、宗门、商会、国家等组织名称
                8. **其他专有名词**：特殊概念、系统名称等

                **审查标准**：
                1. **避免AI常用名**：
                   - 人名：避免"云逸"、"墨染"、"雪儿"、"清雅"、"若曦"、"林xx"、"傅xx"等常见AI生成名
                   - 地名：避免"云海城"、"天元宗"、"万剑山"等套路化名称
                   - 功法：避免"九转神功"、"无极心法"等过于常见的命名
                2. **符合世界观**：
                   - 参考企划书中的世界观设定
                   - 古风世界：使用符合古代文化的命名风格
                   - 现代都市：使用现代常见的命名习惯
                   - 奇幻/科幻：根据设定调整命名风格
                3. **有记忆点**：
                   - 名称要有特色，避免过于普通或难以记住
                   - 可以结合角色性格、背景、命运等元素
                4. **文化一致性**：
                   - 同一文化背景下的命名风格要统一
                   - 避免混用不同文化的命名习惯
                5. **避免违和感**：
                   - 名称要与角色身份、地位、背景匹配
                   - 避免过于现代的网络用语或流行梗

                **优化原则**：
                1. **保留优秀名称**：如果名称已经很好，符合要求，可以保留
                2. **修改问题名称**：对于AI常用名、违和名称，必须修改
                3. **提供替代方案**：为每个修改的名称提供1-2个备选方案
                4. **说明修改理由**：简要说明为什么需要修改，新名称的优势

                **输出格式**：
                1. 首先输出优化后的完整分章大纲（Markdown格式）
                2. 然后输出名称修改清单：
                   ```
                   ## 大纲名称审查报告
                   
                   ### 修改的名称
                   - **原名称**：[类型] 原名称 → **新名称**：新名称
                     修改理由：简要说明
                     出现位置：第X章 [章节标题]
                   
                   ### 保留的名称
                   - [类型] 名称：符合要求，保留
                   
                   ### 新增建议
                   - 如果发现某些重要元素缺少名称，可以建议添加
                   ```

                **重要要求**：
                - 必须输出完整的优化后大纲，不能只输出修改清单
                - 大纲结构、内容、章节数量保持不变，只修改名称
                - 确保所有修改后的名称在大纲中已更新
                - 章节标题中的名称也要审查和优化
            """),
            agent=agent,
            context=context_list,
            expected_output="优化后的完整分章大纲（Markdown格式）+ 名称审查报告，确保所有名称符合要求且已更新到大纲中。"
        )

    # ==================== 细纲生成 Crew Tasks ====================
    
    def detailed_outline_task(self, agent, chapter_range, outline_content, proposal_content="", custom_prompt=""):
        start_chapter, end_chapter = chapter_range
        
        # 构建自定义prompt部分
        custom_prompt_section = ""
        if custom_prompt and custom_prompt.strip():
            custom_prompt_section = f"""
                
                **💡 用户自定义指导**（请特别注意并遵循）：
                {custom_prompt.strip()}
                
                以上是用户提供的额外指导，请在生成细纲时充分考虑并遵循这些要求。
                """
        
        return Task(
            description=dedent(f"""
                为第 {start_chapter}-{end_chapter} 章生成详细细纲（场景节拍表）。
                
                **章节大纲**：
                {outline_content[:1500]}{'...(内容已截断)' if len(outline_content) > 1500 else ''}
                
                **企划书参考**（必须严格遵循）：
                {proposal_content[:3000] if proposal_content else '（无企划书）'}{custom_prompt_section}
                
                **极其重要 - 企划书约束**：
                1. **世界观设定**：必须严格遵循企划书中的世界观、规则、系统设定，不得偏离或添加企划书中没有的设定。
                2. **人物设定**：所有人物（主角、配角、反派等）的性格、能力、背景必须与企划书中的描述一致，不得改变或添加新的人物设定。
                3. **核心冲突**：必须围绕企划书中明确的核心冲突展开，不得偏离主题或引入与核心冲突无关的新冲突。
                4. **故事基调**：必须保持与企划书一致的故事基调（轻松/严肃、热血/温情等）。
                5. **禁止添加新元素**：不得添加企划书中没有的世界观元素、人物、组织、物品等，除非是细纲中必要的细节补充。
                6. **忠实大纲**：在遵循企划书的前提下，严格按照章节大纲的剧情走向进行细化，不得改变大纲的核心事件和剧情逻辑。
                
                任务要求：
                1. **场景拆分**：将每章拆分为 3-5 个具体场景。
                2. **节拍设计**：为每个场景设计 5-10 个节拍（Beats）。
                3. **感官细节**：标注视觉、听觉、嗅觉等具体细节提示。
                4. **情绪节点**：明确每个节拍的情绪色彩（紧张、愉悦、悲伤等）。
                5. **对话/动作指引**：提供关键对话的方向或动作描述建议。
                
                输出格式（Markdown）：
                ```
                ### 第X章 [标题] - 细纲
                
                **场景1：[场景名称]**
                - 地点/时间：具体位置和时间
                - 节拍1：[具体动作/对话]（情绪：紧张）
                - 节拍2：...
                - 感官提示：[视觉、听觉、嗅觉细节]
                
                **场景2：...**
                ```
                
                **关键要求**：
                - 细纲要足够详细，写手可以直接依据撰写
                - **必须严格遵循企划书的世界观、人物设定、核心冲突，不得偏离**
                - 保持与大纲的剧情逻辑一致
                - 预留写手发挥空间，但不要偏离企划书设定
            """),
            agent=agent,
            expected_output=f"第{start_chapter}-{end_chapter}章的详细细纲（Markdown格式），包含场景拆分和节拍设计，严格遵循企划书设定。"
        )

    # ==================== 正文撰写 Crew Tasks ====================
    
    def chapter_summarize_task(self, agent, chapter_content, chapter_number):
        return Task(
            description=dedent(f"""
                将第 {chapter_number} 章的内容压缩成简洁摘要。
                
                **章节内容**（节选）：
                {chapter_content[:1000]}{'...(内容已截断)' if len(chapter_content) > 1000 else ''}
                
                任务要求：
                1. **字数控制**：摘要控制在 150-200 字。
                2. **提取关键信息**：
                   - 核心事件：发生了什么
                   - 人物动作：主要角色做了什么
                   - 情节进展：剧情推进到哪里
                   - 伏笔/回收：埋下或回收了什么伏笔
                   - 情感变化：角色情绪的转变
                3. **简洁明了**：避免细节描写，聚焦核心进展。
                4. **便于衔接**：为后续章节提供清晰的上下文。
                
                输出格式：
                ```
                ## 第{chapter_number}章摘要
                
                [150-200字的简洁摘要，包含核心事件、人物动作、剧情进展、伏笔、情感变化]
                ```
            """),
            agent=agent,
            expected_output=f"第{chapter_number}章的简洁摘要（150-200字），为后续章节提供上下文。"
        )
