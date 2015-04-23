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
        self._logger.info("Plugins folder: %s" % self._settings.getBaseFolder("plugins"))
        self._logger.info("Uploads folder: %s" % self._settings.getBaseFolder("uploads"))

     ##~~ TemplatePlugin API
    def get_template_configs(self):
        return [
            dict(type="tab", name="History")
        ]

    ##~~ AssetPlugin API
    def get_assets(self):
        return {
            "js": ["js/printhistory.js", "js/jquery.flot.pie.js", "js/jquery.flot.time.js", "js/jquery.flot.stack.js"],
            "css": ["css/printhistory.css"]
        }

    #~~ EventPlugin API
    def on_event(self, event, payload):

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
                "fileName": fileName
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


    @octoprint.plugin.BlueprintPlugin.route("/history", methods=["GET"])
    def getHistoryData(self):
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
                self._logger.debug("Returning data")
                return jsonify(history=history_dict)
            else:
                self._logger.debug("Empty file history.yaml")
                return jsonify({})
        else:
            self._logger.debug("File doesn't exist")
            return jsonify({})

    @octoprint.plugin.BlueprintPlugin.route("/history/<int:identifier>", methods=["DELETE"])
    def deleteHistoryData(self, identifier):
        self._logger.debug("Delete file: %s" % identifier)

        import yaml
        from octoprint.server import NO_CONTENT

        path = os.path.join(self._settings.getBaseFolder("uploads"), "history.yaml")

        if os.path.exists(path):
            with open(path, "r") as f:
                try:
                    history_dict = yaml.safe_load(f)

                    if identifier in history_dict:
                        self._logger.debug("Found a identifier: %s" % identifier)
                        del history_dict[identifier]

                        if len(history_dict) == 0:
                            open(path, "w")
                        else:
                            with open(path, "w") as f2:
                                yaml.safe_dump(history_dict, f2, default_flow_style=False, indent="  ", allow_unicode=True)
                except:
                    raise IOError("Couldn't read history data from {path}".format(path=path))

        return NO_CONTENT

    @octoprint.plugin.BlueprintPlugin.route("/export/<string:exportType>", methods=["GET"])
    def exportHistoryData(self, exportType):
        import yaml
        import csv
        import StringIO

        self._logger.debug("Exporting history.yaml to %s" % exportType)
        path = os.path.join(self._settings.getBaseFolder("uploads"), "history.yaml")

        history_dict = {}
        if os.path.exists(path):
            with open(path, "r") as f:
                try:
                    history_dict = yaml.safe_load(f)
                except:
                    raise IOError("Couldn't read history data from {path}".format(path=path))

            if history_dict is not None:
                si = StringIO.StringIO()

                headers = ['File name', 'Timestamp', 'Success', 'Print time', 'Filament length', 'Filament volume']
                if exportType == 'csv':
                    writer = csv.writer(si, quoting=csv.QUOTE_ALL)
                    writer.writerow(headers)

                    for historyHash in history_dict.keys():
                        historyDetails = history_dict[historyHash]
                        writer.writerow([ historyDetails["fileName"], historyDetails["timestamp"], historyDetails["success"], historyDetails["printTime"], historyDetails["filamentLength"], historyDetails["filamentVolume"], ]);

                    response = flask.make_response(si.getvalue())
                    response.headers["Content-type"] = "text/csv"
                    response.headers["Content-Disposition"] = "attachment; filename=octoprint_print_history_export.csv"
                elif exportType == 'excel':
                    import xlsxwriter

                    workbook = xlsxwriter.Workbook(si)
                    worksheet = workbook.add_worksheet()
                    col = 0
                    for header in headers:
                        worksheet.write(0, col, header)
                        col += 1

                    row = 1
                    for historyHash in history_dict.keys():
                        historyDetails = history_dict[historyHash]
                        worksheet.write(row, 0, historyDetails["fileName"])
                        worksheet.write(row, 1, historyDetails["timestamp"])
                        worksheet.write(row, 2, historyDetails["success"])
                        worksheet.write(row, 3, historyDetails["printTime"])
                        worksheet.write(row, 4, historyDetails["filamentLength"])
                        worksheet.write(row, 5, historyDetails["filamentVolume"])

                        row += 1

                    workbook.close()

                    response = flask.make_response(si.getvalue())
                    response.headers["Content-type"] = "application/vnd.ms-excel"
                    response.headers["Content-Disposition"] = "attachment; filename=octoprint_print_history_export.xls"

                return response
            else:
                return flask.make_response("No history file", 400)
        else:
            return flask.make_response("No history file", 400)


__plugin_name__ = "Print History Plugin"
__plugin_implementation__ = PrintHistoryPlugin()
