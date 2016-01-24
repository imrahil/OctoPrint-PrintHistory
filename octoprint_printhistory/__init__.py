# coding=utf-8
from __future__ import absolute_import
import os

__author__ = "Jarek Szczepanski <imrahil@imrahil.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2014 Jarek Szczepanski - Released under terms of the AGPLv3 License"

from flask import jsonify
import flask

import octoprint.plugin
import logging
     
class PrintHistoryPlugin(octoprint.plugin.StartupPlugin,
                         octoprint.plugin.EventHandlerPlugin,
                         octoprint.plugin.SettingsPlugin,
                         octoprint.plugin.BlueprintPlugin,
                         octoprint.plugin.TemplatePlugin,
                         octoprint.plugin.AssetPlugin):

    def __init__(self):
        self._history_file_path = None
        self._console_logger = None

    def initialize(self):
        self._console_logger = logging.getLogger("octoprint.plugins.printhistory.console")

    def on_startup(self, host, port):
        console_logging_handler = logging.handlers.RotatingFileHandler(self._settings.get_plugin_logfile_path(postfix="console"), maxBytes=2*1024*1024)
        console_logging_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        console_logging_handler.setLevel(logging.DEBUG)
  
        self._console_logger.addHandler(console_logging_handler)
        self._console_logger.setLevel(logging.DEBUG)
        self._console_logger.propagate = False
    
    def on_after_startup(self):
        self._console_logger.debug("Plugins folder: %s" % self._settings.getBaseFolder("plugins"))
        self._console_logger.debug("Uploads folder: %s" % self._settings.getBaseFolder("uploads"))

        old_path = os.path.join(self._settings.getBaseFolder("uploads"), "history.yaml")
        self._history_file_path = os.path.join(self.get_plugin_data_folder(), "history.yaml")
        if os.path.exists(old_path):
            os.rename(old_path, self._history_file_path)

     ##~~ TemplatePlugin API
    def get_template_configs(self):
        return [
            dict(type="tab", name="History")
        ]

    ##~~ AssetPlugin API
    def get_assets(self):
        return {
            "js": ["js/printhistory.js", "js/jquery.flot.pie.js", "js/jquery.flot.time.js", "js/jquery.flot.stack.js", "js/bootstrap-editable.min.js", "js/knockout.x-editable.js"],
            "css": ["css/printhistory.css", "css/bootstrap-editable.css"]
        }

    #~~ EventPlugin API
    def on_event(self, event, payload):
        from . import eventHandler
        return eventHandler.eventHandler(self, event, payload)


    @octoprint.plugin.BlueprintPlugin.route("/history", methods=["GET"])
    def getHistoryData(self):
        self._console_logger.debug("Rendering history.yaml")

        history_dict = self._getHistoryDict()

        if history_dict is not None:
            self._console_logger.debug("Returning data")
            return jsonify(history=history_dict)
        else:
            self._console_logger.debug("Empty file history.yaml")
            return jsonify({})

    @octoprint.plugin.BlueprintPlugin.route("/history/<int:identifier>", methods=["DELETE"])
    def deleteHistoryData(self, identifier):
        self._console_logger.debug("Delete file: %s" % identifier)

        from octoprint.server import NO_CONTENT

        history_dict = self._getHistoryDict()

        if identifier in history_dict:
            self._console_logger.debug("Found a identifier: %s" % identifier)
            del history_dict[identifier]

            if len(history_dict) == 0:
                open(self._history_file_path, "w")
            else:
                with open(self._history_file_path, "w") as f2:
                    import yaml
                    yaml.safe_dump(history_dict, f2, default_flow_style=False, indent="  ", allow_unicode=True)

        return NO_CONTENT

    @octoprint.plugin.BlueprintPlugin.route("/savenote", methods=["POST"])
    def saveNote(self):
        identifier = int(flask.request.values["pk"])
        self._console_logger.debug("Saving note: %s" % identifier)

        from octoprint.server import NO_CONTENT

        history_dict = self._getHistoryDict()

        if identifier in history_dict:
            self._console_logger.debug("Found a identifier: %s" % identifier)
            history_dict[identifier]["note"] = flask.request.values["value"]

            with open(self._history_file_path, "w") as f2:
                import yaml
                yaml.safe_dump(history_dict, f2, default_flow_style=False, indent="  ", allow_unicode=True)

        return NO_CONTENT

    @octoprint.plugin.BlueprintPlugin.route("/export/<string:exportType>", methods=["GET"])
    def exportHistoryData(self, exportType):
        from . import export
        return export.exportHistoryData(self, exportType)

    def _getHistoryDict(self):
        if os.path.exists(self._history_file_path):
            with open(self._history_file_path, "r") as f:
                try:
                    import yaml
                    history_dict = yaml.safe_load(f)
                except:
                    self._console_logger.exception("Error while reading .metadata.yaml from {path}".format(**locals()))
                else:
                    if not history_dict:
                        history_dict = dict()
                    return history_dict
        return dict()

    ##~~ Softwareupdate hook
    def get_update_information(self):
        return dict(
            printhistory=dict(
                displayName="Print History Plugin",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="imrahil",
                repo="OctoPrint-PrintHistory",
                current=self._plugin_version,

                # update method: pip w/ dependency links
                pip="https://github.com/imrahil/OctoPrint-PrintHistory/archive/{target_version}.zip"
            )
        )


__plugin_name__ = "Print History Plugin"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = PrintHistoryPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}
