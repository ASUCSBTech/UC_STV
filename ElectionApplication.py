import sys
import argparse
import os
import logging
import interfaces.gui


def main(argv=None):
    if argv is None:
        # Use sys.argv since argv was not passed in.
        argv = sys.argv

    parser = argparse.ArgumentParser(description="UCSB AS Elections Tabulator")
    parser.add_argument("--headless", help="Headless mode (no GUI).", action="store_true", dest="headless")
    parser_group_election = parser.add_argument_group("Election Configuration")
    parser_group_election.add_argument("--config", help="Election configuration file.", dest="config_file")
    parser_group_election.add_argument("--candidates", help="Election candidates file.", dest="candidate_file")
    parser_group_election.add_argument("--ballots", help="Election ballots file.", dest="ballot_file")
    parser_group_logging = parser.add_argument_group("Logging")
    parser_group_logging.add_argument("-l", "--log", help="Enable/disable logging for the application.", action="store_true", dest="log_enabled")
    parser_group_logging.add_argument("-ll", "--log-level", help="Level of logging.", default="DEBUG", dest="log_level")
    parser_group_logging.add_argument("-ld", "--log-destination", help="Set the log output directory.", default="./", dest="log_destination")

    parsed_arguments = parser.parse_args(argv[1:])

    parsed_arguments.log_destination = os.path.normpath(os.path.join(os.path.join(os.path.dirname(__file__)), parsed_arguments.log_destination))

    # Setup logging in the application.
    logger = logging.getLogger("election")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(process)d: %(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler(filename=parsed_arguments.log_destination + "/event.log")
    file_handler.setLevel(parsed_arguments.log_level)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    if parsed_arguments.headless:
        # Not implemented
        print("Headless mode is currently not implemented.")
    elif not parsed_arguments.headless:
        interfaces.gui.run(parsed_arguments)

if __name__ == "__main__":
    sys.exit(main())
