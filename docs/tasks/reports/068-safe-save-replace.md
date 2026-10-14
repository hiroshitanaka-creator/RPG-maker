# 068 安全なセーブ置換・復旧の報告

2026-10-12。ローカル実装・Linux検証の報告。Windows実行と公式GitHub保存・PR・レビューは未達であり、タスク全体の完了ではない。

## 変更ファイル

- `scripts/game/game_session.gd`：save_game/load_gameと同責務の補助処理。
- `scripts/game/play_session_metrics.gd`：write_jsonとJSON候補の読取り補助。
- `test/unit/test_safe_save_replace.gd`、同名`.uid`：今回許可された新規テストとGodot 4.7.2生成UID。
- `docs/tasks/068-safe-save-replace.md`：状態行のみ。本文はc5229a1c6205dde4673835da716e95130ea91cd3の実物。
- この報告書。

基点はmain `9070038523ded3277fa45bf7615cf023aa08e786`。ローカルブランチは`codex/task-068-safe-save-replace`。開始時の未コミット変更はなし。追加コミット・push・GitHubへの書込み・PR・mergeは行っていない。066系列・既存067を取得・統合・再開していない。checkoutの`.agents/skills`は存在せず、保存修正に使える追加ローカルskillはなかった。

## 保存と復旧

1. 保存する文書の型情報を作る。既存`.tmp`だけが有効なときは、無効な`.bak`の整理成功を確認し、存在しない`.bak`へ`.tmp`を先に退避する。ここで失敗したら書込みへ進まない。
2. `.tmp`へ書込み、flush、エラー確認、読み戻し検証をする。読み戻しはセーブなら既存の全検証、write_jsonならJSONのDictionaryを検証する。この段階で失敗しても本物・有効な`.bak`は残す。
3. 本物があれば古い`.bak`を整理し、存在しない`.bak`へ本物をrenameする。整理失敗ではrenameへ進まない。続いて`.tmp`を空いた本物へrenameする。本物なしなら`.bak`を保持して`.tmp`を本物へrenameする。
4. 本物が確定してから`.bak`を削除する。最後の削除が失敗した場合もfalseを返すが、本物と`.bak`は残る。失敗時に`.tmp`を一律削除しない。

古い`.bak`を削除できるのは検証済み新`.tmp`ができた後なので、本物が破損していても最後の有効コピーは失わない。初回保存前に有効なコピーが一切ない場合、最初の書込み前の中断から復旧できるとは扱っていない。有効な`.tmp`だけが既にある場合の保全は別途検証した。

load_gameは本物→`.bak`→`.tmp`の順に、同じ候補読取り処理でJSON解析、SavedDocument.decode、位置補正、metrics、trial_id、数値正規化、型復元前後の全_valid_state、metrics再復元・型比較を行う。検証失敗は次候補へ進み、全部不正ならfalse。検証は候補ローカルで行い、position_relocatedも成功時だけ反映する。

復旧候補は型復元済みの状態・metrics・候補のtrial_idの有無から本物へ保存し直す。現在セッションのsave_gameを呼ばないので、別のarchive IDを混入させない。復旧保存失敗はfalseとし、その前には現在状態・計測・archive・保留中の操作に触れない。成功後のimport_state、archive.resume等は従来の処理を維持する。

## OS別の実行結果

| 検査 | Linux / Godot 4.7.2 | Windows |
| --- | --- | --- |
| 本物だけ有効 | PASS | 未実施 |
| 本物なし・bakだけ有効 | PASS、本物への再保存・再読込み | 未実施 |
| 本物なし・tmpだけ有効 | PASS、切詰め前保全・再保存・再読込み | 未実施 |
| 本物破損・bak有効 | PASS | 未実施 |
| 全部破損 | PASS、false・現在状態不変 | 未実施 |
| 候補順と保存途中の各ファイル配置 | PASS、12配置 | 未実施 |
| JSONとして正常でもdecode/metrics/trial_id/state/型情報が不正 | PASS、次候補へ移り副作用なし | 未実施 |
| 旧形式の省略、型付き配列・小数、候補IDあり/なし | PASS | 未実施 |
| 復旧保存失敗、現在状態・archive・保留操作不変 | PASS | 未実施 |
| save_game/write_jsonの実I/O中断・失敗 | PASS、112試行（各56） | 未実施 |

固定版Linux Godotは公式配布URLから取得し、既存CI指定のZIP SHA-256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`と一致。実行表示は`4.7.2.stable.official.ed1daf0bf`。最初からPATHにあった4.6.3は検証に使用していない。

新規GUTは8テスト・744アサーション成功。既存R-01〜R-08はすべてPASS。R-07はA01〜A14、R-08は新規を含む25テスト・3046アサーション成功。素材strictは問題なし、凍結26件一致。既存の型復元検査成功、位置補正検査は31部屋・199項目成功。

Linuxの中断・失敗注入112試行（save_game 56、write_json 56）が成功した。Linuxでは提出資料内のGDScriptプローブを別プロセスで実行し、straceで実際のopen/write/rename/unlinkにSIGKILLまたはEACCES/ENOSPCを注入した。本物と古いbak、本物破損と正常bak、tmpだけ、本物とbak破損でtmpだけ正常、完全な初回保存を、save_game/write_jsonのそれぞれで実行。中断直後のファイル原bytesとsyscall原ログを保存し、ゲームの有効コピーは別Godotプロセスで再読込みした。模擬ファイル配置だけの検査とは分けて記録している。OS停止・電源断の耐久試験やWindows実行の代用とはしていない。

最初の注入試行はGodotのログ整理に注入が当たり、検証器の期待と不一致になった。その後、プロセスごとのログ先を分離した。次の試行ではSIGKILLのstrace表記を検証器が誤判定したため修正した。両試行のコード・原ログも削除せず同梱。製品コードと既存検査はこの調整で変更していない。

## 実コマンドと原ログ

作業ディレクトリは`/workspace/RPG-maker`。`godot`は`/workspace/task068-tools/bin/godot`（固定版へのリンク）をPATHの先頭に置いた。XDG_CONFIG_HOME、XDG_CACHE_HOME、XDG_DATA_HOMEはそれぞれ書込み可能な`/workspace/task068-config`、`/workspace/task068-cache`、`/workspace/task068-data`を指定した。

```bash
godot --version
godot --headless --editor --import --quit
godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_safe_save_replace.gd -gexit
python tools/run_locked_checks.py
python tools/validate_assets.py --strict
godot --headless --path . --script res://tools/check_saved_value_types.gd
godot --headless --path . --script res://tools/check_saved_position_relocation.gd
python tools/check_frozen_files.py
python /workspace/task068-tools/native_checks.py
git diff --check
```

run_locked_checks.pyの既存全verifyと各300秒上限、型検査60秒・位置補正120秒上限を維持した。実引数・終了コードは提出ZIPの`commands.jsonl`、`native-v3/*/command.json`、各原ログにある。既存検査が生成したscope-lock-current.jsonは原bytesをZIPへ保存した後、作業ツリーでは元の原bytesへ戻した。最初のインポートはXDG_CONFIG_HOME未設定でエディタ設定保存エラーがあったため、書込み可能な設定先を指定して再実行し、エラーなしを確認した。最初の原ログも保存した。

## Windowsの残件と必要条件

この実行環境はLinuxで、Windowsホストへの接続先・資格情報・SSH設定がなく、PowerShell、Wine、QEMU、VirtualBox、libvirtと`/dev/kvm`もない。Windowsを実行したとは報告しない。Wineも使用していない。

必要なのは、親が利用できるWindowsホスト（NTFSの書込み可能な作業領域）、この6ファイルを反映した独立checkout、PowerShell・Python・固定版Godot。既存手順をそのまま利用できる。

```powershell
& tools/get_godot.ps1
. tools/prepare_scope_env.ps1
godot --headless --editor --import --quit
godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_safe_save_replace.gd -gexit
python tools/run_locked_checks.py
python tools/validate_assets.py --strict
python tools/check_frozen_files.py
```

既存get_godot.ps1はWindows ZIPの固定SHA-256 `731980f9608d61333e5baf54a2ef17210acc7a538446c0cb9969f002aca1e953`を照合する。上記により候補・中断配置・失敗時不変を実Windows上で確認できる。実保存プロセスの各操作間での強制停止とI/O失敗は、Windowsのデバッガで対象保存処理を停止してプロセスを終了する検証、およびFileShare.Noneのハンドルで本物/bak/tmpをロックする検証を別途行い、原ログを採取する必要がある。Linux用strace注入はWindowsでは未実行である。

## 自己点検・引継ぎ

- 保存/読込み責務以外のgame_session、write_json責務以外のmetricsは前後原bytes一致。ゲーム規則・形式・数値・画面・検査/期待値/締切を変えていない。
- 既存test、scope-lock、CI、schema、AGENTS、保護検査、README、decision-log等45追跡ファイルを基点bytesと照合して一致。凍結26件も前後一致。新規testだけ今回の明示許可対象。
- インポートが生成した対象外2UIDは成果差分に含めず、提出資料へ退避。新規テストのUIDだけを含める。
- 原bytes・変更差分・実コマンド・原ログ・OS別結果をLibrary ZIPで親へ引き渡す。Drive保全・公式GitHub保存と読み戻し・通常PR・hiroshitanaka-creatorへのCODEOWNERSレビュー要求は親の担当で未実行。CIの新しい全ジョブ結果も未取得。mainへはマージしない。


## 2026-10-15 JST：後続Windows検証・正式受入の追記

上記は2026-10-12の初回ローカル報告として全文保持する。この追記は後続のGitHub実物を照合して時点を補うもので、初回の「未実施」欄を当時の成功に書き換えない。

### 正式提出・レビュー・取込み
- 正式head：26cbdcc1849625bd2f890762216a3bbdb7d5346b。
- [PR #40](https://github.com/hiroshitanaka-creator/RPG-maker/pull/40) は、hiroshitanaka-creatorが2026-10-12 12:33:48 JSTにAPPROVED。その後、同日13:05:50 JSTにmainへ取込み済み。
- 取込SHA：e61ab37f9542648f25b731cd33924e11e134920b。
- PRに含まれた新規Windows workflowも依頼者の後続承認の範囲。既存workflow・既存検査を変更しない条件を維持した。

### Windowsの実結果
[Windows job 114658416918](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/38202397471/job/114658416918)の原ログで、Godot 4.7.2.stable.official.ed1daf0bf、068の8テスト／744アサーション、R-06の2テスト／87アサーションの成功を確認した。failed=0、pending=0、invalid=false、exit=0、tests_ran=true、parser_failed=false、timed_out=false。
本物だけ、bakだけ、tmpだけ、本物破損と正常bak、全候補破損(false)、途中段階のファイル配置を対象にしたWindows上の実ファイル操作である。プロセス強制終了や電源断の耐久試験の成功へ拡張しない。Linuxの112試行は上の初回報告とPR本文の記録であり、この追記で新規実行・原資料全件再照合をしたものではない。

### 取込後CI（当該取込SHAの結果）
| workflow | run | 結果 |
| --- | --- | --- |
| Windows セーブ置換・往復検証 | [38202397471](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/38202397471) | 1/1 success |
| Equipment Codec CI | [38202397480](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/38202397480) | 3/3 success |
| Equipment and Save CI | [38202397499](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/38202397499) | 14/14 success |
| 006 固定受入と最新回帰 | [38202397489](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/38202397489) | 17/17 success |
| CI | [38202397496](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/38202397496) | 3/3 success |

合計5 run・38 jobがcompleted/success。凍結受入job114658417424の原ログでR-01〜R-08全PASS、保護26件一致も確認した。過去の成功と今回の文書追記に起動するCIは別の結果として扱う。

### 記録の自己点検
今回の変更は068依頼書の状態行、当報告への追記、tasks/READMEとdecision-logへの記録だけ。初回本文・ゲームコード・テスト・期待値・締切・workflow・保護ファイル・066系列は変更しない。今回Godotや検査をローカル再実行していない。依頼書の「確認済み」は既に受入済みの068実装を指し、この文書PR自体のCI成功を先取りしない。
