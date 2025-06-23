"""
知識ベース基本モジュール
知識ベースの基本クラスと共通関数を提供します
"""
import pandas as pd
import logging
from datetime import datetime
from ..database import ensure_string

logger = logging.getLogger(__name__)

# 知識ベースの保存用クラス
class KnowledgeBase:
    def __init__(self):
        self.data = None
        self.raw_text = ""
        self.columns = []
        self.sources = {}  # ソース（ファイル名やURL）を保存する辞書 {source_name: sections_dict}
        self.url_data = []  # URLから取得したデータを保存するリスト
        self.url_texts = []  # URLから取得したテキストを保存するリスト
        self.file_data = []  # ファイルから取得したデータを保存するリスト
        self.file_texts = []  # ファイルから取得したテキストを保存するリスト
        self.images = []    # PDFから抽出した画像データを保存するリスト
        self.source_info = {}  # ソースの詳細情報（タイムスタンプ、アクティブ状態など）
        self.original_data = {}  # 各ソースの元のデータを保存する辞書 {source_name: {'df': dataframe, 'text': text}}
        self.company_sources = {}  # 会社ごとのソースを保存する辞書 {company_id: [source_name1, source_name2, ...]}
        
    def get_company_data(self, company_id):
        """会社IDに関連するデータを取得する"""
        if not company_id or company_id not in self.company_sources:
            return None, "", []
            
        company_sources = self.company_sources.get(company_id, [])
        if not company_sources:
            return None, "", []
            
        # 会社のソースに関連するデータを収集
        company_data = []
        company_text = ""
        company_columns = []
        
        for source in company_sources:
            if source in self.original_data:
                source_data = self.original_data[source]
                if 'df' in source_data and not source_data['df'].empty:
                    company_data.append(source_data['df'])
                if 'text' in source_data:
                    company_text += source_data['text'] + "\n\n"
        
        # データフレームを結合
        combined_df = None
        if company_data:
            combined_df = pd.concat(company_data, ignore_index=True)
            company_columns = combined_df.columns.tolist()
            
        return combined_df, company_text, company_columns

# グローバルインスタンス
knowledge_base = KnowledgeBase()

# 知識ベースを更新する内部関数
def _update_knowledge_base(df, text, is_file=True, source_name=None, company_id=None):
    """知識ベースを更新する内部関数"""
    # 元のデータを保存
    if source_name:
        knowledge_base.original_data[source_name] = {
            'df': df.copy(),
            'text': ensure_string(text, for_db=True),
            'company_id': company_id
        }
        
        # 会社のソースリストに追加
        if company_id:
            if company_id not in knowledge_base.company_sources:
                knowledge_base.company_sources[company_id] = []
            if source_name not in knowledge_base.company_sources[company_id]:
                knowledge_base.company_sources[company_id].append(source_name)
    
    # ファイルかURLかに応じてデータを保存
    if is_file:
        knowledge_base.file_data.append(df)
        knowledge_base.file_texts.append(text)
    else:
        knowledge_base.url_data.append(df)
        knowledge_base.url_texts.append(text)
    
    # 全データを結合
    all_data = []
    if knowledge_base.file_data:
        all_data.extend(knowledge_base.file_data)
    if knowledge_base.url_data:
        all_data.extend(knowledge_base.url_data)
    
    if all_data:
        # データフレームを結合
        knowledge_base.data = pd.concat(all_data, ignore_index=True)
        
        # 列名を保存
        knowledge_base.columns = knowledge_base.data.columns.tolist()
        
        # 生テキストを結合
        all_texts = []
        if knowledge_base.file_texts:
            all_texts.extend([ensure_string(text, for_db=True) for text in knowledge_base.file_texts])
        if knowledge_base.url_texts:
            all_texts.extend([ensure_string(text, for_db=True) for text in knowledge_base.url_texts])
        
        knowledge_base.raw_text = "\n\n".join(all_texts)
    
    print(f"知識ベース更新完了: {len(knowledge_base.data) if knowledge_base.data is not None else 0} 行のデータ")

# アクティブなリソースのみを取得する関数
def get_active_resources(company_id=None):
    """アクティブなリソースのみを取得する"""
    active_sources = []
    
    # 会社IDが指定されている場合は、その会社のリソースのみを対象にする
    if company_id and company_id in knowledge_base.company_sources:
        company_sources = knowledge_base.company_sources[company_id]
        for source in company_sources:
            if source in knowledge_base.source_info and knowledge_base.source_info[source].get('active', True):
                active_sources.append(source)
    else:
        # 会社IDが指定されていない場合は、すべてのアクティブなリソースを返す
        for source in knowledge_base.sources.keys():
            if source in knowledge_base.source_info and knowledge_base.source_info[source].get('active', True):
                active_sources.append(source)
    
    return active_sources

# 知識ベース情報を取得する関数
def get_knowledge_base_info():
    """現在の知識ベースの情報を取得する"""
    # 最新の会社名を取得
    from ..company import DEFAULT_COMPANY_NAME as current_company_name
    
    # ソース情報を整形
    sources_info = []
    for source in knowledge_base.sources.keys():
        info = knowledge_base.source_info.get(source, {})
        source_type = "URL" if source.startswith(('http://', 'https://')) else "ファイル"
        
        sources_info.append({
            "name": source,
            "type": source_type,
            "timestamp": info.get('timestamp', '不明'),
            "active": info.get('active', True)
        })
    
    # アクティブなソースを取得
    active_sources = get_active_resources()
    
    return {
        "company_name": current_company_name,
        "total_sources": len(knowledge_base.sources),
        "active_sources": len(active_sources),
        "sources": sources_info,
        "data_size": len(knowledge_base.data) if knowledge_base.data is not None else 0,
        "columns": knowledge_base.columns if knowledge_base.data is not None else []
    }

def _update_knowledge_base_from_list(data_list, text, is_file=True, source_name=None, company_id=None):
    """データリストから知識ベースを更新する関数（DataFrameを使用しない）"""
    try:
        # データリストをDataFrameに変換
        if data_list:
            # 必要な列が存在することを確認
            for item in data_list:
                if 'file' not in item and source_name:
                    item['file'] = source_name
                
                # すべての値を文字列に変換（NULL値はそのまま保持）
                for key, value in item.items():
                    if value is not None:
                        item[key] = ensure_string(value)
            
            # DataFrameに変換
            df = pd.DataFrame(data_list)
            
            # 従来の関数を呼び出し
            _update_knowledge_base(df, text, is_file, source_name, company_id)
            
            logger.info(f"データリストから知識ベース更新完了: {len(data_list)} レコード")
        else:
            logger.warning("空のデータリストが提供されました")
            
    except Exception as e:
        logger.error(f"データリストからの知識ベース更新エラー: {str(e)}")
        raise 