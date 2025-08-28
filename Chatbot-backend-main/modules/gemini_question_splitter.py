"""
Geminiを使った質問分割機能
"""

import logging
from typing import List, Dict
from .multi_gemini_client import get_multi_gemini_client, multi_gemini_available

logger = logging.getLogger(__name__)

async def request_question_split(question: str) -> List[str]:
    """Geminiに質問分割を依頼"""
    try:
        split_prompt = f"""
以下の質問に複数のタスクや要求が含まれている場合は、それぞれを独立した質問に分割してください。
分割が不要な場合は、元の質問をそのまま返してください。

質問: {question}

回答形式:
- 複数のタスクがある場合: 各質問を改行で区切って出力
- 単一のタスクの場合: 元の質問をそのまま出力

例:
入力: "WPD4100388について教えて。また、価格も知りたいです。"
出力:
WPD4100388について教えてください。
WPD4100388の価格について教えてください。
"""
        
        client = get_multi_gemini_client()
        if client and multi_gemini_available():
            logger.info("🤖 Geminiに質問分割を依頼中...")
            response_data = await client.generate_content(split_prompt, {"temperature": 0.1})
            
            # レスポンスからテキストを抽出
            response = None
            if isinstance(response_data, dict):
                if "candidates" in response_data and response_data["candidates"]:
                    candidate = response_data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if parts and "text" in parts[0]:
                            response = parts[0]["text"]
            elif isinstance(response_data, str):
                response = response_data
            
            if response and response.strip():
                # 改行で分割
                questions = [q.strip() for q in response.strip().split('\n') if q.strip()]
                
                # 元の質問と大差ない場合は分割しない
                if len(questions) <= 1 or questions[0] == question:
                    return [question]
                
                logger.info(f"✂️ Gemini分割結果: {len(questions)}個の質問")
                for i, q in enumerate(questions):
                    logger.info(f"   {i+1}. {q}")
                
                return questions
            
        return [question]
        
    except Exception as e:
        logger.error(f"❌ 質問分割エラー: {e}")
        return [question]

async def merge_multiple_responses(responses: List[Dict], original_question: str) -> Dict:
    """複数の回答をマージ"""
    try:
        # 各回答をまとめる
        all_answers = []
        all_sources = []
        all_chunks = []
        
        for i, response in enumerate(responses):
            answer = response.get("answer", "")
            if answer:
                all_answers.append(f"【回答{i+1}】\n{answer}")
            
            sources = response.get("sources", [])
            all_sources.extend(sources)
            
            chunks = response.get("used_chunks", [])
            all_chunks.extend(chunks)
        
        # 重複ソースを除去
        unique_sources = []
        seen_sources = set()
        for source in all_sources:
            source_name = source.get("source", "")
            if source_name not in seen_sources:
                unique_sources.append(source)
                seen_sources.add(source_name)
        
        # 統合回答を作成
        merged_answer = "\n\n".join(all_answers)
        
        return {
            "answer": merged_answer,
            "sources": unique_sources,
            "used_chunks": all_chunks,
            "metadata": {
                "original_question": original_question,
                "split_count": len(responses),
                "total_sources": len(unique_sources),
                "processing_type": "multi_task_split"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 回答マージエラー: {e}")
        # フォールバック: 最初の回答を返す
        return responses[0] if responses else {
            "answer": "回答の統合に失敗しました。",
            "sources": [],
            "error": True
        }
