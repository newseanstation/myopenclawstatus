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
- 追加长期任务（从旧会话确认）：
  - 每周一/三/五 05:00（America/Toronto）自动推送歌词生成任务（A天气季节 / B爱情隐喻 / C风景人文），规则已固化在 `notes/lyrics-rules.md`。
  - 包含“照片模式”：收到真实照片时，输出中/英/日三语歌词。
- 新增日报任务（2026-03-07）：
  - 每天07:00（America/Toronto）推送“美股盘前+MP跟踪+世界重大新闻”简报。
  - 要求：世界新闻3-5条，每条300-500字，附来源链接。
- 英语课程脚本规则更新（2026-03-07）：
  - 每日句子在视频开头先完整显示一遍英文字幕；视频结尾再完整显示同一句英文字幕。
