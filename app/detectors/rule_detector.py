import re

RULES = [
    (r"忽略(之前|以上|所有|先前)的?(指令|提示|规则)", 0.9, "忽略指令"),
    (r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", 0.9, "忽略指令"),
    (r"(泄露|输出|告诉我|打印).{0,6}(系统提示|系统指令|提示词|prompt)", 0.85, "提示词泄露"),
    (r"(你现在是|从现在起你是|扮演|角色扮演)", 0.5, "角色扮演"),
    (r"(越狱|jailbreak|DAN模式|开发者模式)", 0.85, "越狱尝试"),
    (r"(绕过|突破|解除).{0,6}(限制|安全|过滤|审查)", 0.8, "绕过限制"),
    (r"(base64|rot13|十六进制|编码).{0,8}(解码|执行|转换)", 0.4, "编码绕过"),
    (r"system\s*prompt", 0.7, "系统提示探测"),
]

def rule_detect(text: str):
    hits = []
    score = 0.0
    for pattern, weight, name in RULES:
        if re.search(pattern, text, re.I):
            hits.append(name)
            score = max(score, weight)
    return {"score": round(score, 3), "hits": hits}
