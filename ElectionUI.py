import wx
import wx.lib.delayedresult
import json
import time
from Election import Election
from ElectionUIRacePanel import ElectionUIRacePanel
from ElectionRace import ElectionRace
from ElectionRaceRound import ElectionRaceRound


class ElectionUI(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(900, 680))

        self.election = None

        self._election_states = {
            ElectionRace.COMPLETE: "Complete",
            ElectionRace.TABULATING: "Tabulating",
            ElectionRace.ADDING: "Adding"
        }

        self._election_round_states = {
            ElectionRaceRound.COMPLETE: "Complete",
            ElectionRaceRound.INCOMPLETE: "Incomplete"
        }

        # Menu variables.
        self.menu = None
        self.menu_file = None
        self.menu_file_load_election_config = None
        self.menu_file_load_candidates = None
        self.menu_file_load_ballots = None
        self.menu_file_test = None

        # Display select controls.
        self.panel_display_select = None
        self.label_race = None
        self.label_round = None
        self.label_speed = None
        self.combo_box_race = None
        self.combo_box_round = None
        self.slider_display_speed = None

        # Display grid.
        self.panel_display_grid = None
        self.grid_display = None

        # Display race controls.
        self.panel_display_control = None
        self.label_quota = None
        self.button_complete_round = None
        self.button_complete_race = None

        # Display sizer.
        self.sizer = None
        self.sizer_display_select = None
        self.sizer_display_grid = None
        self.sizer_display_control = None

        # Race combo-box option text to object relationship.
        self.combo_box_race_object = {}

        # Round combo-box option text to object relationship.
        self.combo_box_round_object = {}

        # Current race and round.
        self._current_race = None
        self._current_round = None

        # Currently running a race/round.
        self._current_running = False

        self.show_ui()
        self.Centre()
        self.Show()

    def show_ui(self):
        # Status Bar
        self.CreateStatusBar()

        # Menu
        self.menu = wx.MenuBar()

        # File Menu
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

        self.menu.Append(self.menu_file, "&File")

        self.SetMenuBar(self.menu)

        self.panel_display_select = wx.Panel(self, wx.ID_ANY)
        self.label_race = wx.StaticText(self.panel_display_select, wx.ID_ANY, "Race")
        self.label_round = wx.StaticText(self.panel_display_select, wx.ID_ANY, "Round")
        self.label_speed = wx.StaticText(self.panel_display_select, wx.ID_ANY, "Display Speed")
        self.combo_box_race = wx.ComboBox(self.panel_display_select, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN)
        self.combo_box_race.Enable(False)
        self.combo_box_round = wx.ComboBox(self.panel_display_select, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN)
        self.combo_box_round.Enable(False)
        self.panel_display_select.Bind(wx.EVT_COMBOBOX, self.ui_combobox_event)
        self.slider_display_speed = wx.Slider(self.panel_display_select, wx.ID_ANY, 0, 0, 100)
        self.slider_display_speed.SetValue(90)

        self.panel_display_grid = wx.Panel(self, wx.ID_ANY)
        self.grid_display = ElectionUIRacePanel(self.panel_display_grid)

        self.panel_display_control = wx.Panel(self, wx.ID_ANY)
        self.label_quota = wx.StaticText(self.panel_display_control, wx.ID_ANY, "")
        self.button_complete_round = wx.Button(self.panel_display_control, wx.ID_ANY, "Complete Round")
        self.button_complete_round.Enable(False)
        self.panel_display_control.Bind(wx.EVT_BUTTON, self.ui_complete_round, self.button_complete_round)
        self.button_complete_race = wx.Button(self.panel_display_control, wx.ID_ANY, "Complete Race")
        self.button_complete_race.Enable(False)
        self.panel_display_control.Bind(wx.EVT_BUTTON, self.ui_complete_race, self.button_complete_race)

        self.sizer_display_select = wx.FlexGridSizer(2, 6, 0, 0)
        self.sizer_display_select.AddGrowableCol(3)
        self.panel_display_select.SetSizer(self.sizer_display_select)

        self.sizer_display_select.Add((20, 1), 0, 0, 0)
        self.sizer_display_select.Add(self.label_race, 0, 0, 0)
        self.sizer_display_select.Add(self.label_round, 0, 0, 0)
        self.sizer_display_select.Add((20, 20), 0, wx.EXPAND, 0)
        self.sizer_display_select.Add(self.label_speed, 0, 0, 0)
        self.sizer_display_select.Add((20, 1), 0, 0, 0)
        self.sizer_display_select.Add((20, 1), 0, 0, 0)
        self.sizer_display_select.Add(self.combo_box_race, 0, wx.BOTTOM | wx.RIGHT, 10)
        self.sizer_display_select.Add(self.combo_box_round, 0, wx.BOTTOM, 10)
        self.sizer_display_select.Add((20, 20), 0, wx.EXPAND, 0)
        self.sizer_display_select.Add(self.slider_display_speed, 0, wx.BOTTOM | wx.EXPAND, 5)
        self.sizer_display_select.Add((20, 1), 0, 0, 0)

        self.sizer_display_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.panel_display_grid.SetSizer(self.sizer_display_grid)

        self.sizer_display_grid.Add((20, 1), 0, 0, 0)
        self.sizer_display_grid.Add(self.grid_display, 1, wx.ALL | wx.EXPAND, 0)
        self.sizer_display_grid.Add((20, 1), 0, 0, 0)

        self.sizer_display_control = wx.FlexGridSizer(1, 6, 0, 0)
        self.sizer_display_control.AddGrowableRow(0)
        self.sizer_display_control.AddGrowableCol(2)
        self.panel_display_control.SetSizer(self.sizer_display_control)

        self.sizer_display_control.Add((20, 1), 0, 0, 0)
        self.sizer_display_control.Add(self.label_quota, 0, wx.TOP | wx.EXPAND, 5)
        self.sizer_display_control.Add((1, 1), 0, wx.EXPAND, 0)
        self.sizer_display_control.Add(self.button_complete_round, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL | wx.EXPAND, 10)
        self.sizer_display_control.Add(self.button_complete_race, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.TOP, 10)
        self.sizer_display_control.Add((20, 1), 0, wx.EXPAND, 0)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.sizer.Add((1, 10), 0, 0, 0)
        self.sizer.Add(self.panel_display_select, 0, wx.EXPAND, 0)
        self.sizer.Add(self.panel_display_grid, 1, wx.EXPAND, 0)
        self.sizer.Add(self.panel_display_control, 0, wx.EXPAND, 0)
        self.sizer.Add((1, 5), 0, 0, 0)
        self.sizer.SetSizeHints(self)

        self.SetSize((750, 500))
        self.SetMinSize((750, 500))
        self.Layout()

    def ui_combobox_event(self, event):
        if event.GetEventObject() is self.combo_box_race:
            self.change_race(self.combo_box_race_object[self.combo_box_race.GetStringSelection()])
        elif event.GetEventObject() is self.combo_box_round:
            selection_text = self.combo_box_round.GetStringSelection()
            if selection_text == "Latest Round":
                self.change_round(self._current_race.get_round_latest())
            else:
                self.change_round(self.combo_box_round_object[selection_text])
        button_state = self._current_round.parent().state() != ElectionRace.COMPLETE
        self.button_complete_race.Enable(button_state)
        self.button_complete_round.Enable(button_state)
        self.button_complete_round.SetFocus()

    def ui_complete_round(self, event):
        self.ui_disable_all()

        # Complete the current race.
        wx.lib.delayedresult.startWorker(self.ui_complete_action_done, self.complete_current_round)

    def ui_complete_race(self, event):
        self.ui_disable_all()

        # Complete the current round.
        wx.lib.delayedresult.startWorker(self.ui_complete_action_done, self.complete_current_race)

    def ui_disable_all(self):
        # Disable the complete current round/race button
        # and also disable the race change combo box.
        self.button_complete_race.Enable(False)
        self.button_complete_round.Enable(False)
        self.combo_box_race.Enable(False)
        self.combo_box_round.Enable(False)

    def ui_complete_action_done(self, result):
        self.combo_box_race.Enable(True)
        self.combo_box_round.Enable(True)
        if self._current_round.parent().state() != ElectionRace.COMPLETE:
            self.button_complete_race.Enable(True)
            self.button_complete_round.Enable(True)

    def ui_load_election_config(self, event):
        election_configuration_file = wx.FileDialog(self, "", "", "", "Election Configuration files (*.json)|*.json",
                                                   wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if election_configuration_file.ShowModal() == wx.ID_CANCEL:
            return

        try:
            with open(election_configuration_file.GetPath(), encoding="utf-8") as configuration_file:
                configuration = json.loads(configuration_file.read())
                self.election = Election(configuration)
                self.ui_disable_all()
                self.grid_display.destroy_grid()
                self.menu_file_load_candidates.Enable(True)
                self.menu_file_load_ballots.Enable(False)
                return
        except (KeyError, IOError):
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
        except IOError:
            wx.MessageBox("Unable to load candidate file.", "Load Error", wx.OK | wx.ICON_ERROR)

    def ui_load_ballot(self, event):
        election_ballot_file = wx.FileDialog(self, "", "", "", "Ballot files (*.*)|*.*",
                                             wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if election_ballot_file.ShowModal() == wx.ID_CANCEL:
            return

        try:
            progress_dialog = wx.ProgressDialog("Processing Ballots", "", maximum=100, parent=self, style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME)
            self.election.load_ballots(election_ballot_file.GetPath(), progress_dialog)
            progress_dialog.Destroy()

            combo_box_text = []

            election_races = self.election.get_race_all()
            if "display_order" in election_races[0].extended_data():
                election_races.sort(key=lambda election_race: election_race.extended_data()["display_order"])
            else:
                election_races.sort(key=lambda election_race: election_race.position())

            for race in election_races:
                # Add the race to possible races.
                self.combo_box_race_object[race.position()] = race
                combo_box_text.append(race.position())

                # Creates the first round when run is called the first time.
                race.run()
            self.combo_box_race.SetItems(combo_box_text)
            self.change_race(election_races[0])
            self.combo_box_race.SetSelection(self.combo_box_race.FindString(self._current_race.position()))
            self.combo_box_round.Enable(True)
            self.combo_box_race.Enable(True)
            self.button_complete_race.Enable(True)
            self.button_complete_round.Enable(True)
        except IOError:
            wx.MessageBox("Unable to load ballot file.", "Load Error", wx.OK | wx.ICON_ERROR)

    def ui_update_statusbar(self):
        if self._current_race is None or self._current_round is None:
            return

        self.SetStatusText("Race: " + self._election_states[self._current_race.state()] + " | Round: " + self._election_round_states[self._current_round.state()])

    def change_race(self, election_race):
        if self._current_race is election_race:
            return

        self._current_race = election_race
        self.ui_update_rounds(False)
        self.ui_update_statusbar()
        self.change_round(election_race.get_round_latest())
        self.label_quota.SetLabel("Race: " + election_race.position() + "\nRace Winning Quota: " + str(election_race.droop_quota()))

    def change_round(self, election_round):
        self._current_round = election_round
        self.grid_display.set_round(election_round)
        self.ui_update_statusbar()

    def ui_update_rounds(self, preserve_selection=True):
        self.combo_box_round_object = {}
        combo_box_text = []
        current_selection = "Latest Round"

        for election_round in self._current_race.rounds():
            self.combo_box_round_object["Round " + str(election_round.round())] = election_round
            combo_box_text.append("Round " + str(election_round.round()))

        combo_box_text.append("Latest Round")

        if preserve_selection and self.combo_box_round.GetStringSelection():
            current_selection = self.combo_box_round.GetStringSelection()

        self.combo_box_round.SetItems(combo_box_text)

        current_selection_position = self.combo_box_round.FindString(current_selection)
        if current_selection_position is not wx.NOT_FOUND:
            self.combo_box_round.SetSelection(current_selection_position)

    def complete_current_race(self):
        while self._current_race.state() != ElectionRace.COMPLETE:
            self.complete_current_round()
            wx.Yield()

    def complete_current_round(self):
        # Jump to latest round.
        self.change_round(self._current_race.get_round_latest())
        self.combo_box_round.SetSelection(self.combo_box_round.FindString("Latest Round"))

        while self._current_round.state() != ElectionRaceRound.COMPLETE:
            self.ui_update_statusbar()
            self._current_round.parent().run()
            self.grid_display.update()
            time.sleep((self.slider_display_speed.GetMax()+1 - self.slider_display_speed.GetValue())*0.0001)
            wx.Yield()

        self.ui_update_statusbar()

        self.grid_display.update()
        wx.Yield()
        self.ui_update_rounds()
