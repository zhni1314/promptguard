import json
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.gateway import process
from app.audit import init_db

init_db()

with open("tests/test_cases.json", "r", encoding="utf-8") as f:
    cases = json.load(f)

correct = 0
latencies = []

for i, c in enumerate(cases, start=1):
    t0 = time.time()
    r = process(c["text"])
    dt = (time.time() - t0) * 1000
    latencies.append(dt)

    pred_block = r["action"] in ("block", "review")
    label_block = c["label"] == "attack"
    ok = pred_block == label_block
    if ok:
        correct += 1

    status = "✅ 判对" if ok else "❌ 判错"
    label_cn = "攻击" if c["label"] == "attack" else "正常"
    action_cn = {"block": "拦截", "review": "审查", "allow": "放行"}.get(r["action"], r["action"])

    print("-" * 60)
    print(f"{status}  第 {i} 条")
    print(f"  输入      : {c['text']}")
    print(f"  标准答案  : {label_cn}（{c['label']}）")
    print(f"  系统判决  : {action_cn}（{r['action']}）")
    print(f"  风险分    : {r['score']}")
    print(f"  耗时      : {dt:.0f} ms")

print(f"\n准确率: {correct / len(cases) * 100:.1f}%")
print(f"平均延迟: {sum(latencies) / len(latencies):.1f} ms")