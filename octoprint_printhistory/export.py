# coding=utf-8

__author__ = "Jarek Szczepanski <imrahil@imrahil.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2014 Jarek Szczepanski - Released under terms of the AGPLv3 License"

def exportHistoryData(self, exportType):
    import flask
    import csv
    import StringIO
    import re
    from utils import namedtuple_with_defaults, prepare_dict, load_json, rename_duplicates

    history_dicts = self._getHistoryDicts()

    if history_dicts is not None:
        si = StringIO.StringIO()

        headers = ['File name', 'Timestamp', 'Success', 'Print time', 'Filament length', 'Filament volume']
        fields = ['fileName', 'timestamp', 'success', 'printTime', 'filamentLength', 'filamentVolume']
        if exportType == 'csv':
            writer = csv.writer(si, quoting=csv.QUOTE_ALL)
            writer.writerow(headers)

            for historyDetails in history_dicts:
                output = list()
                for field in fields:
                    value = historyDetails.get(field, '-')
                    output.append(value if value is not None else '-')
                writer.writerow(output)

            response = flask.make_response(si.getvalue())
            response.headers["Content-type"] = "text/csv"
            response.headers["Content-Disposition"] = "attachment; filename=octoprint_print_history_export.csv"
        elif exportType == 'csv_extra':
            unused_fields = ["spool", "user", "note", "id", "parameters"]
            csv_header = set(fields)

            for historyDetails in history_dicts:
                parameters = load_json(historyDetails, "parameters")
                csv_header |= set(parameters.keys())
            # Doesn't handle Camelcase
            csv_header = map(lambda x: x.replace(" ", "_"), csv_header)
            csv_header = rename_duplicates(fields, csv_header, prefix="g")
            rearranged_header = fields[:]
            for column in csv_header:
                if column not in headers:
                    rearranged_header.append(column)
            csv_header = rearranged_header

            ParametersRow = namedtuple_with_defaults('TableRow', csv_header)
            writer = csv.writer(si, quoting=csv.QUOTE_ALL)
            writer.writerow(csv_header)
            for historyDetails in history_dicts:
                parameters = load_json(historyDetails, "parameters")
                historyDetails.update(parameters)
                for key in unused_fields:
                    if key in history_dicts:
                        historyDetails.pop(key)

                for key in ["Plastic volume", "Plastic weight", "Filament length"]:
                    if historyDetails.get(key, None):
                        historyDetails[key] = re.search(r"[\d\.]*", historyDetails[key]).group(0)
                if historyDetails.get("Build time", None):
                    # Randomly failed
                    try:
                        match = re.match(r"(\d+) hours (\d+) minutes", historyDetails.get("Build time", None))
                        historyDetails["Build time"] = (int(match.group(1)) * 60 + int(match.group(2))) * 60
                    except: pass
                parameters_row = ParametersRow(**prepare_dict(historyDetails))
                writer.writerow([getattr(parameters_row, field) for field in parameters_row._fields])

            response = flask.make_response(si.getvalue())
            response.headers["Content-type"] = "text/csv"
            response.headers["Content-Disposition"] = "attachment; filename=octoprint_print_history(extra)_export.csv"
        elif exportType == 'excel':
            import xlsxwriter

            workbook = xlsxwriter.Workbook(si)
            worksheet = workbook.add_worksheet()
            for column, header in enumerate(headers):
                worksheet.write(0, column, header)

            for row, historyDetails in enumerate(history_dicts):
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
