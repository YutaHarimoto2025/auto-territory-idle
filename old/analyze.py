import time
from playwright.sync_api import sync_playwright

def run_rl_observation():
    with sync_playwright() as p:
        # 画面を表示して確認するため headless=False
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # ローカルサーバーにアクセス
        page.goto("http://localhost:8000/game.html")
        
        # ゲームが完全にロードされるまで少し待機
        page.wait_for_load_state("networkidle")
        time.sleep(3) 

        print("監視を開始します...")
        
        # ループさせてリアルタイムに数値を取得
        for _ in range(100):
            # page.evaluate を使ってブラウザ内部のJavaScript変数を読み取る
            # ここでは例として、以前見つけた _I2 オブジェクト内を想定
            # 正確な変数名が判明したら 'window._I2.money' などに書き換えます
            gold_value = page.evaluate("() => { 
                // ここに数値を返すJSを書く
                return typeof _I2 !== 'undefined' ? _I2._H2 : 'Loading...'; 
            }")
            
            print(f"現在の報酬(Gold相当): {gold_value}")
            
            # 1秒待機
            time.sleep(1)

        browser.close()

if __name__ == "__main__":
    run_rl_observation()