# coding=utf-8
from __future__ import absolute_import

__author__ = "Jarek Szczepanski <imrahil@imrahil.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2014 Jarek Szczepanski - Released under terms of the AGPLv3 License"

import octoprint.plugin
import octoprint.events

class PrintHistoryPlugin(octoprint.plugin.StartupPlugin,
                         octoprint.plugin.EventHandlerPlugin,
                         octoprint.plugin.SettingsPlugin,
                         octoprint.plugin.TemplatePlugin,
                         octoprint.plugin.AssetPlugin):

    def on_after_startup(self):
        self._logger.info("Hello World from Print History Plugin!")
        self.get

    def get_template_configs(self):
        return [
            dict(type="tab", name="History")
        ]

    #~~ EventPlugin API

    def on_event(self, event, payload):

        supported_event = None

        if event == octoprint.events.Events.PRINT_STARTED:
            supported_event = octoprint.events.Events.PRINT_STARTED

        elif event == octoprint.events.Events.PRINT_DONE:
            supported_event = octoprint.events.Events.PRINT_DONE

        elif event == octoprint.events.Events.PRINT_CANCELLED:
            supported_event = octoprint.events.Events.PRINT_CANCELLED

        if supported_event is None:
            return

        self._logger.info("event: %s" % supported_event)
        metadata = self._file_manager.get_metadata(payload["origin"], payload["file"])
        self._logger.info("metadata: %s" % metadata)


__plugin_name__ = "Print History Plugin"
__plugin_implementations__ = [PrintHistoryPlugin()]
