import numpy as np
import pandas as pd
from .business_loans_and_unlisted_equity import BusinessLoansAndUnlistedEquity


class ListedEquityAndCorporateBonds(BusinessLoansAndUnlistedEquity):
    """
    Calculator for listed equity and corporate bonds PCAF emissions.
    Same logic as BusinessLoansAndUnlistedEquity except attribution factor
    uses EVIC_MILLION_HKD instead of TOTAL_EQUITY_MILLION_HKD + TOTAL_DEBT_MILLION_HKD.
    """

    @staticmethod
    def _attribution_factor_vectorized(df: pd.DataFrame) -> pd.Series:
        """attribution_factor = OUTSTANDING_BALANCE_LCY / EVIC_MILLION_HKD."""
        evic = pd.to_numeric(df["EVIC_MILLION_HKD"], errors="coerce")
        bal = pd.to_numeric(df["OUTSTANDING_BALANCE_LCY"], errors="coerce")
        af = np.where(evic == 0, np.nan, bal / evic)
        return pd.Series(af, index=df.index)


def run_listed_equity_and_corporate_bonds(rc, logger, instruments=None, param=None):
    calculator = ListedEquityAndCorporateBonds(rc, logger, instruments, param)
    return calculator.run()
