# coding=utf-8

__author__ = "Jarek Szczepanski <imrahil@imrahil.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2014 Jarek Szczepanski - Released under terms of the AGPLv3 License"

def eventHandler(self, event, payload):
    import octoprint.events

    from operator import itemgetter

    supported_event = None

    # support for print done & cancelled events
    if event == octoprint.events.Events.PRINT_DONE:
        supported_event = event

    elif event == octoprint.events.Events.PRINT_CANCELLED:
        supported_event = event

    # unsupported event
    if supported_event is None:
        return

    self._console_logger.info("Handled event: %s" % supported_event)
    try:
        fileData = self._file_manager.get_metadata(payload["origin"], payload["file"])
        fileName = payload["filename"]
    except:
        fileData = None

    if fileData is not None:
        timestamp = 0

        self._console_logger.info("Metadata for: %s" % fileName)
        currentFile = {
            "fileName": fileName,
            "note": ""
        }

        # analysis - looking for info about filament usage
        if "analysis" in fileData:
            if "filament" in fileData["analysis"] and "tool0" in fileData["analysis"]["filament"]:
                filamentVolume = fileData["analysis"]["filament"]["tool0"]["volume"]    # TODO - "tool0" means there is no dual extruder support
                filamentLength = fileData["analysis"]["filament"]["tool0"]['length']

                currentFile["filamentVolume"] = filamentVolume
                currentFile["filamentLength"] = filamentLength
                self._console_logger.info("Filament volume: %s, Length: %s" % (filamentVolume, filamentLength))

        # how long print took
        if "statistics" in fileData:
            printer_profile = self._printer_profile_manager.get_current_or_default()["id"]
            if "lastPrintTime" in fileData["statistics"] and printer_profile in fileData["statistics"]["lastPrintTime"]:
                printTime = fileData["statistics"]["lastPrintTime"][printer_profile]

                currentFile["printTime"] = printTime
                self._console_logger.info("PrintTime: %s" % printTime)

        # when print happened and what was result
        if "history" in fileData:
            history = fileData["history"]

            newlist = sorted(history, key=itemgetter('timestamp'), reverse=True)

            if newlist:
                last = newlist[0]

                success = last["success"]
                timestamp = last["timestamp"]

                currentFile["success"] = success
                currentFile["timestamp"] = timestamp
                self._console_logger.info("Success: %s, Timestamp: %s" % (success, timestamp))

        rounded_timestamp = int(timestamp * 1000);

        history_dict = self._getHistoryDict()
        history_dict[rounded_timestamp] = currentFile

        try:
            import yaml
            from octoprint.util import atomic_write
            with atomic_write(self._history_file_path) as f:
                yaml.safe_dump(history_dict, stream=f, default_flow_style=False, indent="  ", allow_unicode=True)
        except:
            self._console_logger.exception("Error while writing history.yaml to {path}".format(**locals()))
