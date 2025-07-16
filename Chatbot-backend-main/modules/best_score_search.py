"""
Best Score Search System
ファジー、エンベディング、完全一致検索を並列実行して一番スコアが高いものを採用

s.mdの「複数スコアのrangeが揃っていないとバイアスが出る」を解決し、
各検索手法の最高スコア結果から最良のものを選択する
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from supabase_adapter import execute_query, select_data
from .chat_config import safe_print
from .vector_search import get_vector_search_instance
from .unified_search_system import SearchResult, SearchType, ScoreNormalizer

logger = logging.getLogger(__name__)

class BestScoreSearchSystem:
    """最高スコア選択型検索システム"""
    
    def __init__(self):
        self.vector_search = get_vector_search_instance()
        self.score_normalizer = ScoreNormalizer()
    
    async def search_best_score(self, 
                               query: str, 
                               company_id: str = None,
                               limit: int = 10) -> List[Dict[str, Any]]:
        """
        並列検索して最高スコアの結果を採用
        
        Args:
            query: 検索クエリ
            company_id: 会社ID
            limit: 結果数制限
        """
        start_time = time.time()
        
        try:
            safe_print(f"🚀 並列検索開始: {query}")
            
            # 3つの検索手法を並列実行
            search_tasks = [
                self._exact_match_search(query, company_id, limit * 2),  # より多く取得
                self._fuzzy_search(query, company_id, limit * 2),
                self._vector_search(query, company_id, limit * 2)
            ]
            
            results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # 各検索手法の結果を処理
            search_results = {}
            search_names = ["完全一致", "Fuzzy", "ベクトル"]
            
            print(f"\n❗❗❗ 並列検索結果処理開始 ❗❗❗")
            
            for i, (results, name) in enumerate(zip(results_list, search_names)):
                print(f"\n❗ === {name}検索結果処理 ===")
                print(f"❗ 結果タイプ: {type(results)}")
                
                if isinstance(results, Exception):
                    print(f"❗❗❗ {name}検索で例外発生: {results} ❗❗❗")
                    safe_print(f"❌ {name}検索エラー: {results}")
                    search_results[name] = []
                elif isinstance(results, list):
                    print(f"❗ {name}検索成功: {len(results)}件取得")
                    if results:
                        print(f"❗ {name}検索サンプル:")
                        for j, item in enumerate(results[:2]):
                            if hasattr(item, 'to_dict'):
                                print(f"❗   [{j+1}] SearchResult: score={item.score}, type={item.search_type}")
                            else:
                                print(f"❗   [{j+1}] 不明なオブジェクト: {type(item)}")
                    search_results[name] = results
                    safe_print(f"✅ {name}検索: {len(results)}件取得")
                else:
                    print(f"❗❗❗ {name}検索で予期しない結果タイプ: {type(results)} ❗❗❗")
                    print(f"❗ 結果内容: {results}")
                    search_results[name] = []
            
            print(f"\n❗ 全検索手法の結果集計:")
            total_results = 0
            for name, results in search_results.items():
                count = len(results) if results else 0
                total_results += count
                print(f"❗   {name}: {count}件")
            print(f"❗ 総結果数: {total_results}件")
            
            if total_results == 0:
                print(f"❗❗❗ 重大な問題: 全ての検索手法で0件の結果 ❗❗❗")
                print(f"❗ 考えられる原因:")
                print(f"❗   1. データベースにデータが存在しない")
                print(f"❗   2. 会社IDフィルタが厳しすぎる")
                print(f"❗   3. システム設定に問題がある")
                print(f"❗   4. エンベディング生成に失敗している")
                return []
            
            # スコア正規化とベストスコア選択
            best_results = await self._select_best_scores(search_results, company_id, limit)
            
            execution_time = int((time.time() - start_time) * 1000)
            safe_print(f"🎯 最高スコア検索完了: {len(best_results)}件を{execution_time}msで取得")
            
            # 結果を詳細表示
            self._display_search_comparison(search_results, best_results, query)
            
            return [result.to_dict() for result in best_results]
            
        except Exception as e:
            logger.error(f"最高スコア検索エラー: {e}")
            return []
    
    async def _exact_match_search(self, query: str, company_id: str, limit: int) -> List[SearchResult]:
        """
        改良された完全一致検索（キーワードベース）
        """
        print(f"❗❗❗ 完全一致検索開始 ❗❗❗")
        print(f"❗ クエリ: '{query}'")
        print(f"❗ 会社ID: '{company_id}'")
        print(f"❗ 制限数: {limit}")
        
        try:
            # 1. データベーステーブル存在確認
            print(f"❗ 1. データベーステーブル存在確認")
            print(f"❗ Supabase基本操作でデータ確認開始")
            
            # 全体データ確認
            sample_result = select_data("chunks", columns="*", limit=1)
            print(f"❗ 全体データ確認結果: {sample_result}")
            print(f"❗ chunksテーブル全体: データ存在確認")
            
            # 会社IDのサンプル確認
            company_sample = select_data("chunks", columns="company_id,id", limit=5)
            print(f"❗ データサンプルの会社ID: {[item['company_id'] for item in company_sample.data]}")
            print(f"❗ サンプルデータ: {company_sample.data[:2]}")
            
            # 指定会社IDでのデータ確認
            company_filter_result = select_data("chunks", columns="*", filters={"company_id": company_id}, limit=1)
            print(f"❗ 会社IDフィルタ結果: {company_filter_result}")
            
            if not company_filter_result.data:
                print(f"❗❗❗ 重要発見: 会社ID「{company_id}」に該当するデータが0件！ ❗❗❗")
                print(f"❗ chunksテーブルにはデータが存在するが、この会社IDではデータなし")
                print(f"❗ 会社IDフィルタを外して検索継続...")
                use_company_filter = False
            else:
                use_company_filter = True
            
            # 2. メイン検索実行
            print(f"❗ 2. Supabase基本操作でメイン検索実行")
            
            if use_company_filter:
                filters = {"company_id": company_id}
                print(f"❗ 検索フィルタ: {filters}")
                
                result = select_data("chunks", columns="*", filters=filters, limit=min(limit * 10, 300))
            else:
                print(f"❗ 会社IDフィルタなしで検索実行")
                result = select_data("chunks", columns="*", limit=min(limit * 10, 300))
            
            print(f"❗ Supabase検索結果タイプ: {type(result)}")
            print(f"❗ Supabase検索結果データ数: {len(result.data) if result.data else 0}")
            
            if not result.data:
                print(f"❗❗❗ エラー原因特定: データベースから0件取得 ❗❗❗")
                return []
            
            # 3. 改良されたキーワードベース検索
            print(f"❗ 3. Supabase結果データ処理とキーワードベース検索")
            print(f"❗ Supabaseから取得: {len(result.data)}件")
            
            # キーワード抽出とフィルタリング
            processed_results = self._improved_keyword_search(query, result.data)
            print(f"❗ 改良されたキーワード検索結果: {len(processed_results)}件")
            
            if not processed_results:
                print(f"❗❗❗ エラー原因特定: キーワードマッチング後0件です ❗❗❗")
                print(f"❗ 原因: クエリ「{query}」から抽出されたキーワードがどのコンテンツにもマッチしない")
                return []
            
            # 4. SearchResultオブジェクトに変換
            search_results = []
            for item in processed_results[:limit]:
                search_result = SearchResult(
                    id=item["id"],
                    content=item["content"],
                    title=item.get("file_name", "Unknown"),
                    score=item["score"],
                    search_type="exact_match",
                    metadata={
                        "doc_id": item.get("doc_id", ""),
                        "chunk_index": item.get("chunk_index", 0),
                        "query": query
                    }
                )
                search_results.append(search_result)
            
            print(f"❗ 完全一致検索最終結果: {len(search_results)}件")
            return search_results
            
        except Exception as e:
            print(f"❗❗❗ 完全一致検索でエラー発生: {str(e)} ❗❗❗")
            import traceback
            traceback.print_exc()
            return []

    def _improved_keyword_search(self, query: str, data: List[Dict]) -> List[Dict]:
        """
        改良されたキーワードベース検索
        """
        print(f"❗ 🔍 改良されたキーワード検索実行")
        print(f"❗ 検索クエリ: '{query}'")
        
        # クエリを小文字に変換
        query_lower = query.lower()
        print(f"❗ 小文字変換: '{query_lower}'")
        
        # 関連キーワードの拡張
        keyword_expansions = {
            "マウス": ["マウス", "mouse", "ポインティングデバイス", "ワイヤレスマウス", "光学マウス", "レーザーマウス", "ゲーミングマウス", "エルゴノミクス"],
            "pc": ["pc", "パソコン", "computer", "デスクトップ", "ノートパソコン", "ノート", "デスクトップPC", "パーソナルコンピューター"],
            "おすすめ": ["おすすめ", "推奨", "選び方", "人気", "ランキング", "最適", "適した", "良い"],
            "教えて": ["教えて", "について", "情報", "詳細", "説明", "紹介", "案内"]
        }
        
        # キーワード抽出
        keywords = []
        for base_keyword, expansions in keyword_expansions.items():
            if base_keyword in query_lower:
                keywords.extend(expansions)
        
        # 直接的なキーワード抽出も追加（物件番号対応）
        import re
        # 物件番号やコード（WPD4100399など）を優先的に抽出
        property_numbers = re.findall(r'[A-Z]+\d+', query)  # 大文字+数字のパターン（物件番号）
        receipt_numbers = re.findall(r'J\d+', query)       # 受注番号パターン
        
        # 柔軟性を保持した多段階キーワード抽出
        # 1. 基本的なキーワード抽出（単語レベル）
        basic_keywords = re.findall(r'[ぁ-んァ-ヶー一-龯]{2,}|[a-zA-Z0-9]{2,}', query_lower)
        
        # 2. 重要な単語の個別抽出（1文字でも重要な場合）
        important_single = re.findall(r'[機装会社製品技術]', query_lower)
        
        # 3. 助詞・接続詞を除いた意味のある単語のみ抽出
        stop_words_extended = {'の', 'に', 'を', 'は', 'が', 'で', 'と', 'から', 'まで', 'より', 'こと', 'もの', 'これ', 'それ', 'あれ', 'どの', 'どんな', '何', 'です', 'ですか', 'ます', 'した'}
        meaningful_keywords = [kw for kw in basic_keywords if kw not in stop_words_extended and len(kw) >= 1]
        
        # 物件番号を最優先で追加（完全一致の優位性保持）
        keywords.extend(property_numbers)      # 最優先：完全一致が必要
        keywords.extend(receipt_numbers)       # 次に優先：完全一致が必要
        keywords.extend(meaningful_keywords)   # 一般キーワード：柔軟性を保持
        keywords.extend(important_single)      # 重要な1文字：補完的に追加
        
        # 重複除去
        keywords = list(set(keywords))
        print(f"❗ 抽出されたキーワード: {keywords}")
        
        # スコアリング
        scored_results = []
        for item in data:
            content = item.get("content", "").lower()
            
            # スコア計算
            score = 0.0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in content:
                    matched_keywords.append(keyword)
                    # キーワードの重要度に応じてスコア付け
                    # 物件番号・受注番号は最優先
                    if re.match(r'[A-Z]+\d+', keyword):  # 物件番号パターン（WPD4100399など）
                        score += 0.85  # 圧倒的最優先（ベクトル検索に確実に勝つ）
                    elif re.match(r'J\d+', keyword):  # 受注番号パターン
                        score += 0.85  # 圧倒的最優先（ベクトル検索に確実に勝つ）
                    elif keyword in ["マウス", "mouse"]:
                        score += 2.0  # 最重要キーワード
                    elif keyword in ["pc", "パソコン", "computer", "デスクトップ", "ノートパソコン"]:
                        score += 1.5  # 重要キーワード
                    elif keyword in ["おすすめ", "推奨", "選び方", "人気", "ランキング"]:
                        score += 1.0  # 関連キーワード
                    elif keyword in ["ワイヤレスマウス", "光学マウス", "レーザーマウス", "ゲーミングマウス"]:
                        score += 1.8  # 特定マウス関連キーワード
                    elif keyword in ["機械", "装置", "設備", "会社", "株式会社"]:  # 日本語キーワード
                        score += 2.0  # 日本語重要キーワード
                    else:
                        score += 0.5  # 一般キーワード
            
            # スコアの正規化（最大1.0）
            if score > 0:
                # より柔軟な正規化（最大キーワード数の半分で満点）
                max_possible_score = len(keywords) * 2.0
                normalized_score = min(score / max_possible_score * 2.0, 1.0)
                item_copy = item.copy()
                item_copy["score"] = normalized_score
                item_copy["matched_keywords"] = matched_keywords
                scored_results.append(item_copy)
        
        # スコア順にソート
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        
        # 閾値フィルタリング（スコア0.1以上）
        filtered_results = [item for item in scored_results if item["score"] >= 0.1]
        
        print(f"❗ キーワードマッチング結果: {len(filtered_results)}件")
        if filtered_results:
            print(f"❗ 最高スコア: {filtered_results[0]['score']:.3f}")
            print(f"❗ 最高スコアのマッチキーワード: {filtered_results[0]['matched_keywords']}")
        
        return filtered_results

    def _improved_fuzzy_search(self, query: str, data: List[Dict]) -> List[Dict]:
        """
        改良されたFuzzy検索（キーワードベース + 意味解析）
        """
        print(f"❗ 🔍 改良されたFuzzy検索実行")
        print(f"❗ 検索クエリ: '{query}'")
        
        # クエリを小文字に変換
        query_lower = query.lower()
        print(f"❗ 小文字変換: '{query_lower}'")
        
        # 質問内容に応じたキーワード拡張
        keyword_expansions = {
            # メール関連
            "メール": ["メール", "email", "mail", "送信", "配信", "通知"],
            "送信": ["送信", "配信", "mail", "email", "通知", "連絡"],
            
            # 設置関連  
            "設置": ["設置", "installation", "install", "工事", "導入", "構築"],
            "完了": ["完了", "終了", "finish", "complete", "済み"],
            
            # 個人情報関連
            "個人": ["個人", "personal", "プライベート", "private"],
            "アドレス": ["アドレス", "address", "宛先", "送付先"],
            
            # 手続き関連
            "手続き": ["手続き", "procedure", "process", "申請", "承認"],
            "確認": ["確認", "check", "verify", "承認", "許可"],
            
            # 業務関連
            "業務": ["業務", "work", "job", "作業", "タスク"],
            "規則": ["規則", "rule", "規定", "ルール", "ガイドライン", "マニュアル"]
        }
        
        # ストップワード（検索精度を下げる単語）
        stop_words = ["について", "教えて", "を", "の", "に", "は", "が", "で", "と", "から", "まで", "？", "?"]
        
        # キーワード抽出
        keywords = []
        for base_keyword, expansions in keyword_expansions.items():
            if base_keyword in query_lower:
                keywords.extend(expansions)
        
        # 直接的なキーワード抽出（ストップワード除外）
        import re
        # 物件番号やコード（WPD4100399など）を優先的に抽出
        property_numbers = re.findall(r'[A-Z]+\d+', query)  # 大文字+数字のパターン（物件番号）
        receipt_numbers = re.findall(r'J\d+', query)       # 受注番号パターン
        
        # 柔軟性を保持した多段階キーワード抽出（Fuzzy検索用）
        # 1. 基本的なキーワード抽出（単語レベル）
        basic_keywords = re.findall(r'[ぁ-んァ-ヶー一-龯]{2,}|[a-zA-Z0-9]{2,}', query_lower)
        
        # 2. 重要な単語の個別抽出
        important_single = re.findall(r'[機装会社製品技術]', query_lower)
        
        # 3. Fuzzy検索用のより柔軟なキーワード（1文字以上も含む）
        all_extracted = basic_keywords + important_single
        meaningful_keywords = [kw for kw in all_extracted if kw not in stop_words and len(kw) >= 1]
        
        # 物件番号を最優先で追加（重複を避けるため先にクリア）
        keywords = []
        keywords.extend(property_numbers)  # 最優先
        keywords.extend(receipt_numbers)   # 次に優先
        keywords.extend(meaningful_keywords)  # 最後に一般キーワード
        
        # 物件番号が見つかった場合は他のキーワードの重要度を下げる
        if property_numbers or receipt_numbers:
            print(f"❗ 優先キーワード検出: 物件番号={property_numbers}, 受注番号={receipt_numbers}")
            # 物件番号が見つかった場合は、一般キーワードは最低限に絞る
            meaningful_keywords = [kw for kw in meaningful_keywords if len(kw) >= 3]
            keywords = property_numbers + receipt_numbers + meaningful_keywords[:3]  # 一般キーワードは3つまで
        
        # 重複除去
        keywords = list(set(keywords))
        print(f"❗ 抽出されたキーワード: {keywords}")
        
        # 意味的関連性スコアリング
        scored_results = []
        for item in data:
            content = item.get("content", "").lower()
            
            # スコア計算
            score = 0.0
            matched_keywords = []
            context_score = 0.0
            
            for keyword in keywords:
                if keyword in content:
                    matched_keywords.append(keyword)
                    
                    # キーワードの重要度と文脈を考慮したスコア付け
                    if keyword in ["メール", "email", "mail"]:
                        score += 3.0  # 最重要キーワード
                        # メール関連の文脈チェック
                        if any(ctx in content for ctx in ["送信", "配信", "通知", "アドレス"]):
                            context_score += 2.0
                    elif keyword in ["設置", "installation", "完了", "finish"]:
                        score += 2.5  # 高重要度
                        if any(ctx in content for ctx in ["工事", "導入", "構築"]):
                            context_score += 1.5
                    elif keyword in ["個人", "personal", "プライベート"]:
                        score += 2.0  # 重要
                        if any(ctx in content for ctx in ["情報", "データ", "アドレス"]):
                            context_score += 1.5
                    elif keyword in ["送信", "配信", "通知"]:
                        score += 2.8  # メール送信関連
                    elif keyword in ["手続き", "確認", "承認", "許可"]:
                        score += 1.8  # プロセス関連
                    elif keyword in ["規則", "rule", "ガイドライン", "マニュアル"]:
                        score += 1.5  # 規則関連
                    elif keyword in ["機械", "装置", "設備", "会社", "株式会社"]:  # 日本語キーワード
                        score += 2.5  # 日本語重要キーワード
                    else:
                        score += 0.8  # 一般キーワード
            
            # 総合スコア計算（基本スコア + 文脈スコア）
            total_score = score + context_score
            
            # より厳格な閾値（意味のないデータを除外）
            if total_score > 0 and len(matched_keywords) > 0:
                # スコアの正規化（最大キーワード数とコンテキストを考慮）
                max_possible_score = len(keywords) * 3.0 + 2.0
                normalized_score = min(total_score / max_possible_score * 1.5, 1.0)
                
                # 最低閾値を0.4に設定（より厳格）
                if normalized_score >= 0.4:
                    item_copy = item.copy()
                    item_copy["fuzzy_score"] = normalized_score
                    item_copy["matched_keywords"] = matched_keywords
                    item_copy["context_score"] = context_score
                    scored_results.append(item_copy)
        
        # スコア順にソート
        scored_results.sort(key=lambda x: x["fuzzy_score"], reverse=True)
        
        print(f"❗ 改良されたFuzzy検索結果: {len(scored_results)}件")
        if scored_results:
            print(f"❗ 最高スコア: {scored_results[0]['fuzzy_score']:.3f}")
            print(f"❗ 最高スコアのマッチキーワード: {scored_results[0]['matched_keywords']}")
            print(f"❗ 文脈スコア: {scored_results[0]['context_score']:.3f}")
        else:
            print(f"❗ 厳格な閾値により、関連性の低いデータをすべて除外しました")
        
        return scored_results
    
    async def _fuzzy_search(self, query: str, company_id: str, limit: int) -> List[SearchResult]:
        """Fuzzy検索（pg_trgm使用）"""
        print(f"\n❗❗❗ Fuzzy検索開始 ❗❗❗")
        print(f"❗ クエリ: '{query}'")
        print(f"❗ 会社ID: '{company_id}'")
        print(f"❗ 制限数: {limit}")
        
        try:
            # pg_trgm拡張機能は制限されているため、基本検索にフォールバック
            print(f"\n❗ 1. 基本検索（pg_trgm代替）")
            print(f"❗ pg_trgm拡張機能の確認はスキップ（SQL制限のため）")
            print(f"❗ 部分一致検索にフォールバック")
            
            # 基本操作での部分一致検索
            print(f"\n❗ 2. Supabase基本操作でFuzzy風検索実行")
            
            try:
                # 検索条件を構築
                search_filters = {}
                if company_id:
                    search_filters['company_id'] = company_id
                
                print(f"❗ 検索フィルタ: {search_filters}")
                
                # 全てのchunksを取得してPython側でフィルタリング
                results = select_data(
                    "chunks", 
                    columns="*",
                    filters=search_filters,
                    limit=limit * 5  # より多く取得してフィルタ
                )
                
                print(f"❗ Supabase検索結果タイプ: {type(results)}")
                print(f"❗ Supabase検索結果データ数: {len(results.data) if results.data else 0}")
                
                # 結果が0件の場合、会社IDフィルタなしで再試行
                if not results.data or len(results.data) == 0:
                    print(f"❗ Fuzzy: 会社IDフィルタで0件のため、フィルタなしで再試行")
                    results_no_filter = select_data(
                        "chunks", 
                        columns="*",
                        limit=limit * 5
                    )
                    print(f"❗ Fuzzy: フィルタなし検索結果データ数: {len(results_no_filter.data) if results_no_filter.data else 0}")
                    if results_no_filter.data and len(results_no_filter.data) > 0:
                        results = results_no_filter
                        print(f"❗ Fuzzy: フィルタなし検索を採用")
                
            except Exception as search_error:
                print(f"❗❗❗ Supabase検索エラー: {search_error} ❗❗❗")
                return []
            
            # 結果データ処理とPython側Fuzzy検索
            print(f"\n❗ 3. Python側Fuzzy検索実行")
            if hasattr(results, 'data') and results.data:
                all_data = results.data
                print(f"❗ Supabaseから取得: {len(all_data)}件")
                
                # Python側で改良されたFuzzy検索実行
                filtered_data = self._improved_fuzzy_search(query, all_data)
                
                # 結果は既にソート済み、制限数まで取得
                data = filtered_data[:limit]
                
                print(f"❗ 改良されたFuzzy検索後: {len(data)}件")
                
            elif hasattr(results, 'error') and results.error:
                print(f"❗❗❗ Supabaseエラー: {results.error} ❗❗❗")
                return []
            else:
                print(f"❗❗❗ エラー原因特定: 未知のSupabase結果タイプ: {type(results)} ❗❗❗")
                return []
            
            if data:
                print(f"❗ 改良されたFuzzyデータサンプル表示:")
                for i, item in enumerate(data[:3]):
                    score = item.get('fuzzy_score', 'N/A')
                    keywords = item.get('matched_keywords', [])
                    context = item.get('context_score', 0)
                    print(f"❗   [{i+1}] score={score}, keywords={keywords[:3]}, context={context}, id={item.get('id', 'N/A')}")
            else:
                print(f"❗❗❗ 改良されたFuzzy検索で関連データが見つかりませんでした ❗❗❗")
                print(f"❗ これは検索精度向上により、無関係なデータが除外されたためです")
                return []
            
            # SearchResultオブジェクト変換
            print(f"\n❗ 4. 改良されたFuzzy SearchResultオブジェクト変換")
            search_results = []
            for i, r in enumerate(data):
                try:
                    content = r.get('content', '')
                    if content:
                        # 改良されたメタデータの設定
                        metadata = {
                            'query': query, 
                            'method': 'improved_fuzzy',
                            'matched_keywords': r.get('matched_keywords', []),
                            'context_score': r.get('context_score', 0)
                        }
                        
                        search_result = SearchResult(
                            id=str(r.get('id', '')),
                            content=content,
                            title=r.get('title', r.get('name', 'Unknown')),
                            score=float(r.get('fuzzy_score', 0.0)),
                            search_type=SearchType.FUZZY_SEARCH.value,
                            metadata=metadata
                        )
                        search_results.append(search_result)
                        keywords = r.get('matched_keywords', [])
                        print(f"❗ 改良Fuzzy変換成功 [{i+1}]: ID={r.get('id')}, スコア={r.get('fuzzy_score'):.3f}, キーワード={keywords[:2]}")
                    else:
                        print(f"❗ Fuzzyコンテンツなしでスキップ [{i+1}]: {r}")
                except Exception as conv_error:
                    print(f"❗❗❗ Fuzzy変換エラー [{i+1}]: {conv_error} ❗❗❗")
                    print(f"❗ データ: {r}")
            
            print(f"❗ 改良されたFuzzy検索最終結果: {len(search_results)}件")
            return search_results
            
        except Exception as e:
            print(f"\n❗❗❗ 改良されたFuzzy検索で致命的エラー発生 ❗❗❗")
            print(f"❗ エラー内容: {e}")
            print(f"❗ エラータイプ: {type(e)}")
            import traceback
            print(f"❗ 詳細トレースバック:")
            traceback.print_exc()
            return []
    
    async def _vector_search(self, query: str, company_id: str, limit: int) -> List[SearchResult]:
        """ベクトル検索"""
        print(f"--- start _vector_search in best_score_search ---")
        print(f"query: {query}, company_id: {company_id}, limit: {limit}")
        print(f"\n❗❗❗ ベクトル検索開始 ❗❗❗")
        print(f"❗ クエリ: '{query}'")
        print(f"❗ 会社ID: '{company_id}'")
        print(f"❗ 制限数: {limit}")
        
        try:
            # ベクトル検索インスタンス確認
            print(f"\n❗ 1. ベクトル検索インスタンス確認")
            print(f"❗ self.vector_search: {self.vector_search}")
            print(f"❗ type(self.vector_search): {type(self.vector_search)}")
            
            if not self.vector_search:
                print(f"❗❗❗ エラー原因特定: ベクトル検索インスタンスがNoneです！ ❗❗❗")
                print(f"❗ 可能な原因:")
                print(f"❗   - VectorSearchSystemの初期化失敗")
                print(f"❗   - 環境変数の設定不備")
                return []
            
            # ベクトル検索メソッド存在確認
            print(f"\n❗ 2. ベクトル検索メソッド存在確認")
            has_method = hasattr(self.vector_search, 'vector_similarity_search')
            print(f"❗ vector_similarity_searchメソッド存在: {has_method}")
            
            if not has_method:
                print(f"❗❗❗ エラー原因特定: vector_similarity_searchメソッドが存在しません！ ❗❗❗")
                return []
            
            # ベクトル検索実行
            print(f"\n❗ 3. ベクトル検索実行")
            print(f"❗ 実行前: self.vector_search.vector_similarity_search('{query}', '{company_id}', {limit})")
            
            results = await self.vector_search.vector_similarity_search(query, company_id, limit)
            
            print(f"❗ ベクトル検索実行結果タイプ: {type(results)}")
            print(f"❗ ベクトル検索実行結果件数: {len(results) if results else 0}")
            
            if results:
                print(f"❗ ベクトル検索データサンプル表示:")
                for i, item in enumerate(results[:3]):
                    print(f"❗   [{i+1}] {list(item.keys()) if isinstance(item, dict) else type(item)}")
                    if isinstance(item, dict):
                        print(f"❗       chunk_id: {item.get('chunk_id', 'N/A')}")
                        print(f"❗       similarity_score: {item.get('similarity_score', 'N/A')}")
                        print(f"❗       snippet length: {len(item.get('snippet', '')) if item.get('snippet') else 0}")
            else:
                print(f"❗❗❗ エラー原因特定: ベクトル検索結果が0件またはNoneです ❗❗❗")
                print(f"❗ 可能な原因:")
                print(f"❗   - エンベディング生成失敗")
                print(f"❗   - データベースにエンベディングデータがない")
                print(f"❗   - pgvector拡張機能の問題")
                return []
            
            # SearchResultオブジェクト変換
            print(f"\n❗ 4. ベクトル検索 SearchResultオブジェクト変換")
            search_results = []
            for i, r in enumerate(results):
                try:
                    # データキーの確認
                    print(f"❗ 変換対象 [{i+1}]: {list(r.keys()) if isinstance(r, dict) else 'Not dict'}")
                    
                    snippet = r.get('snippet', r.get('content', ''))
                    if snippet:
                        search_result = SearchResult(
                            id=str(r.get('chunk_id', r.get('id', ''))),
                            content=snippet,
                            title=r.get('document_name', r.get('title', 'Unknown')),
                            score=float(r.get('similarity_score', r.get('score', 0.0))),
                            search_type=SearchType.VECTOR_SEARCH.value,
                            metadata={'query': query, 'method': 'vector', 'document_type': r.get('document_type', '')}
                        )
                        search_results.append(search_result)
                        print(f"❗ ベクトル変換成功 [{i+1}]: ID={r.get('chunk_id', 'N/A')}, スコア={r.get('similarity_score', 'N/A')}")
                    else:
                        print(f"❗ ベクトルコンテンツなしでスキップ [{i+1}]: snippet={r.get('snippet', 'N/A')}, content={r.get('content', 'N/A')}")
                except Exception as conv_error:
                    print(f"❗❗❗ ベクトル変換エラー [{i+1}]: {conv_error} ❗❗❗")
                    print(f"❗ データ: {r}")
            
            print(f"❗ ベクトル検索最終結果: {len(search_results)}件")
            return search_results
            
        except Exception as e:
            print(f"\n❗❗❗ ベクトル検索で致命的エラー発生 ❗❗❗")
            print(f"❗ エラー内容: {e}")
            print(f"❗ エラータイプ: {type(e)}")
            import traceback
            print(f"❗ 詳細トレースバック:")
            traceback.print_exc()
            return []

        print(f"--- end _vector_search in best_score_search ---")
        print(f"search_results: {search_results}")
        return search_results
    
    async def _select_best_scores(self, 
                                 search_results: Dict[str, List[SearchResult]], 
                                 company_id: str,
                                 limit: int) -> List[SearchResult]:
        """各検索手法の結果からベストスコアを選択"""
        try:
            safe_print(f"📊 スコア正規化と最高スコア選択開始")
            
            # 各検索手法のスコアを正規化
            normalized_results = {}
            
            for method_name, results in search_results.items():
                if not results:
                    normalized_results[method_name] = []
                    continue
                
                # 検索タイプを取得
                search_type = results[0].search_type if results else "unknown"
                
                # スコア正規化
                normalized = await self.score_normalizer.normalize_scores(results, search_type, company_id)
                normalized_results[method_name] = normalized
                
                if normalized:
                    max_score = max(r.score for r in normalized)
                    avg_score = sum(r.score for r in normalized) / len(normalized)
                    safe_print(f"  📈 {method_name}: 最高={max_score:.3f}, 平均={avg_score:.3f}, 件数={len(normalized)}")
            
            # 各手法から最高スコアの結果を1つずつ選択
            best_candidates = []
            
            for method_name, results in normalized_results.items():
                if results:
                    # 最高スコアの結果を選択
                    best_result = max(results, key=lambda x: x.score)
                    best_candidates.append(best_result)
                    safe_print(f"  🏆 {method_name}最高: スコア={best_result.score:.3f}, ID={best_result.id}")
            
            # 最高スコアの候補から上位を選択
            best_candidates.sort(key=lambda x: x.score, reverse=True)
            
            # さらに他の高スコア結果も追加（重複除去）
            additional_results = []
            seen_ids = {r.id for r in best_candidates}
            
            for method_name, results in normalized_results.items():
                for result in results:
                    if result.id not in seen_ids and result.score > 0.3:  # 閾値以上のスコア
                        additional_results.append(result)
                        seen_ids.add(result.id)
            
            # 追加結果をスコア順でソート
            additional_results.sort(key=lambda x: x.score, reverse=True)
            
            # 最終結果を組み合わせ
            final_results = best_candidates + additional_results
            final_results = final_results[:limit]
            
            safe_print(f"🎯 最終選択: {len(final_results)}件")
            for i, result in enumerate(final_results[:5]):  # 上位5件を表示
                safe_print(f"  {i+1}. [{result.search_type}] スコア={result.score:.3f} - {result.title}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"ベストスコア選択エラー: {e}")
            # フォールバック: すべての結果をマージして返す
            all_results = []
            for results in search_results.values():
                all_results.extend(results)
            all_results.sort(key=lambda x: x.score, reverse=True)
            return all_results[:limit]
    
    def _display_search_comparison(self, 
                                  search_results: Dict[str, List[SearchResult]], 
                                  final_results: List[SearchResult],
                                  query: str):
        """検索結果の比較を表示"""
        try:
            print("\n" + "="*80)
            print(f"🔍 【検索結果比較】クエリ: '{query}'")
            print("="*80)
            
            # 各検索手法の結果
            for method_name, results in search_results.items():
                if results:
                    max_score = max(r.score for r in results)
                    min_score = min(r.score for r in results)
                    avg_score = sum(r.score for r in results) / len(results)
                    
                    print(f"📊 {method_name}検索:")
                    print(f"   件数: {len(results)}, 最高: {max_score:.3f}, 最低: {min_score:.3f}, 平均: {avg_score:.3f}")
                    
                    # 上位3件を表示
                    top_results = sorted(results, key=lambda x: x.score, reverse=True)[:3]
                    for i, result in enumerate(top_results, 1):
                        snippet = result.content[:50].replace('\n', ' ') + "..."
                        print(f"   {i}. スコア={result.score:.3f} - {snippet}")
                else:
                    print(f"📊 {method_name}検索: 結果なし")
                print()
            
            # 最終選択結果
            print("🏆 最終選択結果:")
            for i, result in enumerate(final_results[:5], 1):
                method_icon = {"exact_match": "🎯", "fuzzy_search": "🔍", "vector_search": "🧠"}.get(result.search_type, "❓")
                snippet = result.content[:50].replace('\n', ' ') + "..."
                print(f"   {i}. {method_icon} [{result.search_type}] スコア={result.score:.3f} - {snippet}")
            
            print("="*80 + "\n")
            
        except Exception as e:
            logger.error(f"検索結果比較表示エラー: {e}")

# グローバルインスタンス
best_score_search_system = BestScoreSearchSystem()

async def search_with_best_score(query: str, 
                                company_id: str = None,
                                limit: int = 10) -> List[Dict[str, Any]]:
    """
    最高スコア選択型検索のエントリーポイント
    
    ファジー、エンベディング、完全一致検索を並列実行して
    一番スコアが高いものを採用
    
    Args:
        query: 検索クエリ
        company_id: 会社ID
        limit: 結果数制限
    
    Returns:
        検索結果のリスト
    """
    return await best_score_search_system.search_best_score(query, company_id, limit) 