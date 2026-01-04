from pathlib import Path

class Coordinater:
    def __init__(self, working_dir: Path):
        #w座標はfloat, c座標はintで扱う
        
        self.working_dir = working_dir
        # キャンバス設定
        self.canvas_width = 1000
        self.canvas_height = 800
        self._set_html(w=self.canvas_width, h=self.canvas_height)
        self.click_range_x = (50, 950)  # C座標でのクリック可能x範囲
        self.click_range_y = (90, 730)  # C座標でのクリック可能y範囲
        
        # W座標原点がC座標でどこか (Scale=100の時)
        self.base_origin_c_x = 300.0
        self.base_origin_c_y = 200.0
        
        # セル1辺(C座標の長さ１)のベースピクセル数 (Scale=100の時)
        self.base_cell_size = 200.0
        
        # ズーム設定
        self.scales = sorted([100 /(1.1**i) for i in range(10)])
        self.scale_index = 9  # デフォルトはScale=100
        self.scale_index_lb_clicking = 7  # クリック操作に必要な最低ScaleIndex
        
        # 平行移動（W座標単位のオフセット）
        self.pan_w_x = 0.0
        self.pan_w_y = 0.0

    @property
    def current_scale(self):
        return self.scales[self.scale_index]

    @property
    def s_factor(self):
        """Scale / 100 の係数"""
        return self.current_scale / 100.0

    def calc_w_to_c(self, w_x, w_y):
        """W座標(世界) -> C座標(キャンバス)"""
        # 計算式: C = (BaseOrigin * S) + (W - PanW) * (BaseCell * S)
        # 共通項 (S) でまとめると以下の通り
        c_x = self.s_factor * (self.base_origin_c_x + (w_x - self.pan_w_x) * self.base_cell_size)
        c_y = self.s_factor * (self.base_origin_c_y + (w_y - self.pan_w_y) * self.base_cell_size)
        return int(c_x), int(c_y)

    def calc_c_to_w(self, c_x:int, c_y:int):
        """C座標(キャンバス) -> W座標(世界)"""
        # w_to_c の逆関数
        w_x = ((c_x / self.s_factor) - self.base_origin_c_x) / self.base_cell_size + self.pan_w_x
        w_y = ((c_y / self.s_factor) - self.base_origin_c_y) / self.base_cell_size + self.pan_w_y
        return w_x, w_y

    def handle_drag(self, delta_c_x:int, delta_c_y:int):
        """
        マウスドラッグによる平行移動を処理
        delta_c: キャンバス上でのピクセル移動量
        """
        # 1ピクセルあたりのW座標量を計算してオフセットを更新
        # delta_c = - delta_pan_w * (BaseCell * S)
        current_cell_px = self.base_cell_size * self.s_factor
        self.pan_w_x -= delta_c_x / current_cell_px
        self.pan_w_y -= delta_c_y / current_cell_px

    def zoom_in(self):
        if self.scale_index < len(self.scales) - 1:
            self.scale_index += 1
            return True
        return False

    def zoom_out(self):
        if self.scale_index > 0:
            self.scale_index -= 1
            return True
        return False
    
    def _set_html(self, w: int, h: int):
        # ルートからの相対パスを結合
        path_origin = self.working_dir / "game-architecture" / "game_origin.html"
        path_saveto = self.working_dir / "game-architecture" / "game.html"

        # ファイルの読み込み (pathlibなら open もスマート)
        if not path_origin.exists():
            print(f"Error: {path_origin} が見つかりません")
            return

        html_content = path_origin.read_text(encoding="utf-8")

        # 値を埋め込む
        final_html = html_content.replace("{width}", str(w)).replace("{height}", str(h))

        # 保存
        path_saveto.write_text(final_html, encoding="utf-8")
        print(f"HTMLを生成しました: {path_saveto}")