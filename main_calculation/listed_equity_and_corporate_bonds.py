from util.loggers import createLogHandler


def run_listed_equity_and_corporate_bonds(rc, parent_logger=None, param=None):
    """
    Main entry for financed emissions of:
    Listed equity and corporate bonds.

    rc: RunSetting instance
    parent_logger: optional logger to reuse; if None, a local logger is created.
    param: optional parameters dict.
    """
    logger = parent_logger or createLogHandler(
        "listed_equity_and_corporate_bonds",
        rc.log_path / "Log_listed_equity_and_corporate_bonds.log",
    )

    logger.info("Starting calculation for listed equity and corporate bonds.")
    # TODO: implement financed emissions logic for this asset class.

    if parent_logger is None:
        logger.info("Finished calculation for listed equity and corporate bonds.")
        logger.handlers.clear()

