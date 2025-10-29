"""
请求日志数据库模型
用于存储API请求的详细记录
"""

import os

# 数据库路径 - 支持环境变量配置
DB_PATH = os.getenv("DB_PATH", "tokens.db")  # 复用 tokens 数据库

# 创建请求日志表的SQL
SQL_CREATE_REQUEST_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS request_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    duration REAL,
    first_token_time REAL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_request_logs_timestamp ON request_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_request_logs_model ON request_logs(model);
CREATE INDEX IF NOT EXISTS idx_request_logs_provider ON request_logs(provider);
"""
