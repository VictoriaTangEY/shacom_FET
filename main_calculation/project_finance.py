from util.loggers import createLogHandler


def run_project_finance(rc, parent_logger=None, param=None):
    """
    Main entry for financed emissions of:
    Project finance.

    rc: RunSetting instance
    parent_logger: optional logger to reuse; if None, a local logger is created.
    param: optional parameters dict.
    """
    logger = parent_logger or createLogHandler(
        "project_finance",
        rc.log_path / "Log_project_finance.log",
    )

    logger.info("Starting calculation for project finance.")
    # TODO: implement financed emissions logic for this asset class.

    if parent_logger is None:
        logger.info("Finished calculation for project finance.")
        logger.handlers.clear()

