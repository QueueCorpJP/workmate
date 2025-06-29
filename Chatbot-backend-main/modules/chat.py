"""
チャットモジュール
チャット機能とAI応答生成を管理します
"""
import json
import re
import uuid
import sys
from datetime import datetime
import logging
# PostgreSQL関連のインポート
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException, Depends
from .company import DEFAULT_COMPANY_NAME
from .models import ChatMessage, ChatResponse
from .database import get_db, update_usage_count, get_usage_limits
from .knowledge_base import knowledge_base, get_active_resources
from .auth import check_usage_limits
from .resource import get_active_resources_by_company_id, get_active_resources_content_by_ids, get_active_resource_names_by_company_id
from .company import get_company_by_id
import os
import asyncio
import google.generativeai as genai
from .config import setup_gemini
from .utils import safe_print, safe_safe_print

# 🚀 新しいリアルタイムRAGシステムのインポートを追加（最優先）
try:
    from .realtime_rag import process_question_realtime, realtime_rag_available
    REALTIME_RAG_AVAILABLE = realtime_rag_available()
    if REALTIME_RAG_AVAILABLE:
        safe_print("✅ リアルタイムRAGシステムが利用可能です")
    else:
        safe_print("⚠️ リアルタイムRAGシステムの設定が不完全です")
except ImportError as e:
    REALTIME_RAG_AVAILABLE = False
    safe_print(f"⚠️ リアルタイムRAGシステムが利用できません: {e}")

# 新しいRAGシステムのインポートを追加（フォールバック用）
try:
    from .rag_enhanced import enhanced_rag, SearchResult
    RAG_ENHANCED_AVAILABLE = True
except ImportError:
    RAG_ENHANCED_AVAILABLE = False
    safe_print("⚠️ 強化RAGシステムが利用できないため、従来のRAGを使用します")

# 高速化RAGシステムのインポートを追加（正確性重視のため無効化）
try:
    from .rag_optimized import high_speed_rag
    SPEED_RAG_AVAILABLE = False  # 正確性重視のため強制的に無効化
    safe_print("⚠️ 高速化RAGシステムは正確性重視のため無効化されています")
except ImportError:
    SPEED_RAG_AVAILABLE = False
    safe_print("⚠️ 高速化RAGシステムが利用できません")

# ベクトル検索システムのインポートを追加（フォールバック用）
try:
    from .vector_search import get_vector_search_instance, vector_search_available
    VECTOR_SEARCH_AVAILABLE = vector_search_available()
    if VECTOR_SEARCH_AVAILABLE:
        safe_print("✅ ベクトル検索システムが利用可能です")
    else:
        safe_print("⚠️ ベクトル検索システムの設定が不完全です")
except ImportError as e:
    VECTOR_SEARCH_AVAILABLE = False
    safe_print(f"⚠️ ベクトル検索システムが利用できません: {e}")

# 並列ベクトル検索システムのインポートを追加（フォールバック用）
try:
    from .parallel_vector_search import get_parallel_vector_search_instance_sync, ParallelVectorSearchSystem
    PARALLEL_VECTOR_SEARCH_AVAILABLE = True
    safe_print("✅ 並列ベクトル検索システムが利用可能です")
except ImportError as e:
    PARALLEL_VECTOR_SEARCH_AVAILABLE = False
    safe_print(f"⚠️ 並列ベクトル検索システムが利用できません: {e}")

logger = logging.getLogger(__name__)

def safe_print(text):
    """Windows環境でのUnicode文字エンコーディング問題を回避する安全なprint関数"""
    try:
        print(text)
    except UnicodeEncodeError:
        # エンコーディングエラーが発生した場合は、問題のある文字を置換
        try:
            safe_text = str(text).encode('utf-8', errors='replace').decode('utf-8')
            print(safe_text)
        except:
            # それでも失敗する場合はエラーメッセージのみ出力
            print("[出力エラー: Unicode文字を含むメッセージ]")

def safe_safe_print(text):
    """Windows環境でのUnicode文字エンコーディング問題を回避する安全なsafe_print関数"""
    safe_print(text)

async def realtime_rag_search(query: str, company_id: str = None, company_name: str = "お客様の会社", max_results: int = 10) -> str:
    """
    🚀 リアルタイムRAG検索 - 新しい最適化されたRAGフロー
    Step 1〜5の完全なリアルタイム処理
    """
    safe_print(f"🚀 リアルタイムRAG検索開始: '{query[:50]}...'")
    
    if not query or not query.strip():
        safe_print("❌ 空のクエリ")
        return "質問を入力してください。"
    
    # 🚀 【最優先】リアルタイムRAGシステムを実行
    if REALTIME_RAG_AVAILABLE:
        try:
            safe_print("⚡ リアルタイムRAGシステム実行中...")
            
            # リアルタイムRAG処理を実行
            result = await process_question_realtime(
                question=query,
                company_id=company_id,
                company_name=company_name,
                top_k=max_results * 2  # 検索精度向上のため拡大
            )
            
            if result and result.get("answer"):
                answer = result["answer"]
                status = result.get("status", "unknown")
                
                if status == "completed":
                    safe_print(f"✅ リアルタイムRAG成功: {len(answer)}文字の回答を取得")
                    safe_print(f"📊 使用チャンク数: {result.get('chunks_used', 0)}")
                    safe_print(f"📊 最高類似度: {result.get('top_similarity', 0.0):.3f}")
                    return answer
                else:
                    safe_print(f"⚠️ リアルタイムRAGエラー: {result.get('error', 'Unknown error')}")
                    # エラーでも回答があれば返す
                    return answer
            else:
                safe_print("❌ リアルタイムRAG結果が空")
        
        except Exception as e:
            safe_print(f"❌ リアルタイムRAGエラー: {e}")
    else:
        safe_print("❌ リアルタイムRAGシステムが利用できません")
    
    # フォールバック: 従来のRAG検索システムを使用
    safe_print("⚠️ フォールバック: 従来のRAG検索システムを使用")
    return simple_rag_search_fallback("", query, max_results, company_id)

def simple_rag_search_fallback(knowledge_text: str, query: str, max_results: int = 20, company_id: str = None) -> str:
    """
    🔄 フォールバック用の従来RAG検索 - 並列ベクトル検索優先、フォールバックで従来検索
    """
    # デバッグ: 関数開始を確認
    safe_print(f"🔄 フォールバックRAG検索開始 (並列検索対応)")
    safe_print(f"📥 入力パラメータ:")
    safe_print(f"   knowledge_text長: {len(knowledge_text) if knowledge_text else 0} 文字")
    safe_print(f"   query: '{query}'")
    safe_print(f"   max_results: {max_results}")
    safe_print(f"   company_id: {company_id}")
    
    if not query:
        safe_print(f"❌ 早期リターン: query={bool(query)}")
        return "質問を入力してください。"
    
    # 🚀 【優先】並列ベクトル検索を実行
    if PARALLEL_VECTOR_SEARCH_AVAILABLE:
        try:
            safe_print("⚡ 並列ベクトル検索システム実行中...")
            
            # 同期版並列検索を使用（イベントループ問題を回避）
            from .parallel_vector_search import get_parallel_vector_search_instance_sync
            
            parallel_search_system = get_parallel_vector_search_instance_sync()
            if parallel_search_system:
                safe_print("✅ 並列ベクトル検索インスタンス取得成功")
                parallel_result = parallel_search_system.parallel_comprehensive_search_sync(
                    query, company_id, max_results
                )
                
                if parallel_result and len(parallel_result.strip()) > 0:
                    safe_print(f"✅ 並列ベクトル検索成功: {len(parallel_result)}文字の結果を取得")
                    return parallel_result
                else:
                    safe_print("⚠️ 並列ベクトル検索結果が空 - 従来検索にフォールバック")
            else:
                safe_print("❌ 並列ベクトル検索インスタンス取得失敗")
        
        except Exception as e:
            safe_print(f"❌ 並列ベクトル検索エラー: {e}")
            safe_print("⚠️ 従来検索にフォールバック")
    
    # 🔍 【フォールバック】単一ベクトル検索を試行
    if VECTOR_SEARCH_AVAILABLE:
        try:
            safe_print("🔍 ベクトル検索を強制実行中...")
            safe_print(f"   company_id: {company_id}")
            
            vector_search_system = get_vector_search_instance()
            if vector_search_system:
                safe_print("✅ ベクトル検索インスタンス取得成功")
                
                # company_idなしでも実行（デバッグ用）
                vector_result = vector_search_system.get_document_content_by_similarity(
                    query, company_id, max_results
                )
                
                safe_print(f"🔍 ベクトル検索結果: {len(vector_result) if vector_result else 0}文字")
                
                if vector_result and len(vector_result.strip()) > 0:
                    safe_print(f"✅ ベクトル検索成功: {len(vector_result)}文字の結果を取得")
                    return vector_result
                else:
                    safe_print("❌ ベクトル検索結果が空 - エラーとして処理")
                    return "❌ ベクトル検索でデータが見つかりませんでした。データベース接続やエンベディングデータを確認してください。"
            else:
                safe_print("❌ ベクトル検索インスタンス取得失敗")
                return "❌ ベクトル検索システムの初期化に失敗しました。"
        except Exception as e:
            safe_print(f"❌ ベクトル検索エラー: {e}")
            return f"❌ ベクトル検索エラー: {e}"
    else:
        safe_print("❌ ベクトル検索が利用できません")
        return "❌ ベクトル検索システムが利用できません。設定を確認してください。"

def simple_rag_search(knowledge_text: str, query: str, max_results: int = 5, company_id: str = None) -> str:
    """
    🚀 RAG検索のメインエントリーポイント - リアルタイムRAG優先
    """
    # 非同期処理が必要な場合は、同期ラッパーを使用
    try:
        # イベントループが既に実行中かチェック
        loop = asyncio.get_running_loop()
        # 既にイベントループが実行中の場合は、フォールバックを使用
        safe_print("⚠️ イベントループ実行中のため、フォールバックRAGを使用")
        return simple_rag_search_fallback(knowledge_text, query, max_results, company_id)
    except RuntimeError:
        # イベントループが実行されていない場合は、新しいループで実行
        try:
            return asyncio.run(realtime_rag_search(query, company_id, "お客様の会社", max_results))
        except Exception as e:
            safe_print(f"❌ リアルタイムRAG実行エラー: {e}")
            return simple_rag_search_fallback(knowledge_text, query, max_results, company_id)
    
    # 詳細デバッグ情報を追加
    safe_print(f"🔍 RAG検索デバッグ開始")
    safe_print(f"📊 元の知識ベースサイズ: {len(knowledge_text):,}文字")
    safe_print(f"🎯 検索クエリ: '{query}'")
    
    # 正確性重視のため、高速RAGは使用せず従来のRAG検索のみを使用
    try:
        import bm25s
        import re
        
        # 🔍 改善: より柔軟なクエリ前処理
        processed_query = _preprocess_query(query)
        safe_print(f"🔍 クエリ前処理: '{query}' → '{processed_query}'")
        
        # ⚡ 修正: 既に500文字でチャンク化されたテキストをそのまま使用
        # 改行ベースで軽微な分割のみ実行（大きな再分割は不要）
        chunks = [chunk.strip() for chunk in knowledge_text.split('\n\n') if chunk.strip()]
        
        # チャンクが空の場合は行分割にフォールバック
        if not chunks:
            chunks = [line.strip() for line in knowledge_text.split('\n') if len(line.strip()) > 30]
        
        safe_print(f"📊 軽微分割結果: {len(chunks)}個のセクション (800文字チャンク済み)")
        
        if len(chunks) < 2:
            # チャンクが少ない場合は全体を返す（最大20万文字）
            return knowledge_text[:200000]
        
        # 🚀 ハイブリッド検索の実行（検索結果を大幅に増やす）
        search_results_count = min(max_results * 5, len(chunks))  # 2倍→5倍に増加
        bm25_results = _bm25_search(chunks, processed_query, search_results_count)
        semantic_results = _semantic_search(chunks, processed_query, search_results_count)
        
        safe_print(f"📊 BM25検索結果: {len(bm25_results)}件")
        safe_print(f"📊 セマンティック検索結果: {len(semantic_results)}件")
        
        # 上位3件の検索結果をデバッグ出力
        safe_print(f"🔍 BM25上位3件の内容プレビュー:")
        for i, result in enumerate(bm25_results[:3]):
            preview = result['content'][:200].replace('\n', ' ')
            safe_print(f"  {i+1}. スコア:{result['score']:.3f} 内容: {preview}...")
        
        safe_print(f"🔍 セマンティック上位3件の内容プレビュー:")
        for i, result in enumerate(semantic_results[:3]):
            preview = result['content'][:200].replace('\n', ' ')
            safe_print(f"  {i+1}. スコア:{result['score']:.3f} 内容: {preview}...")
        
        # 結果の統合と再ランキング
        combined_results = _combine_search_results(bm25_results, semantic_results, processed_query, max_results)
        
        safe_print(f"📊 統合後の結果: {len(combined_results)}件")
        
        # 🔍 完全検索: 全ての関連チャンクを取得（包括的検索）
        result_chunks = []
        total_length = 0
        max_length = 300000  # 30万文字制限（Gemini制限対応）
        
        # 統合結果から最良のチャンクを選択（より多くのチャンクを採用）
        for i, result in enumerate(combined_results):
            chunk = result['content']
            score = result['score']
            
            safe_print(f"🎯 統合結果{i+1}: スコア{score:.3f}, 長さ{len(chunk)}文字")
            if i < 5:  # 上位5件の内容をプレビュー（デバッグ拡大）
                preview = chunk[:300].replace('\n', ' ')
                safe_print(f"   内容プレビュー: {preview}...")
            
            # より多くのチャンクを採用（最低30個→50個に増加）
            if total_length + len(chunk) > max_length and len(result_chunks) >= 50:
                safe_print(f"🔍 文字数制限到達: {total_length:,}文字 (制限: {max_length:,}文字)")
                break
            
            # スコアが非常に低い場合のみ除外（0.05以下）
            if score >= 0.05:  # 閾値を大幅緩和
                result_chunks.append(chunk)
                total_length += len(chunk)
            else:
                safe_print(f"   ⚠️ スコア不足でスキップ: {score:.3f}")
                if len(result_chunks) < 10:  # 最低10個は確保
                    result_chunks.append(chunk)
                    total_length += len(chunk)
                    safe_print(f"   ✅ 最低限確保のため追加")
        
        result = '\n\n'.join(result_chunks)
        safe_print(f"🚀 ハイブリッドRAG検索完了: {len(result_chunks)}個のチャンク、{len(result)}文字 (元: {len(knowledge_text)}文字)")
        
        # 最終結果の内容プレビューもデバッグ出力
        result_preview = result[:500].replace('\n', ' ')
        safe_print(f"📝 最終RAG結果プレビュー: {result_preview}...")
        
        return result
        
    except Exception as e:
        safe_print(f"RAG検索エラー: {str(e)}")
        # エラーの場合は最初の部分を返す
        return knowledge_text[:50000]  # フォールバック時は5万文字（精度重視）

def _preprocess_query(query: str) -> str:
    """クエリの前処理 - 文字正規化と自動語句分解"""
    # 全角・半角の正規化
    import unicodedata
    import re
    normalized = unicodedata.normalize('NFKC', query)
    
    # 基本的な表記揺れの正規化
    processed = normalized
    processed = re.sub(r'[・･]', ' ', processed)  # 中点を空白に
    processed = re.sub(r'[（）()]', ' ', processed)  # 括弧を空白に
    processed = re.sub(r'\s+', ' ', processed)  # 連続空白を単一空白に
    
    # 複合語の自動分解（助詞で分割）
    particles = ['について', 'に関して', 'に関する', 'における', 'での', 'による']
    for particle in particles:
        if particle in processed:
            parts = processed.split(particle)
            processed = ' '.join(parts).strip()
    
    safe_print(f"🔍 クエリ正規化: '{query}' → '{processed}'")
    return processed

def _bm25_search(chunks: list, query: str, max_results: int) -> list:
    """BM25検索（語彙ベース）"""
    try:
        import bm25s
        
        # BM25S検索エンジンを作成
        corpus_tokens = bm25s.tokenize(chunks)
        retriever = bm25s.BM25()
        retriever.index(corpus_tokens)
        
        # 質問をトークン化して検索
        query_tokens = bm25s.tokenize([query])
        k_value = min(max_results * 2, len(chunks))
        results, scores = retriever.retrieve(query_tokens, k=k_value)
        
        # 結果を整形
        search_results = []
        for i in range(results.shape[1]):
            if i < len(chunks):
                chunk_idx = results[0, i]
                if chunk_idx < len(chunks):
                    search_results.append({
                        'content': chunks[chunk_idx],
                        'score': float(scores[0, i]) if i < len(scores[0]) else 0.0,
                        'type': 'bm25',
                        'index': chunk_idx
                    })
        
        return search_results
        
    except Exception as e:
        safe_print(f"BM25検索エラー: {e}")
        return []

def _semantic_search(chunks: list, query: str, max_results: int) -> list:
    """セマンティック検索（意味ベース）- 軽量で高速な実装（Sentence Transformers不使用）"""
    try:
        # TF-IDFベースのセマンティック検索（最優先）
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            safe_print("📊 軽量TF-IDF セマンティック検索開始")
            
            # TF-IDFベクトル化（軽量高速設定）
            vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),  # 1-gram, 2-gramのみ
                max_features=3000,   # 特徴量を制限
                stop_words=None,     # 日本語のストップワードは使わない
                analyzer='char',     # 文字レベルの解析（日本語に適している）
                min_df=1,
                max_df=0.85,         # 高頻度語を除外
                sublinear_tf=True,   # TF値の対数変換で正規化
                lowercase=True       # 小文字化
            )
            
            # コーパス（チャンク + クエリ）をベクトル化
            corpus = chunks + [query]
            tfidf_matrix = vectorizer.fit_transform(corpus)
            
            # クエリと各チャンクの類似度を計算
            query_vector = tfidf_matrix[-1]  # 最後がクエリ
            chunk_vectors = tfidf_matrix[:-1]  # 最後以外がチャンク
            
            similarities = cosine_similarity(query_vector, chunk_vectors).flatten()
            
            # 結果を整形
            semantic_results = []
            for i, similarity in enumerate(similarities):
                semantic_results.append({
                    'content': chunks[i],
                    'score': float(similarity),
                    'type': 'semantic_tfidf_fast',
                    'index': i
                })
            
            # スコア順でソート
            semantic_results.sort(key=lambda x: x['score'], reverse=True)
            safe_print(f"✅ 軽量TF-IDF セマンティック検索完了: 上位{min(max_results, len(semantic_results))}件")
            return semantic_results[:max_results]
            
        except ImportError:
            safe_print("⚠️ scikit-learn未インストール、改良簡易セマンティック検索を使用")
        
        # フォールバック: 改良された簡易セマンティック検索
        safe_print("🔍 改良簡易セマンティック検索開始")
        semantic_results = []
        
        # クエリの重要語句を抽出（日本語対応強化）
        import re
        
        # 日本語と英数字の単語を抽出
        query_words = set()
        # ひらがな・カタカナ・漢字の単語
        japanese_words = re.findall(r'[ぁ-んァ-ヶ一-龯]+', query)
        # 英数字の単語
        alphanumeric_words = re.findall(r'[a-zA-Z0-9]+', query)
        
        query_words.update([w.lower() for w in japanese_words if len(w) >= 1])
        query_words.update([w.lower() for w in alphanumeric_words if len(w) >= 2])
        
        for i, chunk in enumerate(chunks):
            # チャンクからも同様に単語を抽出
            chunk_japanese = re.findall(r'[ぁ-んァ-ヶ一-龯]+', chunk)
            chunk_alphanumeric = re.findall(r'[a-zA-Z0-9]+', chunk)
            chunk_words = set()
            chunk_words.update([w.lower() for w in chunk_japanese if len(w) >= 1])
            chunk_words.update([w.lower() for w in chunk_alphanumeric if len(w) >= 2])
            
            # 複数の類似度指標を組み合わせ
            scores = []
            
            # 1. Jaccard類似度（改良版）
            if len(query_words) > 0 and len(chunk_words) > 0:
                intersection = len(query_words.intersection(chunk_words))
                union = len(query_words.union(chunk_words))
                jaccard = intersection / union if union > 0 else 0.0
                scores.append(jaccard * 0.4)
            
            # 2. 語句の包含度（重み付き）
            if len(query_words) > 0:
                inclusion = 0
                for word in query_words:
                    if word in chunk.lower():
                        # 長い単語ほど重要視
                        weight = min(2.0, len(word) / 2.0)
                        inclusion += weight
                inclusion = inclusion / len(query_words)
                scores.append(min(1.0, inclusion) * 0.4)
            
            # 3. N-gram一致度（高速版）
            try:
                # 2-gramの一致度を計算
                ngram_score = 0
                query_2grams = set([query[i:i+2] for i in range(len(query)-1)])
                chunk_2grams = set([chunk[i:i+2] for i in range(len(chunk)-1)])
                
                if len(query_2grams) > 0:
                    ngram_intersection = len(query_2grams.intersection(chunk_2grams))
                    ngram_similarity = ngram_intersection / len(query_2grams)
                    ngram_score = ngram_similarity * 0.2
                
                scores.append(min(1.0, ngram_score))
            except:
                scores.append(0.0)
            
            # 総合スコア
            total_score = sum(scores)
            
            semantic_results.append({
                'content': chunk,
                'score': total_score,
                'type': 'semantic_enhanced_fast',
                'index': i
            })
        
        # スコア順でソート
        semantic_results.sort(key=lambda x: x['score'], reverse=True)
        safe_print(f"✅ 改良簡易セマンティック検索完了: 上位{min(max_results, len(semantic_results))}件")
        return semantic_results[:max_results]
        
    except Exception as e:
        safe_print(f"セマンティック検索エラー: {e}")
        return []

def _evaluate_rag_quality(filtered_chunk: str, query: str, rag_attempts: int) -> float:
    """
    RAG検索結果の品質を評価（0.0-1.0のスコア）
    包括的で寛容な評価を実施（情報を見逃さないように）
    """
    if not filtered_chunk or not filtered_chunk.strip():
        return 0.0
    
    score = 0.0
    content_lower = filtered_chunk.lower()
    query_lower = query.lower()
    
    # 1. 文字数による基本スコア（最大0.3） - 緩和
    content_length = len(filtered_chunk.strip())
    if content_length >= 300:  # 300文字以上で最高スコア
        score += 0.3
    elif content_length >= 150:  # 150文字以上で中程度
        score += 0.25
    elif content_length >= 50:   # 50文字以上で最低限（大幅緩和）
        score += 0.2
    else:
        score += 0.1  # 非常に短くても基本スコア付与
    
    # 2. クエリのキーワードマッチング（最大0.5） - 緩和
    import re
    query_words = re.findall(r'\w+', query.lower())
    important_keywords = [word for word in query_words if len(word) >= 1]  # 1文字以上に緩和
    
    # 助詞などの一般的な単語を除外
    stopwords = ['の', 'に', 'を', 'は', 'が', 'で', 'と', 'から', 'まで', 'て', 'た', 'だ', 'です', 'ます']
    important_keywords = [word for word in important_keywords if word not in stopwords]
    
    # 重要キーワードの完全一致チェック（部分一致も許可）
    critical_matches = 0
    partial_matches = 0
    for keyword in important_keywords:
        if keyword.strip() in content_lower:
            critical_matches += 1
        elif any(keyword[:-1] in content_lower for i in range(1, len(keyword)) if len(keyword[:-i]) >= 2):
            # 部分一致も評価
            partial_matches += 1
    
    if len(important_keywords) > 0:
        critical_match_ratio = critical_matches / len(important_keywords)
        partial_match_ratio = partial_matches / len(important_keywords)
        
        # 完全一致の評価（大幅緩和）
        if critical_match_ratio >= 0.2:  # 20%以上で高スコア（50%→20%に緩和）
            score += critical_match_ratio * 0.5
        elif critical_match_ratio >= 0.1:  # 10%以上で中スコア
            score += critical_match_ratio * 0.3
        elif critical_match_ratio > 0:     # 少しでもマッチすればスコア付与
            score += critical_match_ratio * 0.2
        
        # 部分一致のボーナス
        if partial_match_ratio > 0:
            score += partial_match_ratio * 0.1
    
    # 3. 質問と回答の語句重複度評価（最大0.2）
    import re
    query_words = set(re.findall(r'[ぁ-んァ-ヶ一-龯a-zA-Z0-9]+', query_lower))
    content_words = set(re.findall(r'[ぁ-んァ-ヶ一-龯a-zA-Z0-9]+', content_lower))
    
    # 語句の重複度を計算
    if len(query_words) > 0:
        overlap = len(query_words.intersection(content_words))
        overlap_ratio = overlap / len(query_words)
        intent_score = overlap_ratio * 0.2
        score += intent_score
    
    # 4. 無関係な内容の検出による減点（大幅緩和）
    irrelevant_patterns = [
        'システムエラー', 'デバッグ', 'テスト用', '例外処理'
    ]
    
    irrelevant_count = sum(1 for pattern in irrelevant_patterns if pattern in filtered_chunk)
    if irrelevant_count > 0:
        score -= min(0.1, irrelevant_count * 0.05)  # 減点を大幅緩和
    
    # 5. 厳格判定を大幅緩和（90%減点を削除）
    # 具体的な固有名詞を含む質問の場合でも、厳格すぎる減点は行わない
    if any(word in query_lower for word in ['株式会社', '会社', '工芸', '顧客番号', 'ステータス']):
        # 関連性チェックを行うが、大幅な減点はしない
        has_any_relevance = False
        
        # より柔軟な関連性チェック
        for word in query_words:
            if len(word) >= 2:
                # 完全一致
                if word in content_lower:
                    has_any_relevance = True
                    break
                # 部分一致（3文字以上の場合）
                if len(word) >= 3 and any(word[:-1] in content_lower for i in range(1, min(3, len(word)))):
                    has_any_relevance = True
                    break
        
        # 関連性が全くない場合のみ軽微な減点
        if not has_any_relevance:
            score *= 0.7  # 30%減点（90%減点から大幅緩和）
    
    # 6. 語彙レベルでの関連性評価（ボーナス）
    try:
        semantic_bonus = 0.0
        
        # N-gram重複度の計算
        query_bigrams = set([query_lower[i:i+2] for i in range(len(query_lower)-1)])
        content_bigrams = set([content_lower[i:i+2] for i in range(len(content_lower)-1)])
        
        if len(query_bigrams) > 0:
            bigram_overlap = len(query_bigrams.intersection(content_bigrams))
            bigram_ratio = bigram_overlap / len(query_bigrams)
            semantic_bonus = bigram_ratio * 0.1
        
        score += semantic_bonus  # 最大0.1のボーナス
            
    except Exception as e:
        pass
    
    # 7. 包括性ボーナス（新規追加）
    # チャンクが表形式データや構造化データを含む場合のボーナス
    if any(indicator in content_lower for indicator in ['番号', 'id', 'コード', '名前', '会社', '顧客']):
        score += 0.1  # 構造化データボーナス
    
    # スコアを0.0-1.0に正規化（最低スコアを保証）
    final_score = max(0.1, min(1.0, score))  # 最低0.1のスコアを保証
    
    return final_score

def _combine_search_results(bm25_results: list, semantic_results: list, query: str, max_results: int) -> list:
    """BM25とセマンティック検索結果の統合 - 意味的検索を重視"""
    try:
        # 結果の統合とスコア正規化
        all_results = {}
        
        # セマンティック検索のタイプに応じて重みを調整
        semantic_weight = 0.7  # デフォルト
        bm25_weight = 0.3
        
        # 軽量セマンティック検索のタイプに応じて重みを調整
        if semantic_results and semantic_results[0].get('type') == 'semantic_tfidf_fast':
            semantic_weight = 0.65
            bm25_weight = 0.35
            safe_print("📊 軽量TF-IDFセマンティック検索 - 高速バランスモード")
        elif semantic_results and semantic_results[0].get('type') == 'semantic_enhanced_fast':
            semantic_weight = 0.45
            bm25_weight = 0.55
            safe_print("🔍 改良簡易セマンティック検索 - 語彙重視モード")
        else:
            semantic_weight = 0.5
            bm25_weight = 0.5
            safe_print("⚖️ デフォルトバランスモード")
        
        # BM25結果の処理
        max_bm25_score = max([r['score'] for r in bm25_results], default=1.0)
        for result in bm25_results:
            idx = result['index']
            normalized_score = result['score'] / max_bm25_score if max_bm25_score > 0 else 0.0
            
            if idx not in all_results:
                all_results[idx] = {
                    'content': result['content'],
                    'bm25_score': normalized_score * bm25_weight,
                    'semantic_score': 0.0,
                    'index': idx
                }
            else:
                all_results[idx]['bm25_score'] = normalized_score * bm25_weight
        
        # セマンティック結果の処理
        max_semantic_score = max([r['score'] for r in semantic_results], default=1.0)
        for result in semantic_results:
            idx = result['index']
            normalized_score = result['score'] / max_semantic_score if max_semantic_score > 0 else 0.0
            
            if idx not in all_results:
                all_results[idx] = {
                    'content': result['content'],
                    'bm25_score': 0.0,
                    'semantic_score': normalized_score * semantic_weight,
                    'index': idx
                }
            else:
                all_results[idx]['semantic_score'] = normalized_score * semantic_weight
        
        # 統合スコアの計算
        final_results = []
        for idx, result in all_results.items():
            combined_score = result['bm25_score'] + result['semantic_score']
            
            # 意味的類似度が高い場合にボーナス
            if result['semantic_score'] > 0.5:
                combined_score += 0.1  # セマンティックボーナス
            
            # 両方の検索で見つかった場合にボーナス
            if result['bm25_score'] > 0 and result['semantic_score'] > 0:
                combined_score += 0.05  # ハイブリッドボーナス
            
            final_results.append({
                'content': result['content'],
                'score': combined_score,
                'index': idx,
                'bm25_score': result['bm25_score'],
                'semantic_score': result['semantic_score']
            })
        
        # 統合スコア順でソート
        final_results.sort(key=lambda x: x['score'], reverse=True)
        
        safe_print(f"🔍 ハイブリッド検索統合: BM25={len(bm25_results)}件, セマンティック={len(semantic_results)}件 → 統合={len(final_results)}件")
        safe_print(f"📊 重み配分: BM25={bm25_weight:.1f}, セマンティック={semantic_weight:.1f}")
        
        return final_results[:max_results]
        
    except Exception as e:
        safe_print(f"検索結果統合エラー: {e}")
        return bm25_results[:max_results]  # フォールバック

# Geminiモデル（グローバル変数）
model = None

def set_model(gemini_model):
    """Geminiモデルを設定する"""
    global model
    model = gemini_model

def is_casual_conversation(message_text: str) -> bool:
    """メッセージが挨拶や一般的な会話かどうかを判定する（ビジネス質問を除外）"""
    if not message_text:
        return False
    
    message_lower = message_text.strip().lower()
    
    # 漢字・カタカナ・英語の専門用語を含む場合はビジネス関連として判定
    import re
    # 漢字を含む2文字以上の語句（専門用語の可能性）
    has_kanji_terms = bool(re.search(r'[一-龯]{2,}', message_text))
    # カタカナを含む3文字以上の語句（ビジネス用語の可能性）
    has_katakana_terms = bool(re.search(r'[ァ-ヶ]{3,}', message_text))
    # 英語の専門用語（3文字以上）
    has_english_terms = bool(re.search(r'\b[A-Za-z]{3,}\b', message_text))
    
    # 専門用語を含む場合は知識ベース検索を優先
    if has_kanji_terms or has_katakana_terms or has_english_terms:
        # ただし、一般的な単語は除外
        casual_exceptions = ['今日', '明日', '昨日', '時間', '場所', '天気', '元気']
        if not any(exception in message_lower for exception in casual_exceptions):
            return False
    
    # 疑問符がある場合は知識ベース検索を優先（質問の可能性が高い）
    if "?" in message_text or "？" in message_text:
        return False
    
    # 明確な挨拶パターン
    pure_greetings = [
        "こんにちは", "こんにちわ", "おはよう", "おはようございます", "こんばんは", "こんばんわ",
        "よろしく", "よろしくお願いします", "はじめまして", "初めまして",
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening"
    ]
    
    # 明確なお礼パターン
    pure_thanks = [
        "ありがとう", "ありがとうございます", "ありがとうございました", "感謝します",
        "thank you", "thanks", "thx"
    ]
    
    # 明確な別れの挨拶パターン
    pure_farewells = [
        "さようなら", "またね", "また明日", "失礼します", "お疲れ様", "お疲れさまでした",
        "bye", "goodbye", "see you", "good bye"
    ]
    
    # 短い相槌パターン（単独で使われる場合のみ）
    short_responses = [
        "はい", "いいえ", "そうですね", "なるほど", "そうですか", "わかりました",
        "ok", "okay", "yes", "no", "i see", "alright"
    ]
    
    # メッセージが非常に短い場合（3文字以下）
    if len(message_lower) <= 3:
        # 英数字のみの場合（ID、API、URLなど）は除外
        if message_lower.isalnum():
            return False
        return True
    
    # 明確な挨拶・お礼・別れの挨拶をチェック
    all_pure_patterns = pure_greetings + pure_thanks + pure_farewells
    
    for pattern in all_pure_patterns:
        if pattern == message_lower or pattern in message_lower:
            # ただし、他のビジネス用語と組み合わされている場合は除外
            if len(message_lower) > len(pattern) * 2:  # パターンの2倍以上の長さがある場合
                return False
            return True
    
    # 短い相槌のみの場合（他の単語と組み合わされていない）
    for response in short_responses:
        if message_lower == response:
            return True
    
    # 天気など純粋な日常会話（ビジネス文脈なし）
    pure_casual_phrases = [
        "いい天気", "天気がいい", "天気悪い", "雨降り", "晴れ", "曇り",
        "暑い", "寒い", "涼しい", "暖かい",
        "疲れた", "眠い", "お腹空いた"
    ]
    
    for phrase in pure_casual_phrases:
        if phrase in message_lower and len(message_lower) <= len(phrase) + 5:  # 短い文章のみ
            return True
    
    # 非常に短い質問ではない文（10文字以下、疑問符なし、ビジネス用語なし）
    if len(message_text) <= 10 and "?" not in message_text and "？" not in message_text:
        # ただし、数字や英数字が多い場合は除外（IDや番号の可能性）
        alphanumeric_count = sum(1 for c in message_text if c.isalnum())
        if alphanumeric_count <= len(message_text) * 0.3:  # 30%以下が英数字の場合のみ
            return True
    
    return False

async def generate_casual_response(message_text: str, company_name: str) -> str:
    """挨拶や一般的な会話に対する自然な返答を生成する"""
    try:
        if model is None:
            return "こんにちは！何かお手伝いできることはありますか？"
        
        # 挨拶や一般的な会話専用のプロンプト
        casual_prompt = f"""
あなたは{company_name}の親しみやすいアシスタントです。
ユーザーからの挨拶や一般的な会話に対して、自然で親しみやすい返答をしてください。

返答の際の注意点：
1. 親しみやすく、温かい口調で返答してください
2. 会話を続けたい場合は、適切な質問で返してください
3. 長すぎず、短すぎない適度な長さで返答してください
4. 必要に応じて、お手伝いできることがあることを伝えてください
5. 知識ベースの情報は参照せず、一般的な会話として返答してください

ユーザーのメッセージ: {message_text}
"""
        
        response = model.generate_content(casual_prompt)
        
        if response and hasattr(response, 'text') and response.text:
            return response.text.strip()
        else:
            # フォールバック応答（汎用的判定）
            import re
            message_lower = message_text.lower()
            
            # 語句の感情・意図を自動判定
            if re.search(r'(こんにち|hello|hi)', message_lower):
                return "こんにちは！お疲れ様です。何かお手伝いできることはありますか？"
            elif re.search(r'(ありがとう|thank)', message_lower):
                return "どういたしまして！他にも何かお手伝いできることがあれば、お気軽にお声がけください。"
            elif re.search(r'(さようなら|またね|bye)', message_lower):
                return "お疲れ様でした！また何かありましたら、いつでもお声がけください。"
            else:
                return "そうですね！何かお手伝いできることがあれば、お気軽にお声がけください。"
                
    except Exception as e:
        safe_print(f"一般会話応答生成エラー: {str(e)}")
        return "こんにちは！何かお手伝いできることはありますか？"

async def process_chat(message: ChatMessage, db = Depends(get_db), current_user: dict = None):
    """チャットメッセージを処理してGeminiからの応答を返す"""
    try:
        # モデルが設定されているか確認
        if model is None:
            safe_print("❌ モデルが初期化されていません")
            raise HTTPException(status_code=500, detail="AIモデルが初期化されていません")
        
        safe_print(f"✅ モデル初期化確認: {model}")
        safe_print(f"📊 モデルタイプ: {type(model)}")
        
        # メッセージがNoneでないことを確認
        if not message or not hasattr(message, 'text') or message.text is None:
            raise HTTPException(status_code=400, detail="メッセージテキストが提供されていません")
        
        # メッセージテキストを安全に取得
        message_text = message.text if message.text is not None else ""
        
        # 最新の会社名を取得（モジュールからの直接インポートではなく、関数内で再取得）
        from .company import DEFAULT_COMPANY_NAME as current_company_name
        
        # 挨拶や一般的な会話かどうかを判定
        if is_casual_conversation(message_text):
            safe_print(f"🗣️ 一般的な会話として判定: {message_text}")
            
            # 一般的な会話の場合はナレッジを参照せずに返答
            casual_response = await generate_casual_response(message_text, current_company_name)
            
            # チャット履歴を保存（一般会話として）
            from modules.token_counter import TokenUsageTracker
            
            # ユーザーの会社IDを取得（チャット履歴保存用）
            company_id = None
            if message.user_id:
                try:
                    from supabase_adapter import select_data
                    user_result = select_data("users", columns="company_id", filters={"id": message.user_id})
                    if user_result.data and len(user_result.data) > 0:
                        user_data = user_result.data[0]
                        company_id = user_data.get('company_id')
                except Exception as e:
                    safe_print(f"会社ID取得エラー（一般会話）: {str(e)}")
            
            # トークン追跡機能を使用してチャット履歴を保存（ナレッジ参照なし）
            tracker = TokenUsageTracker(db)
            chat_id = tracker.save_chat_with_prompts(
                user_message=message_text,
                bot_response=casual_response,
                user_id=message.user_id,
                prompt_references=0,  # ナレッジ参照なし
                company_id=company_id,
                employee_id=getattr(message, 'employee_id', None),
                employee_name=getattr(message, 'employee_name', None),
                category="一般会話",
                sentiment="neutral",
                model="gemini-2.5-flash"
            )
            
            # 利用制限の処理（一般会話でも質問回数にカウント）
            remaining_questions = None
            limit_reached = False
            
            if message.user_id:
                # 質問の利用制限をチェック
                limits_check = check_usage_limits(message.user_id, "question", db)
                
                if not limits_check["is_unlimited"] and not limits_check["allowed"]:
                    response_text = f"申し訳ございません。デモ版の質問回数制限（{limits_check['limit']}回）に達しました。"
                    return {
                        "response": response_text,
                        "remaining_questions": 0,
                        "limit_reached": True
                    }
                
                # 質問カウントを更新
                if not limits_check.get("is_unlimited", False):
                    updated_limits = update_usage_count(message.user_id, "questions_used", db)
                    if updated_limits:
                        remaining_questions = updated_limits["questions_limit"] - updated_limits["questions_used"]
                        limit_reached = remaining_questions <= 0
                    else:
                        remaining_questions = limits_check["remaining"] - 1 if limits_check["remaining"] > 0 else 0
                        limit_reached = remaining_questions <= 0
            
            safe_print(f"✅ 一般会話応答完了: {len(casual_response)} 文字")
            
            return {
                "response": casual_response,
                "source": "",  # ナレッジ参照なし
                "remaining_questions": remaining_questions,
                "limit_reached": limit_reached
            }
        
        # ユーザーIDがある場合は利用制限をチェック
        remaining_questions = None
        limit_reached = False
        
        if message.user_id:
            # 質問の利用制限をチェック
            limits_check = check_usage_limits(message.user_id, "question", db)
            
            if not limits_check["is_unlimited"] and not limits_check["allowed"]:
                response_text = f"申し訳ございません。デモ版の質問回数制限（{limits_check['limit']}回）に達しました。"
                return {
                    "response": response_text,
                    "remaining_questions": 0,
                    "limit_reached": True
                }
            
            # 無制限でない場合は残り回数を計算
            if not limits_check["is_unlimited"]:
                remaining_questions = limits_check["remaining"]

        # ユーザーの会社IDを取得
        company_id = None
        if message.user_id:
            try:
                from supabase_adapter import select_data
                user_result = select_data("users", columns="company_id", filters={"id": message.user_id})
                if user_result.data and len(user_result.data) > 0:
                    user_data = user_result.data[0]
                    if user_data.get('company_id'):
                        company_id = user_data['company_id']
                        safe_print(f"ユーザーID {message.user_id} の会社ID: {company_id}")
                    else:
                        safe_print(f"ユーザーID {message.user_id} に会社IDが設定されていません")
                else:
                    safe_print(f"ユーザーID {message.user_id} が見つかりません")
            except Exception as e:
                safe_print(f"会社ID取得エラー: {str(e)}")
                # エラー時はcompany_id = Noneのまま継続
        
        # 会社固有のアクティブなリソースを取得
        # 管理者の場合は自分がアップロードしたリソースのみ取得
        uploaded_by = None
        if current_user and current_user.get("role") == "admin":
            uploaded_by = current_user["id"]
            safe_print(f"管理者ユーザー: {current_user.get('email')} - 自分のリソースのみ参照")
        
        active_sources = await get_active_resources_by_company_id(company_id, db, uploaded_by)
        safe_print(f"アクティブなリソース (会社ID: {company_id}): {', '.join(active_sources)}")
        
        # アクティブなリソースがない場合はエラーメッセージを返す
        if not active_sources:
            response_text = f"申し訳ございません。現在、アクティブな知識ベースがありません。管理画面でリソースを有効にしてください。"
            
            # チャット履歴を保存
            chat_id = str(uuid.uuid4())
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO chat_history (id, user_message, bot_response, timestamp, category, sentiment, employee_id, employee_name, user_id, company_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (chat_id, message_text, response_text, datetime.now().isoformat(), "設定エラー", "neutral", message.employee_id, message.employee_name, message.user_id, company_id)
            )
            db.commit()
            
            # ユーザーIDがある場合は質問カウントを更新（アクティブなリソースがなくても利用制限は更新する）
            if message.user_id and not limits_check.get("is_unlimited", False):
                safe_print(f"利用制限更新開始（アクティブリソースなし） - ユーザーID: {message.user_id}")
                safe_print(f"更新前の制限情報: {limits_check}")
                
                updated_limits = update_usage_count(message.user_id, "questions_used", db)
                safe_print(f"更新後の制限情報: {updated_limits}")
                
                if updated_limits:
                    remaining_questions = updated_limits["questions_limit"] - updated_limits["questions_used"]
                    limit_reached = remaining_questions <= 0
                    safe_print(f"計算された残り質問数: {remaining_questions}, 制限到達: {limit_reached}")
                else:
                    safe_print("利用制限の更新に失敗しました")
            
            safe_print(f"返り値（アクティブリソースなし）: remaining_questions={remaining_questions}, limit_reached={limit_reached}")
            
            return {
                "response": response_text,
                "remaining_questions": remaining_questions,
                "limit_reached": limit_reached
            }
        
        # pandas をインポート
        import pandas as pd
        import traceback
        
        # 選択されたリソースを使用して知識ベースを作成
        # source_info = {}  # ソース情報を保存する辞書
        active_resource_names = await get_active_resource_names_by_company_id(company_id, db)
        source_info_list = [
            {
                "name": res_name,
                "section": "",  # or default
                "page": ""
            }
            for res_name in active_resource_names
        ]
        
        # アクティブなリソースのSpecial指示を取得
        special_instructions = []
        try:
            from supabase_adapter import select_data
            for source_id in active_sources:
                source_result = select_data("document_sources", columns="name", filters={"id": source_id})
                if source_result.data and len(source_result.data) > 0:
                    source_data = source_result.data[0]
                    if source_data.get('special') and source_data['special'].strip():
                        special_instructions.append({
                            "name": source_data.get('name', 'Unknown'),
                            "instruction": source_data['special'].strip()
                        })
            safe_print(f"Special指示: {len(special_instructions)}個のリソースにSpecial指示があります")
        except Exception as e:
            safe_print(f"Special指示取得エラー: {str(e)}")
            special_instructions = []
        
        # 🔍 知識ベース取得の詳細デバッグ（本番環境問題調査）
        safe_print(f"📋 アクティブなソース ({len(active_sources)}件): {active_sources}")
        safe_print(f"🔍 知識ベース取得開始...")
        
        active_knowledge_text = await get_active_resources_content_by_ids(active_sources, db)
        
        # 知識ベース取得結果の詳細チェック
        if not active_knowledge_text:
            safe_print(f"❌ 知識ベースが空です - active_knowledge_text: {repr(active_knowledge_text)}")
        elif isinstance(active_knowledge_text, str) and not active_knowledge_text.strip():
            safe_print(f"❌ 知識ベースが空文字列です - 長さ: {len(active_knowledge_text)}")
        else:
            safe_print(f"✅ 知識ベース取得成功 - 長さ: {len(active_knowledge_text):,} 文字")
            safe_print(f"👀 知識ベース先頭200文字: {active_knowledge_text[:200]}...")
        
        # ⚡ 1200文字チャンク化をRAG検索前に実行（task.yaml推奨サイズ）
        if active_knowledge_text and len(active_knowledge_text) > 1000:  # 1000文字を超える場合のみチャンク化
            safe_print(f"🔪 1200文字チャンク化開始 - 元サイズ: {len(active_knowledge_text):,} 文字")
            
            # 1200文字でチャンク化（task.yaml推奨：1000-1200文字）
            CHUNK_SIZE = 1200
            chunks = chunk_knowledge_base(active_knowledge_text, CHUNK_SIZE)
            safe_print(f"🔪 チャンク化完了: {len(chunks)}個のチャンク (チャンクサイズ: {CHUNK_SIZE}文字)")
            
            # チャンク化されたテキストを結合してRAG検索（精度重視）
            chunked_text = '\n\n'.join(chunks[:100])  # 最大100チャンク（80,000文字）まで使用
            active_knowledge_text = simple_rag_search(chunked_text, message_text, max_results=30, company_id=company_id)
            
            safe_print(f"🎯 800文字チャンク+RAG検索完了 - 新サイズ: {len(active_knowledge_text):,} 文字")
        
        # 知識ベースのサイズを制限（精度とスピードのバランス）
        MAX_KNOWLEDGE_SIZE = 200000  # 20万文字制限（800文字×250チャンク相当）
        if active_knowledge_text and len(active_knowledge_text) > MAX_KNOWLEDGE_SIZE:
            safe_print(f"⚠️ 知識ベースが大きすぎます ({len(active_knowledge_text)} 文字)。{MAX_KNOWLEDGE_SIZE} 文字に制限します。")
            active_knowledge_text = active_knowledge_text[:MAX_KNOWLEDGE_SIZE] + "\n\n[注意: 精度を保ちつつ効率化のため、最も関連性の高い部分のみ表示しています]"
        # アクティブな知識ベースが空の場合はエラーメッセージを返す
        if not active_knowledge_text or (isinstance(active_knowledge_text, str) and not active_knowledge_text.strip()):
            response_text = f"申し訳ございません。アクティブな知識ベースの内容が空です。管理画面で別のリソースを有効にしてください。"
            
            # トークン使用量を計算してチャット履歴を保存（エラーケース）
            from modules.token_counter import TokenUsageTracker
            
            # ユーザーの会社IDを取得（チャット履歴保存用） 
            from supabase_adapter import select_data
            user_result = select_data("users", filters={"id": message.user_id}) if hasattr(message, 'user_id') and message.user_id else None
            chat_company_id = user_result.data[0].get("company_id") if user_result and user_result.data else None
            
            # プロンプト参照数を計算（アクティブリソース数）
            error_prompt_references = len(active_sources) if active_sources else 0
            
            # トークン追跡機能を使用してチャット履歴を保存（新料金体系を使用）
            tracker = TokenUsageTracker(db)
            chat_id = tracker.save_chat_with_prompts(
                user_message=message_text,
                bot_response=response_text,
                user_id=message.user_id,
                prompt_references=error_prompt_references,
                company_id=chat_company_id,
                employee_id=getattr(message, 'employee_id', None),
                employee_name=getattr(message, 'employee_name', None),
                category="設定エラー",
                sentiment="neutral",
                model="gemini-2.5-flash"
            )
            
            # ユーザーIDがある場合は質問カウントを更新（知識ベースが空でも利用制限は更新する）
            if message.user_id and not limits_check.get("is_unlimited", False):
                safe_print(f"利用制限更新開始（知識ベース空） - ユーザーID: {message.user_id}")
                safe_print(f"更新前の制限情報: {limits_check}")
                
                updated_limits = update_usage_count(message.user_id, "questions_used", db)
                safe_print(f"更新後の制限情報: {updated_limits}")
                
                if updated_limits:
                    remaining_questions = updated_limits["questions_limit"] - updated_limits["questions_used"]
                    limit_reached = remaining_questions <= 0
                    safe_print(f"計算された残り質問数: {remaining_questions}, 制限到達: {limit_reached}")
                else:
                    safe_print("利用制限の更新に失敗しました")
            
            safe_print(f"返り値（知識ベース空）: remaining_questions={remaining_questions}, limit_reached={limit_reached}")
            
            return {
                "response": response_text,
                "remaining_questions": remaining_questions,
                "limit_reached": limit_reached
            }
            
        # 直近のメッセージを取得（最大3件に制限）
        recent_messages = []
        try:
            if message.user_id:
                with db.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        """
                        SELECT user_message, bot_response
                        FROM chat_history
                        WHERE employee_id = %s
                        ORDER BY timestamp DESC
                        LIMIT 2
                        """,
                        (message.user_id,)
                    )
                    cursor_result = cursor.fetchall()
                    # PostgreSQLの結果をリストに変換してから古い順に並べ替え
                    recent_messages = list(cursor_result)
                    recent_messages.reverse()
        except Exception as e:
            safe_print(f"会話履歴取得エラー: {str(e)}")
            recent_messages = []
        
        # 会話履歴の構築（各メッセージを制限）
        conversation_history = ""
        if recent_messages:
            conversation_history = "直近の会話履歴：\n"
            for idx, msg in enumerate(recent_messages):
                
                try:
                    user_msg = msg.get('user_message', '') or ''
                    bot_msg = msg.get('bot_response', '') or ''
                    
                    # 各メッセージを100文字に制限（トークン削減のため）
                    if len(user_msg) > 100:
                        user_msg = user_msg[:100] + "..."
                    if len(bot_msg) > 100:
                        bot_msg = bot_msg[:100] + "..."
                    
                    conversation_history += f"ユーザー: {user_msg}\n"
                    conversation_history += f"アシスタント: {bot_msg}\n\n"
                except Exception as e:
                    # Windows環境でのUnicode文字エンコーディング問題を避けるため、safe_safe_print関数を使用
                    safe_safe_print(f"会話履歴処理エラー: {str(e)}")
                    # エラーが発生した場合はその行をスキップ
                    continue

        # Special指示をプロンプトに追加するための文字列を構築
        special_instructions_text = ""
        if special_instructions:
            special_instructions_text = "\n\n特別な回答指示（以下のリソースを参照する際は、各リソースの指示に従ってください）：\n"
            for idx, inst in enumerate(special_instructions, 1):
                special_instructions_text += f"{idx}. 【{inst['name']}】: {inst['instruction']}\n"

        # コンテキストキャッシュ対応プロンプトの作成
        from .prompt_cache import (
            build_context_cached_prompt, gemini_context_cache,
            generate_content_with_cache
        )
        from .config import setup_gemini_with_cache
        
        # データベース列情報を取得
        data_columns = ', '.join(knowledge_base.columns) if knowledge_base and hasattr(knowledge_base, 'columns') and knowledge_base.columns else ""
        image_info = f"画像情報：PDFから抽出された画像が{len(knowledge_base.images)}枚あります。" if knowledge_base and hasattr(knowledge_base, 'images') and knowledge_base.images and isinstance(knowledge_base.images, list) else ""
        
        # 知識ベース情報を統合（コンテキストキャッシュの対象）
        full_knowledge_context = f"""利用可能なデータ列：
{data_columns}

知識ベース内容（アクティブなリソースのみ）：
{active_knowledge_text}

{image_info}"""

        # コンテキストキャッシュ対応プロンプト構築
        prompt, cached_content_id = build_context_cached_prompt(
            company_name=current_company_name,
            active_resource_names=active_resource_names,
            active_knowledge_text=full_knowledge_context,
            conversation_history=conversation_history,
            message_text=message_text,
            special_instructions_text=special_instructions_text
        )

        # プロンプトサイズの最終チェック（精度とスピードのバランス）
        MAX_PROMPT_SIZE = 250000  # 25万文字制限（精度重視）
        if len(prompt) > MAX_PROMPT_SIZE:
            safe_print(f"⚠️ プロンプトが大きすぎます ({len(prompt)} 文字)。知識ベースをさらに制限します。")
            # 知識ベースをさらに制限
            reduced_knowledge_size = MAX_PROMPT_SIZE - (len(prompt) - len(active_knowledge_text)) - 10000
            if reduced_knowledge_size > 0:
                active_knowledge_text = active_knowledge_text[:reduced_knowledge_size] + "\n\n[注意: プロンプトサイズ制限のため、知識ベースを短縮しています]"
                # プロンプトを再構築
                prompt = f"""
        あなたは親切で丁寧な対応ができる{current_company_name}のアシスタントです。
        以下の知識ベースを参考に、ユーザーの質問に対って可能な限り具体的で役立つ回答を提供してください。

        利用可能なファイル: {', '.join(active_resource_names) if active_resource_names else ''}

        回答の際の注意点：
        1. 常に丁寧な言葉遣いを心がけ、ユーザーに対して敬意を持って接してください
        2. 知識ベースに情報がない場合でも、一般的な文脈で回答できる場合は適切に対応してください
        3. ユーザーが「もっと詳しく」などと質問した場合は、前回の回答内容に関連する詳細情報を提供してください。「どのような情報について詳しく知りたいですか？」などと聞き返さないでください。
        4. 可能な限り具体的で実用的な情報を提供してください
        5. 知識ベースにOCRで抽出されたテキスト（PDF (OCR)と表示されている部分）が含まれている場合は、それが画像から抽出されたテキストであることを考慮してください
        6. OCRで抽出されたテキストには多少の誤りがある可能性がありますが、文脈から適切に解釈して回答してください
        7. 知識ベースの情報を使用して回答した場合は、回答の最後に「情報ソース: [ファイル名]」の形式で参照したファイル名を記載してください。
        8. 「こんにちは」「おはよう」などの単純な挨拶のみの場合は、情報ソースを記載しないでください。それ以外の質問には基本的に情報ソースを記載してください。
        9. 回答可能かどうかが判断できる質問に対しては、最初に「はい」または「いいえ」で簡潔に答えてから、具体的な説明や補足情報を記載してください
        10. 回答は**Markdown記法**を使用して見やすく整理してください。見出し（#、##、###）、箇条書き（-、*）、番号付きリスト（1.、2.）、強調（**太字**、*斜体*）、コードブロック（```）、表（|）、引用（>）などを適切に使用してください
        11. 手順や説明が複数ある場合は、番号付きリストや箇条書きを使用して構造化してください
        12. 重要な情報は**太字**で強調してください
        13. コードやファイル名、設定値などは`バッククォート`で囲んでください{special_instructions_text}
        
        知識ベース内容（アクティブなリソースのみ）：
        {active_knowledge_text}

        {conversation_history}

        ユーザーの質問：
        {message_text}
        """
            else:
                safe_print("❌ プロンプトが大きすぎて制限できません")
                return {
                    "response": "申し訳ございません。知識ベースが大きすぎるため、現在処理できません。管理者にお問い合わせください。",
                    "source": "",
                    "remaining_questions": remaining_questions,
                    "limit_reached": limit_reached
                }

        # コンテキストキャッシュ対応Geminiによる応答生成
        try:
            if cached_content_id:
                # キャッシュヒット：キャッシュ対応モデルを使用
                cache_model = setup_gemini_with_cache()
                safe_print(f"🎯 Gemini API（キャッシュ使用）呼び出し開始 - キャッシュID: {cached_content_id}")
                safe_print(f"📝 プロンプト長: {len(prompt)} 文字（キャッシュ利用で短縮済み）")
                
                response = generate_content_with_cache(cache_model, prompt, cached_content_id)
            else:
                # キャッシュミス：通常のモデルを使用、将来のキャッシュ用にコンテキストを保存
                safe_print(f"🤖 Gemini API（新規）呼び出し開始 - モデル: {model}")
                safe_print(f"📝 プロンプト長: {len(prompt)} 文字")
                
                response = model.generate_content(prompt)
                
                # コンテキストキャッシュに保存（仮想的な実装）
                # 実際のGemini APIでは、レスポンスからcontent_idを取得する
                if gemini_context_cache.should_cache_context(full_knowledge_context):
                    virtual_content_id = f"cache_{hash(full_knowledge_context) % 100000}"
                    gemini_context_cache.store_context_cache(full_knowledge_context, virtual_content_id)
                    safe_print(f"💾 新規コンテキストキャッシュ保存完了: {virtual_content_id}")
            
            safe_print(f"📨 Gemini API応答受信: {response}")
            
            if not response or not hasattr(response, 'text'):
                safe_print(f"❌ 無効な応答: response={response}, hasattr(text)={hasattr(response, 'text') if response else 'N/A'}")
                raise ValueError("AIモデルからの応答が無効です")
            
            response_text = response.text
            cache_status = "キャッシュ使用" if cached_content_id else "新規作成"
            safe_print(f"✅ 応答テキスト取得成功: {len(response_text)} 文字 ({cache_status})")
            
        except Exception as model_error:
            error_str = str(model_error)
            safe_print(f"❌ AIモデル応答生成エラー: {error_str}")
            safe_print(f"🔍 エラータイプ: {type(model_error)}")
            
            # より詳細なエラー情報をログ出力
            import traceback
            safe_print(f"📋 エラートレースバック:")
            safe_print(traceback.format_exc())
            
            # クォータ制限エラーの場合の特別な処理
            if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
                response_text = "申し訳ございません。現在、AIサービスの利用制限に達しています。しばらく時間をおいてから再度お試しください。"
                safe_print("⏸️ 利用制限の更新をスキップ: AIモデル応答生成エラー: " + error_str)
                
                # エラー応答を返す（利用制限は更新しない）
                return {
                    "response": response_text,
                    "source": "",
                    "remaining_questions": remaining_questions,
                    "limit_reached": limit_reached
                }
            else:
                response_text = f"申し訳ございません。応答の生成中にエラーが発生しました。エラー詳細: {error_str[:100]}..."
        
        # カテゴリと感情を分析するプロンプト
        analysis_prompt = f"""
        以下のユーザーの質問と回答を分析し、以下の情報を提供してください：
        1. カテゴリ: 質問のカテゴリを1つだけ選んでください（観光情報、交通案内、ショッピング、飲食店、イベント情報、挨拶、一般的な会話、その他、未分類）
        2. 感情: ユーザーの感情を1つだけ選んでください（ポジティブ、ネガティブ、ニュートラル）
        3. 参照ソース: 回答に使用した主なソース情報を1つ選んでください。以下のソース情報から選択してください：
        {json.dumps(source_info_list, ensure_ascii=False, indent=2)}

        重要:
        - 参照ソースの選択は、回答の内容と最も関連性の高いソースを選んでください。回答の内容が特定のソースから直接引用されている場合は、そのソースを選択してください。
        - 「こんにちは」「おはよう」などの単純な挨拶のみの場合のみ、カテゴリを「挨拶」に設定し、参照ソースは空にしてください。
        - それ以外の質問には、基本的に参照ソースを設定してください。知識ベースの情報を使用している場合は、必ず適切なソースを選択してください。

        回答は以下のJSON形式で返してください：
        {{
            "category": "カテゴリ名",
            "sentiment": "感情",
            "source": {{
                "name": "ソース名",
                "section": "セクション名",
                "page": "ページ番号"
            }}
        }}

        ユーザーの質問：
        {message_text}

        生成された回答：
        {response_text}
        """
        # 分析の実行
        try:
            analysis_response = model.generate_content(analysis_prompt)
            if not analysis_response or not hasattr(analysis_response, 'text'):
                raise ValueError("分析応答が無効です")
            analysis_text = analysis_response.text
        except Exception as analysis_error:
            error_str = str(analysis_error)
            safe_print(f"分析応答生成エラー: {error_str}")
            
            # クォータ制限エラーの場合でも分析は継続（デフォルト値を使用）
            if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
                safe_print("分析でクォータ制限エラー、デフォルト値を使用")
            
            analysis_text = '{"category": "未分類", "sentiment": "neutral", "source": {"name": "", "section": "", "page": ""}}'
        
        # JSON部分を抽出
        try:
            # JSONの部分を抽出（コードブロックの中身を取得）
            json_match = re.search(r'```json\s*(.*?)\s*```', analysis_text, re.DOTALL)
            if json_match:
                analysis_json = json.loads(json_match.group(1))
            else:
                # コードブロックがない場合は直接パース
                analysis_json = json.loads(analysis_text)
                
            category = analysis_json.get("category", "未分類")
            sentiment = analysis_json.get("sentiment", "neutral")
            source_doc = analysis_json.get("source", {}).get("name", "")
            source_page = analysis_json.get("source", {}).get("page", "")

            # 単純な挨拶のみの場合はソース情報をクリア
            # message_text = message.text.strip().lower() if message.text else ""
            # greetings = ["こんにちは", "こんにちわ", "おはよう", "おはようございます", "こんばんは", "よろしく", "ありがとう", "さようなら", "hello", "hi", "thanks", "thank you", "bye"]
            
            # if category == "挨拶" or any(greeting in message_text for greeting in greetings):
            #     # 応答テキストに「情報ソース:」が含まれているかチェック
            #     if response_text and "情報ソース:" in response_text:
            #         # 情報ソース部分を削除
            #         response_text = re.sub(r'\n*情報ソース:.*$', '', response_text, flags=re.DOTALL)
            #     source_doc = ""
            #     source_page = ""
            #     safe_print("2222222222222")
                
        except Exception as json_error:
            safe_print(f"JSON解析エラー: {str(json_error)}")
            category = "未分類"
            sentiment = "neutral"
            source_doc = ""
            source_page = ""
        
        # トークン使用量を計算してチャット履歴を保存
        from modules.token_counter import TokenUsageTracker
        
        # ユーザーの会社IDを取得（トークン追跡用）
        from supabase_adapter import select_data
        user_result = select_data("users", filters={"id": message.user_id}) if message.user_id else None
        final_company_id = user_result.data[0].get("company_id") if user_result and user_result.data else None
        
        # プロンプト参照数をカウント（アクティブなリソース数）
        prompt_references = len(active_sources) if active_sources else 0
        
        safe_print(f"🔍 トークン追跡デバッグ:")
        safe_print(f"  ユーザーID: {message.user_id}")
        safe_print(f"  会社ID: {final_company_id}")
        safe_print(f"  メッセージ長: {len(message_text)}")
        safe_print(f"  応答長: {len(response_text)}")
        safe_print(f"  プロンプト参照数: {prompt_references}")
        
        # 新しいトークン追跡機能を使用してチャット履歴を保存
        try:
            tracker = TokenUsageTracker(db)
            chat_id = tracker.save_chat_with_prompts(
                user_message=message_text,
                bot_response=response_text,
                user_id=message.user_id,
                prompt_references=prompt_references,
                company_id=final_company_id,
                employee_id=message.employee_id,
                employee_name=message.employee_name,
                category=category,
                sentiment=sentiment,
                source_document=source_doc,
                source_page=source_page,
                model="gemini-2.5-flash"  # Gemini料金体系を使用
            )
            safe_print(f"✅ トークン追跡保存成功: {chat_id}")
        except Exception as token_error:
            safe_print(f"❌ トークン追跡エラー: {token_error}")
            # トークン追跡でエラーが発生した場合はフォールバック保存
            chat_id = str(uuid.uuid4())
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO chat_history (id, user_message, bot_response, timestamp, category, sentiment, employee_id, employee_name, source_document, source_page, user_id, company_id, prompt_references) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (chat_id, message_text, response_text, datetime.now().isoformat(), category, sentiment, message.employee_id, message.employee_name, source_doc, source_page, message.user_id, company_id, prompt_references)
            )
            db.commit()
        
        # ユーザーIDがある場合は質問カウントを更新
        if message.user_id and not limits_check.get("is_unlimited", False):
            safe_print(f"利用制限更新開始 - ユーザーID: {message.user_id}")
            safe_print(f"更新前の制限情報: {limits_check}")
            
            updated_limits = update_usage_count(message.user_id, "questions_used", db)
            safe_print(f"更新後の制限情報: {updated_limits}")
            
            if updated_limits:
                remaining_questions = updated_limits["questions_limit"] - updated_limits["questions_used"]
                limit_reached = remaining_questions <= 0
                safe_print(f"計算された残り質問数: {remaining_questions}, 制限到達: {limit_reached}")
            else:
                safe_print("利用制限の更新に失敗しました")
        
        safe_print(f"返り値: remaining_questions={remaining_questions}, limit_reached={limit_reached}")
        
        # ソース情報が有効な場合のみ返す（source_docとsource_pageが空でない場合）
        source_text = ""
        if source_doc and source_doc.strip():
            source_text = source_doc
            if source_page and str(source_page).strip():
                source_text += f" (P.{source_page})"
        
        safe_print(f"最終ソース情報: '{source_text}'")
        
        return {
            "response": response_text,
            "source": source_text if source_text and source_text.strip() else "",
            "remaining_questions": remaining_questions,
            "limit_reached": limit_reached
        }
    except Exception as e:
        safe_print(f"チャットエラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def chunk_knowledge_base(text: str, chunk_size: int = 1200) -> list[str]:
    """
    知識ベースを指定されたサイズでチャンク化する
    
    Args:
        text: チャンク化するテキスト
        chunk_size: チャンクのサイズ（文字数）デフォルト1200文字（task.yaml推奨）
    
    Returns:
        チャンク化されたテキストのリスト
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    overlap = int(chunk_size * 0.5)  # 50%のオーバーラップ（task.yaml推奨）
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        
        # チャンクの境界を調整（文の途中で切れないように）
        if end < len(text):
            # 最後の改行を探す
            search_start = max(start, end - 200)  # 200文字前から検索（1200文字チャンクに適正化）
            last_newline = text.rfind('\n', search_start, end)
            if last_newline > start:
                end = last_newline + 1
            else:
                # 改行がない場合は最後のスペースを探す
                last_space = text.rfind(' ', search_start, end)
                if last_space > start:
                    end = last_space + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # 次の開始位置（オーバーラップを考慮）
        if end < len(text):
            start = max(start + 1, end - overlap)
        else:
            start = end
    
    return chunks

async def process_chat_chunked(message: ChatMessage, db = Depends(get_db), current_user: dict = None):
    """
    チャンク化システムを使用したチャット処理
    知識ベースを50万文字ごとにチャンク化して段階的に処理
    """
    safe_print(f"🔄 チャンク化チャット処理開始 - ユーザーID: {message.user_id}")
    
    try:
        # 基本的な初期化処理
        message_text = message.message if hasattr(message, 'message') else message.text
        remaining_questions = 0
        limit_reached = False
        
        # 利用制限チェック
        from .database import get_usage_limits
        limits_check = get_usage_limits(message.user_id, db) if message.user_id else {"is_unlimited": True, "questions_limit": 0, "questions_used": 0}
        safe_print(f"利用制限チェック結果: {limits_check}")
        
        if not limits_check.get("is_unlimited", False):
            remaining_questions = limits_check["questions_limit"] - limits_check["questions_used"]
            limit_reached = remaining_questions <= 0
            
            if limit_reached:
                safe_print(f"❌ 利用制限到達 - 残り質問数: {remaining_questions}")
                return {
                    "response": "申し訳ございません。本日の質問回数制限に達しました。明日になると再度ご利用いただけます。",
                    "remaining_questions": 0,
                    "limit_reached": True
                }
        
        # 会社名の取得
        current_company_name = "WorkMate"
        if message.user_id:
            try:
                from supabase_adapter import select_data
                user_result = select_data("users", filters={"id": message.user_id})
                if user_result and user_result.data:
                    company_id = user_result.data[0].get("company_id")
                    if company_id:
                        company_data = get_company_by_id(company_id, db)
                        current_company_name = company_data["name"] if company_data else "WorkMate"
            except Exception as e:
                safe_print(f"会社名取得エラー: {str(e)}")
        
        # アクティブなリソースの取得
        active_sources = []
        if message.user_id:
            try:
                from supabase_adapter import select_data
                user_result = select_data("users", filters={"id": message.user_id})
                if user_result and user_result.data:
                    company_id = user_result.data[0].get("company_id")
                    if company_id:
                        active_sources = await get_active_resources_by_company_id(company_id, db)
            except Exception as e:
                safe_print(f"アクティブリソース取得エラー: {str(e)}")
        
        if not active_sources:
            safe_print("❌ アクティブなリソースが見つかりません")
            return {
                "response": "申し訳ございません。アクティブな知識ベースが見つかりません。管理画面でリソースを有効にしてください。",
                "remaining_questions": remaining_questions,
                "limit_reached": limit_reached
            }
        
        # 知識ベース内容の取得
        safe_print(f"📚 知識ベース取得開始 - アクティブソース: {len(active_sources)}個")
        active_knowledge_text = await get_active_resources_content_by_ids(active_sources, db)
        
        if not active_knowledge_text or not active_knowledge_text.strip():
            safe_print("❌ 知識ベース内容が空です")
            return {
                "response": "申し訳ございません。知識ベースの内容が空です。管理画面で別のリソースを有効にしてください。",
                "remaining_questions": remaining_questions,
                "limit_reached": limit_reached
            }
        
        safe_print(f"📊 取得した知識ベース: {len(active_knowledge_text)} 文字")
        
        # アクティブなリソースの情報とSpecial指示を取得
        special_instructions = []
        active_resource_names = []
        try:
            from supabase_adapter import select_data
            for source_id in active_sources:
                source_result = select_data("document_sources", columns="name", filters={"id": source_id})
                if source_result.data and len(source_result.data) > 0:
                    source_data = source_result.data[0]
                    source_name = source_data.get('name', 'Unknown')
                    active_resource_names.append(source_name)
                    
                    if source_data.get('special') and source_data['special'].strip():
                        special_instructions.append({
                            "name": source_name,
                            "instruction": source_data['special'].strip()
                        })
            safe_print(f"アクティブリソース: {len(active_resource_names)}個 - {active_resource_names}")
            safe_print(f"Special指示: {len(special_instructions)}個のリソースにSpecial指示があります")
        except Exception as e:
            safe_print(f"リソース情報取得エラー: {str(e)}")
            special_instructions = []
            active_resource_names = []

        # Special指示をプロンプトに追加するための文字列を構築
        special_instructions_text = ""
        if special_instructions:
            special_instructions_text = "\n\n特別な回答指示（以下のリソースを参照する際は、各リソースの指示に従ってください）：\n"
            for idx, inst in enumerate(special_instructions, 1):
                special_instructions_text += f"{idx}. 【{inst['name']}】: {inst['instruction']}\n"

        # 🔪 最初から1200文字でチャンク化（task.yaml推奨サイズ）
        CHUNK_SIZE = 1200  # 1200文字でチャンク化（task.yaml推奨：1000-1200文字）
        raw_chunks = chunk_knowledge_base(active_knowledge_text, CHUNK_SIZE)
        safe_print(f"🔪 チャンク化完了: {len(raw_chunks)}個のチャンク (チャンクサイズ: {CHUNK_SIZE:,}文字)")
        
        # 会話履歴の取得
        conversation_history = ""
        try:
            if message.user_id:
                from supabase_adapter import select_data
                chat_history_result = select_data(
                    "chat_history",
                    filters={"employee_id": message.user_id},
                    limit=2
                )
                
                if chat_history_result and chat_history_result.data:
                    recent_messages = list(reversed(chat_history_result.data))
                    
                    if recent_messages:
                        conversation_history = "直近の会話履歴：\n"
                        for msg in recent_messages:
                            user_msg = (msg.get('user_message', '') or '')[:100]
                            bot_msg = (msg.get('bot_response', '') or '')[:100]
                            if len(msg.get('user_message', '')) > 100:
                                user_msg += "..."
                            if len(msg.get('bot_response', '')) > 100:
                                bot_msg += "..."
                            conversation_history += f"ユーザー: {user_msg}\n"
                            conversation_history += f"アシスタント: {bot_msg}\n\n"
        except Exception as e:
            safe_print(f"会話履歴取得エラー: {str(e)}")
        
        # 🔍 情報発見まで継続検索: 見つかったら即座に終了、見つからなければ最後まで継続
        all_rag_results = []  # RAG検索結果を蓄積
        all_chunk_info = []   # チャンク情報を蓄積
        successful_chunks = 0
        processed_chunks = set()  # 処理済みチャンクのインデックスを記録
        BATCH_SIZE = min(5, len(raw_chunks))  # バッチサイズを縮小して精度向上（25→5）
        
        safe_print(f"🔍 全ファイル全チャンク完全検索モード: 合計{len(raw_chunks)}個のチャンク、バッチサイズ{BATCH_SIZE}で処理")
        safe_print(f"🎯 戦略: 全チャンクを検索してから最良の結果を選択（早期終了なし）")
        safe_print(f"📚 検索対象: 全{len(active_resource_names)}ファイルの統合知識ベース")
        
        batch_start = 0
        total_batches = (len(raw_chunks) + BATCH_SIZE - 1) // BATCH_SIZE  # 切り上げ除算
        current_batch_num = 1
        skipped_batches = 0  # RAG品質不足でスキップしたバッチ数
        
        # 🚀 全バッチのRAG検索を実行（早期終了なし）
        while batch_start < len(raw_chunks):
            # 未処理のチャンクから次のバッチを取得
            available_chunks = [i for i in range(batch_start, min(batch_start + BATCH_SIZE, len(raw_chunks))) 
                              if i not in processed_chunks]
            
            if not available_chunks:
                batch_start += BATCH_SIZE
                current_batch_num += 1
                continue
                
            safe_print(f"🔄 RAG検索バッチ ({current_batch_num}/{total_batches}): チャンク {available_chunks[0]+1}-{available_chunks[-1]+1} ({len(available_chunks)}個)")
            safe_print(f"📊 RAG処理進捗: {len(processed_chunks)}/{len(raw_chunks)}チャンク完了 ({len(processed_chunks)/len(raw_chunks)*100:.1f}%)")
            
            # 複数チャンクを結合してRAG検索
            combined_chunk = ""
            chunk_info = []
            
            for chunk_idx in available_chunks:
                raw_chunk = raw_chunks[chunk_idx]
                combined_chunk += f"\n\n=== チャンク {chunk_idx+1} ===\n{raw_chunk}"
                chunk_info.append(f"チャンク{chunk_idx+1}({len(raw_chunk):,}文字)")
            
            safe_print(f"📊 結合チャンク: {chunk_info}")
            safe_print(f"📊 結合サイズ: {len(combined_chunk):,} 文字")
            
            # 🔄 高度なRAG検索（制限なし）
            filtered_chunk = None
            rag_attempts = 0
            min_content_threshold = 50  # さらに緩和（100→50）
            
            if len(combined_chunk) > 1000:  # 閾値を大幅に緩和
                safe_print(f"🔄 RAG検索開始")
                
                # シンプルな検索戦略
                # company_idを取得（process_chat_chunked内で利用可能なように）
                user_company_id = None
                if message.user_id:
                    try:
                        from supabase_adapter import select_data
                        user_result = select_data("users", filters={"id": message.user_id})
                        if user_result and user_result.data:
                            user_company_id = user_result.data[0].get("company_id")
                    except Exception:
                        pass
                
                filtered_chunk = simple_rag_search(combined_chunk, message_text, max_results=100, company_id=user_company_id)
                rag_attempts = 1
                
                safe_print(f"📊 RAG検索結果: {len(filtered_chunk)} 文字")
            else:
                filtered_chunk = combined_chunk
                safe_print(f"📊 小さなバッチのため RAG検索をスキップ")
            
            # 🎯 厳格なRAG品質判定
            rag_quality_score = _evaluate_rag_quality(filtered_chunk, message_text, rag_attempts)
            safe_print(f"🎯 最終RAG品質スコア: {rag_quality_score:.2f} (閾値: 0.10)")
            
            # 品質スコアの閾値を調整（0.20→0.10）して、より多くの結果を含める
            if rag_quality_score >= 0.10:
                safe_print(f"✅ RAG品質合格 (スコア: {rag_quality_score:.2f}) - 結果を蓄積")
                
                # RAG結果を蓄積（全て処理してから最良を選択）
                batch_info = f"バッチ {len(available_chunks)}個 ({available_chunks[0]+1}-{available_chunks[-1]+1})"
                rag_info = f"RAG検索{rag_attempts}回実行" if rag_attempts > 0 else "RAG検索なし"
                
                all_rag_results.append({
                    'content': filtered_chunk,
                    'batch_info': batch_info,
                    'rag_info': rag_info,
                    'quality_score': rag_quality_score,
                    'chunk_indices': available_chunks,
                    'content_length': len(filtered_chunk),
                    'batch_num': current_batch_num
                })
                
                all_chunk_info.extend(chunk_info)
                successful_chunks += len(available_chunks)
                safe_print(f"📚 RAG結果蓄積: {len(all_rag_results)}個目のバッチを追加")
            else:
                safe_print(f"⚠️ RAG品質不足 (スコア: {rag_quality_score:.2f} < 0.10) - このバッチをスキップ")
                skipped_batches += 1
            
            # このバッチのチャンクを処理済みに追加
            for chunk_idx in available_chunks:
                processed_chunks.add(chunk_idx)
            
            # 次のバッチへ進む（情報が見つからない場合は最後まで継続）
            batch_start += BATCH_SIZE
            current_batch_num += 1
            
            # 🎯 重要: 情報が見つかった場合のみ早期終了を検討
            # しかし、ユーザーの要求により「見つからない場合は最後まで検索」を保証
            if all_rag_results:
                safe_print(f"✅ 情報発見: {len(all_rag_results)}個のバッチで情報を発見")
                safe_print(f"🔄 継続検索: 見つからない場合に備えて最後まで検索を継続")
                # 早期終了は行わず、全チャンクを確実に処理
        
        # 🏆 全チャンク処理完了後、最良の結果を選択
        final_response = ""
        if all_rag_results:
            safe_print(f"🏆 全チャンク検索完了！最良の結果を選択: {len(all_rag_results)}個のバッチから")
            
            # 結果を品質スコア順にソート
            sorted_results = sorted(all_rag_results, key=lambda x: x['quality_score'], reverse=True)
            
            # 上位の結果を統合（最大5個まで）
            top_results = sorted_results[:min(5, len(sorted_results))]
            safe_print(f"📊 上位{len(top_results)}個の結果を統合:")
            for i, result in enumerate(top_results, 1):
                safe_print(f"  {i}. バッチ{result['batch_num']}: スコア{result['quality_score']:.2f}, 長さ{result['content_length']:,}文字")
            
            # 上位結果を統合
            combined_rag_content = ""
            total_quality_score = 0
            for i, rag_result in enumerate(top_results, 1):
                combined_rag_content += f"\n\n=== 最良RAG結果 {i}/{len(top_results)} ===\n"
                combined_rag_content += f"処理情報: {rag_result['batch_info']}, {rag_result['rag_info']}\n"
                combined_rag_content += f"品質スコア: {rag_result['quality_score']:.2f}\n"
                combined_rag_content += f"内容:\n{rag_result['content']}"
                total_quality_score += rag_result['quality_score']
            
            average_quality = total_quality_score / len(top_results)
            safe_print(f"📊 統合RAG結果: {len(combined_rag_content):,}文字, 平均品質スコア: {average_quality:.2f}")
            
            # 統合プロンプトの作成（全チャンク検索完了版）
            unified_prompt = f"""
あなたは親切で丁寧な対応ができる{current_company_name}のアシスタントです。
以下は全{len(raw_chunks)}チャンクの完全検索で発見された最良の知識ベース情報です。この情報を基に、ユーザーの質問に対して最も具体的で詳細な回答を提供してください。

**重要な指示:**
1. 全ファイル全チャンクから選ばれた最良の情報を活用してください
2. 質問に直接関連する情報を中心に、具体的で詳細な回答を作成してください
3. 複数の結果から最も適切な情報を統合して回答してください
4. **実際に知識ベースから有用な情報を見つけて回答した場合**、回答の最後に「情報ソース: [ファイル名]」を記載してください
5. 回答は**Markdown記法**を使用して見やすく整理してください

検索統計: 
- 対象ファイル: {len(active_resource_names)}個 ({', '.join(active_resource_names)})
- 検索チャンク: 全{len(raw_chunks)}個
- 発見結果: {len(all_rag_results)}個のバッチ
- 選択結果: 上位{len(top_results)}個 (平均品質スコア: {average_quality:.2f}){special_instructions_text}

全チャンク検索で発見された最良の情報:
{combined_rag_content}

{conversation_history}

ユーザーの質問：
{message_text}
"""
            
            # Gemini API呼び出し（一度だけ）
            try:
                model = setup_gemini()
                
                safe_print(f"🤖 統合Gemini API呼び出し開始")
                safe_print(f"📏 統合プロンプトサイズ: {len(unified_prompt):,} 文字")
                
                # タイムアウト付きでAPI呼び出し
                import time
                start_time = time.time()
                
                response = model.generate_content(unified_prompt)
                
                end_time = time.time()
                elapsed_time = end_time - start_time
                safe_print(f"📨 統合API応答受信 (処理時間: {elapsed_time:.2f}秒)")
                
                if response and hasattr(response, 'text'):
                    if response.text and response.text.strip():
                        final_response = response.text.strip()
                        safe_print(f"📝 統合応答テキスト長: {len(final_response)} 文字")
                        safe_print(f"📝 統合応答内容（最初の100文字）: {final_response[:100]}...")
                    else:
                        safe_print(f"⚠️ 統合応答で空のテキスト")
                        final_response = "申し訳ございません。適切な回答を生成できませんでした。"
                else:
                    safe_print(f"⚠️ 統合応答で無効な応答オブジェクト")
                    final_response = "申し訳ございません。システムエラーが発生しました。"
                    
            except Exception as e:
                safe_print(f"❌ 統合Gemini API呼び出しエラー: {str(e)}")
                safe_print(f"🔍 エラータイプ: {type(e).__name__}")
                import traceback
                safe_print(f"🔍 エラー詳細: {traceback.format_exc()}")
                final_response = f"申し訳ございません。システムエラーが発生しました: {str(e)}"
        else:
            # RAG結果が全くない場合
            safe_print(f"❌ 全てのバッチでRAG品質不足のため、情報が見つかりませんでした")
            final_response = f"""申し訳ございません。全{len(raw_chunks)}個のチャンクを検索いたしましたが、ご質問に対する適切な回答が見つかりませんでした。

🔍 **検索結果**:
- 検索対象: {len(raw_chunks)}個のチャンク
- 処理完了: {len(processed_chunks)}個 (100%)
- RAG品質合格: {len(all_rag_results)}個
- スキップ: {skipped_batches}個（品質不足）

別の質問方法でお試しいただくか、管理者にお問い合わせください。"""
        
        # プロンプト参照数を計算（アクティブリソース数をプロンプト参照数として使用）
        prompt_references = len(active_sources)
        safe_print(f"💰 プロンプト参照数: {prompt_references} (アクティブリソース数)")
        
        # チャット履歴の保存
        try:
            from modules.token_counter import TokenUsageTracker
            from supabase_adapter import select_data
            
            user_result = select_data("users", filters={"id": message.user_id}) if message.user_id else None
            chat_company_id = user_result.data[0].get("company_id") if user_result and user_result.data else None
            
            tracker = TokenUsageTracker(db)
            chat_id = tracker.save_chat_with_prompts(
                user_message=message_text,
                bot_response=final_response,
                user_id=message.user_id,
                prompt_references=prompt_references,
                company_id=chat_company_id,
                employee_id=message.employee_id,
                employee_name=message.employee_name,
                category="チャンク処理",
                sentiment="neutral",
                model="gemini-2.5-flash"
            )
            safe_print(f"💾 チャット履歴保存完了 - ID: {chat_id}, プロンプト参照: {prompt_references}")
        except Exception as e:
            safe_print(f"チャット履歴保存エラー: {str(e)}")
        
        # 利用制限の更新
        if message.user_id and not limits_check.get("is_unlimited", False):
            try:
                from .database import update_usage_count
                updated_limits = update_usage_count(message.user_id, "questions_used", db)
                if updated_limits:
                    remaining_questions = updated_limits["questions_limit"] - updated_limits["questions_used"]
                    limit_reached = remaining_questions <= 0
                    safe_print(f"📊 利用制限更新完了 - 残り: {remaining_questions}")
            except Exception as e:
                safe_print(f"利用制限更新エラー: {str(e)}")
        
        processing_rate = (len(processed_chunks) / len(raw_chunks) * 100) if raw_chunks else 0
        success_rate = (successful_chunks / len(raw_chunks) * 100) if raw_chunks else 0
        
        safe_print(f"🔍 情報発見まで継続検索処理完了")
        safe_print(f"📊 処理統計: 全{len(raw_chunks)}チャンク中 {len(processed_chunks)}チャンク処理済み ({processing_rate:.1f}%)")
        safe_print(f"📊 成功統計: {successful_chunks}チャンクから有効回答取得 ({success_rate:.1f}%)")
        safe_print(f"📝 RAG結果蓄積: {len(all_rag_results)}個のバッチ")
        safe_print(f"🤖 Gemini呼び出し: 1回のみ (情報発見時即座送信)")
        safe_print(f"⚡ 効率化: {skipped_batches}バッチをRAG品質判定でスキップ ({skipped_batches/total_batches*100:.1f}%削減)")
        
        # 情報発見まで継続検索の結果を詳細に報告
        if all_rag_results:
            safe_print(f"🎉 情報発見成功: {len(all_rag_results)}個のバッチで情報を発見し、即座にGeminiに送信")
            safe_print(f"✅ 効率的終了: 情報発見後は残り{len(raw_chunks) - len(processed_chunks)}チャンクをスキップ")
        elif len(processed_chunks) == len(raw_chunks):
            safe_print(f"🔍 完全検索完了: 全{len(raw_chunks)}チャンクを探索したが、該当する情報は見つかりませんでした")
        else:
            safe_print(f"⚠️ 不完全な処理: {len(raw_chunks) - len(processed_chunks)}チャンクが未処理")
        
        # ソース情報の抽出（回答からファイル名を抽出）
        source_text = ""
        if final_response and active_resource_names:
            # 回答から「情報ソース:」部分を抽出
            import re
            source_match = re.search(r'情報ソース[:：]\s*([^\n]+)', final_response)
            if source_match:
                # 情報が見つからない場合の回答には情報ソースを含めない
                no_info_in_response = any(phrase in final_response.lower() for phrase in [
                    "情報は含まれておりませんでした",
                    "情報が含まれておりませんでした", 
                    "に関する情報は含まれておりません",
                    "該当する情報が見つかりません"
                ])
                
                if not no_info_in_response:
                    source_text = source_match.group(1).strip()
                
                # 情報ソース部分を回答から削除
                final_response = re.sub(r'\n*情報ソース[:：][^\n]*', '', final_response).strip()
        
        # 無効なソース情報は空文字列にする
        invalid_sources = ['なし', 'デバッグ', 'debug', '情報なし', '該当なし', '不明', 'unknown', 'null', 'undefined']
        if source_text.lower() in [s.lower() for s in invalid_sources] or 'デバッグ' in source_text or 'debug' in source_text.lower():
            source_text = ""
        
        safe_print(f"📄 最終ソース情報: '{source_text}'")
        
        # =============================================================
        # 🔍 最終分析レポート - RAG精度と参照状況の詳細分析
        # =============================================================
        safe_print(f"\n{'='*80}")
        safe_print(f"🔍 最終分析レポート - RAG精度と参照状況")
        safe_print(f"{'='*80}")
        
        # 1. 検索範囲と処理統計
        safe_print(f"📊 【検索範囲】")
        safe_print(f"  └ 対象ファイル: {len(active_resource_names)}個")
        for i, file_name in enumerate(active_resource_names, 1):
            safe_print(f"    {i}. {file_name}")
        safe_print(f"  └ 総チャンク数: {len(raw_chunks)}個")
        safe_print(f"  └ 処理完了チャンク: {len(processed_chunks)}個 ({processing_rate:.1f}%)")
        safe_print(f"  └ 成功チャンク: {successful_chunks}個 ({success_rate:.1f}%)")
        
        # 2. RAG検索品質分析
        safe_print(f"\n📈 【RAG検索品質分析】")
        if all_rag_results:
            safe_print(f"  └ 品質合格バッチ: {len(all_rag_results)}個")
            safe_print(f"  └ 品質不足スキップ: {skipped_batches}個")
            safe_print(f"  └ 品質合格率: {len(all_rag_results)/(len(all_rag_results)+skipped_batches)*100:.1f}%")
            
            # 品質スコア分布
            quality_scores = [result['quality_score'] for result in all_rag_results]
            min_score = min(quality_scores)
            max_score = max(quality_scores)
            avg_score = sum(quality_scores) / len(quality_scores)
            safe_print(f"  └ 品質スコア分布:")
            safe_print(f"    ├ 最高スコア: {max_score:.3f}")
            safe_print(f"    ├ 最低スコア: {min_score:.3f}")
            safe_print(f"    └ 平均スコア: {avg_score:.3f}")
            
            # 上位5個の詳細
            safe_print(f"  └ 上位品質バッチ詳細:")
            sorted_results = sorted(all_rag_results, key=lambda x: x['quality_score'], reverse=True)
            for i, result in enumerate(sorted_results[:5], 1):
                safe_print(f"    {i}. バッチ{result['batch_num']}: スコア{result['quality_score']:.3f}, {result['content_length']:,}文字")
        else:
            safe_print(f"  └ ⚠️ 品質合格バッチ: 0個（全バッチが品質基準未満）")
            safe_print(f"  └ 全バッチがスキップ: {skipped_batches}個")
            safe_print(f"  └ 品質基準: 0.10以上が必要")
        
        # 3. データカバレッジ分析
        safe_print(f"\n📋 【データカバレッジ分析】")
        total_chars = sum(len(chunk) for chunk in raw_chunks)
        processed_chars = sum(len(raw_chunks[i]) for i in processed_chunks)
        coverage_rate = (processed_chars / total_chars * 100) if total_chars > 0 else 0
        
        safe_print(f"  └ 総データ量: {total_chars:,}文字")
        safe_print(f"  └ 処理データ量: {processed_chars:,}文字")
        safe_print(f"  └ カバレッジ率: {coverage_rate:.1f}%")
        
        if all_rag_results:
            used_chars = sum(result['content_length'] for result in all_rag_results)
            utilization_rate = (used_chars / total_chars * 100) if total_chars > 0 else 0
            safe_print(f"  └ 回答利用データ: {used_chars:,}文字")
            safe_print(f"  └ データ利用率: {utilization_rate:.1f}%")
        
        # 4. 検索精度評価
        safe_print(f"\n🎯 【検索精度評価】")
        query_keywords = set(message_text.lower().split())
        if all_rag_results and final_response:
            # キーワード一致率計算
            response_words = set(final_response.lower().split())
            keyword_matches = len(query_keywords.intersection(response_words))
            keyword_match_rate = (keyword_matches / len(query_keywords) * 100) if query_keywords else 0
            
            safe_print(f"  └ クエリキーワード数: {len(query_keywords)}個")
            safe_print(f"  └ 回答内一致キーワード: {keyword_matches}個")
            safe_print(f"  └ キーワード一致率: {keyword_match_rate:.1f}%")
            
            # 情報発見状況
            has_source = bool(source_text and source_text.strip())
            safe_print(f"  └ 情報ソース特定: {'✅ 成功' if has_source else '❌ 失敗'}")
            if has_source:
                safe_print(f"    └ ソース: {source_text}")
        
        # 5. 処理効率分析
        safe_print(f"\n⚡ 【処理効率分析】")
        safe_print(f"  └ 総バッチ数: {total_batches}個")
        safe_print(f"  └ 効率的スキップ: {skipped_batches}個 ({skipped_batches/total_batches*100:.1f}%)")
        safe_print(f"  └ Gemini API呼び出し: 1回（最適化済み）")
        
        # 6. 最終回答品質判定
        safe_print(f"\n✅ 【最終回答品質判定】")
        if final_response:
            response_length = len(final_response)
            safe_print(f"  └ 回答文字数: {response_length:,}文字")
            
            # 回答品質の判定
            quality_indicators = {
                "具体的な情報": any(word in final_response for word in ['手順', '方法', '設定', '場合', '必要', '確認']),
                "データベース情報": source_text and source_text.strip(),
                "構造化された回答": '##' in final_response or '###' in final_response or '- ' in final_response,
                "適切な長さ": 50 <= response_length <= 5000,
                "エラー回答でない": not any(phrase in final_response for phrase in ['申し訳', 'エラー', '見つかりません'])
            }
            
            safe_print(f"  └ 回答品質チェック:")
            quality_score = 0
            for indicator, result in quality_indicators.items():
                status = "✅" if result else "❌"
                safe_print(f"    ├ {indicator}: {status}")
                if result:
                    quality_score += 1
            
            final_quality = (quality_score / len(quality_indicators)) * 100
            safe_print(f"    └ 総合品質スコア: {final_quality:.1f}% ({quality_score}/{len(quality_indicators)})")
        
        # 7. 問題・改善提案
        safe_print(f"\n🔧 【問題・改善提案】")
        if len(all_rag_results) == 0:
            safe_print(f"  ⚠️ 問題: 全バッチでRAG品質が基準未満（スコア < 0.10）")
            safe_print(f"     └ 提案: 検索クエリの見直しまたは知識ベースの拡充が必要")
        elif success_rate < 50:
            safe_print(f"  ⚠️ 問題: チャンク成功率が低い（{success_rate:.1f}% < 50%）")
            safe_print(f"     └ 提案: チャンクサイズまたは検索アルゴリズムの調整を検討")
        elif coverage_rate < 80:
            safe_print(f"  ⚠️ 問題: データカバレッジが不完全（{coverage_rate:.1f}% < 80%）")
            safe_print(f"     └ 提案: より包括的な検索戦略の実装を検討")
        else:
            safe_print(f"  ✅ 良好: RAG検索システムは正常に動作しています")
        
        # 8. 処理完了サマリー
        safe_print(f"\n🏁 【処理完了サマリー】")
        safe_print(f"  └ 検索実行: {'✅ 完了' if len(processed_chunks) > 0 else '❌ 失敗'}")
        safe_print(f"  └ 情報発見: {'✅ 成功' if all_rag_results else '❌ 失敗'}")
        safe_print(f"  └ 回答生成: {'✅ 成功' if final_response and len(final_response) > 20 else '❌ 失敗'}")
        safe_print(f"  └ ソース特定: {'✅ 成功' if source_text and source_text.strip() else '❌ 失敗'}")
        
        safe_print(f"{'='*80}")
        safe_print(f"🔍 最終分析レポート完了")
        safe_print(f"{'='*80}\n")
        
        return {
            "response": final_response,
            "source": source_text,
            "remaining_questions": remaining_questions,
            "limit_reached": limit_reached,
            "chunks_processed": len(raw_chunks),
            "successful_chunks": successful_chunks,
            # 分析データを追加
            "analysis": {
                "total_chunks": len(raw_chunks),
                "processed_chunks": len(processed_chunks),
                "successful_chunks": successful_chunks,
                "processing_rate": processing_rate,
                "success_rate": success_rate,
                "coverage_rate": coverage_rate,
                "quality_batches": len(all_rag_results),
                "skipped_batches": skipped_batches,
                "data_coverage": f"{processed_chars:,}/{total_chars:,} chars",
                "final_quality": final_quality if 'final_quality' in locals() else 0
            }
        }
        
    except Exception as e:
        safe_print(f"❌ チャンク化処理で重大エラー: {str(e)}")
        # エラー時のデフォルト値を設定
        try:
            remaining_questions = remaining_questions if 'remaining_questions' in locals() else 0
            limit_reached = limit_reached if 'limit_reached' in locals() else False
        except:
            remaining_questions = 0
            limit_reached = False
            
        return {
            "response": f"申し訳ございません。システムエラーが発生しました: {str(e)}",
            "source": "",
            "remaining_questions": remaining_questions,
            "limit_reached": limit_reached
        }

async def lightning_rag_search(knowledge_text: str, query: str, max_results: int = 20) -> str:
    """
    雷速RAG検索 - 最高速度を重視した検索システム
    - キャッシュシステム
    - 事前フィルタリング
    - 大きなチャンクサイズによる高速化
    """
    if not SPEED_RAG_AVAILABLE:
        safe_print("高速RAGが利用できないため、従来のRAGにフォールバック")
        return simple_rag_search(knowledge_text, query, max_results)
    
    if not knowledge_text or not query:
        return knowledge_text
    
    try:
        safe_print(f"⚡ 雷速RAG検索開始: {len(knowledge_text):,}文字, クエリ: {query[:30]}...")
        
        # 高速検索実行
        result = await high_speed_rag.lightning_search(
            query=query,
            knowledge_text=knowledge_text,
            max_results=max_results
        )
        
        if result:
            safe_print(f"⚡ 雷速RAG検索完了: {len(result):,}文字の関連情報を抽出")
            return result
        else:
            safe_print("⚠️ 雷速RAG検索で結果が見つからず、従来のRAGにフォールバック")
            return simple_rag_search(knowledge_text, query, max_results)
    
    except Exception as e:
        safe_print(f"❌ 雷速RAG検索エラー: {str(e)}")
        # エラー時は従来のRAGにフォールバック
        return simple_rag_search(knowledge_text, query, max_results)

async def enhanced_rag_search(knowledge_text: str, query: str, max_results: int = 20) -> str:
    """
    強化されたRAG検索システム
    - インテリジェントなチャンク化
    - ハイブリッド検索（BM25 + セマンティック）
    - 反復検索による高精度検索
    """
    if not RAG_ENHANCED_AVAILABLE:
        safe_print("強化RAGが利用できないため、従来のRAGにフォールバック")
        return simple_rag_search(knowledge_text, query, max_results)
    
    if not knowledge_text or not query:
        return knowledge_text
    
    try:
        safe_print(f"🚀 強化RAG検索開始: {len(knowledge_text):,}文字, クエリ: {query[:50]}...")
        
        # 反復検索による高精度検索
        result = await enhanced_rag.iterative_search(
            query=query,
            knowledge_text=knowledge_text,
            max_iterations=3,
            min_results=5
        )
        
        if result:
            safe_print(f"✅ 強化RAG検索完了: {len(result):,}文字の関連情報を抽出")
            return result
        else:
            safe_print("⚠️ 強化RAG検索で結果が見つからず、従来のRAGにフォールバック")
            return simple_rag_search(knowledge_text, query, max_results)
    
    except Exception as e:
        safe_print(f"❌ 強化RAG検索エラー: {str(e)}")
        # エラー時は従来のRAGにフォールバック
        return simple_rag_search(knowledge_text, query, max_results)

def adaptive_rag_search(knowledge_text: str, query: str, max_results: int = 10) -> str:
    """
    適応的RAG検索 - 知識ベースのサイズに応じて最適な検索手法を選択
    """
    if not knowledge_text or not query:
        return knowledge_text
    
    text_length = len(knowledge_text)
    safe_print(f"📊 適応的RAG検索: テキスト長 {text_length:,}文字")
    
    # 小さなテキストの場合は全体を返す
    if text_length <= 10000:
        safe_print("📝 小さなテキストのため全体を返却")
        return knowledge_text
    
    # 中程度のテキストの場合は従来のRAG
    elif text_length <= 100000:
        safe_print("🎯 中程度のテキストのため従来のRAG検索を実行")
        return simple_rag_search(knowledge_text, query, max_results)
    
    # 大きなテキストの場合は強化RAG（非同期処理が必要なため、ここでは従来のRAGを使用）
    else:
        safe_print("🚀 大きなテキストのため高性能RAG検索を実行")
        # 段落数を増やして精度向上
        return simple_rag_search(knowledge_text, query, max_results * 2)

def multi_pass_rag_search(knowledge_text: str, query: str, max_results: int = 15) -> str:
    """
    多段階RAG検索 - 複数の検索戦略を組み合わせて精度を向上
    """
    if not knowledge_text or not query:
        return knowledge_text
    
    try:
        safe_print(f"🔄 多段階RAG検索開始: {len(knowledge_text):,}文字")
        
        # 第1段階: 広い検索
        broad_results = simple_rag_search(knowledge_text, query, max_results * 3)
        
        # 第2段階: クエリを拡張して再検索
        expanded_query = expand_query(query)
        if expanded_query != query:
            safe_print(f"🔍 クエリを拡張: '{query}' → '{expanded_query}'")
            expanded_results = simple_rag_search(knowledge_text, expanded_query, max_results * 2)
            
            # 結果をマージ
            combined_text = f"{broad_results}\n\n{'='*50}\n\n{expanded_results}"
            
            # 第3段階: 重複を除去して最終調整
            final_results = simple_rag_search(combined_text, query, max_results)
        else:
            final_results = broad_results
        
        safe_print(f"✅ 多段階RAG検索完了: {len(final_results):,}文字")
        return final_results
        
    except Exception as e:
        safe_print(f"❌ 多段階RAG検索エラー: {str(e)}")
        return simple_rag_search(knowledge_text, query, max_results)

def expand_query(query: str) -> str:
    """
    クエリ拡張 - 類義語や関連用語を追加して検索精度を向上
    """
    # 基本的なクエリ拡張のマッピング
    expansion_map = {
        '方法': ['手順', 'やり方', 'プロセス', '流れ'],
        '手順': ['方法', 'ステップ', 'プロセス', '流れ'],
        '問題': ['課題', 'トラブル', 'エラー', '不具合'],
        '設定': ['構成', 'コンフィグ', '設定値', 'セットアップ'],
        '使い方': ['利用方法', '操作方法', '使用方法', '操作手順'],
        'エラー': ['問題', 'トラブル', '不具合', 'バグ'],
        '料金': ['価格', '費用', 'コスト', '値段'],
        '機能': ['特徴', '仕様', '性能', '能力'],
    }
    
    expanded_terms = []
    query_words = query.split()
    
    for word in query_words:
        expanded_terms.append(word)
        if word in expansion_map:
            # 1つの類義語を追加（クエリが長くなりすぎないように）
            expanded_terms.append(expansion_map[word][0])
    
    expanded_query = ' '.join(expanded_terms)
    return expanded_query if len(expanded_query) <= len(query) * 2 else query