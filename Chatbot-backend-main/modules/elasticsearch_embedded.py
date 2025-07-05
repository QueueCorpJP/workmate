"""
Embedded Elasticsearch for simplified setup
Pythonアプリケーション内でElasticsearchを起動
"""

import subprocess
import os
import time
import requests
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class EmbeddedElasticsearch:
    def __init__(self, port=9200):
        self.port = port
        self.process = None
        self.es_home = None
        
    def download_elasticsearch(self):
        """Elasticsearch をダウンロード（Windows用）"""
        # 簡単な実装 - 実際の本格実装では適切なダウンロード処理を追加
        logger.info("Elasticsearch をダウンロード中...")
        # ここで実際のダウンロード処理
        pass
        
    def start(self):
        """Elasticsearch を起動"""
        try:
            # 既に起動中かチェック
            if self.is_running():
                logger.info("Elasticsearch は既に起動中です")
                return True
                
            # 起動処理
            logger.info("Elasticsearch を起動中...")
            
            # Windows用の起動コマンド例
            if os.name == 'nt':  # Windows
                cmd = ['elasticsearch.bat']
            else:  # Linux/Mac
                cmd = ['elasticsearch']
                
            # 実際の起動処理
            # self.process = subprocess.Popen(cmd, ...)
            
            # 起動完了を待つ
            self.wait_for_startup()
            
            return True
            
        except Exception as e:
            logger.error(f"Elasticsearch 起動エラー: {e}")
            return False
            
    def is_running(self):
        """Elasticsearch が起動中かチェック"""
        try:
            response = requests.get(f"http://localhost:{self.port}", timeout=5)
            return response.status_code == 200
        except:
            return False
            
    def wait_for_startup(self, timeout=60):
        """起動完了を待つ"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_running():
                logger.info("Elasticsearch 起動完了")
                return True
            time.sleep(2)
        return False
        
    def stop(self):
        """Elasticsearch を停止"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            logger.info("Elasticsearch 停止完了")

# グローバルインスタンス
embedded_es = EmbeddedElasticsearch()

def start_embedded_elasticsearch():
    """Embedded Elasticsearch を起動"""
    return embedded_es.start()

def stop_embedded_elasticsearch():
    """Embedded Elasticsearch を停止"""
    embedded_es.stop() 