# 072 港の乗船案内：提出時報告

2026-10-17 JST。基点 8f2bc17b8c36b4304eb17de1a29e91e67a21cf57。

## 変更
world/region2_port.json と tools/build_region2_port.py の同じ案内1文字列ずつのみ。親がGitHub基点原文を取得し、旧文1回→新文1回の置換と全量一致を確認。その他ゲームファイルは変更しない。

## 実検証
固定Godot 4.7.2.stable.official.ed1daf0bf、クラウドLinux。通常mainのシーンを外部観測ハーネスで起動。船取得済み状態をimport_stateで注入した診断であり、新規開始から全編自然攻略した証明ではない。
初回下船、港務所への移動、2ページ会話・終了、退室再入室の再会話、中央桟橋から乗船・帰航・下船を入力イベントで確認。前後各132確認・15PNG。Codexが30PNGを目視。実画面にはVSync非対応警告あり。
親はZIP全量hashと報告・差分を確認。画像全30枚の親再目視は未実施。

正式 python tools/run_locked_checks.py：90.522秒、exit0、R-01〜R-08全PASS。既存予算維持、tests_ran=true/parser_failed=false/timed_out=false。
R-01 2tests/765assertions、R-02 5/946、R-03 2/73、R-04 1/293、R-05 2/79、R-06 2/87、R-07 A01〜A14、R-08 25/3046。
現行 check_second_region_coast.gd：1.550秒/180秒、SECOND_COAST_PASS checks=91、exit0。
保護26件一致。新規最終headlessログのSCRIPT ERROR/ERROR/WARNING/timeout0。
素材strict、港935項目、背景Godot94項目、背景Python検査も成功。

## 既知の未合格
追加の旧 tools/check_coastal_travel.gd は SCRIPT ERROR: Invalid access to property or key 'return_learned' on a base object of type 'Dictionary'. の後180秒timeout。
基点のfixtureが第1港のNPC占有位置[8,6]へ主人公を置き、import_state拒否後も検査を進める経路を静的確認。過去baseline原ログにも同じ失敗。今回の第2港案内文変更とは無関係。現行CI/凍結verifyの呼出し対象ではないが、未合格は保持。検査を変更・除外して成功化していない。

## 原資料
全量ZIPはLibraryに保全。親がサイズ/SHA256一致を確認済み。Driveへの追加保全は未実施。
- 原本・patch・画像・ログ：libfile_14701ba9ebf88191858d173f665cd058、6,342,704 bytes、814b9911baeaaa9dc4619e7bbe80c1f5aa349f59bc268867ef0cf0898df2fd5e
- 旧航路切分け：libfile_7358dbfa43e0819195dd3a84a4e203b1、458,127 bytes、7cdf3df5acfc58ccb0a53bc87c63e1b667b4d8e556c42f12c5a50549564f29fc
- 正式最終検証：libfile_8b5ac786f6808191bae155fb37486787、424,885 bytes、2da79893667ae544970a4c7b297dd6c4de3dd160e07c83c169d5472906144d6e

## 未達
GitHub正式提出SHAの全CI、PR、main反映は本記録作成時点で未実施。クラウドでの成功をCI成功と読み替えない。スキル2種取得不能、原稿以外の創作判断なし。既存資料・未追跡UIDはパッチへ混ぜていない。履歴改変/force pushなし。
