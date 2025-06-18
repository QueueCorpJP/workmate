"""
テストデータファクトリー
一貫性のあるテストデータを生成するためのファクトリークラス
"""
import factory
import factory.fuzzy
from faker import Faker
from datetime import datetime, timezone
import uuid
import hashlib

fake = Faker('ja_JP')  # 日本語ロケール


class CompanyFactory(factory.Factory):
    """企業テストデータファクトリー"""
    
    class Meta:
        model = dict
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.LazyAttribute(lambda obj: fake.company())
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())


class UserFactory(factory.Factory):
    """ユーザーテストデータファクトリー"""
    
    class Meta:
        model = dict
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    email = factory.LazyAttribute(lambda obj: fake.email())
    password = factory.LazyAttribute(lambda obj: hashlib.sha256("password123".encode()).hexdigest())
    name = factory.LazyAttribute(lambda obj: fake.name())
    role = factory.fuzzy.FuzzyChoice(['user', 'admin', 'manager'])
    company_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    created_by = factory.LazyFunction(lambda: str(uuid.uuid4()))


class UsageLimitsFactory(factory.Factory):
    """使用量制限テストデータファクトリー"""
    
    class Meta:
        model = dict
    
    user_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    document_uploads_used = factory.fuzzy.FuzzyInteger(0, 5)
    document_uploads_limit = factory.fuzzy.FuzzyInteger(2, 20)
    questions_used = factory.fuzzy.FuzzyInteger(0, 50)
    questions_limit = factory.fuzzy.FuzzyInteger(10, 100)
    is_unlimited = factory.fuzzy.FuzzyChoice([True, False])


class DocumentSourceFactory(factory.Factory):
    """文書ソーステストデータファクトリー"""
    
    class Meta:
        model = dict
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.LazyAttribute(lambda obj: fake.file_name(extension='pdf'))
    type = factory.fuzzy.FuzzyChoice(['pdf', 'docx', 'txt', 'xlsx'])
    page_count = factory.fuzzy.FuzzyInteger(1, 100)
    content = factory.LazyAttribute(lambda obj: fake.text(max_nb_chars=5000))
    uploaded_by = factory.LazyFunction(lambda: str(uuid.uuid4()))
    company_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    uploaded_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    active = factory.fuzzy.FuzzyChoice([True, False])


class ChatHistoryFactory(factory.Factory):
    """チャット履歴テストデータファクトリー"""
    
    class Meta:
        model = dict
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_message = factory.LazyAttribute(lambda obj: fake.text(max_nb_chars=200))
    bot_response = factory.LazyAttribute(lambda obj: fake.text(max_nb_chars=500))
    timestamp = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    category = factory.fuzzy.FuzzyChoice(['greeting', 'question', 'support', 'feedback'])
    sentiment = factory.fuzzy.FuzzyChoice(['positive', 'neutral', 'negative'])
    employee_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    employee_name = factory.LazyAttribute(lambda obj: fake.name())
    source_document = factory.LazyAttribute(lambda obj: fake.file_name(extension='pdf'))
    source_page = factory.fuzzy.FuzzyInteger(1, 50)
    input_tokens = factory.fuzzy.FuzzyInteger(10, 1000)
    output_tokens = factory.fuzzy.FuzzyInteger(20, 2000)
    total_tokens = factory.LazyAttribute(lambda obj: obj.input_tokens + obj.output_tokens)
    model_name = factory.fuzzy.FuzzyChoice(['gpt-4o-mini', 'gpt-4', 'claude-3'])
    cost_usd = factory.LazyAttribute(lambda obj: obj.total_tokens * 0.000001)
    user_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    company_id = factory.LazyFunction(lambda: str(uuid.uuid4()))


class PlanHistoryFactory(factory.Factory):
    """プラン履歴テストデータファクトリー"""
    
    class Meta:
        model = dict
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    from_plan = factory.fuzzy.FuzzyChoice(['free', 'basic', 'premium'])
    to_plan = factory.fuzzy.FuzzyChoice(['basic', 'premium', 'enterprise'])
    changed_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    duration_days = factory.fuzzy.FuzzyInteger(1, 365)


class ApplicationFactory(factory.Factory):
    """申請テストデータファクトリー"""
    
    class Meta:
        model = dict
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    company_name = factory.LazyAttribute(lambda obj: fake.company())
    contact_name = factory.LazyAttribute(lambda obj: fake.name())
    email = factory.LazyAttribute(lambda obj: fake.email())
    phone = factory.LazyAttribute(lambda obj: fake.phone_number())
    expected_users = factory.fuzzy.FuzzyChoice(['1-10', '11-50', '51-100', '100+'])
    current_usage = factory.LazyAttribute(lambda obj: fake.text(max_nb_chars=200))
    message = factory.LazyAttribute(lambda obj: fake.text(max_nb_chars=500))
    application_type = factory.fuzzy.FuzzyChoice(['production-upgrade', 'feature-request'])
    status = factory.fuzzy.FuzzyChoice(['pending', 'approved', 'rejected'])
    submitted_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    processed_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    processed_by = factory.LazyAttribute(lambda obj: fake.name())
    notes = factory.LazyAttribute(lambda obj: fake.text(max_nb_chars=300))


class MonthlyTokenUsageFactory(factory.Factory):
    """月次トークン使用量テストデータファクトリー"""
    
    class Meta:
        model = dict
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    company_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    year_month = factory.LazyAttribute(lambda obj: fake.date().strftime('%Y-%m'))
    total_input_tokens = factory.fuzzy.FuzzyInteger(1000, 100000)
    total_output_tokens = factory.fuzzy.FuzzyInteger(2000, 200000)
    total_tokens = factory.LazyAttribute(lambda obj: obj.total_input_tokens + obj.total_output_tokens)
    total_cost_usd = factory.LazyAttribute(lambda obj: obj.total_tokens * 0.000001)
    conversation_count = factory.fuzzy.FuzzyInteger(10, 1000)
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())


class CompanySettingsFactory(factory.Factory):
    """企業設定テストデータファクトリー"""
    
    class Meta:
        model = dict
    
    company_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    monthly_token_limit = factory.fuzzy.FuzzyInteger(100000, 50000000)
    warning_threshold_percentage = factory.fuzzy.FuzzyInteger(70, 90)
    critical_threshold_percentage = factory.fuzzy.FuzzyInteger(90, 99)
    pricing_tier = factory.fuzzy.FuzzyChoice(['basic', 'premium', 'enterprise'])
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())


# 複合データ生成のためのヘルパー関数
class TestDataGenerator:
    """テストデータ生成のヘルパークラス"""
    
    @staticmethod
    def create_company_with_users(user_count=5):
        """企業と関連するユーザーを生成"""
        company = CompanyFactory()
        users = []
        
        for _ in range(user_count):
            user = UserFactory(company_id=company['id'])
            usage_limits = UsageLimitsFactory(user_id=user['id'])
            users.append({
                'user': user,
                'usage_limits': usage_limits
            })
        
        return {
            'company': company,
            'users': users
        }
    
    @staticmethod
    def create_chat_session(user_id, company_id, message_count=10):
        """チャットセッションを生成"""
        messages = []
        
        for _ in range(message_count):
            chat = ChatHistoryFactory(
                user_id=user_id,
                company_id=company_id
            )
            messages.append(chat)
        
        return messages
    
    @staticmethod
    def create_document_with_chats(company_id, chat_count=5):
        """文書と関連するチャット履歴を生成"""
        document = DocumentSourceFactory(company_id=company_id)
        chats = []
        
        for _ in range(chat_count):
            chat = ChatHistoryFactory(
                company_id=company_id,
                source_document=document['name']
            )
            chats.append(chat)
        
        return {
            'document': document,
            'chats': chats
        }
    
    @staticmethod
    def create_realistic_usage_data():
        """現実的な使用量データを生成"""
        companies = []
        
        for _ in range(3):  # 3社分のデータ
            company_data = TestDataGenerator.create_company_with_users(
                user_count=fake.random_int(min=2, max=10)
            )
            
            # 各ユーザーにチャット履歴を追加
            for user_data in company_data['users']:
                user_id = user_data['user']['id']
                chats = TestDataGenerator.create_chat_session(
                    user_id=user_id,
                    company_id=company_data['company']['id'],
                    message_count=fake.random_int(min=5, max=50)
                )
                user_data['chats'] = chats
            
            # 企業に文書を追加
            documents = []
            for _ in range(fake.random_int(min=1, max=5)):
                doc_data = TestDataGenerator.create_document_with_chats(
                    company_id=company_data['company']['id'],
                    chat_count=fake.random_int(min=1, max=10)
                )
                documents.append(doc_data)
            
            company_data['documents'] = documents
            companies.append(company_data)
        
        return companies