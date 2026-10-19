import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 攻击模板 JSON 文件路径：项目根目录下 data/attack_templates.json
DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "attack_templates.json"

# 加载注入攻击模板列表，每项为一段典型的 Prompt 注入/越狱提示词
with open(DATA_PATH, "r", encoding="utf-8") as f:
    TEMPLATES = json.load(f)

# 使用字符级 1-3 gram 的 TF-IDF 向量化器，捕捉常见的提示词拼写模式（如 "ignore previous"、"jailbreak" 等）
_vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(1, 3))
# 预先对所有模板生成 TF-IDF 矩阵，检测时只需 transform 新文本即可
_template_matrix = _vectorizer.fit_transform(TEMPLATES)  # 预先计算模板矩阵


def similarity_detect(text: str):
    """
    基于 TF-IDF + 余弦相似度检测输入文本是否与已知的 Prompt 注入/越狱模板相似。

    原理：将输入文本与预加载的攻击模板列表映射到同一个 TF-IDF 向量空间，
    计算它与每个模板的余弦相似度，取最高得分及对应模板作为匹配结果。

    Args:
        text: 需要检测的用户输入文本。

    Returns:
        dict: 包含以下两个字段：
            - score (float): 最高相似度得分，范围 [0.0, 1.0]，保留 3 位小数；
              分数越高表示越可能是已知攻击模板的变体。
            - matched (str): 相似度最高的那条攻击模板原文；
              若输入为空字符串则返回空字符串。
    """
    # 空输入直接返回零分，避免无意义的向量化计算
    if not text.strip():
        return {"score": 0.0, "matched": ""}

    # 将单条输入文本转换为与模板矩阵相同维度的 TF-IDF 向量
    vec = _vectorizer.transform([text])

    # 计算输入向量与每条模板向量的余弦相似度，返回一个 1×N 的数组；
    # [0] 取出这一行得到长度为 N 的一维相似度数组
    sims = cosine_similarity(vec, _template_matrix)[0]

    # 返回得分最高的模板索引
    idx = int(sims.argmax())

    # 返回最高相似度（保留 3 位小数）及对应的攻击模板原文
    return {"score": round(float(sims[idx]), 3), "matched": TEMPLATES[idx]}