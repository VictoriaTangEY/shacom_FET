import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, Any
from input_handler.load_parameters import get_parameter_data
from .all_general_calculator import GeneralPcafCalculator, NA_STR


class Mortgages(GeneralPcafCalculator):

    def _merge_parameter_tables(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = self._merge_emission_factor(df)
        df = self._merge_energy_consumption_table(df)
        return df

    def _energy_consumption_vectorized(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        Determine energy consumption option and consumption for all rows.
        Returns (classify_option Series, building_energy Series).
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
        # building_energy = PROPERTY_ACTUAL_ENERGY_CONSUMPTIONESTIMATED × GROSS_FLOOR_AREA
        mask_1 = self._has_value(actual_intensity) & self._has_value(area)
        opt = opt.where(~mask_1, "1")
        energy = energy.where(~mask_1, actual_intensity * area)

        # Option 2: Estimated consumption by building type
        # building_energy = Energy_Consumption_Table × GROSS_FLOOR_AREA
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
        self.logger.info("Starting calculation for mortgages")
        
        df = self._merge_parameter_tables(self.instruments)
        
        # Step 1: Attribution factor
        attribution_factor = self._attribution_factor_vectorized(df)
        zero_denom = pd.to_numeric(df["PROPERTY_VALUE_AT_ORIGINATION"], errors="coerce").fillna(0) == 0
        attribution_factor = attribution_factor.where(~zero_denom, NA_STR)

        ## Log rows with zero denominator
        for contract_id in df.loc[zero_denom, "CONTRACT_ID"].dropna().unique():
            msg = (
                "MORTGAGES: CONTRACT_ID=%s has PROPERTY_VALUE_AT_ORIGINATION = 0; "
                "ATTRIBUTION_FACTOR=NA. Please check input data."
            ) % contract_id
            self.logger.warning(msg)
            print(msg)
        df["ATTRIBUTION_FACTOR"] = attribution_factor

        # Step 2: Classify option and building energy consumption
        classify_option, building_energy = self._energy_consumption_vectorized(df)
        df["CLASSIFY_OPTION"] = classify_option
        df = df.drop(columns=["Energy_Consumption_Table"], errors="ignore")

        emission_factor = (
            pd.to_numeric(df["EMISSION_FACTOR"], errors="coerce")
            if "EMISSION_FACTOR" in df.columns
            else pd.Series(np.nan, index=df.index)
        )

        # Step 3: Building emission and financed emission
        # BUILDING_EMISSION = building_energy × EMISSION_FACTOR
        building_emission = np.where(
            (building_energy == NA_STR) | pd.isna(emission_factor),
            NA_STR,
            pd.to_numeric(building_energy, errors="coerce") * emission_factor,
        )
        df["BUILDING_EMISSION"] = pd.Series(building_emission, index=df.index)

        af_series = df["ATTRIBUTION_FACTOR"]

        # FINANCED_EMISSION = ATTRIBUTION_FACTOR × BUILDING_EMISSION
        financed = np.where(
            (af_series == NA_STR) | (df["BUILDING_EMISSION"] == NA_STR),
            NA_STR,
            pd.to_numeric(af_series, errors="coerce")
            * pd.to_numeric(df["BUILDING_EMISSION"], errors="coerce"),
        )
        df["FINANCED_EMISSION"] = pd.Series(financed, index=df.index)

        # Step 4: Write output
        self._write_output(
            df,
            output_columns=["CLASSIFY_OPTION", "ATTRIBUTION_FACTOR", "BUILDING_EMISSION", "FINANCED_EMISSION"],
            append=True,
        )
        return df


def run_mortgages(rc, logger, instruments=None, param=None):
    calculator = Mortgages(rc, logger, instruments, param)
    return calculator.run()