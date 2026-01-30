#!/usr/bin/env bash
# 使用 BFG 从 Git 历史中彻底删除 config.yaml（含 API Key）
# 使用前请先安装 BFG 或下载 JAR，见下方说明。

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# 1. 定位 BFG
BFG_CMD=""
if command -v bfg &>/dev/null; then
  BFG_CMD="bfg"
elif [ -f "$REPO_ROOT/bfg.jar" ]; then
  BFG_CMD="java -jar $REPO_ROOT/bfg.jar"
else
  echo "未找到 BFG。请任选一种方式："
  echo "  A) 安装: brew install bfg"
  echo "  B) 下载 JAR 到项目根目录:"
  echo "     https://github.com/rtyley/bfg-repo-cleaner/releases"
  echo "     下载 bfg-1.15.0.jar 并重命名为 bfg.jar 放在 $REPO_ROOT"
  exit 1
fi

# 2. 从历史中删除 config.yaml
echo "正在从历史中删除 config.yaml ..."
$BFG_CMD --delete-files config.yaml

# 3. 清理 reflog 并 GC
echo "正在执行 git reflog expire 与 gc ..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo "完成。config.yaml 已从所有历史提交中移除。"
echo "本地 config.yaml 若存在会保留；请勿再提交。可用 git log -p -- config.yaml 自检。"
