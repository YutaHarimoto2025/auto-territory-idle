import yaml
import json
import time
import os
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright, Playwright

class GameProcessor:
    def __init__(self, config_path="mapping.yaml", js_path="print_injection.js"):
        # 1. 設定のべた書き・読み込み
        width = 1000
        height = 800
        self._set_html(width, height)
        self.print_interval = 1000  # ミリ秒単位
        self.header_param = f"print_interval:{self.print_interval}, "
        
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.mapping = config['logging_variables']
        self.js_path = js_path

        # 2. 保存先の設定
        os.makedirs("results", exist_ok=True)
        self.csv_file = "results/game_log_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
        
        # 3. Playwrightの開始
        self._pw: Playwright = sync_playwright().start()
        self.browser = self._pw.chromium.launch(headless=False, args=["--start-maximized"])
        self.context = self.browser.new_context(no_viewport=True)
        self.page = self.context.new_page()
        
        # コンソールリスナーの登録
        self.page.on("console", self._handle_console)

    def setup(self, url="http://localhost:8000/game.html"):
        """ゲームの読み込みとJS注入"""
        print(f"URLへ移動中: {url}")
        self.page.goto(url)
        
        # ゲームの初期化（mainオブジェクトができるまで）を待機
        print("ゲームの初期化を待っています...")
        try:
            self.page.wait_for_function("(typeof _2c === 'function') && _2c(1) !== null", timeout=30000)
        except Exception as e:
            print(f"待機中にエラーが発生しました（時間がかかりすぎている可能性があります）: {e}")

        # JSの読み込みと置換・注入
        with open(self.js_path, "r", encoding="utf-8") as f:
            js_template = f.read()
        
        injection_js = js_template.replace("%MAPPING_JSON%", json.dumps(self.mapping)) \
                                  .replace("%INTERVAL%", str(self.print_interval))
        
        self.page.evaluate(injection_js)
        print("監視スクリプトを注入しました。")
        time.sleep(1) # 注入後の安定待ち

    # def action(self, action_type: str):
        
    #     return result

    def _handle_console(self, msg):
        """console.log から RL_DATA を抽出して処理"""
        if "RL_DATA:" in msg.text:
            try:
                json_str = msg.text.split("RL_DATA:")[1].strip()
                raw_data = json.loads(json_str)
                
                # 数値を float に変換し、小数点1桁で丸める
                float_data = {str(k): round(float(v), 1) for k, v in raw_data.items()}
                
                # --- 整形プリント出力 ---
                print("\n--- Current Game State---")
                keys = list(float_data.keys())
                for i, k in enumerate(keys):
                    if i == len(keys) - 1: # 最後だけ末尾のパイプなし
                        print(f"{k}: {float_data[k]}")
                    else:
                        print(f"{k}: {float_data[k]}", end=" | ")
                
                # CSV保存
                self._save_to_csv(float_data)

            except Exception as e:
                pass 
        
        if "CLICK_COORD:" in msg.text:
            print(f"EVENT: {msg.text}")

    def _save_to_csv(self, data_dict):
        """独自ヘッダー付きでCSVに保存"""
        is_first = not os.path.exists(self.csv_file)
        if is_first:
            # 新規作成時のみ、独自文字列を1行目に書き込む
            with open(self.csv_file, 'w', encoding='utf-8') as f:
                f.write(self.header_param + "\n")
        
        df = pd.DataFrame([data_dict])
        # 追記モード。初回のみヘッダー(カラム名)を付ける
        df.to_csv(self.csv_file, mode='a', header=is_first, index=False, encoding='utf-8')
        
    def _set_html(self, w:int, h:int):
        # テンプレートを読み込んで置換
        path_origin = "game-architecture/game_origin.html"
        path_saveto = "game-architecture/game.html"
        with open(path_origin, "r", encoding="utf-8") as f:
            html_content = f.read()

        # 値を埋め込む
        final_html = html_content.replace("{width}", str(w)).replace("{height}", str(h))

        # 保存（またはサーバーで返す）
        with open(path_saveto, "w", encoding="utf-8") as f:
            f.write(final_html)

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