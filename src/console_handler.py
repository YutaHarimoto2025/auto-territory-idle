from __future__ import annotations
import json, os, yaml
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.coordinater import Coordinater

class ConsoleHandler:
    def __init__(self, working_dir:Path, coordinater:Coordinater):
        self.working_dir = working_dir
        self.coordinater = coordinater
        
        # 2. 保存先の設定
        os.makedirs(self.working_dir / "results", exist_ok=True)
        self.csv_file = self.working_dir / "results" / ("game_log_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv")
        self.header_str = ""
        
        mapping_yaml_path= self.working_dir / "mapping.yaml"
        self.injection_js_path= self.working_dir /"print_injection.js"
        
        with open(mapping_yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.mapping: dict = config['logging_variables']
        self.print_interval= 1000  # ミリ秒単位
        self.accelaration_factor = 1  # 生産加速倍率

    def console_step(self, msg):
        """console.log から RL_DATA を抽出して処理"""
        if "RL_DATA:" in msg.text:
            try:
                json_str = msg.text.split("RL_DATA:")[1].strip()
                raw_data = json.loads(json_str)
                
                # 数値を float に変換し、小数点1桁で丸める
                float_data = {str(k): round(float(v), 1) for k, v in raw_data.items()}
                
                # --- 整形プリント出力 ---
                print("\n [State] ", end="|")
                keys = list(float_data.keys())
                for i, k in enumerate(keys):
                    if i == len(keys) - 1: # 最後だけ末尾のパイプなし
                        print(f"{k}: {float_data[k]}")
                    else:
                        print(f"{k}: {float_data[k]}", end=" | ")
                
                # CSV保存
                self._save_to_csv(float_data)

            except Exception as e:
                print(f"Error processing RL_DATA: {e}") 
        
        if "CLICK_COORD:" in msg.text:
            try:
                json_str = msg.text.split("CLICK_COORD:")[1].strip()
                coord_data = json.loads(json_str)
                
                # Canvas座標を float として取得
                c_x = float(coord_data.get("x", 0))
                c_y = float(coord_data.get("y", 0))
                
                # Coordinator を使って World 座標へ変換
                w_x, w_y = self.coordinater.calc_c_to_w(c_x, c_y)
                
                # 表示 (小数点1桁に丸める)
                print(f"\n[Debug] Clicked on World : ({round(w_x, 2)}, {round(w_y, 2)}), Canvas: ({c_x}, {c_y})")
                
            except Exception as e:
                print(f"Error parsing CLICK_COORD: {e}")
            
    def set_csv_header(self, header_str:str):
        """CSVヘッダーを設定"""
        self.header_str = header_str
            
    def _save_to_csv(self, data_dict):
        """独自ヘッダー付きでCSVに保存"""
        is_first = not os.path.exists(self.csv_file)
        if is_first:
            # 新規作成時のみ、独自文字列を1行目に書き込む
            with open(self.csv_file, 'w', encoding='utf-8') as f:
                f.write(self.header_str + "\n")
        
        df = pd.DataFrame([data_dict])
        # 追記モード。初回のみヘッダー(カラム名)を付ける
        df.to_csv(self.csv_file, mode='a', header=is_first, index=False, encoding='utf-8')
        
    def get_js_injection(self):
        # JSの読み込みと置換・注入
        with open(self.injection_js_path, "r", encoding="utf-8") as f:
            js_template = f.read()
        
        injection_js = js_template.replace("%MAPPING_JSON%", json.dumps(self.mapping)) \
                                  .replace("%INTERVAL%", str(self.print_interval)) \
                                  .replace("%ACCELARATION%", str(self.accelaration_factor))
        return injection_js