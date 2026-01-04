(function() {
    // 以下のプレースホルダは Python 側で置換されます
    const mapping = %MAPPING_JSON%;
    const updateInterval = %INTERVAL%;
    const SPEED_MULTIPLIER = %ACCELARATION%; // n倍速

    if (window.rl_spy_active) return;
    window.rl_spy_active = true;

    // 計測開始
    window.rl_start_time = Date.now();
    window.rl_step_count = 1;

    setInterval(() => {
        try {
            // ゲームエンジンのメインインスタンス取得
            let main = (typeof _2c === 'function') ? _2c(1) : null;
            let result = {};
            // 経過時間とステップ数の計算
            result["step"] = window.rl_step_count;
            // result["elapsed_ms"] = (Date.now() - window.rl_start_time); //print_intervalでわかる
            window.rl_step_count++;

            // YAMLから渡されたマッピングに基づきデータ収集
            for (let key in mapping) {
                let info = mapping[key];
                let val = (info.scope === "main" && main) ? main[info.var] : global[info.var];
                result[key] = val;
            }

            // Python へ送信
            console.log("RL_DATA:" + JSON.stringify(result));
        } catch (e) {
            // ゲームループを止めないためにエラーは無視
        }
    }, updateInterval);

    window.addEventListener('mousedown', (e) => {
        // 画面上の絶対座標を表示
        console.log(`CLICK_COORD: {"x": ${e.clientX}, "y": ${e.clientY}}`);
    });

    // 生産加速ロジック
    const INTERVAL_MS = 100;    // 0.1秒ごとに処理
    
    console.log("Setting constant speed to: " + SPEED_MULTIPLIER + "x");

    setInterval(() => {
        const main = (typeof _2c === 'function') ? _2c(1) : null;
        if (!main) return;

        // 加速すべき「追加の秒数」を計算
        // 0.1秒の間に (3-1) * 0.1 = 0.2秒分をV3で足すと、実時間と合わせて3倍になる
        const extraTime = (INTERVAL_MS / 1000) * (SPEED_MULTIPLIER - 1);

        try {
            // 有料アイテムの Time Warp (関数 _x7) と同じ公式手順を実行
            // if (typeof _U3 === 'function') _U3(main, main); // 更新準備
            if (typeof _V3 === 'function') _V3(main, main, extraTime); // 資源加算
        } catch (e) {
            // エラー時はゲームを止めないよう無視
        }
    }, INTERVAL_MS);
})();