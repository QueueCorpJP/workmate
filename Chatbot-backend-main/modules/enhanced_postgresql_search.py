"""
Enhanced PostgreSQL Search with Japanese Morphological Analysis
日本語形態素解析を活用した高精度PostgreSQL検索システム

「株式会社あいう」のようなスペースのない日本語テキストでも
適切に単語分割して検索精度を向上させます。
"""

import logging
import re
from typing import List, Dict, Any, Optional, Set
from .database import get_db
from supabase_adapter import get_supabase_client, execute_query

# 日本語形態素解析
try:
    from janome.tokenizer import Tokenizer
    JANOME_AVAILABLE = True
except ImportError:
    JANOME_AVAILABLE = False

logger = logging.getLogger(__name__)

class EnhancedJapaneseTextProcessor:
    """日本語テキスト処理クラス"""
    
    def __init__(self):
        self.tokenizer = None
        if JANOME_AVAILABLE:
            try:
                self.tokenizer = Tokenizer()
                logger.info("✅ Janome形態素解析器を初期化しました")
            except Exception as e:
                logger.warning(f"⚠️ Janome初期化エラー: {e}")
        else:
            logger.warning("⚠️ Janomeが利用できません。基本的なテキスト処理を使用します")
    
    def tokenize_japanese_text(self, text: str) -> List[str]:
        """日本語テキストを単語に分割"""
        if not text or not text.strip():
            return []
        
        tokens = []
        
        # Janomeを使用した形態素解析
        if self.tokenizer:
            try:
                for token in self.tokenizer.tokenize(text, wakati=True):
                    if len(token) >= 2:  # 2文字以上の単語のみ
                        tokens.append(token)
            except Exception as e:
                logger.warning(f"形態素解析エラー: {e}")
        
        # フォールバック: 正規表現ベースの分割
        fallback_tokens = self._fallback_tokenize(text)
        tokens.extend(fallback_tokens)
        
        # N-gram分割も追加（文字レベル）
        ngram_tokens = self._generate_ngrams(text, n=2)
        tokens.extend(ngram_tokens)
        
        # 重複除去と短すぎる語の除外
        unique_tokens = list(set([t for t in tokens if len(t) >= 2]))
        
        logger.debug(f"テキスト分割結果: '{text}' -> {unique_tokens[:10]}...")
        return unique_tokens
    
    def _fallback_tokenize(self, text: str) -> List[str]:
        """フォールバック用の基本的なテキスト分割"""
        tokens = []
        
        # 漢字の連続
        kanji_matches = re.findall(r'[一-龠々〆〤]{2,}', text)
        tokens.extend(kanji_matches)
        
        # ひらがなの連続（3文字以上）
        hiragana_matches = re.findall(r'[ぁ-ん]{3,}', text)
        tokens.extend(hiragana_matches)
        
        # カタカナの連続（2文字以上）
        katakana_matches = re.findall(r'[ァ-ヶー]{2,}', text)
        tokens.extend(katakana_matches)
        
        # アルファベットの連続（2文字以上）
        alphabet_matches = re.findall(r'[a-zA-Z]{2,}', text)
        tokens.extend(alphabet_matches)
        
        # 数字を含む表現
        number_matches = re.findall(r'[0-9]+[円万千百十億兆台個件名人年月日時分秒]?', text)
        tokens.extend(number_matches)
        
        return tokens
    
    def _generate_ngrams(self, text: str, n: int = 2) -> List[str]:
        """N-gram分割"""
        if len(text) < n:
            return []
        
        ngrams = []
        for i in range(len(text) - n + 1):
            ngram = text[i:i + n]
            # 日本語文字のみのN-gramを生成
            if re.match(r'^[ぁ-んァ-ヶー一-龠々〆〤]+$', ngram):
                ngrams.append(ngram)
        
        return ngrams
    
    def normalize_company_terms(self, text: str) -> str:
        """会社名の正規化"""
        # 会社形態の統一
        company_patterns = {
            r'株式会社': ['(株)', 'カブシキガイシャ', 'ｶﾌﾞｼｷｶﾞｲｼｬ'],
            r'有限会社': ['(有)', 'ユウゲンガイシャ', 'ﾕｳｹﾞﾝｶﾞｲｼｬ'],
            r'合同会社': ['(同)', 'ゴウドウガイシャ', 'ｺﾞｳﾄﾞｳｶﾞｲｼｬ'],
            r'合資会社': ['(資)', 'ゴウシガイシャ', 'ｺﾞｳｼｶﾞｲｼｬ'],
            r'合名会社': ['(名)', 'ゴウメイガイシャ', 'ｺﾞｳﾒｲｶﾞｲｼｬ'],
        }
        
        normalized = text
        for standard, variants in company_patterns.items():
            for variant in variants:
                normalized = normalized.replace(variant, standard)
        
        return normalized


class EnhancedPostgreSQLSearch:
    """改善されたPostgreSQL検索システム"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.text_processor = EnhancedJapaneseTextProcessor()
        
    async def initialize(self):
        """検索システムの初期化"""
        try:
            # 必要な拡張の有効化
            await self._execute_sql("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            
            # 改善されたインデックス作成
            await self._execute_sql("""
                CREATE INDEX IF NOT EXISTS idx_chunks_content_trgm_enhanced 
                ON chunks USING gin (content gin_trgm_ops);
            """)
            
            await self._execute_sql("""
                CREATE INDEX IF NOT EXISTS idx_chunks_content_fulltext_japanese 
                ON chunks USING gin (to_tsvector('japanese', content));
            """)
            
            # 部分一致用のインデックス
            await self._execute_sql("""
                CREATE INDEX IF NOT EXISTS idx_chunks_content_like 
                ON chunks (content text_pattern_ops);
            """)
            
            logger.info("✅ Enhanced PostgreSQL Search初期化完了")
            return True
            
        except Exception as e:
            logger.error(f"❌ Enhanced PostgreSQL Search初期化エラー: {e}")
            return False
    
    async def _execute_sql(self, sql: str):
        """SQLを実行"""
        try:
            result = execute_query(sql)
            return result
        except Exception as e:
            logger.warning(f"SQL実行エラー（継続）: {e}")
            return None
    
    async def enhanced_search(self, 
                            query: str, 
                            company_id: int = None,
                            limit: int = 10, 
                            threshold: float = 0.2) -> List[Dict[str, Any]]:
        """
        改善された日本語対応検索
        
        Args:
            query: 検索クエリ
            company_id: 会社ID
            limit: 結果数制限
            threshold: 類似度閾値
        """
        try:
            # 1. クエリの前処理と正規化
            normalized_query = self.text_processor.normalize_company_terms(query)
            
            # 2. 形態素解析による単語分割
            query_tokens = self.text_processor.tokenize_japanese_text(normalized_query)
            
            if not query_tokens:
                query_tokens = [query]  # フォールバック
            
            logger.info(f"検索クエリ分割: '{query}' -> {query_tokens[:5]}...")
            
            # 3. 複数の検索手法を統合
            all_results = []
            
            # 3.1 原文検索
            original_results = await self._search_with_query(query, company_id, limit, threshold, "original")
            all_results.extend(original_results)
            
            # 3.2 正規化クエリ検索
            if normalized_query != query:
                normalized_results = await self._search_with_query(normalized_query, company_id, limit, threshold, "normalized")
                all_results.extend(normalized_results)
            
            # 3.3 分割された単語での検索
            for token in query_tokens[:5]:  # 上位5つの単語のみ
                token_results = await self._search_with_query(token, company_id, limit // 2, threshold, f"token_{token}")
                all_results.extend(token_results)
            
            # 4. 結果の統合と重複除去
            merged_results = self._merge_and_deduplicate(all_results, limit)
            
            logger.info(f"Enhanced Search実行完了: クエリ='{query}', 結果数={len(merged_results)}")
            return merged_results
            
        except Exception as e:
            logger.error(f"Enhanced Search実行エラー: {e}")
            return []
    
    async def _search_with_query(self, 
                               search_query: str, 
                               company_id: int = None,
                               limit: int = 10, 
                               threshold: float = 0.2,
                               search_type: str = "default") -> List[Dict[str, Any]]:
        """特定のクエリで検索実行"""
        try:
            # 会社IDフィルター条件
            company_filter = ""
            params = []
            param_idx = 1
            
            if company_id:
                company_filter = f" AND c.company_id = ${param_idx}"
                params.append(company_id)
                param_idx += 1
            
            # 検索クエリのパラメータ追加
            params.extend([search_query, search_query, search_query, search_query, threshold, limit])
            
            sql = f"""
            WITH enhanced_search_results AS (
                -- 1. 完全一致検索（最高スコア）
                SELECT 
                    c.id as chunk_id,
                    c.content,
                    ds.name as file_name,
                    1.0 as similarity_score,
                    'exact_match' as match_type,
                    c.company_id
                FROM chunks c
                LEFT JOIN document_sources ds ON c.doc_id = ds.id
                WHERE c.content IS NOT NULL 
                  AND c.content ILIKE '%' || ${param_idx-5} || '%'
                  AND ds.active = true
                  {company_filter}
                
                UNION ALL
                
                -- 2. Trigram類似度検索
                SELECT 
                    c.id as chunk_id,
                    c.content,
                    ds.name as file_name,
                    similarity(c.content, ${param_idx-4}) as similarity_score,
                    'trigram' as match_type,
                    c.company_id
                FROM chunks c
                LEFT JOIN document_sources ds ON c.doc_id = ds.id
                WHERE c.content IS NOT NULL 
                  AND similarity(c.content, ${param_idx-4}) > ${param_idx-1}
                  AND ds.active = true
                  {company_filter}
                
                UNION ALL
                
                -- 3. 全文検索（日本語対応）
                SELECT 
                    c.id as chunk_id,
                    c.content,
                    ds.name as file_name,
                    ts_rank(to_tsvector('japanese', c.content), plainto_tsquery('japanese', ${param_idx-3})) as similarity_score,
                    'fulltext' as match_type,
                    c.company_id
                FROM chunks c
                LEFT JOIN document_sources ds ON c.doc_id = ds.id
                WHERE c.content IS NOT NULL 
                  AND to_tsvector('japanese', c.content) @@ plainto_tsquery('japanese', ${param_idx-3})
                  AND ds.active = true
                  {company_filter}
                
                UNION ALL
                
                -- 4. 部分一致検索（曖昧検索）
                SELECT 
                    c.id as chunk_id,
                    c.content,
                    ds.name as file_name,
                    0.6 as similarity_score,
                    'partial_match' as match_type,
                    c.company_id
                FROM chunks c
                LEFT JOIN document_sources ds ON c.doc_id = ds.id
                WHERE c.content IS NOT NULL 
                  AND c.content ILIKE '%' || ${param_idx-2} || '%'
                  AND ds.active = true
                  {company_filter}
            )
            SELECT DISTINCT
                chunk_id,
                content,
                file_name,
                MAX(similarity_score) as max_score,
                array_agg(DISTINCT match_type) as match_types,
                company_id
            FROM enhanced_search_results
            GROUP BY chunk_id, content, file_name, company_id
            ORDER BY max_score DESC
            LIMIT ${param_idx};
            """
            
            # パラメータをSQLに埋め込み（Supabase用）
            formatted_sql = sql
            for i, param in enumerate(params):
                placeholder = f"${i+1}"
                if isinstance(param, str):
                    formatted_sql = formatted_sql.replace(placeholder, f"'{param}'")
                else:
                    formatted_sql = formatted_sql.replace(placeholder, str(param))
            
            rows = execute_query(formatted_sql)
            
            results = []
            for row in rows:
                results.append({
                    'chunk_id': row.get('chunk_id'),
                    'content': row.get('content'),
                    'file_name': row.get('file_name'),
                    'score': float(row.get('max_score', 0)),
                    'match_types': row.get('match_types', []),
                    'search_type': search_type,
                    'highlight': self._highlight_matches(row.get('content', ''), search_query),
                    'company_id': row.get('company_id')
                })
                
            return results
            
        except Exception as e:
            logger.error(f"検索実行エラー（{search_type}）: {e}")
            return []
    
    def _merge_and_deduplicate(self, all_results: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """結果の統合と重複除去"""
        seen_ids = set()
        merged_results = []
        
        # スコア順でソート
        all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        for result in all_results:
            chunk_id = result.get('chunk_id')
            if chunk_id and chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                merged_results.append(result)
                
                if len(merged_results) >= limit:
                    break
        
        return merged_results
    
    def _highlight_matches(self, content: str, query: str) -> str:
        """検索結果をハイライト"""
        try:
            if not content or not query:
                return content
            
            # 基本的なハイライト
            highlighted = content.replace(query, f"<mark>{query}</mark>")
            
            # 分割された単語もハイライト
            tokens = self.text_processor.tokenize_japanese_text(query)
            for token in tokens:
                if len(token) >= 2:
                    highlighted = highlighted.replace(token, f"<mark>{token}</mark>")
            
            return highlighted
        except:
            return content
    
    async def close(self):
        """接続を閉じる（Supabaseでは不要）"""
        pass


# グローバルインスタンス
enhanced_postgresql_search = EnhancedPostgreSQLSearch()

async def initialize_enhanced_postgresql_search():
    """Enhanced PostgreSQL Search初期化"""
    return await enhanced_postgresql_search.initialize()

async def enhanced_search_chunks(query: str, 
                               company_id: int = None, 
                               limit: int = 10, 
                               threshold: float = 0.2) -> List[Dict[str, Any]]:
    """Enhanced Search実行"""
    return await enhanced_postgresql_search.enhanced_search(query, company_id, limit, threshold) 