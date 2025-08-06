"""
🔗 拡張チャット統合モジュール
enhanced_realtime_rag.pyと既存のチャット処理システムを統合

機能:
- 長い質問の自動検出
- 適切なRAGシステムの選択（基本 vs 拡張）
- 既存のchat_processing.pyとの互換性維持
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# 拡張RAGシステムのインポート
from .enhanced_realtime_rag import (
    process_question_enhanced_realtime,
    enhanced_realtime_rag_available,
    get_enhanced_realtime_rag_processor
)

# 基本RAGシステムのインポート
from .realtime_rag import (
    process_question_realtime,
    realtime_rag_available
)

logger = logging.getLogger(__name__)

class EnhancedChatIntegration:
    """拡張チャット統合システム"""
    
    def __init__(self):
        """初期化"""
        self.enhanced_available = enhanced_realtime_rag_available()
        self.basic_available = realtime_rag_available()
        
        # 複雑さ判定の閾値
        self.complexity_threshold = 0.6
        self.min_question_length = 50  # 最小質問長
        
        logger.info(f"✅ 拡張チャット統合システム初期化完了")
        logger.info(f"   拡張RAG利用可能: {self.enhanced_available}")
        logger.info(f"   基本RAG利用可能: {self.basic_available}")
    
    def should_use_enhanced_rag(self, question: str) -> bool:
        """
        拡張RAGを使用すべきかどうかを判定
        
        Args:
            question: ユーザーの質問
            
        Returns:
            bool: 拡張RAGを使用すべき場合True
        """
        if not self.enhanced_available:
            return False
        
        # 基本的な長さチェック
        if len(question) < self.min_question_length:
            return False
        
        # 複雑さの簡易判定
        complexity_indicators = [
            # 比較を求める質問
            ('と' in question and ('違い' in question or '比較' in question)),
            # 複数の情報を求める質問
            ('また' in question or 'さらに' in question or 'それから' in question),
            # 手順や段階的な説明を求める質問
            ('手順' in question or 'やり方' in question or 'ステップ' in question),
            # 複数の疑問符
            question.count('？') > 1 or question.count('?') > 1,
            # 長い質問（100文字以上）
            len(question) > 100,
            # 複数の要素を含む質問
            ('について' in question and question.count('について') > 1),
            # 詳細な説明を求める質問
            ('詳しく' in question or '具体的に' in question),
        ]
        
        complexity_score = sum(complexity_indicators) / len(complexity_indicators)
        
        logger.info(f"🔍 複雑さ判定: スコア={complexity_score:.2f}, 閾値={self.complexity_threshold}")
        logger.info(f"   判定指標: {[i for i, indicator in enumerate(complexity_indicators) if indicator]}")
        
        return complexity_score >= self.complexity_threshold
    
    async def process_chat_with_enhanced_rag(
        self,
        question,
        db,
        current_user,
        company_id: str = None,
        company_name: str = "お客様の会社",
        user_id: str = "anonymous"
    ) -> Dict[str, Any]:
        """
        拡張RAGを使用したチャット処理
        
        Args:
            question: ユーザーの質問（ChatMessageオブジェクトまたは文字列）
            db: データベース接続
            current_user: 現在のユーザー
            company_id: 会社ID
            company_name: 会社名
            user_id: ユーザーID
            
        Returns:
            Dict: 処理結果
        """
        # ChatMessageオブジェクトから文字列を取得
        if hasattr(question, 'text'):
            question_text = question.text
        else:
            question_text = str(question)
        
        logger.info(f"🚀 拡張RAGチャット処理開始: '{question_text[:100]}...'")
        start_time = datetime.now()
        
        try:
            # 拡張RAGを使用すべきかチェック
            use_enhanced = self.should_use_enhanced_rag(question_text)
            
            if use_enhanced:
                logger.info("🔄 拡張RAGシステムを使用")
                result = await process_question_enhanced_realtime(
                    question=question_text,
                    company_id=company_id,
                    company_name=company_name,
                    top_k=50
                )
                
                # 処理タイプを明確化
                if 'metadata' in result:
                    result['metadata']['integration_decision'] = 'enhanced_rag'
                    result['metadata']['complexity_decision'] = 'complex_question'
                else:
                    result['metadata'] = {
                        'integration_decision': 'enhanced_rag',
                        'complexity_decision': 'complex_question'
                    }
                
            else:
                logger.info("📝 基本RAGシステムを使用")
                if self.basic_available:
                    result = await process_question_realtime(
                        question=question_text,
                        company_id=company_id,
                        company_name=company_name,
                        top_k=50
                    )
                    
                    # 処理タイプを明確化
                    if 'metadata' not in result:
                        result['metadata'] = {}
                    result['metadata']['integration_decision'] = 'basic_rag'
                    result['metadata']['complexity_decision'] = 'simple_question'
                else:
                    # フォールバック応答
                    result = {
                        "answer": "申し訳ございませんが、現在システムが利用できません。しばらく時間をおいて再度お試しください。",
                        "timestamp": datetime.now().isoformat(),
                        "status": "error",
                        "metadata": {
                            "integration_decision": "fallback",
                            "complexity_decision": "system_unavailable"
                        }
                    }
            
            # 共通メタデータの追加
            processing_time = (datetime.now() - start_time).total_seconds()
            if 'metadata' not in result:
                result['metadata'] = {}
            
            result['metadata'].update({
                'user_id': user_id,
                'integration_processing_time': processing_time,
                'question_length': len(question_text),
                'enhanced_rag_available': self.enhanced_available,
                'basic_rag_available': self.basic_available
            })
            
            logger.info(f"✅ 拡張RAGチャット処理完了: {processing_time:.2f}秒")
            logger.info(f"   決定: {result['metadata']['integration_decision']}")
            logger.info(f"   複雑度: {result['metadata']['complexity_decision']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 拡張RAGチャット処理エラー: {e}")
            import traceback
            logger.error(f"詳細エラー: {traceback.format_exc()}")
            
            # エラー時のフォールバック
            processing_time = (datetime.now() - start_time).total_seconds()
            return {
                "answer": "申し訳ございませんが、処理中にエラーが発生しました。しばらく時間をおいて再度お試しください。",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "metadata": {
                    "integration_decision": "error_fallback",
                    "complexity_decision": "error",
                    "user_id": user_id,
                    "integration_processing_time": processing_time,
                    "question_length": len(question_text)
                }
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """システム状態を取得"""
        return {
            "enhanced_rag_available": self.enhanced_available,
            "basic_rag_available": self.basic_available,
            "complexity_threshold": self.complexity_threshold,
            "min_question_length": self.min_question_length,
            "integration_ready": self.enhanced_available or self.basic_available
        }


# グローバルインスタンス
_enhanced_chat_integration = None

def get_enhanced_chat_integration() -> Optional[EnhancedChatIntegration]:
    """拡張チャット統合システムのインスタンスを取得（シングルトンパターン）"""
    global _enhanced_chat_integration
    
    if _enhanced_chat_integration is None:
        try:
            _enhanced_chat_integration = EnhancedChatIntegration()
            logger.info("✅ 拡張チャット統合システム初期化完了")
        except Exception as e:
            logger.error(f"❌ 拡張チャット統合システム初期化エラー: {e}")
            return None
    
    return _enhanced_chat_integration

async def process_enhanced_chat_message(
    question: str,
    company_id: str = None,
    company_name: str = "お客様の会社",
    user_id: str = "anonymous"
) -> Dict[str, Any]:
    """
    拡張チャットメッセージ処理の外部呼び出し用関数
    
    Args:
        question: ユーザーの質問
        company_id: 会社ID
        company_name: 会社名
        user_id: ユーザーID
        
    Returns:
        Dict: 処理結果
    """
    integration = get_enhanced_chat_integration()
    if not integration:
        return {
            "answer": "システムの初期化に失敗しました。管理者にお問い合わせください。",
            "error": "EnhancedChatIntegration initialization failed",
            "timestamp": datetime.now().isoformat(),
            "status": "error"
        }
    
    return await integration.process_chat_with_enhanced_rag(
        question, company_id, company_name, user_id
    )

def enhanced_chat_integration_available() -> bool:
    """拡張チャット統合が利用可能かチェック"""
    integration = get_enhanced_chat_integration()
    if not integration:
        return False
    
    status = integration.get_system_status()
    return status.get('integration_ready', False)

# 使用例とテスト用の関数
async def test_enhanced_chat_integration():
    """拡張チャット統合のテスト"""
    test_questions = [
        # シンプルな質問（基本RAG使用予定）
        "パソコンの価格を教えてください。",
        
        # 複雑な質問（拡張RAG使用予定）
        "A社とB社のサービスの違いは何ですか？それぞれの特徴と料金体系を比較して教えてください。",
        "新しいシステムを導入する手順を教えてください。また、導入時の注意点や必要な準備についても詳しく説明してください。",
        "故障受付シートの名称と記入方法について教えてください。また、提出先や処理の流れも知りたいです。",
        
        # 中程度の複雑さ（境界ケース）
        "システムの使い方について詳しく教えてください。また、トラブル時の対処法も知りたいです。"
    ]
    
    integration = get_enhanced_chat_integration()
    if not integration:
        logger.error("❌ テスト実行不可: 統合システムの初期化に失敗")
        return
    
    logger.info("🧪 拡張チャット統合システムのテスト開始")
    logger.info(f"📊 システム状態: {integration.get_system_status()}")
    
    for i, question in enumerate(test_questions, 1):
        logger.info(f"\n{'='*100}")
        logger.info(f"🧪 テスト {i}/{len(test_questions)}: {question}")
        logger.info(f"{'='*100}")
        
        try:
            # 複雑さ判定のテスト
            use_enhanced = integration.should_use_enhanced_rag(question)
            logger.info(f"🔍 複雑さ判定結果: {'拡張RAG' if use_enhanced else '基本RAG'}")
            
            # 実際の処理
            result = await integration.process_chat_with_enhanced_rag(question)
            
            logger.info(f"✅ テスト {i} 完了:")
            logger.info(f"   統合決定: {result.get('metadata', {}).get('integration_decision', 'unknown')}")
            logger.info(f"   複雑度判定: {result.get('metadata', {}).get('complexity_decision', 'unknown')}")
            logger.info(f"   処理時間: {result.get('metadata', {}).get('integration_processing_time', 0):.2f}秒")
            logger.info(f"   回答長: {len(result.get('answer', ''))}文字")
            logger.info(f"   回答プレビュー: {result.get('answer', '')[:200]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト {i} 失敗: {e}")
    
    logger.info("\n🎉 拡張チャット統合システムのテスト完了")

if __name__ == "__main__":
    import asyncio
    # テスト実行
    asyncio.run(test_enhanced_chat_integration())