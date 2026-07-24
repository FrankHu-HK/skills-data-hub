"""
SkillHub 信息决策平台 - 后端服务器
个人技能监控 + 竞品分析 + 市场洞察 + 版本追踪
"""
import http.server
import json
import urllib.request
import urllib.error
import threading
import time
import os
import re

# ========== 配置 ==========
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
        _loc = ("第" + _m.group(1) + "行第" + _m.group(2) + "列附近") if _m else "某处"
        CONFIG_LOAD_ERROR = "config.json 格式有误（" + _loc + "）：请检查逗号、引号、括号是否配对，可用 jsonlint.com 在线校验"
    else:
        CONFIG_LOAD_ERROR = "无法读取 config.json：请确认文件存在且未损坏"
PORT = int(CFG.get("port", 8866))
USER_ID = CFG.get("user_id", "user_YOUR_ID_HERE")
if USER_ID == "user_YOUR_ID_HERE":
    CONFIG_LOAD_ERROR = "未配置用户ID | 请打开 config.json，将 user_id 改为你的 SkillHub 用户ID（登录 skillhub.cn → 个人中心 → URL 中 /user/ 后面的部分）"
    if not CONFIG_LOAD_ERROR:
        CONFIG_LOAD_ERROR = "未配置用户ID"
API_BASE = "https://api.skillhub.cn"
COLLECT_INTERVAL = 50
MAX_HISTORY = 720
MARKET_INTERVAL = 50      # 市场数据50秒刷新
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")
MARKET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "market_data.json")
PUBLISH_STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "publish_status.json")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://skillhub.cn",
    "Referer": "https://skillhub.cn/",
}

# ========== 全局状态 ==========
history = {"timestamps": [], "skills": {}, "followers": [], "totalComments": []}
market_data = {"categories": [], "showcase": [], "competitors": {}, "analysis": {}}
user_info = {}
collect_count = 0
last_error = None
LAST_OK = [time.time()]  # 上次成功采集时间戳，冻结看门狗据此判断是否需要自愈重启
data_lock = threading.Lock()
market_lock = threading.Lock()
eval_cache = {}  # slug -> {"score","createdAt","time"} 测评分数缓存，降低API压力
# 评论数缓存：stats.comments 接口恒为 0，真实评论数来自 /api/v1/skills/{slug}/comments 的 total 字段
comment_counts_cache = {}
comment_fetch_counter = [0]
COMMENT_FETCH_EVERY = 6  # 每 6 个采集周期(约5分钟)刷新一次评论数，避免高频撞限流导致数据冻结；首周期强制刷新


# 发布状态（本地精准追踪）：公开 API 不暴露发布审核状态(安全审核中/已发布)，
# 改由发布脚本写入 publish_status.json（slug->状态），或用户确认后人工更新。
publish_status = {}
def load_publish_status():
    global publish_status
    try:
        with open(PUBLISH_STATUS_FILE, "r", encoding="utf-8") as f:
            publish_status = json.load(f)
    except Exception:
        publish_status = {}

# ========== 前端构建号（用于版本自检测，避免浏览器缓存旧版导致"假离线"）==========
def get_dashboard_build():
    """从 dashboard.html 提取「构建XXXX」号，作为前端版本标识；文件缺失时回退 0"""
    try:
        fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")
        with open(fp, "r", encoding="utf-8") as f:
            txt = f.read()
        m = re.search(r"构建(\d+)", txt)
        return int(m.group(1)) if m else 0
    except Exception:
        return 0

# ========== 工具 ==========
def fetch_json(url, method="GET", body=None, retries=2, backoff=1.0):
    """请求 SkillHub API；遇瞬时拒绝连接(WinError 10061)/超时/限流自动重试+退避，
    限流(429)自动延长退避，降低采集失败与误报"""
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
            # 限流：延长退避，避免高频撞墙
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
    """把采集异常映射为新手可读的白话中文，绝不暴露原始异常文本/技术栈"""
    em = str(e).lower()
    et = type(e).__name__
    if any(k in str(e) for k in ("10061", "10054", "WinError", "ConnectionRefused", "ConnectionReset", "NameResolution", "getaddrinfo", "[Errno")) or "URLError" in et or "ConnectionError" in et:
        return "网络连接异常：暂时连不上 SkillHub，已保留上次数据，系统每约 50 秒自动重试"
    if "timeout" in em or "timed out" in em:
        return "网络较慢：服务器响应超时，已保留上次数据，系统正在自动重试"
    if "429" in str(e) or "rate" in em or "请求过于频繁" in str(e) or "too many" in em:
        return "刷新频率过高被限流：系统已自动减速，请稍候片刻"
    if "401" in str(e) or "403" in str(e) or "未授权" in str(e) or "forbidden" in em:
        return "账号授权失效：请检查 config.json 里的 user_id 是否正确"
    if "404" in str(e):
        return "接口地址变更：请联系技能开发者更新"
    if "ssl" in em or "certificate" in em:
        return "网络安全校验失败：请检查本机网络代理或证书设置"
    return "数据获取失败：已保留上次数据，系统会自动重试（错误详情已记入服务端日志）"


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
    """五维度→子维度均→五维度总平"""
    dim_avgs = []
    for d_key, d_val in dims.items():
        if isinstance(d_val, dict) and "items" in d_val:
            subs = [iv["score"] for iv in d_val["items"].values()
                    if isinstance(iv, dict) and "score" in iv and isinstance(iv["score"], (int, float))]
            if subs:
                dim_avgs.append(sum(subs)/len(subs))
    return round(sum(dim_avgs)/len(dim_avgs), 2) if dim_avgs else None

def calc_security_status(sec_reports):
    """从技能详情 securityReports（源码安全扫描：keen/sanbu 等）推导发布/安全状态
    返回: 安全审核中 / 安全通过 / 安全风险 / —（无数据）"""
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
        return "安全风险"
    if scanning:
        return "安全审核中"
    # 其余（含 benign / passed / safe）视为已通过安全扫描
    return "安全通过"

# ========== 个人技能采集 ==========
def collect_self_data():
    global collect_count, last_error, user_info
    from datetime import datetime, timezone, timedelta
    from concurrent.futures import ThreadPoolExecutor, as_completed
    ts = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    try:
        load_publish_status()  # 每次采集重载本地发布状态；用户编辑 publish_status.json 后10秒内网页生效
        # 用户信息 + 技能列表 — 并发拉取；失败时不覆盖 user_info（保留上次成功值）
        skills_list = []
        _pool = ThreadPoolExecutor(max_workers=4)
        try:
            _f_user = _pool.submit(fetch_json, f"{API_BASE}/api/v1/users/{USER_ID}")
            _f_skills = _pool.submit(fetch_json, f"{API_BASE}/api/v1/users/{USER_ID}/skills?page=1&pageSize=20")
            for _f, _name in [(_f_user,"用户"),(_f_skills,"技能列表")]:
                try:
                    _r = _f.result(timeout=15)
                    if _name == "用户":
                        user_info = _r.get("user", {})
                    else:
                        skills_list = _r.get("skills", [])
                except Exception as _e:
                    print(f"[{ts}] {_name}拉取失败: {_e}")
        finally:
            _pool.shutdown(wait=False)  # 不等待后台线程，防卡死

        # 技能详情 — 并发拉取，总超时 20s
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

                # 评论数采集：stats.comments 恒为0，改走专属列表接口拿 total（节流，首周期强制）
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
                                pass  # 保留上次缓存值，确保平滑
                    finally:
                        _poolc.shutdown(wait=False)


        if skills_list:
            with data_lock:
                history["timestamps"].append(ts)
                if len(history["timestamps"]) > MAX_HISTORY:
                    history["timestamps"] = history["timestamps"][-MAX_HISTORY:]
                # 粉丝数量：用户级指标，单独按时间线追踪，用于"较上一小时"环比
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
                # 兼容旧版 history.json：补齐新增字段键，避免 KeyError 并完成自动迁移
                for _k in ("subCategories","claimState","verified","createdAt","comments","category","namespace","requiresKey"):
                    hs.setdefault(_k, [])
                hs["name"] = sk["name"]
                hs["downloads"].append(stats.get("downloads", sk.get("downloads",0)))
                hs["stars"].append(stats.get("stars", sk.get("stars",0)))
                hs["version"].append(sk.get("version",""))
                hs["versionUpdatedAt"].append(sk.get("updatedAt",""))
                # 发布状态走本地精准追踪(publish_status.json)，不再依赖不准确的 securityReports 源码扫描状态
                hs.setdefault("security", []).append(publish_status.get(slug, "已发布"))

                # 新增：核心指标卡所需的静态/慢变元数据与评论数
                sci = detail.get("skill",{}) if detail else {}
                hs["subCategories"].append(sci.get("subCategories", []))
                hs["claimState"].append(sci.get("claim_state", ""))
                hs["verified"].append(bool(sci.get("verified", False)))
                hs["createdAt"].append(sci.get("createdAt", ""))
                hs["comments"].append(comment_counts_cache.get(slug, 0))

                # 类目 / namespace / 是否需要key（静态元数据，随详情与列表抓取）
                hs["category"].append(sci.get("category", ""))
                _ns = sk.get("namespace", {}) or {}
                hs["namespace"].append(_ns.get("canonicalName", "") if isinstance(_ns, dict) else "")
                _lbl = sci.get("labels", {}) or {}
                hs["requiresKey"].append(str(_lbl.get("requires_api_key", "false")) if isinstance(_lbl, dict) else "false")

                # 测评分数：每5分钟才真正请求一次API，平时复用缓存，降低限流风险
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

                # 总评论量：全部技能评论数之和，按时间线追踪用于"较上一小时"
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

        # 昨日下载量基准：跨日快照，供前端"用户总下载量·环比增长"与昨日比较
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
                    history["yesterday_dl"] = history["last_total_dl"]   # 累计总量(昨日23:59/今日00:00快照,供环比与每日增量)
                if history.get("last_dl_by_skill"):
                    history["yesterday_dl_by_skill"] = dict(history["last_dl_by_skill"])  # 每技能跨日快照，供「日排名」图表
            history["last_date"] = _today_str
            history["last_total_dl"] = _total_dl_now
            history["last_dl_by_skill"] = _dl_by_skill_now
        except Exception:
            pass

        collect_count += 1
        last_error = None
        LAST_OK[0] = time.time()
        print(f"[{ts}] 个人数据 #{collect_count} | 6技能")
    except Exception as e:
        last_error = friendly_error(e)
        print(f"[{ts}] 采集失败: {last_error}")

# ========== 市场数据采集 ==========
def collect_market_data():
    """采集市场数据：类目+showcase+竞品"""
    global market_data
    try:
        # 类目
        cats = fetch_json(f"{API_BASE}/api/v1/categories")
        cat_items = cats.get("items", [])

        # showcase 热门
        showcase = fetch_json(f"{API_BASE}/api/v1/showcase/featured")
        showcase_skills = showcase.get("skills", [])

        # 按类目分组统计
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

        # 热度排名：按总下载量
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

        # 竞品匹配引擎 v2：名称+介绍双匹配 + 核心专业词过滤 + 排除词 + 自动派生（通用化，不依赖固定竞品列表）
        import urllib.parse

        # keyword_map 每技能可选字段：
        #   search: API搜索关键词列表
        #   name_filter: 名称匹配词（任一命中技能名称即候选）
        #   desc_filter: 介绍匹配词（任一命中技能介绍即候选；缺省用 search 词，避免泛词误匹配介绍）
        #   core_filter: 核心专业词（配置后必须命中，确保竞品专业相关）
        #   strict_name: True=core_filter 必须出现在技能名称中（如劳动仲裁类，排除泛法律技能）
        #   desc_exclude: 介绍排除词（介绍命中任一即剔除，用于多义缩写消歧义）
        #   exclude: 排除词（名称命中任一即剔除，如 MBTI/婚姻 等无关领域）
        keyword_map = dict(CFG.get("keyword_map", {}) or {})

        # 自动派生：keyword_map 未覆盖的技能，按显示名自动生成搜索词与过滤词
        # —— 不同用户技能不同，竞品自动不同，无需手工维护统一竞品列表
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
                    time.sleep(0.2)  # 节流：关键词搜索之间留间隔，降低限流
                    skills = []
                    if isinstance(resp, dict):
                        skills = resp.get("data", {}).get("skills", [])
                    for sk in skills:
                        sk_slug = sk.get("slug", "")
                        if sk_slug == slug or sk_slug in _skill_names_cfg:
                            continue  # 排除自己与自己的其他技能
                        sk_name = sk.get("name", "") or ""
                        sk_desc = sk.get("description", "") or ""
                        name_lc = sk_name.lower()
                        desc_lc = sk_desc.lower()

                        # ① 排除词：名称命中任一排除词直接剔除（如 MBTI人格测试 之类无关技能）
                        if any(ex.lower() in name_lc for ex in excludes):
                            continue
                        if desc_excludes and any(ex.lower() in desc_lc for ex in desc_excludes):
                            continue  # 介绍命中排除词：消歧义（如 NPD=产品开发/色谱检测器 的无关技能）

                        # ② 名称+介绍双匹配：名称命中 name_filter 或 介绍命中 desc_filter
                        matched_kw = None
                        matched_in = None
                        for nf in name_filters:
                            if nf.lower() in name_lc:
                                matched_kw, matched_in = nf, "名称"
                                break
                        if not matched_kw:
                            for df in desc_filters:
                                if df.lower() in desc_lc:
                                    matched_kw, matched_in = df, "介绍"
                                    break
                        if not matched_kw:
                            continue

                        # ③ 核心专业词校验：确保竞品与本技能专业强相关
                        #    strict_name=True（如劳动仲裁类）：核心词必须出现在名称中，
                        #    其他法律类即使介绍提到劳动也不算竞品
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
                    print(f"  [!] 竞品搜索 {kw} 失败: {e}")

            print(f"  [{slug}] 名称+介绍双匹配得到{len(all_matches)}个竞品")

            # 取下载量TOP15，获取详细信息后再分两个维度
            top_dl_raw = sorted(all_matches.values(), key=lambda x: -x["downloads"])[:15]

            # 获取每个竞品的详情（createdAt/updatedAt）
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

            # 维度1：下载量TOP10
            by_dl = sorted(top_dl_raw, key=lambda x: -x["downloads"])[:10]

            # 维度2：初版上传时间最新TOP10
            by_new = sorted([m for m in top_dl_raw if m.get("createdAt")], key=lambda x: -(x.get("createdAt") or 0))[:10]

            competitors[slug] = {"byDownloads": by_dl, "byNewest": by_new}
            print(f"  [{slug}] 下载TOP10: {[m['downloads'] for m in by_dl]} | 最新上传: {[m.get('createdAt','') for m in by_new[:3]]}")

        # 平台技能实时总数（系统现有 Skill 数量）：空关键词搜索返回的 data.total
        # 保留上次的值作为兜底，API 失败时不归零
        total_skills = market_data.get("total_skills", 0)
        try:
            total_resp = fetch_json(f"{API_BASE}/api/skills?keyword=&page=1&pageSize=1&sortBy=downloads&order=desc")
            if isinstance(total_resp, dict):
                _new_total = (total_resp.get("data", {}) or {}).get("total", 0) or 0
                if _new_total > 0:
                    total_skills = _new_total
        except Exception as e:
            print(f"[市场] 获取技能总数失败(保留上次值 {total_skills}): {e}")

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

        print(f"[市场] 类目{len(cat_items)} showcase{len(showcase_skills)} 热度{len(hotness)}")

    except Exception as e:
        print(f"[市场] 采集失败: {e}")

# ========== 采集循环 ==========
def collector_loop():
    # 首次采个人数据（快，不阻塞HTTP服务）；异常不影响后续HTTP服务与循环
    try:
        collect_self_data()
    except Exception as _e:
        print(f"[{time.strftime('%H:%M:%S')}] 首次采集异常(已捕获，继续): {_e}")
    # 延迟加载历史（如果有）
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
    # 延迟10秒后再采集市场数据（避免阻塞HTTP启动）
    def delayed_market():
        time.sleep(0.5)
        collect_market_data()
    threading.Thread(target=delayed_market, daemon=True).start()

    market_counter = 0
    while True:
        try:
            time.sleep(COLLECT_INTERVAL)
            # 带超时的采集：35秒内必须完成，否则放弃本轮（冻结看门狗兜底自愈）
            _ct = threading.Thread(target=collect_self_data, daemon=True)
            _ct.start()
            _ct.join(timeout=35)
            if _ct.is_alive():
                print(f"[{time.strftime('%H:%M:%S')}] 采集超时(>35s)，放弃本轮")
            market_counter += 1
            if market_counter * COLLECT_INTERVAL >= MARKET_INTERVAL:
                collect_market_data()
                market_counter = 0
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] 采集循环异常(已自愈): {e}")
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
        """若客户端支持 gzip 则压缩 body 字节；压缩级别 1 速度优先（1.3MB history 在 localhost 压成 ~150KB）"""
        try:
            ae = self.headers.get('Accept-Encoding','')
            if 'gzip' in ae.lower():
                import gzip
                return gzip.compress(body, compresslevel=1)
        except Exception:
            pass
        return None  # 不压缩

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
        """显式提供静态文件，绕过SimpleHTTPRequestHandler的路径问题"""
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
            # dashboard.html 频繁刷新且体积较大，gzip 收益高
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
        # 前端版本自检测接口：返回服务端 dashboard.html 的构建号，供浏览器比对后自动重载
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
        """导出历史数据为CSV，支持长期趋势分析"""
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
        # 使用 gzip 压缩（history 1.3MB → ~100KB，传输速度提升 10x+）
        self.write_response(body, "application/json; charset=utf-8")
        # 不再调用 self.end_headers() 和 self.wfile.write()，因为 write_response 已处理
        # 兼容旧调用方：如果没压缩则按原方式返回
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

# ========== 冻结看门狗 ==========
def freeze_watchdog():
    """若距上次成功采集超过 3*COLLECT_INTERVAL 仍无新数据，说明采集线程卡死/冻结，
    强制退出进程，由 start_monitor.sh 的 while 循环干净重启（重启前会先释放 8866 端口）。
    彻底杜绝"数据不动了"的长期冻结。"""
    while True:
        time.sleep(30)
        try:
            since = time.time() - LAST_OK[0]
            if since > 3 * COLLECT_INTERVAL:
                print(f"[{time.strftime('%H:%M:%S')}] 冻结看门狗触发：距上次成功采集 {int(since)}s 超过阈值 {3*COLLECT_INTERVAL}s，强制重启进程以自愈")
                os._exit(1)
        except Exception:
            pass

# ========== 启动 ==========
def main():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE,"r",encoding="utf-8") as f:
                loaded = json.load(f)
            with data_lock:
                history.clear(); history.update(loaded)
                history.setdefault("followers", [])
                history.setdefault("totalComments", [])
            print(f"加载历史: {len(history['timestamps'])} 条")
        except Exception as e:
            print(f"加载历史失败: {e}")

    load_publish_status()  # 启动即加载本地发布状态
    threading.Thread(target=collector_loop, daemon=True).start()
    threading.Thread(target=freeze_watchdog, daemon=True).start()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), MonitorHandler)
    print(f"\n{'='*50}")
    print(f"  SkillHub 信息决策平台 v2.0")
    print(f"  本机: http://localhost:{PORT}")
    print(f"  平板: http://<本机IP>:{PORT}")
    print(f"{'='*50}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == "__main__":
    main()
