"""
Entry point: run setup (create run folder, copy files) then execute run_main.
"""
import json
from pathlib import Path

from run_main import main as run_main
from run_setup import setup_run


def main():
    config_path = setup_run()
    print(f"Starting main with config: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    run_main(run_config=config)


if __name__ == "__main__":
    main()
