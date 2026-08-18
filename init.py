from pathlib import Path
import subprocess
import sys

WORKSPACE_DIRS = [
    "_workingspace/log",
    "_workingspace/diary",
    "_workingspace/plans",
]


def init() -> None:
    print("dna_kernel — 初期セットアップ")
    print()

    print("_workingspace/ ディレクトリを確認します...")
    for d in WORKSPACE_DIRS:
        path = Path(d)
        if not path.exists():
            path.mkdir(parents=True)
            (path / ".gitkeep").touch()
            print(f"  作成: {d}/")
        else:
            print(f"  確認: {d}/ (存在)")

    print()
    print("ホーム config（会話言語）を確認します...")
    script = Path(__file__).resolve().parent / "tools" / "kernel" / "user_prefs.py"
    subprocess.run([sys.executable, str(script), "init-config"], check=False)

    print()
    print("セットアップ完了。以下のツールが使えます:")
    print("  uv run python tools/kernel/workspace_audit_log.py append '本文'")
    print("  uv run python tools/kernel/json_weighted_pick.py <file.json> -p <path>")
    print("  uv run python tools/kernel/user_prefs.py show conversation.language")
    print()
    print("導入プロファイル:")
    print("  Rule-only   : ルール正本と各AIツール向け設定を統一")
    print("  Governance  : 完了判定・計画検査・査証ログまで統一")
    print("  Full        : onboarding・user-locale・補助処理まで利用")
    print("依存性: Python 3.11以上。uvは任意、日常のRulesync生成にNode.jsは不要です。")
    print()
    print("ルール再生成の標準手順（generate の後に sync 必須）:")
    print("  python tools/install_rulesync.py")
    print("  python tools/rulesync.py generate --dry-run")
    print("  python tools/rulesync.py generate")
    print("  python tools/rulesync.py generate --check")
    print("  uv run python tools/kernel/user_prefs.py sync")


if __name__ == "__main__":
    init()
