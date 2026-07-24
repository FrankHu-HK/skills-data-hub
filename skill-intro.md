# Skills-Data-Hub v1.2.4 — Product Introduction

> SkillHub developer global data monitoring and decision platform with a ~50-second refresh. Enter your user ID; all data is polled and refreshed on a unified ~50-second cycle, platform-wide keyword competitor search with dual-dimension ranking, category heat insight — a one-stop decision workflow.

## Table of Contents (quick navigation)

- [One-line Positioning](#one-line-positioning)
- [Capability Boundaries (read this first)](#capability-boundaries-read-this-first)
- [Product Positioning and Core Value](#product-positioning-and-core-value)
- [Core Features](#core-features)
- [Quick Start](#quick-start)
- [Customization](#customization)
- [Technical Specs](#technical-specs)

## Capability Boundaries (read this first)

> This tool **monitors only the SkillHub platform** skill data, **requires network** access, refreshes data every ~50 seconds (not real-time millisecond-level), **does not generate / rewrite skill content**, and does not cover non-SkillHub platform data. When offline the dashboard stops refreshing, but already-loaded data is retained.

## One-line Positioning

Turns SkillHub's backend data into a **~50-second-refresh decision screen**, letting you see your skills' performance anytime, watch competitors, and find blue oceans.

## Product Positioning and Core Value

A real-time data monitoring and intelligent operations analytics platform built for AI Skill developers, giving every skill its own "digital vital signs" and moving developers from passive waiting after release into the era of data-driven continuous optimization.

### Solving Core Pain Points

**1. Solving the "can't see real performance after publishing" problem**
Traditional Skill operations only see simple download data, unable to fully understand a skill's development state. This platform monitors followers, downloads, favorites, scores, rankings and other core metrics in real time, making growth trends clear at a glance.

**2. Solving the "no effect validation after iteration" problem**
Developers often face: after a version update, did it actually improve? Are users satisfied? Did the score improve? The platform innovatively designed linked monitoring of "version update time VS evaluation report update time", precisely tracking market feedback after each upgrade, forming a complete optimization closed loop.

**3. Solving the data-lag, can't-decide-in-real-time problem**
Adopts a unified ~50-second poll refresh for all data, clearly marks data freshness, and shows the skill's growth trajectory through dynamic number changes, trend curves, and dot trends, letting developers grasp Skill dynamics like analyzing stock quotes.

**4. Solving the "operations rely on experience, lack data basis" problem**
Through historical trend analysis, growth curves, and metric changes, it helps developers find growth opportunities, locate root causes, and use data to guide content optimization, feature upgrades, and operations strategy.

**5. Solving the "great Skills lack professional management tools" problem**
Future AI Skills will become important digital assets needing a data console like internet products. This platform provides professional, intelligent, visual management, letting developers continuously improve skill competitiveness.

### Core Value

Upgrades AI Skills from "a tool published once" to "an intelligent product that evolves continuously".
Use real-time data to insight value, use continuous iteration to create growth.

## Core Features

### 1. All data unified real-time ~50-second refresh

- All your skills: downloads (page-flip big number), favorites, evaluation score (blue), version publish time, evaluation report time
- Top overview: platform live skill count, today's total downloads, day-over-day growth, total favorites, total comments, follower count

### 2. Competitor analysis (dual-dimension)

- Based on platform-wide keyword search, skill name + skill description dual-field matching, assisted by core professional word / exclusion word filtering, precisely matching competitors for each skill; skills without configured keywords auto-derive from display name (each user's competitors differ automatically)
- Dimension 1: download TOP10
- Dimension 2: latest upload TOP10
- Each row contains: competitor name / downloads / favorites / update time / first-upload time

### 3. Market insight

- Category heat board (sorted by average downloads + star rating)
- Strategy suggestions: blue-ocean category recommendations, differentiation advantage, red-ocean warnings

### 4. Trend visualization

- Real-time download ranking bar chart
- Version number and evaluation score shown on every skill card, version update and evaluation report time linked

### 5. One-click CSV export

- The "Export CSV" button at top-right downloads the full history (timestamp / skill / downloads / favorites / score / comments) with one click, for long-term trend analysis in Excel / WPS, no command line needed.

### 6. Engineering features

- Python backend + HTML/Chart.js frontend, **zero external dependencies** (standard library only)
- PC / tablet cross-device real-time viewing on same WiFi
- Auto-detects your skills; personalization (user_id / short names / competitor keywords / port) all written to `config.json`, no code changes
- Built-in concurrency, request retry, cache bypass and other stability optimizations (all data unified ~50-second poll)
- Auto-recovery (v1.2.4): any collection round anomaly auto-retries keeping good data; 【Freeze Watchdog】 auto-restarts the process if no new data for >150 seconds + the daemon script releases the occupied port before start, completely eliminating "data stopped moving"

## Quick Start

1. Open `config.json` in the same directory, change `user_id` to your user ID
   - How to get it: log in to SkillHub → Profile → the part after `/user/` in the URL
2. Start: `cd Skills-Data-Hub && python server.py`
3. Open the dashboard:
   - PC: `http://localhost:8866`
   - Tablet: on same WiFi find your PC IP (cmd → `ipconfig`), open `http://<IP-address>:8866`

## Customization

- Skill short names: edit `skill_names` in `config.json`
- Competitor keywords: edit `keyword_map` in `config.json` (search terms + name_filter name filter + desc_filter description filter + core_filter core professional word + strict_name strict-name mode + exclude exclusion words)

## Technical Specs

- Language: Python 3.7+ (no pip dependency)
- Data source: SkillHub public API
- Service: ThreadingHTTPServer concurrency, all data unified ~50-second poll, /api/export CSV export, browser tab-bar alerts (score / downloads / new skill)
- Version: v1.2.5 (2026-07-24)
- Version labeling: v1.2.5 is the semantic version (public release number); the dashboard's internal "build number" (e.g. 2378) is only for frontend auto-reload detection and needs no attention
