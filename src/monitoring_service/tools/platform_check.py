from __future__ import annotations

import locale
import platform
import sys

from monitoring_service.paths import get_config_dir


def check_platform_compatibility() -> bool:
    print("=== Monitoring Service Platform Compatibility Check ===\n")

    system = platform.system()
    print(f"[INFO] Operating System: {system} {platform.release()}")

    python_version = sys.version_info
    print(f"[INFO] Python Version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("[WARNING] Python version too low, recommend Python 3.8+")
        return False
    print("[YES] Python version meets requirements")

    print(f"[INFO] Default encoding: {sys.getdefaultencoding()}")
    print(f"[INFO] Filesystem encoding: {sys.getfilesystemencoding()}")
    print(f"[INFO] Locale encoding: {locale.getpreferredencoding()}")
    if sys.getdefaultencoding().lower() != "utf-8":
        print("[WARNING] Default encoding is not UTF-8, may affect Chinese text")
    else:
        print("[YES] Encoding settings normal")

    config_dir = get_config_dir()
    required_files = [
        config_dir / "config.ini",
        config_dir / "token_mapping.json",
        config_dir / "monitored_users.json",
    ]

    print("\n[INFO] Checking required files:")
    all_files_exist = True
    for file_path in required_files:
        if file_path.exists():
            print(f"  [YES] {file_path}")
        else:
            print(f"  [NO] {file_path} - File missing")
            all_files_exist = False

    print("\n[INFO] Recommended startup method:")
    if system == "Windows":
        print("  Windows: Run start_monitor.bat")
    else:
        print("  macOS/Linux: Run ./start_monitor.sh")

    print(f"\n[INFO] Path handling test: {config_dir / 'test.json'}")
    print("\n=== Compatibility Check Complete ===")
    if all_files_exist:
        print("[SUCCESS] System compatibility is good, ready to run")
        return True
    print("[WARNING] Some files are missing and may affect startup")
    return False


def show_windows_specific_notes() -> None:
    if platform.system() == "Windows":
        print("\n=== Windows Users Special Notes ===")
        print("1. Recommend running in Command Prompt or Windows Terminal")
        print("2. For encoding issues, run: chcp 65001")
        print("3. If python command is unavailable, try py")


def main() -> None:
    success = check_platform_compatibility()
    show_windows_specific_notes()
    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

