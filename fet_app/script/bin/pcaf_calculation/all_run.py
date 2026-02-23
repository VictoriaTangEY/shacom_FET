from typing import Optional, Dict

import pandas as pd

from .listed_equity_and_corporate_bonds import run_listed_equity_and_corporate_bonds
from .business_loans_and_unlisted_equity import run_business_loans_and_unlisted_equity
from .project_finance import run_project_finance
from .commercial_real_estate import run_commercial_real_estate
from .mortgages import run_mortgages
from .sovereign_debt import run_sovereign_debt


def run_all(
    rc,
    logger,
    instruments_splits: Dict[str, pd.DataFrame],
    param: Optional[Dict[str, pd.DataFrame]] = None,
) -> None:

    logger.info("===================================================")
    logger.info("Starting PCAF calculation")

    counts = {
        code: len(df)
        for code, df in instruments_splits.items()
        if df is not None and not df.empty
    }
    logger.info("Instrument rows by PCAF_ASSET_CLASS: %s", counts)

    run_listed_equity_and_corporate_bonds(
        rc=rc,
        logger=logger,
        instruments=instruments_splits.get("LECB"),
        param=param,
    )
    run_business_loans_and_unlisted_equity(
        rc=rc,
        logger=logger,
        instruments=instruments_splits.get("BLUE"),
        param=param,
    )
    run_project_finance(
        rc=rc,
        logger=logger,
        instruments=instruments_splits.get("PROJFIN"),
        param=param,
    )
    run_commercial_real_estate(
        rc=rc,
        logger=logger,
        instruments=instruments_splits.get("CRE"),
        param=param,
    )
    run_mortgages(
        rc=rc,
        logger=logger,
        instruments=instruments_splits.get("RESMTG"),
        param=param,
    )
    run_sovereign_debt(
        rc=rc,
        logger=logger,
        instruments=instruments_splits.get("SOVBND"),
        param=param,
    )

    logger.info("PCAF calculation completed")
