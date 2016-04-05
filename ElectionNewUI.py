import wx
import json
import logging
import sys
from Election import Election
from ElectionMainUI import ElectionMainUI


class ElectionNewUI(wx.Dialog):
    def __init__(self, *args, **kwds):
        wx.Dialog.__init__(self, *args, **kwds)

        # Configuration file.
        self.label_configuration_file = None
        self.text_ctrl_configuration_file = None
        self.button_configuration_file_browse = None

        # Candidate file.
        self.label_candidate_file = None
        self.text_ctrl_candidate_file = None
        self.button_candidate_file_browse = None

        # Ballot file.
        self.label_ballot_file = None
        self.text_ctrl_ballot_file = None
        self.button_ballot_file_browse = None

        # Create button.
        self.button_create = None

        # Display sizer.
        self.sizer_main = None
        self.sizer_form = None

        # File paths.
        self.configuration_file = None
        self.candidate_file = None
        self.ballot_file = None

        # Logger
        self.logger = logging.getLogger("application.ui.new")

        self.show_ui()
        self.Centre()

    def show_ui(self):
        self.label_configuration_file = wx.StaticText(self, wx.ID_ANY, "Configuration File")
        self.text_ctrl_configuration_file = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        self.button_configuration_file_browse = wx.Button(self, wx.ID_ANY, "Browse...")
        self.Bind(wx.EVT_BUTTON, self.ui_browse_configuration_file, self.button_configuration_file_browse)

        self.label_candidate_file = wx.StaticText(self, wx.ID_ANY, "Candidate File")
        self.text_ctrl_candidate_file = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        self.button_candidate_file_browse = wx.Button(self, wx.ID_ANY, "Browse...")
        self.Bind(wx.EVT_BUTTON, self.ui_browse_candidate_file, self.button_candidate_file_browse)

        self.label_ballot_file = wx.StaticText(self, wx.ID_ANY, "Ballot File")
        self.text_ctrl_ballot_file = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        self.button_ballot_file_browse = wx.Button(self, wx.ID_ANY, "Browse...")
        self.Bind(wx.EVT_BUTTON, self.ui_browse_ballot_file, self.button_ballot_file_browse)

        self.button_create = wx.Button(self, wx.ID_ANY, "Create")
        self.Bind(wx.EVT_BUTTON, self.ui_create, self.button_create)
        self.button_create.Enable(False)

        self.sizer_main = wx.FlexGridSizer(2, 1, 5, 0)
        self.sizer_form = wx.FlexGridSizer(3, 3, 5, 5)
        self.sizer_form.Add(self.label_configuration_file, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT | wx.TOP, 5)
        self.sizer_form.Add(self.text_ctrl_configuration_file, 0, wx.EXPAND | wx.TOP, 5)
        self.sizer_form.Add(self.button_configuration_file_browse, 0, wx.RIGHT | wx.TOP, 5)
        self.sizer_form.Add(self.label_candidate_file, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT, 5)
        self.sizer_form.Add(self.text_ctrl_candidate_file, 0, wx.EXPAND, 0)
        self.sizer_form.Add(self.button_candidate_file_browse, 0, wx.RIGHT, 5)
        self.sizer_form.Add(self.label_ballot_file, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT, 5)
        self.sizer_form.Add(self.text_ctrl_ballot_file, 0, wx.EXPAND, 0)
        self.sizer_form.Add(self.button_ballot_file_browse, 0, wx.RIGHT, 5)
        self.sizer_form.AddGrowableCol(1)
        self.sizer_main.Add(self.sizer_form, 1, wx.EXPAND, 0)
        self.sizer_main.Add(self.button_create, 0, wx.ALIGN_RIGHT | wx.BOTTOM | wx.RIGHT, 5)
        self.SetSizer(self.sizer_main)
        self.sizer_main.Fit(self)
        self.sizer_main.AddGrowableRow(0)
        self.sizer_main.AddGrowableCol(0)
        self.Layout()

        self.SetTitle("UCSB AS Election Tabulator")

    def ui_browse_configuration_file(self, event):
        election_configuration_file = wx.FileDialog(self, "", "", "", "Election Configuration files (*.json)|*.json", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if election_configuration_file.ShowModal() == wx.ID_CANCEL:
            return

        self.set_configuration_file(election_configuration_file.GetPath())
        self.ui_check_complete()

    def ui_browse_candidate_file(self, event):
        election_candidate_file = wx.FileDialog(self, "", "", "", "Candidate files (*.*)|*.*", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if election_candidate_file.ShowModal() == wx.ID_CANCEL:
            return

        self.set_candidate_file(election_candidate_file.GetPath())
        self.ui_check_complete()

    def ui_browse_ballot_file(self, event):
        election_ballot_file = wx.FileDialog(self, "", "", "", "Ballot files (*.*)|*.*", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if election_ballot_file.ShowModal() == wx.ID_CANCEL:
            return

        self.set_ballot_file(election_ballot_file.GetPath())
        self.ui_check_complete()

    def set_configuration_file(self, configuration_file):
        self.configuration_file = configuration_file
        self.text_ctrl_configuration_file.SetValue(self.configuration_file)

    def set_candidate_file(self, candidate_file):
        self.candidate_file = candidate_file
        self.text_ctrl_candidate_file.SetValue(self.candidate_file)

    def set_ballot_file(self, ballot_file):
        self.ballot_file = ballot_file
        self.text_ctrl_ballot_file.SetValue(self.ballot_file)

    def ui_create(self, event):
        try:
            election = Election(self.configuration_file)
        except (ValueError, KeyError, IOError):
            self.logger.error("Unable to parse configuration file from `%s`.", self.configuration_file, exc_info=sys.exc_info())
            wx.MessageDialog(self, "Unable to load configuration file. Please verify that the file specified is the correct configuration file.", caption="Load Error", style=wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()
            return

        try:
            election.load_candidates(self.candidate_file)
        except (ValueError, KeyError, IOError):
            self.logger.error("Unable to load candidate file from `%s`.", self.candidate_file, exc_info=sys.exc_info())
            wx.MessageDialog(self, "Unable to load candidate file. Please verify that the file specified is the correct candidate file.", caption="Load Error", style=wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()
            return

        try:
            progress_dialog = wx.ProgressDialog("Processing Ballots", "", maximum=100, parent=self, style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME)
            election.load_ballots(self.ballot_file, progress_dialog)
            progress_dialog.Destroy()
        except (ValueError, KeyError, IOError):
            self.logger.error("Unable to load ballot file from `%s`.", self.ballot_file, exc_info=sys.exc_info())
            wx.MessageDialog(self, "Unable to load ballot file. Please verify that the file specified is the correct ballot file.", caption="Load Error", style=wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()
            return

        for race in election.get_race_all():
            race.run()

        ElectionMainUI(None, election)
        self.EndModal(wx.ID_OK)

    def ui_check_complete(self):
        self.button_create.Enable(not not (self.configuration_file and self.candidate_file and self.ballot_file))
