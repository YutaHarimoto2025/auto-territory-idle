import yaml
import json
import time
import os
import pandas as pd
import git
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, Playwright

from src import (Coordinater, ConsoleHandler)

class GameProcessor:
    def __init__(self):
        git_repo = git.Repo(Path(__file__).resolve(), search_parent_directories=True)
        working_dir = Path(git_repo.working_tree_dir)
        self.coordinater = Coordinater(working_dir)
        self.console_handler = ConsoleHandler(working_dir)
        
        # 3. Playwrightの開始
        self._pw: Playwright = sync_playwright().start()
        self.browser = self._pw.chromium.launch(headless=False, args=["--start-maximized"])
        self.context = self.browser.new_context(no_viewport=True)
        self.page = self.context.new_page()
        
        # コンソールリスナーの登録
        self.page.on("console", self.console_handler.console_step) #第一引数に ConsoleMessage を受け取る
        
        # CSVヘッダーに記録するパラメータ
        header_params = ["self.console_handler.print_interval", "self.coordinater.canvas_width", "self.coordinater.canvas_height"]
        self.console_handler.set_csv_header(str({p: eval(p) for p in header_params}))
    
    def setup(self, url="http://localhost:8000/game.html"):
        """ゲームの読み込みとJS注入"""
        self.page.goto(url)
        
        # ゲームの初期化（mainオブジェクトができるまで）を待機
        print("ゲームの初期化を待っています...")
        try:
            self.page.wait_for_function("(typeof _2c === 'function') && _2c(1) !== null", timeout=30000)
        except Exception as e:
            print(f"待機中にエラーが発生しました（時間がかかりすぎている可能性があります）: {e}")

        injection_js = self.console_handler.get_js_injection()
        self.page.evaluate(injection_js)
        print("監視スクリプトを注入しました。")
        time.sleep(1) # 注入後の安定待ち

    # def action(self, action_type: str):
        
    #     return result
            
    def close(self):
        print("ブラウザを終了します。")
        self.browser.close()
        self._pw.stop()

if __name__ == "__main__":
    # クラスのインスタンス化
    proc = GameProcessor()
    
    # 1. 起動と注入
    proc.setup()

    # 2. アクションの実行

    # 3. メインループ（監視継続）
    print("監視中... (results フォルダにCSVが保存されています)")
    try:
        while True:
            # Playwrightのイベントループを阻害しないための待機
            proc.page.wait_for_timeout(5000)
    except KeyboardInterrupt:
        print("\nユーザーにより停止されました。")
    finally:
        proc.close()