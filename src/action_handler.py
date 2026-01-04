from __future__ import annotations
from playwright.sync_api import sync_playwright, Page, Playwright
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.coordinater import Coordinater

class ActionHandler:
    def __init__(self, page: Page, coordinator: Coordinater):
        self.page = page
        self.coordinator = coordinator
        self.time_sleep = 0.1#0.035  # アクション後の待機時間（秒）
        
        # 「ワールド座標（タイル数）」の残差を持つ
        self.error_w_x = 0.0
        self.error_w_y = 0.0

    def click_world(self, w_x, w_y):
        """World座標を指定してクリック"""
        c_x, c_y = self.coordinator.calc_w_to_c(w_x, w_y)
        self.page.mouse.click(c_x, c_y, delay=self.time_sleep*1000) #2フレームは必要
        print(f"[Action] Clicked World: ({w_x}, {w_y})")
        time.sleep(self.time_sleep) #2フレあれば安定

    def drag_world(self, delta_w_x, delta_w_y):
        # time.sleep(0.5) #クリック直後にドラッグすると不安定になるため少し待機
        
        # 前回の残差を加算
        delta_w_x += self.error_w_x
        delta_w_y += self.error_w_y
        # 1. 画面中心（スタート地点）の計算
        start_c_x = int(self.coordinator.canvas_width / 2)
        start_c_y = int(self.coordinator.canvas_height / 2)

        # 2. Worldの移動量をCanvasのピクセル量に変換
        # 1タイルあたりのピクセル数 = base_cell_size * s_factor
        current_cell_px = self.coordinator.base_cell_size * self.coordinator.s_factor
        
        # ドラッグ距離（ピクセル）を計算
        # 画面を右に5タイル動かしたいなら、マウスは右に (5 * タイル幅) ピクセル動かす
        delta_c_x = round(delta_w_x * current_cell_px)
        delta_c_y = round(delta_w_y * current_cell_px)
        self.error_w_x = delta_w_x - (delta_c_x / current_cell_px)
        self.error_w_y = delta_w_y - (delta_c_y / current_cell_px)

        end_c_x = start_c_x + delta_c_x
        end_c_y = start_c_y + delta_c_y

        # 3. Playwrightで操作
        self.page.mouse.move(start_c_x, start_c_y)
        self.page.mouse.down(button="right")
        time.sleep(self.time_sleep)
        self.page.mouse.move(end_c_x, end_c_y, steps=5)
        self.page.mouse.move(end_c_x, end_c_y)
        self.page.mouse.up(button="right")
        time.sleep(self.time_sleep)

        # 4. Coordinatorの内部状態（パン）を更新
        # 注意: 画面を「右」にドラッグすると、カメラの基準点(pan)は「左」に移動する
        self.coordinator.handle_drag(delta_c_x, delta_c_y)
        
        print(f"[Action] Dragged World Delta: ({delta_w_x}, {delta_w_y}), retained error=({self.error_w_x}, {self.error_w_y})")
        
    def zoom_in(self, times=1):
        """拡大: Ctrl++ 送信と内部数値更新"""
        success_count = 0
        for _ in range(times):
            if self.coordinator.zoom_in():
                # Ctrl++ を送信
                self.page.keyboard.press("Control++", delay=self.time_sleep*1000) #ctrl + ^ だがなぜか ctrl + +
                time.sleep(self.time_sleep)
                success_count += 1
            else:
                # これ以上拡大できない場合は中断
                break
        print(f"[Action] Zoom In: success_count={success_count}")
        return success_count

    def zoom_out(self, times=1):
        """縮小: 指定回数実行し、実際に成功した回数を返す"""
        success_count = 0
        for _ in range(times):
            if self.coordinator.zoom_out():
                # Ctrl+- を送信
                self.page.keyboard.press("Control+-", delay=self.time_sleep*1000)
                time.sleep(self.time_sleep)
                success_count += 1
            else:
                # これ以上縮小できない場合は中断
                break
        print(f"[Action] Zoom Out: success_count={success_count}")
        return success_count
    
    # 統合メソッド gemini作----------------------------------------------------------
    def click_world_points(self, targets: list[tuple[float, float]]):
        """
        一連のWorld座標を順にクリックする統合メソッド。
        ターゲットが範囲外であったり、スケールが不足している場合は、
        自動的にズームアウト、移動（ドラッグ）、ズームインを行って調整します。
        """
        # Coordinaterから設定を取得
        range_x = self.coordinator.click_range_x
        range_y = self.coordinator.click_range_y
        min_scale_index = self.coordinator.scale_index_lb_clicking

        for w_x, w_y in targets:
            # 1. 現時点でのCanvas座標を計算
            c_x, c_y = self.coordinator.calc_w_to_c(w_x, w_y)
            
            # 判定: 範囲内かつスケールが十分か
            in_range = (range_x[0] <= c_x <= range_x[1]) and (range_y[0] <= c_y <= range_y[1])
            scale_ok = (self.coordinator.scale_index >= min_scale_index)

            # 2. 調整が必要な場合
            if not (in_range and scale_ok):
                print(f"[Action] Adjusting view for target World:({w_x}, {w_y})")
                
                # A. 範囲外の場合、移動効率を最大化するために一旦ズームアウト
                if not in_range:
                    current_scale = self.coordinator.scale_index
                    if current_scale > 0:
                        self.zoom_out(current_scale) # scale_indexを0にする
                
                # B. ドラッグ: ターゲットを画面の中央（最も安全な位置）へ持ってくる
                # ズームアウト後の座標で再計算
                c_x, c_y = self.coordinator.calc_w_to_c(w_x, w_y)
                center_c_x = self.coordinator.canvas_width / 2
                center_c_y = self.coordinator.canvas_height / 2
                
                # ターゲットを中央へ動かすためのピクセル差分 (delta = センター - 現在地)
                diff_px_x = center_c_x - c_x
                diff_px_y = center_c_y - c_y
                
                # ワールド座標の移動量に変換
                cell_px = self.coordinator.base_cell_size * self.coordinator.s_factor
                total_delta_w_x = diff_px_x / cell_px
                total_delta_w_y = diff_px_y / cell_px
                
                # 指定範囲内に収まるよう分割ドラッグを実行
                self._multi_step_drag(total_delta_w_x, total_delta_w_y)
                
                # C. スケールを目標値まで戻す
                needed_zoom = min_scale_index - self.coordinator.scale_index
                if needed_zoom > 0:
                    self.zoom_in(needed_zoom)

            # 3. 実行（調整後は必ず範囲内かつ適切なスケールになります）
            self.click_world(w_x, w_y)

    def _multi_step_drag(self, total_delta_w_x, total_delta_w_y):
        """
        ドラッグの移動先 (end_c_x, y) が常に click_range 内に収まるように、
        必要に応じて分割して drag_world を呼び出します。
        """
        range_x = self.coordinator.click_range_x
        range_y = self.coordinator.click_range_y
        start_c_x = self.coordinator.canvas_width / 2
        start_c_y = self.coordinator.canvas_height / 2
        
        # 1回で移動可能な最大ピクセル量 (中心からクリック可能範囲の境界まで)
        # これを超えると drag_world 内の end_c_x, y が範囲外になります
        max_px_x = min(range_x[1] - start_c_x, start_c_x - range_x[0])
        max_px_y = min(range_y[1] - start_c_y, start_c_y - range_y[0])

        rem_w_x = total_delta_w_x
        rem_w_y = total_delta_w_y
        
        # 移動すべき残量がなくなるまでループ
        while abs(rem_w_x) > 1e-9 or abs(rem_w_y) > 1e-9:
            current_cell_px = self.coordinator.base_cell_size * self.coordinator.s_factor
            
            # X方向のステップ決定
            step_w_x = rem_w_x
            step_c_x = step_w_x * current_cell_px
            if abs(step_c_x) > max_px_x:
                step_c_x = max_px_x if step_c_x > 0 else -max_px_x
                step_w_x = step_c_x / current_cell_px

            # Y方向のステップ決定
            step_w_y = rem_w_y
            step_c_y = step_w_y * current_cell_px
            if abs(step_c_y) > max_px_y:
                step_c_y = max_px_y if step_c_y > 0 else -max_px_y
                step_w_y = step_c_y / current_cell_px
            
            # 分割した1ステップ分を実行
            self.drag_world(step_w_x, step_w_y)
            
            # 残量を更新
            rem_w_x -= step_w_x
            rem_w_y -= step_w_y