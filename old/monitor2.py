import yaml
import json
import time
import os
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

# YAMLの読み込み
with open("mapping.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
mapping = config['logging_variables']
print_interval = 1000  # ミリ秒単位
header_param = f"print_interval:{print_interval}, "

os.makedirs("results", exist_ok=True)
CSV_FILE = "results/game_log_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
        
def save_to_csv(data_dict):
    is_first = not os.path.exists(CSV_FILE)
    if is_first:
        # 新規作成時のみ、独自文字列を書き込む
        with open(CSV_FILE, 'w', encoding='utf-8') as f:
            f.write(header_param + "\n")
    df = pd.DataFrame([data_dict])
    # 追記モードで保存
    df.to_csv(CSV_FILE, mode='a', header=is_first, index=False)

def handle_console(msg):

    if "RL_DATA:" in msg.text:
        try:
            # JSON文字列を抽出
            json_str = msg.text.split("RL_DATA:")[1].strip()
            raw_data = json.loads(json_str)
            
            # 【リクエスト】str: float の辞書に変換し、小数点1桁で表示
            float_data = {str(k): round(float(v), 1) for k, v in raw_data.items()}
            
            # プリント出力　改行せず
            print("\n--- Current Game State---")
            for k, v in float_data.items():
                #最後だけ|~なし
                if k == list(float_data.keys())[-1]:
                    print(f"{k}: {v}")
                else:
                    print(f"{k}: {v}", end=" | ")
            
            
            # 強化学習で使うときはこの float_data をそのまま返せます
            # return float_data
            save_to_csv(float_data)

        except Exception as e:
            pass # 解析失敗はスルー
    
    # 【デバッグ用】ブラウザで console.log されたものをすべて Python ターミナルに出す
    # これで "RL_DATA:" が出ているか確認してください
    # print(f"【DEBUG】 {msg.text}")

def run_monitor():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        context = browser.new_context(no_viewport=True) 
        page = context.new_page()

        # 重要：goto の前にリスナーを登録！
        page.on("console", handle_console)

        print("ゲームを読み込んでいます...")
        page.goto("http://localhost:8000/game.html")
        
        # ゲームの起動待ち（GameMakerの初期化）
        page.wait_for_timeout(2000)

        # 2. 外部JSファイルを読み込み、プレースホルダを置換
        with open("print_injection.js", "r", encoding="utf-8") as f:
            js_template = f.read()
        
        injection_js = js_template.replace("%MAPPING_JSON%", json.dumps(mapping)) \
                                  .replace("%INTERVAL%", str(print_interval))

        print("監視スクリプトを注入します...")
        page.evaluate(injection_js) #開発者ツールのConsoleで実行する内容
        
        res1 = page.evaluate("window.game_action('build_wheat')")
        res2 = page.evaluate("window.game_action('hire_worker')")
        print("test",res1, res2)

        # Python側のメインループ（Playwrightのイベントを邪魔しないように待機）
        print("監視中... (Pythonターミナルを確認してください)")
        while True:
            page.wait_for_timeout(5000)

if __name__ == "__main__":
    run_monitor()