import httpx
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT


def ask_ollama(prompt: str, temperature: float = 0.0,
               max_tokens: int = 64, timeout: float = None) -> str:
    """
    调用本地 Ollama 大模型生成文本回复。

    通过 HTTP POST 请求与 Ollama 的 `/api/generate` 接口通信，
    传入提示词及采样参数，返回模型生成的文本内容。

    Args:
        prompt: 发送给模型的提示词文本。
        temperature: 采样温度，值越低输出越确定性（0.0 为贪心解码）。
        max_tokens: 最大生成 token 数，对应 Ollama 的 `num_predict` 参数。
        timeout: 请求超时时间（秒）。若为 None 则使用配置中的默认超时。

    Returns:
        模型生成的回复文本。若响应中无 `response` 字段则返回空字符串。

    Raises:
        httpx.HTTPStatusError: 当 Ollama 返回 4xx/5xx 状态码时触发。
        httpx.TimeoutException: 当请求超时时触发。
    """
    resp = httpx.post(
        f"{OLLAMA_BASE_URL}/api/generate",  # Ollama 本地推理接口
        json={
            "model": OLLAMA_MODEL,            # 使用的模型名称（配置项）
            "prompt": prompt,                 # 用户提示词
            "stream": False,                  # 关闭流式返回，等待完整结果
            "options": {
                "temperature": temperature,  # 控制生成的随机性
                "num_predict": max_tokens,   # 限制本次生成的最大 token 数
            },
        },
        timeout=OLLAMA_TIMEOUT if timeout is None else timeout,    # 优先使用调用方传入的超时，否则用默认值
    )
    resp.raise_for_status()                  # 若响应状态码异常则抛出 HTTP 错误
    return resp.json().get("response", "")   # 从响应 JSON 中提取 response 字段，缺失时返回空串