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
from datetime import datetime
from tkinter import ttk

REFRESH_SEC = 10
DEEP_REFRESH_SEC = 120


def run_cmd(cmd, timeout=25):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (p.stdout or "").strip(), (p.stderr or "").strip(), p.returncode
    except Exception as e:
        return "", str(e), 1


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
    p = percentile_from_score(score)
    return {
        "score": round(score, 1),
        "grade": grade,
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
        self.deep_status_text = ""
        self.last_deep_ts = 0
        self.rating = {"score": 0, "grade": "D", "percentile": 1, "reasons": []}

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
        self.rank_bar = ttk.Progressbar(card0, maximum=100)
        self.rank_bar.pack(fill="x", padx=8, pady=(8, 2))
        self.rank_detail = ttk.Label(card0, text="分位: --")
        self.rank_detail.pack(anchor="w", padx=8, pady=(0, 8))

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
        self.disk_lbl.pack(anchor="w", padx=8, pady=(0, 10))

        card3 = ttk.LabelFrame(right, text="能力级别 / 升级状态", style="Card.TLabelframe")
        card3.pack(fill="x", pady=6)
        self.capability_text = tk.Text(card3, height=12, bg="#0d1f36", fg="#d9f0ff", bd=0)
        self.capability_text.pack(fill="both", expand=True, padx=8, pady=8)

        card4 = ttk.LabelFrame(right, text="当前任务与动画", style="Card.TLabelframe")
        card4.pack(fill="both", expand=True, pady=6)
        self.task_text = tk.Text(card4, height=8, bg="#0d1f36", fg="#d9f0ff", bd=0)
        self.task_text.pack(fill="x", padx=8, pady=8)

        self.canvas = tk.Canvas(card4, width=420, height=210, bg="#07111f", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        refresh_btn = ttk.Button(self, text="立即刷新", command=self.refresh_async)
        refresh_btn.pack(pady=(0, 10))

    def refresh_async(self):
        threading.Thread(target=self.refresh_data, daemon=True).start()

    def refresh_data(self):
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
        self.rating = score_openclaw(self.openclaw_info, self.sys, self.deep_status_text)

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
        self.after(REFRESH_SEC * 1000, self.refresh_async)

    def render(self, task_line):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_lbl.config(text=now)

        score = self.rating.get("score", 0)
        grade = self.rating.get("grade", "D")
        pct = self.rating.get("percentile", 1)
        self.rank_lbl.config(text=f"评级: {grade}  |  总分: {score:.1f}/100")
        self.rank_bar["value"] = score
        self.rank_detail.config(text=f"群体分位(估算): P{pct}  ·  维度: 安全/更新/可用性/资源/深度探针")

        self.system_text.delete("1.0", "end")
        self.system_text.insert("end", f"Dashboard: {self.openclaw_info.get('dashboard','-')}\n")
        self.system_text.insert("end", f"Gateway: {self.openclaw_info.get('gateway','-')}\n")
        self.system_text.insert("end", f"Sessions: {self.openclaw_info.get('sessions','-')}\n")
        self.system_text.insert("end", f"Heartbeat: {self.openclaw_info.get('heartbeat','-')}\n")
        self.system_text.insert("end", f"Tailscale: {self.openclaw_info.get('tailscale','-')}\n")

        self.mem_bar["value"] = self.sys.get("mem_pct", 0)
        self.disk_bar["value"] = self.sys.get("disk_pct", 0)
        self.mem_lbl.config(text=f"内存: {self.sys.get('mem_used_gb',0):.1f}/{self.sys.get('mem_total_gb',0):.1f} GB ({self.sys.get('mem_pct',0):.1f}%)")
        self.disk_lbl.config(text=f"磁盘: {self.sys.get('disk_used_gb',0):.1f}/{self.sys.get('disk_total_gb',0):.1f} GB ({self.sys.get('disk_pct',0):.1f}%)")

        self.capability_text.delete("1.0", "end")
        self.capability_text.insert("end", f"升级状态: {self.openclaw_info.get('update','-')}\n")
        self.capability_text.insert("end", f"Agents: {self.openclaw_info.get('agents','-')}\n")
        self.capability_text.insert("end", f"Security: {self.openclaw_info.get('security','-')}\n\n")
        self.capability_text.insert("end", "扣分明细:\n")
        for r in self.rating.get("reasons", [])[:5]:
            self.capability_text.insert("end", f"- {r}\n")

        self.task_text.delete("1.0", "end")
        self.task_text.insert("end", f"当前活跃任务(估计):\n{task_line}\n\n")
        self.task_text.insert("end", "这只小龙虾正在巡航：\n")
        self.task_text.insert("end", "- 每10秒采样基础状态\n")
        self.task_text.insert("end", "- 每120秒刷新深度探针\n")
        self.task_text.insert("end", "- 生成官方可比体量评级\n")

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
