import sys
import argparse
import os
import logging
import logging.handlers
import interfaces.gui


def main(argv=None):
    if argv is None:
        # Use sys.argv since argv was not passed in.
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="UCSB AS Elections Tabulator")
    # Headless mode is not implemented.
    # parser.add_argument("--headless", help="Headless mode (no GUI).", action="store_true", dest="headless")
    parser_group_election = parser.add_argument_group("election configuration")
    parser_group_election.add_argument("--config", help="election configuration file", dest="config_file")
    parser_group_election.add_argument("--candidates", help="election candidates file", dest="candidate_file")
    parser_group_election.add_argument("--ballots", help="election ballots file", dest="ballot_file")
    parser_group_logging = parser.add_argument_group("logging")
    parser_group_logging.add_argument("--no-log", help="disable logging for the application", action="store_false", default=True, dest="log_enabled")
    parser_group_logging.add_argument("-ll", "--log-level", help="set the level of logging", default="DEBUG", dest="log_level")
    parser_group_logging.add_argument("-ld", "--log-destination", help="set the log output directory", default="./logs/", dest="log_destination")

    parsed_arguments = parser.parse_args(argv)

    parsed_arguments.log_destination = os.path.normpath(os.path.join(os.path.join(os.path.dirname(__file__)), parsed_arguments.log_destination))
    if not os.path.exists(parsed_arguments.log_destination):
        os.makedirs(parsed_arguments.log_destination)

    # Setup logging in the application.
    if not parsed_arguments.log_enabled:
        # Disable logging by preventing logging of all levels of errors.
        logging.disable(logging.CRITICAL)

    logger = logging.getLogger("election")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(process)d: %(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler(filename=parsed_arguments.log_destination + "/event.log")
    file_handler.setLevel(parsed_arguments.log_level)
    file_handler.setFormatter(formatter)

    memory_handler = logging.handlers.MemoryHandler(1024 * 100, target=file_handler)

    logger.addHandler(memory_handler)

    # Headless mode is not implemented.
    # if parsed_arguments.headless:
    #     print("Headless mode is currently not implemented.")
    # elif not parsed_arguments.headless:
    #     interfaces.gui.run(parsed_arguments)
    interfaces.gui.run(parsed_arguments)

if __name__ == "__main__":
    sys.exit(main())
