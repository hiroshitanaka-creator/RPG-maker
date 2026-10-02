# 第2地方の港町：依頼者原画

2026年10月1日、依頼者がChatGPTの画像生成で作成し、これまでの依頼者原画と同じ扱いで使うよう指示した7枚。原本は1バイトも変更しない。ファイルの実際の拡張子は `.PNG`。

| 原本 | 使用先 |
| --- | --- |
| FE4B1B12-C9B1-4DB0-B374-81F51D061BA6.PNG | 港町外観の目標。外観は部品を並べて作る |
| 75462BFD-D5F5-4BEC-94EF-2241C7A1D0C7.PNG | 宿屋の中 |
| 7BDBE31E-F3AF-49E2-AD04-6505CCEA796C.PNG | 道具屋の中 |
| C9A48E60-3050-4DE6-AB1F-5399C014323B.PNG | 武器屋の中 |
| A57472FD-36AF-4085-BA41-25B571A3F2AF.PNG | 防具屋の中。建物・店員・会話まで |
| FBE86B94-685C-4745-85C0-B45FF36DCCFF.PNG | 祠の中。石板の模様は飾り |
| 4D2815AA-E544-49BB-9714-0B9E8FB43D94.PNG | 港務所の中 |

寸法とSHA-256の全件一覧は `assets/source_records/region2-port-originals.json`。外観の無加工複製は `docs/reference/visual-targets/region2-port-town.png`、配置の提案は `docs/proposals/region2-port-layout.md`。

2026年10月2日の追加指示で、`9BC9CFCF-2A63-4939-83E5-0886F820494B.PNG`（住人10人）も使用する。正面の原画を基準に横・後ろ・歩行動作を生成し、原画自体は変更しない。生成記録は `assets/source_records/region2-port-generation.json`、変換記録は `assets/source_records/region2-port-assets.json`。

オアシスの村・第2地方の世界マップ・遺跡4階層・砂岩の巨像の7枚は、`docs/roadmap-v2.md` 付録Bへ将来用途を記録し、今回の港町では使わない。フォルダ作成用の空ファイル `.keep` は無視し、変更しない。

部品と室内背景の台帳は、既存の依頼者素材と同じ取り込み経路に合わせ、`assets/_incoming/owner-2026-09-26/supplement-2026-10-02-region2-port/` に置く同一バイトの保管コピーを原本として参照する。実際の受領場所はこのフォルダ、受領日は2026年10月1日である。元ファイルの移動・改変は行わない。
