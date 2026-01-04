//アクション定義 既存メソッドでクリックを再現しようとしたが，無理だった
window.game_action = function(type, tileIndex = 0) {
    try {
        let main = (typeof _2c === 'function') ? _2c(1) : null;
        if (!main) return "Error: main not found";

        switch(type) {
            case "build_wheat":
                // 1. 建築状態をセット (これをしないと関数が拒否することがある)
                main._Ic[9] = 1;  // Build Mode ON
                main._Ic[10] = 2; // Wheat (ID:2)

                // 2. 「上位の建設スクリプト」を直接実行する
                // 解析の結果、このゲームでは _I2._a3[157] 付近に
                // 「指定されたタイルに今選んでいる建物を建てる」ロジックがあります。
                // 番号はビルドにより変わるため、以下の「高レイヤー命令」を試します。
                
                // 方法A: マップクリック処理をエミュレート (最も安全)
                // _I2._a3[157] は多くの Territory Idle クローンで「マップタイルクリック」のIDです
                // 引数: (self, other, tileIndex)
                if (typeof _I2._a3[157] === 'function') {
                    _I2._a3[157](main, main, tileIndex);
                    return `Executed High-Level Build on Tile ${tileIndex}`;
                }

                // 方法B: 建設確定スクリプトを探して実行
                // 内部で global._fd (Gold) を減らしている関数を叩く
                return "Error: High-level function not found. Use Physical Click.";

            case "hire_worker":
                // 雇用はUI更新を伴うスクリプトを叩く
                // 雇用コスト(global._pb)をチェックして実行する上位関数
                if (typeof _k4 === 'function') {
                    _k4(main, main, 1, 0); 
                    return "Success: Worker hired via _k4";
                }
                return "Error: hire function _k4 not found";
        }
    } catch(e) {
        return "Action Error: " + e.message;
    }
};
// スクリプト呼び出しの監視
window.spy_scripts = function() {
    _I2._a3.forEach((originalFn, index) => {
        _I2._a3[index] = function() {
            if (index > 100 && index < 300) { // 核心的なロジックはこの範囲に多い
                console.log(`SCRIPT_CALLED: Index ${index}`);
            }
            return originalFn.apply(this, arguments);
        };
    });
    console.log("Spying started. Please build a Wheat Field now!");
};
window.spy_scripts();