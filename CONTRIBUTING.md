# 贡献指南

欢迎通过 Issue 和 Pull Request 参与本项目。

## 如何参与

1. **提 Issue**：Bug 报告、功能建议、文档纠错均可，请尽量说明复现步骤或使用场景。
2. **Fork 并克隆**：Fork 本仓库后克隆到本地，在**新分支**上开发（如 `fix/xxx`、`feat/xxx`）。
3. **发起 PR**：完成修改后向 `main` 发起 Pull Request，简要描述改动与原因。维护者会 review 后合并。

## 约定

- **架构**：数据访问放在 `database.py`，业务逻辑放在 `services/`，页面只做 UI，参考 [CLAUDE.md](CLAUDE.md)。
- **数据库**：所有表统一使用 `stories.db`，结构变更请新增 `migrations/` 脚本，勿直接改表。
- **提交信息**：使用中文，能概括本次改动即可。
- **大改动**：新功能、多模块修改、数据库或 UI 变更，建议在 [operateLog.md](operateLog.md) 中记录一行变更摘要。

## 本地开发

```bash
git clone https://github.com/rackyun/story_idea_generator.git
cd story_idea_generator
pip install -r requirements.txt
cp config.example.yaml config.yaml   # 编辑 config.yaml 填入 API
streamlit run app.py
```

感谢你的贡献。
