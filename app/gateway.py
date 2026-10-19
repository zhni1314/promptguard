import httpx

from app.detectors.rule_detector import rule_detect
from app.detectors.similarity_detector import similarity_detect
from app.detectors.llm_detector import llm_detect
from app.detectors.output_filter import filter_output
from app.audit import log_event
from app.llm_client import ask_ollama
from app.config import (
    BLOCK_THRESHOLD,
    REVIEW_THRESHOLD,
    DEGRADED_SCORE,
    OLLAMA_GEN_TIMEOUT,
)

BLOCK_ANSWER = "请求已被 PromptGuard 拦截：检测到高风险提示词注入意图。"

# 检测失效时的中文标签（直接拼 status 会得到「组件degraded」这种半英半中的告警）
STATUS_LABEL = {"degraded": "环境降级", "fault": "内部故障"}
DETECTOR_BROKEN = ("degraded", "fault")

# gen_status 取值：
#   success  生成正常
#   timeout  生成超时（检测那一刻是好的，只是回答没赶上）
#   degraded 生成环境不可用（模型没启动 / HTTP 错误 / 空响应）
#   fault    生成阶段内部异常
#   skipped  根本没走到生成（被拦截，或检测已失效）
GEN_SUCCESS = "success"
GEN_SKIPPED = "skipped"


def _llm_score(llm):
    # degraded（环境）和 fault（内部）都不能给 0 分放行：兜底分强制越过 REVIEW_THRESHOLD
    if (llm or {}).get("status") in DETECTOR_BROKEN:
        return DEGRADED_SCORE
    risk = (llm or {}).get("risk", "low")
    return {"high": 0.9, "medium": 0.5, "low": 0.0}.get(risk, 0.0)


def _generate(user_input: str):
    """内容生成阶段。返回 (文本, gen_status)。

    与检测阶段对称：这里也要分清「环境超时」和「内部异常」，
    否则生成失败会被一律记成 success，日志里根本看不出问题出在哪一段。
    """
    try:
        raw = ask_ollama(user_input, timeout=OLLAMA_GEN_TIMEOUT)
    except httpx.TimeoutException:
        return (f"[模型生成超时(>{OLLAMA_GEN_TIMEOUT:.0f}s)，已降级为规则/相似度检测结果]",
                "timeout")
    except httpx.HTTPStatusError:
        return ("[模型服务返回错误状态，已降级为规则/相似度检测结果]", "degraded")
    except httpx.RequestError:
        return ("[本地模型未启动或调用失败，已降级为规则/相似度检测结果]", "degraded")
    except Exception as e:
        return (f"[内部生成异常({type(e).__name__})，已降级为规则/相似度检测结果]", "fault")

    if not raw:
        return ("[本地模型返回空响应，已降级为规则/相似度检测结果]", "degraded")
    return raw, GEN_SUCCESS


def process(user_input: str):
    rule = rule_detect(user_input)
    sim = similarity_detect(user_input)
    llm = llm_detect(user_input)

    status = llm.get("status")
    detector_broken = status in DETECTOR_BROKEN
    final_score = max(rule["score"], sim["score"], _llm_score(llm))

    if final_score >= BLOCK_THRESHOLD:
        # 已拦截，不必浪费一次生成
        action = "block"
        raw = BLOCK_ANSWER
        gen_status = GEN_SKIPPED
    elif detector_broken:
        # 语义检测失效：不给 allowance，也不返回未经检测的模型输出，强制人工审查
        action = "review"
        raw = f"[安全网关警告：语义检测组件{STATUS_LABEL.get(status, status)}，已触发降级审查策略]"
        gen_status = GEN_SKIPPED
    else:
        # action 只描述「这条输入的准入判决」，生成是否成功记在 gen_status，
        # 两者分开才能一眼看出「输入没问题(allow)，但生成环节降级了」
        action = "review" if final_score >= REVIEW_THRESHOLD else "allow"
        raw, gen_status = _generate(user_input)

    filtered = filter_output(raw)
    answer = filtered["text"]
    llm["output_filter_hits"] = filtered["hits"]

    log_event(user_input, rule, sim, llm, final_score, action, gen_status=gen_status)

    return {
        "action": action,
        "degraded": detector_broken,
        "gen_status": gen_status,
        "score": round(final_score, 3),
        "rule": rule,
        "similarity": sim,
        "llm": llm,
        "answer": answer,
    }
