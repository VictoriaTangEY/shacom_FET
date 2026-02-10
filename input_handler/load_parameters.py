import json
from pathlib import Path

import pandas as pd


def load_configuration_file(config_path):
    """Load and return run configuration from a JSON file."""
    with open(Path(config_path), "r", encoding="utf-8") as f:
        return json.load(f)


def load_parameters(parm_path, logger=None):
    """
    Load parameter data from Excel files in parm_path.
    Reads all *Param.xlsx and *Template.xlsx (excluding temp ~ files) and
    returns a dict mapping sheet names to DataFrames.
    """
    parm_path = Path(parm_path)
    if not parm_path.exists():
        if logger is not None:
            logger.warning("Parameter path does not exist: %s", parm_path)
        return {}

    param = {}
    for pattern in ("*Param.xlsx", "*Template.xlsx"):
        for wb_file in parm_path.glob(pattern):
            if wb_file.name.startswith("~"):
                continue
            try:
                xl = pd.ExcelFile(wb_file)
                for sheet in xl.sheet_names:
                    param[sheet] = pd.read_excel(wb_file, sheet_name=sheet)
            except Exception as e:
                if logger is not None:
                    logger.exception("Failed to load parameter workbook %s: %s", wb_file, e)
                else:
                    print(f"Failed to load {wb_file}: {e}")
    return param
