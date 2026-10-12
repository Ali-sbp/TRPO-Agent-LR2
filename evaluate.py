import argparse
import json
from datetime import datetime
from pathlib import Path

import config
from agent import run_agent
from sources import FileSource


def judge(case, result):
    # ok = finished by itself, notified about every important message and nothing else
    important = set(case["important"])
    allowed = important | set(case.get("acceptable", []))
    got = set(result["notified_ids"])
    missed = sorted(important - got)
    extra = sorted(got - allowed)
    ok = result["status"] == "done" and not missed and not extra
    return ok, missed, extra


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--cases", default="tests")
    args = parser.parse_args()

    rows, summary = [], []
    for path in sorted(Path(args.cases).glob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        wins = 0
        print(f"\n{path.name}: {case['description']}")
        for i in range(1, args.runs + 1):
            result = run_agent(FileSource(path), quiet=True, tag=f"eval-{path.stem}")
            ok, missed, extra = judge(case, result)
            wins += ok
            note = "" if result["status"] == "done" else " (step limit)"
            print(f"  run {i:>2}: {'ok  ' if ok else 'FAIL'} steps={result['steps']:<2} "
                  f"tokens={result['tokens']:<6} missed={missed or '-'} extra={extra or '-'}{note}")
            rows.append({"case": path.name, "run": i, "ok": ok, "missed": missed, "extra": extra,
                         "steps": result["steps"], "tokens": result["tokens"], "log": result["log"]})
        rate = wins / args.runs
        summary.append((path.name, wins, args.runs, rate))
        print(f"  success rate: {wins}/{args.runs} = {rate:.0%}")

    total_wins = sum(s[1] for s in summary)
    total_runs = sum(s[2] for s in summary)
    avg_steps = sum(r["steps"] for r in rows) / len(rows)
    avg_tokens = sum(r["tokens"] for r in rows) / len(rows)
    print("\ntotal")
    for name, w, n, rate in summary:
        print(f"  {name:<32} {w}/{n}  {rate:.0%}")
    print(f"  {'all':<32} {total_wins}/{total_runs}  {total_wins / total_runs:.0%}")
    print(f"  avg steps {avg_steps:.1f}, avg tokens {avg_tokens:.0f}")

    config.LOGS_DIR.mkdir(exist_ok=True)
    out = config.LOGS_DIR / f"eval-results-{datetime.now():%Y%m%d-%H%M%S}.json"
    out.write_text(json.dumps({"summary": summary, "runs": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("saved to", out)


if __name__ == "__main__":
    main()
