from datetime import datetime


class Logger:
    def _write_to_file_(self, msg):
        """
        sub method for open and write into .log file
        :param msg: str
        :return: None
        """
        with open(f"logs/{datetime.now().date()}.log", "a") as f:
            f.write(msg + "\n")

    @staticmethod
    def log(msg):
        """
        print into cmd and write to file log message
        :param msg: str
        :return: None
        """
        print(msg)
        logger._write_to_file_(msg)


logger = Logger()
