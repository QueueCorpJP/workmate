"""
データベーススキーマ定義
アプリケーションで使用するデータベーステーブルを定義します
"""

SCHEMA = {
    "companies": """
    CREATE TABLE IF NOT EXISTS companies (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,

    "users": """
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        company_id TEXT,
        created_by TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES companies (id),
        FOREIGN KEY (created_by) REFERENCES users (id)
    )
    """,

    "usage_limits": """
    CREATE TABLE IF NOT EXISTS usage_limits (
        user_id TEXT PRIMARY KEY,
        document_uploads_used INTEGER NOT NULL DEFAULT 0,
        document_uploads_limit INTEGER NOT NULL DEFAULT 2,
        questions_used INTEGER NOT NULL DEFAULT 0,
        questions_limit INTEGER NOT NULL DEFAULT 10,
        is_unlimited INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """,

    "document_sources": """
    CREATE TABLE IF NOT EXISTS document_sources (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        page_count INTEGER,
        content TEXT NOT NULL,
        uploaded_by TEXT NOT NULL,
        company_id TEXT NOT NULL,
        uploaded_at TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (uploaded_by) REFERENCES users (id),
        FOREIGN KEY (company_id) REFERENCES companies (id)
    )
    """,

    "chat_history": """
    CREATE TABLE IF NOT EXISTS chat_history (
        id TEXT PRIMARY KEY,
        user_message TEXT NOT NULL,
        bot_response TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        category TEXT,
        sentiment TEXT,
        employee_id TEXT,
        employee_name TEXT,
        source_document TEXT,
        source_page TEXT
    )
    """,
    
    "plan_history": """
    CREATE TABLE IF NOT EXISTS plan_history (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        from_plan TEXT NOT NULL,
        to_plan TEXT NOT NULL,
        changed_at TEXT NOT NULL,
        duration_days INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """,
    
    "applications": """
    CREATE TABLE IF NOT EXISTS applications (
        id TEXT PRIMARY KEY,
        company_name TEXT NOT NULL,
        contact_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        expected_users TEXT,
        current_usage TEXT,
        message TEXT,
        application_type TEXT NOT NULL DEFAULT 'production-upgrade',
        status TEXT NOT NULL DEFAULT 'pending',
        submitted_at TEXT NOT NULL,
        processed_at TEXT,
        processed_by TEXT,
        notes TEXT
    )
    """
}

INITIAL_DATA = {
    "default_company": """
    INSERT OR IGNORE INTO companies (id, name, created_at)
    VALUES ('company_1', 'ヘルプ', datetime('now'))
    """,

    "admin_user": """
    INSERT OR IGNORE INTO users (id, email, password, name, role, company_id, created_at)
    VALUES ('admin', 'queue@queuefood.co.jp', 'John.Queue2025', '管理者', 'admin', 'company_1', datetime('now'))
    """,

    "admin_unlimited": """
    INSERT OR IGNORE INTO usage_limits (user_id, is_unlimited)
    VALUES ('admin', 1)
    """
}
