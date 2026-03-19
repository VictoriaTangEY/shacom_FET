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


def run_pcaf_all(
    rc,
    logger,
    instruments_splits: Dict[str, pd.DataFrame],
    param: Optional[Dict[str, pd.DataFrame]] = None,
) -> None:

    logger.info("===================================================")
    logger.info("Starting PCAF calculation")

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
