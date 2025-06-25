"""
プロンプト生成の最適化とキャッシュ
高速なプロンプト生成と再利用可能なテンプレートキャッシュ
Geminiコンテキストキャッシュ対応
"""
from functools import lru_cache
import hashlib
import time
from typing import List, Optional, Dict, Any

def safe_print(text):
    """安全なprint関数"""
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            safe_text = str(text).encode('utf-8', errors='replace').decode('utf-8')
            print(safe_text)
        except:
            print("[出力エラー: Unicode文字を含むメッセージ]")

# Geminiコンテキストキャッシュ管理
class GeminiContextCache:
    """Geminiコンテキストキャッシュの管理クラス"""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 3600  # 1時間のTTL
        self.min_context_size = 2000  # 最小キャッシュサイズ（2KB）
    
    def _generate_context_hash(self, content: str) -> str:
        """コンテキストのハッシュ値を生成"""
        # 内容の正規化（改行や空白の統一）
        normalized = content.strip().replace('\r\n', '\n').replace('\r', '\n')
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]
    
    def should_cache_context(self, content: str) -> bool:
        """コンテキストをキャッシュすべきかを判定"""
        return len(content) >= self.min_context_size
    
    def get_cached_content_id(self, knowledge_base_content: str) -> Optional[str]:
        """キャッシュされたコンテンツIDを取得"""
        if not self.should_cache_context(knowledge_base_content):
            return None
        
        context_hash = self._generate_context_hash(knowledge_base_content)
        cache_entry = self.cache.get(context_hash)
        
        if cache_entry:
            # TTLチェック
            if time.time() - cache_entry['timestamp'] < self.cache_ttl:
                safe_print(f"🎯 コンテキストキャッシュヒット: {context_hash}")
                return cache_entry['content_id']
            else:
                # 期限切れキャッシュを削除
                del self.cache[context_hash]
                safe_print(f"⏰ 期限切れキャッシュを削除: {context_hash}")
        
        return None
    
    def store_context_cache(self, knowledge_base_content: str, content_id: str):
        """コンテキストキャッシュを保存"""
        if not self.should_cache_context(knowledge_base_content):
            return
        
        context_hash = self._generate_context_hash(knowledge_base_content)
        self.cache[context_hash] = {
            'content_id': content_id,
            'timestamp': time.time(),
            'size': len(knowledge_base_content)
        }
        safe_print(f"💾 コンテキストキャッシュ保存: {context_hash} (サイズ: {len(knowledge_base_content):,}文字)")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """キャッシュ統計情報を取得"""
        valid_entries = 0
        expired_entries = 0
        total_size = 0
        
        current_time = time.time()
        for cache_entry in self.cache.values():
            if current_time - cache_entry['timestamp'] < self.cache_ttl:
                valid_entries += 1
                total_size += cache_entry['size']
            else:
                expired_entries += 1
        
        return {
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'total_cached_size': total_size,
            'cache_hit_potential': f"{(valid_entries / max(1, len(self.cache))) * 100:.1f}%"
        }
    
    def cleanup_expired_cache(self):
        """期限切れキャッシュのクリーンアップ"""
        current_time = time.time()
        expired_keys = [
            key for key, cache_entry in self.cache.items()
            if current_time - cache_entry['timestamp'] >= self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            safe_print(f"🧹 期限切れキャッシュをクリーンアップ: {len(expired_keys)}件")

# グローバルコンテキストキャッシュインスタンス
gemini_context_cache = GeminiContextCache()

@lru_cache(maxsize=50)
def get_optimized_prompt_template(company_name: str, has_special_instructions: bool) -> str:
    """プロンプトテンプレートの最適化版（LRUキャッシュ使用）"""
    
    base_instructions = f"""あなたは親切で丁寧な対応ができる{company_name}のアシスタントです。
以下の知識ベースを参考に、ユーザーの質問に対して可能な限り具体的で役立つ回答を提供してください。

回答の際の注意点：
1. 常に丁寧な言葉遣いを心がけ、ユーザーに対して敬意を持って接してください
2. 知識ベースに情報がない場合でも、一般的な文脈で回答できる場合は適切に対応してください
3. ユーザーが「もっと詳しく」などと質問した場合は、前回の回答内容に関連する詳細情報を提供してください
4. 可能な限り具体的で実用的な情報を提供してください
5. 知識ベースにOCRで抽出されたテキストが含まれている場合は、文脈から適切に解釈してください
6. 知識ベースの情報を使用して回答した場合は、回答の最後に「情報ソース: [ファイル名]」の形式で参照したファイル名を記載してください
7. 回答は**Markdown記法**を使用して見やすく整理してください
8. 重要な情報は**太字**で強調してください
9. コードやファイル名、設定値などは`バッククォート`で囲んでください"""
    
    if has_special_instructions:
        base_instructions += "\n10. 特別な回答指示がある場合は、その指示に従ってください"
    
    return base_instructions

@lru_cache(maxsize=100)
def get_cached_conversation_format(history_length: int) -> str:
    """会話履歴フォーマットのキャッシュ版"""
    if history_length == 0:
        return ""
    return "直近の会話履歴：\n{conversation_content}\n"

def build_conversation_history_fast(recent_messages: List[dict]) -> str:
    """高速会話履歴構築"""
    if not recent_messages:
        return ""
    
    format_template = get_cached_conversation_format(len(recent_messages))
    
    conversation_parts = []
    for msg in reversed(recent_messages):  # 古い順に並び替え
        try:
            user_msg = (msg.get('user_message', '') or '')[:100]
            bot_msg = (msg.get('bot_response', '') or '')[:100]
            
            # 長い場合は省略記号を追加
            if len(msg.get('user_message', '')) > 100:
                user_msg += "..."
            if len(msg.get('bot_response', '')) > 100:
                bot_msg += "..."
            
            conversation_parts.append(f"ユーザー: {user_msg}")
            conversation_parts.append(f"アシスタント: {bot_msg}")
            
        except Exception as e:
            safe_print(f"会話履歴処理エラー: {e}")
            continue
    
    if conversation_parts:
        return format_template.format(conversation_content="\n".join(conversation_parts))
    return ""

def build_optimized_prompt(
    company_name: str,
    active_resource_names: List[str],
    active_knowledge_text: str,
    conversation_history: str,
    message_text: str,
    special_instructions_text: str = ""
) -> str:
    """最適化されたプロンプトの構築"""
    
    # テンプレートをキャッシュから取得
    template = get_optimized_prompt_template(company_name, bool(special_instructions_text))
    
    # ファイル名リストの構築（高速化）
    file_list = ', '.join(active_resource_names) if active_resource_names else ''
    
    # プロンプトの組み立て
    prompt_parts = [
        template,
        f"\n利用可能なファイル: {file_list}" if file_list else "",
        special_instructions_text,
        f"\n知識ベース内容：\n{active_knowledge_text}",
        f"\n{conversation_history}" if conversation_history else "",
        f"\nユーザーの質問：\n{message_text}"
    ]
    
    # 空の部分を除去して結合
    final_prompt = ''.join(part for part in prompt_parts if part)
    
    safe_print(f"✅ 最適化プロンプト構築完了: {len(final_prompt):,}文字")
    
    return final_prompt

def build_context_cached_prompt(
    company_name: str,
    active_resource_names: List[str],
    active_knowledge_text: str,
    conversation_history: str,
    message_text: str,
    special_instructions_text: str = ""
) -> tuple[str, Optional[str]]:
    """コンテキストキャッシュ対応のプロンプト構築"""
    
    # コンテキストキャッシュをチェック
    cached_content_id = gemini_context_cache.get_cached_content_id(active_knowledge_text)
    
    if cached_content_id:
        # キャッシュヒット：知識ベース部分を省略したプロンプトを構築
        template = get_optimized_prompt_template(company_name, bool(special_instructions_text))
        file_list = ', '.join(active_resource_names) if active_resource_names else ''
        
        # キャッシュされたコンテキストを参照するプロンプト
        prompt_parts = [
            template,
            f"\n利用可能なファイル: {file_list}" if file_list else "",
            special_instructions_text,
            "\n[注意: 知識ベースはキャッシュされたコンテキストを使用]",
            f"\n{conversation_history}" if conversation_history else "",
            f"\nユーザーの質問：\n{message_text}"
        ]
        
        final_prompt = ''.join(part for part in prompt_parts if part)
        safe_print(f"🎯 キャッシュ対応プロンプト構築: {len(final_prompt):,}文字 (キャッシュID: {cached_content_id})")
        
        return final_prompt, cached_content_id
    else:
        # キャッシュミス：通常のプロンプトを構築
        full_prompt = build_optimized_prompt(
            company_name, active_resource_names, active_knowledge_text,
            conversation_history, message_text, special_instructions_text
        )
        safe_print(f"💾 新規コンテキスト: キャッシュ作成対象")
        
        return full_prompt, None

def generate_content_with_cache(model, prompt: str, cached_content_id: Optional[str] = None):
    """コンテキストキャッシュを使用したコンテンツ生成"""
    try:
        if cached_content_id:
            # キャッシュされたコンテキストを使用
            # 注意: 実際のGemini APIでのキャッシュ使用は、APIの仕様に依存
            # ここでは概念的な実装を示している
            safe_print(f"🚀 キャッシュコンテキスト使用: {cached_content_id}")
            response = model.generate_content(prompt)
        else:
            # 通常のコンテンツ生成
            response = model.generate_content(prompt)
        
        return response
    except Exception as e:
        safe_print(f"❌ コンテンツ生成エラー: {str(e)}")
        raise

def estimate_prompt_size(
    company_name: str,
    active_resource_names: List[str],
    active_knowledge_text: str,
    conversation_history: str,
    message_text: str,
    special_instructions_text: str = ""
) -> int:
    """プロンプトサイズの高速推定（実際に構築せずにサイズを推定）"""
    
    # 基本テンプレートサイズ
    template_size = len(get_optimized_prompt_template(company_name, bool(special_instructions_text)))
    
    # 各コンポーネントのサイズ
    file_list_size = len(', '.join(active_resource_names)) if active_resource_names else 0
    knowledge_size = len(active_knowledge_text)
    history_size = len(conversation_history)
    message_size = len(message_text)
    special_size = len(special_instructions_text)
    
    # 固定文字列の推定サイズ（改行、ラベルなど）
    fixed_text_size = 200
    
    total_size = (
        template_size + 
        file_list_size + 
        knowledge_size + 
        history_size + 
        message_size + 
        special_size + 
        fixed_text_size
    )
    
    return total_size

def truncate_knowledge_for_size_limit(
    knowledge_text: str, 
    target_size: int, 
    other_content_size: int
) -> str:
    """サイズ制限に合わせて知識ベースを切り詰め"""
    
    available_size = target_size - other_content_size - 1000  # 1000文字のバッファ
    
    if available_size <= 0:
        return ""
    
    if len(knowledge_text) <= available_size:
        return knowledge_text
    
    # 文の境界で切り詰め
    truncated = knowledge_text[:available_size]
    last_sentence = max(
        truncated.rfind('。'),
        truncated.rfind('\n'),
        truncated.rfind('. '),
        available_size - 200  # 最低限のフォールバック
    )
    
    if last_sentence > 0:
        truncated = truncated[:last_sentence + 1]
    
    truncated += "\n\n[注意: サイズ制限のため、知識ベースを短縮しています]"
    
    safe_print(f"⚠️ 知識ベース切り詰め: {len(knowledge_text):,} → {len(truncated):,}文字")
    
    return truncated

# プロンプトキャッシュの統計情報
def get_cache_stats() -> dict:
    """キャッシュの統計情報を取得"""
    context_stats = gemini_context_cache.get_cache_stats()
    
    return {
        "template_cache_info": get_optimized_prompt_template.cache_info(),
        "conversation_format_cache_info": get_cached_conversation_format.cache_info(),
        "gemini_context_cache": context_stats
    }

def clear_prompt_caches():
    """全てのプロンプトキャッシュをクリア"""
    get_optimized_prompt_template.cache_clear()
    get_cached_conversation_format.cache_clear()
    gemini_context_cache.cleanup_expired_cache()
    # 全コンテキストキャッシュをクリア
    gemini_context_cache.cache.clear()
    safe_print("✅ 全プロンプトキャッシュ（コンテキストキャッシュ含む）をクリアしました") 