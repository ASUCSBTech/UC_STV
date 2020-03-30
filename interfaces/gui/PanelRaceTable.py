import wx
import wx.grid

from backend.ElectionRace import ElectionRace

class PanelRaceTable(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Set font size.
        if wx.SystemOptions.HasOption("font-size"):
            font = self.GetFont()
            font.SetPointSize(wx.SystemOptions.GetOptionInt("font-size"))
            self.SetFont(font)

        self.grid = wx.grid.Grid(self, wx.ID_ANY)
        self.grid.SetTable(PanelRaceTable.RaceGridData(), True)
        self.grid.AutoSize()
        self.grid.EnableEditing(False)
        self.grid.DisableCellEditControl()
        self.grid.DisableDragColMove()
        self.grid.DisableDragGridSize()
        self.grid.DisableDragRowSize()

        cell_attribute = wx.grid.GridCellAttr()
        renderer = PanelRaceTable.RaceGridBarRender()
        cell_attribute.SetRenderer(renderer)
        self.grid.SetColAttr(self.grid.GetTable().ColumnsFindString("Quota Percentage"), cell_attribute)

        cell_attribute = wx.grid.GridCellAttr()
        cell_attribute.SetAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        self.grid.SetColAttr(self.grid.GetTable().ColumnsFindString("Status"), cell_attribute)

        # Use the default label font, but in a normal font weight.
        grid_label_font = self.grid.GetLabelFont()
        grid_label_font.SetWeight(wx.FONTWEIGHT_NORMAL)
        self.grid.SetLabelFont(grid_label_font)

        # Set the column label size to be the height of the text at
        # column zero (first column) plus five.
        self.grid.SetColLabelSize(wx.MemoryDC().GetFullMultiLineTextExtent(self.grid.GetColLabelValue(0), font=self.grid.GetLabelFont())[1] + 5)

        self.grid.SetRowLabelSize(0)

        self.grid.GetGridWindow().Bind(wx.EVT_SIZE, self.on_size)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.grid, 1, wx.ALL | wx.EXPAND, 0)

        self.SetSizer(self.sizer)
        self.sizer.Layout()

    def on_size(self, event):
        columns = self.grid.GetNumberCols()
        width = 0
        for i in range(columns - 1):
            width += self.grid.GetColSize(i)

        frame_width = self.grid.GetGridWindow().GetClientRect().GetWidth()
        remaining_width = frame_width - width

        self.grid.SetColSize(columns - 1, -1)
        if self.grid.GetColSize(columns - 1) < remaining_width:
            self.grid.SetColSize(columns - 1, remaining_width)

        if event and self.GetAutoLayout():
            self.Layout()

    def update(self, table_data, update_layout=True):
        grid_table = self.grid.GetTable()
        grid_table.set_table_data(table_data)
        if update_layout:
            self.grid.AutoSizeColumns(setAsMin=False)
            dc = wx.MemoryDC()
            dc.SetFont(self.GetFont())
            point_size = self.GetFont().GetPointSize()
            temp_point_size = 1.5 * point_size
            self.grid.SetColSize(grid_table.ColumnsFindString("Status"), dc.GetTextExtent("TRANSFERRING")[0] + temp_point_size)
            self.grid.SetColSize(grid_table.ColumnsFindString("Score"), dc.GetTextExtent("0000 (0000.0000)")[0] + 5)
            self.on_size(None)
        self.grid.ForceRefresh()

    def setGridFont(self, font_size):
        font = self.GetFont()
        font.SetPointSize(font_size)
        columns = self.grid.GetNumberCols()
        rows = self.grid.GetNumberRows()

        for i in range(rows):
            for j in range(columns-1):
                if(font.GetPointSize() < 15):
                    self.grid.SetCellFont(i,j,font)
                else:
                    if(j == 2):
                        font.SetPointSize(15)
                        self.grid.SetCellFont(i,j,font)
                    else:
                        font.SetPointSize(font_size)
                        self.grid.SetCellFont(i,j,font)
        self.grid.AutoSize()
        self.grid.ForceRefresh()

    def highlightWinners(self, max_winners):
        grid_table = self.grid.GetTable()
        colour = wx.Colour(255,255,0)
        columns = self.grid.GetNumberCols()
        rows = self.grid.GetNumberRows()
        for i in range(max_winners):
            for j in range(rows):
                self.grid.SetCellBackgroundColour(i,j,colour)


    def colorReset(self):
        grid_table = self.grid.GetTable()
        colour = wx.Colour(255,255,255)
        columns = self.grid.GetNumberCols()
        rows = self.grid.GetNumberRows()

        for i in range (rows):
            for j in range(columns):
                self.grid.SetCellBackgroundColour(i,j,colour)


    class RaceGridData(wx.grid.GridTableBase):
        def __init__(self):
            wx.grid.GridTableBase.__init__(self)
            self._table_columns = ["Candidate", "Party", "Status", "Score", "Quota Percentage"]
            self._table_rows = []

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

        def ColumnsFindString(self, value):
            return self._table_columns.index(value)

        def SetValue(self, row, col, value):
            # Values should not be editable.
            return

        def set_table_data(self, table_data):
            current_row_count = len(self._table_rows)
            self._table_rows = table_data

            self.GetView().BeginBatch()
            new_row_count = len(self._table_rows)
            if new_row_count < current_row_count:
                msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, new_row_count - 1, current_row_count - new_row_count)
                self.GetView().ProcessTableMessage(msg)
            elif new_row_count > current_row_count:
                msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED, new_row_count - current_row_count)
                self.GetView().ProcessTableMessage(msg)
            msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
            self.GetView().ProcessTableMessage(msg)
            self.GetView().EndBatch()

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

            bar_color = wx.MEDIUM_GREY_BRUSH
            grid_table = grid.GetTable()
            if grid_table:
                row_status = grid.GetCellValue(row, grid_table.ColumnsFindString("Status"))
                if row_status == "WON":
                    bar_color = wx.YELLOW_BRUSH
            dc.SetBrush(bar_color)
            dc.DrawRectangle(rect.x, rect.y, rect.width * float(grid.GetCellValue(row, col)), rect.height)

        def GetBestSize(self, grid, attr, dc, row, col):
            return wx.Size(grid.GetColSize(col), grid.GetRowMinimalAcceptableHeight())
