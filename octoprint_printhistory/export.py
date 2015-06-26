# coding=utf-8

__author__ = "Jarek Szczepanski <imrahil@imrahil.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2014 Jarek Szczepanski - Released under terms of the AGPLv3 License"

def exportHistoryData(self, exportType):
    import os
    import flask
    import yaml
    import csv
    import StringIO

    self._logger.debug("Exporting history.yaml to %s" % exportType)

    history_dict = {}
    if os.path.exists(self._history_file_path):
        with open(self._history_file_path, "r") as f:
            try:
                history_dict = yaml.safe_load(f)
            except:
                raise IOError("Couldn't read history data from {path}".format(path=self._history_file_path))

        if history_dict is not None:
            si = StringIO.StringIO()

            headers = ['File name', 'Timestamp', 'Success', 'Print time', 'Filament length', 'Filament volume']
            if exportType == 'csv':
                writer = csv.writer(si, quoting=csv.QUOTE_ALL)
                writer.writerow(headers)

                for historyHash in history_dict.keys():
                    historyDetails = history_dict[historyHash]
                    output = list()
                    output.append(historyDetails["fileName"] if "fileName" in historyDetails and historyDetails["fileName"] is not None else "-")
                    output.append(historyDetails["timestamp"] if "timestamp" in historyDetails and historyDetails["timestamp"] is not None else "-")
                    output.append(historyDetails["success"] if "success" in historyDetails and historyDetails["success"] is not None else "-")
                    output.append(historyDetails["printTime"] if "printTime" in historyDetails and historyDetails["printTime"] is not None else "-")
                    output.append(historyDetails["filamentLength"] if "filamentLength" in historyDetails and historyDetails["filamentLength"] is not None else "-")
                    output.append(historyDetails["filamentVolume"] if "filamentVolume" in historyDetails and historyDetails["filamentVolume"] is not None else "-")

                    writer.writerow(output);

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
                    worksheet.write(row, 0, (historyDetails["fileName"] if "fileName" in historyDetails and historyDetails["fileName"] is not None else "-"))
                    worksheet.write(row, 1, (historyDetails["timestamp"] if "timestamp" in historyDetails and historyDetails["timestamp"] is not None else "-"))
                    worksheet.write(row, 2, (historyDetails["success"] if "success" in historyDetails and historyDetails["success"] is not None else "-"))
                    worksheet.write(row, 3, (historyDetails["printTime"] if "printTime" in historyDetails and historyDetails["printTime"] is not None else "-"))
                    worksheet.write(row, 4, (historyDetails["filamentLength"] if "filamentLength" in historyDetails and historyDetails["filamentLength"] is not None else "-"))
                    worksheet.write(row, 5, (historyDetails["filamentVolume"] if "filamentVolume" in historyDetails and historyDetails["filamentVolume"] is not None else "-"))

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


