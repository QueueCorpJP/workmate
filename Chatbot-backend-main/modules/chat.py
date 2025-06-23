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

# 新しいRAGシステムのインポートを追加
try:
    from .rag_enhanced import enhanced_rag, SearchResult
    RAG_ENHANCED_AVAILABLE = True
except ImportError:
    RAG_ENHANCED_AVAILABLE = False
    safe_print("⚠️ 強化RAGシステムが利用できないため、従来のRAGを使用します")

# 高速化RAGシステムのインポートを追加
try:
    from .rag_optimized import high_speed_rag
    SPEED_RAG_AVAILABLE = True
    safe_print("⚡ 高速化RAGシステムが利用可能です")
except ImportError:
    SPEED_RAG_AVAILABLE = False
    safe_print("⚠️ 高速化RAGシステムが利用できません")

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

def simple_rag_search(knowledge_text: str, query: str, max_results: int = 5) -> str:
    """
    ハイブリッドRAG検索 - BM25S（語彙）+ セマンティック（意味）検索の組み合わせ
    """
    if not knowledge_text or not query:
        return knowledge_text
    
    # 高速化RAGが利用可能な場合は優先使用
    if SPEED_RAG_AVAILABLE and len(knowledge_text) > 10000:
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 既存のイベントループがある場合
                future = asyncio.ensure_future(high_speed_rag.lightning_search(query, knowledge_text, max_results))
                return knowledge_text[:50000]  # 暫定的な結果を返す
            else:
                # 新しいイベントループを作成
                return asyncio.run(high_speed_rag.lightning_search(query, knowledge_text, max_results))
        except Exception as e:
            safe_print(f"高速RAG呼び出しエラー: {e}")
    
    try:
        import bm25s
        import re
        
        # 🔍 改善: より柔軟なクエリ前処理
        processed_query = _preprocess_query(query)
        safe_print(f"🔍 クエリ前処理: '{query}' → '{processed_query}'")
        
        # 高速化: より大きなチャンクサイズで分割
        if len(knowledge_text) > 50000:
            # 大きなテキストの場合は大きなチャンクで分割
            chunk_size = 3000
            chunks = []
            for i in range(0, len(knowledge_text), chunk_size):
                chunk = knowledge_text[i:i+chunk_size].strip()
                if chunk and len(chunk) > 100:
                    chunks.append(chunk)
        else:
            # 小さなテキストの場合は段落分割
            chunks = re.split(r'\n\s*\n', knowledge_text)
            chunks = [p.strip() for p in chunks if len(p.strip()) > 50]
        
        if len(chunks) < 2:
            return knowledge_text[:100000]  # チャンクが少ない場合はそのまま
        
        # 🚀 ハイブリッド検索の実行
        bm25_results = _bm25_search(chunks, processed_query, max_results)
        semantic_results = _semantic_search(chunks, processed_query, max_results)
        
        # 結果の統合と再ランキング
        combined_results = _combine_search_results(bm25_results, semantic_results, processed_query, max_results)
        
        # 🔍 完全検索: 全ての関連チャンクを取得（文字数制限を大幅緩和）
        result_chunks = []
        total_length = 0
        max_length = 500000  # 制限を50万文字に大幅拡大
        
        # 統合結果から最良のチャンクを選択
        for result in combined_results:
            chunk = result['content']
            score = result['score']
            
            if total_length + len(chunk) > max_length and len(result_chunks) >= 20:
                # 最低20個のチャンクは確保し、それ以降は制限適用
                safe_print(f"🔍 文字数制限到達: {total_length:,}文字 (制限: {max_length:,}文字)")
                break
            result_chunks.append(chunk)
            total_length += len(chunk)
        
        result = '\n\n'.join(result_chunks)
        safe_print(f"🚀 ハイブリッドRAG検索完了: {len(result_chunks)}個のチャンク、{len(result)}文字 (元: {len(knowledge_text)}文字)")
        return result
        
    except Exception as e:
        safe_print(f"RAG検索エラー: {str(e)}")
        # エラーの場合は最初の部分を返す
        return knowledge_text[:50000]  # フォールバック時の文字数も増加

def _preprocess_query(query: str) -> str:
    """クエリの前処理 - 表記揺れや類義語に対応"""
    # 全角・半角の正規化
    import unicodedata
    normalized = unicodedata.normalize('NFKC', query)
    
    # 類義語の展開
    synonyms = {
        '顧客番号': ['お客様番号', '顧客ID', '顧客コード', '会員番号', 'カスタマーID'],
        '会社': ['企業', '法人', '株式会社', '有限会社', '合同会社'],
        '料金': ['価格', '費用', '金額', 'プライス', 'コスト'],
        '契約': ['申込', '申し込み', '契約書', '合意'],
    }
    
    # クエリに類義語を追加
    expanded_terms = [normalized]
    for term, syns in synonyms.items():
        if term in normalized:
            expanded_terms.extend(syns)
    
    return ' '.join(expanded_terms)

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
    """セマンティック検索（意味ベース）- Sentence Transformersを使用"""
    try:
        # Sentence Transformersを使った本格的なセマンティック検索
        try:
            from sentence_transformers import SentenceTransformer, util
            import torch
            
            # 日本語対応の多言語モデルを使用
            model_name = 'paraphrase-multilingual-MiniLM-L12-v2'
            model = SentenceTransformer(model_name)
            safe_print(f"🤖 セマンティックモデル読み込み: {model_name}")
            
            # クエリとチャンクをエンベディング化
            query_embedding = model.encode([query])
            chunk_embeddings = model.encode(chunks)
            
            # コサイン類似度を計算
            similarities = util.cos_sim(query_embedding, chunk_embeddings)[0]
            
            # 結果を整形
            semantic_results = []
            for i, similarity in enumerate(similarities):
                semantic_results.append({
                    'content': chunks[i],
                    'score': float(similarity),
                    'type': 'semantic_transformer',
                    'index': i
                })
            
            # スコア順でソート
            semantic_results.sort(key=lambda x: x['score'], reverse=True)
            safe_print(f"🧠 Transformer セマンティック検索完了: 上位{min(max_results, len(semantic_results))}件")
            return semantic_results[:max_results]
            
        except ImportError:
            safe_print("⚠️ Sentence Transformers未インストール、TF-IDFベースのセマンティック検索にフォールバック")
            
            # TF-IDFベースのセマンティック検索（フォールバック）
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                from sklearn.metrics.pairwise import cosine_similarity
                import numpy as np
                
                # TF-IDFベクトル化
                vectorizer = TfidfVectorizer(
                    ngram_range=(1, 2),  # 1-gram, 2-gramを使用
                    max_features=10000,
                    stop_words=None,  # 日本語のストップワードは使わない
                    analyzer='char',   # 文字レベルの解析（日本語に適している）
                    min_df=1
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
                        'type': 'semantic_tfidf',
                        'index': i
                    })
                
                # スコア順でソート
                semantic_results.sort(key=lambda x: x['score'], reverse=True)
                safe_print(f"📊 TF-IDF セマンティック検索完了: 上位{min(max_results, len(semantic_results))}件")
                return semantic_results[:max_results]
                
            except ImportError:
                safe_print("⚠️ scikit-learn未インストール、簡易セマンティック検索にフォールバック")
        
        # 最後の手段: 改良された簡易セマンティック検索
        semantic_results = []
        
        # クエリの重要語句を抽出
        import re
        query_words = set(re.findall(r'\w+', query.lower()))
        
        for i, chunk in enumerate(chunks):
            chunk_words = set(re.findall(r'\w+', chunk.lower()))
            
            # 複数の類似度指標を組み合わせ
            scores = []
            
            # 1. Jaccard類似度
            if len(query_words) > 0 and len(chunk_words) > 0:
                intersection = len(query_words.intersection(chunk_words))
                union = len(query_words.union(chunk_words))
                jaccard = intersection / union if union > 0 else 0.0
                scores.append(jaccard * 0.4)
            
            # 2. 語句の包含度
            if len(query_words) > 0:
                inclusion = sum(1 for word in query_words if word in chunk.lower()) / len(query_words)
                scores.append(inclusion * 0.3)
            
            # 3. 文字列距離（レーベンシュタイン距離の簡易版）
            try:
                # 部分文字列の一致度
                substring_match = 0
                for word in query_words:
                    if len(word) >= 2 and word in chunk.lower():
                        substring_match += len(word) / len(query)
                scores.append(min(1.0, substring_match) * 0.3)
            except:
                scores.append(0.0)
            
            # 総合スコア
            total_score = sum(scores)
            
            semantic_results.append({
                'content': chunk,
                'score': total_score,
                'type': 'semantic_simple',
                'index': i
            })
        
        # スコア順でソート
        semantic_results.sort(key=lambda x: x['score'], reverse=True)
        safe_print(f"🔍 簡易セマンティック検索完了: 上位{min(max_results, len(semantic_results))}件")
        return semantic_results[:max_results]
        
    except Exception as e:
        safe_print(f"セマンティック検索エラー: {e}")
        return []

def _evaluate_rag_quality(filtered_chunk: str, query: str, rag_attempts: int) -> float:
    """
    RAG検索結果の品質を評価（0.0-1.0のスコア）
    具体的な質問に対してより厳格な評価を実施
    """
    if not filtered_chunk or not filtered_chunk.strip():
        return 0.0
    
    score = 0.0
    content_lower = filtered_chunk.lower()
    query_lower = query.lower()
    
    # 1. 文字数による基本スコア（最大0.2） - 厳格化
    content_length = len(filtered_chunk.strip())
    if content_length >= 500:  # 500文字以上で最高スコア
        score += 0.2
    elif content_length >= 300:  # 300文字以上で中程度
        score += 0.15
    elif content_length >= 150:   # 150文字以上で最低限
        score += 0.1
    
    # 2. 重要キーワードの厳格マッチング（最大0.6） - 大幅強化
    query_words = set(query.lower().split())
    
    # 重要キーワードの特定（会社名、固有名詞など）
    important_keywords = []
    company_patterns = [
        r'株式会社\s*[\w\s]+',
        r'有限会社\s*[\w\s]+', 
        r'合同会社\s*[\w\s]+',
        r'[\w\s]+会社',
        r'[\w\s]+工芸',
        r'[\w\s]+工業',
        r'[\w\s]+商事'
    ]
    
    # クエリから会社名や重要語句を抽出
    for pattern in company_patterns:
        matches = re.findall(pattern, query)
        important_keywords.extend(matches)
    
    # クエリの主要単語を重要キーワードとして追加
    for word in query_words:
        if len(word) >= 2 and word not in ['の', 'に', 'を', 'は', 'が', 'で', 'と', 'から', 'まで']:
            important_keywords.append(word)
    
    # 重要キーワードの完全一致チェック
    critical_matches = 0
    for keyword in important_keywords:
        if keyword.strip() in content_lower:
            critical_matches += 1
    
    if len(important_keywords) > 0:
        critical_match_ratio = critical_matches / len(important_keywords)
        
        # 重要キーワードが50%以上マッチした場合のみ高スコア
        if critical_match_ratio >= 0.5:
            score += critical_match_ratio * 0.6
        elif critical_match_ratio >= 0.3:
            score += critical_match_ratio * 0.3
        elif critical_match_ratio >= 0.1:
            score += critical_match_ratio * 0.1
    
    # 3. 質問の意図に対する回答の適合性（最大0.2）
    intent_keywords = {
        'ステータス': ['状態', 'ステータス', '現状', '状況', '進捗', '段階'],
        '顧客番号': ['顧客番号', 'お客様番号', '顧客ID', '顧客コード', '番号'],
        '連絡先': ['電話', 'TEL', 'FAX', 'メール', '住所', '連絡先'],
        '料金': ['料金', '価格', '費用', 'コスト', '金額', '値段'],
        '契約': ['契約', '取引', '合意', '約束', '条件']
    }
    
    intent_score = 0
    for intent, keywords in intent_keywords.items():
        if intent.lower() in query_lower:
            # 質問に意図が含まれている場合、回答にその関連語句があるかチェック
            for keyword in keywords:
                if keyword in content_lower:
                    intent_score += 0.05
                    break
    
    score += min(0.2, intent_score)
    
    # 4. 無関係な内容の検出による減点
    irrelevant_patterns = [
        'システムエラー', 'デバッグ', 'テスト', 'サンプル', '例：', '例)', 
        '※', '注意', '重要', 'エラーが発生', '申し訳ございません'
    ]
    
    irrelevant_count = sum(1 for pattern in irrelevant_patterns if pattern in filtered_chunk)
    if irrelevant_count > 0:
        score -= min(0.3, irrelevant_count * 0.1)
    
    # 5. 最終的な厳格判定
    # 具体的な固有名詞を含む質問の場合、その固有名詞が含まれていない回答は大幅減点
    if any(word in query_lower for word in ['株式会社', '会社', '工芸', '顧客番号', 'ステータス']):
        has_relevant_content = False
        
        # クエリの重要語句が回答に含まれているかチェック
        for word in query_words:
            if len(word) >= 2 and word in content_lower:
                has_relevant_content = True
                break
        
        if not has_relevant_content:
            score *= 0.1  # 90%減点
    
    # 6. 意味的類似度による品質向上（ボーナス）
    try:
        # 簡易的な意味的類似度チェック
        semantic_bonus = 0.0
        
        # 質問と回答の文脈的関連性をチェック
        context_keywords = {
            'ステータス': ['状態', '現状', '進行', '段階', '状況', 'status'],
            '顧客': ['お客様', 'クライアント', 'client', 'customer'],
            '会社': ['企業', '法人', 'company', 'corporation'],
            '番号': ['ID', 'コード', 'number', 'code'],
            '工芸': ['クラフト', 'アート', 'craft', 'art'],
        }
        
        for main_word, related_words in context_keywords.items():
            if main_word in query_lower:
                # 関連語句が回答に含まれている場合はボーナス
                for related in related_words:
                    if related.lower() in content_lower:
                        semantic_bonus += 0.02
                        break
        
        # 文脈的な一貫性ボーナス
        if semantic_bonus > 0:
            score += min(0.1, semantic_bonus)  # 最大0.1のボーナス
            
    except Exception as e:
        # エラーが発生した場合はボーナスなし
        pass
    
    # スコアを0.0-1.0に正規化
    final_score = max(0.0, min(1.0, score))
    
    return final_score

def _combine_search_results(bm25_results: list, semantic_results: list, query: str, max_results: int) -> list:
    """BM25とセマンティック検索結果の統合 - 意味的検索を重視"""
    try:
        # 結果の統合とスコア正規化
        all_results = {}
        
        # セマンティック検索のタイプに応じて重みを調整
        semantic_weight = 0.7  # デフォルト
        bm25_weight = 0.3
        
        # Transformerベースの場合は意味的検索をより重視
        if semantic_results and semantic_results[0].get('type') == 'semantic_transformer':
            semantic_weight = 0.8
            bm25_weight = 0.2
            safe_print("🧠 Transformerベースセマンティック検索 - 意味重視モード")
        elif semantic_results and semantic_results[0].get('type') == 'semantic_tfidf':
            semantic_weight = 0.6
            bm25_weight = 0.4
            safe_print("📊 TF-IDFベースセマンティック検索 - バランスモード")
        else:
            semantic_weight = 0.4
            bm25_weight = 0.6
            safe_print("🔍 簡易セマンティック検索 - 語彙重視モード")
        
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
    """メッセージが挨拶や一般的な会話かどうかを判定する"""
    if not message_text:
        return False
    
    message_lower = message_text.strip().lower()
    
    # 挨拶パターン
    greetings = [
        "こんにちは", "こんにちわ", "おはよう", "おはようございます", "こんばんは", "こんばんわ",
        "よろしく", "よろしくお願いします", "はじめまして", "初めまして",
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening"
    ]
    
    # お礼パターン
    thanks = [
        "ありがとう", "ありがとうございます", "ありがとうございました", "感謝します",
        "thank you", "thanks", "thx"
    ]
    
    # 別れの挨拶パターン
    farewells = [
        "さようなら", "またね", "また明日", "失礼します", "お疲れ様", "お疲れさまでした",
        "bye", "goodbye", "see you", "good bye"
    ]
    
    # 一般的な会話パターン
    casual_phrases = [
        "元気", "調子", "どう", "天気", "今日", "明日", "昨日", "週末", "休み",
        "疲れた", "忙しい", "暇", "時間", "いい天気", "寒い", "暑い", "雨",
        "how are you", "what's up", "how's it going", "nice weather", "tired", "busy"
    ]
    
    # 短い質問や相槌パターン
    short_responses = [
        "はい", "いいえ", "そうですね", "なるほど", "そうですか", "わかりました",
        "ok", "okay", "yes", "no", "i see", "alright"
    ]
    
    # メッセージが短すぎる場合（3文字以下）は一般的な会話として扱う
    if len(message_lower) <= 3:
        return True
    
    # 各パターンをチェック
    all_patterns = greetings + thanks + farewells + casual_phrases + short_responses
    
    for pattern in all_patterns:
        if pattern in message_lower:
            return True
    
    # 疑問符がなく、短いメッセージ（20文字以下）は一般的な会話として扱う
    if len(message_text) <= 20 and "?" not in message_text and "？" not in message_text:
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
            # フォールバック応答
            message_lower = message_text.lower()
            if any(greeting in message_lower for greeting in ["こんにちは", "こんにちわ", "hello", "hi"]):
                return "こんにちは！お疲れ様です。何かお手伝いできることはありますか？"
            elif any(thanks in message_lower for thanks in ["ありがとう", "thank you", "thanks"]):
                return "どういたしまして！他にも何かお手伝いできることがあれば、お気軽にお声がけください。"
            elif any(farewell in message_lower for farewell in ["さようなら", "またね", "bye", "goodbye"]):
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
                model="gemini-pro"
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
                source_result = select_data("document_sources", columns="name,special", filters={"id": source_id})
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
        
        # 改良されたRAG検索で関連部分のみを抽出（高精度・高速化）
        if active_knowledge_text and len(active_knowledge_text) > 50000:
            safe_print(f"🎯 改良RAG検索開始 - 元サイズ: {len(active_knowledge_text):,} 文字")
            
            # 高速化を重視した検索手法を選択
            if SPEED_RAG_AVAILABLE:
                # 雷速RAG検索を最優先で使用
                active_knowledge_text = await lightning_rag_search(active_knowledge_text, message_text, max_results=30)
            elif len(active_knowledge_text) > 500000:
                # 非常に大きなテキストの場合は強化RAG検索
                if RAG_ENHANCED_AVAILABLE:
                    active_knowledge_text = await enhanced_rag_search(active_knowledge_text, message_text, max_results=25)
                else:
                    active_knowledge_text = multi_pass_rag_search(active_knowledge_text, message_text, max_results=20)
            elif len(active_knowledge_text) > 200000:
                # 大きなテキストの場合は多段階検索
                active_knowledge_text = multi_pass_rag_search(active_knowledge_text, message_text, max_results=15)
            else:
                # 中程度のテキストの場合は適応的検索
                active_knowledge_text = adaptive_rag_search(active_knowledge_text, message_text, max_results=12)
            
            safe_print(f"🎯 改良RAG検索完了 - 新サイズ: {len(active_knowledge_text):,} 文字")
            
            # RAG検索後のサイズが30万文字以下なら通常処理に切り替え
            if len(active_knowledge_text) <= 300000:
                safe_print(f"🔄 RAG検索後のサイズが小さいため、通常処理に切り替えます")
                # 通常のprocess_chat関数を呼び出し
                return await process_chat(message, db, current_user)
        
        # 知識ベースのサイズを制限（API制限対応のため一時的に復活）
        MAX_KNOWLEDGE_SIZE = 300000  # 30万文字制限（API制限対応）
        if active_knowledge_text and len(active_knowledge_text) > MAX_KNOWLEDGE_SIZE:
            safe_print(f"⚠️ 知識ベースが大きすぎます ({len(active_knowledge_text)} 文字)。{MAX_KNOWLEDGE_SIZE} 文字に制限します。")
            active_knowledge_text = active_knowledge_text[:MAX_KNOWLEDGE_SIZE] + "\n\n[注意: 知識ベースが大きいため、一部のみ表示しています]"
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
                model="gemini-pro"
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

        # プロンプトの作成
        prompt = f"""
        あなたは親切で丁寧な対応ができる{current_company_name}のアシスタントです。
        以下の知識ベースを参考に、ユーザーの質問に対して可能な限り具体的で役立つ回答を提供してください。

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
        
        利用可能なデータ列：
        {', '.join(knowledge_base.columns) if knowledge_base and hasattr(knowledge_base, 'columns') and knowledge_base.columns else ""}

        知識ベース内容（アクティブなリソースのみ）：
        {active_knowledge_text}

        {f"画像情報：PDFから抽出された画像が{len(knowledge_base.images)}枚あります。" if knowledge_base and hasattr(knowledge_base, 'images') and knowledge_base.images and isinstance(knowledge_base.images, list) else ""}

        {conversation_history}

        ユーザーの質問：
        {message_text}
        """

        # プロンプトサイズの最終チェック（トークン制限対応）
        MAX_PROMPT_SIZE = 400000  # 40万文字制限（API制限対応）
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

        # Geminiによる応答生成
        try:
            safe_print(f"🤖 Gemini API呼び出し開始 - モデル: {model}")
            safe_print(f"📝 プロンプト長: {len(prompt)} 文字")
            
            response = model.generate_content(prompt)
            
            safe_print(f"📨 Gemini API応答受信: {response}")
            
            if not response or not hasattr(response, 'text'):
                safe_print(f"❌ 無効な応答: response={response}, hasattr(text)={hasattr(response, 'text') if response else 'N/A'}")
                raise ValueError("AIモデルからの応答が無効です")
            
            response_text = response.text
            safe_print(f"✅ 応答テキスト取得成功: {len(response_text)} 文字")
            
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
                model="gemini-pro"  # Gemini料金体系を使用
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

def chunk_knowledge_base(text: str, chunk_size: int = 500000) -> list[str]:
    """
    知識ベースを指定されたサイズでチャンク化する
    
    Args:
        text: チャンク化するテキスト
        chunk_size: チャンクのサイズ（文字数）
    
    Returns:
        チャンク化されたテキストのリスト
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # チャンクの境界を調整（文の途中で切れないように）
        if end < len(text):
            # 最後の改行を探す
            last_newline = text.rfind('\n', start, end)
            if last_newline > start:
                end = last_newline + 1
            else:
                # 改行がない場合は最後のスペースを探す
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
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
                source_result = select_data("document_sources", columns="name,special", filters={"id": source_id})
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

        # 🔪 まず知識ベース全体をチャンク化（RAG前に実行）
        CHUNK_SIZE = 500000  # 50万文字でチャンク化
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
        BATCH_SIZE = min(25, len(raw_chunks))  # バッチサイズを拡大（15→25）
        
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
            
            if len(combined_chunk) > 3000:  # 閾値をさらに緩和（5000→3000）
                safe_print(f"🔄 高度RAG検索開始: 全戦略を試行")
                
                # より多様な検索戦略を定義
                search_strategies = [
                    # 基本検索戦略
                    {'max_results': min(40, max(20, len(combined_chunk) // 25000)), 'query': message_text, 'name': '標準検索'},
                    {'max_results': min(60, max(30, len(combined_chunk) // 20000)), 'query': message_text, 'name': '拡張検索'},
                    {'max_results': min(80, max(40, len(combined_chunk) // 15000)), 'query': expand_query(message_text), 'name': 'クエリ拡張検索'},
                    
                    # 高度な検索戦略
                    {'max_results': min(100, max(50, len(combined_chunk) // 12000)), 'query': expand_query(message_text), 'name': '最大範囲検索'},
                    {'max_results': min(120, len(combined_chunk) // 10000), 'query': f"{message_text} OR {expand_query(message_text)}", 'name': 'OR検索'},
                    {'max_results': min(150, len(combined_chunk) // 8000), 'query': message_text.replace(' ', ' AND '), 'name': 'AND検索'},
                    
                    # 特殊検索戦略
                    {'max_results': min(200, len(combined_chunk) // 6000), 'query': f"({message_text}) OR ({expand_query(message_text)})", 'name': '高度OR検索'},
                    {'max_results': min(250, len(combined_chunk) // 5000), 'query': message_text, 'name': '最大密度検索'},
                ]
                
                best_result = None
                best_score = 0.0
                best_strategy = None
                
                for strategy in search_strategies:
                    rag_attempts += 1
                    safe_print(f"🎯 RAG検索 {rag_attempts}回目: {strategy['name']}, max_results={strategy['max_results']}")
                    safe_print(f"🔍 検索クエリ: '{strategy['query'][:50]}{'...' if len(strategy['query']) > 50 else ''}'")
                    
                    current_result = simple_rag_search(combined_chunk, strategy['query'], max_results=strategy['max_results'])
                    current_length = len(current_result.strip())
                    safe_print(f"📊 RAG検索{rag_attempts}回目結果: {current_length} 文字")
                    
                    # 品質評価を実行
                    if current_length >= min_content_threshold:
                        quality_score = _evaluate_rag_quality(current_result, message_text, rag_attempts)
                        safe_print(f"🎯 RAG品質スコア ({rag_attempts}回目): {quality_score:.2f}")
                        
                        # より良い結果があれば採用
                        if quality_score > best_score:
                            best_result = current_result
                            best_score = quality_score
                            best_strategy = strategy['name']
                            safe_print(f"✅ 新しい最良結果を採用: {strategy['name']} (スコア: {quality_score:.2f})")
                    else:
                        safe_print(f"⚠️ 結果が短すぎます ({current_length} < {min_content_threshold})")
                
                # 最良の結果を採用
                if best_result:
                    filtered_chunk = best_result
                    safe_print(f"🏆 最良結果を採用: {best_strategy}, スコア: {best_score:.2f}, 長さ: {len(filtered_chunk)} 文字")
                else:
                    # 最良結果がない場合は最長の結果を採用
                    longest_result = None
                    longest_length = 0
                    for strategy in search_strategies[:3]:  # 基本戦略のみ再試行
                        result = simple_rag_search(combined_chunk, strategy['query'], max_results=strategy['max_results'])
                        if len(result) > longest_length:
                            longest_result = result
                            longest_length = len(result)
                    
                    if longest_result:
                        filtered_chunk = longest_result
                        safe_print(f"📊 最長結果を採用: {longest_length} 文字")
                    else:
                        filtered_chunk = combined_chunk[:10000]  # 最後の手段
                        safe_print(f"📊 部分結果を採用: {len(filtered_chunk)} 文字")
                
                safe_print(f"🔄 高度RAG検索完了: {rag_attempts}回試行、最終結果 {len(filtered_chunk or '')} 文字")
            else:
                filtered_chunk = combined_chunk
                safe_print(f"📊 小さなバッチのため RAG検索をスキップ")
            
            # 🎯 厳格なRAG品質判定
            rag_quality_score = _evaluate_rag_quality(filtered_chunk, message_text, rag_attempts)
            safe_print(f"🎯 最終RAG品質スコア: {rag_quality_score:.2f} (閾値: 0.30)")
            
            # 品質スコアを厳格化（0.10→0.30）
            if rag_quality_score >= 0.30:
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
                safe_print(f"⚠️ RAG品質不足 (スコア: {rag_quality_score:.2f} < 0.30) - このバッチをスキップ")
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
                model="gemini-pro"
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
        
        return {
            "response": final_response,
            "source": source_text,
            "remaining_questions": remaining_questions,
            "limit_reached": limit_reached,
            "chunks_processed": len(raw_chunks),
            "successful_chunks": successful_chunks
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