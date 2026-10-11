# 066 保存QA：ビルド生成物の厳密な段階別照合
状態：依頼登録・未着手
日付：2026-10-11 JST
対象：hiroshitanaka-creator/RPG-maker
担当：実装・テストはRPG-makerクラウドCodex GPT-6 Astra / High。GitHub保存・PRはルッカが公式GitHub接続（hiroshitanaka-ai）で行う。
作業ブランチ：codex/task-066-native-build-contract-v1
基点：e83bbce4018946da3e5f61f7b9f972474197f9e1（065提出）
## 承認と最優先条件
依頼者は2026-10-11 15:34 JST、21ファイルの新契約/CI変更と上記役割分担のA案を承認し、「規模の縮小・検査が簡単に通る様に裾を広げる対応は承認しません」と指定した。
変更集合を広げるだけ、成功期待値への変更、検査省略、時間延長、元失敗の隠蔽は禁止。許可した3生成物も無条件除外しない。固定入力の正規ビルド、原ログ、直後採取、以後不変の全条件で検査する。条件を満たせなければ未達として具体的な証拠を返し、勝手に縮小/緩和しない。
## 目的と現状
旧065の固定提出・コード・証拠を保持し、新しい契約世代で最新QAのビルド前・直後・検査後を連続して検証する。既存065へ後から意味を変えたパッチを当てない。
065は全51CI43成功8失敗。latest4jobのpins、固定059全10、capture12/27、12sample、065全56は成功したが、generation-contractの実worktree差分は失敗。latest両OS transaction本体も別途失敗。固定055/057両OStransactionも失敗。これを066成功で遡って取り消さない。
Linux隔離再現ではbuild後に現OS debug/release SOとmanifestの3件だけ変更、source38不変、両品binary checks7件ずつ成功。ただし実CIの差分pathは未確定、Windows同再現は未実施。
## 参照
AGENTS.md、docs/tasks/README.md、065/061依頼・報告、tools/fixtures/equipment-save-transaction-platform/のgeneration_contract.py/test_generation_contract.py/diagnostic_ci057.py/diagnostic_evidence059.py/run_ci.py/build.py/SConstructと現workflowを読む。素材規約/企画/台帳もリポジトリ指示に従い確認する。
最新mainには2ab6718f204af7196ce3dbb986ed9393d27cac92でCODEOWNERS追加済み。保護・依頼者レビュー境界を尊重する。本タスクではmainを無断統合しない。元基点を保つ。PR統合段階の最新main再統合・全検証は別途親が管理する。
## 変更可能な全21ファイル
変更：
1. .github/workflows/equipment-transaction-platform.yml
新規コード：
2. tools/fixtures/equipment-save-transaction-platform/native_build_contract_v1.py
3. tools/fixtures/equipment-save-transaction-platform/test_native_build_contract_v1.py
4. tools/fixtures/equipment-save-transaction-platform/diagnostic_ci_build_v1.py
5. tools/fixtures/equipment-save-transaction-platform/diagnostic_evidence_build_v1.py
文書：
6. docs/tasks/066-save-native-build-contract-v1.md（この依頼の状態のみ）
7. docs/tasks/reports/066-save-native-build-contract-v1.md
証拠（prefix docs/verification/save-native-build-contract-v1/）：
8. README.md
9. assertion-map.json
10. code-fixed-sha.txt
11. hashes.json
12. local-results.json
13. local-stdout.log
14. local-stderr.log
15. local-artifacts.tar.gz.b64
16. linux-results.json
17. linux-artifacts.tar.gz.b64
18. windows-results.json
19. windows-artifacts.tar.gz.b64
20. ci-results.json
21. scope-diff.json
未実行のOS/段階はNOT_RUNとし、架空archiveを作らない。ただし未実施を受入成功と扱わない。CI実行後の原証拠追加はこの集合内で行う。
docs/tasks/README.mdとdocs/decision-log.mdは親が担当し、Codexは変更しない。その他の旧ファイル/旧証拠は不変。
## 契約の必須条件
1. 旧065の登録/完成完全SHAで旧検査器・全期待値を固定し、完成範囲を検査する。最新の066承認集合は別に厳密検証。任意の将来変更を許さない。旧112 assertionと追加条件の継続/固定/新条件対応を一意に記録する。
2. ビルド前：実HEAD完全SHA、tracked集合/mode/blobと実bytes、source/QA/workflow/addonsの許可Git差分を検査。dirtyを拒否。shipped退避品はGit原blobと独立に照合する。期待binary4pathは固定列挙し、manifestやbuild.jsonから期待集合を作らない。build.py/SConstruct/依存pin/profileと実依存treeを検査。
3. ビルド直後：現OSのdebug/release2binary＋共有manifestだけが差分候補。他OS2binary、gdextension、その他addon/source/QA/workflowは不変。候補3件は差分必須ではなく、同一bytes再ビルドは正例。追加/削除/rename/mode/symlinkは拒否。manifestは厳密JSON、重複キー禁止、固定4entry、全hashを原bytesから独立再算出。
4. 実build argv/依存/exit/原stdout/stderrを保持し、非0・timeout・停止未確認・欠落を成功にしない。生成前/直後/検査後のsnapshotはテスト出力と別directoryで排他的作成し、各採取時hashをjobログへ先行記録。自己生成manifestとbuild.jsonの一致だけを出自の根拠にしない。
5. 検査後/診断後：sourceとrebuilt/shipped原bytesを先行snapshotに照合。失敗後も証拠採取するが、事前採取のやり直し、生成物をGit版へ戻して成功化、別clean checkoutだけを見て実QA対象を隠すことは禁止。
6. binary_checksのrebuilt/shipped各7件は実process/log/summaryがある場合だけ判定。run_ciはtransaction失敗で未到達になり得るため、未到達はNOT_RUNとする。本体の失敗伝播を保持し、contract単体成功を全体成功へすり替えない。
7. 新collectorはsnapshot原bytes・段階間参照hash・実process記録の完全集合をarchiveし、独立に再展開/再照合。元失敗と全受付の回収を維持する。
8. 信頼境界を正直に記す。固定入力と観測ビルド/段階間同一性を検査し、再現可能buildやcompiler正当性、同権限悪意processの完全改ざん防御は未実証なら主張しない。これは負例省略の口実にしない。
## CI配線・予算不変
新stepはmatrix.profile == 'latest'のみ。既存のshipped退避前後、既存build直後、検査/診断後へ採取点を置く。最新diagnosticだけ新runner/collectorへ切替。
fixed055/fixed057の手順、既存build/launch/保護/原artifact uploadの意味・各コマンド上限・15分jobを変更しない。scope059全10、capture12/27、12sample、065専用全56、原取引172/2178/97kill・16伝播・codec154/975・R8・保護26を維持する。CIが足りないから分母/期待数を減らさない。continue-on-error/黙ったskip/失敗選別再試行禁止。
## 必須正負・出口
- 両OS両phaseの正規buildと同一bytes正例。
- 事前dirty/shipped偽造/source/C++/build.py/SConstruct/pin/profile/GDScript/gdextension改変を個別拒否。
- 他OSbinary/未列挙addon/追加/削除/rename/symlink/mode改変拒否。
- manifest余分/欠落/重複キー/誤OS/hash不一致拒否。
- binary+manifest+build.json同時再hash偽装、build後/テスト中/診断中差替えを独立先行資料で拒否。
- snapshot欠落/順序逆転/別SHA・OS・job流用/schema downgrade拒否。
- build非0/timeout/未実行/原log欠落/停止未確認を非0またはNOT_RUNのまま保持。
- fixed055/057で新stepが発火しないこと。
- 元全assertion保持を実物比較し、全変更が21集合内・旧保護不変・依頼範囲不縮小と確認。
- CIは親が正確な提出SHAに対する全job終了結果を取得する。未実行検証は未実行と明記し、受入待ちにする。066単体成功でもF1/S3や保存全体・通常UI接続の受入としない。
## 提出と役割分担
MSI、小文字githubの両接続、creator認証経路は使わない。認証操作/資格情報取得/トークン転記をしない。クラウドCodexはローカル実装・実測と成果の引渡しを担当し、remote push/PR/mergeはしない。通常Git読取りが拒否されたら迂回せず報告。親は公式GitHubのai認証で登録/commit/PR/CI照会する。
親が保存できるよう変更全ファイルの原bytes、サイズ/SHA256/パス、基点、依頼状態の差分、実検証結果を引き渡す。専用ZIP/JSONをLibraryの正規機能で保存できれば、そのLibrary IDと検証結果を返す。ローカルpathだけで親が取得できると扱わない。機能がなければ引渡しの具体的な不足を報告し、可能な小さいUTF8ファイルは返信で原文を提示する。原証拠を短縮/再生成/捨てて転送しない。
親のAPI commit SHAはローカルcommit SHAと異なり得る。完成コード/ローカル実行/正式提出の各SHAを区別し、必要な証拠固定は親との段階的引渡し後に確定。API保存後の原bytes一致とauthor確認を行い、架空SHAを作らない。
