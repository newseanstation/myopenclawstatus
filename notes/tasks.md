# tasks（任务清单）

> 目的：把“口头交代”变成可追踪的待办，避免遗忘。

## 进行中 / 待办
- [ ] **每晚 00:00（America/Toronto）自动摘要/归档**：仅处理 `notes/inbox.md` + 当天新增对话（需要先被摘到 inbox）。
- [x] **歌词自动推送 cron 重建（周一/三/五 05:00 America/Toronto）**：按 `notes/lyrics-rules.md` 执行 A/B/C 三类任务，支持“照片模式”三语歌词。  
  - jobs: `lyrics-mon-0500` / `lyrics-wed-0500` / `lyrics-fri-0500`（channel: telegram, to: 5913602407）
- [x] **Linux 开机后一键自检脚本**：30秒检查 OpenClaw 状态、常用工具、外接 NTFS 挂载状态（从 Windows-OpenClaw 迁移后的持续维护项）。  
  - script: `scripts/openclaw-selfcheck.sh`
- [x] **每日市场与国际新闻简报（10:00 America/Toronto）**：
  - 跟踪美股预期走势与MP（MP Materials）盘前及相关消息
  - 汇总当日世界重大新闻3-5条（每条300-500字）
  - cron job: `market-world-brief-0700`
- [x] **Lotto Max 选号**：每周二/五 10:00（America/Toronto）给 3 注；选号前查看近30期热冷分布（lotteryextreme）。
  - cron job: `lotto-max-1000`

## 已完成
- [x] 建立 `notes/`、`memory/`、`notes/inbox.md` 结构
- [x] 创建并维护：`notes/car-buying.md`、`notes/lyrics-rules.md`
- [x] **Linux OpenClaw 环境补齐（由 Windows-OpenClaw 任务迁移）**：
  - 基础：`git curl wget unzip p7zip-full htop python3 python3-pip build-essential cmake ffmpeg rsync`
  - 增强：`jq ripgrep fd-find tmux tree git-lfs`
  - 验证通过：`7z / htop / pip3 / ffmpeg / jq / rg / fdfind / tmux / tree / git-lfs`
