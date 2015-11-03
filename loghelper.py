"""
Help to set up logger with WheelLogHandler, which logs to a separate file per 
wheel module.
"""
import logging
import os
import sys

logger = logging.getLogger(__name__)


def rotate_filenames_and_rename(filename, num_files):
    """
    hello.log will be renamed to hello.log.1,
    
    all existing hello.log.<num> (num < num_files) will be renamed to 
    hello.log.<num+1>
    
    hello.log.<num_files> will be deleted
    """
    filename_max = '%s.%d' % (filename, num_files)
    if os.path.exists(filename_max):
        os.remove(filename_max)
    for i in range(num_files, 0, -1):
        old_filename = '%s.%d' % (filename, i)
        new_filename = '%s.%d' % (filename, i+1)
        if os.path.exists(old_filename):
            os.rename(old_filename, new_filename)
    os.rename(filename, '%s.1' % (filename))


class WheelLogHandler(logging.Handler):
    """
    Log wheel logging to separate files
    
    You must provide extra = {wheel_slug: ...} for the wheel specific logs
    Other logs will go to main.log
    """
    def __init__(
        self, logpath, logrotate_filesize=1000000, logrotate_numfiles=10, 
        *args, **kwargs):
        
        self.logpath = logpath
        self.logrotate_filesize = logrotate_filesize
        self.logrotate_numfiles = logrotate_numfiles
        super(WheelLogHandler, self).__init__(*args, **kwargs)

    def emit(self, record, *args, **kwargs):
        """
        Emit a record. 
        """
        try:
            msg = self.format(record)
            if record.levelno >= self.level:
                filename = '%s.log' % record.__dict__.get('wheel_slug', 'main')
                full_filename = os.path.join(self.logpath, filename)
                with open(full_filename, 'a') as f:
                    f.write(msg + '\n')
                file_stat = os.stat(full_filename)
                if file_stat.st_size > self.logrotate_filesize:
                    # a bit tricky because we are in the logging routine
                    rotate_filenames_and_rename(
                        full_filename, self.logrotate_numfiles)
                    logger.info('Rotated logfile [%s].' % filename)              
        except:
           pass
           # logging should never stop executing main program


def setup_logging(
        logpath, file_level=logging.DEBUG, console_level=logging.DEBUG,
        file_formatter='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s',
        console_formatter='%(asctime)8s %(levelname)5s - %(message)s',
        logrotate_filesize=1000000, logrotate_numfiles=10):
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

    wheel_log_handler = WheelLogHandler(
        logpath, 
        logrotate_filesize=logrotate_filesize, 
        logrotate_numfiles=logrotate_numfiles)
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
