import wx
import json
from Election import Election
# TEST
from ElectionRace import ElectionRace
# END TEST

class ElectionUI(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(900, 680))

        self.election = None

        # Menu variables.
        self.menu = None
        self.menu_file = None
        self.menu_file_load_election_config = None
        self.menu_file_load_candidates = None
        self.menu_file_load_ballots = None
        self.menu_file_test = None

        self.show_ui()
        self.Centre()
        self.Show()

    def show_ui(self):
        self.CreateStatusBar()

        self.menu = wx.MenuBar()

        self.menu_file = wx.Menu()

        # File Menu > Load Election Configuration
        self.menu_file_load_election_config = self.menu_file.Append(wx.ID_ANY,
                                                                    "Load &Election Configuration\tCTRL+SHIFT+E",
                                                                    "Load election configuration.")
        self.Bind(wx.EVT_MENU, self.ui_load_election_config, self.menu_file_load_election_config)

        # File Menu > Load Candidates
        self.menu_file_load_candidates = self.menu_file.Append(wx.ID_ANY, "Load Candi&dates\tCTRL+SHIFT+D",
                                                               "Load candidates.")
        self.menu_file_load_candidates.Enable(False)
        self.Bind(wx.EVT_MENU, self.ui_load_candidates, self.menu_file_load_candidates)

        # File Menu > Load Ballots
        self.menu_file_load_ballots = self.menu_file.Append(wx.ID_ANY, "Load &Ballot Data\tCTRL+SHIFT+C",
                                                            "Load ballot data.")
        self.menu_file_load_ballots.Enable(False)
        self.Bind(wx.EVT_MENU, self.ui_load_ballot, self.menu_file_load_ballots)

        # TEMPORARY: File Menu > Test
        self.menu_file_test = self.menu_file.Append(wx.ID_ANY, "Test\tCTRL+SHIFT+T",
                                                            "Test it.")
        self.menu_file_test.Enable(False)
        self.Bind(wx.EVT_MENU, self.ui_test, self.menu_file_test)

        self.menu.Append(self.menu_file, "&File")

        self.SetMenuBar(self.menu)

    def ui_load_election_config(self, event):
        election_configuration_file = wx.FileDialog(self, "", "", "", "Election Configuration files (*.json)|*.json",
                                                   wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if election_configuration_file.ShowModal() == wx.ID_CANCEL:
            return

        try:
            with open(election_configuration_file.GetPath(), encoding="utf-8") as configuration_file:
                configuration = json.loads(configuration_file.read())
                self.election = Election(configuration)
                self.menu_file_load_candidates.Enable(True)
                self.menu_file_load_ballots.Enable(False)
                return
        except IOError as err:
            wx.MessageBox("Unable to load configuration file.", "Load Error", wx.OK | wx.ICON_ERROR)
            return

    def ui_load_candidates(self, event):
        election_candidate_file = wx.FileDialog(self, "", "", "", "Candidate files (*.*)|*.*",
                                             wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if election_candidate_file.ShowModal() == wx.ID_CANCEL:
            return

        try:
            self.election.load_candidates(election_candidate_file.GetPath())
            self.menu_file_load_ballots.Enable(True)
        except IOError as err:
            wx.MessageBox("Unable to load candidate file.", "Load Error", wx.OK | wx.ICON_ERROR)

    def ui_load_ballot(self, event):
        election_ballot_file = wx.FileDialog(self, "", "", "", "Ballot files (*.*)|*.*",
                                             wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if election_ballot_file.ShowModal() == wx.ID_CANCEL:
            return

        try:
            self.election.load_ballots(election_ballot_file.GetPath())
            self.menu_file_test.Enable(True)
        except IOError as err:
            wx.MessageBox("Unable to load ballot file.", "Load Error", wx.OK | wx.ICON_ERROR)

    def ui_test(self, event):
        all_races = self.election.race_get_all()
        for race in all_races:
            print(all_races[race].get_position())
            while all_races[race].get_state() == ElectionRace.INCOMPLETE:
                all_races[race].run()
            print(all_races[race].round_get_latest().get_round_votes())
            print(all_races[race].get_winners())