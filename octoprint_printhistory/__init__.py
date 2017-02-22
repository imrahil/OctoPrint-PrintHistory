# coding=utf-8
from __future__ import absolute_import
import os

__author__ = "Jarek Szczepanski <imrahil@imrahil.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2016 Jarek Szczepanski - Released under terms of the AGPLv3 License"

from flask import jsonify, request, make_response
from octoprint.server.util.flask import with_revalidation_checking, check_etag

import octoprint.plugin
import sqlite3


class PrintHistoryPlugin(octoprint.plugin.StartupPlugin,
                         octoprint.plugin.EventHandlerPlugin,
                         octoprint.plugin.SettingsPlugin,
                         octoprint.plugin.BlueprintPlugin,
                         octoprint.plugin.TemplatePlugin,
                         octoprint.plugin.AssetPlugin):

    def __init__(self):
        self._history_db_path = None
        self._history_dict = None
        self._comm = None

    def on_after_startup(self):
        old_path = os.path.join(self.get_plugin_data_folder(), "history.yaml")
        self._history_db_path = os.path.join(self.get_plugin_data_folder(), "history.db")

        conn = sqlite3.connect(self._history_db_path)
        cur  = conn.cursor()
        create_sql = """\
        CREATE TABLE IF NOT EXISTS print_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fileName TEXT NOT NULL DEFAULT "",
            note TEXT,
            spool TEXT NOT NULL DEFAULT "",
            filamentVolume REAL,
            filamentLength REAL,
            printTime REAL,
            success INTEGER,
            timestamp REAL,
            user TEXT NOT NULL DEFAULT "",
            parameters TEXT NOT NULL DEFAULT ""
        );

        CREATE TABLE IF NOT EXISTS modifications (
            id INTEGER NOT NULL PRIMARY KEY ON CONFLICT REPLACE,
            action TEXT NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TRIGGER IF NOT EXISTS history_ondelete AFTER DELETE ON print_history
        BEGIN
            INSERT INTO modifications (id, action) VALUES (old.id, 'DELETE');
        END;

        CREATE TRIGGER IF NOT EXISTS history_onupdate AFTER UPDATE ON print_history
        BEGIN
            INSERT INTO modifications (id, action) VALUES (old.id, 'UPDATE');
        END;

        CREATE TRIGGER IF NOT EXISTS history_oninsert AFTER INSERT ON print_history
        BEGIN
            INSERT INTO modifications (id, action) VALUES (new.id, 'INSERT');
        END;
        """
        cur.executescript(create_sql)

        # migration for existing tables
        try:
            cur.execute('ALTER TABLE print_history ADD COLUMN spool TEXT NOT NULL DEFAULT "";')
        except:
            pass
        conn.commit()

        try:
            cur.execute('ALTER TABLE print_history ADD COLUMN user TEXT NOT NULL DEFAULT "";')
        except:
            pass
        conn.commit()

        try:
            cur.execute('ALTER TABLE print_history ADD COLUMN parameters TEXT NOT NULL DEFAULT "";')
        except:
            pass
        conn.commit()

        if os.path.exists(old_path):
            with open(old_path, "r") as f:
                try:
                    from yaml import safe_load
                    history_dict = safe_load(f)
                except:
                    raise

            if history_dict is None:
                history_dict = dict()

            history = []
            for historyHash in history_dict.keys():
                historyDetails = history_dict[historyHash]
                row = list()
                row.append(historyDetails["fileName"] if "fileName" in historyDetails else None)
                row.append(historyDetails["note"] if "note" in historyDetails else None)
                row.append(historyDetails["filamentVolume"] if "filamentVolume" in historyDetails else None)
                row.append(historyDetails["filamentLength"] if "filamentLength" in historyDetails else None)
                row.append(historyDetails["printTime"] if "printTime" in historyDetails else None)
                success = historyDetails["success"] if "success" in historyDetails else None
                row.append(1 if success is True else 0)
                row.append(historyDetails["timestamp"] if "timestamp" in historyDetails else None)
                history.append(row)

            cur.executemany('''INSERT INTO print_history (fileName, note, filamentVolume, filamentLength, printTime, success, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)''', history)
            conn.commit()

            os.rename(old_path, os.path.join(self.get_plugin_data_folder(), "history.bak"))

        conn.close()

    ##~~ SettingsPlugin API
    def get_settings_defaults(self):
        return dict(
            spool_inventory=[]
        )

    ##~~ TemplatePlugin API
    def get_template_configs(self):
        return [
            dict(type="tab", name="History"),
            dict(type="settings", template="printhistory_settings.jinja2")
        ]

    ##~~ AssetPlugin API
    def get_assets(self):
        return {
            "js": ["js/printhistory.js", "js/jquery.flot.pie.js", "js/jquery.flot.time.js", "js/jquery.flot.stack.js"],
            "css": ["css/printhistory.css"]
        }

    #~~ EventPlugin API
    def on_event(self, event, payload):
        from . import eventHandler
        return eventHandler.eventHandler(self, event, payload)

    @octoprint.plugin.BlueprintPlugin.route("/history", methods=["GET"])
    def getHistoryData(self):
        from octoprint.settings import valid_boolean_trues

        force = request.values.get("force", "false") in valid_boolean_trues

        if force:
            self._history_dict = None

        def view():
            history_dict = self._getHistoryDict()

            if history_dict is not None:
                result = jsonify(history=history_dict)
            else:
                result = jsonify({})

            return result

        def etag():
            conn = sqlite3.connect(self._history_db_path)
            cur  = conn.cursor()
            cur.execute("SELECT changed_at FROM modifications ORDER BY changed_at DESC LIMIT 1")
            lm = cur.fetchone()
            conn.close()

            import hashlib
            hash = hashlib.sha1()
            hash.update(str(lm))
            hexdigest = hash.hexdigest()
            return hexdigest

        def condition():
            check = check_etag(etag())
            return check

        return with_revalidation_checking(etag_factory=lambda *args, **kwargs: etag(),
                                          condition=lambda *args, **kwargs: condition(),
                                          unless=lambda: force)(view)()


    @octoprint.plugin.BlueprintPlugin.route("/history/<int:identifier>", methods=["DELETE"])
    def deleteHistoryData(self, identifier):
        self._history_dict = None

        conn = sqlite3.connect(self._history_db_path)
        cur  = conn.cursor()
        cur.execute("DELETE FROM print_history WHERE id = ?", (identifier,))
        conn.commit()
        conn.close()

        return self.getHistoryData()

    @octoprint.plugin.BlueprintPlugin.route("/details", methods=["PUT"])
    def saveNote(self):
        from werkzeug.exceptions import BadRequest

        try:
       		json_data = request.json
       	except BadRequest:
       		return make_response("Malformed JSON body in request", 400)

        if not "id" in json_data:
       		return make_response("No profile included in request", 400)

        identifier = json_data["id"]
        note = json_data["note"] if "note" in json_data else ""
        spool = json_data["spool"] if "spool" in json_data else ""
        user = json_data["user"] if "user" in json_data else ""
        success = json_data["success"]
        filamentLength = json_data["filamentLength"] if "filamentLength" in json_data else 0
        filamentVolume = json_data["filamentVolume"] if "filamentVolume" in json_data else 0

        self._history_dict = None

        conn = sqlite3.connect(self._history_db_path)
        cur  = conn.cursor()
        cur.execute("UPDATE print_history SET note = ?, spool = ?, user = ?, success = ?, filamentLength = ?, filamentVolume = ? WHERE id = ?", (note, spool, user, success, filamentLength, filamentVolume, identifier))
        conn.commit()
        conn.close()

        return self.getHistoryData()

    @octoprint.plugin.BlueprintPlugin.route("/export/<string:exportType>", methods=["GET"])
    def exportHistoryData(self, exportType):
        from . import export
        return export.exportHistoryData(self, exportType)

    #
    # private methods
    #

    def _getHistoryDict(self):
        if self._history_dict is not None:
            return self._history_dict

        conn = sqlite3.connect(self._history_db_path)
        cur  = conn.cursor()
        cur.execute("SELECT * FROM print_history ORDER BY timestamp")
        history_dict = [dict((cur.description[i][0], value) \
                  for i, value in enumerate(row)) for row in cur.fetchall()]

        conn.close()

        if history_dict is None:
            history_dict = dict()

        self._history_dict = history_dict

        return self._history_dict

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

    def factory_serial_handler(self, comm_instance, port, baudrate, read_timeout):
        self._comm = comm_instance
        return None

__plugin_name__ = "Print History Plugin"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = PrintHistoryPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.transport.serial.factory": __plugin_implementation__.factory_serial_handler
	}
