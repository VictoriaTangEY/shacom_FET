from pathlib import Path


class run_setting:
    """Runtime environment built from config dict (paths, run options)."""

    def __init__(self, run_config):
        c = run_config.copy()
        rs = c["RUN_SETTING"]

        self.run_yymm = rs["RUN_YYMM"]
        self.prev_yymm = rs["PREV_YYMM"]
        self.run_path = Path(rs["RUN_PATH"])
        self.param_version = rs.get("PARAM_VERSION", self.run_yymm)
        self.run_mode = rs.get("RUN_MODE", 1)

        self.param_path = self.run_path / "parameter"
        self.in_data_path = self.run_path / "data" / "input"
        self.prev_in_data_path = self.run_path / "data" / "prev_input"

        self.result_path = self.run_path / "data" / "output"
        self.report_path = self.run_path / "data" / "output"
        self.log_path = self.run_path / "logs"

        const = c.get("CONSTANT", {})
        self.days_in_year = const.get("days_in_year", 365.25)
        self.days_in_month = const.get("days_in_month", 30.5)

        io_setting = c.get("DATA_IO_SETTING", {})
        self.input_data_ext = io_setting.get("INPUT_DATA_EXT", "csv")
