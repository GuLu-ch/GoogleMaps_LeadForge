import argparse
import sys

from gmap_collector.app import create_application


def main() -> int:
    """程序入口。"""
    parser = argparse.ArgumentParser(description="Google Maps 商家信息采集工具")
    parser.add_argument("--check", action="store_true", help="只验证应用能否初始化，不显示窗口")
    args = parser.parse_args()

    application, window = create_application()
    if args.check:
        window.close()
        return 0

    window.show()
    return application.exec()


if __name__ == "__main__":
    sys.exit(main())
