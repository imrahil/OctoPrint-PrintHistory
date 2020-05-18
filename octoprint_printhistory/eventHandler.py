# coding=utf-8

"""
    Deprecated since version 1.3.0:

    file: the file’s full path on disk (local) or within its storage (sdcard). To be removed in 1.4.0.

    filename: the file’s name. To be removed in 1.4.0.
"""

__author__ = "Jarek Szczepanski <imrahil@imrahil.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2014 Jarek Szczepanski - Released under terms of the AGPLv3 License"

debug_mode = False

def eventHandler(self, event, payload):
    from octoprint.events import Events
<<<<<<< Updated upstream
    import time
    from operator import itemgetter

=======
    from operator         import itemgetter
    from .parser          import UniversalParser
    import octoprint.filemanager.storage as storage
    import octoprint.filemanager.destinations as destinations
    import octoprint.plugin as plugin
    import time
>>>>>>> Stashed changes
    import sqlite3
    import json

    supported_event = None

    # support for print done & cancelled events
    if event == Events.PRINT_DONE:
        supported_event = event
    elif event == Events.PRINT_FAILED:
        supported_event = event
    elif event == Events.METADATA_STATISTICS_UPDATED:
        supported_event = event
    # /if event == Events.type

    # unsupported event
    if supported_event is None:
        return
    # /if supported_event is None

    fileData = None

    if supported_event is not Events.METADATA_STATISTICS_UPDATED:

        try:
            fileData = self._file_manager.get_metadata(payload["origin"], payload["path"])
        except:
            fileData = None
        # /try

        fileName = payload["name"]

        if fileData is not None:
            success = None
            estimatedPrintTime = timestamp = 0

            filemanager = self._file_manager
            path        = ("/" if payload["path"]!="" else "") + payload["name"]
            path        = filemanager.path_on_disk(payload["origin"], path)

<<<<<<< Updated upstream
=======
            # loggerF(filemanager.path_on_disk(payload["origin"], path))

            gcode_parser = UniversalParser(path, logger=self._logger)
            parameters = gcode_parser.parse()
>>>>>>> Stashed changes
            currentFile = {
                "fileName": fileName,
                "note": ""
            }

            # analysis - looking for info about filament usage
            if "analysis" in fileData:
                if "filament" in fileData["analysis"]:
                    if "tool0" in fileData["analysis"]["filament"]:
                        filamentVolume = fileData["analysis"]["filament"]["tool0"]["volume"]
                        filamentLength = fileData["analysis"]["filament"]["tool0"]['length']


                        currentFile["filamentVolume"] = filamentVolume if filamentVolume is not None else 0
                        currentFile["filamentLength"] = filamentLength if filamentLength is not None else 0

                    # /if "tool0" in fileData["analysis"]["filament"]

                    if "tool1" in fileData["analysis"]["filament"]:
                        filamentVolume = fileData["analysis"]["filament"]["tool1"]["volume"]
                        filamentLength = fileData["analysis"]["filament"]["tool1"]['length']

                        currentFile["filamentVolume2"] = filamentVolume if filamentVolume is not None else 0
                        currentFile["filamentLength2"] = filamentLength if filamentLength is not None else 0
                    # /if "tool1" in fileData["analysis"]["filament"]

                    estimatedPrintTime = fileData["analysis"]["estimatedPrintTime"] if "estimatedPrintTime" in fileData["analysis"] else 0

                    # Temporarily disabled
                    # if "tool0" in fileData["analysis"]["filament"] and "tool1" in fileData["analysis"]["filament"]:
                    #     currentFile["note"] = "Dual extrusion"
                # /if "filament" in fileData["analysis"]
            else:
                currentFile["filamentVolume"] = 0
                currentFile["filamentLength"] = 0
            # /if "analysis" in fileData

            # how long print took
            if "time" in payload:
                currentFile["printTime"] = payload["time"]
            else:
<<<<<<< Updated upstream
                printTime = self._comm.getPrintTime()
                currentFile["printTime"] = printTime if printTime is not None else ""

=======
                printTime = self._comm.getPrintTime() if self._comm is not None else ""
                currentFile["printTime"] = printTime
            # /if "time" in payload
>>>>>>> Stashed changes

            # when print happened and what was the result
            if "history" in fileData:
                history = fileData["history"]

                newlist = sorted(history, key=itemgetter('timestamp'), reverse=True)

                if newlist:
                    last = newlist[0]

                    success = last["success"]
                # /if newlist
            # /if "history" in fileData

            if not success:
                success = False if event == Events.PRINT_FAILED else True
            # /if not success

            timestamp = int(time.time())

            currentFile["success"] = success
            currentFile["timestamp"] = timestamp

            self._history_dict = None

            conn = sqlite3.connect(self._history_db_path)
            cur  = conn.cursor()
            cur.execute("INSERT INTO print_history (fileName, note, filamentVolume, filamentLength, printTime, success, timestamp) VALUES (:fileName, :note, :filamentVolume, :filamentLength, :printTime, :success, :timestamp)", currentFile)
            conn.commit()
            conn.close()
        # /if fileData is not None
    else:
        # sometimes Events.PRINT_DONE is fired BEFORE metadata.yaml is updated - we have to wait for Events.METADATA_STATISTICS_UPDATED and update database

        try:
            fileData = self._file_manager.get_metadata(payload["storage"], payload["path"])
        except:
            fileData = None
        # /try

        if fileData!=None and "history" in fileData:
            history = fileData["history"]

            newlist = sorted(history, key=itemgetter('timestamp'), reverse=True)

            if newlist:
                last = newlist[0]

                success = last["success"]
                timestamp = int(last["timestamp"])

                conn = sqlite3.connect(self._history_db_path)
                cur = conn.cursor()
                cur.execute('''
                            UPDATE print_history
                                SET success = ?
                                WHERE timestamp = ?
                            ''',
                            (success, timestamp))
                # cur.execute("INSERT INTO print_history (success, timestamp) values (?, ?)", (success, timestamp))
                conn.commit()
                conn.close()
            # /if newlist
        # /if "history" in fileData
    # /if supported_event is not Events.METADATA_STATISTICS_UPDATED
# /def eventHandler(self, event, payload)

