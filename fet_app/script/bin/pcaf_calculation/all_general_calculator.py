import numpy as np
import pandas as pd
from typing import Dict, Optional, Any, List
from input_handler.load_parameters import get_parameter_data

# NA string
NA_STR = "Invalid"
# Output columns
OUTPUT_COLUMNS = [
    "CLASSIFY_OPTION",
    "COMPANY_EMISSION",
    "BUILDING_EMISSION",
    "PROJECT_EMISSION",
    "SOVEREIGN_EMISSION",
    "ATTRIBUTION_FACTOR",
    "FINANCED_EMISSION",
]


class GeneralPcafCalculator:

    def __init__(self, rc, logger, instruments=None, param: Optional[Dict[str, pd.DataFrame]] = None):
        self.rc = rc
        self.logger = logger
        self.instruments = instruments.copy() if instruments is not None else pd.DataFrame()
        self.param = param or {}
        self._ensure_output_columns()

    # Add output columns
    def _ensure_output_columns(self) -> None:
        for col in OUTPUT_COLUMNS:
            if col not in self.instruments.columns:
                self.instruments[col] = np.nan

    # Left-merge Emission_Factor on COUNTRY_CODE -> adds EMISSION_FACTOR
    def _merge_emission_factor(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        emission_df = get_parameter_data(self.param, "Emission_Factor")
        if not emission_df.empty and "COUNTRY_CODE" in emission_df.columns and "EMISSION_FACTOR" in emission_df.columns:
            df = df.merge(
                emission_df[["COUNTRY_CODE", "EMISSION_FACTOR"]].drop_duplicates(subset=["COUNTRY_CODE"]),
                on="COUNTRY_CODE",
                how="left",
            )
        else:
            df["EMISSION_FACTOR"] = np.nan

        return df

    # Left-merge Carbon_Intensity_Rev on INDUSTRY_CLASSIFICATION_CODE -> adds CARBON_INTENSITY_SCOPE_FINAL_REV
    # Left-merge Carbon_Intensity_Asst on INDUSTRY_CLASSIFICATION_CODE -> adds CARBON_INTENSITY_FINAL_ASSET
    def _merge_carbon_intensity(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        def _merge_intensity(d: pd.DataFrame, sheet_name: str, value_col: str) -> pd.DataFrame:
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

    # Left-merge Energy_Consumption_Table on COLLATERAL_TYPE -> adds Energy_Consumption_Table
    def _merge_energy_consumption_table(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        energy_df = get_parameter_data(self.param, "Energy_Consumption_Table")
        if not energy_df.empty and "COLLATERAL_TYPE" in energy_df.columns and "Energy_Consumption_Table" in energy_df.columns:
            df = df.merge(
                energy_df[["COLLATERAL_TYPE", "Energy_Consumption_Table"]].drop_duplicates(subset=["COLLATERAL_TYPE"]),
                on="COLLATERAL_TYPE",
                how="left",
            )
        else:
            df["Energy_Consumption_Table"] = np.nan

        return df

    def _merge_parameter_tables(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self._merge_emission_factor(df)
        return df

    @staticmethod
    def _has_value(s: pd.Series) -> pd.Series:
        """True where cell has a value (empty/NaN = no, 0 = yes)."""
        return pd.notna(s) & ~(s.astype(str).str.strip() == "")

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

    # Write output to output.csv file
    def _write_output(
        self,
        df: pd.DataFrame,
        output_columns: List[str],
        append: bool = False,
    ) -> None:
        self.rc.result_path.mkdir(parents=True, exist_ok=True)
        out_path = self.rc.result_path / "output.csv"
        out = df.copy()
        for col in output_columns:
            if col in out.columns:
                out[col] = out[col].apply(self._to_display_value)
        if append and out_path.exists():
            try:
                existing = pd.read_csv(out_path, dtype=str)
                out_all = pd.concat([existing, out], ignore_index=True, sort=False)
            except Exception:
                out_all = out
        else:
            out_all = out
        non_output_cols = [c for c in out_all.columns if c not in OUTPUT_COLUMNS]
        output_cols_ordered = [c for c in OUTPUT_COLUMNS if c in out_all.columns]
        out_all = out_all[non_output_cols + output_cols_ordered]
        out_all.to_csv(out_path, index=False, encoding="utf-8")

