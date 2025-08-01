from pathlib import Path


def load_project_dir() -> Path:
    return Path().cwd().parent


def main():
    print(load_project_dir())


if __name__ == "__main__":
    main()
