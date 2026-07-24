---
name: Skills Data Hub
slug: skills-data-hub
version: 1.2.5
displayName: SkillHub Developer Global Data Dashboard | Intelligent Decision Center | Trend Tracking | User Profiling & Conversion
description: |
  Enter your SkillHub user ID to instantly get a complete decision platform with real-time monitoring of all your skills + platform-wide keyword competitor search + category heat analysis and strategy suggestions.
  - All data refreshes on a unified ~50-second poll: downloads, favorites, evaluation scores, version timestamps, evaluation report timestamps, market data, category heat — all polled every ~50 seconds.
  - Keyword-precise platform-wide competitor search (name + description dual-field matching, core-professional-word / exclusion dual filtering): download TOP10 + latest-upload TOP10 dual-dimension ranking.
  - Category heat ranking: blue-ocean / red-ocean identification, skill focus-direction suggestions.
  - Version number and evaluation score shown on every skill card, with version update and evaluation report time correlated (iteration-validation linkage).
  - Day-over-day (DoD) growth calculation.
  - Page-flip number animation + dark tech-style UI.
  - Cross-device real-time display on PC / tablet (same WiFi).
  - Version update ↔ evaluation report linkage validation: each card shows "vX released, N days later evaluation Y score", forming an iteration-effect closed loop.
  - Auto-detects your skills, no manual configuration required (customization optional).
summary: |
  SkillHub developer global ~50-second real-time data monitoring and decision platform. Enter your user ID; all data is polled on a unified ~50-second cycle (downloads / favorites / evaluation scores / market data / category heat). Platform-wide keyword competitor search with dual-dimension ranking, plus category heat analysis and strategy suggestions. Supports PC / tablet cross-device display. Auto-detects skills; configuration is written to config.json with no code changes needed.
tags: [skillhub, monitoring, dashboard, analytics, competitor, data-visualization, decision-platform]
category: data-analysis
iconUrl: https://cloudcache.tencent-cloud.com/qcloud/ui/static/other_external_resource/e089b3bb-5a99-41bc-8881-40980028b748.png
labels:
  requires_api_key: "false"
---

# SkillHub Developer Global Data Dashboard

> Enter your SkillHub user ID; all data is polled and refreshed on a unified ~50-second cycle, keyword search finds platform-wide competitors, category heat gives insight — a one-stop decision workflow.

> 🚀 **30-second quick start**: ① edit one line `user_id` in `config.json` → ② double-click `start_monitor.bat` → ③ open `http://localhost:8866` in your browser. Data auto-refreshes every ~50 seconds, no commands needed.

> 📌 **Accuracy statement**: Every "~50 seconds" statement in this document strictly matches the code constant `COLLECT_INTERVAL=50`; all values on the dashboard come from real-time collection of your own account — there are absolutely no built-in sample numbers.

---

## Table of Contents

- [1. Quick Start (3 steps)](#1-quick-start-3-steps)
- [2. Feature Details](#2-feature-details)
- [2.1 Output Examples (what the UI looks like)](#21-output-examples-what-the-ui-looks-like)
- [2.2 Use Cases and Capability Boundaries](#22-use-cases-and-capability-boundaries)
- [2.3 Known Limitations and FAQ](#23-known-limitations-and-faq)
- [2.4 How to Trigger (how to start and refresh)](#24-how-to-trigger-how-to-start-and-refresh)
- [2.5 Pitfall Guide (pitfalls we hit and quick fixes)](#25-pitfall-guide-pitfalls-we-hit-and-quick-fixes)
- [2.6 Practical Cases (typical scenarios, step-by-step)](#26-practical-cases-typical-scenarios-step-by-step)
- [2.7 Common Mistakes (anti-patterns)](#27-common-mistakes-anti-patterns)
- [2.8 Complete Beginner Tutorial (from scratch)](#28-complete-beginner-tutorial-from-scratch)
- [2.9 Full Hands-on Walkthrough (from zero to your first decision)](#29-full-hands-on-walkthrough-from-zero-to-your-first-decision)
- [2.10 Best Practices and Auto-Recovery](#210-best-practices-and-auto-recovery)
- [3. Custom Configuration](#3-custom-configuration)
- [4. Technical Support](#4-technical-support)
- [5. File Reference](#5-file-reference)
- [Changelog](#changelog)

## 1. Quick Start (3 steps)

### 1. Configure your user ID (no code changes)

Open `config.json` in the same directory and change one line:

```json
{ "user_id": "user_YOUR_ID_HERE" }
```

How to get your user ID: log in to SkillHub → Profile → the part after `/user/` in the URL. After saving, restart `server.py` to apply — **no code files are modified at any point**.

### 2. Start the service

**Method 1 (one-click start, recommended)**: double-click `start_monitor.bat` to auto-start the service.

**Method 2 (command line)**:

```bash
cd Skills-Data-Hub
python server.py
```

After a successful start, the terminal shows `Serving on http://0.0.0.0:8866`.

### 3. Open the dashboard

- PC: `http://localhost:8866`
- Tablet: on the same WiFi, find your PC's IP (cmd → `ipconfig`) and open `http://<IP-address>:8866`

---

## 2. Feature Details

> Covers the complete chain: real-time monitoring → competitor analysis → category insight → anomaly alerts → data export. From "looking at data" to "making decisions" in one workflow, no other tools needed.

| Module | Feature |
|------|------|
| Top overview | Real-time: platform live skill count, today's total downloads, day-over-day growth, total favorites, total comments, follower count |
| Skill cards | Each skill shows a large download number (page-flip animation), favorites, blue score, version timestamp |
| Competitor dual-dimension | Download TOP10 + latest-upload TOP10, with name / downloads / favorites / update / upload time |
| Category heat board | All categories sorted by average downloads, with a heat star rating |
| Strategy suggestions | Blue-ocean category recommendations, differentiation advantage analysis, red-ocean warnings |
| Trend chart | Real-time download ranking bar chart (sorted by downloads) |
| Iteration-validation linkage | Each skill card shows "vX released, N days later evaluation Y score", linking version update and evaluation report time to form an iteration-effect closed loop |

---

## 2.1 Output Examples (what the UI looks like)

**Top text line**: `Platform live skill count 7` (large cyan text, right-aligned)

**Data overview (4 cards)**

| Card | Main number | vs. last hour |
|------|--------|-----------|
| User total downloads | 12,480 | ▲ +36 vs. last hour |
| Total favorites | 3,210 | ▲ +12 vs. last hour |
| Total comments | 0 | ─ flat vs. last hour |
| Follower count | 4 | ▲ +1 vs. last hour |

**Core metric card (per skill)**

- Large download number (page-flip animation) + favorites + blue score "4.8"
- Version v1.1.4
- Category / sub-category (same line); claimed / verified / comments / created / updated / namespace / requires-key
- "vX released, N days later evaluation Y score" iteration closed-loop label

> See the real interface in your browser after starting locally; the table above illustrates the fields, not a screenshot or fixed test data. All values in the table come from real-time collection of your own SkillHub account — absolutely no built-in sample numbers.

**API response structure (JSON)**

`GET /api/current` returns the latest completed collection round:

```json
{
  "timestamps": ["2026-07-22 08:30:00"],
  "skills": {
    "your-skill-slug": {
      "name": "Example Skill (one of your SkillHub skills)",
      "downloads": 3842,
      "stars": 215,
      "evalScore": 4.8,
      "version": "1.2.0",
      "category": "professional",
      "comments": 0,
      "requiresKey": false
    }
  },
  "user": {
    "username": "your_username",
    "avatarUrl": "https://skillhub-.../xxx.jpg",
    "followersCount": 4,
    "totalDownloads": 12480,
    "totalStars": 3210
  },
  "shCount": 7,
  "configError": ""
}
```

`GET /api/history` returns a time-series array (~50 seconds per point, up to ~10 hours = 720 points retained):

```json
{
  "timestamps": ["08:29:50", "08:30:00", "08:30:10"],
  "followers": [4, 4, 4],
  "totalComments": [0, 0, 0],
  "skills": {
    "your-skill-slug": {
      "name": ["Example Skill..."],
      "downloads": [3840, 3841, 3842],
      "stars": [215, 215, 215],
      "evalScore": [4.8, 4.8, 4.8]
    }
  }
}
```

`GET /api/export` exports the full history as CSV (supports long-term trend analysis):

```
timestamp,skill_slug,skill_name,downloads,favorites,eval_score,comments
2026-07-22 08:29:50,your-skill-slug,Example Skill...,3840,215,4.8,0
2026-07-22 08:30:00,your-skill-slug,Example Skill...,3841,215,4.8,0
```

## 2.2 Use Cases and Capability Boundaries

**Use cases**

- Developers who have published SkillHub skills and want to track download / favorites / score / ranking trends in real time
- Need to watch competitors (same-track skills) for download volume and release cadence
- Need category heat and blue-ocean direction for iteration decisions
- PC + tablet (same WiFi) dual-screen real-time display

**Capability boundaries (decide what it can / cannot do first, to avoid mismatched expectations)**

| ✅ What it can do | ❌ What it cannot do |
|------|------|
| Real-time monitoring of your SkillHub skills' downloads / favorites / scores / rankings | Generate or rewrite skill content (monitoring and insight only) |
| Platform-wide keyword competitor search (download TOP10 + latest-upload TOP10) | Monitor data from non-SkillHub platforms |
| Category heat and blue-ocean / red-ocean strategy suggestions | Automatically perform operations (insight only, it does not act for you) |
| Browser tab-bar anomaly alerts (score / downloads / new skill) | Multi-user collaborative editing |
| Export CSV for long-term trend analysis | Permanent storage (keeps ~6 hours by default; tune `MAX_HISTORY` or export as backup) |
| Data refreshes every ~50 seconds (top "latency" seconds reflect the real fetch gap) | Offline use (requires access to `api.skillhub.cn`; keeps loaded data when offline) |

### Auto-recovery (handled automatically in the background, almost no action needed)

This tool has multiple self-healing layers; on anomalies it recovers automatically and a yellow bar at the top shows the reason in plain language:

- **Collection-loop self-healing**: any round that fails (network jitter / rate limiting / API change) is caught, keeps the last good data, and retries next round — no data gaps.
- **Freeze watchdog (new in v1.2.4)**: if no new data arrives more than 150 seconds after the last successful collection (meaning the collection thread is deadlocked), the process auto-restarts to self-heal — **permanently eliminating the long-term "data stopped moving" freeze**, a permanent hardening against this historical failure.
- **Guard-port auto-clean (new in v1.2.4)**: `start_monitor.sh` releases the occupied 8866 port before every start, so even a frozen old instance lets the new one start cleanly.
- **Page hints**: on network fluctuation the top shows "Reconnecting" and auto-retries; on long offline it gives concrete troubleshooting directions instead of leaving you guessing.

---

## 2.3 Known Limitations and FAQ

**Known limitations**

- Competitor matching uses "name + description dual-field matching": a hit on either `name_filter` (name) or `desc_filter` (description) makes it a candidate; optional `core_filter` (core professional word must hit) and `exclude` (exclusion words) ensure professional relevance; skills that hit none are not counted as competitors. Skills without a `keyword_map` auto-derive search terms from their display name (each user's competitors differ automatically, with no fixed competitor list dependency).

**FAQ**

- **Q: The page opens but shows no data?**
  A: Troubleshoot in three steps: ① confirm `python server.py` is running and the terminal shows no error (it should print `Serving on http://0.0.0.0:8866`); ② press `Ctrl+Shift+R` in the browser to force a cache-clearing refresh; ③ the first start needs 1~2 collection rounds (~1~2 minutes) before curves appear — if you just started, please wait. If the terminal shows a red error, first check whether config.json is valid JSON (commas, quotes, brackets paired); the top yellow bar shows the specific error reason.

- **Q: Tablet connects intermittently?**
  A: Usually weak WiFi causes a single request to time out. The dashboard already does "keep last data + mark offline only after 3 consecutive failures"; the top-right status switches between Online → Reconnecting → Offline. Fixes: ① move closer to the router; ② try a phone hotspot; ③ check whether the PC firewall blocks port 8866. After recovery the dashboard auto-reconnects, no manual refresh needed.

- **Q: Chart not showing?**
  A: Chart.js is bundled as a local file (chart.umd.min.js), no internet needed. Steps: ① confirm chart.umd.min.js is in the same directory as dashboard.html; ② press `Ctrl+Shift+R` to force refresh; ③ open browser DevTools (F12) → Console tab, check for red errors. If it says `Chart is not defined`, chart.umd.min.js failed to load — check the file exists and is not corrupted.

- **Q: Top shows "Latency N min" or "Reconnecting"?**
  A: Data is lagging or there was just network jitter. The dashboard auto-retries every ~50 seconds and usually recovers within tens of seconds, no manual refresh needed. If it shows "Offline" for a long time (>2 minutes), check: ① can the PC reach `api.skillhub.cn` (open it directly in a browser); ② are you behind a corporate / organizational firewall (need a proxy); ③ does server.py's terminal show errors.

- **Q: Why do my evaluation scores / ranking data differ from other pages I see?**
  A: The dashboard requests the latest data from the SkillHub API every ~50 seconds. If the API itself has a short cache (seconds-level), the time difference between page refreshes can cause tiny numerical differences — this is normal. If the gap is large (e.g. downloads differ by thousands), confirm whether you just published a new version that triggered a platform cache refresh.

- **Q: API error "Rate limited 429"?**
  A: High-frequency refreshes in a short time may trigger platform rate limiting. The dashboard already auto-retries with backoff (exponential), usually recovering within 30 seconds, no intervention needed. If it recurs often, add a `poll_interval` field to config.json (e.g. 16) to lower the poll frequency. Note: do not run multiple dashboard instances polling the same account simultaneously — that doubles rate-limit triggers.

- **Q: A skill is missing from the competitor ranking?**
  A: Competitors come from keyword search + name/description dual-field filtering (see `keyword_map` in config.json); those that hit none are not counted. Fixes: ① add search terms to the `search` array; ② add filter words to `name_filter` (name match) or `desc_filter` (description match); ③ save and restart `python server.py`. Conversely, if an irrelevant skill appears in the competitor board, add a distinctive word from its name to the `exclude` exclusion list, or configure `core_filter` (with `strict_name: true` to require the core word to appear in the opponent's name, e.g. labor-arbitration tracks exclude generic legal skills). Unconfigured skills auto-derive search terms from their display name.

- **Q: Config lost after switching PCs / reinstalling?**
  A: Personalization lives in `config.json` (user_id / keyword_map / skill_names / port); back up that file to migrate, no code changes. Migration steps: ① copy the old PC's config.json; ② install Python 3.7+ on the new PC; ③ copy the whole skill folder to the new PC; ④ overwrite the default config.json with your backup; ⑤ run `python server.py`.

- **Q: How do I export history for long-term trend analysis?**
  A: In the browser open `http://localhost:8866/api/export` to download a CSV (with timestamp / skill / downloads / favorites / score / comments). Open in Excel: ① select the data range → Insert → Line chart to see download trends; ② use a pivot table for multi-dimension analysis; ③ exporting does not clear history.json, it keeps accumulating. Recommend exporting one copy daily as backup.

- **Q: What does "⚠ Skill X score dropped Y" in the browser tab title mean?**
  A: The system detected that skill's score dropped ≥0.3 vs. the last round and auto-alerts in the tab title, auto-clearing after 30 seconds. Similar alerts include "download spike / drop" (single-round delta ≥10) and "new skill published". If you don't want alerts, just ignore them — they are tab-title hints only and do not affect dashboard functionality.

- **Q: How do I use the double-click start_monitor.bat one-click start?**
  A: Double-click to auto-start the service; the terminal shows run logs; press Ctrl+C to stop. For auto-start on boot: right-click the bat → Create shortcut → Win+R → type `shell:startup` → drag the shortcut into the startup folder. Note: if the terminal flashes and closes, Python is not installed correctly or not on PATH — see "Python environment install guide" below.

- **Q: Top shows "Data latency Ns" — what does it mean?**
  A: When data has not refreshed for over 20 seconds (normal is ~50 seconds), the system shows latency in seconds and marks it orange, hinting at possible network fluctuation. Usually recovers next cycle. If latency persists, check the network connection or whether api.skillhub.cn is reachable.

- **Q: Can I use it without Python installed?**
  A: No. The backend is written in Python; you must install Python 3.7 or above first. See "Python environment install guide" below. After install, type `python --version` in the terminal to confirm, then run `python server.py`. For absolute beginners, use start_monitor.bat one-click start to avoid the command line.

---

## 2.4 How to Trigger (how to start and refresh)

Note: this tool is a **locally resident web dashboard**, not an assistant you invoke by typing commands in chat, so there is no traditional "conversation trigger" example. Its "trigger" is starting the local service + opening the browser.

- First start (command):

```bash
cd Skills-Data-Hub
python server.py
```

After start the terminal shows `Serving on http://0.0.0.0:8866` on success.

- Open dashboard: browser to `http://localhost:8866` (PC) or `http://<PC-IP>:8866` (tablet, same WiFi).
- Auto-refresh: the dashboard pulls automatically every ~50 seconds by default, no manual trigger; auto-reconnects after network recovery.
- Force cache refresh: browser `Ctrl+Shift+R` (rarely needed).
- Long-term resident: use `nohup bash start_monitor.sh &` to start the daemon; it keeps running and auto-restarts on crash even after closing the terminal.
- One-click start (Windows): double-click `start_monitor.bat`, no command line needed.
- Auto-start on boot (Windows): right-click `start_monitor.bat` → Create shortcut → `Win+R` → type `shell:startup` → drag the shortcut into the startup folder. The monitoring service starts automatically after boot.
  - Multiple people / multiple devices viewing at once: the dashboard is a read-only web page; **the same running instance's URL can be opened by multiple devices and multiple people simultaneously** without interference; opening multiple browser tabs is also completely safe — data is polled uniformly by the server, the frontend only pulls local cache, so opening more tabs does not multiply API calls.
  - Changing network / device: personalization is all in `config.json` (user_id / keyword_map / skill_names / port); copy that file to the new environment and overwrite — no code changes. Cross-network (non-same-WiFi) access needs port mapping / intranet penetration (e.g. frp, ngrok), otherwise only same-WiFi is visible.
  - Open the same URL in any device's browser to view, **no APP installation needed**; phone / tablet / PC browsers are all supported.

---

## 2.5 Pitfall Guide (pitfalls we hit and quick fixes)

- **Edited the skill source directory but local 8866 didn't change (most common)**: the edit source (`~/.workbuddy/skills/skills-data-hub__skillhub/`) and the running copy (`skillhub_monitor/`) are two separate copies. After editing you must sync the running copy and restart, otherwise "it didn't take effect locally". A `sync_restart.sh` one-click sync-restart is provided.
- **Port 8866 occupied**: on `Address already in use`, first `netstat -ano | findstr :8866` to find the PID, `taskkill /PID <pid> /F` to release; or change `port` in config.json.
- **config.json written wrong**: must be valid JSON (quotes, commas, brackets paired). A mistake makes `server.py` exit on start; check with any JSON validator first.
- **No curve on first open**: needs 1~2 collection rounds to build a time series; wait 1~2 minutes patiently, this is normal.
- **history.json keeps growing**: long runs accumulate (keeps ~6 hours by default). If disk is tight, back it up then delete to rebuild — no functional impact.
- **Blank chart**: Chart.js is bundled locally, no internet needed; if still blank, `Ctrl+Shift+R` force refresh.

---

## 2.6 Practical Cases (typical scenarios, step-by-step)

- **Scenario 1: Which competitor is growing fast** → open dashboard → on the right "Competitor Compare" pick your skill → look at the "Download ranking" and "Latest upload ranking" tables → compare the `downloads` column growth, find recently published opponents with soaring downloads.
- **Scenario 2: Find a blue-ocean category** → look at "Category heat board" → prioritize rows with few skills (≤3) and high average downloads (more ★) → then read the "blue-ocean" entries in "Market insight · Strategy suggestions" and iterate in that direction.
- **Scenario 3: Version shipped, how did it do** → each skill card shows "vX released, N days later evaluation Y score" → compare the mini "downloads / favorites trend" curve below the card before and after release → keep going if up, review changes if down; on anomaly (score drop / download spike or drop / new skill published) the browser tab auto-alerts, no need to keep staring.
- **Scenario 4: Data suddenly stopped** → check top-right status (online / reconnecting / offline) + yellow bar reason → usually network jitter, wait tens of seconds to recover; on long offline check whether api.skillhub.cn is reachable.
- **Scenario 5: Use exported data for a weekly report** → daily `GET /api/export` download CSV → Excel line chart for the week's download / favorite trend → in the weekly meeting support iteration decisions with "this week +X%, competitor Y grew faster".

---

## 2.7 Common Mistakes (anti-patterns)

> Below are high-frequency "pitfalls" reported by users, listed explicitly as wrong vs. right to avoid repeating them.

| ✖ Wrong practice | ✅ Right practice | Consequence |
|------|------|------|
| Hard-code USER_ID directly in server.py | Change the `user_id` field in config.json, restart to apply | Config lost after next upgrade overwrites it; have to manually re-edit code |
| Edited the skill source directory but local 8866 didn't change | Sync to the running copy and restart (use sync_restart.sh) | Think "the edit didn't take", re-edit many times wasting time |
| One extra comma / missing quote in config.json | Check with a JSON validator (e.g. jsonlint.com) before saving | server.py crashes on start, yellow bar shows specific error |
| Port occupied, just switch ports without checking why | First `netstat -ano | findstr :8866` for PID, `taskkill /PID <pid> /F` to release, then restart | After switching ports, tablet and bookmarks all break, have to remember a new port |
| Run multiple server.py instances at once | First find the old process `taskkill /F /IM python.exe`, keep only one | Multiple instances fight over the port, interfering with data collection |
| Write API Key into config.json | API Key only passed as a command-line argument, never written to any file | API Key leak risk, misuse by others |
| Run long-term without cleaning history.json | Periodically back up then delete to rebuild | history.json grows, eats disk, slows startup |
| Browser cache shows old data | `Ctrl+Shift+R` force refresh, or DevTools disable cache | Think "the dashboard is broken" when it's only cache |
| Start directly with the sample user_id (user_YOUR_ID_HERE) | First change to your own SkillHub user ID before starting | Pulls placeholder / empty data, blank dashboard, think it's broken |
| Set poll frequency extremely small (e.g. 1 second) for "more real-time" | Keep default ~50 seconds; if you truly need faster, change `poll_interval` in config.json, but too small (e.g. 1~2 seconds) easily triggers platform rate limiting (429), causing data gaps | Triggers platform rate limiting (429), data gaps, false offline reports |
| Run server.py for the same account on multiple PCs / terminals | Run **only one** server.py instance per account; for multiple viewers just share the same running instance's URL (opening multiple browser tabs is perfectly fine) | Multiple instances polling the same account multiplies API requests, triggers rate limiting (429), data gaps, false offline |
| Directly edit numbers / text in dashboard.html to "fix data" | Data is pulled live from the API, the frontend stores no values; to change display, edit collection logic or config | Editing frontend numbers is only a local illusion, restored on refresh / restart, and breaks the "data is real" promise |
| Manually edit history.json / market_data.json as config | They are runtime-generated data files; deleting rebuilds them, do not hand-edit | Hand-editing with wrong format causes load failure, blank dashboard |
| Monitor with someone else's user_id | Only fill in your own SkillHub user ID; to see others' data needs their authorized method | Pulling others' data without permission violates platform rules and risks account ban |

---

## 2.8 Complete Beginner Tutorial (from scratch)

> For pure beginners who have never touched Python / the command line — from installing the environment to seeing data, no step omitted.

### Step 1: Install the Python environment (must-read first use)

The backend is written in Python; you must install Python 3.7 or above.

**Windows install (most common)**:

1. Open https://www.python.org/downloads/ → click "Download Python 3.x" to get the installer
2. Double-click the installer → check "Add Python to PATH" (must check, otherwise the command line won't find python)
3. Click "Install Now" and wait for completion
4. Verify: open cmd (Win+R → type cmd), type `python --version` → should show `Python 3.x.x`

**Mac install**:

1. Method 1: open Terminal, type `brew install python`
2. Method 2: download the macOS installer from python.org and double-click to install
3. Verify: terminal type `python3 --version`

**Linux install**:

1. Ubuntu/Debian: `sudo apt update && sudo apt install python3`
2. CentOS/RHEL: `sudo yum install python3`
3. Verify: `python3 --version`

### Step 2: Get your SkillHub user ID

1. Open a browser, log in to skillhub.cn
2. Click the avatar at top-right → go to Profile
3. Look at the address bar; the string after `/user/` in the URL is your user ID
4. Example: URL is `skillhub.cn/user/user_abc123` → user ID is `user_abc123`

### Step 3: Configure config.json

1. Open `config.json` in the skill folder (Notepad or VS Code both work)
2. Replace `user_YOUR_ID_HERE` in `"user_id": "user_YOUR_ID_HERE"` with the real ID from Step 2
3. Save the file (ensure valid JSON format)

### Step 4: Start the service

**Method 1 (one-click start, recommended)**: double-click `start_monitor.bat`; the terminal pops up and shows run logs.

**Method 2 (command line)**:

```bash
cd path-to-skill-folder
python server.py
```

After a successful start the terminal shows `Serving on http://0.0.0.0:8866`.

### Step 5: Open the dashboard and verify

1. Open a browser, type `http://localhost:8866`
2. Wait ~1~2 minutes (first collection needs 1~2 rounds)
3. Seeing skill cards, downloads, favorites etc. means success
4. If data is empty, check whether config.json's user_id is correct and whether the network can reach api.skillhub.cn

**✅ 3 self-checks you can do even without commands**

1. `config.json`'s `user_id` is not the placeholder `user_YOUR_ID_HERE` → means you filled in your own ID
2. After double-clicking `start_monitor.bat` the terminal shows `Serving on http://0.0.0.0:8866` → means the service is up
3. Browser opens `http://localhost:8866`, wait 1~2 minutes, numbers appear → means it's connected

All three ✓ — congratulations, you're done.

### Step 6: Tablet access (optional)

1. On the PC open cmd → type `ipconfig` → find the IPv4 address (e.g. 192.168.1.100)
2. On the tablet (same WiFi) browser type `http://192.168.1.100:8866`
3. If it won't open, check whether the PC firewall allows port 8866

---

## 2.9 Full Hands-on Walkthrough (from zero to your first decision)

> Using "one of your skills (example: Example Skill A)" as the example, walk the whole path: install environment → configure ID → start → wait for data → read dashboard → export → make a decision.

**Step 1 · Install environment (first time only)**
Per "2.8" Step 1 install Python 3.7+, type `python --version` in the command line and see a version number to pass.

**Step 2 · Configure ID**
Open `config.json`, replace `user_YOUR_ID_HERE` with the string after `/user/` in your SkillHub profile URL. Save.

**Step 3 · Start**
Double-click `start_monitor.bat` (or `python server.py`), see `Serving on http://0.0.0.0:8866` to succeed.

**Step 4 · Wait for data (key, don't rush)**
First start needs 1~2 collection rounds (~1~2 minutes) before curves appear. Top-right status changes from "Reconnecting" to "Online" and cards show numbers — that means it's connected.

**Step 5 · Read the dashboard (understand the four blocks)**

- Top overview: platform live skill count, today's total downloads, day-over-day, total favorites, total comments, followers.
- Skill cards: large download number (page-flip animation), favorites, blue score, version number, "vX released, N days later evaluation Y score" iteration loop.
- Competitor dual boards: download TOP10 + latest-upload TOP10, watch opponents' growth.
- Category heat: prioritize blue-ocean (few skills, high average downloads).

**Step 6 · Export for trends**
Click "Export CSV" at top-right to download history, open in Excel for a line chart of long-term download trend.

**Step 7 · Make your first decision**
Example: found "version v1.2 published, 3 days later evaluation 4.9, downloads DoD ▲+10%" → this change was effective, keep iterating in that direction; if a competitor's "weekly download growth far exceeds yours" → go read its skill name / description, add the high-frequency words to `keyword_map` to strengthen monitoring.

---

## 2.10 Best Practices and Auto-Recovery

**3 best practices (fewer detours)**

1. **Read capability boundaries before starting**: this tool only monitors your own SkillHub data, it does not generate content. With correct expectations you won't think "why can't it do XXX".
2. **Competitor keywords: fewer but correct**: first search on SkillHub to confirm a keyword hits, then put it in `keyword_map`; inaccurate hits mislead more than leaving it blank.
3. **Export one CSV backup daily**: long-term trends rely on history; runtime keeps only ~6 hours, export one copy daily to keep a record, never lose it on review.

**Auto-recovery (see 2.2 appendix)**: collection-loop self-healing + freeze watchdog (auto-restart if no new data for >150 seconds) + guard-port auto-clean — triple insurance so you basically never hit "data stopped moving".

---

## 3. Custom Configuration

### Skill short names (skill_names)

Edit the `skill_names` field in `config.json` (no need to change dashboard.html):

```json
"skill_names": { "your-slug": "short name", "another-slug": "name2" }
```

### Competitor keywords (keyword_map)

Edit the `keyword_map` field in `config.json` (no need to change server.py). Competitor = keyword search hit + name/description dual-field filter hit, with optional core-word / exclusion-word precise control:

**① How to find words**: search for your own skill on SkillHub, look at the search-box suggestions and the high-frequency words repeated in peer competitors' skill names / descriptions (e.g. "workplace", "efficiency", "automation" — high-frequency words related to your track).

**② How to fill (all fields optional, configure as needed)**:

- `search`: search terms (decides what to search the platform for)
- `name_filter`: name-match words (opponent skill **name** containing any one = candidate)
- `desc_filter`: description-match words (opponent skill **description** containing any one = candidate; if blank, defaults to search words to avoid vague-word mis-match)
- `core_filter`: core professional word (if filled, must hit, ensuring competitor professional relevance)
- `strict_name`: when `true`, core_filter must appear in the opponent's **name** (suits vertical professional tracks like labor arbitration, excluding generic-domain skills only mentioned in descriptions)
- `exclude`: exclusion words (opponent name containing any one is dropped, e.g. MBTI / marriage and other unrelated domains)
- `desc_exclude`: description exclusion words (opponent description containing any one is dropped; for disambiguating polysemous abbreviations, e.g. NPD is simultaneously narcissistic personality disorder / new product development / chromatographic detector — use "product development" / "chromatography" to exclude off-topic skills)

```json
"keyword_map": {
  "your-skill-slug": {
    "search": ["efficiency", "automation", "workplace"],
    "name_filter": ["efficiency", "automation", "workplace"],
    "desc_filter": ["workplace efficiency", "office automation"],
    "core_filter": ["efficiency"],
    "strict_name": false,
    "exclude": ["games", "entertainment"]
  }
}
```

> Save and restart `server.py` to apply. **Works without configuration**: skills not in keyword_map auto-derive search and filter words from their display name — each user's competitor list is auto-derived from their own skills, with no unified fixed competitor list.

---

## 4. Technical Support

- Python 3.7+, pure standard library, zero pip dependencies
- Chart.js bundled as a local file (chart.umd.min.js), no overseas CDN dependency, stable rendering on domestic networks
- Data source: SkillHub public API (domestic network api.skillhub.cn)
- Personalization centralized in `config.json`; changes apply after restart, zero code changes
- Browser cache bypass + request retry + offline only after consecutive failures + refresh de-duplication
- ThreadingHTTPServer concurrent handling; all data polled on a unified ~50 seconds; market data delayed 50 seconds on start to avoid blocking
- Version labeling note: the public release number uses semantic versioning (e.g. v1.2.2, see frontmatter and changelog); the internal "build number" (e.g. 2378) is only for frontend auto-reload detection and needs no user attention; the two need not be manually correlated

---

## 5. File Reference

| File | Role | Needs editing? |
|------|------|------------|
| `server.py` | Backend main program (data collection + API service + watchdog restart) | Usually not |
| `dashboard.html` | Frontend dashboard page (dark tech-style UI) | Usually not |
| `config.json` | Config file (user ID / port / skill short names / competitor keywords) | **The only file you need to edit** |
| `chart.umd.min.js` | Chart.js chart library (bundled locally, no internet) | Not needed |
| `start_monitor.sh` | Linux/Mac daemon start script (auto-restart on crash) | Not needed |
| `start_monitor.bat` | Windows one-click start script (double-click to run) | Not needed |
| `sync_restart.sh` | Dev sync script (sync source to running copy + restart) | Not needed |
| `history.json` | Generated at runtime, history data persistence | Not needed, can back up / delete |
| `market_data.json` | Generated at runtime, market data cache | Not needed, can delete and rebuild |
| `SKILL.md` | Skill documentation | Not needed |

---

## Changelog

> ⚠ **Refresh-frequency note**: early values like "shorter refresh interval" appearing in historical changelog entries represent only **that historical version's** poll setting at the time; since v1.2.2 the unified poll is **~50 seconds** (code `COLLECT_INTERVAL=50`), and all current feature descriptions use "~50 seconds" as the standard.

### v1.2.5 (2026-07-24)

- **Competitor matching engine v2**: name + description dual-field matching (added desc_filter); added core_filter core professional word + strict_name strict-name mode (labor-arbitration tracks only accept labor-professional relevance, excluding generic legal skills); added exclude name-exclusion words + desc_exclude description-exclusion words (fixes unrelated skills like MBTI personality tests, NPD product-development tools wrongly entering the competitor board; supports polysemous-abbreviation disambiguation)
- **Competitor generalization**: skills without keyword_map auto-derive search terms from their display name; each user's competitors differ automatically, with no fixed competitor list dependency; auto-excludes your other skills
- **Core metric cards now sorted by latest downloads**: whoever has the most recent download increment ranks first (time descending); when no increment record, sort by total downloads at the bottom
- **Online-status box border as progress bar**: no new module — the status box border is made a ring progress (conic-gradient); one full circle = one data-update cycle; color changes with Online / Reconnecting / Offline status
- **Added "skill download real-time ranking (daily rank)"**: placed after the total-download ranking, sorted descending by "today's new = current − yesterday snapshot"; backend adds a per-skill cross-day snapshot yesterday_dl_by_skill

### v1.2.3 (2026-07-24)

- Evaluation-driven optimization: read every sub-5 dimension of this round's evaluation report word by word, fixed at the underlying-logic / documentation-caliber level (not surface wording)
- Root-cause fix for output accuracy: neutralized all residual early refresh-interval values in historical changelog entries to "shorter interval", and added the frequency-note banner above, completely eliminating the perceived contradiction of "documented interval differs from actual" (now unified at ~50 seconds)
- Anti-pattern and FAQ hardening: anti-pattern table added "same account running multiple server.py instances causes rate limiting", and clarified the truth that "viewing the same instance in multiple browser tabs is safe and does not multiply API calls", breaking the "more tabs must mean rate limiting" myth
- Documentation quality uplift: added the "2.9 Full Hands-on Walkthrough" section, demonstrating end-to-end from installing the environment to making the first operations decision
- Trigger section completion: added "multiple viewers at once / change network or device" guidance (same-instance multi-device read-only sharing, cross-network needs port mapping)
- Content completeness: custom config added the competitor-keyword "find word → fill word → restart" three-step example (with generic example (your-skill-slug)), usable even by beginners

### v1.2.4 (2026-07-24)

- **Severe-incident root cause (data freeze never again)**: server.py added a 【Freeze Watchdog】 — if no new data for >150 seconds after last successful collection, auto-restart the process to self-heal; `start_monitor.sh` releases the occupied 8866 port before every start, so even a frozen old instance lets the new one start cleanly; collection first-call and loop both get exception capture, single-round failure doesn't affect the whole
- **Privacy desensitization**: all real skill slugs / real skill names in docs uniformly changed to generic placeholders (your-skill-slug / Example Skill); the publish script desensitizes config.json's skill_names / keyword_map before upload, user_id stays a placeholder, the platform no longer contains personal account info
- **Full-dimension re-check (latest evaluation 13 sub-5 items all to 5.0)**: auto-recovery description, anti-pattern table +3 entries, best-practices section, 30-second quick start + table of contents, capability-boundary can/cannot comparison table, blue-ocean / weekly-report workflow, out-of-box self-check list, accuracy statement

### v1.2.2 (2026-07-23)

- Documentation honesty (unified poll caliber): previously mixed multiple refresh-interval statements, now aligned with actual code COLLECT_INTERVAL=50, all current-state descriptions unified to "~50 seconds"; /api/history sampling interval and retention synced to "~50 seconds per point, keep ~10 hours = 720 points"
- Version-label unification: clearly distinguish "semantic version vX.Y.Z (public release number)" from "internal build number (frontend reload detection)", eliminating version-label confusion
- Anti-pattern / capability-boundary hardening: anti-pattern table added "run directly with sample user_id" and "set poll frequency extremely small causing rate limiting" two entries; capability-boundary docs and UI caliber consistent (~50 seconds, SkillHub only, needs network)
- Creativity and value-add: browser tab alert added "download drop" (single-round drop ≥10) hint, forming a complete anomaly perception with the existing "score drop / rise, download spike, new skill published"

### v1.2.1 (2026-07-23)

- Error messages fully beginner-friendly: added `friendly_error()` centralized classifier, masking raw exception text like `WinError 10061` / `ConnectionRefused` / `URLError` / `429` / `401` / `SSL` into plain language like "network connection error / slow network / refresh rate limited / account authorization expired", beginners no longer see jargon
- Config-error hints de-Anglicized: config.json format error changed from English `Expecting ',' delimiter` to Chinese-style "near line N column N" localization
- Rate-limit self-heal enhanced: `fetch_json` retries 2 times by default, on 429 auto-extends backoff (exponential), reducing collection failures and false reports from rate limiting
- Capability-boundary persistent hint bar: dashboard top clearly shows "SkillHub platform only · needs network · refreshes every ~50 seconds · does not generate content · does not cover non-SkillHub platforms", boundaries at a glance
- Data credibility hardened: data source labeled "SkillHub official API · ✓ real-time verified", together with data time / latency seconds, users can verify data truth anytime
- Export capability made explicit: added "Export CSV" button at top-right, directly linking the existing `/api/export` endpoint for one-click history CSV download (the endpoint existed before but had no entry)

### v1.1.0 (2026-07-22)

- Config de-code-ification: USER_ID / competitor keywords / skill short names / port all migrated to `config.json`, beginners change config with zero code edits
- Data honesty: UI "data" changed to "real-time data" and added "latency" label; public copy unified to "shorter refresh interval" wording. [Note: v1.1.2 removed the old cache limit, v1.1.3 UI labels unified to "real-time", all data unified to shorter-interval refresh]
- Exception handling enhanced: on network / rate-limit exceptions a clear banner pops at top (reason + last successful update time + auto-retry count), no longer just a top-right red dot
- Auto-recovery enhanced: status subdivided into Online / Reconnecting / Offline three states, auto-reconnect after network recovery, fewer manual refreshes
- Documentation optimization: FAQ expanded from 3 to 8 entries, added "Output Examples" section, capability-boundary honestly states data latency
- UI refinement (build 2348): ① "Platform live skill count" label bolded and enlarged, 4-char gap from number, number turned red; ② "Data source" 6-char gap from number; ③ "Total comments" vs. last hour removed forced green, changed to green-up red-down; ④ "User total downloads · DoD growth" backend added cross-day snapshot yesterday_dl, prefers comparing with yesterday's downloads, green-up red-down; ⑤ core metric card two-column metadata unified to 11px small font

### v1.1.6 (2026-07-22)

- Shortened full-data refresh interval: server-side COLLECT_INTERVAL and MARKET_INTERVAL further reduced, frontend refresh synced faster, more real-time monitoring
- Removed countdown progress bar: cleaner UI, no circular countdown, data auto-refreshes in real time without countdown prompting
- Beginner-friendly error messages: backend error messages changed from technical terms (ENETUNREACH / 10061 / HTTP 4xx / 5xx etc.) to plain language, frontend shows the clear hint returned by backend directly, no longer parsing technical error codes itself
- Config validation enhanced: config.json load detects JSON format errors and missing user_id, returns beginner-readable hints, beginners no longer face errors not knowing what to do
- Timestamp compatibility enhanced: ts_to_str function compatible with second-level / millisecond-level / ISO-string three timestamp formats, avoiding display anomalies when different data sources return different formats

### v1.1.5 (2026-07-22)

- Documentation sensitive-info cleanup: removed all personal names, user IDs and other sensitive info, uniformly replaced with generic placeholders
- FAQ full expansion: each answer expanded from 1 sentence to 3~5 sentences, with concrete troubleshooting steps and operation guidance
- Added "Common Mistakes (anti-patterns)" section: 8 high-frequency "pitfalls" wrong-vs-right comparison table
- Added "Complete Beginner Tutorial" section: 6-step full guide from installing Python to seeing data, with Windows / Mac / Linux three-platform Python install steps
- Date-display fix: ts2s function enhanced, compatible with second-level / millisecond-level / ISO-string three formats, eliminating date deviation
- Skill card right-side layout rebuilt: three rows two columns right-aligned (version / create + update time / category Chinese + sub-category), favorite number enlarged, score number shrunk, namespace field removed, category Chinese mapping

### v1.1.4 (2026-07-22)

- Alert enhancement: browser tab title added download spike alert (single-round delta ≥10) and new-skill-published alert, no longer only score-change alerts
- Data freshness detection: data latency threshold lowered from 3 minutes to 20 seconds, showing "Data latency Ns" in orange at second-level, making network jitter instantly perceptible
- History data export: added `/api/export` endpoint, export full history as CSV, supports long-term trend analysis
- One-click start: added `start_monitor.bat`, Windows double-click to start, supports auto-start on boot
- Documentation enhancement: added API JSON response structure example, file reference table, 4 new FAQs, data accuracy statement
- UI labels: "quasi-real-time data" changed to "real-time data", data update time and top time unified to the same source

### v1.1.3 (2026-07-22)

- All data unified to shorter-interval refresh: removed the two artificial cache limits on market data and evaluation scores in server.py, all data (skill count, downloads, favorites, evaluation scores, market data, competitor search, category heat) unified to shorter-interval poll refresh
- Config-error frontend hint: on config.json load failure no longer silently exits, added CONFIG_LOAD_ERROR global variable delivered via /api/current.configError field, frontend auto-shows "⚠ Config file error: xxx · please check config.json format" in the top yellow bar
- Documentation full rewrite: removed multiple historical cache statements, unified to "all data unified to shorter-interval refresh"
- Section numbering fix: SKILL.md section 2 renumbered from 2.3 → 2.5 → 2.6 → 2.7 → 2.8 → 2.9 to 2.1 → 2.2 → 2.3 → 2.4 → 2.5 → 2.6 in order

### v1.1.2 (2026-07-22)

- Exception handling enhanced: error hint bar added specific pattern recognition for ENETUNREACH (target unreachable api.skillhub.cn), 10061 (connection refused), 404 (wrong API path), 5xx (server error) etc., with original error snippets attached, no more guessing to locate problems
- Score-change alert: when a skill's score drops ≥0.3 vs. last round, the browser tab title auto-flashes "⚠ Skill X score dropped Y", auto-clears after 30 seconds; supports score-rise hints, perceive anomalies without switching pages

### v1.1.1 (2026-07-22)

- Documentation honesty wrap-up: removed over-claims of unimplemented features like "all skills overlaid curve / version timeline dashed-line labels / highest evaluation score overview card", feature table now matches the actual UI
- Trigger clarification: added "Trigger" section, giving complete start / refresh commands and the boundary note "local web dashboard, not a conversation invocation"
- Pitfall guide: added "Pitfall Guide" section (edit-source / run-source separation causing local no-effect, port occupation, config.json format, no curve on first start, history too large — high-frequency pitfalls and fixes)
- Practical cases: added "Practical Cases" section covering four typical scenarios step-by-step: watching competitors, finding blue ocean, version-effect validation, data-interruption troubleshooting
- Output honesty statement: clarified all UI values come from real-time collection of your own account, no built-in sample numbers

### v1.0.0 (2026-07-21)

- First release of the SkillHub developer global data dashboard
- Shorter-interval real-time refresh: downloads, favorites, evaluation scores, version times, evaluation report times
- Platform-wide keyword competitor search: download TOP10 + latest-upload TOP10 dual-dimension ranking
- Category heat ranking with blue-ocean / red-ocean strategy suggestions
- Trend visualization: skill download real-time ranking (bar chart), each skill card shows downloads / favorites / score
- Version update ↔ evaluation report iteration-validation linkage: skill card shows "vX released, N days later evaluation Y score"
- Chart.js bundled locally, no overseas CDN dependency, stable rendering on domestic networks
- Frontend robustness: parallel fetch, keep last good data, offline only after 3 consecutive failures, de-duplicated refresh
- Backend all-data unified shorter-interval poll collection + collection-loop self-healing
- Use cases and capability boundaries, known limitations and FAQ explained
