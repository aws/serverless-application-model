# Logger configurations
import logging


class LoggingConfiguration:
    @staticmethod
    def configure_request_logger(logger):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter(
                "\nREQUEST LOG [%(test)s] | Time: %(asctime)s %(message)s | Status: %(status)s | Headers: %(headers)s"
            )
        )
        logger.addHandler(console_handler)
        logger.propagate = False
