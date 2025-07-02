import logging
import os
import sys

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'app.log')

# Ensure log directory exists (though it's also created by a run_in_bash_session step)
# This is a fallback if the script is run in an environment where the prior mkdir didn't happen or isn't persistent.
os.makedirs(LOG_DIR, exist_ok=True)

# Determine the name of the calling script for more informative logs
# This might be tricky in CGI context as __file__ of the main script is what we want.
# We'll pass the script name to the get_logger function.

def get_logger(script_name_for_log):
    # Use a fixed logger name to ensure all scripts use the same logger instance and handlers
    logger = logging.getLogger("MatricaAppLogger")

    # Prevent adding multiple handlers if get_logger is called multiple times by the same process
    # (though each CGI script invocation is typically a new process)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG) # Set to DEBUG to capture all levels; can be configured higher in production

        # File Handler
        # Use a WatchedFileHandler if available and appropriate for production (handles log rotation by external tools)
        # For simplicity here, using RotatingFileHandler or just FileHandler.
        # Let's use FileHandler for now, rotation can be mentioned in README for production.
        fh = logging.FileHandler(LOG_FILE)
        fh.setLevel(logging.DEBUG)

        # Console Handler (useful for local dev if CGI output to console is monitored, less so in prod)
        # For CGI, stderr is often where this would go and get mixed with web server error logs.
        # We are directing Python's stderr prints in APIs to actual server logs, so this might be redundant
        # or could be configured differently. For now, let's keep it simple.
        # ch = logging.StreamHandler(sys.stderr) # Or sys.stdout
        # ch.setLevel(logging.ERROR)

        # Formatter
        # Include the name of the script that generated the log message
        formatter = logging.Formatter(
            f'%(asctime)s - %(levelname)s - [{script_name_for_log}] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        # ch.setFormatter(formatter)

        logger.addHandler(fh)
        # logger.addHandler(ch)

    # To use the specific script name in each log message without changing the logger instance name,
    # we can return a logger adapter or just rely on the formatter as done above.
    # The formatter solution is simpler for this context.
    return logger

# Example usage (for testing this module directly, not for actual use in other scripts):
if __name__ == '__main__':
    # Get the name of the current script (logger_config.py)
    current_script_name = os.path.basename(__file__)
    logger = get_logger(current_script_name)

    logger.debug("This is a debug message from logger_config.")
    logger.info("This is an info message from logger_config.")
    logger.warning("This is a warning message from logger_config.")
    logger.error("This is an error message from logger_config.")
    try:
        x = 1 / 0
    except ZeroDivisionError:
        logger.exception("This is an exception message from logger_config (includes stack trace).")

    print(f"Logging configured. Check {LOG_FILE}")
