from datetime import datetime


class Logger:
    def _write_to_file_(self, msg):
        with open(f"logs/{datetime.now().date()}.log", "a") as f:
            f.write(msg + "\n")

    @staticmethod
    def log(msg):
        print(msg)
        logger._write_to_file_(msg)


logger = Logger()
