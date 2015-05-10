# coding=utf-8

__author__ = "Jarek Szczepanski <imrahil@imrahil.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2014 Jarek Szczepanski - Released under terms of the AGPLv3 License"

def eventHandler(self, event, payload):
    import octoprint.events
    import os

    supported_event = None

    # support for print done & cancelled events
    if event == octoprint.events.Events.PRINT_DONE:
        supported_event = octoprint.events.Events.PRINT_DONE

    elif event == octoprint.events.Events.PRINT_CANCELLED:
        supported_event = octoprint.events.Events.PRINT_CANCELLED

    # unsupported event
    if supported_event is None:
        return

    self._logger.info("event: %s" % supported_event)
    try:
        fileData = self._file_manager.get_metadata(payload["origin"], payload["file"])
        path, fileName = self._file_manager.sanitize(payload["origin"], payload["file"])
    except:
        fileData = None

    if fileData is not None:
        data = {}
        timestamp = 0

        self._logger.info("metadata for %s" % fileName)
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
                self._logger.info("filament volume: %s, length: %s" % (filamentVolume, filamentLength))

        # how long print took
        if "statistics" in fileData:
            printer_profile = self._printer_profile_manager.get_current_or_default()["id"]
            if "lastPrintTime" in fileData["statistics"] and printer_profile in fileData["statistics"]["lastPrintTime"]:
                printTime = fileData["statistics"]["lastPrintTime"][printer_profile]

                currentFile["printTime"] = printTime
                self._logger.info("printTime: %s" % printTime)

        # when print happened and what was result
        if "history" in fileData:
            history = fileData["history"]
            last = None

            for entry in history:
                if not last or ("timestamp" in entry and "timestamp" in last and entry["timestamp"] > last["timestamp"]):
                    last = entry
            if last:
                success = last["success"]
                timestamp = last["timestamp"]

                currentFile["success"] = success
                currentFile["timestamp"] = timestamp
                self._logger.info("success: %s, timestamp: %s" % (success, timestamp))

        rounded_timestamp = int(timestamp * 1000);
        data[rounded_timestamp] = currentFile
        path = os.path.join(self._settings.getBaseFolder("uploads"), "history.yaml")

        with open(path, "a") as f:
            try:
                import yaml
                yaml.safe_dump(data, f, default_flow_style=False, indent="  ", allow_unicode=True)
            except:
                self._logger.exception("Error while writing history.yaml")
