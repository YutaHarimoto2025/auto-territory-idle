import os
from playwright.sync_api import sync_playwright

def download_assets():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # 通信が発生したファイルをすべて保存する仕掛け
        def handle_response(response):
            url = response.url
            # if "game299284.konggames.com" in url: # ゲームのサーバーのみ対象
            # URLからローカルのパスを作成
            relative_path = url.split("live/")[-1].split("?")[0]
            if not relative_path or relative_path.endswith("/"): return
            
            path = os.path.join("game-architecture", relative_path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # 保存
            with open(path, "wb") as f:
                f.write(response.body())
            print(f"Saved: {relative_path}")

        page.on("response", handle_response)
        
        # ゲームページへアクセス（ここで全ファイルが読み込まれる）
        page.goto("https://game299284.konggames.com/gamez/0029/9284/live/game.html", wait_until="networkidle")
        
        browser.close()

if __name__ == "__main__":
    download_assets()