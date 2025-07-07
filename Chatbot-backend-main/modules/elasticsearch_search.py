"""
Elasticsearch検索モジュール
Fuzzy searchとadvanced query機能を提供
"""

import os
import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Elasticsearchの条件付きインポート
try:
    from elasticsearch import Elasticsearch
    from elasticsearch_dsl import Search, Q, Document, Text, Keyword, Integer, Float, Date, Index
    from elasticsearch_dsl.connections import connections
    ELASTICSEARCH_AVAILABLE = True
except ImportError as e:
    ELASTICSEARCH_AVAILABLE = False
    # ダミークラス定義
    class Elasticsearch:
        def __init__(self, *args, **kwargs):
            pass
        def ping(self):
            return False
        def indices(self):
            return self
        def exists(self, *args, **kwargs):
            return False
        def create(self, *args, **kwargs):
            pass
        def search(self, *args, **kwargs):
            return {'hits': {'hits': []}}

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class ElasticsearchManager:
    """Elasticsearch管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.es_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
        self.es_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
        self.es_user = os.getenv("ELASTICSEARCH_USER", "elastic")
        self.es_password = os.getenv("ELASTICSEARCH_PASSWORD", "")
        self.es_scheme = os.getenv("ELASTICSEARCH_SCHEME", "http")
        self.index_name = os.getenv("ELASTICSEARCH_INDEX", "workmate_documents")
        
        # Elasticsearchクライアントの初期化
        self.es = None
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # データベース接続設定
        self.db_url = self._get_db_url()
        
        self._init_elasticsearch()
    
    def _get_db_url(self) -> str:
        """データベースURL構築"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL と SUPABASE_KEY が必要です")
        
        if "supabase.co" in supabase_url:
            project_id = supabase_url.split("://")[1].split(".")[0]
            db_password = os.getenv('DB_PASSWORD', '')
            return f"postgresql://postgres.{project_id}:{db_password}@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"
        else:
            return os.getenv("DATABASE_URL", "")
    
    def _init_elasticsearch(self):
        """Elasticsearchクライアントの初期化"""
        if not ELASTICSEARCH_AVAILABLE:
            logger.warning("⚠️ Elasticsearchモジュールが利用できません")
            self.es = None
            return
            
        try:
            # 認証情報の設定
            if self.es_user and self.es_password:
                auth = (self.es_user, self.es_password)
            else:
                auth = None
            
            # Elasticsearchクライアント作成
            self.es = Elasticsearch(
                hosts=[{
                    'host': self.es_host,
                    'port': self.es_port,
                    'scheme': self.es_scheme
                }],
                http_auth=auth,
                verify_certs=False,
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # 接続テスト
            if self.es.ping():
                logger.info(f"✅ Elasticsearch接続成功: {self.es_host}:{self.es_port}")
                if ELASTICSEARCH_AVAILABLE:
                    connections.add_connection('default', self.es)
                
                # インデックスの作成
                self._create_index()
            else:
                logger.error("❌ Elasticsearch接続失敗")
                self.es = None
        
        except Exception as e:
            logger.error(f"❌ Elasticsearch初期化エラー: {e}")
            self.es = None
    
    def _create_index(self):
        """インデックスの作成"""
        try:
            # インデックスが存在しない場合は作成
            if not self.es.indices.exists(index=self.index_name):
                # 日本語解析用のマッピング設定
                mapping = {
                    "settings": {
                        "analysis": {
                            "analyzer": {
                                "japanese_analyzer": {
                                    "type": "custom",
                                    "tokenizer": "kuromoji_tokenizer",
                                    "filter": [
                                        "kuromoji_baseform",
                                        "kuromoji_part_of_speech",
                                        "kuromoji_stemmer",
                                        "lowercase",
                                        "cjk_width"
                                    ]
                                },
                                "ngram_analyzer": {
                                    "type": "custom",
                                    "tokenizer": "ngram_tokenizer",
                                    "filter": ["lowercase"]
                                }
                            },
                            "tokenizer": {
                                "ngram_tokenizer": {
                                    "type": "ngram",
                                    "min_gram": 2,
                                    "max_gram": 3,
                                    "token_chars": ["letter", "digit"]
                                }
                            }
                        },
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    },
                    "mappings": {
                        "properties": {
                            "chunk_id": {"type": "keyword"},
                            "document_id": {"type": "keyword"},
                            "document_name": {"type": "text", "analyzer": "japanese_analyzer"},
                            "document_type": {"type": "keyword"},
                            "chunk_index": {"type": "integer"},
                            "content": {
                                "type": "text",
                                "analyzer": "japanese_analyzer",
                                "fields": {
                                    "ngram": {
                                        "type": "text",
                                        "analyzer": "ngram_analyzer"
                                    },
                                    "raw": {
                                        "type": "keyword"
                                    }
                                }
                            },
                            "company_id": {"type": "keyword"},
                            "created_at": {"type": "date"},
                            "updated_at": {"type": "date"},
                            "embedding": {"type": "dense_vector", "dims": 768},
                            "special": {"type": "boolean"}
                        }
                    }
                }
                
                self.es.indices.create(
                    index=self.index_name,
                    body=mapping
                )
                logger.info(f"✅ インデックス作成完了: {self.index_name}")
            else:
                logger.info(f"📋 インデックス既存: {self.index_name}")
        
        except Exception as e:
            logger.error(f"❌ インデックス作成エラー: {e}")
    
    def is_available(self) -> bool:
        """Elasticsearchが利用可能かチェック"""
        return self.es is not None and self.es.ping()
    
    async def sync_database_to_elasticsearch(self, company_id: str = None):
        """データベースからElasticsearchに同期"""
        try:
            if not self.is_available():
                logger.error("❌ Elasticsearch利用不可")
                return False
            
            if not PSYCOPG2_AVAILABLE:
                logger.error("❌ psycopg2利用不可")
                return False
            
            logger.info("🔄 データベースからElasticsearchへの同期開始")
            
            # データベースからチャンクデータを取得
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    sql = """
                    SELECT 
                        c.id as chunk_id,
                        c.doc_id as document_id,
                        c.chunk_index,
                        c.content,
                        c.company_id,
                        c.embedding,
                        c.created_at,
                        c.updated_at,
                        ds.name as document_name,
                        ds.type as document_type,
                        ds.special
                    FROM chunks c
                    LEFT JOIN document_sources ds ON c.doc_id = ds.id
                    WHERE c.content IS NOT NULL
                    """
                    
                    params = []
                    if company_id:
                        sql += " AND c.company_id = %s"
                        params.append(company_id)
                    
                    cur.execute(sql, params)
                    rows = cur.fetchall()
                    
                    logger.info(f"📊 同期対象: {len(rows)}件")
                    
                    # バッチでElasticsearchにインデックス
                    batch_size = 100
                    for i in range(0, len(rows), batch_size):
                        batch = rows[i:i + batch_size]
                        await self._index_batch(batch)
                        logger.info(f"📝 進捗: {i + len(batch)}/{len(rows)}")
                    
                    logger.info("✅ 同期完了")
                    return True
        
        except Exception as e:
            logger.error(f"❌ 同期エラー: {e}")
            return False
    
    async def _index_batch(self, batch: List[Dict]):
        """バッチでのインデックス処理"""
        try:
            if not ELASTICSEARCH_AVAILABLE:
                logger.warning("⚠️ Elasticsearchが利用できないため、バッチインデックスをスキップします")
                return
                
            actions = []
            
            for row in batch:
                doc = {
                    "_index": self.index_name,
                    "_id": row['chunk_id'],
                    "_source": {
                        "chunk_id": row['chunk_id'],
                        "document_id": row['document_id'],
                        "document_name": row['document_name'] or 'Unknown',
                        "document_type": row['document_type'] or 'unknown',
                        "chunk_index": row['chunk_index'],
                        "content": row['content'],
                        "company_id": row['company_id'],
                        "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                        "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None,
                        "embedding": row['embedding'] if row['embedding'] else None,
                        "special": row['special'] or False
                    }
                }
                actions.append(doc)
            
            # バルクインデックス
            try:
                from elasticsearch.helpers import bulk
                bulk(self.es, actions)
            except ImportError:
                logger.warning("⚠️ elasticsearch.helpersが利用できません")
            
        except Exception as e:
            logger.error(f"❌ バッチインデックスエラー: {e}")

class ElasticsearchFuzzySearch:
    """Elasticsearch Fuzzy Search機能"""
    
    def __init__(self, es_manager: ElasticsearchManager):
        self.es_manager = es_manager
        self.es = es_manager.es
        self.index_name = es_manager.index_name
    
    async def fuzzy_search(self, 
                          query: str, 
                          company_id: str = None,
                          fuzziness: str = "AUTO",
                          limit: int = 20) -> List[Dict]:
        """
        Fuzzy search実行
        
        Args:
            query: 検索クエリ
            company_id: 会社ID
            fuzziness: ファジネス設定 ("AUTO", "0", "1", "2")
            limit: 結果件数
        
        Returns:
            検索結果リスト
        """
        try:
            if not self.es_manager.is_available():
                logger.error("❌ Elasticsearch利用不可")
                return []
            
            logger.info(f"🔍 Fuzzy Search実行: '{query}' (fuzziness: {fuzziness})")
            
            # 検索クエリ構築
            search_query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["content^3", "document_name^2", "content.ngram"],
                                    "fuzziness": fuzziness,
                                    "type": "best_fields",
                                    "operator": "or"
                                }
                            }
                        ]
                    }
                },
                "highlight": {
                    "fields": {
                        "content": {
                            "fragment_size": 200,
                            "number_of_fragments": 3
                        }
                    }
                },
                "size": limit,
                "sort": [
                    {"_score": {"order": "desc"}},
                    {"created_at": {"order": "desc"}}
                ]
            }
            
            # 会社IDフィルタ
            if company_id:
                search_query["query"]["bool"]["filter"] = [
                    {"term": {"company_id": company_id}}
                ]
            
            # 検索実行
            result = self.es.search(
                index=self.index_name,
                body=search_query
            )
            
            # 結果の整形
            search_results = []
            for hit in result['hits']['hits']:
                source = hit['_source']
                
                # ハイライト情報の取得
                highlight = hit.get('highlight', {})
                highlighted_content = highlight.get('content', [])
                
                search_results.append({
                    'chunk_id': source['chunk_id'],
                    'document_id': source['document_id'],
                    'document_name': source['document_name'],
                    'document_type': source['document_type'],
                    'chunk_index': source['chunk_index'],
                    'content': source['content'],
                    'highlighted_content': highlighted_content,
                    'similarity_score': hit['_score'],
                    'search_type': 'elasticsearch_fuzzy',
                    'fuzziness': fuzziness,
                    'metadata': {
                        'company_id': source.get('company_id'),
                        'created_at': source.get('created_at'),
                        'special': source.get('special', False)
                    }
                })
            
            logger.info(f"✅ Fuzzy Search完了: {len(search_results)}件")
            return search_results
        
        except Exception as e:
            logger.error(f"❌ Fuzzy Search エラー: {e}")
            return []
    
    async def advanced_search(self, 
                            query: str,
                            company_id: str = None,
                            search_type: str = "multi_match",
                            fuzziness: str = "AUTO",
                            limit: int = 20) -> List[Dict]:
        """
        高度な検索機能
        
        Args:
            query: 検索クエリ
            company_id: 会社ID
            search_type: 検索タイプ ("multi_match", "phrase", "wildcard", "regex")
            fuzziness: ファジネス設定
            limit: 結果件数
        """
        try:
            if not self.es_manager.is_available():
                return []
            
            logger.info(f"🔍 Advanced Search: '{query}' (type: {search_type})")
            
            # 検索タイプに応じたクエリ構築
            if search_type == "multi_match":
                query_part = {
                    "multi_match": {
                        "query": query,
                        "fields": ["content^3", "document_name^2", "content.ngram"],
                        "fuzziness": fuzziness,
                        "type": "best_fields"
                    }
                }
            elif search_type == "phrase":
                query_part = {
                    "match_phrase": {
                        "content": {
                            "query": query,
                            "slop": 2
                        }
                    }
                }
            elif search_type == "wildcard":
                query_part = {
                    "wildcard": {
                        "content": {
                            "value": f"*{query}*",
                            "case_insensitive": True
                        }
                    }
                }
            elif search_type == "regex":
                query_part = {
                    "regexp": {
                        "content": {
                            "value": query,
                            "case_insensitive": True
                        }
                    }
                }
            else:
                # デフォルトはmulti_match
                query_part = {
                    "multi_match": {
                        "query": query,
                        "fields": ["content^3", "document_name^2"],
                        "fuzziness": fuzziness
                    }
                }
            
            search_query = {
                "query": {
                    "bool": {
                        "must": [query_part]
                    }
                },
                "highlight": {
                    "fields": {
                        "content": {
                            "fragment_size": 200,
                            "number_of_fragments": 3
                        }
                    }
                },
                "size": limit,
                "sort": [
                    {"_score": {"order": "desc"}},
                    {"created_at": {"order": "desc"}}
                ]
            }
            
            # 会社IDフィルタ
            if company_id:
                search_query["query"]["bool"]["filter"] = [
                    {"term": {"company_id": company_id}}
                ]
            
            # 検索実行
            result = self.es.search(
                index=self.index_name,
                body=search_query
            )
            
            # 結果の整形
            search_results = []
            for hit in result['hits']['hits']:
                source = hit['_source']
                
                search_results.append({
                    'chunk_id': source['chunk_id'],
                    'document_id': source['document_id'],
                    'document_name': source['document_name'],
                    'document_type': source['document_type'],
                    'chunk_index': source['chunk_index'],
                    'content': source['content'],
                    'highlighted_content': hit.get('highlight', {}).get('content', []),
                    'similarity_score': hit['_score'],
                    'search_type': f'elasticsearch_{search_type}',
                    'fuzziness': fuzziness,
                    'metadata': {
                        'company_id': source.get('company_id'),
                        'created_at': source.get('created_at'),
                        'special': source.get('special', False)
                    }
                })
            
            logger.info(f"✅ Advanced Search完了: {len(search_results)}件")
            return search_results
        
        except Exception as e:
            logger.error(f"❌ Advanced Search エラー: {e}")
            return []

# グローバルインスタンス
_elasticsearch_manager = None
_elasticsearch_fuzzy_search = None

def get_elasticsearch_manager() -> Optional[ElasticsearchManager]:
    """Elasticsearchマネージャーを取得"""
    global _elasticsearch_manager
    
    if _elasticsearch_manager is None:
        try:
            _elasticsearch_manager = ElasticsearchManager()
            logger.info("✅ Elasticsearchマネージャー初期化完了")
        except Exception as e:
            logger.error(f"❌ Elasticsearchマネージャー初期化エラー: {e}")
            return None
    
    return _elasticsearch_manager

def get_elasticsearch_fuzzy_search() -> Optional[ElasticsearchFuzzySearch]:
    """Elasticsearch Fuzzy Searchを取得"""
    global _elasticsearch_fuzzy_search
    
    if _elasticsearch_fuzzy_search is None:
        es_manager = get_elasticsearch_manager()
        if es_manager and es_manager.is_available():
            _elasticsearch_fuzzy_search = ElasticsearchFuzzySearch(es_manager)
            logger.info("✅ Elasticsearch Fuzzy Search初期化完了")
        else:
            logger.error("❌ Elasticsearch Fuzzy Search初期化失敗")
            return None
    
    return _elasticsearch_fuzzy_search

def elasticsearch_available() -> bool:
    """Elasticsearchが利用可能かチェック"""
    try:
        if not ELASTICSEARCH_AVAILABLE:
            return False
            
        es_manager = get_elasticsearch_manager()
        return es_manager is not None and es_manager.is_available()
    except Exception:
        return False 