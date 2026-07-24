# 📡 Skills Data Hub · SkillHub Developer Analytics Dashboard

> A real-time decision center for **SkillHub** creators — unified ~50-second polling of downloads, favorites, eval scores, market data, and category heat, plus full-platform competitor search and blue-ocean / red-ocean strategy hints.

---

## ✨ Why this exists

Shipping a skill is half the job; **knowing how it performs** is the other half. Skills Data Hub turns the scattered SkillHub numbers into one command center you can leave open on a second monitor — on PC **or** tablet, over the same Wi-Fi.

---

## 🎯 Key Features

- **Unified ~50s live refresh** — Downloads, favorites, eval scores, version time, eval-report time, market data, and category heat are polled together on a ~50-second cadence.
- **Full-platform competitor search** — Keyword match across **name + description** with core-term / exclude-term dual filtering. Dual ranking: **Top-10 by downloads** and **Top-10 newest uploads**.
- **Category heat ranking** — Blue-ocean vs. red-ocean identification with suggested skill directions.
- **Version ↔ eval闭环** — Every skill card shows `vX released N days ago → eval Y score`, so you can verify whether an iteration actually moved the needle.
- **Day-over-day growth** — Yesterday's环比 (period-over-period) delta computed per metric.
- **Polished UX** — Page-turn number animations, dark tech-style UI, cross-device real-time display (PC/tablet on same Wi-Fi).
- **Zero-config detection** — Auto-detects your skills; optional custom config in `config.json` (no code changes needed).

---

## 🚀 How to use

1. Open the dashboard (web app shipped in this repo).
2. Enter your **SkillHub user ID**.
3. Watch the live board: your skills' real-time metrics, competitor rankings, and category heat.
4. Use the suggestions to decide *what to build next* and *what to iterate*.

> **Data source:** SkillHub public platform data. An API key is **not** required (`requires_api_key: false`).

---

## 🧩 What's inside

| Path | Purpose |
|------|---------|
| `index.html` / app entry | The analytics dashboard |
| `config.json` | Optional user config (skill auto-detection, custom overrides) |
| `references/` | Metric definitions, ranking logic, UI notes |
| `README.md` | This document |

---

## 🌍 Who it's for

- **SkillHub skill developers** who want a real operations dashboard, not guesswork.
- **Indie AI-tool makers** tracking competitor moves and category trends.
- **Teams** running multiple skills and needing one unified view.

---

## 💖 Sponsor

If the dashboard helps you ship a better skill or spot a blue ocean, consider sponsoring its development. Sponsorship keeps it **free and continuously improved**.

[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-brightgreen)](https://github.com/sponsors/FrankHu-HK)

> GitHub Sponsors is the only official donation channel for this project.

---

## 📄 License

Released under the [MIT License](./LICENSE). Authored by 胡景堃 (Frank Hu).
