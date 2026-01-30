# 小说灵感与创作助手

基于 Streamlit + CrewAI 的 AI 小说创作辅助工具，支持灵感生成、企划书编写、完整小说创作与长篇小说管理。

---

## 功能概览

### 灵感生成器（基础版）
- 随机生成小说要素（题材、主角、场景、冲突等）
- AI 扩写生成角色卡与故事梗概
- 支持下载为 Markdown

### 智能写作团队（CrewAI）
- 多 Agent 协作生成企划书
- 多轮脑暴与迭代优化
- 从企划书一键生成完整小说

### 历史与小说管理
- **历史管理**：SQLite 存储，搜索、筛选、分页、批量操作
- **长篇小说**：章节管理、版本快照、对比与恢复
- **统计与导出**：字数统计、写作时间线、Markdown / TXT / EPUB / PDF 导出

---

## 环境要求

- Python 3.9+
- 兼容 OpenAI API 的 LLM 服务（用于灵感扩写与 CrewAI）

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/rackyun/story_idea_generator.git
cd story_idea_generator
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

**可选依赖**（按需安装）：
- `ebooklib`：EPUB 导出
- `weasyprint`：PDF 导出
- `plotly`：统计图表

### 3. 配置 LLM

复制示例配置并填入你的 API 信息：

```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`，填写 `base_url`、`api_key`、`model`。`config.yaml` 已加入 `.gitignore`，不会被提交到仓库。

### 4. 启动应用

```bash
streamlit run app.py
```

或使用脚本：

```bash
chmod +x run.sh && ./run.sh
```

浏览器访问终端提示的地址（默认 `http://localhost:8501`）。

---

## 页面导航

| 页面       | 说明                         |
|------------|------------------------------|
| 主页       | 灵感生成器 + 智能写作团队    |
| 历史管理   | 记录列表、搜索、筛选、批量操作 |
| 历史详情   | 单条记录查看与编辑           |
| 小说管理   | 章节、版本、统计、导出       |
| 章节编辑   | 单章内容编辑                 |
| 版本对比   | 不同版本差异对比             |

---

## 项目结构

```
story_idea_generator/
├── app.py                 # Streamlit 主入口
├── config.example.yaml    # 配置示例，复制为 config.yaml 后填写
├── database.py            # 数据库与各 Manager（stories / chapters / versions / outline 等）
├── logic.py               # 随机要素、LLM 封装、历史管理
├── crew_agents.py         # CrewAI Agent 定义
├── crew_tasks.py          # CrewAI 任务流
├── requirements.txt
├── run.sh                 # 启动脚本
│
├── pages/                 # Streamlit 多页
│   ├── 1_📚_历史管理.py
│   ├── 2_📖_历史详情.py
│   ├── 3_📚_小说管理.py
│   ├── 4_✏️_章节编辑.py
│   └── 5_🔄_版本对比.py
│
├── services/              # 业务服务层
│   ├── story_service.py
│   ├── novel_service.py
│   ├── chapter_service.py
│   ├── writing_service.py
│   ├── chapter_writing_service.py
│   ├── outline_service.py
│   ├── detailed_outline_service.py
│   ├── proposal_service.py
│   └── crew_orchestration_service.py
│
├── utils/
│   ├── export.py          # 多格式导出
│   ├── stats.py           # 字数与统计
│   ├── version_diff.py    # 版本对比
│   └── novel_length_config.py
│
├── migrations/            # 数据库迁移
│   ├── migrate_json_to_db.py
│   ├── migrate_split_novels.py
│   ├── migrate_add_outlines.py
│   └── migrate_outline_to_segments.py
│
└── CLAUDE.md              # 开发与架构说明（面向 AI 助手）
```

首次运行时会自动创建 SQLite 数据库 `stories.db`（该文件已在 `.gitignore` 中，不会提交）。

---

## 技术栈

| 类别     | 技术 |
|----------|------|
| 前端     | Streamlit |
| 数据库   | SQLite |
| AI / 协作 | OpenAI API、CrewAI |
| 导出     | Markdown、ebooklib（EPUB）、weasyprint（PDF） |
| 可视化   | Plotly |

---

## 配置与注意事项

1. **API 安全**：`config.yaml` 已加入 `.gitignore`，请基于 `config.example.yaml` 复制并填写，勿提交真实密钥。
2. **数据库**：数据存放在 `stories.db`，请自行定期备份。
3. **从旧版迁移**：若曾使用 JSON 历史，可执行 `python migrations/migrate_json_to_db.py` 等脚本进行迁移。

---

## 开发与贡献

- 架构与数据库说明见 [CLAUDE.md](CLAUDE.md)。
- 参与方式与约定见 [CONTRIBUTING.md](CONTRIBUTING.md)。
- 欢迎提 Issue 与 Pull Request。

---

## 许可证

本项目采用 [MIT License](LICENSE)，可自由使用、修改与分发。详见仓库内 `LICENSE` 文件。

---

## 更新日志

### v2.0.0
- SQLite 存储与历史管理（搜索、筛选、分页）
- 长篇小说章节管理、版本快照与对比
- 多格式导出（Markdown / TXT / EPUB / PDF）
- 统计与写作时间线

### v1.0.0
- 灵感生成器与 CrewAI 智能写作团队
- JSON 历史记录
