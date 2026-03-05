import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, Any
from input_handler.load_parameters import get_parameter_data

NA_STR = "NA"


class BusinessLoansAndUnlistedEquity:
    """
    Calculator for business loans and unlisted equity PCAF emissions.
    Merges parameter tables, classifies emission options, computes attribution
    factor and financed emission.
    """

    def __init__(self, rc, logger, instruments=None, param=None):
        self.rc = rc
        self.logger = logger
        self.instruments = instruments.copy() if instruments is not None else pd.DataFrame()
        self.param = param or {}

    def _merge_parameter_tables(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Left-merge parameter tables onto df so each row has mapped columns.
        - Emission_Factor: on COUNTRY_CODE -> adds EMISSION_FACTOR
        - Carbon_Intensity_Rev: on INDUSTRY_CLASSIFICATION_CODE -> adds CARBON_INTENSITY_SCOPE_FINAL_REV
        - Carbon_Intensity_Asst: on INDUSTRY_CLASSIFICATION_CODE -> adds CARBON_INTENSITY_FINAL_ASSET
        """
        df = df.copy()

        # Emission_Factor: on COUNTRY_CODE
        emission_df = get_parameter_data(self.param, "Emission_Factor")
        if not emission_df.empty and "COUNTRY_CODE" in emission_df.columns and "EMISSION_FACTOR" in emission_df.columns:
            df = df.merge(
                emission_df[["COUNTRY_CODE", "EMISSION_FACTOR"]].drop_duplicates(subset=["COUNTRY_CODE"]),
                on="COUNTRY_CODE",
                how="left",
            )
        else:
            df["EMISSION_FACTOR"] = np.nan

        # Carbon_Intensity_Rev, Carbon_Intensity_Asst: on INDUSTRY_CLASSIFICATION_CODE
        def _merge_intensity(d: pd.DataFrame, sheet_name: str, value_col: str):
            tbl = get_parameter_data(self.param, sheet_name)
            if tbl.empty or "INDUSTRY_CLASSIFICATION_CODE" not in tbl.columns or value_col not in tbl.columns:
                d = d.copy()
                d[value_col] = np.nan
                return d
            tbl = tbl[["INDUSTRY_CLASSIFICATION_CODE", value_col]].drop_duplicates(subset=["INDUSTRY_CLASSIFICATION_CODE"])
            return d.merge(tbl, on="INDUSTRY_CLASSIFICATION_CODE", how="left")

        df = _merge_intensity(df, "Carbon_Intensity_Rev", "CARBON_INTENSITY_SCOPE_FINAL_REV")
        df = _merge_intensity(df, "Carbon_Intensity_Asst", "CARBON_INTENSITY_FINAL_ASSET")

        return df

    @staticmethod
    def _has_value(s: pd.Series) -> pd.Series:
        """True where cell has a value (empty/NaN = no, 0 = yes)."""
        return pd.notna(s) & ~(s.astype(str).str.strip() == "")

    def _classify_and_company_emission_vectorized(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        Determine classify option and company emission for all rows.
        Returns (classify_option Series, company_emission Series).
        """
        opt = pd.Series(NA_STR, index=df.index)
        em = pd.Series(NA_STR, index=df.index)

        scope1_2 = pd.to_numeric(df["CO2_EQUIVALENT_EMISSIONS_SCOPE1_2_OBLIGOR"], errors="coerce")
        scope3 = pd.to_numeric(df["CO2_EQUIVALENT_EMISSIONS_SCOPE3_OBLIGOR"], errors="coerce")
        energy = pd.to_numeric(df["COMPANY_ENERGY_CONSUMPTION"], errors="coerce")
        rev = pd.to_numeric(df["TOTAL_REVENUE_MILLION_HKD"], errors="coerce")
        ast = pd.to_numeric(df["TOTAL_ASSET_MILLION_HKD"], errors="coerce")
        emission_factor = df["EMISSION_FACTOR"] if "EMISSION_FACTOR" in df.columns else pd.Series(np.nan, index=df.index)
        intensity_rev = df["CARBON_INTENSITY_SCOPE_FINAL_REV"] if "CARBON_INTENSITY_SCOPE_FINAL_REV" in df.columns else pd.Series(np.nan, index=df.index)
        intensity_asst = df["CARBON_INTENSITY_FINAL_ASSET"] if "CARBON_INTENSITY_FINAL_ASSET" in df.columns else pd.Series(np.nan, index=df.index)

        # Option 1a: Verified emissions (Scope 1+2)
        is_verify_y = df["IS_VERIFY_EMISSION"].astype(str).str.strip().str.upper() == "Y"
        mask_1a = is_verify_y & self._has_value(scope1_2)
        opt = opt.where(~mask_1a, "1a")
        em = em.where(~mask_1a, scope1_2)

        # Option 1b: Unverified but Scope 3 obligor has value
        mask_1b = (opt == NA_STR) & self._has_value(scope3)
        opt = opt.where(~mask_1b, "1b")
        em = em.where(~mask_1b, scope3)

        # Option 2a: Physical activity – energy consumption × emission factor
        mask_2a = (opt == NA_STR) & self._has_value(energy) & pd.notna(emission_factor)
        opt = opt.where(~mask_2a, "2a")
        em = em.where(~mask_2a, energy * emission_factor)

        # Option 3a: Economic – revenue × carbon intensity (t CO2/100 million)
        mask_3a = (opt == NA_STR) & self._has_value(rev) & pd.notna(intensity_rev)
        opt = opt.where(~mask_3a, "3a")
        em = em.where(~mask_3a, rev * intensity_rev / 100.0)

         # Option 3b: Economic – asset × carbon intensity (t CO2/100 million)
        mask_3b = (opt == NA_STR) & self._has_value(ast) & pd.notna(intensity_asst)
        opt = opt.where(~mask_3b, "3b")
        em = em.where(~mask_3b, ast * intensity_asst / 100.0)

        return opt, em

    @staticmethod
    def _attribution_factor_vectorized(df: pd.DataFrame) -> pd.Series:
        """attribution_factor = OUTSTANDING_BALANCE_LCY / (TOTAL_EQUITY_MILLION_HKD + TOTAL_DEBT_MILLION_HKD)."""
        eq = pd.to_numeric(df["TOTAL_EQUITY_MILLION_HKD"], errors="coerce").fillna(0)
        debt = pd.to_numeric(df["TOTAL_DEBT_MILLION_HKD"], errors="coerce").fillna(0)
        denom = eq + debt
        bal = pd.to_numeric(df["OUTSTANDING_BALANCE_LCY"], errors="coerce")
        af = np.where(denom == 0, np.nan, bal / denom)
        return pd.Series(af, index=df.index)

    @staticmethod
    def _to_display_value(x: Any) -> Any:
        """For output CSV: show 'NA' explicitly for missing/invalid."""
        if pd.isna(x) or x is None:
            return NA_STR
        if isinstance(x, float) and np.isnan(x):
            return NA_STR
        if isinstance(x, str) and x.strip() == "":
            return NA_STR
        return x

    def run(self) -> pd.DataFrame:
        """Execute the full calculation pipeline and write output."""
        self.logger.info("Starting calculation for business loans and unlisted equity")

        df = self._merge_parameter_tables(self.instruments)

        # Step 1: Classify option and company emission (vectorized using merged columns)
        classify_option, company_emission = self._classify_and_company_emission_vectorized(df)
        df["CLASSIFY_OPTION"] = classify_option
        df["COMPANY_EMISSION"] = company_emission

        ## Log rows with no option matched
        no_match = (classify_option == NA_STR) & (company_emission == NA_STR)
        for contract_id in df.loc[no_match, "CONTRACT_ID"].dropna().unique():
            msg = "BLUE: CONTRACT_ID=%s has no applicable classify option; CLASSIFY_OPTION=NA, COMPANY_EMISSION=NA. Please check input data." % contract_id
            self.logger.warning(msg)
            print(msg)

        # Step 2: Attribution factor
        attribution_factor = self._attribution_factor_vectorized(df)
        zero_denom = (
            pd.to_numeric(df["TOTAL_EQUITY_MILLION_HKD"], errors="coerce").fillna(0)
            + pd.to_numeric(df["TOTAL_DEBT_MILLION_HKD"], errors="coerce").fillna(0)
        ) == 0
        attribution_factor = attribution_factor.where(~zero_denom, NA_STR)

        ## Log rows with zero denominator
        for contract_id in df.loc[zero_denom, "CONTRACT_ID"].dropna().unique():
            msg = "BLUE: CONTRACT_ID=%s has TOTAL_EQUITY_MILLION_HKD + TOTAL_DEBT_MILLION_HKD = 0; ATTRIBUTION_FACTOR=NA. Please check input data." % contract_id
            self.logger.warning(msg)
            print(msg)
        df["ATTRIBUTION_FACTOR"] = attribution_factor

        # Step 3: Financed emission
        af = df["ATTRIBUTION_FACTOR"]
        ce = df["COMPANY_EMISSION"]
        financed = np.where(
            (af == NA_STR) | (ce == NA_STR),
            NA_STR,
            pd.to_numeric(af, errors="coerce") * pd.to_numeric(ce, errors="coerce"),
        )
        df["FINANCED_EMISSION"] = pd.Series(financed, index=df.index)

        # Write output with explicit NA for problem rows
        self.rc.result_path.mkdir(parents=True, exist_ok=True)
        out_path = self.rc.result_path / "output.csv"
        out = df.copy()
        for col in ["CLASSIFY_OPTION", "COMPANY_EMISSION", "ATTRIBUTION_FACTOR", "FINANCED_EMISSION"]:
            out[col] = out[col].apply(self._to_display_value)
        out.to_csv(out_path, index=False, encoding="utf-8")

        return df


def run_business_loans_and_unlisted_equity(rc, logger, instruments=None, param=None):
    calculator = BusinessLoansAndUnlistedEquity(rc, logger, instruments, param)
    return calculator.run()
