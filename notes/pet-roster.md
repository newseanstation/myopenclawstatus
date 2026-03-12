# 宠物总表（状态舱可点击打开）

你可以在这里手动维护“宠物名称/emoji/职责/对应设定文件”。

## 当前宠物

- 🦞 k23bot（总管）
  - 职责：总协调与任务调度
  - 设定文件：`notes/tasks.md`

- 🤓 茶几新闻社
  - 职责：方边特刊新闻快报与PDF
  - 设定文件：`notes/fangbian-template.md`

- 🐶 幸运大师
  - 职责：Lotto选号与复盘
  - 设定文件：`notes/lotto-rules.md`

- 🦁 冯导
  - 职责：英语短句脚本
  - 设定文件：`notes/english-lesson-log.md`

- 🐒 冯工
  - 职责：状态舱与系统运维
  - 设定文件：`openclaw_lobster_monitor.py`

## 新增宠物（手动）

按下面模板追加：

- 😀 名称
  - 职责：...
  - 设定文件：`...`

> 备注：当前状态舱里“点击宠物打开设定文件”的映射写在 `openclaw_lobster_monitor.py` 的 `self.pet_map`。新增宠物后，如需可点击打开，请同步让我更新映射。
