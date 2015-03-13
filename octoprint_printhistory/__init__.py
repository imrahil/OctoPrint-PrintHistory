# coding=utf-8
from __future__ import absolute_import

__author__ = "Jarek Szczepanski <imrahil@imrahil.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2014 Jarek Szczepanski - Released under terms of the AGPLv3 License"

import octoprint.plugin
import octoprint.events

class PrintHistoryPlugin(octoprint.plugin.EventHandlerPlugin,
                         octoprint.plugin.SettingsPlugin,
                         octoprint.plugin.TemplatePlugin,
                         octoprint.plugin.AssetPlugin):
            
        
__plugin_name__ = "Print History Plugin"
__plugin_implementations__ = [PrintHistoryPlugin()]
