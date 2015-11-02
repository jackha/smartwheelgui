"""
Help to set up logger with WheelLogHandler, which logs to a separate file per 
wheel module.
"""
import logging
import os
import sys


class WheelLogHandler(logging.Handler):
    """
    Log wheel logging to separate files
    
    You must provide extra = {wheel_slug: ...} for the wheel specific logs
    Other logs will go to main.log
    """
    def __init__(self, logpath, *args, **kwargs):
        self.logpath = logpath
        super(WheelLogHandler, self).__init__(*args, **kwargs)

    def emit(self, record, *args, **kwargs):
        """
        Emit a record. 
        """
        try:
            msg = self.format(record)
            if record.levelno >= self.level:
                filename = '%s.log' % record.__dict__.get('wheel_slug', 'main')
                with open(os.path.join(self.logpath, filename), 'a') as f:
                    f.write(msg + '\n')
                # now log
                # print("*** %s" % (msg))
                # print(dir(record))
                # print(record.__dict__)
        except:
            pass


def setup_logging(
        logpath, file_level=logging.DEBUG, console_level=logging.DEBUG,
        file_formatter='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s',
        console_formatter='%(asctime)8s %(levelname)5s - %(message)s'):
    """
    filepath: the path to store all logging files in
    """
    if not os.path.exists(logpath):
        os.makedirs(logpath)

    # Set up root logger that logs everything.
    root_logger = logging.getLogger('')
    root_logger.setLevel(logging.DEBUG)

    # file_handler = logging.handlers.RotatingFileHandler(
    #     filename, mode='a', maxBytes=1000000, backupCount=1, encoding=None,
    #     delay=0)
    # file_handler.setLevel(file_level)
    # formatter = logging.Formatter(
    #         file_formatter,
    #         datefmt='%m%d %H:%M:%S')
    # file_handler.setFormatter(formatter)
    # root_logger.addHandler(file_handler)

    wheel_log_handler = WheelLogHandler(logpath)
    wheel_log_handler.setLevel(file_level)
    wheel_log_formatter = logging.Formatter(
            file_formatter,
            datefmt='%H:%M:%S')
    wheel_log_handler.setFormatter(wheel_log_formatter)
    root_logger.addHandler(wheel_log_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    formatter = logging.Formatter(
            console_formatter,
            datefmt='%H:%M:%S')
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    return root_logger
