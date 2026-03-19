from pathlib import Path
from typing import Dict
import pandas as pd
from run_setup import INPUT_INSTRUMENT_FILE


class DataPreprocessor:

    def __init__(self, context):
        self.rc = context

    # Load instrument_table.csv from input data path
    def load_instrument_table(self, logger) -> pd.DataFrame:
        instrument_path = self.rc.in_data_path / INPUT_INSTRUMENT_FILE
        try:
            df = pd.read_csv(instrument_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load instrument_table: {e}") from e

        df.columns = [str(c).strip() for c in df.columns]
        return df

    # Split the input instrument DataFrame into subsets by PCAF_ASSET_CLASS
    def split_by_pcaf_asset_class(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        splits: Dict[str, pd.DataFrame] = {}
        for code in ["LECB", "BLUE", "PROJFIN", "CRE", "RESMTG", "SOVBND"]:
            splits[code] = df[df["PCAF_ASSET_CLASS"] == code].copy()
        return splits

    def load_and_split_instruments(self, logger) -> Dict[str, pd.DataFrame]:
        df = self.load_instrument_table(logger)
        return self.split_by_pcaf_asset_class(df)

