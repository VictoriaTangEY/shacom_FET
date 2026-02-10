from pathlib import Path


class run_setting:
    """Runtime environment built from config dict (paths, run options)."""

    def __init__(self, run_config):
        c = run_config.copy()
        rs = c["RUN_SETTING"]

        self.run_yymm = rs["RUN_YYMM"]
        self.prev_yymm = rs["PREV_YYMM"]
        self.master_path = Path(rs["MASTERPATH"])
        self.output_path = Path(rs["OUTPUTPATH"])
        self.param_version = rs.get("PARAM_VERSION", self.run_yymm)
        self.run_mode = rs.get("RUN_MODE", 1)

        self.param_path = self.master_path / str(self.run_yymm) / "parameter"
        self.in_data_path = self.master_path / str(self.run_yymm) / "input data"
        self.prev_in_data_path = self.master_path / str(self.prev_yymm) / "input data"

        self.result_path = self.output_path / str(self.run_yymm) / "data" / "02_result"
        self.report_path = self.output_path / str(self.run_yymm) / "data" / "03_report"
        self.log_path = self.output_path / str(self.run_yymm) / "log"

        const = c.get("CONSTANT", {})
        self.days_in_year = const.get("days_in_year", 365.25)
        self.days_in_month = const.get("days_in_month", 30.5)

        io_setting = c.get("DATA_IO_SETTING", {})
        self.input_data_ext = io_setting.get("INPUT_DATA_EXT", "csv")
