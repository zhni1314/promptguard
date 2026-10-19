import re

# 敏感信息脱敏规则：(正则模式, 替换符)
# 顺序决定脱敏优先级，匹配到的敏感片段会被替换为对应的占位字符串
PATTERNS = [
    (r"1[3-9]\d{9}", "***手机号***"),         # 中国大陆手机号，1 开头、第二位 3-9、共 11 位
    (r"\d{17}[\dXx]", "***身份证***"),         # 18 位身份证号，末位可能是 X/x
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "***邮箱***"),  # 标准邮箱格式
    (r"sk-[a-zA-Z0-9]{16,}", "***APIKEY***"),  # OpenAI 风格 API Key（sk- 前缀 + 16+ 字符）
    (r"AKIA[0-9A-Z]{16}", "***AWSKEY***"),     # AWS Access Key ID（AKIA 前缀 + 16 位大写字母数字）
]


def filter_output(text: str):
    """
    对输入文本执行敏感信息脱敏，替换掉已配置 PATTERNS 列表中的各类隐私/密钥片段。

    每次调用按 PATTERNS 定义的顺序逐条尝试匹配与替换；同一条规则命中后，
    该规则下的所有匹配都会被一次性替换（re.sub 的默认全局替换行为）。
    返回的 hits 列表按规则顺序记录**命中过哪些类别的敏感信息**（不去重），
    供上层审计或日志使用。

    Args:
        text: 待脱敏的原始文本，通常是 LLM 生成的回复或用户输入。

    Returns:
        dict: 包含两个字段：
            - text (str): 脱敏后的文本，所有命中 PATTERNS 的片段已被占位符替换；
              若没有任何命中，则与输入相同。
            - hits (list[str]): 本次命中的替换符列表，例如
              ["***邮箱***", "***APIKEY***"]；若完全未命中则为空列表 []。
    """
    hits = []
    for pattern, repl in PATTERNS:
        # 先用 search 做一次命中探测，避免未命中时也要跑 sub 的开销；
        # 同时只有真正命中的类别才记录到 hits 里
        if re.search(pattern, text):
            hits.append(repl)                      # 登记命中的类别标记
            text = re.sub(pattern, repl, text)     # 全局替换：同一条规则替换所有匹配
    return {"text": text, "hits": hits}