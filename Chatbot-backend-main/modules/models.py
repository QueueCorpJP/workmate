"""
モデル定義モジュール
APIで使用するPydanticモデルを定義します
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, HttpUrl, EmailStr

# ユーザー認証関連モデル
class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    password: str
    name: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    created_at: datetime
    company_name: str

class UsageLimit(BaseModel):
    document_uploads_used: int
    document_uploads_limit: int
    questions_used: int
    questions_limit: int
    is_unlimited: bool

class UserWithLimits(UserResponse):
    usage_limits: UsageLimit

# チャット関連モデル
class ChatMessage(BaseModel):
    text: str
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    source: Optional[str] = None
    remaining_questions: Optional[int] = None
    limit_reached: Optional[bool] = None

class ChunkReferenceInfo(BaseModel):
    """参照チャンク情報"""
    chunk_id: str
    document_name: str
    chunk_index: int
    content_preview: str
    scores: Dict[str, float]
    selection_reason: str
    search_method: str

class ChunkSelectionInfo(BaseModel):
    """チャンク選択情報"""
    total_chunks_found: int
    chunks_selected: int
    dynamic_threshold: float
    selection_criteria: Dict[str, Any]
    query_analysis: Dict[str, Any]
    summary: str

class ChunkVisibilityInfo(BaseModel):
    """チャンク可視化情報"""
    chunk_references: List[ChunkReferenceInfo]
    selection_analysis: ChunkSelectionInfo
    metadata: Dict[str, Any]

class EnhancedChatResponse(BaseModel):
    """チャンク可視化機能付きチャットレスポンス"""
    response: str
    source: Optional[str] = None
    remaining_questions: Optional[int] = None
    limit_reached: Optional[bool] = None
    chunk_visibility: Optional[ChunkVisibilityInfo] = None

class ChatHistoryItem(BaseModel):
    id: str
    user_message: str
    bot_response: str
    timestamp: datetime
    category: Optional[str] = None
    sentiment: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    source_document: Optional[str] = None
    source_page: Optional[str] = None

# 分析関連モデル
class AnalysisResult(BaseModel):
    category_distribution: Dict[str, int]
    sentiment_distribution: Dict[str, int]
    common_questions: List[Dict[str, Any]]
    insights: str

# 強化分析関連モデル
class EnhancedAnalysisResult(BaseModel):
    resource_reference_count: Dict[str, Any]
    category_distribution_analysis: Dict[str, Any]
    active_user_trends: Dict[str, Any]
    unresolved_and_repeat_analysis: Dict[str, Any]
    sentiment_analysis: Dict[str, Any]
    ai_insights: Optional[str] = None
    analysis_metadata: Dict[str, Any]

# 資料参照分析結果
class ResourceReferenceItem(BaseModel):
    name: str
    type: str
    reference_count: int
    unique_users: int
    unique_days: int
    last_referenced: Optional[str] = None
    avg_satisfaction: float
    usage_intensity: float

class ResourceReferenceAnalysis(BaseModel):
    resources: List[ResourceReferenceItem]
    total_references: int
    most_referenced: Optional[ResourceReferenceItem] = None
    least_referenced: Optional[ResourceReferenceItem] = None
    active_resources: int
    summary: str

# アクティブユーザー推移分析結果
class DailyTrend(BaseModel):
    date: str
    active_users: int
    total_messages: int
    unique_names: int
    positive_ratio: float

class WeeklyTrend(BaseModel):
    week_start: str
    week_end: str
    avg_active_users: float
    total_messages: int
    days_with_activity: int

class TrendAnalysis(BaseModel):
    direction: str
    percentage_change: float
    period: str

class ActiveUserTrends(BaseModel):
    daily_trends: List[DailyTrend]
    weekly_trends: List[WeeklyTrend]
    trend_analysis: TrendAnalysis
    peak_day: Optional[DailyTrend] = None
    total_unique_users: int
    summary: str

# 社員利用状況関連モデル
class EmployeeUsageItem(BaseModel):
    employee_id: str
    employee_name: str
    message_count: int
    last_activity: datetime
    top_categories: List[Dict[str, Any]]
    recent_questions: List[str]

class EmployeeUsageResult(BaseModel):
    employee_usage: List[EmployeeUsageItem]

# URL送信関連モデル
class UrlSubmission(BaseModel):
    url: str
    user_id: Optional[str] = None

# 会社名関連モデル
class CompanyNameResponse(BaseModel):
    company_name: str

class CompanyNameRequest(BaseModel):
    company_name: str

# アップロードリソース関連モデル
class ResourceItem(BaseModel):
    id: str
    name: str
    type: str
    timestamp: datetime
    active: bool = True
    uploaded_by: Optional[str] = None
    uploader_name: Optional[str] = None
    page_count: Optional[int] = None
    usage_count: Optional[int] = None
    last_used: Optional[str] = None
    special: Optional[str] = None

class ResourcesResult(BaseModel):
    resources: List[ResourceItem]
    message: str

class ResourceToggleResponse(BaseModel):
    name: str
    active: bool
    message: str

class ResourceSpecialUpdateRequest(BaseModel):
    special: str

# デモ利用状況関連モデル
class DemoUsageStats(BaseModel):
    total_users: int
    active_users: int
    total_documents: int
    total_questions: int
    limit_reached_users: int
    total_companies: Optional[int] = None

# 管理者関連モデル
class AdminUserCreate(BaseModel):
    email: str
    password: str
    name: str
    role: str  # "user" または "employee"
    company_id: Optional[str] = None  # company_idを任意にして自動生成対応
    company_name: Optional[str] = None  # 会社名を管理者が設定可能

# プラン変更関連のモデル
class UpgradePlanRequest(BaseModel):
    plan_id: str
    payment_method: Optional[str] = None

class UpgradePlanResponse(BaseModel):
    success: bool
    message: str
    plan_id: str
    user_id: str
    payment_url: Optional[str] = None

class SubscriptionInfo(BaseModel):
    plan_id: str
    plan_name: str
    status: str
    start_date: str
    next_billing_date: Optional[str] = None
    price: float