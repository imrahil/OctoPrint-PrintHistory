# coding=utf-8

__author__ = "Jarek Szczepanski <imrahil@imrahil.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2014 Jarek Szczepanski - Released under terms of the AGPLv3 License"

def exportHistoryData(self, exportType):
    import flask
    import csv
    import StringIO

    history_dict = self._getHistoryDict()

    if history_dict is not None:
        si = StringIO.StringIO()

        headers = ['File name', 'Timestamp', 'Success', 'Print time', 'Filament length', 'Filament volume']
        fields = ['fileName', 'timestamp', 'success', 'printTime', 'filamentLength', 'filamentVolume']
        if exportType == 'csv':
            writer = csv.writer(si, quoting=csv.QUOTE_ALL)
            writer.writerow(headers)

            for historyDetails in history_dict:
                output = list()
                for field in fields:
                    value = historyDetails.get(field, '-')
                    output.append(value if value is not None else '-')
                writer.writerow(output);

            response = flask.make_response(si.getvalue())
            response.headers["Content-type"] = "text/csv"
            response.headers["Content-Disposition"] = "attachment; filename=octoprint_print_history_export.csv"
        elif exportType == 'excel':
            import xlsxwriter

            workbook = xlsxwriter.Workbook(si)
            worksheet = workbook.add_worksheet()
            for column, header in enumerate(headers):
                worksheet.write(0, column, header)

            for row, historyDetails in enumerate(history_dict):
                for column, field in enumerate(fields):
                    value = historyDetails.get(field, '-')
                    worksheet.write(row + 1, column, (value if value is not None else '-'))

            workbook.close()

            response = flask.make_response(si.getvalue())
            response.headers["Content-type"] = "application/vnd.ms-excel"
            response.headers["Content-Disposition"] = "attachment; filename=octoprint_print_history_export.xlsx"

        return response
    else:
        return flask.make_response("No history file", 400)
