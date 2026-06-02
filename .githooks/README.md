# Git Hooks 说明

启用后，**每次 `git commit` 成功都会自动发钉钉**，概要来自 commit message。

## 一次性启用（本仓库）

```bash
git config core.hooksPath .githooks
```

Windows / Unix 均使用 `.githooks/post-commit`（Git Bash 下 sh 脚本）。

## 手动发送（最近一次 commit）

```bash
python .cursor/skills/ifrit-project-dev/scripts/send_dingtalk_notify.py --from-last-commit
```

预览不发送：加 `--dry-run`。

## 前提

项目根目录 `.env` 已配置 `DINGTALK_ACCESS_TOKEN`。
