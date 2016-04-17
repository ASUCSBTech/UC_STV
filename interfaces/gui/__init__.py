import logging
import wx

from interfaces.gui.WindowNew import WindowNew


class ElectionGUIApplication(wx.App):
    def OnInit(self):
        self.SetAppName("UCSB AS Election Tabulator")
        return 1


def run(parsed_arguments):
    log_destination = parsed_arguments.log_destination
    log_level = parsed_arguments.log_level

    # Setup logging in the application.
    logger = logging.getLogger("ui")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(process)d: %(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler(filename=log_destination + "/ui.log", encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    application = ElectionGUIApplication()
    application_new_ui = WindowNew(None)
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
