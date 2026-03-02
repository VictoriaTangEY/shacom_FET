import json
from pathlib import Path
from typing import Dict

import pandas as pd

# Parameter Excel sheets: first N rows are metadata (Parameter name, description, mandatory, data type); data starts after.
PARAM_METADATA_ROWS = 4


def get_parameter_data(param: Dict[str, pd.DataFrame], sheet_name: str) -> pd.DataFrame:
    """
    Return the data portion of a parameter sheet (skip metadata rows).
    Use this for lookups; the raw sheet has column names in row 0 but data starts at row PARAM_METADATA_ROWS.
    """
    if not param or sheet_name not in param:
        return pd.DataFrame()
    df = param[sheet_name]
    if df is None or df.empty or len(df) <= PARAM_METADATA_ROWS:
        return pd.DataFrame()
    return df.iloc[PARAM_METADATA_ROWS:].copy()


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
        msg = f"Parameter path does not exist: {parm_path}"
        if logger is not None:
            logger.error(msg)
        else:
            print(msg)
        raise FileNotFoundError(msg)

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
                    logger.exception(
                        "Failed to load parameter workbook %s: %s", wb_file, e
                    )
                else:
                    print(f"Failed to load {wb_file}: {e}")
                raise
    return param
