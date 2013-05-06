import logging

# shared logging format
logFormat = logging.Formatter("[%(asctime)s][%(funcName)s] - %(message)s", '%m/%d/%y %I:%M%p')


def get_custom_logger():
    return logging.getLogger("eyeFiLogger")


def setup_custom_logger():
    # Create the main logger
    logger = get_custom_logger()
    logger.setLevel(logging.DEBUG)

    # Create two handlers. One to print to the log and one to print to the console
    consoleHandler = logging.StreamHandler()
    # Set how both handlers will print the pretty log events
    consoleHandler.setFormatter(logFormat)
    # Append both handlers to the main Eye Fi Server logger
    logger.addHandler(consoleHandler)

    return logger


def setup_logfile(logfile):
    logger = get_custom_logger()
    fileHandler = logging.FileHandler(logfile, "w", encoding=None)
    fileHandler.setFormatter(logFormat)
    logger.addHandler(fileHandler)
