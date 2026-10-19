import os

# Ollama 服务地址，用 127.0.0.1 避免 Windows 下 localhost 的 IPv6 回退延迟
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

# 检测阶段超时（短提示词，快速失败）
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "30"))
# 生成阶段超时（长回答，3B 模型可能 36 秒以上）
OLLAMA_GEN_TIMEOUT = float(os.getenv("OLLAMA_GEN_TIMEOUT", "120"))

# 风险阈值
BLOCK_THRESHOLD = 0.8
REVIEW_THRESHOLD = 0.5
# 检测失效时的降级分数，越过 REVIEW_THRESHOLD，强制人工审查
DEGRADED_SCORE = 0.7

# SQLite 数据库路径
DB_PATH = os.getenv("PROMPTGUARD_DB", "promptguard_audit.db")

