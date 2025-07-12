"""
Unnamed Column Handler
unnamed_column_handling_guide_en.mdの指針に基づいて「Unnamed」カラムを検出・修正するモジュール
"""
import pandas as pd
import re
import logging
from typing import List, Dict, Tuple, Optional, Union
from ..database import ensure_string

logger = logging.getLogger(__name__)

class UnnamedColumnHandler:
    """「Unnamed」カラムを検出・修正するクラス"""
    
    def __init__(self):
        # ビジネス特有のキーワード（日本語対応）
        self.header_keywords = [
            # 基本情報
            '顧客', 'お客様', '会社', '企業', '組織', '部門', '部署',
            '名前', '氏名', 'name', '名称', 'title', 'タイトル', '項目', 'フィールド',
            '住所', 'address', '連絡先', '電話', 'phone', 'tel',
            'メール', 'email', 'mail', 'fax', 'URL', 'ウェブサイト',
            
            # 識別子
            'id', 'ID', '番号', 'no', 'number', 'code', 'コード',
            '識別', 'identifier', 'ident', '管理', '管理番号', 'キー',
            
            # 日付・時刻
            '日付', 'date', '時刻', 'time', '年', 'year', '月', 'month', '日', 'day',
            '開始', 'start', '終了', 'end', '期間', 'period',
            '作成', 'created', '更新', 'updated', '最終', 'last', '登録日', '完了日',
            
            # 金額・数値
            '金額', 'amount', '価格', 'price', '料金', 'fee', '費用', 'cost',
            '数量', 'quantity', '個数', 'count', '件数', 'total', '合計',
            '単価', 'unit', '税', 'tax', '消費税', '割引', '利益',
            
            # ステータス・状態
             'status', 'ステータス', '状態', 'state', '段階', 'phase',
            '完了', 'complete', '進行', 'progress', '開始', 'active',
            '停止', 'stop', '終了', 'finish', '承認', 'approval', '状況',
            
            # 分類・カテゴリ
            'カテゴリ', 'category', '分類', 'type', '種類', 'kind',
            'レベル', 'level', 'グレード', 'grade', 'ランク', 'rank', 'グループ', '区分',
            
            # その他
            '備考', 'note', 'memo', 'メモ', '説明', 'description',
            '内容', 'content', '詳細', 'detail', '要約', 'summary',
            '適用', '対象', 'ソース', '情報源', 'データ', '値'
        ]
        
        # Unnamedパターン
        self.unnamed_patterns = [
            r'^Unnamed.*',
            r'^Unnamed:\s*\d*$',  # 'Unnamed: 1', 'Unnamed: 2' など
            r'^Column.*',
            r'^列.*',
            r'^無題.*',
            r'^\s*$',  # 空白
            r'^_+$',   # アンダースコアのみ
            r'^\d+$'   # 数字のみ
        ]
    
    def detect_header_row(self, df: pd.DataFrame) -> int:
        """真のヘッダー行を検出する"""
        try:
            if df.empty:
                return 0
            
            max_score = -1
            best_row = 0
            
            # 最初の5行を検査
            for i in range(min(5, len(df))):
                row = df.iloc[i]
                score = self._calculate_header_score(row)
                
                logger.debug(f"行 {i}: スコア {score}, 内容: {list(row.values)[:3]}")
                
                if score > max_score:
                    max_score = score
                    best_row = i
            
            # スコアが十分高い場合のみヘッダーとして採用
            if max_score >= 3:
                logger.info(f"ヘッダー行検出: 行 {best_row} (スコア: {max_score})")
                return best_row
            
            # デフォルトで最初の行をヘッダーとする
            logger.info("明確なヘッダー行が検出されませんでした。行 0 をヘッダーとして使用")
            return 0
            
        except Exception as e:
            logger.error(f"ヘッダー行検出エラー: {str(e)}")
            return 0
    
    def _calculate_header_score(self, row: pd.Series) -> float:
        """行がヘッダーである可能性のスコアを計算"""
        score = 0
        non_empty_cells = 0
        
        for value in row.values:
            if pd.notna(value) and str(value).strip():
                non_empty_cells += 1
                value_str = ensure_string(value).lower()
                
                # キーワードマッチング
                for keyword in self.header_keywords:
                    if keyword.lower() in value_str:
                        score += 2
                        break
                
                # 文字列の特徴をチェック
                if any(char.isalpha() for char in value_str):
                    score += 1
                
                # 数字のみの場合はマイナス
                if value_str.isdigit():
                    score -= 1
        
        # 空のセルが多すぎる場合はマイナス
        if non_empty_cells < len(row) * 0.3:
            score -= 2
        
        return score
    
    def detect_unnamed_columns(self, df: pd.DataFrame) -> List[int]:
        """Unnamedカラムを検出する"""
        unnamed_columns = []
        
        try:
            for i, col in enumerate(df.columns):
                col_str = ensure_string(col)
                
                # Unnamedパターンにマッチするかチェック
                for pattern in self.unnamed_patterns:
                    if re.match(pattern, col_str, re.IGNORECASE):
                        unnamed_columns.append(i)
                        logger.debug(f"Unnamedカラム検出: インデックス {i}, 名前: '{col_str}'")
                        break
                        
        except Exception as e:
            logger.error(f"Unnamedカラム検出エラー: {str(e)}")
        
        return unnamed_columns
    
    def analyze_column_content(self, df: pd.DataFrame, col_index: int) -> Dict[str, any]:
        """カラムの内容を分析する"""
        try:
            if col_index >= len(df.columns):
                return {'type': 'invalid', 'is_row_index': False, 'suggested_name': None}
            
            col_data = df.iloc[:, col_index]
            
            # 空のカラムチェック
            non_null_count = col_data.count()
            if non_null_count == 0:
                return {'type': 'empty', 'is_row_index': False, 'suggested_name': None}
            
            # 行インデックスかどうかをチェック
            is_row_index = self._is_row_index_column(col_data)
            
            # データ型を分析
            data_type = self._analyze_data_type(col_data)
            
            # 名前を提案
            suggested_name = self._suggest_column_name(col_data, col_index, df)
            
            return {
                'type': data_type,
                'is_row_index': is_row_index,
                'suggested_name': suggested_name,
                'non_null_count': non_null_count,
                'total_count': len(col_data)
            }
            
        except Exception as e:
            logger.error(f"カラム内容分析エラー: {str(e)}")
            return {'type': 'error', 'is_row_index': False, 'suggested_name': None}
    
    def _is_row_index_column(self, col_data: pd.Series) -> bool:
        """カラムが行インデックスかどうかを判定"""
        try:
            # NaN値を除去
            non_null_data = col_data.dropna()
            
            if len(non_null_data) < 2:
                return False
            
            # 数値のみかチェック
            try:
                numeric_data = pd.to_numeric(non_null_data, errors='coerce')
                # 安全な NaN チェック
                has_nan = False
                try:
                    has_nan = numeric_data.isna().any()
                except Exception as nan_error:
                    logger.debug(f"Series NaN チェックエラー: {str(nan_error)}")
                    # Series の真偽値判定エラーの場合は個別チェック
                    try:
                        has_nan = any(pd.isna(val) for val in numeric_data)
                    except Exception as individual_error:
                        logger.debug(f"個別NaNチェックエラー: {str(individual_error)}")
                        has_nan = True  # エラーの場合は安全側に倒す
                
                if has_nan:
                    return False
                
                # 連続する整数かチェック
                if all(val == int(val) for val in numeric_data):
                    # ソートして連続性をチェック
                    sorted_data = sorted(numeric_data)
                    differences = [sorted_data[i+1] - sorted_data[i] for i in range(len(sorted_data)-1)]
                    
                    # 差が1の場合が70%以上
                    if sum(1 for diff in differences if diff == 1) / len(differences) >= 0.7:
                        return True
                        
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.error(f"行インデックス判定エラー: {str(e)}")
            return False
    
    def _analyze_data_type(self, col_data: pd.Series) -> str:
        """データ型を分析"""
        try:
            non_null_data = col_data.dropna()
            
            if len(non_null_data) == 0:
                return 'empty'
            
            # 数値型チェック
            try:
                pd.to_numeric(non_null_data, errors='raise')
                return 'numeric'
            except:
                pass
            
            # 日付型チェック
            try:
                pd.to_datetime(non_null_data, errors='raise')
                return 'datetime'
            except:
                pass
            
            # 文字列型
            return 'text'
            
        except Exception as e:
            logger.error(f"データ型分析エラー: {str(e)}")
            return 'unknown'
    
    def _suggest_column_name(self, col_data: pd.Series, col_index: int, df: pd.DataFrame) -> Optional[str]:
        """カラム名を提案"""
        try:
            # 隣接するカラムの名前から推測
            if col_index > 0:
                prev_col = df.columns[col_index - 1]
                prev_str = ensure_string(prev_col).lower()
                
                # パターンマッチング
                if 'id' in prev_str or '番号' in prev_str:
                    return '関連情報'
                elif 'name' in prev_str or '名前' in prev_str or '氏名' in prev_str:
                    return '詳細'
                elif 'date' in prev_str or '日付' in prev_str:
                    return '時刻'
                elif 'price' in prev_str or '価格' in prev_str or '金額' in prev_str:
                    return '税額'
            
            # データの内容から推測
            non_null_data = col_data.dropna()
            if len(non_null_data) > 0:
                sample_values = [ensure_string(val).lower() for val in non_null_data.head(5)]
                
                # よくあるパターン
                for sample in sample_values:
                    if re.search(r'\d{4}[-/]\d{2}[-/]\d{2}', sample):
                        return '日付'
                    elif re.search(r'\d+[円￥]', sample):
                        return '金額'
                    elif '@' in sample:
                        return 'メールアドレス'
                    elif re.search(r'\d{3}-\d{4}-\d{4}', sample):
                        return '電話番号'
            
            # デフォルト名
            return f'データ{col_index + 1}'
            
        except Exception as e:
            logger.error(f"カラム名提案エラー: {str(e)}")
            return f'カラム{col_index + 1}'
    
    def fix_dataframe(self, df: pd.DataFrame, filename: str = "") -> Tuple[pd.DataFrame, List[str]]:
        """DataFrameのUnnamedカラム問題を修正"""
        try:
            if df.empty:
                return df, ["空のDataFrameです"]
            
            modifications = []
            
            # Step 1: 真のヘッダー行を検出
            header_row = self.detect_header_row(df)

            # --- 多段ヘッダー対応開始 ---
            base_header_idx = header_row
            second_header_idx = base_header_idx + 1 if base_header_idx + 1 < len(df) else None
            use_second_header = False

            if second_header_idx is not None:
                row2 = df.iloc[second_header_idx]
                non_empty = sum(1 for v in row2 if pd.notna(v) and str(v).strip())
                if non_empty >= len(row2) * 0.4:
                    use_second_header = True

            # 1段目ヘッダー行
            top_values = [ensure_string(v) for v in df.iloc[base_header_idx]]
            # 2段目ヘッダー行（存在しない場合は空文字）
            if use_second_header:
                sub_values_raw = [ensure_string(v) for v in df.iloc[second_header_idx]]
            else:
                sub_values_raw = [''] * len(top_values)

            # 結合セル対策: 直前の値を横展開
            propagated_top = []
            last_top = ''
            for v in top_values:
                v_clean = v.strip()
                if v_clean:
                    last_top = v_clean
                    propagated_top.append(v_clean)
                else:
                    propagated_top.append(last_top)

            # 最終カラム名生成
            combined_columns = []
            for i, (top, sub) in enumerate(zip(propagated_top, sub_values_raw)):
                top = top.strip()
                sub = sub.strip()
                if top and sub and top != sub:
                    col_name = f"{top}_{sub}"
                elif sub:
                    col_name = sub
                elif top:
                    col_name = top
                else:
                    col_name = f'列_{i+1}'
                combined_columns.append(col_name)

            # 重複カラム名解消
            seen = {}
            final_columns = []
            for col in combined_columns:
                base_name = col
                counter = seen.get(base_name, 0)
                if counter > 0:
                    col = f"{base_name}_{counter}"
                seen[base_name] = counter + 1
                final_columns.append(col)

            # データ部を抽出
            skip_rows = base_header_idx + (2 if use_second_header else 1)
            df_fixed = df.iloc[skip_rows:].copy()
            df_fixed.columns = final_columns

            modifications.append(
                f"行 {base_header_idx}{(' と ' + str(second_header_idx)) if use_second_header else ''} をヘッダーとして設定し、{skip_rows} 行をスキップしました")
            # --- 多段ヘッダー対応終了 ---
            
            # Step 2: Unnamedカラムを検出
            unnamed_cols = self.detect_unnamed_columns(df_fixed)
            
            if not unnamed_cols:
                modifications.append("Unnamedカラムは検出されませんでした")
                return df_fixed, modifications
            
            # Step 3: 各Unnamedカラムを分析・修正
            columns_to_drop = []
            renamed_columns = {}
            
            for col_idx in unnamed_cols:
                analysis = self.analyze_column_content(df_fixed, col_idx)
                old_name = df_fixed.columns[col_idx]
                
                if analysis['is_row_index']:
                    # 行インデックスの場合は削除
                    columns_to_drop.append(old_name)
                    modifications.append(f"行インデックスカラム '{old_name}' を削除しました")
                    
                elif analysis['type'] == 'empty':
                    # 空のカラムは削除
                    columns_to_drop.append(old_name)
                    modifications.append(f"空のカラム '{old_name}' を削除しました")
                    
                elif analysis['suggested_name']:
                    # 名前を変更
                    new_name = analysis['suggested_name']
                    # 重複を避ける
                    counter = 1
                    original_new_name = new_name
                    while new_name in df_fixed.columns or new_name in renamed_columns.values():
                        new_name = f"{original_new_name}_{counter}"
                        counter += 1
                    
                    renamed_columns[old_name] = new_name
                    modifications.append(f"カラム '{old_name}' を '{new_name}' に名前変更しました")
                else:
                    # デフォルト名を設定
                    new_name = f"データ{col_idx + 1}"
                    counter = 1
                    while new_name in df_fixed.columns or new_name in renamed_columns.values():
                        new_name = f"データ{col_idx + 1}_{counter}"
                        counter += 1
                        
                    renamed_columns[old_name] = new_name
                    modifications.append(f"カラム '{old_name}' を '{new_name}' に名前変更しました")
            
            # Step 4: 修正を適用
            # 削除
            if columns_to_drop:
                df_fixed = df_fixed.drop(columns=columns_to_drop)
            
            # 名前変更
            if renamed_columns:
                df_fixed = df_fixed.rename(columns=renamed_columns)
            
            # Step 5: 右端の空カラムを除去
            empty_cols = []
            for col in df_fixed.columns:
                try:
                    # 安全な空カラム判定
                    col_series = df_fixed[col]
                    
                    # まずNA値をチェック
                    try:
                        is_all_na = col_series.isna().all()
                        if is_all_na:
                            empty_cols.append(col)
                            continue
                    except Exception as na_error:
                        logger.debug(f"カラム '{col}' のNA値チェックでエラー: {str(na_error)}")
                        # 個別にNA値チェック
                        all_na = True
                        try:
                            for val in col_series:
                                if pd.notna(val):
                                    all_na = False
                                    break
                            if all_na:
                                empty_cols.append(col)
                                continue
                        except Exception as individual_na_error:
                            logger.debug(f"カラム '{col}' の個別NA値チェックでエラー: {str(individual_na_error)}")
                            # エラーの場合は安全側に倒す（削除しない）
                            pass
                    
                    # 文字列として変換して空文字チェック
                    try:
                        str_series = col_series.astype(str)
                        try:
                            is_all_empty = (str_series.str.strip() == '').all()
                            if is_all_empty:
                                empty_cols.append(col)
                        except Exception as all_error:
                            logger.debug(f"カラム '{col}' の.all()チェックでエラー: {str(all_error)}")
                            # 個別に空文字チェック
                            all_empty = True
                            for val in str_series:
                                if val.strip() != '':
                                    all_empty = False
                                    break
                            if all_empty:
                                empty_cols.append(col)
                    except Exception as str_error:
                        # 文字列変換でエラーが発生した場合は個別にチェック
                        all_empty = True
                        try:
                            for val in col_series:
                                if pd.notna(val):
                                    val_str = str(val).strip()
                                    if val_str and val_str != '':
                                        all_empty = False
                                        break
                        except Exception as individual_error:
                            # 個別チェックでもエラーが発生した場合は安全側に倒す
                            logger.debug(f"カラム '{col}' の個別値チェックでエラー: {str(individual_error)}")
                            all_empty = False  # 削除しない
                        
                        if all_empty:
                            empty_cols.append(col)
                            
                except Exception as col_error:
                    logger.warning(f"カラム '{col}' の空判定でエラー: {str(col_error)}")
                    # エラーが発生した場合はスキップ
                    continue
            
            if empty_cols:
                df_fixed = df_fixed.drop(columns=empty_cols)
                modifications.append(f"右端の空カラム {len(empty_cols)} 個を削除しました")
            
            modifications.append(f"修正完了: {len(df_fixed.columns)} カラム, {len(df_fixed)} 行")
            
            return df_fixed, modifications
            
        except Exception as e:
            logger.error(f"DataFrame修正エラー: {str(e)}")
            return df, [f"修正中にエラーが発生しました: {str(e)}"]
    
    def create_clean_sections(self, df: pd.DataFrame, filename: str) -> List[Dict]:
        """修正されたDataFrameから綺麗なセクションを作成"""
        try:
            if df.empty:
                return [{
                    'section': "エラー",
                    'content': "データが空です",
                    'source': 'Table',
                    'file': filename,
                    'url': None
                }]
            
            sections = []
            
            # ヘッダー情報をセクションとして追加
            header_info = "カラム: " + ", ".join(df.columns.tolist())
            sections.append({
                'section': "テーブル構造",
                'content': header_info,
                'source': 'Table',
                'file': filename,
                'url': None
            })
            
            # 各行をセクションとして追加
            for index, row in df.iterrows():
                content_parts = []
                for col, value in row.items():
                    if pd.notna(value) and str(value).strip():
                        content_parts.append(f"{col}: {ensure_string(value)}")
                
                if content_parts:
                    content = " | ".join(content_parts)
                    sections.append({
                        'section': f"行 {index + 1}",
                        'content': content,
                        'source': 'Table',
                        'file': filename,
                        'url': None
                    })
            
            return sections
            
        except Exception as e:
            logger.error(f"セクション作成エラー: {str(e)}")
            return [{
                'section': "エラー",
                'content': f"セクション作成中にエラーが発生しました: {str(e)}",
                'source': 'Table',
                'file': filename,
                'url': None
            }]
    
    def _is_unnamed_pattern(self, value: str) -> bool:
        """値がunnamedパターンにマッチするかチェック"""
        try:
            value_str = ensure_string(value).strip()
            
            for pattern in self.unnamed_patterns:
                if re.match(pattern, value_str, re.IGNORECASE):
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Unnamedパターンチェックエラー: {str(e)}")
            return False 

 