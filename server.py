"""
SkillHub Info & Decision Platform - Backend Server
Personal skill monitoring + competitor analysis + market insight + version tracking
"""
import http.server
import json
import urllib.request
import urllib.error
import threading
import time
import os
import re

# ========== Config ==========
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
CFG = {}
CONFIG_LOAD_ERROR = ""
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as _f:
        CFG = json.load(_f)
except Exception as _cfg_ex:
    CFG = {}
    _raw_msg = str(_cfg_ex)
    if "Expecting" in _raw_msg or "char" in _raw_msg:
        import re as _re
        _m = _re.search(r"line (\d+) column (\d+)", _raw_msg)
        _loc = ("No." + _m.group(1) + "line " + _m.group(2) + "column nearby") if _m else "somewhere"
        CONFIG_LOAD_ERROR = "config.json format error (" + _loc + "): check that commas, quotes, and brackets are paired; validate online at jsonlint.com"
    else:
        CONFIG_LOAD_ERROR = "Cannot read config.json: confirm the file exists and is not corrupted"
PORT = int(CFG.get("port", 8866))
USER_ID = CFG.get("user_id", "user_YOUR_ID_HERE")
if USER_ID == "user_YOUR_ID_HERE":
    CONFIG_LOAD_ERROR = "User ID not configured | Open config.json and set user_id to your SkillHub user ID (log in to skillhub.cn -> Profile -> the part after /user/ in the URL)"
    if not CONFIG_LOAD_ERROR:
        CONFIG_LOAD_ERROR = "User ID not configured"
API_BASE = "https://api.skillhub.cn"
COLLECT_INTERVAL = 50
MAX_HISTORY = 720
MARKET_INTERVAL = 50      # Market data refreshed every 50s
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")
MARKET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "market_data.json")
PUBLISH_STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "publish_status.json")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://skillhub.cn",
    "Referer": "https://skillhub.cn/",
}

# ========== global state ==========
history = {"timestamps": [], "skills": {}, "followers": [], "totalComments": []}
market_data = {"categories": [], "showcase": [], "competitors": {}, "analysis": {}}
user_info = {}
collect_count = 0
last_error = None
LAST_OK = [time.time()]  # Timestamp of last successful collection; freeze watchdog uses this to decide whether self-healing restart is needed
data_lock = threading.Lock()
market_lock = threading.Lock()
eval_cache = {}  # slug -> {"score","createdAt","time"} Evaluation-score cache, reduces APIpressure
# Comment-count cache: the stats.comments endpoint is always 0; real counts come from the 'total' field of /api/v1/skills/{slug}/comments
comment_counts_cache = {}
comment_fetch_counter = [0]
COMMENT_FETCH_EVERY = 6  # Refresh comment counts every 6 collection cycles (~5 min) to avoid rate-limit-induced freezes; forced on first cycle


# Publish status (tracked locally): the public API does not expose review status (under security review / published).
# The publish script writes publish_status.json (slug -> status), or the user updates it manually after confirmation.
publish_status = {}
def load_publish_status():
    global publish_status
    try:
        with open(PUBLISH_STATUS_FILE, "r", encoding="utf-8") as f:
            publish_status = json.load(f)
    except Exception:
        publish_status = {}

# ========== Frontend build number (used for version self-check; avoids cached old frontend causing "fake offline")==========
def get_dashboard_build():
    """ from dashboard.html Extract 'buildXXXX' number as the frontend version id; falls back if the file is missing 0"""
    try:
        fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")
        with open(fp, "r", encoding="utf-8") as f:
            txt = f.read()
        m = re.search(r"build(\d+)", txt)
        return int(m.group(1)) if m else 0
    except Exception:
        return 0

# ========== tool ==========
def fetch_json(url, method="GET", body=None, retries=2, backoff=1.0):
    """Call the SkillHub API; auto-retry + backoff on transient connection-refused (WinError 10061) / timeout / rate-limit.
    Rate-limit (429) auto-extends backoff, reducing collection failures and false alarms"""
    last_exc = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers, method=method)
            if body:
                req.data = json.dumps(body).encode()
                req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last_exc = e
            # Rate limit: extend backoff to avoid frequent hard hits
            if e.code == 429 and attempt < retries - 1:
                time.sleep(backoff * 3 * (attempt + 1))
            elif attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
        except Exception as e:
            last_exc = e
            if attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
    raise last_exc

def friendly_error(e):
    """Map collection exceptions to beginner-readable plain language; never expose raw exception text / tech stack"""
    em = str(e).lower()
    et = type(e).__name__
    if any(k in str(e) for k in ("10061", "10054", "WinError", "ConnectionRefused", "ConnectionReset", "NameResolution", "getaddrinfo", "[Errno")) or "URLError" in et or "ConnectionError" in et:
        return "Network connection error: cannot reach SkillHub temporarily; last good data retained, system auto-retries every ~50s"
    if "timeout" in em or "timed out" in em:
        return "Slow network: server response timed out; last good data retained, system is auto-retrying"
    if "429" in str(e) or "rate" in em or "Requests too frequent" in str(e) or "too many" in em:
        return "Rate-limited due to high refresh frequency: system has auto-slowed down, please wait a moment"
    if "401" in str(e) or "403" in str(e) or "unauthorized" in str(e) or "forbidden" in em:
        return "Account authorization invalid: check that user_id in config.json is correct"
    if "404" in str(e):
        return "API endpoint changed: please contact the skill developer to update"
    if "ssl" in em or "certificate" in em:
        return "Network security check failed: check your local network proxy or certificate settings"
    return "Data fetch failed: last good data retained, system will auto-retry (details logged on server)"


def ts_to_str(ts):
    if not ts: return ""
    try:
        from datetime import datetime, timezone, timedelta
        tz = timezone(timedelta(hours=8))
        if isinstance(ts, str):
            if "-" in ts:
                try:
                    d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    return d.astimezone(tz).strftime("%y-%m-%d %H:%M")
                except:
                    return ts[:16]
            ts = float(ts)
        if ts < 1e12:
            ts = ts * 1000
        d = datetime.fromtimestamp(ts/1000, tz)
        return d.strftime("%y-%m-%d %H:%M")
    except:
        return str(ts)[:16]

def _last_valid(arr):
    for v in reversed(arr):
        if v is not None: return v
    return None

def calc_eval_score(dims):
    """five dimensions→sub-dimension averages→five-dimension overall average"""
    dim_avgs = []
    for d_key, d_val in dims.items():
        if isinstance(d_val, dict) and "items" in d_val:
            subs = [iv["score"] for iv in d_val["items"].values()
                    if isinstance(iv, dict) and "score" in iv and isinstance(iv["score"], (int, float))]
            if subs:
                dim_avgs.append(sum(subs)/len(subs))
    return round(sum(dim_avgs)/len(dim_avgs), 2) if dim_avgs else None

def calc_security_status(sec_reports):
    """Derive publish/security status from the skill detail's securityReports (source-code security scan: keen/sanbu etc.)
    Returns: Under Security Review / Security Passed / Security Risk / - (no data)"""
    if not isinstance(sec_reports, dict) or not sec_reports:
        return "—"
    scanning = False
    risk = False
    for scanner, rep in sec_reports.items():
        if not isinstance(rep, dict):
            continue
        st = str(rep.get("status", "")).lower()
        if st in ("scanning", "pending", "running", "processing", "reviewing"):
            scanning = True
        elif st in ("malicious", "danger", "risk", "unsafe", "blocked"):
            risk = True
    if risk:
        return "Security Risk"
    if scanning:
        return "Under Security Review"
    # the rest (including benign / passed / safe) is treated as having passed security scan
    return "Security Passed"

# ========== Personal skill collection ==========
def collect_self_data():
    global collect_count, last_error, user_info
    from datetime import datetime, timezone, timedelta
    from concurrent.futures import ThreadPoolExecutor, as_completed
    ts = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    try:
        load_publish_status()  # Reload local publish status on every collection; user edits  publish_status.json  after10s for the web page to take effect
        # userinfo + skill list — Concurrent fetch; do not overwrite on failure user_info(keep last successful value)
        skills_list = []
        _pool = ThreadPoolExecutor(max_workers=4)
        try:
            _f_user = _pool.submit(fetch_json, f"{API_BASE}/api/v1/users/{USER_ID}")
            _f_skills = _pool.submit(fetch_json, f"{API_BASE}/api/v1/users/{USER_ID}/skills?page=1&pageSize=20")
            for _f, _name in [(_f_user,"user"),(_f_skills,"skill list")]:
                try:
                    _r = _f.result(timeout=15)
                    if _name == "user":
                        user_info = _r.get("user", {})
                    else:
                        skills_list = _r.get("skills", [])
                except Exception as _e:
                    print(f"[{ts}] {_name} fetch failed: {_e}")
        finally:
            _pool.shutdown(wait=False)  # Do not wait for background threads, to prevent freezing

        # Skill details - concurrent fetch, 20s total timeout
        skill_details = {}
        if skills_list:
            _pool2 = ThreadPoolExecutor(max_workers=4)
            try:
                _futures = {sk["slug"]: _pool2.submit(fetch_json, f"{API_BASE}/api/v1/skills/{sk['slug']}") for sk in skills_list}
                for _slug, _f in _futures.items():
                    try:
                        skill_details[_slug] = _f.result(timeout=15)
                    except Exception:
                        skill_details[_slug] = None
            finally:
                _pool2.shutdown(wait=False)

                # Comment collection: stats.comments always0, use the dedicated list endpoint to get  total(throttled, forced on first cycle)
                comment_fetch_counter[0] += 1
                _do_fetch_cm = (comment_fetch_counter[0] == 1) or (comment_fetch_counter[0] % COMMENT_FETCH_EVERY == 0)
                if _do_fetch_cm and skills_list:
                    _poolc = ThreadPoolExecutor(max_workers=4)
                    try:
                        _cf = {sk["slug"]: _poolc.submit(fetch_json, f"{API_BASE}/api/v1/skills/{sk['slug']}/comments?pageSize=1") for sk in skills_list}
                        for _slug, _f in _cf.items():
                            try:
                                _cj = _f.result(timeout=12)
                                if isinstance(_cj, dict) and "total" in _cj:
                                    comment_counts_cache[_slug] = int(_cj.get("total", 0) or 0)
                            except Exception:
                                pass  # Keep last cached value to ensure smoothness
                    finally:
                        _poolc.shutdown(wait=False)


        if skills_list:
            with data_lock:
                history["timestamps"].append(ts)
                if len(history["timestamps"]) > MAX_HISTORY:
                    history["timestamps"] = history["timestamps"][-MAX_HISTORY:]
                # Followers: a user-level metric tracked on its own timeline, used for "vs last hour" comparison
                history.setdefault("followers", [])
                history.setdefault("totalComments", [])
                history["followers"].append(user_info.get("followersCount", 0))
                if len(history["followers"]) > MAX_HISTORY:
                    history["followers"] = history["followers"][-MAX_HISTORY:]

            for sk in skills_list:
                slug = sk["slug"]
                detail = skill_details.get(slug)
                stats = detail.get("skill",{}).get("stats",{}) if detail else {}

                if slug not in history["skills"]:
                    history["skills"][slug] = {"name":"","downloads":[],"stars":[],"version":[],"versionUpdatedAt":[],"evalScore":[],"evalTime":[],"security":[],"subCategories":[],"claimState":[],"verified":[],"createdAt":[],"comments":[],"category":[],"namespace":[],"requiresKey":[]}

                hs = history["skills"][slug]
                # Compatible with old history.json: backfill new field keys to avoid KeyError and complete auto-migration
                for _k in ("subCategories","claimState","verified","createdAt","comments","category","namespace","requiresKey"):
                    hs.setdefault(_k, [])
                hs["name"] = sk["name"]
                hs["downloads"].append(stats.get("downloads", sk.get("downloads",0)))
                hs["stars"].append(stats.get("stars", sk.get("stars",0)))
                hs["version"].append(sk.get("version",""))
                hs["versionUpdatedAt"].append(sk.get("updatedAt",""))
                # Publish status uses local precise tracking (publish_status.json), no longer relying on inaccurate securityReports source-scan status
                hs.setdefault("security", []).append(publish_status.get(slug, "Published"))

                # New: static / slow-changing metadata and comment counts needed by the core metric cards
                sci = detail.get("skill",{}) if detail else {}
                hs["subCategories"].append(sci.get("subCategories", []))
                hs["claimState"].append(sci.get("claim_state", ""))
                hs["verified"].append(bool(sci.get("verified", False)))
                hs["createdAt"].append(sci.get("createdAt", ""))
                hs["comments"].append(comment_counts_cache.get(slug, 0))

                # category / namespace / requiresKey (static metadata, fetched with detail and list)
                hs["category"].append(sci.get("category", ""))
                _ns = sk.get("namespace", {}) or {}
                hs["namespace"].append(_ns.get("canonicalName", "") if isinstance(_ns, dict) else "")
                _lbl = sci.get("labels", {}) or {}
                hs["requiresKey"].append(str(_lbl.get("requires_api_key", "false")) if isinstance(_lbl, dict) else "false")

                # Evaluation score: only hit the API once every 5 min, otherwise reuse cache to reduce rate-limit risk
                lev = _last_valid(hs["evalScore"])
                let = _last_valid(hs.get("evalTime",[]))
                now = time.time()
                cached = eval_cache.get(slug)
                ev = None
                if (not cached) or (now - cached.get("time", 0) > 10):
                    try:
                        ed = fetch_json(f"{API_BASE}/api/v1/skills/{slug}/evaluation")
                        if ed and ed.get("dimensions"):
                            sc = calc_eval_score(ed["dimensions"])
                            ev = {"score": sc, "createdAt": ed.get("createdAt", "")}
                            eval_cache[slug] = {"score": sc, "createdAt": ed.get("createdAt", ""), "time": now}
                    except:
                        ev = None
                if ev is None and cached:
                    ev = {"score": cached["score"], "createdAt": cached.get("createdAt", "")}
                if ev and ev.get("score") is not None:
                    hs["evalScore"].append(ev["score"])
                    hs["evalTime"].append(ev.get("createdAt", ""))
                elif lev is not None:
                    hs["evalScore"].append(lev)
                    hs["evalTime"].append(let)
                else:
                    hs["evalScore"].append(None)
                    hs["evalTime"].append(None)

                for key in ["downloads","stars","version","versionUpdatedAt","evalScore","evalTime","security","subCategories","claimState","verified","createdAt","comments","category","namespace","requiresKey"]:
                    if len(hs[key]) > MAX_HISTORY:
                        hs[key] = hs[key][-MAX_HISTORY:]

                # Total comments: sum of all skills' comments, tracked on a timeline for "vs last hour"
                history.setdefault("totalComments", [])
                _tc = 0
                for _slug in history["skills"]:
                    _h = history["skills"].get(_slug)
                    if _h and _h.get("comments"):
                        _v = _h["comments"][-1]
                        if _v is not None:
                            _tc += _v
                history["totalComments"].append(_tc)
                if len(history["totalComments"]) > MAX_HISTORY:
                    history["totalComments"] = history["totalComments"][-MAX_HISTORY:]

            try:
                with open(HISTORY_FILE,"w",encoding="utf-8") as f:
                    json.dump(history, f, ensure_ascii=False)
            except: pass

        # Yesterday download baseline: a cross-day snapshot for the frontend "total downloads vs yesterday" comparison
        try:
            _now_bj = datetime.now(timezone(timedelta(hours=8)))
            _today_str = _now_bj.strftime("%Y-%m-%d")
            _total_dl_now = 0
            _dl_by_skill_now = {}
            for _slug2, _hs in history["skills"].items():
                _d = _hs.get("downloads")
                if _d:
                    _v = _d[-1]
                    if _v is not None:
                        _total_dl_now += _v
                        _dl_by_skill_now[_slug2] = _v
            _prev_date = history.get("last_date")
            if _prev_date is None:
                history["last_date"] = _today_str
            elif _prev_date != _today_str:
                if history.get("last_total_dl") is not None:
                    history["yesterday_dl"] = history["last_total_dl"]   # cumulative total(yesterday23:59/today00:00snapshot,for day-over-day and daily increment)
                if history.get("last_dl_by_skill"):
                    history["yesterday_dl_by_skill"] = dict(history["last_dl_by_skill"])  # Per-skill cross-day snapshot for the 'daily ranking' chart
            history["last_date"] = _today_str
            history["last_total_dl"] = _total_dl_now
            history["last_dl_by_skill"] = _dl_by_skill_now
        except Exception:
            pass

        collect_count += 1
        last_error = None
        LAST_OK[0] = time.time()
        print(f"[{ts}] personal data #{collect_count}")
    except Exception as e:
        last_error = friendly_error(e)
        print(f"[{ts}] collection failed: {last_error}")

# ========== Market Data Collection ==========
def collect_market_data():
    """Collect market data: categories+showcase+competitor"""
    global market_data
    try:
        # Categories
        cats = fetch_json(f"{API_BASE}/api/v1/categories")
        cat_items = cats.get("items", [])

        # Showcase featured
        showcase = fetch_json(f"{API_BASE}/api/v1/showcase/featured")
        showcase_skills = showcase.get("skills", [])

        # Group stats by category
        cat_stats = {}
        for c in cat_items:
            cat_stats[c["key"]] = {"name": c["name"], "count": 0, "total_dl": 0, "total_st": 0, "skills": []}

        for sk in showcase_skills:
            cat = sk.get("category", "other")
            if cat in cat_stats:
                cat_stats[cat]["count"] += 1
                cat_stats[cat]["total_dl"] += sk.get("downloads", 0)
                cat_stats[cat]["total_st"] += sk.get("stars", 0)
                cat_stats[cat]["skills"].append({
                    "name": sk.get("name",""),
                    "slug": sk.get("slug",""),
                    "downloads": sk.get("downloads",0),
                    "stars": sk.get("stars",0),
                    "score": sk.get("score"),
                    "ownerName": sk.get("ownerName",""),
                    "version": sk.get("version",""),
                })

        # Hotness ranking: by total downloads
        hotness = []
        for key, st in cat_stats.items():
            if st["count"] > 0:
                hotness.append({
                    "category": key,
                    "name": st["name"],
                    "skill_count": st["count"],
                    "avg_dl": round(st["total_dl"]/st["count"]) if st["count"] else 0,
                    "total_dl": st["total_dl"],
                })
        hotness.sort(key=lambda x: -x["avg_dl"])

        # Competitor matching engine v2: name + description dual-match + core-keyword filter + exclude words + auto-derivation (generic, no fixed competitor list)
        import urllib.parse

        # keyword_map optional fields per skill:
        #   search: API search keyword list
        #   name_filter: name-match words (any hit on skill name makes it a candidate)
        #   desc_filter: description-match words (any hit on skill description makes it a candidate; defaults to search words to avoid vague-word mismatches)
        #   core_filter: core professional keyword (once set, must match to ensure competitor relevance)
        #   strict_name: True = core_filter must appear in the skill name (e.g. labor-dispute niche, excludes generic legal skills)
        #   desc_exclude: description exclude words (any hit on description removes it; used to disambiguate polysemous abbreviations)
        #   exclude: exclude words (any hit on name removes it, e.g. unrelated domains like MBTI / marriage)
        keyword_map = dict(CFG.get("keyword_map", {}) or {})

        # Auto-derivation: skills not covered by keyword_map get search/filter words auto-generated from their display name
        # -- Different users have different skills, so competitors differ automatically; no manual unified competitor list needed
        _skill_names_cfg = CFG.get("skill_names", {}) or {}
        for _slug, _disp in _skill_names_cfg.items():
            if _slug in keyword_map:
                continue
            _disp = (_disp or "").strip()
            if not _disp:
                continue
            keyword_map[_slug] = {
                "search": [_disp],
                "name_filter": [_disp],
                "desc_filter": [_disp],
            }

        competitors = {}
        for slug, config in keyword_map.items():
            kw_list = config.get("search", [])
            name_filters = config.get("name_filter", [])
            desc_filters = config.get("desc_filter") or list(kw_list)
            core_filters = config.get("core_filter", [])
            strict_name = bool(config.get("strict_name"))
            excludes = config.get("exclude", [])
            desc_excludes = config.get("desc_exclude", [])
            all_matches = {}

            for kw in kw_list:
                try:
                    encoded = urllib.parse.quote(kw)
                    url = f"{API_BASE}/api/skills?keyword={encoded}&page=1&pageSize=20&sortBy=downloads&order=desc"
                    resp = fetch_json(url)
                    time.sleep(0.2)  # Throttle: add a gap between keyword searches to reduce rate-limiting
                    skills = []
                    if isinstance(resp, dict):
                        skills = resp.get("data", {}).get("skills", [])
                    for sk in skills:
                        sk_slug = sk.get("slug", "")
                        if sk_slug == slug or sk_slug in _skill_names_cfg:
                            continue  # Exclude self and own other skills
                        sk_name = sk.get("name", "") or ""
                        sk_desc = sk.get("description", "") or ""
                        name_lc = sk_name.lower()
                        desc_lc = sk_desc.lower()

                        # 1 Exclude words: any name hit removes it directly (e.g. unrelated skills like 'MBTI test')
                        if any(ex.lower() in name_lc for ex in excludes):
                            continue
                        if desc_excludes and any(ex.lower() in desc_lc for ex in desc_excludes):
                            continue  # Description hit on exclude word: disambiguate (e.g. NPD = product-dev / chromatograph-detector unrelated skills)

                        # 2 Name + description dual match: name hits name_filter OR description hits desc_filter
                        matched_kw = None
                        matched_in = None
                        for nf in name_filters:
                            if nf.lower() in name_lc:
                                matched_kw, matched_in = nf, "name"
                                break
                        if not matched_kw:
                            for df in desc_filters:
                                if df.lower() in desc_lc:
                                    matched_kw, matched_in = df, "description"
                                    break
                        if not matched_kw:
                            continue

                        # 3 Core-keyword check: ensure competitor is strongly relevant to this skill
                        #    strict_name=True (e.g. labor-dispute niche): core word must appear in the name,
                        #    other legal skills mentioning labor in description still do not count as competitors
                        if core_filters:
                            _scope = name_lc if strict_name else (name_lc + " " + desc_lc)
                            if not any(cf.lower() in _scope for cf in core_filters):
                                continue

                        if sk_slug not in all_matches:
                            all_matches[sk_slug] = {
                                "name": sk_name,
                                "slug": sk_slug,
                                "downloads": sk.get("downloads", 0),
                                "stars": sk.get("stars", 0),
                                "ownerName": sk.get("ownerName", sk.get("namespace", {}).get("displayName", "")),
                                "matchedKw": matched_kw,
                                "matchedIn": matched_in,
                            }
                except Exception as e:
                    print(f"  [!] competitor search {kw} failed: {e}")

            print(f"  [{slug}] name+description dual match found {len(all_matches)} competitors")

            # take downloadsTOP15, then fetch details and split into two dimensions
            top_dl_raw = sorted(all_matches.values(), key=lambda x: -x["downloads"])[:15]

            # Fetch details for each competitor (createdAt/updatedAt)
            import time as _time
            for sk in top_dl_raw:
                try:
                    detail = fetch_json(f"{API_BASE}/api/v1/skills/{sk['slug']}")
                    sk["createdAt"] = detail.get("skill", {}).get("createdAt", "")
                    sk["updatedAt"] = detail.get("skill", {}).get("updatedAt", "")
                    _time.sleep(0.3)
                except:
                    sk["createdAt"] = ""
                    sk["updatedAt"] = ""

            # Dimension 1: Top 10 by downloads
            by_dl = sorted(top_dl_raw, key=lambda x: -x["downloads"])[:10]

            # Dimension 2: Top 10 by earliest-upload time (newest)
            by_new = sorted([m for m in top_dl_raw if m.get("createdAt")], key=lambda x: -(x.get("createdAt") or 0))[:10]

            competitors[slug] = {"byDownloads": by_dl, "byNewest": by_new}
            print(f"  [{slug}] Top10 downloads: {[m['downloads'] for m in by_dl]} | Newest: {[m.get('createdAt','') for m in by_new[:3]]}")

        # Platform live skill total (current number of Skills): data.total from an empty-keyword search
        # Keep last value as fallback; do not zero out when API fails
        total_skills = market_data.get("total_skills", 0)
        try:
            total_resp = fetch_json(f"{API_BASE}/api/skills?keyword=&page=1&pageSize=1&sortBy=downloads&order=desc")
            if isinstance(total_resp, dict):
                _new_total = (total_resp.get("data", {}) or {}).get("total", 0) or 0
                if _new_total > 0:
                    total_skills = _new_total
        except Exception as e:
            print(f"[market] failed to get skill total (kept last value {total_skills}): {e}")

        with market_lock:
            market_data = {
                "categories": cat_items,
                "showcase": showcase_skills,
                "cat_stats": cat_stats,
                "hotness": hotness,
                "competitors": competitors,
                "total_showcase": len(showcase_skills),
                "total_skills": total_skills,
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            try:
                with open(MARKET_FILE,"w",encoding="utf-8") as f:
                    json.dump(market_data, f, ensure_ascii=False)
            except: pass

        print(f"[market] categories {len(cat_items)} showcase {len(showcase_skills)} hotness {len(hotness)}")

    except Exception as e:
        print(f"[market] collection failed: {e}")

# ========== collection loop ==========
def collector_loop():
    # First personal-data collection (fast, non-blockingHTTPservice); exceptions do not affect the restHTTPservice and loop
    try:
        collect_self_data()
    except Exception as _e:
        print(f"[{time.strftime('%H:%M:%S')}] first collection error (caught, continuing): {_e}")
    # Lazy-load history if present
    if last_error and os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE,"r",encoding="utf-8") as f:
                loaded = json.load(f)
            with data_lock:
                history.clear(); history.update(loaded)
                history.setdefault("followers", [])
                history.setdefault("totalComments", [])
        except: pass
    if os.path.exists(MARKET_FILE):
        try:
            with open(MARKET_FILE,"r",encoding="utf-8") as f:
                loaded = json.load(f)
            with market_lock:
                market_data.clear(); market_data.update(loaded)
        except: pass
    # Delay market collection by 10s (avoid blocking HTTP startup)
    def delayed_market():
        time.sleep(0.5)
        collect_market_data()
    threading.Thread(target=delayed_market, daemon=True).start()

    market_counter = 0
    while True:
        try:
            time.sleep(COLLECT_INTERVAL)
            # Collection with timeout: 35s must complete within the timeout, else skip this round (freeze watchdog self-heals)
            _ct = threading.Thread(target=collect_self_data, daemon=True)
            _ct.start()
            _ct.join(timeout=35)
            if _ct.is_alive():
                print(f"[{time.strftime('%H:%M:%S')}] collection timeout (>35s), skipping this round")
            market_counter += 1
            if market_counter * COLLECT_INTERVAL >= MARKET_INTERVAL:
                collect_market_data()
                market_counter = 0
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] collection loop error (self-healed): {e}")
            time.sleep(5)

# ========== HTTP API ==========
class MonitorHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.directory = os.path.dirname(os.path.abspath(__file__))
        super().__init__(*args, directory=self.directory, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control','no-cache,no-store,must-revalidate')
        self.send_header('Pragma','no-cache')
        self.send_header('Expires','0')
        self.send_header('Vary','Accept-Encoding')
        super().end_headers()

    def _gzip_compress(self, body):
        """If the client supports  gzip then compress body bytes; compression level  1 speed first (1.3MB history  in localhost compress to ~150KB)"""
        try:
            ae = self.headers.get('Accept-Encoding','')
            if 'gzip' in ae.lower():
                import gzip
                return gzip.compress(body, compresslevel=1)
        except Exception:
            pass
        return None  # not compressed

    def write_response(self, body, content_type):
        gz = self._gzip_compress(body)
        if gz:
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Encoding','gzip')
            self.send_header('Content-Length', str(len(gz)))
            self.end_headers()
            self.wfile.write(gz)
        else:
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def do_GET(self):
        raw = self.path
        path = raw.split("?")[0] if "?" in raw else raw
        routes = {
            "/api/current": self.handle_current,
            "/api/history": self.handle_history,
            "/api/status": self.handle_status,
            "/api/market": self.handle_market,
            "/api/competitors": self.handle_competitors,
            "/api/version": self.handle_version,
            "/api/config": self.handle_config,
            "/api/export": self.handle_export,
        }
        if path in routes:
            routes[path]()
        elif path.startswith("/api/versions/"):
            self.path = self.path
            self.handle_versions()
        elif path in ("/", "/index.html", "/dashboard.html"):
            self.serve_file("dashboard.html")
        else:
            self.serve_file(path.lstrip("/"))

    def serve_file(self, filename):
        """Explicitly serve static files, bypassing SimpleHTTPRequestHandlerpath issue"""
        filepath = os.path.join(self.directory, filename)
        if not os.path.isfile(filepath):
            self.send_error(404)
            return
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            ct = "text/html; charset=utf-8"
            if filename.endswith(".css"): ct = "text/css"
            elif filename.endswith(".js"): ct = "application/javascript"
            elif filename.endswith(".json"): ct = "application/json"
            elif filename.endswith(".jpg") or filename.endswith(".jpeg"): ct = "image/jpeg"
            elif filename.endswith(".png"): ct = "image/png"
            # dashboard.html Frequently refreshed and large in size, gzip high gain
            self.write_response(content, ct)
        except Exception as e:
            self.send_error(500, str(e))

    def handle_current(self):
        with data_lock:
            result = {"timestamps":[], "skills":{}, "user": user_info, "configError": CONFIG_LOAD_ERROR, "shCount": market_data.get("total_skills", 0), "collectInterval": COLLECT_INTERVAL}
            if history["timestamps"]:
                result["timestamps"] = [history["timestamps"][-1]]
                for slug, hs in history["skills"].items():
                    result["skills"][slug] = {
                        "name": hs.get("name", ""),
                        "downloads": hs.get("downloads", [])[-1] if hs.get("downloads") else 0,
                        "stars": hs.get("stars", [])[-1] if hs.get("stars") else 0,
                        "version": hs.get("version", [])[-1] if hs.get("version") else "",
                        "versionUpdatedAt": hs.get("versionUpdatedAt", [])[-1] if hs.get("versionUpdatedAt") else "",
                        "evalScore": _last_valid(hs.get("evalScore", [])),
                        "evalTime": _last_valid(hs.get("evalTime", [])),
                        "security": _last_valid(hs.get("security", [])),
                        "subCategories": hs.get("subCategories", [])[-1] if hs.get("subCategories", []) else [],
                        "claimState": hs.get("claimState", [])[-1] if hs.get("claimState", []) else "",
                        "verified": hs.get("verified", [])[-1] if hs.get("verified", []) else False,
                        "createdAt": hs.get("createdAt", [])[-1] if hs.get("createdAt", []) else "",
                        "comments": hs.get("comments", [])[-1] if hs.get("comments", []) else 0,
                        "category": hs.get("category", [])[-1] if hs.get("category", []) else "",
                        "namespace": hs.get("namespace", [])[-1] if hs.get("namespace", []) else "",
                        "requiresKey": hs.get("requiresKey", [])[-1] if hs.get("requiresKey", []) else "false",
                    }
        self.send_json(result)

    def handle_history(self):
        with data_lock:
            self.send_json(json.loads(json.dumps(history)))

    def handle_status(self):
        self.send_json({
            "collectCount": collect_count,
            "lastError": last_error,
            "historyPoints": len(history["timestamps"]),
            "skills": list(history["skills"].keys()),
            "marketUpdated": market_data.get("updated_at",""),
        })

    def handle_version(self):
        # Frontend version self-check endpoint: returns the server-side  dashboard.html 's build number for the browser to compare and auto-reload
        self.send_json({
            "build": get_dashboard_build(),
            "serverTime": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

    def handle_config(self):
        self.send_json({"skill_names": CFG.get("skill_names", {})})

    def handle_market(self):
        with market_lock:
            self.send_json(market_data)

    def handle_competitors(self):
        with market_lock:
            self.send_json(market_data.get("competitors", {}))

    def handle_versions(self):
        path = self.path.split("?")[0]
        slug = path.split("/api/versions/")[-1] if "/api/versions/" in path else ""
        if not slug:
            self.send_json({"error": "missing slug"})
            return
        try:
            data = fetch_json(f"{API_BASE}/api/v1/skills/{slug}/versions")
            versions = data.get("versions", [])
            self.send_json({"slug": slug, "versions": versions})
        except Exception as e:
            self.send_json({"error": str(e)})

    def handle_export(self):
        """Export history data as CSV, supports long-term trend analysis"""
        import csv as _csv
        import io as _io
        buf = _io.StringIO()
        writer = _csv.writer(buf)
        writer.writerow(["timestamp", "skill_slug", "skill_name", "downloads", "favorites", "eval_score", "comments"])
        with data_lock:
            ts_list = history["timestamps"]
            for slug, hs in history["skills"].items():
                name = hs.get("name", [""])
                name = name[0] if name else ""
                dl_arr = hs.get("downloads", [])
                st_arr = hs.get("stars", [])
                sc_arr = hs.get("evalScore", [])
                cm_arr = hs.get("comments", [])
                for i in range(len(ts_list)):
                    writer.writerow([
                        ts_list[i],
                        slug,
                        name,
                        dl_arr[i] if i < len(dl_arr) else "",
                        st_arr[i] if i < len(st_arr) else "",
                        sc_arr[i] if i < len(sc_arr) else "",
                        cm_arr[i] if i < len(cm_arr) else "",
                    ])
        csv_data = buf.getvalue()
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="skillhub_history.csv"')
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(csv_data.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(csv_data.encode("utf-8"))

    def send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        # use gzip compress (history 1.3MB → ~100KB, transfer speed improved 10x+)
        self.write_response(body, "application/json; charset=utf-8")
        # no longer call self.end_headers()  and self.wfile.write(), because write_response handled
        # Backward-compatible with old callers: if not compressed, return the original way
        ae = self.headers.get('Accept-Encoding','')
        if 'gzip' not in ae.lower():
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass

# ========== Freeze watchdog ==========
def freeze_watchdog():
    """If more than  3*COLLECT_INTERVAL still no new data means the collection thread is stuck/freeze,
    Force-exit the process, handled by  start_monitor.sh 's while loop cleanly restarts (releasing first before restart 8866 port).
    completely eliminate"data stopped moving"long-term freeze."""
    while True:
        time.sleep(30)
        try:
            since = time.time() - LAST_OK[0]
            if since > 3 * COLLECT_INTERVAL:
                print(f"[{time.strftime('%H:%M:%S')}] freeze watchdog triggered: {int(since)}s since last success exceeds threshold {3*COLLECT_INTERVAL}s, forcing process restart to self-heal")
                os._exit(1)
        except Exception:
            pass

# ========== start ==========
def main():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE,"r",encoding="utf-8") as f:
                loaded = json.load(f)
            with data_lock:
                history.clear(); history.update(loaded)
                history.setdefault("followers", [])
                history.setdefault("totalComments", [])
            print(f"loaded history: {len(history['timestamps'])} points")
        except Exception as e:
            print(f"load history failed: {e}")

    load_publish_status()  # StartupImmediately load local publish status
    threading.Thread(target=collector_loop, daemon=True).start()
    threading.Thread(target=freeze_watchdog, daemon=True).start()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), MonitorHandler)
    print(f"\n{'='*50}")
    print(f"  SkillHub Info & Decision Platform v2.0")
    print(f"  Local: http://localhost:{PORT}")
    print(f"  Tablet: http://<local-IP>:{PORT}")
    print(f"{'='*50}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == "__main__":
    main()
