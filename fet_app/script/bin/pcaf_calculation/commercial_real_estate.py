import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, Any
from input_handler.load_parameters import get_parameter_data
from .all_general_calculator import GeneralPcafCalculator, NA_STR


class CommercialRealEstate(GeneralPcafCalculator):

    def _merge_parameter_tables(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = self._merge_emission_factor(df)
        df = self._merge_energy_consumption_table(df)
        return df

    def _energy_consumption_vectorized(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        Determine energy consumption option and consumption for all rows.
        Returns (classify_option Series, energy_consumption Series).
        """
        opt = pd.Series(NA_STR, index=df.index)
        energy = pd.Series(NA_STR, index=df.index)

        actual_intensity = (
            pd.to_numeric(df["PROPERTY_ACTUAL_ENERGY_CONSUMPTIONESTIMATED "], errors="coerce")
            if "PROPERTY_ACTUAL_ENERGY_CONSUMPTIONESTIMATED " in df.columns
            else pd.Series(np.nan, index=df.index)
        )
        area = (
            pd.to_numeric(df["GROSS_FLOOR_AREA"], errors="coerce")
            if "GROSS_FLOOR_AREA" in df.columns
            else pd.Series(np.nan, index=df.index)
        )
        est_intensity = (
            pd.to_numeric(df["Energy_Consumption_Table"], errors="coerce")
            if "Energy_Consumption_Table" in df.columns
            else pd.Series(np.nan, index=df.index)
        )

        # Option 1: Actual energy consumption
        mask_1 = self._has_value(actual_intensity) & self._has_value(area)
        opt = opt.where(~mask_1, "1")
        energy = energy.where(~mask_1, actual_intensity * area)

        # Option 2: Estimated consumption by building type
        mask_2 = (opt == NA_STR) & self._has_value(est_intensity) & self._has_value(area)
        opt = opt.where(~mask_2, "2")
        energy = energy.where(~mask_2, est_intensity * area)

        return opt, energy

    @staticmethod
    def _attribution_factor_vectorized(df: pd.DataFrame) -> pd.Series:
        """attribution_factor = OUTSTANDING_BALANCE_LCY / PROPERTY_VALUE_AT_ORIGINATION."""
        value = pd.to_numeric(df["PROPERTY_VALUE_AT_ORIGINATION"], errors="coerce")
        bal = pd.to_numeric(df["OUTSTANDING_BALANCE_LCY"], errors="coerce")
        af = np.where(value == 0, np.nan, bal / value)
        return pd.Series(af, index=df.index)

    def run(self) -> pd.DataFrame:
        """Execute the full calculation pipeline and write output."""
        self.logger.info("Starting calculation for commercial real estate")
        
        df = self._merge_parameter_tables(self.instruments)
        
        # Step 1: Attribution factor
        attribution_factor = self._attribution_factor_vectorized(df)
        zero_denom = pd.to_numeric(df["PROPERTY_VALUE_AT_ORIGINATION"], errors="coerce").fillna(0) == 0
        attribution_factor = attribution_factor.where(~zero_denom, NA_STR)

        ## Log rows with zero denominator
        for contract_id in df.loc[zero_denom, "CONTRACT_ID"].dropna().unique():
            msg = (
                "COMMERCIAL_REAL_ESTATE: CONTRACT_ID=%s has PROPERTY_VALUE_AT_ORIGINATION = 0; "
                "ATTRIBUTION_FACTOR=NA. Please check input data."
            ) % contract_id
            self.logger.warning(msg)
            print(msg)
        df["ATTRIBUTION_FACTOR"] = attribution_factor

        # Step 2: Classify option and building energy consumption
        classify_option, energy_consumption = self._energy_consumption_vectorized(df)
        df["CLASSIFY_OPTION"] = classify_option
        df["ENERGY_CONSUMPTION"] = energy_consumption

        emission_factor = (
            pd.to_numeric(df["EMISSION_FACTOR"], errors="coerce")
            if "EMISSION_FACTOR" in df.columns
            else pd.Series(np.nan, index=df.index)
        )

        # Step 3: Building emission and financed emission
        energy_series = df["ENERGY_CONSUMPTION"]

        building_emission = np.where(
            (energy_series == NA_STR) | pd.isna(emission_factor),
            NA_STR,
            pd.to_numeric(energy_series, errors="coerce") * emission_factor,
        )
        df["BUILDING_EMISSION"] = pd.Series(building_emission, index=df.index)

        af_series = df["ATTRIBUTION_FACTOR"]

        financed = np.where(
            (af_series == NA_STR) | (df["BUILDING_EMISSION"] == NA_STR),
            NA_STR,
            pd.to_numeric(af_series, errors="coerce")
            * pd.to_numeric(df["BUILDING_EMISSION"], errors="coerce"),
        )
        df["FINANCED_EMISSION"] = pd.Series(financed, index=df.index)

        # Write output with explicit NA for problem rows
        self.rc.result_path.mkdir(parents=True, exist_ok=True)
        out_path = self.rc.result_path / "output.csv"
        out_new = df.copy()
        for col in ["CLASSIFY_OPTION", "ATTRIBUTION_FACTOR", "BUILDING_EMISSION", "FINANCED_EMISSION"]:
            if col in out_new.columns:
                out_new[col] = out_new[col].apply(self._to_display_value)
        out_new = out_new.drop(
            columns=[c for c in ["Energy_Consumption_Table", "ENERGY_CONSUMPTION"] if c in out_new.columns]
        )

        try:
            if out_path.exists():
                existing = pd.read_csv(out_path, dtype=str)
                out_all = pd.concat([existing, out_new], ignore_index=True, sort=False)
            else:
                out_all = out_new
        except Exception:
            out_all = out_new

        cols = list(out_all.columns)
        if "COMPANY_EMISSION" in cols and "BUILDING_EMISSION" in cols:
            cols.remove("BUILDING_EMISSION")
            insert_idx = cols.index("COMPANY_EMISSION") + 1
            cols.insert(insert_idx, "BUILDING_EMISSION")
            out_all = out_all[cols]

        out_all.to_csv(out_path, index=False, encoding="utf-8")

        return df


def run_commercial_real_estate(rc, logger, instruments=None, param=None):
    calculator = CommercialRealEstate(rc, logger, instruments, param)
    return calculator.run()