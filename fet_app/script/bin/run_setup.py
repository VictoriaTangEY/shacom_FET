import json
import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd

INPUT_INSTRUMENT_FILE = "instrument_table.csv"


def get_fet_app_path() -> Path:
    """fet_app root: 3 levels up from this script (script/bin/run_setup.py)."""
    return Path(__file__).resolve().parent.parent.parent


def _parse_reporting_date_to_yymmdd(raw_value) -> int:
    """Parse REPORTING_DATE (e.g. DD/MM/YYYY) to YYYYMMDD integer."""
    s = str(raw_value).strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y%m%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return int(dt.strftime("%Y%m%d"))
        except ValueError:
            continue
    raise ValueError(f"Cannot parse REPORTING_DATE: {raw_value}")


def _get_run_yymm_from_input(fet_app: Path) -> int:
    """Read REPORTING_DATE from instrument_table.csv first row, return as YYYYMMDD."""
    input_path = fet_app / INPUT_INSTRUMENT_FILE
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    df.columns = [str(c).strip() for c in df.columns]
    if "REPORTING_DATE" not in df.columns:
        raise ValueError(f"Column REPORTING_DATE not found in {INPUT_INSTRUMENT_FILE}")

    raw_date = df["REPORTING_DATE"].iloc[0]
    return _parse_reporting_date_to_yymmdd(raw_date)


def setup_run(fet_app_path: Path | None = None) -> Path:
    """
    Create run folder, copy parameter/input from fet_app to runs/run_XXX/.
    RUN_YYMM is derived from REPORTING_DATE in instrument_table.csv.
    Returns path to run config file (run_path/config/run_config_file.json).
    """
    fet_app = fet_app_path or get_fet_app_path()
    runs_dir = fet_app / "runs"

    run_yymm = _get_run_yymm_from_input(fet_app)
    start_dt = datetime.now().strftime("%Y%m%d%H%M%S")
    run_name = f"run_{run_yymm}_{start_dt}"
    run_path = runs_dir / run_name

    (run_path / "config").mkdir(parents=True, exist_ok=True)
    (run_path / "data" / "input").mkdir(parents=True, exist_ok=True)
    (run_path / "data" / "output").mkdir(parents=True, exist_ok=True)
    (run_path / "logs").mkdir(parents=True, exist_ok=True)
    (run_path / "parameter").mkdir(parents=True, exist_ok=True)

    run_config = {
        "RUN_SETTING": {
            "RUN_YYMM": run_yymm,
            "RUN_PATH": str(run_path.resolve()),
        },
        "CONSTANT": {
            "days_in_year": 365.25,
            "days_in_month": 30.5,
        },
        "DATA_IO_SETTING": {
            "INPUT_DATA_EXT": "csv",
        },
    }

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
