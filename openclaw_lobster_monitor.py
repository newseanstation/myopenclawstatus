#!/usr/bin/env python3
import json
import math
import os
import re
import shutil
import subprocess
import threading
import time
import tkinter as tk
from pathlib import Path
from datetime import datetime
from tkinter import ttk, messagebox

REFRESH_SEC = 10
DEEP_REFRESH_SEC = 120
WORKSPACE_DIR = Path("/home/k23linux/.openclaw/workspace")
SETTINGS_PATH = WORKSPACE_DIR / "notes" / "lobster-settings.json"


def run_cmd(cmd, timeout=25):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (p.stdout or "").strip(), (p.stderr or "").strip(), p.returncode
    except Exception as e:
        return "", str(e), 1


def load_lobster_settings():
    default = {"showPets": True}
    try:
        if SETTINGS_PATH.exists():
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                default.update(data)
    except Exception:
        pass
    return default


def save_lobster_settings(settings: dict):
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def parse_json_loose(text):
    s = (text or "").strip()
    if not s:
        return None
    # 兼容前面混有 doctor warnings 的输出
    for ch in ("{", "["):
        i = s.find(ch)
        if i != -1:
            candidate = s[i:]
            try:
                return json.loads(candidate)
            except Exception:
                continue
    return None


def parse_openclaw_status(text):
    info = {
        "dashboard": "-",
        "update": "-",
        "gateway": "-",
        "agents": "-",
        "sessions": "-",
        "heartbeat": "-",
        "security": "-",
        "channels": "-",
        "tailscale": "-",
    }

    mapping = {
        "dashboard": r"Dashboard\s*│\s*(.+)",
        "update": r"Update\s*│\s*(.+)",
        "gateway": r"Gateway\s*│\s*(.+)",
        "agents": r"Agents\s*│\s*(.+)",
        "sessions": r"Sessions\s*│\s*(.+)",
        "heartbeat": r"Heartbeat\s*│\s*(.+)",
        "channels": r"Channel\s*│\s*(.+)",
        "tailscale": r"Tailscale\s*│\s*(.+)",
    }

    for k, pat in mapping.items():
        m = re.search(pat, text)
        if m:
            info[k] = m.group(1).strip()

    m = re.search(r"Summary:\s*([^\n]+)", text)
    if m:
        info["security"] = m.group(1).strip()

    return info


def parse_security_counts(summary):
    # e.g. "0 critical · 2 warn · 1 info"
    out = {"critical": 0, "warn": 0, "info": 0}
    for k in out:
        m = re.search(rf"(\d+)\s+{k}", summary or "", re.IGNORECASE)
        if m:
            out[k] = int(m.group(1))
    return out


def extract_update_flag(update_text):
    t = (update_text or "").lower()
    if "available" in t:
        return "available"
    if "up to date" in t or "current" in t:
        return "ok"
    return "unknown"


def workspace_stats(workspace_dir: Path):
    file_count = 0
    task_files = 0
    total_bytes = 0
    task_open = 0
    task_done = 0

    task_patterns = ["task", "todo", "issue", "ticket", "job", "需求", "任务"]
    task_exts = {".md", ".txt", ".json", ".yaml", ".yml"}

    try:
        for p in workspace_dir.rglob("*"):
            if not p.is_file():
                continue
            file_count += 1
            try:
                sz = p.stat().st_size
            except Exception:
                sz = 0
            total_bytes += sz

            name_lower = p.name.lower()
            ext = p.suffix.lower()
            is_task_file = ext in task_exts and any(k in name_lower for k in task_patterns)
            if is_task_file:
                task_files += 1
                # Markdown checkbox任务统计
                if ext in {".md", ".txt"}:
                    try:
                        txt = p.read_text(encoding="utf-8", errors="ignore")
                        task_open += len(re.findall(r"(?im)^\s*[-*]\s*\[\s\]", txt))
                        task_done += len(re.findall(r"(?im)^\s*[-*]\s*\[[xX]\]", txt))
                    except Exception:
                        pass
    except Exception:
        pass

    # workspace占所在分区比例
    part_total = part_used = 0
    try:
        du = shutil.disk_usage(str(workspace_dir))
        part_total = du.total
        part_used = du.used
    except Exception:
        pass

    ws_gb = total_bytes / (1024**3)
    part_used_pct = (total_bytes / part_total * 100) if part_total else 0

    return {
        "file_count": file_count,
        "task_files": task_files,
        "task_open": task_open,
        "task_done": task_done,
        "task_total": task_open + task_done,
        "workspace_gb": ws_gb,
        "partition_total_gb": part_total / (1024**3) if part_total else 0,
        "partition_used_gb": part_used / (1024**3) if part_total else 0,
        "workspace_partition_pct": part_used_pct,
    }


def system_stats():
    la1, la5, la15 = os.getloadavg()
    total, used, _ = shutil.disk_usage("/")
    mem_total = 0
    mem_avail = 0
    cpu_count = os.cpu_count() or 1

    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            d = f.read()
        mt = re.search(r"MemTotal:\s+(\d+)", d)
        ma = re.search(r"MemAvailable:\s+(\d+)", d)
        if mt and ma:
            mem_total = int(mt.group(1)) * 1024
            mem_avail = int(ma.group(1)) * 1024
    except Exception:
        pass

    mem_used = max(mem_total - mem_avail, 0)
    mem_pct = (mem_used / mem_total * 100) if mem_total else 0
    disk_pct = used / total * 100 if total else 0

    return {
        "cpu_count": cpu_count,
        "load1": la1,
        "load5": la5,
        "load15": la15,
        "mem_pct": mem_pct,
        "disk_pct": disk_pct,
        "mem_used_gb": mem_used / (1024**3) if mem_total else 0,
        "mem_total_gb": mem_total / (1024**3) if mem_total else 0,
        "disk_used_gb": used / (1024**3),
        "disk_total_gb": total / (1024**3),
    }


def percentile_from_score(score):
    # 经验近似，不宣称官方统计
    return max(1, min(99, int(round(5 + score * 0.9))))


def grade_from_score(score):
    if score >= 92:
        return "S"
    if score >= 82:
        return "A"
    if score >= 70:
        return "B"
    if score >= 58:
        return "C"
    return "D"


def stage_from_score(score):
    if score >= 92:
        return "🦞 龙虾王（Legend）", None
    if score >= 82:
        return "🦞 壮虾（Elite）", 92
    if score >= 70:
        return "🦞 成虾（Strong）", 82
    if score >= 58:
        return "🦐 幼虾（Growing）", 70
    return "🫧 虾苗（Booting）", 58


def classify_manual_warnings(info):
    # 这些通常是配置层面的长期项，自动维护无法直接消除
    sec_text = (info.get("security", "") or "").lower()
    manual = []
    if "warn" in sec_text:
        # 仅凭 summary 无法逐条识别，先给出通用提示
        manual.append("安全告警中含配置项（需人工修改配置）")
    return manual


def alert_level(info, sys_stats):
    sec = parse_security_counts(info.get("security", ""))
    update_flag = extract_update_flag(info.get("update", ""))
    mem = sys_stats.get("mem_pct", 0)
    disk = sys_stats.get("disk_pct", 0)
    manual_items = classify_manual_warnings(info)

    if sec.get("critical", 0) > 0:
        return "red", "存在 critical 安全风险", manual_items
    if sec.get("warn", 0) >= 3 or mem > 92 or disk > 95:
        return "red", "资源或安全告警偏高", manual_items
    if update_flag == "available" or sec.get("warn", 0) > 0 or mem > 82 or disk > 85:
        if manual_items:
            return "yellow", "建议维护：含需人工处理的配置告警", manual_items
        return "yellow", "建议维护：有更新或轻度告警", manual_items
    return "green", "健康：运行状态良好", manual_items


def score_openclaw(info, sys_stats, deep_text):
    reasons = []
    score = 100.0

    # 1) 安全基线 (35)
    sec = parse_security_counts(info.get("security", ""))
    sec_penalty = sec["critical"] * 20 + sec["warn"] * 5 + sec["info"] * 1
    if sec_penalty:
        reasons.append(f"安全项扣分: -{sec_penalty:.0f} (critical={sec['critical']}, warn={sec['warn']}, info={sec['info']})")
    score -= sec_penalty

    # 2) 更新状态 (15)
    uf = extract_update_flag(info.get("update", ""))
    if uf == "available":
        score -= 8
        reasons.append("有可用更新: -8")
    elif uf == "unknown":
        score -= 2
        reasons.append("升级状态未知: -2")

    # 3) 网关/会话可用性 (25)
    g = (info.get("gateway", "") or "").lower()
    if "reachable" not in g:
        score -= 10
        reasons.append("Gateway 未显示 reachable: -10")

    s = (info.get("sessions", "") or "").lower()
    if "active" not in s:
        score -= 8
        reasons.append("未检测到 active sessions: -8")

    # 4) 资源健康 (25)
    mem = sys_stats.get("mem_pct", 0)
    disk = sys_stats.get("disk_pct", 0)
    load_norm = sys_stats.get("load1", 0) / max(sys_stats.get("cpu_count", 1), 1)

    if mem > 92:
        score -= 10
        reasons.append("内存占用过高(>92%): -10")
    elif mem > 82:
        score -= 5
        reasons.append("内存占用偏高(>82%): -5")

    if disk > 95:
        score -= 10
        reasons.append("磁盘占用过高(>95%): -10")
    elif disk > 85:
        score -= 5
        reasons.append("磁盘占用偏高(>85%): -5")

    if load_norm > 1.8:
        score -= 8
        reasons.append("CPU负载偏高(load1/cpu>1.8): -8")
    elif load_norm > 1.2:
        score -= 4
        reasons.append("CPU负载略高(load1/cpu>1.2): -4")

    # 5) 深度探针（官方可比扩展）
    dt = (deep_text or "").lower()
    if dt:
        if "probes" in dt and "skipped" in dt:
            score -= 2
            reasons.append("深度探针未开启: -2")
        if "channels" in dt and "ok" not in dt:
            score -= 3
            reasons.append("部分通道状态非 OK: -3")

    score = max(0, min(100, score))
    grade = grade_from_score(score)
    stage, next_target = stage_from_score(score)
    p = percentile_from_score(score)
    return {
        "score": round(score, 1),
        "grade": grade,
        "stage": stage,
        "next_target": next_target,
        "percentile": p,
        "reasons": reasons if reasons else ["状态优秀：未发现明显扣分项"],
    }


class LobsterMonitor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OpenClaw 小龙虾状态舱")
        self.geometry("1020x680")
        self.configure(bg="#07111f")

        self.angle = 0
        self.openclaw_info = {}
        self.sys = {}
        self.ws = {}
        self.deep_status_text = ""
        self.last_deep_ts = 0
        self.last_maint_ts = 0
        self.maint_running = False
        self.refresh_running = False
        self.rating = {"score": 0, "grade": "D", "percentile": 1, "reasons": []}
        self.settings = load_lobster_settings()
        self.show_pets_var = tk.BooleanVar(value=bool(self.settings.get("showPets", True)))
        self.pet_map = {
            "茶几新闻社": "/home/k23linux/.openclaw/workspace/notes/fangbian-template.md",
            "幸运大师": "/home/k23linux/.openclaw/workspace/notes/lotto-rules.md",
            "冯导": "/home/k23linux/.openclaw/workspace/notes/english-lesson-log.md",
            "冯工": "/home/k23linux/.openclaw/workspace/openclaw_lobster_monitor.py",
            "k23bot（总管）": "/home/k23linux/.openclaw/workspace/notes/tasks.md",
        }
        self.cron_jobs = []
        self.pet_item_paths = {}

        self._build_ui()
        self.after(100, self.animate)
        self.refresh_async()

    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background="#07111f", foreground="#d9f0ff", font=("Segoe UI", 10))
        style.configure("Hdr.TLabel", font=("Segoe UI", 16, "bold"), foreground="#7fe0ff")
        style.configure("Card.TLabelframe", background="#0d1f36", foreground="#9fe8ff")
        style.configure("Card.TLabelframe.Label", background="#0d1f36", foreground="#9fe8ff")
        style.configure("TProgressbar", troughcolor="#122844", background="#4dd6ff")

        top = ttk.Frame(self)
        top.pack(fill="x", padx=12, pady=8)

        self.hdr = ttk.Label(top, text="🦞 OpenClaw 小龙虾状态舱", style="Hdr.TLabel")
        self.hdr.pack(side="left")

        self.time_lbl = ttk.Label(top, text="")
        self.time_lbl.pack(side="right")

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=12, pady=8)

        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True)

        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))

        card0 = ttk.LabelFrame(left, text="小龙虾体量评比（官方可比指标）", style="Card.TLabelframe")
        card0.pack(fill="x", pady=6)
        self.rank_lbl = ttk.Label(card0, text="评级: --", font=("Segoe UI", 14, "bold"))
        self.rank_lbl.pack(anchor="w", padx=8, pady=(8, 0))
        self.stage_lbl = ttk.Label(card0, text="成长阶段: --", font=("Segoe UI", 11))
        self.stage_lbl.pack(anchor="w", padx=8, pady=(2, 0))
        self.rank_bar = ttk.Progressbar(card0, maximum=100)
        self.rank_bar.pack(fill="x", padx=8, pady=(8, 2))
        self.next_bar = ttk.Progressbar(card0, maximum=100)
        self.next_bar.pack(fill="x", padx=8, pady=(2, 2))
        self.rank_detail = ttk.Label(card0, text="分位: --")
        self.rank_detail.pack(anchor="w", padx=8, pady=(0, 6))

        self.alert_canvas = tk.Canvas(card0, width=560, height=36, bg="#0d1f36", highlightthickness=0)
        self.alert_canvas.pack(anchor="w", padx=8, pady=(0, 4))

        ctrl = ttk.Frame(card0)
        ctrl.pack(fill="x", padx=8, pady=(0, 8))
        self.auto_maint_var = tk.BooleanVar(value=False)
        self.auto_maint_chk = ttk.Checkbutton(ctrl, text="告警自动维护", variable=self.auto_maint_var)
        self.auto_maint_chk.pack(side="left")
        self.maint_btn = ttk.Button(ctrl, text="一键维护", command=self.run_maintenance_async)
        self.maint_btn.pack(side="left", padx=(10, 0))
        self.manual_btn = ttk.Button(ctrl, text="手动修复向导", command=self.open_manual_wizard)
        self.manual_btn.pack(side="left", padx=(10, 0))
        self.maint_lbl = ttk.Label(ctrl, text="维护状态: 待命")
        self.maint_lbl.pack(side="left", padx=(10, 0))

        card1 = ttk.LabelFrame(left, text="系统资讯", style="Card.TLabelframe")
        card1.pack(fill="x", pady=6)
        self.system_text = tk.Text(card1, height=8, bg="#0d1f36", fg="#d9f0ff", bd=0)
        self.system_text.pack(fill="both", expand=True, padx=8, pady=8)

        card2 = ttk.LabelFrame(left, text="资源配备", style="Card.TLabelframe")
        card2.pack(fill="x", pady=6)
        self.mem_bar = ttk.Progressbar(card2, maximum=100)
        self.mem_bar.pack(fill="x", padx=8, pady=(12, 4))
        self.mem_lbl = ttk.Label(card2, text="内存")
        self.mem_lbl.pack(anchor="w", padx=8)
        self.disk_bar = ttk.Progressbar(card2, maximum=100)
        self.disk_bar.pack(fill="x", padx=8, pady=(10, 4))
        self.disk_lbl = ttk.Label(card2, text="磁盘")
        self.disk_lbl.pack(anchor="w", padx=8)

        self.ws_bar = ttk.Progressbar(card2, maximum=100)
        self.ws_bar.pack(fill="x", padx=8, pady=(10, 4))
        self.ws_lbl = ttk.Label(card2, text="Workspace")
        self.ws_lbl.pack(anchor="w", padx=8)

        self.ws_task_lbl = ttk.Label(card2, text="任务文件")
        self.ws_task_lbl.pack(anchor="w", padx=8, pady=(0, 10))

        card3 = ttk.LabelFrame(right, text="能力级别 / 升级状态", style="Card.TLabelframe")
        card3.pack(fill="x", pady=6)
        self.capability_text = tk.Text(card3, height=12, bg="#0d1f36", fg="#d9f0ff", bd=0)
        self.capability_text.pack(fill="both", expand=True, padx=8, pady=8)

        card4 = ttk.LabelFrame(right, text="当前任务与动画", style="Card.TLabelframe")
        card4.pack(fill="both", expand=True, pady=6)
        self.task_text = tk.Text(card4, height=7, bg="#0d1f36", fg="#d9f0ff", bd=0)
        self.task_text.pack(fill="x", padx=8, pady=8)

        pet_top = ttk.Frame(card4)
        pet_top.pack(fill="x", padx=8, pady=(0, 4))
        self.pet_toggle_chk = ttk.Checkbutton(pet_top, text="显示宠物栏", variable=self.show_pets_var, command=self.on_toggle_pets)
        self.pet_toggle_chk.pack(side="left")

        self.pet_frame = ttk.LabelFrame(card4, text="宠物栏（点击可打开设定）", style="Card.TLabelframe")
        self.pet_frame.pack(fill="x", padx=8, pady=(0, 8))

        self.pet_list = tk.Listbox(self.pet_frame, height=5, bg="#0d1f36", fg="#d9f0ff", bd=0, font=("Segoe UI Emoji", 12))
        self.pet_list.pack(fill="x", padx=6, pady=(6, 6))
        self.pet_list.bind("<Double-Button-1>", lambda _e: self.open_selected_pet_file())

        pet_btns = ttk.Frame(self.pet_frame)
        pet_btns.pack(fill="x", padx=6, pady=(0, 6))
        ttk.Button(pet_btns, text="打开选中宠物设定", command=self.open_selected_pet_file).pack(side="left")
        ttk.Button(pet_btns, text="一键建立宠物园", command=self.bootstrap_pet_park).pack(side="left", padx=(8, 0))
        ttk.Button(pet_btns, text="打开宠物总表", command=lambda: self.open_local_path("/home/k23linux/.openclaw/workspace/notes/pet-roster.md")).pack(side="left", padx=(8, 0))
        ttk.Button(pet_btns, text="打开任务清单", command=lambda: self.open_local_path("/home/k23linux/.openclaw/workspace/notes/tasks.md")).pack(side="left", padx=(8, 0))

        self.canvas = tk.Canvas(card4, width=420, height=180, bg="#07111f", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.on_toggle_pets()

        footer = ttk.Frame(self)
        footer.pack(pady=(0, 10), fill="x", padx=12)
        self.refresh_btn = ttk.Button(footer, text="立即刷新", command=self.refresh_async)
        self.refresh_btn.pack(side="left")
        self.refresh_state_lbl = ttk.Label(footer, text="刷新状态: 待命")
        self.refresh_state_lbl.pack(side="left", padx=(10, 0))

    def refresh_async(self):
        if self.refresh_running:
            self.refresh_state_lbl.config(text="刷新状态: 进行中（请稍候）")
            return
        self.refresh_running = True
        self.refresh_btn.state(["disabled"])
        self.refresh_state_lbl.config(text="刷新状态: 正在拉取状态...")
        threading.Thread(target=self.refresh_data, daemon=True).start()

    def refresh_data(self):
        try:
            status_text, err, code = run_cmd("openclaw status")
            if code != 0:
                status_text = f"openclaw status 执行失败\n{err}"
            self.openclaw_info = parse_openclaw_status(status_text)

            # 深度探针低频刷新，减少负担
            now = time.time()
            if now - self.last_deep_ts > DEEP_REFRESH_SEC:
                deep_out, _, deep_code = run_cmd("openclaw status --deep", timeout=45)
                if deep_code == 0:
                    self.deep_status_text = deep_out
                    self.last_deep_ts = now

            self.sys = system_stats()
            self.ws = workspace_stats(WORKSPACE_DIR)
            self.rating = score_openclaw(self.openclaw_info, self.sys, self.deep_status_text)

            self.load_cron_jobs_now()

            sess_out, _, _ = run_cmd("openclaw sessions --json")
            task_line = "-"
            if sess_out:
                try:
                    obj = json.loads(sess_out)
                    if isinstance(obj, dict) and "sessions" in obj and obj["sessions"]:
                        latest = obj["sessions"][0]
                        task_line = f"{latest.get('key','?')} | {latest.get('model','?')}"
                except Exception:
                    pass

            self.after(0, lambda: self.render(task_line))
            self.after(0, lambda: self.refresh_state_lbl.config(text=f"刷新状态: 完成 {datetime.now().strftime('%H:%M:%S')}"))
        finally:
            self.refresh_running = False
            self.after(0, lambda: self.refresh_btn.state(["!disabled"]))
            self.after(REFRESH_SEC * 1000, self.refresh_async)

    def render(self, task_line):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_lbl.config(text=now)

        score = self.rating.get("score", 0)
        grade = self.rating.get("grade", "D")
        stage = self.rating.get("stage", "-")
        next_target = self.rating.get("next_target", None)
        pct = self.rating.get("percentile", 1)
        self.rank_lbl.config(text=f"评级: {grade}  |  总分: {score:.1f}/100")
        self.stage_lbl.config(text=f"成长阶段: {stage}")
        self.rank_bar["value"] = score
        if next_target is None:
            self.next_bar["value"] = 100
            gap_text = "已达最高阶段"
        else:
            base = 0
            if next_target == 92:
                base = 82
            elif next_target == 82:
                base = 70
            elif next_target == 70:
                base = 58
            elif next_target == 58:
                base = 0
            progress = (score - base) / max((next_target - base), 1) * 100
            self.next_bar["value"] = max(0, min(100, progress))
            gap_text = f"距离下一阶段还差 {max(0, next_target - score):.1f} 分"
        self.rank_detail.config(text=f"群体分位(估算): P{pct}  ·  {gap_text}  ·  维度: 安全/更新/可用性/资源/深度探针")

        level, level_text, manual_items = alert_level(self.openclaw_info, self.sys)
        self.alert_canvas.delete("all")
        self.alert_canvas.create_text(6, 18, text="告警灯:", anchor="w", fill="#d9f0ff", font=("Segoe UI", 10, "bold"))
        colors_off = {"red": "#5a1b1b", "yellow": "#5a5216", "green": "#164d2a"}
        colors_on = {"red": "#ff4d4f", "yellow": "#ffd666", "green": "#52c41a"}
        order = ["red", "yellow", "green"]
        x0 = 70
        for i, c in enumerate(order):
            fill = colors_on[c] if c == level else colors_off[c]
            self.alert_canvas.create_oval(x0 + i * 34, 8, x0 + 20 + i * 34, 28, fill=fill, outline="#0a0a0a")
        extra = f"（手动项 {len(manual_items)}）" if manual_items else ""
        self.alert_canvas.create_text(186, 18, text=f"{level_text}{extra}", anchor="w", fill="#d9f0ff", font=("Segoe UI", 10))

        # 自动维护开关：黄/红灯触发，30分钟冷却
        if self.auto_maint_var.get() and level in ("yellow", "red") and not self.maint_running:
            if time.time() - self.last_maint_ts > 1800:
                self.run_maintenance_async()

        self.system_text.delete("1.0", "end")
        self.system_text.insert("end", f"Dashboard: {self.openclaw_info.get('dashboard','-')}\n")
        self.system_text.insert("end", f"Gateway: {self.openclaw_info.get('gateway','-')}\n")
        self.system_text.insert("end", f"Sessions: {self.openclaw_info.get('sessions','-')}\n")
        self.system_text.insert("end", f"Heartbeat: {self.openclaw_info.get('heartbeat','-')}\n")
        self.system_text.insert("end", f"Tailscale: {self.openclaw_info.get('tailscale','-')}\n")

        self.mem_bar["value"] = self.sys.get("mem_pct", 0)
        self.disk_bar["value"] = self.sys.get("disk_pct", 0)
        self.ws_bar["value"] = self.ws.get("workspace_partition_pct", 0)

        self.mem_lbl.config(text=f"内存: {self.sys.get('mem_used_gb',0):.1f}/{self.sys.get('mem_total_gb',0):.1f} GB ({self.sys.get('mem_pct',0):.1f}%)")
        self.disk_lbl.config(text=f"磁盘: {self.sys.get('disk_used_gb',0):.1f}/{self.sys.get('disk_total_gb',0):.1f} GB ({self.sys.get('disk_pct',0):.1f}%)")
        self.ws_lbl.config(
            text=(
                f"Workspace体积: {self.ws.get('workspace_gb',0):.3f} GB"
                f"（占分区 {self.ws.get('workspace_partition_pct',0):.3f}%）"
            )
        )
        self.ws_task_lbl.config(
            text=(
                f"任务条目: 总{self.ws.get('task_total',0)}"
                f"（进行中{self.ws.get('task_open',0)} / 已完成{self.ws.get('task_done',0)}）"
                f"  ·  任务文件: {self.ws.get('task_files',0)}  ·  文件总数: {self.ws.get('file_count',0)}"
            )
        )

        self.capability_text.delete("1.0", "end")
        self.capability_text.insert("end", f"升级状态: {self.openclaw_info.get('update','-')}\n")
        self.capability_text.insert("end", f"Agents: {self.openclaw_info.get('agents','-')}\n")
        self.capability_text.insert("end", f"Security: {self.openclaw_info.get('security','-')}\n\n")
        self.capability_text.insert("end", "扣分明细:\n")
        for r in self.rating.get("reasons", [])[:5]:
            self.capability_text.insert("end", f"- {r}\n")
        if manual_items:
            self.capability_text.insert("end", "\n需手动处理:\n")
            for m in manual_items:
                self.capability_text.insert("end", f"- {m}\n")

        self.task_text.delete("1.0", "end")
        self.task_text.insert("end", f"当前活跃任务(估计):\n{task_line}\n\n")
        self.task_text.insert("end", "这只小龙虾正在巡航：\n")
        self.task_text.insert("end", "- 每10秒采样基础状态\n")
        self.task_text.insert("end", "- 每120秒刷新深度探针\n")
        self.task_text.insert("end", "- 生成官方可比体量评级\n")

        self.refresh_pet_roster()

    def on_toggle_pets(self):
        show = bool(self.show_pets_var.get())
        try:
            if show:
                self.pet_frame.pack(fill="x", padx=8, pady=(0, 8))
            else:
                self.pet_frame.pack_forget()
        except Exception:
            pass
        self.settings["showPets"] = show
        save_lobster_settings(self.settings)

    def load_cron_jobs_now(self):
        cron_out, _, _ = run_cmd("openclaw cron list --json", timeout=40)
        if not cron_out:
            self.cron_jobs = []
            return
        obj = parse_json_loose(cron_out)
        self.cron_jobs = obj.get("jobs", []) if isinstance(obj, dict) else []

    def infer_pet(self, job_name: str):
        n = (job_name or "").lower()
        if "lotto" in n:
            return "🐶", "幸运大师", self.pet_map.get("幸运大师")
        if "english" in n or "kids" in n:
            return "🦁", "冯导", self.pet_map.get("冯导")
        if "world-special" in n or "brief" in n or "news" in n:
            return "🤓", "茶几新闻社", self.pet_map.get("茶几新闻社")
        if "lyrics" in n:
            return "🎵", "词作宠物", "/home/k23linux/.openclaw/workspace/notes/lyrics-rules.md"
        if "market" in n:
            return "📈", "市场观察员", "/home/k23linux/.openclaw/workspace/notes/tasks.md"
        return "🧩", "任务宠物", "/home/k23linux/.openclaw/workspace/notes/tasks.md"

    def bootstrap_pet_park(self):
        # 一键基于当前 cron 任务生成/刷新宠物总表
        self.load_cron_jobs_now()
        lines = [
            "# 宠物总表（自动生成）",
            "",
            "- 🦞 k23bot（总管）",
            "  - 职责：总协调与任务调度",
            "  - 设定文件：`notes/tasks.md`",
            "",
            "## 自动识别宠物",
            "",
        ]
        seen = set()
        for j in self.cron_jobs:
            name = j.get("name", "unnamed")
            if name in seen:
                continue
            seen.add(name)
            emo, pet_name, path = self.infer_pet(name)
            lines += [
                f"- {emo} {pet_name}",
                f"  - 任务：`{name}`",
                f"  - 设定文件：`{Path(path).name if path else 'notes/tasks.md'}`",
                "",
            ]

        out = WORKSPACE_DIR / "notes" / "pet-roster.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines), encoding="utf-8")
        self.refresh_pet_roster()
        messagebox.showinfo("完成", "已一键建立/刷新宠物园，并更新 notes/pet-roster.md")

    def refresh_pet_roster(self):
        self.pet_list.delete(0, "end")
        self.pet_item_paths = {}

        # 固定总管
        head = "🦞 k23bot（总管）— 调度与总协调"
        self.pet_list.insert("end", head)
        self.pet_item_paths[head] = self.pet_map.get("k23bot（总管）")

        seen = set()
        count = 0
        for j in self.cron_jobs:
            name = j.get("name", "unnamed")
            if name in seen:
                continue
            seen.add(name)
            emo, pet_name, path = self.infer_pet(name)
            sched = j.get("schedule", {}).get("expr", "") if isinstance(j.get("schedule", {}), dict) else ""
            line = f"{emo} {pet_name} — {name} ({sched})"
            self.pet_list.insert("end", line)
            self.pet_item_paths[line] = path or "/home/k23linux/.openclaw/workspace/notes/tasks.md"
            count += 1

        if count == 0:
            line = "⚠️ 暂未读取到 cron 任务（可点一键建立宠物园重试）"
            self.pet_list.insert("end", line)
            self.pet_item_paths[line] = "/home/k23linux/.openclaw/workspace/notes/tasks.md"

    def open_local_path(self, path):
        p = Path(path)
        if not p.exists():
            messagebox.showwarning("文件不存在", f"未找到：{path}")
            return
        try:
            subprocess.Popen(["xdg-open", str(p)])
        except Exception as e:
            messagebox.showerror("打开失败", str(e))

    def open_selected_pet_file(self):
        sel = self.pet_list.curselection()
        if not sel:
            messagebox.showinfo("提示", "请先选择一个宠物。")
            return
        line = self.pet_list.get(sel[0])
        target = self.pet_item_paths.get(line)
        if not target:
            messagebox.showwarning("未配置", "未找到该宠物的设定文件映射")
            return
        self.open_local_path(target)

    def run_maintenance_async(self):
        if self.maint_running:
            return
        self.maint_running = True
        self.maint_lbl.config(text="维护状态: 执行中...")
        threading.Thread(target=self.perform_maintenance, daemon=True).start()

    def open_manual_wizard(self):
        out, err, code = run_cmd("openclaw security audit", timeout=40)
        txt = out if code == 0 else (err or "无法读取 security audit 输出")

        tips = []
        lower = txt.lower()
        if "trusted proxies" in lower or "reverse proxy headers" in lower:
            tips.append(
                "1) 反向代理信任配置\n"
                "- 问题：gateway.trustedProxies 为空\n"
                "- 处理：若你通过反向代理暴露控制台，在配置里设置 trustedProxies；若仅本机使用可忽略。\n"
            )
        if "denycommands" in lower:
            tips.append(
                "2) denyCommands 精确匹配\n"
                "- 问题：denyCommands 中有无效命令名\n"
                "- 处理：改为精确命令ID（如 canvas.present / canvas.hide / canvas.navigate 等）。\n"
            )

        if not tips:
            tips.append("未识别到常见可向导修复项。可运行：openclaw security audit --deep 查看详情。")

        cmds = (
            "可复制命令：\n"
            "- openclaw security audit --deep\n"
            "- openclaw status --deep\n"
            "- openclaw config show\n"
            "- openclaw gateway restart\n"
        )

        message = "\n".join(tips) + "\n" + cmds
        messagebox.showinfo("手动修复向导", message)

    def perform_maintenance(self):
        logs = []
        commands = [
            "openclaw security audit",
            "openclaw gateway restart",
            "openclaw status --deep",
        ]

        # 仅在检测到可更新时尝试更新
        if "available" in (self.openclaw_info.get("update", "").lower()):
            commands.insert(0, "openclaw update")

        for c in commands:
            out, err, code = run_cmd(c, timeout=120)
            snippet = (out or err or "").splitlines()[:2]
            logs.append(f"[{code}] {c} :: {' | '.join(snippet) if snippet else 'ok'}")

        self.last_maint_ts = time.time()
        self.maint_running = False
        self.after(0, lambda: self.maint_lbl.config(text="维护状态: 完成" if logs else "维护状态: 无动作"))

    def animate(self):
        self.canvas.delete("all")
        cx, cy = 210, 110

        self.canvas.create_oval(cx - 70, cy - 35, cx + 70, cy + 35, fill="#ff6b6b", outline="#ffa1a1", width=2)
        self.canvas.create_oval(cx - 25, cy - 45, cx - 12, cy - 32, fill="#fff")
        self.canvas.create_oval(cx + 12, cy - 45, cx + 25, cy - 32, fill="#fff")
        self.canvas.create_oval(cx - 21, cy - 41, cx - 16, cy - 36, fill="#000")
        self.canvas.create_oval(cx + 16, cy - 41, cx + 21, cy - 36, fill="#000")

        a = math.sin(self.angle)
        left_y = cy - 10 - 18 * a
        right_y = cy - 10 + 18 * a
        self.canvas.create_line(cx - 70, cy - 5, cx - 120, left_y, fill="#ff8a8a", width=6, smooth=True)
        self.canvas.create_oval(cx - 135, left_y - 12, cx - 110, left_y + 12, fill="#ff7f7f", outline="")

        self.canvas.create_line(cx + 70, cy - 5, cx + 120, right_y, fill="#ff8a8a", width=6, smooth=True)
        self.canvas.create_oval(cx + 110, right_y - 12, cx + 135, right_y + 12, fill="#ff7f7f", outline="")

        self.canvas.create_polygon(cx, cy + 35, cx - 24, cy + 65, cx + 24, cy + 65, fill="#ff7b7b", outline="#ffa1a1")

        for i in range(6):
            y = (cy + 90 - (time.time() * 30 + i * 35) % 200)
            x = 30 + i * 60 + (5 * math.sin(self.angle + i))
            r = 3 + (i % 3)
            self.canvas.create_oval(x - r, y - r, x + r, y + r, outline="#86dfff")

        self.angle += 0.15
        self.after(60, self.animate)


if __name__ == "__main__":
    app = LobsterMonitor()
    app.mainloop()
