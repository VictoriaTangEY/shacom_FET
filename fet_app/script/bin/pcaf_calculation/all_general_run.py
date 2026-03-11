import json
import time
from typing import Optional, Dict

import pandas as pd

from .listed_equity_and_corporate_bonds import run_listed_equity_and_corporate_bonds
from .business_loans_and_unlisted_equity import run_business_loans_and_unlisted_equity
from .project_finance import run_project_finance
from .commercial_real_estate import run_commercial_real_estate
from .mortgages import run_mortgages
from .sovereign_debt import run_sovereign_debt

DEBUG_LOG_PATH = r"c:\Users\UV665AR\OneDrive - EY\Documents\GitHub\shacom_FET\.cursor\debug.log"


def run_all(
    rc,
    logger,
    instruments_splits: Dict[str, pd.DataFrame],
    param: Optional[Dict[str, pd.DataFrame]] = None,
) -> None:

    logger.info("===================================================")
    logger.info("Starting PCAF calculation")

    # Debug: record run_path at the very beginning so we can link logs to run folder
    try:
        payload = {
            "id": f"log_{int(time.time()*1000)}_run_all_start",
            "timestamp": int(time.time() * 1000),
            "location": "all_general_run.py:run_all:start",
            "message": "Starting PCAF calculation for run",
            "data": {
                "run_path": str(getattr(rc, "run_path", "")),
                "result_path": str(getattr(rc, "result_path", "")),
            },
        }
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as _f:
            _f.write(json.dumps(payload) + "\n")
    except Exception:
        pass

    counts = {
        code: len(df)
        for code, df in instruments_splits.items()
        if df is not None and not df.empty
    }
    logger.info("Instrument rows by PCAF_ASSET_CLASS: %s", counts)

    try:
        run_business_loans_and_unlisted_equity(
            rc=rc,
            logger=logger,
            instruments=instruments_splits.get("BLUE"),
            param=param,
        )
    except Exception:
        logger.exception("Error during business loans and unlisted equity calculation")
        raise
    
    try:
        run_listed_equity_and_corporate_bonds(
            rc=rc,
            logger=logger,
            instruments=instruments_splits.get("LECB"),
            param=param,
        )
    except Exception:
        logger.exception("Error during listed equity and corporate bonds calculation")
        raise

    try:
        run_mortgages(
            rc=rc,
            logger=logger,
            instruments=instruments_splits.get("RESMTG"),
            param=param,
        )
    except Exception:
        logger.exception("Error during mortgages calculation")
        raise

    try:
        run_project_finance(
            rc=rc,
            logger=logger,
            instruments=instruments_splits.get("PROJFIN"),
            param=param,
        )
    except Exception:
        logger.exception("Error during project finance calculation")
        raise

    try:
        run_commercial_real_estate(
            rc=rc,
            logger=logger,
            instruments=instruments_splits.get("CRE"),
            param=param,
        )
    except Exception:
        logger.exception("Error during commercial real estate calculation")
        raise

    try:
        run_sovereign_debt(
            rc=rc,
            logger=logger,
            instruments=instruments_splits.get("SOVBND"),
            param=param,
        )
    except Exception:
        logger.exception("Error during sovereign debt calculation")
        raise

    logger.info("PCAF calculation completed")
