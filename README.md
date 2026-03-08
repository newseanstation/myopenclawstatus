# My OpenClaw Status Cockpit (Lobster Monitor)

A lightweight visual cockpit for OpenClaw status, with a playful lobster-style UI.

## Features

- OpenClaw status snapshot (`openclaw status`)
- Deep check refresh (`openclaw status --deep`, low-frequency)
- Health scoring and level (S/A/B/C/D)
- Growth stage visualization (虾苗 → 龙虾王)
- Red/Yellow/Green warning lights
- One-click maintenance + auto-maintenance switch
- Manual fix wizard for configuration-type warnings
- Workspace statistics:
  - task entry count (open/done)
  - task files count
  - workspace disk usage ratio
- Animated lobster in dashboard

## File

- `openclaw_lobster_monitor.py`

## Run

```bash
python3 openclaw_lobster_monitor.py
```

If `tkinter` is missing on Ubuntu:

```bash
sudo apt update
sudo apt install -y python3-tk
```

## Notes

- This is a custom project, not an official default OpenClaw UI.
- Some security warnings are configuration-level and may require manual decisions.

## License

MIT (see `LICENSE`)
