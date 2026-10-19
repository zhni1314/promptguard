import json
import sqlite3
from datetime import datetime
from app.config import DB_PATH

# 建表语句：新库直接带上全部列
CREATE_SQL = """
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT,
        user_input TEXT,
        rule_score REAL,
        rule_hits TEXT,
        sim_score REAL,
        sim_matched TEXT,
        llm_status TEXT,
        llm_risk TEXT,
        llm_reason TEXT,
        raw_llm_output TEXT,
        gen_status TEXT,
        final_score REAL,
        action TEXT
    )
"""

# 老库缺列时的增量迁移：(列名, 列定义)。
# 加新列只需在这里追加一行 —— CREATE TABLE IF NOT EXISTS 对已存在的表是空操作，
# 靠这个列表才能把老库平滑升上来，且不动历史数据。
MIGRATIONS = [
    ("llm_status", "TEXT"),
    ("raw_llm_output", "TEXT"),
    ("gen_status", "TEXT"),
]


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = _connect()
    conn.execute(CREATE_SQL)

    existing = {row[1] for row in conn.execute("PRAGMA table_info(audit_log)")}
    for column, ddl in MIGRATIONS:
        if column not in existing:
            conn.execute(f"ALTER TABLE audit_log ADD COLUMN {column} {ddl}")

    conn.commit()
    conn.close()


def log_event(user_input, rule, sim, llm, final_score, action, gen_status=""):
    conn = _connect()
    conn.execute(
        """INSERT INTO audit_log
        (ts, user_input, rule_score, rule_hits, sim_score, sim_matched,
         llm_status, llm_risk, llm_reason, raw_llm_output, gen_status,
         final_score, action)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            datetime.now().isoformat(timespec="seconds"),
            user_input,
            rule["score"],
            json.dumps(rule["hits"], ensure_ascii=False),
            sim["score"],
            sim["matched"],
            llm.get("status", ""),
            llm.get("risk", ""),
            llm.get("reason", ""),
            llm.get("raw", ""),
            gen_status,
            final_score,
            action,
        ),
    )
    conn.commit()
    conn.close()


def fetch_logs(limit=100):
    conn = _connect()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
