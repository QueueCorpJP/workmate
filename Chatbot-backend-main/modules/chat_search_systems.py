"""
チャット検索システム
各種検索システムの実装を管理します
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from .chat_config import (
    safe_print, HTTPException, get_db_cursor, model,
    DIRECT_SEARCH_AVAILABLE, PARALLEL_SEARCH_AVAILABLE, 
    ENHANCED_JAPANESE_SEARCH_AVAILABLE, VECTOR_SEARCH_AVAILABLE,
    DIRECT_VECTOR_SEARCH_AVAILABLE, PARALLEL_VECTOR_SEARCH_AVAILABLE
)
try:
    from .elasticsearch_search import (
        get_elasticsearch_fuzzy_search, elasticsearch_available
    )
    ELASTICSEARCH_IMPORT_AVAILABLE = True
except ImportError as e:
    ELASTICSEARCH_IMPORT_AVAILABLE = False
    def get_elasticsearch_fuzzy_search():
        return None
    def elasticsearch_available():
        return False
from .postgresql_fuzzy_search import fuzzy_search_chunks
# enhanced_postgresql_search module does not exist, using postgresql_fuzzy_search instead
from .postgresql_fuzzy_search import fuzzy_search_chunks as enhanced_search_chunks, initialize_postgresql_fuzzy as initialize_enhanced_postgresql_search

# 検索関数の条件付きインポート
if DIRECT_SEARCH_AVAILABLE:
    from .chat_config import direct_search
else:
    async def direct_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        return []

if PARALLEL_SEARCH_AVAILABLE:
    from .chat_config import parallel_search  
else:
    async def parallel_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        return []

if ENHANCED_JAPANESE_SEARCH_AVAILABLE:
    from .chat_config import enhanced_japanese_search
else:
    async def enhanced_japanese_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        return []

if VECTOR_SEARCH_AVAILABLE:
    from .chat_config import vector_search
else:
    async def vector_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        return []

async def direct_search_system(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    直接検索システム
    """
    if not DIRECT_SEARCH_AVAILABLE:
        safe_print("Direct search is not available")
        return []
    
    try:
        results = await direct_search(query, limit)
        safe_print(f"Direct search returned {len(results)} results")
        return results
    except Exception as e:
        safe_print(f"Error in direct search: {e}")
        return []

async def parallel_search_system(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    並列検索システム
    """
    if not PARALLEL_SEARCH_AVAILABLE:
        safe_print("Parallel search is not available")
        return []
    
    try:
        results = await parallel_search(query, limit)
        safe_print(f"Parallel search returned {len(results)} results")
        return results
    except Exception as e:
        safe_print(f"Error in parallel search: {e}")
        return []

async def enhanced_japanese_search_system(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    拡張日本語検索システム
    """
    if not ENHANCED_JAPANESE_SEARCH_AVAILABLE:
        safe_print("Enhanced Japanese search is not available")
        return []
    
    try:
        results = await enhanced_japanese_search(query, limit)
        safe_print(f"Enhanced Japanese search returned {len(results)} results")
        return results
    except Exception as e:
        safe_print(f"Error in enhanced Japanese search: {e}")
        return []

async def vector_search_system(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    ベクトル検索システム
    """
    if not VECTOR_SEARCH_AVAILABLE:
        safe_print("Vector search is not available")
        return []
    
    try:
        results = await vector_search(query, limit)
        safe_print(f"Vector search returned {len(results)} results")
        return results
    except Exception as e:
        safe_print(f"Error in vector search: {e}")
        return []

async def elasticsearch_fuzzy_search_system(query: str, 
                                           company_id: str = None,
                                           fuzziness: str = "AUTO",
                                           limit: int = 10) -> List[Dict[str, Any]]:
    """
    Elasticsearch Fuzzy検索システム
    """
    if not elasticsearch_available():
        safe_print("Elasticsearch is not available")
        return []
    
    try:
        es_search = get_elasticsearch_fuzzy_search()
        if not es_search:
            safe_print("Elasticsearch fuzzy search not initialized")
            return []
        
        results = await es_search.fuzzy_search(
            query=query,
            company_id=company_id,
            fuzziness=fuzziness,
            limit=limit
        )
        safe_print(f"Elasticsearch fuzzy search returned {len(results)} results")
        return results
    except Exception as e:
        safe_print(f"Error in Elasticsearch fuzzy search: {e}")
        return []

async def elasticsearch_advanced_search_system(query: str,
                                              company_id: str = None,
                                              search_type: str = "multi_match",
                                              fuzziness: str = "AUTO",
                                              limit: int = 10) -> List[Dict[str, Any]]:
    """
    Elasticsearch高度検索システム
    """
    if not elasticsearch_available():
        safe_print("Elasticsearch is not available")
        return []
    
    try:
        es_search = get_elasticsearch_fuzzy_search()
        if not es_search:
            safe_print("Elasticsearch fuzzy search not initialized")
            return []
        
        results = await es_search.advanced_search(
            query=query,
            company_id=company_id,
            search_type=search_type,
            fuzziness=fuzziness,
            limit=limit
        )
        safe_print(f"Elasticsearch advanced search returned {len(results)} results")
        return results
    except Exception as e:
        safe_print(f"Error in Elasticsearch advanced search: {e}")
        return []

async def postgresql_fuzzy_search_system(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    PostgreSQL Fuzzy検索システム（別サーバー不要！）
    """
    try:
        results = await fuzzy_search_chunks(query, limit)
        formatted_results = []
        
        for result in results:
            formatted_results.append({
                'id': result['chunk_id'],
                'title': result['file_name'],
                'content': result['content'],
                'url': '',
                'similarity': result['score'],
                'metadata': {
                    'source': 'postgresql_fuzzy_search',
                    'search_types': result.get('search_types', []),
                    'highlight': result.get('highlight', '')
                }
            })
            
        safe_print(f"PostgreSQL Fuzzy search returned {len(formatted_results)} results")
        return formatted_results
        
    except Exception as e:
        safe_print(f"Error in PostgreSQL Fuzzy search: {e}")
        return []

async def enhanced_postgresql_search_system(query: str, 
                                          company_id: int = None,
                                          limit: int = 10) -> List[Dict[str, Any]]:
    """
    Enhanced PostgreSQL検索システム（postgresql_fuzzy_searchを使用）
    """
    try:
        # Use fuzzy_search_chunks instead (company_id is not supported in fuzzy search)
        results = await enhanced_search_chunks(query, limit)
        formatted_results = []
        
        for result in results:
            formatted_results.append({
                'id': result['chunk_id'],
                'title': result['file_name'],
                'content': result['content'],
                'url': '',
                'similarity': result['score'],
                'metadata': {
                    'source': 'postgresql_fuzzy_search',
                    'search_types': result.get('search_types', []),
                    'highlight': result.get('highlight', ''),
                    'company_id': company_id  # Pass through for compatibility
                }
            })
            
        safe_print(f"Enhanced PostgreSQL search returned {len(formatted_results)} results")
        return formatted_results
        
    except Exception as e:
        safe_print(f"Error in Enhanced PostgreSQL search: {e}")
        return []

async def fallback_search_system(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    フォールバック検索システム - エンベディング検索のみを使用
    """
    search_systems = [
        ("Vector Search", vector_search_system),  # エンベディング検索のみ
    ]
    
    for system_name, search_func in search_systems:
        try:
            safe_print(f"Trying {system_name}...")
            results = await search_func(query, limit)
            if results:
                safe_print(f"{system_name} succeeded with {len(results)} results")
                return results
            else:
                safe_print(f"{system_name} returned no results")
        except Exception as e:
            safe_print(f"{system_name} failed: {e}")
            continue
    
    safe_print("All search systems failed")
    return []

async def multi_system_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    複数システム検索 - エンベディング検索のみを使用
    """
    search_tasks = []
    
    # Vector Search（エンベディング検索のみ）
    if VECTOR_SEARCH_AVAILABLE:
        search_tasks.append(vector_search_system(query, limit))
    else:
        safe_print("Vector search is not available")
        return []
    
    if not search_tasks:
        safe_print("No search systems available")
        return []
    
    try:
        # 並列実行
        results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # 結果をマージ（重複除去）
        merged_results = []
        seen_ids = set()
        
        for results in results_list:
            if isinstance(results, Exception):
                safe_print(f"Search system error: {results}")
                continue
            
            if isinstance(results, list):
                for result in results:
                    if isinstance(result, dict) and 'id' in result:
                        if result['id'] not in seen_ids:
                            seen_ids.add(result['id'])
                            merged_results.append(result)
        
        # スコア順でソート（エンベディング検索のみ）
        merged_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # 制限数まで切り詰め
        final_results = merged_results[:limit]
        safe_print(f"Multi-system search returned {len(final_results)} unique results")
        
        return final_results
        
    except Exception as e:
        safe_print(f"Error in multi-system search: {e}")
        return await fallback_search_system(query, limit)

async def database_search_fallback(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    データベース直接検索フォールバック（重要キーワード抽出対応）
    """
    try:
        cursor = get_db_cursor()
        if not cursor:
            safe_print("Database cursor not available")
            return []
        
        # 🔄 バリエーション生成を組み込み
        try:
            from .question_variants_generator import generate_question_variants
            safe_print(f"Generating query variants for: {query}")
            variants_result = await generate_question_variants(query)
            search_terms = variants_result.all_variants
            safe_print(f"Generated {len(search_terms)} query variants")
        except Exception as e:
            safe_print(f"Variant generation failed, using original query: {e}")
            search_terms = [query]
        
        # 🎯 重要キーワード抽出: 長い文章から重要な単語のみを抽出
        important_keywords = []
        
        # 元のクエリから重要キーワードを抽出
        query_keywords = extract_important_keywords(query)
        important_keywords.extend(query_keywords)
        
        # バリエーションからも重要キーワードを抽出（長い文章は除外）
        for term in search_terms:
            if len(term) <= 10:  # 10文字以下の短い語句のみ使用
                important_keywords.append(term)
            else:
                # 長い文章からキーワードを抽出
                term_keywords = extract_important_keywords(term)
                important_keywords.extend(term_keywords)
        
        # 重複を除去し、最大10個に制限
        important_keywords = list(set(important_keywords))[:10]
        safe_print(f"Extracted important keywords: {important_keywords}")
        
        if not important_keywords:
            important_keywords = [query]  # フォールバック
        
        # 🔍 重要キーワードによるスマートスコアリング検索
        # 各キーワードをOR条件で検索し、複数マッチにボーナスを付与
        keyword_conditions = []
        parameters = []
        
        for i, keyword in enumerate(important_keywords):
            keyword_conditions.append(f"c.content ILIKE %s")
            parameters.append(f"%{keyword}%")
        
        # SQL文を構築
        sql_query = f"""
            SELECT 
                c.id,
                ds.name as title,
                c.content,
                '' as url,
                -- スコアリング: 複数キーワードマッチにボーナス
               CASE 
                    {' + '.join([f"WHEN c.content ILIKE %s THEN 1.0" for _ in important_keywords])}
                    ELSE 0.0
               END as rank
        FROM chunks c
        LEFT JOIN document_sources ds ON c.doc_id = ds.id
        WHERE c.content IS NOT NULL 
          AND LENGTH(c.content) > 10
          AND ds.active = true
              AND ({' OR '.join(keyword_conditions)})
        ORDER BY rank DESC, LENGTH(c.content) DESC
        LIMIT %s
        """
        
        # パラメータを構築（スコアリング用 + 条件用 + LIMIT用）
        all_parameters = []
        # スコアリング用パラメータ
        for keyword in important_keywords:
            all_parameters.append(f"%{keyword}%")
        # 条件用パラメータ
        all_parameters.extend(parameters)
        # LIMIT用パラメータ
        all_parameters.append(limit)
        
        safe_print(f"Executing SQL search with {len(important_keywords)} keywords")
        cursor.execute(sql_query, all_parameters)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'title': row[1] or 'Unknown Document',
                'content': row[2] or '',
                'url': row[3] or '',
                'similarity': float(row[4]) if row[4] else 0.0,
                'metadata': {
                    'source': 'database_search_fallback',
                    'keywords': important_keywords
                }
            })
        
        safe_print(f"Database search found {len(results)} results")
        return results
        
    except Exception as e:
        safe_print(f"Database search error: {e}")
        return []

def extract_important_keywords(text: str) -> List[str]:
    """
    テキストから重要なキーワードを抽出
    """
    import re
    
    # 基本的なキーワード抽出
    keywords = []
    
    # 名詞的な単語を抽出（日本語の場合）
    # カタカナ語（3文字以上）
    katakana_words = re.findall(r'[ァ-ヶー]{3,}', text)
    keywords.extend(katakana_words)
    
    # 漢字を含む単語（2文字以上）
    kanji_words = re.findall(r'[一-龠]{2,}', text)
    keywords.extend(kanji_words)
    
    # ひらがな（特定の重要語）
    important_hiragana = ['やすい', 'たかい', 'おおきい', 'ちいさい', 'あたらしい', 'ふるい']
    for word in important_hiragana:
        if word in text:
            keywords.append(word)
    
    # アルファベット（2文字以上）
    alphabet_words = re.findall(r'[a-zA-Z]{2,}', text)
    keywords.extend(alphabet_words)
    
    # 数字を含む語
    number_words = re.findall(r'[0-9]+[円万千百十億兆台個件名人]', text)
    keywords.extend(number_words)
    
    # 特別な語彙
    special_words = ['安い', 'パソコン', 'PC', '価格', '値段', '料金', '費用', 'コスト']
    for word in special_words:
        if word in text:
            keywords.append(word)
    
    # 重複を除去し、空文字列を除外
    keywords = list(set([k for k in keywords if k.strip()]))
    
    return keywords[:5]  # 最大5個

async def smart_search_system(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    スマート検索システム - エンベディング検索のみを使用
    """
    safe_print(f"Starting smart search for query: {query}")
    
    # エンベディング検索のみを使用
    if VECTOR_SEARCH_AVAILABLE:
        safe_print("Using Vector Search (embedding-based) as primary search")
        return await vector_search_system(query, limit)
    else:
        safe_print("Vector search is not available")
        return []