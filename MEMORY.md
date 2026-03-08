# MEMORY.md

## Preferences / Identity
- Assistant name: **k23bot** (user said “k23bot is ok”).
- 信息管理偏好：采用**方案4（文件归档 + 自动摘要）**。
  - notes：中文为主，必要时加英文小节。
  - 自动摘要：**每晚一次**。
- 用户偏好：自动推送歌词任务——每周一/三/五 **早上5点（America/Toronto）**。
  - A（周一）：天气与季节；关键词参考 <https://www.mulanci.org/>；中文歌词；约4分钟；末尾加“@远方的歌”。
  - B（周三）：男女爱情；关键词参考 <https://www.mulanci.org/>；可写感官/器官但用比喻不直白；中文歌词；约4分钟；末尾加“@远方的歌”。
  - C（周五）：风景与人文地理；关键词参考 <https://www.chinawriter.com.cn/404015/404018/>；中文歌词；约4分钟；末尾加“@远方的歌”。
  - 每次输出都包含：风格关键词 / ≤1000英文字符的音乐风格描述 / 详细元素要求（旋律、伴奏、节奏、人声、混音建议）。
  - “照片模式”另算：用户发真实相片时，再写中/英/日歌词。

## ClawHub
- clawhub 可用；常用命令：`search` / `install` / `update --all`。

## Car shopping (current)
- Looking for **Subaru Crosstrek** around **$31–32k**, **<50,000 km**, **no-accident preferred**.

## English teaching video script preference
- Fixed length: **15 seconds**.
- Roles: **1 teacher + 2 children**.
- Keep concise: **2–3 short sentences per script**.
- Include brief **scene description** matching the sentence.
- Remove any "Japan" setting/content from these scripts.

## OpenClaw setup notes
- Memory search (embeddings) configured for **local** use (no external OpenAI/Google keys):
  - `agents.defaults.memorySearch.provider = "local"`
  - `agents.defaults.memorySearch.fallback = "none"` (avoid remote fallback failures)
  - Local model observed: `hf:ggml-org/embeddinggemma-300M-GGUF/embeddinggemma-300M-Q8_0.gguf`
  - Commands: `openclaw memory index` / `openclaw memory status` / `openclaw memory search "..."`
  - Windows prerequisite: `cmake` must be installed and on PATH (VS Build Tools CMake is OK; may need to add its bin dir to PATH).
  - On this machine, CMake path (VS Build Tools): `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin`
- Dashboard chat can show `disconnected (1008): unauthorized: gateway token missing` when the browser has not saved (or has had cleared) the gateway token.
- User had CCleaner/Kamo privacy tool installed; likely cleared/blocked browser storage, causing token to disappear on restart. User deleted Kamo.
