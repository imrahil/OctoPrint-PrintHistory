# coding=utf-8
from __future__ import absolute_import
import os

__author__ = "Jarek Szczepanski <imrahil@imrahil.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2014 Jarek Szczepanski - Released under terms of the AGPLv3 License"

from flask import jsonify
import flask

import octoprint.plugin
import octoprint.events

class PrintHistoryPlugin(octoprint.plugin.StartupPlugin,
                         octoprint.plugin.EventHandlerPlugin,
                         octoprint.plugin.SettingsPlugin,
                         octoprint.plugin.BlueprintPlugin,
                         octoprint.plugin.TemplatePlugin,
                         octoprint.plugin.AssetPlugin):

    def on_after_startup(self):
        self._logger.info("Hello World from Print History Plugin!")
        self._logger.info("Plugins folder: %s" % self._settings.getBaseFolder("plugins"))

    def get_template_configs(self):
        return [
            dict(type="tab", name="History")
        ]

    #~~ EventPlugin API

    def on_event(self, event, payload):

        supported_event = None

        # if event == octoprint.events.Events.PRINT_STARTED:
        #     supported_event = octoprint.events.Events.PRINT_STARTED

        if event == octoprint.events.Events.PRINT_DONE:
            supported_event = octoprint.events.Events.PRINT_DONE

        elif event == octoprint.events.Events.PRINT_CANCELLED:
            supported_event = octoprint.events.Events.PRINT_CANCELLED

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
                "fileName": fileName
            }

            # analysis - we can find info about filament usage
            if "analysis" in fileData:
                if "filament" in fileData["analysis"] and "tool0" in fileData["analysis"]["filament"]:
                    filamentVolume = fileData["analysis"]["filament"]["tool0"]["volume"]
                    filamentLength = fileData["analysis"]["filament"]["tool0"]['length']

                    currentFile["filamentVolume"] = filamentVolume
                    currentFile["filamentLength"] = filamentLength
                    self._logger.info("filament volume: %s, length: %s" % (filamentVolume, filamentLength))

            # how long print took
            if "statistics" in fileData:
                printer_profile = self._printer_profile_manager.get_current_or_default()["id"]
                if "lastPrintTime" in fileData["statistics"] and printer_profile in fileData["statistics"]["lastPrintTime"]:
                    lastPrintTime = fileData["statistics"]["lastPrintTime"][printer_profile]

                    currentFile["lastPrintTime"] = lastPrintTime
                    self._logger.info("lastPrintTime: %s" % lastPrintTime)

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


    @octoprint.plugin.BlueprintPlugin.route("/history", methods=["GET"])
    def discovery(self):
        import yaml

        self._logger.debug("Rendering history.yaml")
        path = os.path.join(self._settings.getBaseFolder("uploads"), "history.yaml")

        history_dict = {}
        if os.path.exists(path):
            with open(path, "r") as f:
                try:
                    history_dict = yaml.safe_load(f)
                except:
                    raise IOError("Couldn't read history data from {path}".format(path=path))

            if history_dict is not None:
                return jsonify(history=history_dict)
        else:
            return flask.make_response("No history file", 400)




__plugin_name__ = "Print History Plugin"
__plugin_implementation__ = PrintHistoryPlugin()
