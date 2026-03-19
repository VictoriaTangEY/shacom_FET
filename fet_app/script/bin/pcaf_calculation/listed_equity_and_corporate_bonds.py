import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, Any
from input_handler.load_parameters import get_parameter_data
from .all_general_calculator import GeneralPcafCalculator, NA_STR


class ListedEquityAndCorporateBonds(GeneralPcafCalculator):

    def _merge_parameter_tables(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = self._merge_emission_factor(df)
        df = self._merge_carbon_intensity(df)
        return df

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
        """attribution_factor = OUTSTANDING_BALANCE_LCY / EVIC_MILLION_HKD."""
        evic = pd.to_numeric(df["EVIC_MILLION_HKD"], errors="coerce")
        bal = pd.to_numeric(df["OUTSTANDING_BALANCE_LCY"], errors="coerce")
        af = np.where(evic == 0, np.nan, bal / evic)
        return pd.Series(af, index=df.index)

    def run(self) -> pd.DataFrame:
        self.logger.info("Starting calculation for listed equity and corporate bonds")

        df = self._merge_parameter_tables(self.instruments)

        # Step 1: Classify option and company emission
        classify_option, company_emission = self._classify_and_company_emission_vectorized(df)
        df["CLASSIFY_OPTION"] = classify_option
        df["COMPANY_EMISSION"] = company_emission

        no_match = (classify_option == NA_STR) & (company_emission == NA_STR)

        for contract_id in df.loc[no_match, "CONTRACT_ID"].dropna().unique():
            msg = "LECB: CONTRACT_ID=%s has no applicable classify option; CLASSIFY_OPTION=NA, COMPANY_EMISSION=NA. Please check input data." % contract_id
            self.logger.warning(msg)
            print(msg)

        # Step 2: Attribution factor
        attribution_factor = self._attribution_factor_vectorized(df)
        zero_denom = pd.to_numeric(df["EVIC_MILLION_HKD"], errors="coerce").fillna(0) == 0
        attribution_factor = attribution_factor.where(~zero_denom, NA_STR)

        for contract_id in df.loc[zero_denom, "CONTRACT_ID"].dropna().unique():
            msg = "LECB: CONTRACT_ID=%s has EVIC_MILLION_HKD = 0; ATTRIBUTION_FACTOR=NA. Please check input data." % contract_id
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

        # Step 4: Write output
        self._write_output(
            df,
            output_columns=["CLASSIFY_OPTION", "COMPANY_EMISSION", "ATTRIBUTION_FACTOR", "FINANCED_EMISSION"],
            append=True,
        )
        return df


def run_listed_equity_and_corporate_bonds(rc, logger, instruments=None, param=None):
    calculator = ListedEquityAndCorporateBonds(rc, logger, instruments, param)
    return calculator.run()
