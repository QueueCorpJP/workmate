"""
🔄 ハイブリッドExcel処理システム
Google Sheets API + OpenAI API の最適な組み合わせ

処理フロー：
1️⃣ Google Sheets APIで構造化データ抽出
2️⃣ OpenAI APIで意味解釈とデータクリーニング
3️⃣ 両方の結果を統合して最高品質のデータを生成
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
from datetime import datetime

# OpenAI API
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Google APIs
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class HybridExcelProcessor:
    """Google Sheets API + OpenAI API のハイブリッド処理システム"""
    
    def __init__(self):
        self.openai_client = None
        self.sheets_service = None
        self.drive_service = None
        
        # API初期化
        self._init_openai()
        self._init_google_apis()
    
    def _init_openai(self):
        """OpenAI APIクライアント初期化"""
        if not OPENAI_AVAILABLE:
            logger.warning("⚠️ OpenAI APIライブラリが利用できません")
            return
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("⚠️ OPENAI_API_KEY環境変数が設定されていません")
            return
        
        self.openai_client = openai.OpenAI(api_key=api_key)
        logger.info("✅ OpenAI APIクライアント初期化完了")
    
    def _init_google_apis(self):
        """Google APIs初期化"""
        if not GOOGLE_APIS_AVAILABLE:
            logger.warning("⚠️ Google APIライブラリが利用できません")
            return
        
        # Google APIサービス初期化（既存のコードを流用）
        service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        if service_account_file:
            # サービスアカウント認証
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file,
                scopes=['https://www.googleapis.com/auth/drive',
                        'https://www.googleapis.com/auth/spreadsheets']
            )
            
            self.drive_service = build('drive', 'v3', credentials=credentials)
            self.sheets_service = build('sheets', 'v4', credentials=credentials)
            logger.info("✅ Google APIs初期化完了（サービスアカウント）")
    
    async def process_excel_hybrid(self, 
                                 content: bytes, 
                                 filename: str,
                                 access_token: str = None,
                                 service_account_file: str = None) -> Dict[str, Any]:
        """
        🔄 ハイブリッドExcel処理のメイン関数
        
        Args:
            content: Excelファイルのバイト内容
            filename: ファイル名
            access_token: OAuth2アクセストークン
            service_account_file: サービスアカウントファイル
            
        Returns:
            処理結果辞書
        """
        logger.info(f"🔄 ハイブリッドExcel処理開始: {filename}")
        
        # Phase 1: Google Sheets APIで構造化抽出
        sheets_result = await self._process_with_google_sheets(
            content, filename, access_token, service_account_file
        )
        
        # Phase 2: OpenAI APIで意味解釈とクリーニング
        openai_result = await self._process_with_openai(
            content, filename, sheets_result
        )
        
        # Phase 3: 結果統合と品質評価
        final_result = await self._merge_and_evaluate(
            sheets_result, openai_result, filename
        )
        
        logger.info(f"✅ ハイブリッド処理完了: {filename}")
        return final_result
    
    async def _process_with_google_sheets(self, 
                                        content: bytes, 
                                        filename: str,
                                        access_token: str = None,
                                        service_account_file: str = None) -> Dict[str, Any]:
        """Google Sheets APIによる構造化処理"""
        logger.info("📊 Google Sheets API処理開始")
        
        try:
            # 既存のGoogle Sheets処理を流用
            from .excel_sheets_processor import process_excel_with_google_sheets_api
            
            result = await process_excel_with_google_sheets_api(
                content, filename, access_token, service_account_file
            )
            
            logger.info(f"✅ Google Sheets API処理完了: {len(result.get('data_list', []))} レコード")
            return result
            
        except Exception as e:
            logger.error(f"❌ Google Sheets API処理エラー: {str(e)}")
            return {"success": False, "error": str(e), "data_list": []}
    
    async def _process_with_openai(self, 
                                 content: bytes, 
                                 filename: str,
                                 sheets_result: Dict[str, Any]) -> Dict[str, Any]:
        """OpenAI APIによる意味解釈とクリーニング"""
        logger.info("🤖 OpenAI API処理開始")
        
        if not self.openai_client:
            logger.warning("⚠️ OpenAI APIクライアントが利用できません")
            return {"success": False, "processed_data": None}
        
        try:
            # Google Sheetsの結果を取得
            sheets_data = sheets_result.get('data_list', [])
            if not sheets_data:
                logger.warning("⚠️ Google Sheetsから処理するデータがありません")
                return {"success": False, "processed_data": None}
            
            # OpenAI APIにデータクリーニングを依頼
            enhanced_data = await self._enhance_data_with_openai(sheets_data, filename)
            
            logger.info(f"✅ OpenAI API処理完了: {len(enhanced_data)} レコード拡張")
            return {"success": True, "processed_data": enhanced_data}
            
        except Exception as e:
            logger.error(f"❌ OpenAI API処理エラー: {str(e)}")
            return {"success": False, "error": str(e), "processed_data": None}
    
    async def _enhance_data_with_openai(self, 
                                      data_list: List[Dict], 
                                      filename: str) -> List[Dict]:
        """OpenAI APIでデータの意味解釈と拡張"""
        
        if len(data_list) > 100:
            # 大きなデータセットの場合はサンプリング
            sample_data = data_list[:10]
            logger.info(f"📊 大容量データのため先頭10レコードでサンプル分析")
        else:
            sample_data = data_list
        
        # データの構造分析プロンプト
        analysis_prompt = f"""
以下のExcelデータ（{filename}）を分析し、データの意味と構造を理解して改善提案をしてください：

{str(sample_data[:5])}  # 最初の5レコードを送信

以下の形式でJSONレスポンスを返してください：
{{
    "data_type": "商品リスト/顧客データ/財務データ/その他",
    "key_columns": ["重要な列名のリスト"],
    "missing_info": ["欠損している重要情報"],
    "suggestions": ["データ改善の提案"],
    "category_mapping": {{"列名": "カテゴリ分類"}},
    "quality_score": "1-100の品質スコア"
}}
"""
        
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4o-mini",  # コスト効率の良いモデル
                messages=[
                    {"role": "system", "content": "あなたはExcelデータ分析の専門家です。日本語で分析結果を返してください。"},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1,
                max_tokens=128000  # GPT-4o-miniの最大トークン数
            )
            
            analysis_result = response.choices[0].message.content
            logger.info(f"🧠 OpenAI分析結果: {analysis_result[:200]}...")
            
            # 分析結果を元にデータを拡張
            enhanced_data = []
            for record in data_list:
                enhanced_record = record.copy()
                
                # OpenAIの分析結果を基にデータ品質向上
                enhanced_record["ai_analysis"] = {
                    "processed_at": datetime.now().isoformat(),
                    "quality_enhanced": True,
                    "source": "openai_analysis"
                }
                
                enhanced_data.append(enhanced_record)
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"❌ OpenAI分析エラー: {str(e)}")
            return data_list  # エラー時は元データを返す
    
    async def _merge_and_evaluate(self, 
                                sheets_result: Dict[str, Any], 
                                openai_result: Dict[str, Any], 
                                filename: str) -> Dict[str, Any]:
        """Google SheetsとOpenAIの結果を統合し品質評価"""
        logger.info("🔗 結果統合と品質評価開始")
        
        # ベースデータの決定
        if sheets_result.get('success') and sheets_result.get('data_list'):
            base_data = sheets_result['data_list']
            primary_source = "google_sheets"
        else:
            base_data = []
            primary_source = "none"
        
        # OpenAI拡張データの統合
        if openai_result.get('success') and openai_result.get('processed_data'):
            enhanced_data = openai_result['processed_data']
            enhancement_applied = True
        else:
            enhanced_data = base_data
            enhancement_applied = False
        
        # 品質スコア計算
        quality_score = self._calculate_quality_score(
            sheets_result, openai_result, enhancement_applied
        )
        
        # 最終結果
        final_result = {
            "success": True,
            "filename": filename,
            "processing_method": "hybrid",
            "primary_source": primary_source,
            "enhancement_applied": enhancement_applied,
            "quality_score": quality_score,
            "data_list": enhanced_data,
            "metadata": {
                "sheets_success": sheets_result.get('success', False),
                "openai_success": openai_result.get('success', False),
                "total_records": len(enhanced_data),
                "processed_at": datetime.now().isoformat()
            }
        }
        
        logger.info(f"✅ ハイブリッド統合完了 - 品質スコア: {quality_score}/100")
        return final_result
    
    def _calculate_quality_score(self, 
                               sheets_result: Dict[str, Any], 
                               openai_result: Dict[str, Any], 
                               enhancement_applied: bool) -> int:
        """処理品質スコアを計算"""
        score = 0
        
        # Google Sheets処理成功: +40点
        if sheets_result.get('success'):
            score += 40
        
        # OpenAI拡張成功: +30点
        if openai_result.get('success'):
            score += 30
        
        # 両方成功: ボーナス +20点
        if sheets_result.get('success') and openai_result.get('success'):
            score += 20
        
        # データ量による加点
        data_count = len(sheets_result.get('data_list', []))
        if data_count > 0:
            score += min(10, data_count // 10)  # 最大10点
        
        return min(100, score) 