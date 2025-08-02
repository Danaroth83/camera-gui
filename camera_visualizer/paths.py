from pathlib import Path
import dotenv


def load_project_dir() -> Path:
    return Path(__file__).resolve().parents[1]

def load_data_path():
    dotenv.load_dotenv()
    return load_project_dir() / "data"


def main():
    print(load_project_dir())


if __name__ == "__main__":
    main()
