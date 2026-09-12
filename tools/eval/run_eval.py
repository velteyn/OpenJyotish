"""Direct AI eval harness — test models against the LM Studio server.

Builds the EXACT anchor the app sends (same AiEngine code path), asks
eval questions, and scores answers with deterministic assertions. No
commits needed per experiment; transcripts stay local (see .gitignore).

Usage:
  # ask the resident model two short probes (no loads, no unloads):
  PYTHONPATH=src python3 tools/eval/run_eval.py --probes short

  # load a candidate first (unloaded at end unless --keep-loaded):
  PYTHONPATH=src python3 tools/eval/run_eval.py --probes short \\
      --load qwen/qwen3.5-9b --ctx 8192

  # supported-slate presets (see SUPPORTED_MODELS in jhora/ai/engine.py):
  PYTHONPATH=src python3 tools/eval/run_eval.py --probes short --preset speed
  PYTHONPATH=src python3 tools/eval/run_eval.py --probes short --preset quality

  # the full long-form question (slow: ~10+ min generations):
  PYTHONPATH=src python3 tools/eval/run_eval.py --probes full

Chart birth data comes from tools/eval/local_chart.json (gitignored,
never commit) of the form:
  {"year":1990,"month":1,"day":15,"hour":17.5,"lat":12.97,"lon":77.59,
   "tz":"+0530","spouse":"..."}

Safety: the harness unloads ONLY instances it loaded itself. It never
touches user-loaded models.
"""

import argparse
import datetime
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from jhora.ai.engine import AiEngine, AiConfig  # noqa: E402
from jhora.charts.chart import ChartBuilder  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
LOCAL_CHART = os.path.join(HERE, "local_chart.json")


def _post(base, path, payload, timeout):
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode() or "{}")


def _get(base, path, timeout=20):
    with urllib.request.urlopen(base.rstrip("/") + path,
                                timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def load_model(base, key, ctx):
    """Load a candidate; returns instance id or '' (never raises fatally)."""
    try:
        status, data = _post(base, "/api/v1/models/load",
                             {"model": key, "context_length": ctx},
                             timeout=300)
    except Exception as e:
        print(f"  load request failed: {e}")
        return ""
    if status not in (200, 201, 202):
        print(f"  load refused: HTTP {status}")
        return ""
    return str(data.get("instance_id") or data.get("model_instance_id") or "")


def unload_model(base, instance_id):
    try:
        status, _ = _post(base, "/api/v1/models/unload",
                          {"instance_id": instance_id}, timeout=60)
        return status in (200, 201, 202)
    except Exception as e:
        print(f"  unload failed: {e}")
        return False


def ask(base, model, messages, max_tokens, timeout=1500):
    """Non-streaming chat completion (long generations need long timeouts)."""
    status, data = _post(base, "/v1/chat/completions",
                         {"model": model, "messages": messages,
                          "temperature": 0.7, "max_tokens": max_tokens,
                          "stream": False}, timeout=timeout)
    if status != 200:
        return f"[HTTP {status}]", "error"
    choice = (data.get("choices") or [{}])[0]
    text = (choice.get("message") or {}).get("content", "")
    finish = choice.get("finish_reason", "")
    if finish == "length":
        text += "\n\n[truncated — output budget exhausted]"
    return text, finish or "stop"


def build_messages(question, chart_cfg, max_ctx):
    b = ChartBuilder()
    cd = b.build(chart_cfg["year"], chart_cfg["month"], chart_cfg["day"],
                 chart_cfg["hour"], lat=chart_cfg["lat"], lon=chart_cfg["lon"],
                 tz=chart_cfg["tz"])
    eng = AiEngine(AiConfig(provider="lmstudio", max_context_tokens=max_ctx))
    anchor = eng._conversation_anchor(cd)
    return AiEngine._chat_messages(anchor, question, []), cd


def score(answer, case):
    low = answer.lower()
    hits = [s for s in case.get("must_contain", []) if s.lower() in low]
    miss = [s for s in case.get("must_contain", []) if s.lower() not in low]
    bad = [s for s in case.get("must_not_contain", []) if s.lower() in low]
    return hits, miss, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://localhost:1234",
                    help="LM Studio base URL (remote e.g. http://LAN-IP:1234)")
    ap.add_argument("--probes", default="short", help="short|full|all")
    ap.add_argument("--model", default="",
                    help="instance id/key to ask (default: resident chat model)")
    ap.add_argument("--load", default="",
                    help="model key to load first (unloaded at end unless --keep-loaded)")
    ap.add_argument("--preset", default="",
                    help="supported-slate preset: quality (=ministral-3-14b) "
                         "or speed (=qwen/qwen3.5-9b); sets --load/--ctx")
    ap.add_argument("--ctx", type=int, default=8192)
    ap.add_argument("--keep-loaded", action="store_true")
    ap.add_argument("--tag", default=datetime.datetime.now().strftime("%Y%m%d-%H%M"))
    args = ap.parse_args()

    from cases import CASES
    from jhora.ai.engine import SUPPORTED_MODELS
    if args.preset:
        want = {"quality": "ministral-3-14b",
                "speed": "qwen/qwen3.5-9b"}.get(args.preset)
        if not want:
            sys.exit("--preset must be quality|speed")
        args.load = want
        for preset in SUPPORTED_MODELS:
            if preset["match"] in want or want in preset["match"]:
                args.ctx = preset["ctx"]
                break
    if args.probes == "short":
        cases = [c for c in CASES if c.get("long") != True]
    elif args.probes == "full":
        cases = [c for c in CASES if c.get("long") == True]
    else:
        cases = list(CASES)

    with open(LOCAL_CHART) as f:
        chart_cfg = json.load(f)

    managed = ""
    if args.load:
        print(f"loading {args.load} ctx={args.ctx} ...")
        managed = load_model(args.server, args.load, args.ctx)
        print("  instance:", managed or "FAILED")
        if not managed:
            sys.exit("load failed — not touching anything else")

    model = args.model
    if not model:
        if managed:
            model = managed
        else:
            # resident chat model, same preference the app uses
            cat = _get(args.server, "/api/v1/models")
            found = ""
            for m in cat.get("models", []):
                if m.get("type") == "llm" and m.get("loaded_instances"):
                    found = m["loaded_instances"][0]["id"]
                    break
            model = found or "loaded"
    print("asking model:", model)

    eng = AiEngine(AiConfig(provider="lmstudio",
                            base_url=args.server + "/v1", model=model))
    ctx = eng.detect_context_length(model) or 8192
    print("detected ctx:", ctx)

    os.makedirs(RESULTS, exist_ok=True)
    report = {"model": model, "ctx": ctx, "tag": args.tag, "cases": {}}
    for case in cases:
        print(f"\n=== {case['id']} ===")
        messages, _cd = build_messages(case["question"](chart_cfg),
                                       chart_cfg, ctx)
        answer, finish = ask(args.server, model, messages,
                             case.get("max_tokens", 2048))
        hits, miss, bad = score(answer, case)
        print(f"  finish={finish} len={len(answer)} "
              f"hits={len(hits)}/{len(hits) + len(miss)} bad={bad}")
        for s in miss:
            print(f"  MISS: {s}")
        report["cases"][case["id"]] = {
            "finish": finish, "hits": hits, "miss": miss, "bad": bad,
            "answer": answer, "question": case["question"](chart_cfg),
        }
        with open(os.path.join(RESULTS, f"{args.tag}-{case['id']}.json"),
                  "w") as f:
            json.dump(report["cases"][case["id"]], f, indent=1)

    print(f"\nmodel={model} ctx={ctx}")
    for cid, r in report["cases"].items():
        print(f"  {cid}: {len(r['hits'])} hits, {len(r['miss'])} miss, "
              f"bad={r['bad']} finish={r['finish']}")

    if managed and not args.keep_loaded:
        print("unloading harness instance ...",
              "OK" if unload_model(args.server, managed) else "FAILED")


if __name__ == "__main__":
    main()
