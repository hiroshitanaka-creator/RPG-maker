# 保存専用I/O

通常ゲームはGodot/GDScriptのまま。ここは明示QA rootのOS操作だけを担う内部拡張で、codec、migration、phase、数量、UI、メモリ適用を持たない。

`dependencies.json`の公式godot-cpp完全commitとMIT本文を固定する。4.5 ABIを4.7.2でロードする。配布先はWindows x86_64/ローカルNTFS（Windows 10以降、UCRT標準搭載）とLinux x86_64。Linux提出物のglibc要求は配布manifest/依存実測へ記録する。全FS・UNC・reparse volumeへの保証はしない。UNC/namespace/ADS/予約名/末尾dot-spaceは拒否する。drive/case/非ASCII/空白/長いpathは専用検査で区別する。

開発環境だけにPython3/SCons4.10.0、Linux C++ compilerまたはWindows MSVC Build Tools/SDKが必要。配布は`addons/equipment_save_io`全体とGodot4.7.2。利用者へGNU導入、compiler、管理者、Developer Modeを要求しない。保護されたexport設定を変更せず、通常画面/保存/ロードには未接続。

```text
python -m pip install scons==4.10.0
python native/equipment_save_io/build.py --platform linux --output /dedicated/build-evidence
python native/equipment_save_io/build.py --platform windows --output C:/dedicated/build-evidence
```

WindowsはMSVC環境shellから実行。任意の`--cpp`も完全commitを照合。LinuxからのWindows QA配布物構築は`--mingw /dedicated/llvm-mingw`（公式llvm-mingw 20261006/UCRT/LLVM23.1.3）も使用できる。ソースは改変せず、旧bindingのcstdlib宣言を強制includeで補う。DLLはC++ runtimeを静的リンクし、Windows標準DLLだけへ依存する。build.jsonに実argv/exit/秒数/コンパイラ/hashを残す。各target600秒、CI15分を維持する。

rootをhandle/fdで保持し、各componentをreparse/O_NOFOLLOW・volumeで照合する。Windows directory/fileはdelete共有を与えず保持する。Linuxはroot fdからopenat/fstat、flock、O_EXCL、renameat2(RENAME_NOREPLACE)を使う。write_exactは部分write/EINTRを処理し、flush/closeのOS errorを返す。未確認の機能へ通常WRITE/rename fallbackしない。

WindowsはNtCreateFileのRootDirectory/OBJ_DONT_REPARSEとNtSetInformationFileの相対renameを用いる。drive root以降は親handleから解決し、各生存directory handleの属性・volumeを再確認する。lock/観測file/保持directoryのキーはCompareStringOrdinalのcase-insensitive比較へ統一する。API欠落は失敗にする。

writer.lockは生存handleでkernel lockを保持し、終了で解放する。PID/nonceは監査用。旧053 leaseの生存照会だけalive/dead/unknownで、確定dead以外拒否する。新regular leaseをexclusive renameで公開すると旧053のis_link検証が拒否する。既存symlink lease/owner/保存原物を削除しない。旧原物からの復旧はLinux実processで検査する。Windowsでは旧053自身が全pathを拒否する。

確定backup/出力へ置換・切詰めを許さず、lock所有下の未完tmp再利用とreceipt.tmp→receipt.json置換を別API契約にする。取引intent/候補照合の責任はGDScript側。namespaceへの悪意ある非協調操作や電源断/媒体故障の全耐久性をprocess kill検査の成功から推定しない。実ENOSPC/専用nested別volumeは専用領域提供が必要で、注入を実測と呼ばない。

配布物にはlicenses/も同梱する。godot-cpp MIT、LLVM Apache2/LLVM exception、MinGW-w64 runtime各本文とGCC runtime exceptionを原文で保持する。公式toolchain完全commitとarchive hashは今回検証のtoolchain-pins.jsonを参照。
