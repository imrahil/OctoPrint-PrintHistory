from enum import Enum, auto
import inspect

class OctoDebugger:
    SEPARATOR = ": "

    class DisplayType(Enum):
        # Debug = auto()
        Info  = auto()

    def __init__(self, _self_, isEnabled):
        self._self_=_self_
        self.isEnabled=isEnabled

    def log(self, dispType, *args):
        # if the object has been disabled, just return.
        # This is to allow for easy disabling of the
        if not self.isEnabled: return

        # https://docs.python.org/3/library/inspect.html
        # Get information for debugging purposes
        stack = inspect.stack()[2]
        func  = stack.function
        lnum  = stack.lineno
        fname = stack.filename.split("\\")
        fname = fname[len(fname)-1]

        msg= str(fname) + self.SEPARATOR + str(func) + self.SEPARATOR + str(lnum) + self.SEPARATOR

        for item in args:
            msg+=str(item)

        # if DisplayType==DisplayType.Debug:
        #     self._self_._logger.debug(msg)
        if dispType==self.DisplayType.Info:
            self._self_._logger.info(msg)

    def info(self, *args):
        self.log(self.DisplayType.Info, args)

    def debug(self, *args):
        self.log(self.DisplayType.Info, args)
