# Changelog

## v0.1.0 - 2026-03-08

### Added
- Initial OpenClaw Lobster Status Cockpit GUI (`openclaw_lobster_monitor.py`)
- Real-time status panels: system info, resources, sessions, heartbeat
- Official-comparable score model:
  - score (0-100)
  - grade (S/A/B/C/D)
  - estimated percentile (Pxx)
- Growth stage visualization:
  - 虾苗 / 幼虾 / 成虾 / 壮虾 / 龙虾王
  - next-tier progress bar and gap points
- Warning lights (red/yellow/green) + text reason
- One-click maintenance and auto-maintenance switch
- Manual remediation wizard for configuration-type warnings
- Workspace metrics:
  - workspace size and partition ratio
  - task entry counts (open/done/total)
  - task file count and total file count
- Refresh UX improvements:
  - running-state label
  - disable while refreshing
  - completion timestamp

### Docs
- Added `README.md`
- Added `LICENSE` (MIT)
- Added GitHub release workflow and Windows `.exe` build workflow
