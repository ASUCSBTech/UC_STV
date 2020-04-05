import logging
import time
import threading
import sys

import wx
import wx.lib.newevent
import wx.lib.delayedresult

from interfaces.gui.DialogAbout import DialogAbout
from interfaces.gui.PanelRaceTable import PanelRaceTable
from backend.ElectionRace import ElectionRace
from backend.ElectionRaceRound import ElectionRaceRound

TabulationProgressEvent, EVT_TABULATION_PROGRESS = wx.lib.newevent.NewEvent()
TabulationCompleteEvent, EVT_TABULATION_COMPLETE = wx.lib.newevent.NewEvent()


class WindowMain(wx.Frame):

    def __init__(self, parent, election):
        wx.Frame.__init__(self, parent, size=(900, 680))

        self.logger = logging.getLogger("ui.main")

        self.election = election

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
        self.menu_file_new = None
        self.menu_help = None
        self.menu_help_about = None

        # Window panel.
        self.window_panel = None

        # Display select controls.
        self.panel_display_select = None
        self.label_race = None
        self.label_round = None
        self.label_speed = None
        self.combo_box_race = None
        self.combo_box_round = None
        self.slider_display_speed = None

        #Font sizer
        self.label_font = None
        self.font_sizer = None

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

        # Current round.
        self._current_round = None

        # Current round worker.
        self._current_worker = None

        self.show_ui()
        self.Centre()
        self.Show()
        self.logger.info("Main application user interface displayed.")

    def show_ui(self):
        self.logger.info("Launching main application user interface.")

        # Status Bar
        self.CreateStatusBar()

        # Menu
        self.menu = wx.MenuBar()

        # File Menu
        self.logger.debug("Creating file menu.")
        self.menu_file = wx.Menu()

        # File Menu > New Election
        self.menu_file_new = self.menu_file.Append(wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.show_new, self.menu_file_new)

        self.menu.Append(self.menu_file, "&File")

        # Help Menu
        self.logger.debug("Creating help menu.")
        self.menu_help = wx.Menu()

        # Help Menu > About
        self.menu_help_about = self.menu_help.Append(wx.ID_ABOUT, "&About UCSB AS Election Tabulator")
        self.Bind(wx.EVT_MENU, self.show_about, self.menu_help_about)

        self.menu.Append(self.menu_help, "&Help")

        self.SetMenuBar(self.menu)

        self.window_panel = wx.Panel(self, wx.ID_ANY)

        self.panel_display_select = wx.Panel(self.window_panel, wx.ID_ANY)
        self.label_race = wx.StaticText(self.panel_display_select, wx.ID_ANY, "Race")
        self.label_round = wx.StaticText(self.panel_display_select, wx.ID_ANY, "Round 1")
        self.label_font = wx.StaticText(self.panel_display_select, wx.ID_ANY, "Font Size")
        self.label_speed = wx.StaticText(self.panel_display_select, wx.ID_ANY, "Display Speed")
        self.combo_box_race = wx.ComboBox(self.panel_display_select, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN)
        self.combo_box_round = wx.ComboBox(self.panel_display_select, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN)
        self.panel_display_select.Bind(wx.EVT_COMBOBOX, self.ui_combobox_event)
        self.slider_display_speed = wx.Slider(self.panel_display_select, wx.ID_ANY, 0, 0, 100)
        self.slider_display_speed.SetValue(90)
        self.panel_display_select.Bind(wx.EVT_SLIDER, self.ui_slider_event)

        self.font_sizer = wx.SpinCtrl(self.panel_display_select, value = "13", pos = (335, 18))
        self.panel_display_select.Bind(wx.EVT_SPINCTRL, self.font_event, self.font_sizer)

        self.panel_display_grid = wx.Panel(self.window_panel, wx.ID_ANY)
        self.grid_display = PanelRaceTable(self.panel_display_grid)

        self.panel_display_control = wx.Panel(self.window_panel, wx.ID_ANY)
        self.label_quota = wx.StaticText(self.panel_display_control, wx.ID_ANY, "")
        # Allow override of font size in label.
        if wx.SystemOptions.HasOption("font-size"):
            font = self.label_quota.GetFont()
            font.SetPointSize(wx.SystemOptions.GetOptionInt("font-size"))
            self.label_quota.SetFont(font)

        self.button_complete_round = wx.Button(self.panel_display_control, wx.ID_ANY, "Complete Round")
        self.panel_display_control.Bind(wx.EVT_BUTTON, self.ui_complete_round, self.button_complete_round)
        self.button_complete_race = wx.Button(self.panel_display_control, wx.ID_ANY, "Complete Race")
        self.panel_display_control.Bind(wx.EVT_BUTTON, self.ui_complete_race, self.button_complete_race)

        self.sizer_display_select = wx.FlexGridSizer(2, 6, 0, 0)
        self.sizer_display_select.AddGrowableCol(3)
        self.panel_display_select.SetSizer(self.sizer_display_select)

        self.sizer_display_select.Add((20, 1), 0, 0, 0)
        self.sizer_display_select.Add(self.label_race, 0, 0, 0)
        self.sizer_display_select.Add(self.label_round, 0, 0, 0)
        self.sizer_display_select.Add(self.label_font, 0, 0, 0)
        self.sizer_display_select.Add(self.label_speed, 0, 0, 0)
        self.sizer_display_select.Add((20, 1), 0, 0, 0)
        self.sizer_display_select.Add((20, 1), 0, 0, 0)
        self.sizer_display_select.Add(self.combo_box_race, 0, wx.BOTTOM | wx.RIGHT, 10)
        self.sizer_display_select.Add(self.combo_box_round, 0, wx.BOTTOM, 10)
        self.sizer_display_select.Add((20, 20), 0, wx.EXPAND, 0)


        self.sizer_display_select.Add(self.slider_display_speed, 0, wx.BOTTOM | wx.EXPAND, 5)

        self.sizer_display_select.Add((20,1), 0, 0, 0)

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
        self.window_panel.SetSizer(self.sizer)

        self.sizer.Add(self.panel_display_select, 0, wx.EXPAND | wx.TOP, 10)
        self.sizer.Add(self.panel_display_grid, 1, wx.EXPAND, 0)
        self.sizer.Add(self.panel_display_control, 0, wx.EXPAND | wx.BOTTOM, 5)
        self.sizer.SetSizeHints(self)

        self.SetSize((750, 500))
        self.SetMinSize((750, 500))
        self.Layout()

        self.SetTitle("UCSB AS Election Tabulator")

        # Setup the UI state.
        combo_box_text = []

        election_races = self.election.get_race_all()
        election_race_count = len(election_races)
        election_races.sort(key=lambda election_race: (election_race_count+1 if "display_order" not in election_race.extended_data() else election_race.extended_data()["display_order"], election_race.position()))

        for race in election_races:
            # Add the race to possible races.
            self.combo_box_race_object[race.position()] = race
            combo_box_text.append(race.position())

        self.combo_box_race.SetItems(combo_box_text)
        self.change_race(election_races[0])
        self.combo_box_race.SetSelection(self.combo_box_race.FindString(self._current_round.parent().position()))

        if "default_speed" in self.election.configuration()["general"]:
            self.logger.debug("Default tabulation speed set at `%d`.", self.election.configuration()["general"]["default_speed"])
            self.slider_display_speed.SetValue(self.election.configuration()["general"]["default_speed"])

    def show_about(self, event):
        DialogAbout(self)

    def show_new(self, event):
        if wx.MessageDialog(self, "There is currently an election open. Would you like to close this election?", caption="Confirm Close", style=wx.YES_NO | wx.NO_DEFAULT | wx.CENTRE).ShowModal() == wx.ID_YES:
            self.Close(True)
            from interfaces.gui.WindowNew import WindowNew
            application_new_ui = WindowNew(None)
            application_new_ui.ShowModal()
            application_new_ui.Destroy()

    def ui_combobox_event(self, event):
        if event.GetEventObject() is self.combo_box_race:
            self.logger.info("Changed display to `%s` race.", self.combo_box_race.GetStringSelection())
            self.change_race(self.combo_box_race_object[self.combo_box_race.GetStringSelection()])
        elif event.GetEventObject() is self.combo_box_round:
            selection_text = self.combo_box_round.GetStringSelection()

            if selection_text == "Latest Round":
                self.change_round(self._current_round.parent().get_round_latest())
                self.label_round.SetLabel("Round " + str(self._current_round.parent().get_round_latest()))
            else:
                self.change_round(self.combo_box_round_object[selection_text])
                self.label_round.SetLabel(selection_text)
        button_state = self._current_round.parent().state() != ElectionRace.COMPLETE
        self.button_complete_race.Enable(button_state)
        self.button_complete_round.Enable(button_state)
        self.button_complete_round.SetFocus()

    def font_event(self, evt):
        font_size = evt.GetPosition() 
        self.grid_display.setGridFont(font_size)
        self.logger.info("Changed font size to: %d\n" % font_size)

    def ui_slider_event(self, event):
        if self._current_worker is None or not self._current_worker.is_alive():
            return

        self._current_worker.set_processing_delay(self.slider_display_speed.GetMax() + 1 - self.slider_display_speed.GetValue())

    def ui_complete_round(self, event):
        self.logger.info("Received `%s` button click.", event.GetEventObject().GetLabelText())
        self.ui_disable_all()
        self.complete_current_round()

    def ui_complete_race(self, event):
        self.logger.info("Received `%s` button click.", event.GetEventObject().GetLabelText())
        self.ui_disable_all()
        self.complete_current_race()

    def ui_disable_all(self):
        # Disable the complete current round/race button
        # and also disable the race change combo box.
        self.button_complete_race.Enable(False)
        self.button_complete_round.Enable(False)
        self.combo_box_race.Enable(False)
        self.combo_box_round.Enable(False)
        self.menu_file_new.Enable(False)

    def ui_complete_action_done(self):
        self.combo_box_race.Enable(True)
        self.combo_box_round.Enable(True)
        self.menu_file_new.Enable(True)
        if self._current_round.parent().state() != ElectionRace.COMPLETE:
            self.button_complete_race.Enable(True)
            self.button_complete_round.Enable(True)

    def ui_update_statusbar(self, race_state, round_state):
        self.SetStatusText("Race: " + self._election_states[race_state] + " | Round: " + self._election_round_states[round_state])

    def ui_update_rounds(self, preserve_selection=True):
        self.combo_box_round_object = {}
        combo_box_text = []
        current_selection = "Latest Round"

        for election_round in self._current_round.parent().rounds():
            self.combo_box_round_object["Round " + str(election_round.round())] = election_round
            combo_box_text.append("Round " + str(election_round.round()))

        combo_box_text.append("Latest Round")

        if preserve_selection and self.combo_box_round.GetStringSelection():
            current_selection = self.combo_box_round.GetStringSelection()

        self.combo_box_round.SetItems(combo_box_text)

        current_selection_position = self.combo_box_round.FindString(current_selection)
        if current_selection_position is not wx.NOT_FOUND:
            self.combo_box_round.SetSelection(current_selection_position)

    def change_race(self, election_race):
        if self._current_round and election_race is self._current_round.parent():
            return

        self.change_round(election_race.get_round_latest())
        self.label_round.SetLabel("Round " + str(election_race.get_round_latest()))
        self.ui_update_rounds(False)
        self.label_quota.SetLabel("Race: " + self.label_quota.EscapeMnemonics(election_race.position()) + "\nRace Winning Quota: " + str(election_race.droop_quota()))
        self.grid_display.colorReset()

    def change_round(self, election_round):
        if election_round is not self._current_round:
            self.logger.info("Changed display to round `%s` of race `%s`.", election_round, election_round.parent())
        self._current_round = election_round
        self.grid_display.update(ElectionRace.get_data_table(election_round))
        self.ui_update_statusbar(election_round.parent().state(), election_round.state())
        self.grid_display.colorReset()

    def complete_current_race(self):
        # Jump to latest round.
        self.ui_disable_all()
        self.change_round(self._current_round.parent().get_round_latest())
        self.combo_box_round.SetSelection(self.combo_box_round.FindString("Latest Round"))

        self._current_worker = TabulationThread(self, self._current_round, 50, self.slider_display_speed.GetMax() + 1 - self.slider_display_speed.GetValue(), TabulationThread.TYPE_COMPLETE_RACE)
        self._current_worker.start()
        self.Bind(EVT_TABULATION_PROGRESS, self.tabulation_on_progress)
        self.Bind(EVT_TABULATION_COMPLETE, self.tabulation_on_complete)

    def complete_current_round(self):
        # Jump to latest round.
        self.ui_disable_all()
        self.change_round(self._current_round.parent().get_round_latest())
        self.combo_box_round.SetSelection(self.combo_box_round.FindString("Latest Round"))
        self.label_round.SetLabel("Round " + str(self._current_round.parent().get_round_latest()))
        self._current_worker = TabulationThread(self, self._current_round, 50, self.slider_display_speed.GetMax() + 1 - self.slider_display_speed.GetValue(), TabulationThread.TYPE_COMPLETE_ROUND)
        self._current_worker.start()
        self.Bind(EVT_TABULATION_PROGRESS, self.tabulation_on_progress)
        self.Bind(EVT_TABULATION_COMPLETE, self.tabulation_on_complete)

    def tabulation_on_progress(self, event):
        self.grid_display.update(event.table_data) #update_layout=False
        self.ui_update_statusbar(event.race_state, event.round_state)
        self.label_round.SetLabel("Round " + str(self._current_round.parent().get_round_latest()))

    def tabulation_on_complete(self, event):
        self.change_round(self._current_round.parent().get_round_latest())
        self.ui_update_rounds()
        self.ui_complete_action_done()
        election_races = self.election.get_race_all()
        current_race_number = self.combo_box_race.FindString(self._current_round.parent().position())
        this_round = self._current_round.parent().get_round_latest().round()
        if(self._current_round.parent().state() == ElectionRace.COMPLETE):
            self.grid_display.highlightWinners(election_races[current_race_number].max_winners())

class TabulationThread(threading.Thread):
    (TYPE_COMPLETE_ROUND, TYPE_COMPLETE_RACE) = range(2)

    def __init__(self, notify_window, election_round, update_interval, processing_delay, completion_type):
        threading.Thread.__init__(self)
        self._notify_window = notify_window
        self._election_round = election_round
        self._update_interval = update_interval
        self._processing_delay = processing_delay
        self._completion_type = completion_type
        self.logging = logging.getLogger("ui.tabulator_thread")

    def set_update_interval(self, update_interval):
        self.logging.debug("Changed update interval to `%d`.", update_interval)
        self._update_interval = update_interval

    def set_processing_delay(self, processing_delay):
        self.logging.debug("Changed processing delay to `%d`.", processing_delay)
        self._processing_delay = processing_delay

    def run(self):
        self.logging.debug("Starting election tabulator thread.")
        try:
            if self._completion_type is self.TYPE_COMPLETE_ROUND:
                self.complete_round()
            elif self._completion_type is self.TYPE_COMPLETE_RACE:
                parent_election = self._election_round.parent()
                while parent_election.state() != ElectionRace.COMPLETE:
                    self.complete_round()
                    self._election_round = parent_election.get_round_latest()
        except Exception as e:
            self.logging.error(e, exc_info=sys.exc_info())

        wx.PostEvent(self._notify_window, TabulationCompleteEvent())
        self.logging.debug("Completed election tabulator thread.")

    def complete_round(self):
        iteration = 0

        while self._election_round.state() != ElectionRaceRound.COMPLETE:
            self._election_round.parent().run()
            if iteration % self._update_interval == 0:
                table_data = ElectionRace.get_data_table(self._election_round)
                race_state = self._election_round.parent().state()
                round_state = self._election_round.state()
                wx.PostEvent(self._notify_window, TabulationProgressEvent(race_state=race_state, round_state=round_state, table_data=table_data))
            time.sleep(self._processing_delay * 0.0001)
            iteration += 1
        self._election_round.parent().run()