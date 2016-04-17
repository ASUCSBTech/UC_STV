import wx.adv


class DialogAbout:
    def __init__(self, parent):
        about_info = wx.adv.AboutDialogInfo()
        about_info.SetName("UCSB AS Election Tabulator")
        about_info.SetVersion("1.0")
        about_info.SetDescription("Displays and tabulates voter ballots utilizing a single transferable vote system\nwith support for custom election configurations and dynamic ballot format parsing.")
        about_info.SetCopyright("Copyright (C) 2016 The Regents of the University of California.")
        about_info.SetWebSite("https://www.as.ucsb.edu/")
        about_info.AddDeveloper("Ryan Tse <tse@umail.ucsb.edu>")

        wx.adv.AboutBox(about_info, parent)