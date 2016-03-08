import sys
import getopt
import wx
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
    try:
        try:
            (opts, args) = getopt.getopt(argv[1:], "h", ["help"])
        except getopt.error as msg:
            raise Usage(msg)

        application = ElectionApplication()
        ElectionUI(None, title="UCSB AS Election Tabulator")
        application.MainLoop()
    except Usage as err:
        print(err.msg, file=sys.stderr)
        print("--help, -h for help.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
