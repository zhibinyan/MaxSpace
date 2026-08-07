#!/usr/bin/env bash
# 用法: ./git.sh "提交说明"
# 或:   bash git.sh "提交说明"
#
# 流程: fetch → 若有远程更新则 pull → 无冲突则 add + commit + push
# 有冲突时打印冲突文件并退出（非 0）

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

MSG="${1:-}"
if [[ -z "$MSG" ]]; then
  echo "用法: $0 \"提交说明\"" >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "错误: 当前目录不是 git 仓库" >&2
  exit 1
fi

list_conflict_files() {
  git diff --name-only --diff-filter=U 2>/dev/null || true
  # merge/rebase 过程中也可能标记为 unmerged
  git ls-files -u 2>/dev/null | awk '{print $4}' | sort -u || true
}

abort_if_conflicts() {
  local files
  files="$(list_conflict_files | sort -u)"
  if [[ -n "$files" ]]; then
    echo "错误: 存在冲突，已中止提交。冲突文件:" >&2
    echo "$files" | while IFS= read -r f; do
      [[ -n "$f" ]] && echo "  - $f" >&2
    done
    exit 2
  fi
}

# 已有未完成的 merge/rebase
if [[ -f .git/MERGE_HEAD ]] || [[ -d .git/rebase-merge ]] || [[ -d .git/rebase-apply ]]; then
  echo "错误: 仓库处于 merge/rebase 进行中，请先处理完再执行。" >&2
  abort_if_conflicts
  exit 2
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$BRANCH" == "HEAD" ]]; then
  echo "错误: 当前处于 detached HEAD，无法自动提交" >&2
  exit 1
fi

echo "==> fetch origin ..."
git fetch origin

UPSTREAM="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
if [[ -z "$UPSTREAM" ]]; then
  echo "警告: 当前分支未设置上游。尝试使用 origin/$BRANCH"
  if git show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
    UPSTREAM="origin/$BRANCH"
  else
    echo "错误: 找不到远程跟踪分支 origin/$BRANCH，无法检查更新" >&2
    exit 1
  fi
fi

LOCAL="$(git rev-parse HEAD)"
REMOTE="$(git rev-parse "$UPSTREAM")"
BASE="$(git merge-base HEAD "$UPSTREAM")"

NEED_PULL=0
if [[ "$LOCAL" != "$REMOTE" ]]; then
  if [[ "$LOCAL" == "$BASE" ]]; then
    # 本地落后远程
    NEED_PULL=1
  elif [[ "$REMOTE" == "$BASE" ]]; then
    # 仅本地超前，无需 pull
    NEED_PULL=0
  else
    # 已分叉：仍尝试 pull（merge），若冲突则报错
    NEED_PULL=1
  fi
fi

if [[ "$NEED_PULL" -eq 1 ]]; then
  echo "==> 检测到远程有更新，正在 pull ($UPSTREAM) ..."
  set +e
  git pull --no-edit
  PULL_STATUS=$?
  set -e

  CONFLICTS="$(list_conflict_files | sort -u)"
  if [[ -n "$CONFLICTS" ]]; then
    echo "错误: pull 产生冲突，已中止提交。冲突文件:" >&2
    echo "$CONFLICTS" | while IFS= read -r f; do
      [[ -n "$f" ]] && echo "  - $f" >&2
    done
    exit 2
  fi

  if [[ "$PULL_STATUS" -ne 0 ]]; then
    echo "错误: git pull 失败（退出码 $PULL_STATUS）" >&2
    exit "$PULL_STATUS"
  fi
  echo "==> pull 完成，无冲突"
else
  echo "==> 远程无新提交，跳过 pull"
fi

abort_if_conflicts

# 无变更则不必提交
if git diff --quiet && git diff --cached --quiet && [[ -z "$(git ls-files --others --exclude-standard)" ]]; then
  echo "==> 工作区干净，无需提交"
  exit 0
fi

echo "==> git add -A"
git add -A

abort_if_conflicts

echo "==> git commit"
git commit -m "$MSG"

echo "==> git push"
if git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
  git push
else
  git push -u origin "$BRANCH"
fi

echo "==> 提交并推送成功"
git status -sb
