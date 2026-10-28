# 083 撮影assertionの移行対応

083基点 `a4dc7c9d0d705f3181391fdccee4e4c825ddcaaf` の撮影補助の全 `48` castle_check呼出しを括弧・文字列を解釈して抽出。最新版と全式・順序が一致。コメントとroom4撮影入力1値以外のコードも一致する。実行時はループ展開によりjourneyが132条件となる。削除・省略・閾値/上限変更なし。

| ID | 元行→最新行 | 関数 / 実行モード | 固定版 | 最新版・後続 |
|---|---|---|---|---|
| CAP009-001 | 30→30 | picture / journey / details / restart-0〜4（共有部） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-002 | 31→31 | picture / journey / details / restart-0〜4（共有部） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-003 | 65→65 | picture / journey / details / restart-0〜4（共有部） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。旧[8,5]の遮蔽はAPI/実キーを別検査。 |
| CAP009-004 | 66→66 | picture / journey / details / restart-0〜4（共有部） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-005 | 87→87 | _run / journey / details / restart-0〜4（共有部） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-006 | 89→89 | _run / journey / details / restart-0〜4（共有部） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-007 | 92→92 | _run / journey / details / restart-0〜4（共有部） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-008 | 95→95 | _run / journey / details / restart-0〜4（共有部） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-009 | 105→105 | coast_to_village / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-010 | 109→109 | coast_to_village / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-011 | 123→123 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-012 | 125→125 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-013 | 126→126 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-014 | 129→129 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-015 | 131→131 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-016 | 135→135 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-017 | 142→144 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-018 | 145→147 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-019 | 147→149 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-020 | 148→150 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-021 | 150→152 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-022 | 151→153 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-023 | 152→154 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-024 | 155→157 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-025 | 158→160 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-026 | 161→163 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-027 | 162→164 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-028 | 164→166 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-029 | 165→167 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-030 | 166→168 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-031 | 168→170 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-032 | 169→171 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-033 | 170→172 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-034 | 171→173 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-035 | 173→175 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-036 | 176→178 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-037 | 178→180 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-038 | 180→182 | journey / journey（通常キー・通常メニュー） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-039 | 185→187 | restart_route / restart-0〜4 | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-040 | 190→192 | restart_route / restart-0〜4 | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-041 | 191→193 | restart_route / restart-0〜4 | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-042 | 193→195 | restart_route / restart-0〜4 | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-043 | 198→200 | details / details | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-044 | 200→202 | details / details | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-045 | 203→205 | details / details | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-046 | 206→208 | details / details | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-047 | 207→209 | details / details | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |
| CAP009-048 | 210→212 | finish / journey / details / restart-0〜4（共有部） | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。元assertion維持。 |

全式・元行・最新版行・CIジョブURLは assertion-migration.json。継承元・実行判定・既存の009/016世代対応表は083基点から全bytes不変。固定006の当時条件を最新の132件へ減らしたわけではなく、083基点の全呼出しを保持している。

旧room4-frontの「全画素可視」は新人物配置により旧[8,5]では成立しないため、最新の可視検査点を隣[7,5]に移す。元位置は後続の人物遮蔽検査で正負を確認する。通常キーjourney/counter-back、API入力撮影、追加した実方向キー撮影の3経路は区別する。

新規S10集中検査はCI未接続。毎回CI実行されるとの主張はしない。counter-back正例と故障注入の最新CIログ・終了値は ci-lifecycle-green-611c598.log / counter-back-negative-proof-611c598.json。各負例は実assertion FAIL・終了1・parse errorなし・timeoutなしを確認した。
