(function() {
    // 以下のプレースホルダは Python 側で置換されます
    const mapping = %MAPPING_JSON%;
    const updateInterval = %INTERVAL%;

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
})();