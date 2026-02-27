# inbox（随手记）

把你临时想到的点直接发我，我会先落到这里（必要时按日期加条目），然后在每晚摘要时整理进对应的定稿文件。

---

## 2026-02-21
- 方案4落地：建立 notes/、memory/、inbox 入口，创建 car/lyrics/lotto 初稿文件。

## 2026-02-26
- 用户反馈：希望我能根据 Telegram 过往约定持续执行，避免“忘事/没做”。
- 已落实：夜间摘要 cron + 周二/五 Lotto Max 选号 cron。

## 2026-02-27
- Ubuntu 新装机必备软件清单（用于跑 OpenClaw）：
  - sudo apt update
  - sudo apt install -y git curl wget unzip p7zip-full htop python3 python3-pip build-essential cmake
  - （可选）Chrome/Chromium、Timeshift、VS Code、openssh-server（如需远程）
- 从 Windows-OpenClaw 迁移任务到 Linux：
  - 已完成环境补齐与验证：p7zip-full、htop、python3-pip、ffmpeg、jq、ripgrep、fd-find、tmux、tree、git-lfs
  - 追加待办：做“开机后一键自检脚本”（OpenClaw 状态 + 工具链 + NTFS 挂载）
