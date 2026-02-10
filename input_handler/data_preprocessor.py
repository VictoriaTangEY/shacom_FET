from pathlib import Path
from typing import Dict
import pandas as pd


class DataPreprocessor:

    def __init__(self, context):
        self.rc = context

    def load_instrument_table(self, logger) -> pd.DataFrame:
        """
        Load the full instrument_table as a pandas DataFrame.
        """
        instrument_path = self.rc.in_data_path / f"instrument_table.{self.rc.input_data_ext}"

        try:
            df = pd.read_csv(instrument_path)
        except Exception as e:
            logger.exception("Failed to load instrument_table: %s", e)
            raise

        if "PCAF_ASSET_CLASS" not in df.columns:
            logger.error("Column 'PCAF_ASSET_CLASS' not found in instrument_table.")
            raise KeyError("PCAF_ASSET_CLASS column missing in instrument_table.")

        return df

    def split_by_pcaf_asset_class(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Split the input instrument DataFrame into subsets by PCAF_ASSET_CLASS.
        Returns a dict mapping asset class code to its subset DataFrame.
        """
        splits: Dict[str, pd.DataFrame] = {}
        for code in ["LECB", "BLUE", "PROJFIN", "CRE", "RESMTG", "SOVBND"]:
            splits[code] = df[df["PCAF_ASSET_CLASS"] == code].copy()
        return splits

    def load_and_split_instruments(self, logger) -> Dict[str, pd.DataFrame]:
        df = self.load_instrument_table(logger)
        return self.split_by_pcaf_asset_class(df)

