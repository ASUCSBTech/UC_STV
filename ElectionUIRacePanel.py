import wx
import wx.grid
import math
from ElectionRaceRound import ElectionRaceRound
from ElectionCandidateState import ElectionCandidateState


class ElectionUIRacePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.grid = self.create_grid(None)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.grid, 1, wx.ALL | wx.EXPAND, 0)

        self.SetSizer(self.sizer)

        self._election_round = None
        self._election_race = None

    def on_size(self, event):
        columns = self.grid.GetNumberCols()
        width = 0
        for i in range(columns-1):
            width += self.grid.GetColSize(i)

        frame_width = self.grid.GetGridWindow().GetClientRect().GetWidth()
        remaining_width = frame_width - width

        self.grid.SetColSize(columns-1, -1)
        if self.grid.GetColSize(columns-1) < remaining_width:
            self.grid.SetColSize(columns-1, remaining_width)

        if event and self.GetAutoLayout():
            self.Layout()

        wx.Yield()

    def update(self):
        self.grid.GetTable().update()
        self.grid.ForceRefresh()

    def get_round(self):
        return self._election_round

    def set_round(self, election_round):
        if election_round is self._election_round:
            return

        if election_round.parent() is self._election_race:
            self.grid.GetTable().set_round(election_round)
            self._election_round = election_round
            return

        self._election_round = election_round
        self._election_race = election_round.parent()

        self.sizer.Remove(0)
        self.grid = self.create_grid(election_round)
        self.grid.GetGridWindow().Bind(wx.EVT_SIZE, self.on_size)

        self.sizer.Add(self.grid, 1, wx.ALL | wx.EXPAND, 0)
        self.sizer.Layout()

        wx.Yield()

        self.update()

        # Resize the columns to the correct size.
        self.grid.AutoSizeColumns(setAsMin=False)
        self.grid.SetColSize(2, 90)
        self.grid.SetColSize(3, 90)
        self.on_size(None)
        wx.Yield()

    def create_grid(self, election_round):
        new_grid = wx.grid.Grid(self, wx.ID_ANY)
        new_grid.SetTable(ElectionUIRacePanel.RaceGridData(None), True)
        new_grid.AutoSize()
        new_grid.EnableEditing(False)
        new_grid.DisableCellEditControl()
        new_grid.DisableDragColMove()
        new_grid.DisableDragColSize()
        new_grid.DisableDragGridSize()
        new_grid.DisableDragRowSize()

        # Use the default label font, but in a normal font weight.
        grid_label_font = new_grid.GetLabelFont()
        grid_label_font.SetWeight(wx.FONTWEIGHT_NORMAL)
        new_grid.SetLabelFont(grid_label_font)

        # Set the column label size to be the height of the text at
        # column zero (first column) plus five.
        new_grid.SetColLabelSize(
            wx.MemoryDC().GetFullMultiLineTextExtent(new_grid.GetColLabelValue(0),
                                                     font=new_grid.GetLabelFont())[1] + 5)

        new_grid.SetRowLabelSize(0)

        new_grid.GetTable().set_round(election_round)
        return new_grid

    class RaceGridData(wx.grid.GridTableBase):
        def __init__(self, election_round):
            wx.grid.GridTableBase.__init__(self)
            self._election_round = election_round
            self._table_columns = ["Candidate", "Party", "Status", "Score", "Quota Percentage"]
            self._table_rows = []
            self._candidate_states = {
                ElectionCandidateState.WON: "WON",
                ElectionCandidateState.RUNNING: "RUNNING",
                ElectionCandidateState.ELIMINATED: "ELIMINATED"
            }
            self.update()

        def GetNumberRows(self):
            return len(self._table_rows)

        def GetNumberCols(self):
            return len(self._table_columns)

        def IsEmptyCell(self, row, col):
            # Cells will never be empty because there
            # are exactly the correct number of cells
            # as there are rows and columns.
            return False

        def GetColLabelValue(self, col):
            return self._table_columns[col]

        def GetTypeName(self, row, col):
            return wx.grid.GRID_VALUE_STRING

        def GetValue(self, row, col):
            try:
                return str(self._table_rows[row][col])
            except IndexError:
                return ""

        def SetValue(self, row, col, value):
            # Values should not be editable.
            return

        def set_round(self, election_round):
            if election_round is self._election_round:
                return

            self._election_round = election_round
            self.update()

            cell_attribute = wx.grid.GridCellAttr()
            renderer = ElectionUIRacePanel.RaceGridBarRender()
            cell_attribute.SetRenderer(renderer)
            self.GetView().SetColAttr(self._table_columns.index("Quota Percentage"), cell_attribute)

            cell_attribute = wx.grid.GridCellAttr()
            cell_attribute.SetAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
            self.GetView().SetColAttr(self._table_columns.index("Status"), cell_attribute)

        def update(self):
            if self._election_round is None:
                return

            current_row_count = len(self._table_rows)
            if self._election_round.state() is ElectionRaceRound.INCOMPLETE:
                candidate_states = self._election_round.get_candidates_state(ElectionRaceRound.CANDIDATE_PRE_STATE)
                candidate_state_groups = self._election_round.get_candidates_by_state(
                    ElectionRaceRound.CANDIDATE_PRE_STATE)
            else:
                candidate_states = self._election_round.get_candidates_state(ElectionRaceRound.CANDIDATE_POST_STATE)
                candidate_state_groups = self._election_round.get_candidates_by_state(
                    ElectionRaceRound.CANDIDATE_POST_STATE)

            scores = self._election_round.get_candidates_score()

            new_table_rows = []
            score_resolution = 4

            # Grouped order in the following:
            # WON - ordered by winning round # in ascending order and winning round score.
            # RUNNING - ordered by round score
            # ELIMINATED - ordered by eliminated round in descending order
            table_group_won = sorted(candidate_state_groups[ElectionCandidateState.WON], key=lambda sort_candidate: (
                                     self._election_round.round() - candidate_states[sort_candidate].round().round(),
                                     candidate_states[sort_candidate].round().get_candidate_score(sort_candidate)),
                                     reverse=True)
            for candidate in table_group_won:
                candidate_score = candidate_states[candidate].round().get_candidate_score(candidate)
                new_table_rows.append([
                    candidate.name(),
                    candidate.party(),
                    self._candidate_states[ElectionCandidateState.WON],
                    self.round_down(candidate_score, score_resolution),
                    candidate_score / self._election_round.parent().droop_quota()
                ])

            table_group_running = sorted(candidate_state_groups[ElectionCandidateState.RUNNING],
                                         key=lambda sort_candidate: scores[sort_candidate], reverse=True)
            for candidate in table_group_running:
                candidate_score = scores[candidate]
                new_table_rows.append([
                    candidate.name(),
                    candidate.party(),
                    self._candidate_states[ElectionCandidateState.RUNNING],
                    self.round_down(candidate_score, score_resolution),
                    candidate_score / self._election_round.parent().droop_quota()
                ])

            table_group_eliminated = sorted(candidate_state_groups[ElectionCandidateState.ELIMINATED],
                                            key=lambda sort_candidate: (
                                            candidate_states[sort_candidate].round().round(),
                                            candidate_states[sort_candidate].round().get_candidate_score(
                                                sort_candidate)), reverse=True)
            for candidate in table_group_eliminated:
                candidate_score = candidate_states[candidate].round().get_candidate_score(candidate)
                new_table_rows.append([
                    candidate.name(),
                    candidate.party(),
                    self._candidate_states[ElectionCandidateState.ELIMINATED],
                    "0 (" + str(self.round_down(candidate_score, score_resolution)) + ")",
                    "0"
                ])

            self._table_rows = new_table_rows

            self.GetView().BeginBatch()
            new_row_count = len(self._table_rows)
            if new_row_count < current_row_count:
                msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, new_row_count - 1,
                                               current_row_count - new_row_count)
                self.GetView().ProcessTableMessage(msg)
            elif new_row_count > current_row_count:
                msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED,
                                               new_row_count - current_row_count)
                self.GetView().ProcessTableMessage(msg)
            msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
            self.GetView().ProcessTableMessage(msg)
            self.GetView().EndBatch()

        @staticmethod
        def round_down(value, places):
            return math.floor(value * (10 ** places)) / float(10 ** places)

    class RaceGridBarRender(wx.grid.GridCellRenderer):
        def __init__(self):
            wx.grid.GridCellRenderer.__init__(self)

        def Draw(self, grid, attr, dc, rect, row, col, selected):
            dc.SetBackgroundMode(wx.SOLID)
            if selected:
                background_color = grid.GetSelectionBackground()
            else:
                background_color = grid.GetCellBackgroundColour(row, col)
            dc.SetBrush(wx.Brush(background_color))
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)

            dc.SetBrush(wx.BLUE_BRUSH)
            dc.DrawRectangle(rect.x, rect.y, rect.width * float(grid.GetCellValue(row, col)), rect.height)

        def GetBestSize(self, grid, attr, dc, row, col):
            return wx.Size(grid.GetColSize(col), grid.GetRowMinimalAcceptableHeight())
