"""
Run setup: create run folder, copy config/parameter/input from fet_app to runs/run_XXX/.
"""
import json
import shutil
from datetime import datetime
from pathlib import Path


def get_fet_app_path() -> Path:
    """fet_app root: 3 levels up from this script (script/bin/run_setup.py)."""
    return Path(__file__).resolve().parent.parent.parent


def setup_run(fet_app_path: Path | None = None) -> Path:
    """
    Create run folder, copy config/parameter/input, return path to run config.
    """
    fet_app = fet_app_path or get_fet_app_path()
    config_path = fet_app / "run_config_file.json"
    runs_dir = fet_app / "runs"

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    run_yymm = config["RUN_SETTING"]["RUN_YYMM"]
    start_dt = datetime.now().strftime("%Y%m%d%H%M%S")
    run_name = f"run_{run_yymm}_{start_dt}"
    run_path = runs_dir / run_name

    # Create folder structure
    (run_path / "config").mkdir(parents=True, exist_ok=True)
    (run_path / "data" / "input").mkdir(parents=True, exist_ok=True)
    (run_path / "data" / "output").mkdir(parents=True, exist_ok=True)
    (run_path / "logs").mkdir(parents=True, exist_ok=True)
    (run_path / "parameter").mkdir(parents=True, exist_ok=True)

    # Copy config and add RUN_PATH
    run_config = config.copy()
    run_config["RUN_SETTING"] = run_config["RUN_SETTING"].copy()
    run_config["RUN_SETTING"]["RUN_PATH"] = str(run_path.resolve())

    run_config_path = run_path / "config" / "run_config_file.json"
    with open(run_config_path, "w", encoding="utf-8") as f:
        json.dump(run_config, f, indent=2, ensure_ascii=False)

    # Copy parameter files (*Param.xlsx, *Template.xlsx)
    for pattern in ("*Param.xlsx", "*Template.xlsx"):
        for src in fet_app.glob(pattern):
            if not src.name.startswith("~"):
                shutil.copy2(src, run_path / "parameter" / src.name)

    # Copy input data (*.csv)
    for src in fet_app.glob("*.csv"):
        shutil.copy2(src, run_path / "data" / "input" / src.name)

    return run_config_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create run folder and copy config/parameter/input")
    parser.add_argument("--fet-app", type=Path, default=None, help="Path to fet_app root")
    args = parser.parse_args()

    config_path = setup_run(args.fet_app)
    print(f"Run folder created. Config: {config_path}")
