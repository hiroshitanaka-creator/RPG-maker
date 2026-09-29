# スプリント5：港町

依頼者が森の塔とスイナの加入を採用し、次の区切りとして港町を指示した。転移呪文と船は、この次の区切りへ分ける。

## 実装した範囲

目標画像はIMG_1008。表示名は「港町」とし、正式な固有名を新たに決めていない。町の外観と8施設の計9マップ、町の外に9人・施設に8人を置いた。

- 山道から徒歩で港町へ出入りする。退出後は入口の1マス手前へ左向きで戻る。
- 石畳の通り、露店4軒、井戸、海岸の灯台、木の桟橋を置いた。桟橋以外の海へは歩いて入れない。
- 宿で4人のHP・MPを回復する。道具屋は既存の回復薬、武器屋は既存の補強剣を扱う。価格・性能は変更していない。
- 防具屋は建物・店員・会話まで。購入・装備の未決事項を今回埋めていない。
- 祠では既存の清めの処理を使う。民家、荷受け所、灯台の部屋へも歩いて入れる。
- 町と施設では戦闘が起きない。場所・向き・4人の状態・所持品を通常保存で保つ。
- 船の取得・航行、転移呪文の取得・実行は追加していない。桟橋の停泊場所は次の区切りで船を置くために残している。

原画そのものをマップに貼り付けず、登録済み素材を配置した。桟橋2素材は、既存の橋の中央の木目を切り出して作り、natural.gplの既存64色以内へそろえた。元の画像と共通パレットは変更していない。

## 確認画像

[目標と全体配置の比較](verification/sprint5-port-town/target-comparison.png)の右側は本番配置データから描いた全体図。実ゲームの画像は次のとおり。

- [世界マップの入口](verification/sprint5-port-town/runtime/01-world-port.png)、[町へ入った直後](verification/sprint5-port-town/runtime/02-town-entrance.png)
- [宿屋](verification/sprint5-port-town/runtime/03-inn.png)、[露店の広場](verification/sprint5-port-town/runtime/04-market.png)
- [道具屋](verification/sprint5-port-town/runtime/05-item-shop.png)、[武器屋](verification/sprint5-port-town/runtime/06-weapon-shop.png)、[防具屋](verification/sprint5-port-town/runtime/07-armor-shop.png)
- [祠](verification/sprint5-port-town/runtime/08-shrine.png)、[民家](verification/sprint5-port-town/runtime/09-home.png)、[荷受け所](verification/sprint5-port-town/runtime/10-harbor-office.png)
- [灯台の部屋](verification/sprint5-port-town/runtime/11-lighthouse-room.png)、[灯台前の海岸](verification/sprint5-port-town/runtime/12-lighthouse-coast.png)
- [上の桟橋](verification/sprint5-port-town/runtime/13-upper-pier.png)、[下の桟橋](verification/sprint5-port-town/runtime/14-lower-pier.png)、[山道へ戻った直後](verification/sprint5-port-town/runtime/15-return-world.png)

## 追加検査の範囲

依頼者が今回、次の3本の作成・実行を明示承認した。既存検査・R-01〜R-08・保護ファイル・合否条件・上限は変更しない。

1. `tools/check_port_town.py`：全施設と桟橋への到達、海への侵入防止、素材参照、原画一致を確認する。
2. `tools/prepare_port_departure.gd`：採用済みの通常操作経路で新規開始から村・洞窟・城・森の塔を通過し、山道で通常保存する。保存内容は書き換えない。
3. `tools/capture_port_town.gd`：上の保存のSHA-256を照合し、隔離した保存スロットへ同じバイトを複製する。タイトル画面の「手動セーブから再開」で読み込み、港町の出入り・全施設・会話・買い物・回復・保存復元・非戦闘を通常操作で確認し撮影する。

前の区切りの到達検査と、港町の検査を分けている。双方とも180秒・3,000入力・600歩の上限を維持し、時間や入力数を増やして合格させていない。撮影時のみ垂直同期の待ちを外し、ゲーム内の移動速度は変えない。検査中の保存はユーザーの通常保存とは別のスロットを使う。

## 実行結果

- `python tools/check_erosion_costumes_registered.py`：比較先を9d9fc2eに固定した検査が成功。192合成シート・1,440コマ・追加376画像。既存の判定式24件は読み取り先以外が一致する。
- `python tools/check_port_town.py`：9マップ・町の住人9人・16扉接続、桟橋と海岸の到達、海への侵入防止、原画のバイト一致が成功。
- `prepare_port_departure.gd`：通常到達84項目とR-07の14項目が成功。位置・所持品・仲間を注入せず開始保存を作成した。
- `capture_port_town.gd`：65項目・実画面15枚が成功。宿、買い物、保存復元、全施設の出入り、町内の非戦闘、人物の画素が90%以上見えることを確認した。
- `python tools/validate_assets.py --strict`：1,052画像・14音・3パレット・2字体が成功。
- `python tools/check_frozen_files.py`：26件一致。
- `python3 D:/Codex/.codex/scope-lock/scripts/verify_cli.py --quiet .`：R-01〜R-08すべて成功。結果は `docs/verification/sprint5-port-town/r01-r08.txt`。

追加検査では、灯台前の岩の通行阻害と、入場直後の場所名による主人公の隠れを見つけた。岩を1マス移し、港町の到着位置を1マス奥へ移して修正した。検査の合格条件は緩めていない。CIはpush後に全ジョブの終了を確認して報告する。

## 変更ファイル

- `world/first_region.json`、`world/interiors.json`、`world/first_region_visuals.json`：港町・扉・入口・桟橋・住人。
- `scripts/world/first_region.gd`、`scripts/world/first_region_view.gd`、`scripts/ui/first_region_atlas.gd`、`scripts/game/game_session.gd`：出入り・表示・保存条件・町内の非戦闘・祠。
- `assets/objects/port_pier_deck.png`、`assets/objects/port_pier_edge.png`、`assets/registry.json`、`assets/source_records/port-town.json`：桟橋と出所。
- `tools/build_port_town.py` と上記の追加検査3本：再現・確認画像・検査。
- 参考画像のREADME、計画書、この報告書と確認画像。

村・洞窟・城・森の塔の既存配置は変更していないことを、港町追加前のJSONとの内容比較で確認した。森の塔の見た目の3点は計画書の「見た目の仕上げ」に記録するだけにとどめた。

## 今回の境界

港町の確認画像を報告して止まる。転移呪文と船は次の区切り。港町の見た目の採否、防具の購入・装備、全体の難易度や60時間の実測は今回の機械検査で完了と扱わない。
