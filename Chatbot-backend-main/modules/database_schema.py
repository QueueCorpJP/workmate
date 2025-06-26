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
        special TEXT,
        parent_id TEXT,
        FOREIGN KEY (uploaded_by) REFERENCES users (id),
        FOREIGN KEY (company_id) REFERENCES companies (id),
        FOREIGN KEY (parent_id) REFERENCES document_sources (id)
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
        source_page TEXT,
        input_tokens INTEGER DEFAULT 0,
        output_tokens INTEGER DEFAULT 0,
        total_tokens INTEGER DEFAULT 0,
        model_name TEXT DEFAULT 'gemini-2.5-flash',
        cost_usd DECIMAL(10,6) DEFAULT 0.000000,
        user_id TEXT,
        company_id TEXT,
        prompt_references INTEGER DEFAULT 0,
        base_cost_usd DECIMAL(10,6) DEFAULT 0.000000,
        prompt_cost_usd DECIMAL(10,6) DEFAULT 0.000000,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (company_id) REFERENCES companies (id)
    )
    """,
    
    "monthly_token_usage": """
    CREATE TABLE IF NOT EXISTS monthly_token_usage (
        id TEXT PRIMARY KEY,
        company_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        year_month TEXT NOT NULL,
        total_input_tokens INTEGER DEFAULT 0,
        total_output_tokens INTEGER DEFAULT 0,
        total_tokens INTEGER DEFAULT 0,
        total_cost_usd DECIMAL(10,6) DEFAULT 0.000000,
        conversation_count INTEGER DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (company_id) REFERENCES companies (id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(company_id, user_id, year_month)
    )
    """,

    "company_settings": """
    CREATE TABLE IF NOT EXISTS company_settings (
        company_id TEXT PRIMARY KEY,
        monthly_token_limit INTEGER DEFAULT 25000000,
        warning_threshold_percentage INTEGER DEFAULT 80,
        critical_threshold_percentage INTEGER DEFAULT 95,
        pricing_tier TEXT DEFAULT 'basic',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (company_id) REFERENCES companies (id)
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

# データベースビューの定義
VIEWS = {
    "current_month_usage": """
    CREATE VIEW IF NOT EXISTS current_month_usage AS
    SELECT 
        company_id,
        user_id,
        SUM(total_tokens) as current_month_tokens,
        COUNT(*) as current_month_conversations,
        SUM(cost_usd) as current_month_cost_usd
    FROM chat_history 
    WHERE strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')
    GROUP BY company_id, user_id
    """,

    "company_current_month_summary": """
    CREATE VIEW IF NOT EXISTS company_current_month_summary AS
    SELECT 
        c.id as company_id,
        c.name as company_name,
        COALESCE(SUM(cmu.current_month_tokens), 0) as total_current_month_tokens,
        COALESCE(SUM(cmu.current_month_conversations), 0) as total_current_month_conversations,
        COALESCE(SUM(cmu.current_month_cost_usd), 0) as total_current_month_cost_usd,
        COUNT(DISTINCT cmu.user_id) as active_users_this_month
    FROM companies c
    LEFT JOIN current_month_usage cmu ON c.id = cmu.company_id
    GROUP BY c.id, c.name
    """
}

# インデックスの定義
INDEXES = {
    "idx_chat_history_company_timestamp": """
    CREATE INDEX IF NOT EXISTS idx_chat_history_company_timestamp 
    ON chat_history(company_id, timestamp)
    """,
    
    "idx_chat_history_user_timestamp": """
    CREATE INDEX IF NOT EXISTS idx_chat_history_user_timestamp 
    ON chat_history(user_id, timestamp)
    """,
    
    "idx_chat_history_tokens": """
    CREATE INDEX IF NOT EXISTS idx_chat_history_tokens 
    ON chat_history(total_tokens)
    """,
    
    "idx_monthly_usage_company_month": """
    CREATE INDEX IF NOT EXISTS idx_monthly_usage_company_month 
    ON monthly_token_usage(company_id, year_month)
    """,
    
    "idx_monthly_usage_user_month": """
    CREATE INDEX IF NOT EXISTS idx_monthly_usage_user_month 
    ON monthly_token_usage(user_id, year_month)
    """
}

INITIAL_DATA = {
    # 初期データは database.py の init_db() 関数で動的に生成される
}
