import sys
import wx
import logging
import argparse
from ElectionNewUI import ElectionNewUI
from ElectionUI import ElectionUI


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


class ElectionApplication(wx.App):
    def OnInit(self):
        self.SetAppName("UCSB AS Election Tabulator")
        return 1


def main(argv=None):
    if argv is None:
        # Use sys.argv since argv was not passed in.
        argv = sys.argv

    parser = argparse.ArgumentParser(description="UCSB AS Elections Tabulator")
    parser_group_election = parser.add_argument_group("Election Configuration")
    parser_group_election.add_argument("--config", help="Election configuration file.", dest="config_file")
    parser_group_election.add_argument("--candidates", help="Election candidates file.", dest="candidate_file")
    parser_group_election.add_argument("--ballots", help="Election ballots file.", dest="ballot_file")
    parser_group_logging = parser.add_argument_group("Logging")
    parser_group_logging.add_argument("-l", "--log", help="Enable/disable logging for the application.", action="store_true", dest="log_enabled")
    parser_group_logging.add_argument("-ll", "--log-level", help="Level of logging.", default="DEBUG", dest="log_level")
    parser_group_logging.add_argument("-ld", "--log-destination", help="Set the file log output.", default="event.log", dest="log_destination")

    parsed_arguments = parser.parse_args(argv[1:])

    log_destination = parsed_arguments.log_destination
    log_level = parsed_arguments.log_level

    # Setup logging in the application.
    logger = logging.getLogger("application")
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(filename=log_destination)
    file_handler.setLevel(log_level)

    formatter = logging.Formatter("%(process)d: %(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger.info("Application started.")

    application = ElectionApplication()
    application_new_ui = ElectionNewUI(None)
    if parsed_arguments.config_file:
        application_new_ui.set_configuration_file(parsed_arguments.config_file)
    if parsed_arguments.candidate_file:
        application_new_ui.set_candidate_file(parsed_arguments.candidate_file)
    if parsed_arguments.ballot_file:
        application_new_ui.set_ballot_file(parsed_arguments.ballot_file)
    application_new_ui.ui_check_complete()
    application_new_ui.ShowModal()
    application_new_ui.Destroy()
    application.MainLoop()


if __name__ == "__main__":
    sys.exit(main())
