from utils.overview import build_overview


def main():
    print("正在加载数据并构建数据概览...（首次启动较慢）")
    build_overview()


if __name__ == "__main__":
    main()