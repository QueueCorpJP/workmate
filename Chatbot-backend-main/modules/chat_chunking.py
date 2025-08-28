"""
チャンキング機能とチャンク化チャット処理
大きなテキストのチャンク化と分割処理を管理します
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from .chat_config import safe_print, HTTPException, model, get_db_cursor
from .chat_utils import chunk_knowledge_base
from .chat_rag import adaptive_rag_search, format_search_results
from .chat_processing import generate_response_with_context

async def process_chunked_chat(
    message: str,
    user_id: str = "anonymous",
    chunk_size: int = 700,  # 🎯 600-800文字範囲の中央値（ユーザー要求準拠）
    max_chunks: int = 140  # チャンクサイズに応じた個数
) -> Dict[str, Any]:
    """
    チャンク化されたチャット処理
    
    Args:
        message: ユーザーメッセージ
        user_id: ユーザーID
        chunk_size: チャンクサイズ
        max_chunks: 最大チャンク数
        
    Returns:
        処理結果
    """
    try:
        safe_print(f"Processing chunked chat for user {user_id}")
        
        # メッセージが長い場合はチャンク化
        if len(message) > chunk_size:
            message_chunks = chunk_knowledge_base(message, chunk_size)
            safe_print(f"Message chunked into {len(message_chunks)} parts")
            
            # 各チャンクを処理
            chunk_results = []
            for i, chunk in enumerate(message_chunks[:max_chunks]):
                safe_print(f"Processing chunk {i+1}/{len(message_chunks)}")
                
                # RAG検索を実行（細粒度化に合わせて件数増加）
                search_results = await adaptive_rag_search(chunk, limit=20)
                
                # 結果を保存
                chunk_results.append({
                    'chunk_index': i,
                    'chunk_text': chunk,
                    'search_results': search_results,
                    'result_count': len(search_results)
                })
            
            # 全チャンクの結果をマージ
            merged_results = merge_chunk_results(chunk_results)
            
            # 統合された応答を生成
            response = await generate_chunked_response(message, merged_results)
            
            return {
                'response': response,
                'processing_type': 'chunked',
                'chunk_count': len(message_chunks),
                'processed_chunks': len(chunk_results),
                'search_results': merged_results,
                'chunk_details': chunk_results
            }
        
        else:
            # 通常の処理
            from .chat_processing import process_chat_message
            return await process_chat_message(message, user_id)
            
    except Exception as e:
        safe_print(f"Error in chunked chat processing: {e}")
        raise HTTPException(status_code=500, detail=f"チャンク化処理中にエラーが発生しました: {str(e)}")

def merge_chunk_results(chunk_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    チャンク結果をマージして重複を除去
    
    Args:
        chunk_results: チャンク処理結果のリスト
        
    Returns:
        マージされた検索結果
    """
    merged_results = []
    seen_ids = set()
    
    # 各チャンクの結果を統合
    for chunk_result in chunk_results:
        search_results = chunk_result.get('search_results', [])
        
        for result in search_results:
            result_id = result.get('id')
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                # チャンク情報を追加
                result['source_chunk'] = chunk_result['chunk_index']
                merged_results.append(result)
    
    # スコア順でソート
    merged_results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    safe_print(f"Merged {len(merged_results)} unique results from chunks")
    return merged_results

async def generate_chunked_response(
    original_message: str, 
    merged_results: List[Dict[str, Any]]
) -> str:
    """
    チャンク化された結果から統合応答を生成
    
    Args:
        original_message: 元のメッセージ
        merged_results: マージされた検索結果
        
    Returns:
        生成された応答
    """
    try:
        if not model:
            raise Exception("Gemini model is not available")
        
        # 検索結果をフォーマット（🎯 5000文字対応最適化）
        formatted_results = format_search_results(merged_results, max_length=15000)
        
        # チャンク化処理用のプロンプト
        prompt = f"""
以下は長いメッセージを分割して検索した結果です。
全体的な文脈を考慮して、包括的で一貫性のある回答を日本語で提供してください。

【元のメッセージ】
{original_message}

【検索結果（複数の参考資料から統合）】
{formatted_results}

【回答の指針】
1. 元のメッセージ全体の意図を理解する
2. 検索結果から関連する情報を抽出・統合する
3. 論理的で一貫性のある回答を構成する
4. 必要に応じて、情報の出典や参考URLを示す
5. 情報が不足している部分は明記する
6. 技術的な内部構造情報（分割番号、データベースIDなど）は出力しない

【回答】"""
        
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip()
        else:
            raise Exception("No response generated from model")
            
    except Exception as e:
        safe_print(f"Error generating chunked response: {e}")
        return "申し訳ございませんが、長いメッセージの処理中にエラーが発生しました。メッセージを短く分けて再度お試しください。"

async def process_knowledge_base_chunking(
    text: str,
    chunk_size: int = 700,  # 🎯 600-800文字範囲の中央値（ユーザー要求準拠）
    overlap_ratio: float = 0.1  # 🎯 10%オーバーラップ（サイズ制御重視）
) -> List[Dict[str, Any]]:
    """
    知識ベースのチャンク化処理
    
    Args:
        text: チャンク化するテキスト
        chunk_size: チャンクサイズ
        overlap_ratio: オーバーラップ比率
        
    Returns:
        チャンク化された結果
    """
    try:
        safe_print(f"Chunking knowledge base text of length {len(text)}")
        
        # テキストをチャンク化
        chunks = chunk_knowledge_base(text, chunk_size)
        
        # 各チャンクの詳細情報を作成
        chunk_details = []
        for i, chunk in enumerate(chunks):
            chunk_info = {
                'index': i,
                'text': chunk,
                'length': len(chunk),
                'word_count': len(chunk.split()),
                'start_position': text.find(chunk) if chunk in text else -1
            }
            chunk_details.append(chunk_info)
        
        safe_print(f"Created {len(chunk_details)} chunks")
        return chunk_details
        
    except Exception as e:
        safe_print(f"Error in knowledge base chunking: {e}")
        return []

async def store_chunked_knowledge(
    chunks: List[Dict[str, Any]], 
    source_id: str,
    metadata: Dict[str, Any] = None
) -> bool:
    """
    チャンク化された知識をデータベースに保存
    
    Args:
        chunks: チャンク化されたデータ
        source_id: ソースID
        metadata: メタデータ
        
    Returns:
        成功した場合True
    """
    try:
        cursor = get_db_cursor()
        if not cursor:
            safe_print("Database cursor not available")
            return False
        
        # チャンクを順次保存
        for chunk in chunks:
            insert_query = """
            INSERT INTO knowledge_chunks (source_id, chunk_index, content, length, word_count, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            chunk_metadata = {
                'start_position': chunk.get('start_position', -1),
                'original_metadata': metadata or {}
            }
            
            cursor.execute(insert_query, (
                source_id,
                chunk['index'],
                chunk['text'],
                chunk['length'],
                chunk['word_count'],
                str(chunk_metadata)
            ))
        
        cursor.connection.commit()
        safe_print(f"Stored {len(chunks)} chunks for source {source_id}")
        return True
        
    except Exception as e:
        safe_print(f"Error storing chunked knowledge: {e}")
        return False

async def retrieve_chunked_knowledge(
    source_id: str,
    chunk_indices: List[int] = None
) -> List[Dict[str, Any]]:
    """
    チャンク化された知識を取得
    
    Args:
        source_id: ソースID
        chunk_indices: 取得するチャンクのインデックス（Noneの場合は全て）
        
    Returns:
        取得されたチャンク
    """
    try:
        cursor = get_db_cursor()
        if not cursor:
            safe_print("Database cursor not available")
            return []
        
        if chunk_indices:
            # 特定のチャンクを取得
            placeholders = ','.join(['%s'] * len(chunk_indices))
            query = f"""
            SELECT chunk_index, content, length, word_count, metadata
            FROM knowledge_chunks
            WHERE source_id = %s AND chunk_index IN ({placeholders})
            ORDER BY chunk_index
            """
            cursor.execute(query, [source_id] + chunk_indices)
        else:
            # 全チャンクを取得
            query = """
            SELECT chunk_index, content, length, word_count, metadata
            FROM knowledge_chunks
            WHERE source_id = %s
            ORDER BY chunk_index
            """
            cursor.execute(query, (source_id,))
        
        rows = cursor.fetchall()
        
        chunks = []
        for row in rows:
            chunk = {
                'index': row[0],
                'text': row[1],
                'length': row[2],
                'word_count': row[3],
                'metadata': row[4]
            }
            chunks.append(chunk)
        
        safe_print(f"Retrieved {len(chunks)} chunks for source {source_id}")
        return chunks
        
    except Exception as e:
        safe_print(f"Error retrieving chunked knowledge: {e}")
        return []

def calculate_optimal_chunk_size(text: str, target_chunks: int = 5) -> int:
    """
    最適なチャンクサイズを計算（600-800文字範囲厳守）
    
    Args:
        text: 対象テキスト
        target_chunks: 目標チャンク数
        
    Returns:
        最適なチャンクサイズ（600-800文字範囲）
    """
    text_length = len(text)
    
    if text_length <= 600:  # 🎯 最小サイズ以下の場合
        return text_length
    
    # 目標チャンク数に基づいて計算
    optimal_size = text_length // target_chunks
    
    # 🎯 600-800文字の範囲に制限
    min_size = 600
    max_size = 800
    
    optimal_size = max(min_size, min(max_size, optimal_size))
    
    safe_print(f"Calculated optimal chunk size: {optimal_size} for text length {text_length} (range: 600-800)")
    return optimal_size

async def analyze_chunk_quality(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    チャンクの品質を分析
    
    Args:
        chunks: 分析するチャンク
        
    Returns:
        品質分析結果
    """
    if not chunks:
        return {'error': 'No chunks to analyze'}
    
    # 基本統計
    lengths = [chunk['length'] for chunk in chunks]
    word_counts = [chunk['word_count'] for chunk in chunks]
    
    analysis = {
        'chunk_count': len(chunks),
        'total_length': sum(lengths),
        'average_length': sum(lengths) / len(lengths),
        'min_length': min(lengths),
        'max_length': max(lengths),
        'average_words': sum(word_counts) / len(word_counts),
        'length_variance': calculate_variance(lengths),
        'quality_score': 0.0
    }
    
    # 品質スコア計算（0-1の範囲）
    # 長さの一貫性、適切なサイズ範囲、オーバーラップ品質を考慮
    length_consistency = 1.0 - (analysis['length_variance'] / analysis['average_length'])
    size_appropriateness = 1.0 if 600 <= analysis['average_length'] <= 800 else 0.5  # 🎯 600-800文字範囲に調整
    
    analysis['quality_score'] = (length_consistency + size_appropriateness) / 2
    
    safe_print(f"Chunk quality analysis: score={analysis['quality_score']:.3f}")
    return analysis

def calculate_variance(values: List[float]) -> float:
    """
    分散を計算
    
    Args:
        values: 値のリスト
        
    Returns:
        分散
    """
    if not values:
        return 0.0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance