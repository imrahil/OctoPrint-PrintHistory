# coding=utf-8

__author__ = "Jarek Szczepanski <imrahil@imrahil.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2014 Jarek Szczepanski - Released under terms of the AGPLv3 License"

def exportHistoryData(self, exportType):
    import flask
    import csv
<<<<<<< Updated upstream
    import StringIO
=======
    import re
    from utils import namedtuple_with_defaults, prepare_dict, load_json, rename_duplicates
>>>>>>> Stashed changes

    try:
        import StringIO
    except ImportError:
        import io as StringIO

    history_dict = self._getHistoryDict()

    if history_dict is not None:
        si = StringIO.StringIO()

        headers = ['File name', 'Timestamp', 'Success', 'Print time', 'Filament length', 'Filament volume']
        if exportType == 'csv':
            writer = csv.writer(si, quoting=csv.QUOTE_ALL)
            writer.writerow(headers)

            for historyDetails in history_dict:
                output = list()
<<<<<<< Updated upstream
                output.append(historyDetails["fileName"] if "fileName" in historyDetails and historyDetails["fileName"] is not None else "-")
                output.append(historyDetails["timestamp"] if "timestamp" in historyDetails and historyDetails["timestamp"] is not None else "-")
                output.append(historyDetails["success"] if "success" in historyDetails and historyDetails["success"] is not None else "-")
                output.append(historyDetails["printTime"] if "printTime" in historyDetails and historyDetails["printTime"] is not None else "-")
                output.append(historyDetails["filamentLength"] if "filamentLength" in historyDetails and historyDetails["filamentLength"] is not None else "-")
                output.append(historyDetails["filamentVolume"] if "filamentVolume" in historyDetails and historyDetails["filamentVolume"] is not None else "-")

                writer.writerow(output);
=======
                for field in fields:
                    value = historyDetails.get(field, '-')
                    output.append(value if value is not None else '-')
                # /for field in fields
                writer.writerow(output)
            # /for historyDetailes in history_dict
>>>>>>> Stashed changes

            response = flask.make_response(si.getvalue())
            response.headers["Content-type"] = "text/csv"
            response.headers["Content-Disposition"] = "attachment; filename=octoprint_print_history_export.csv"
<<<<<<< Updated upstream
=======
        elif exportType == 'csv_extra':
            fields = ["fileName", "timestamp", "success", "printTime", "filamentLength", "filamentVolume"]
            unused_fields = ["spool", "user", "note", "id", "parameters"]
            csv_header = set(fields)

            for historyDetails in history_dict:
                parameters = load_json(historyDetails, "parameters")
                csv_header |= set(parameters.keys())
            # /for historyDetailes in history_dict

            csv_header = map(lambda x: x.replace(" ", "_"), csv_header)
            csv_header = rename_duplicates(fields, csv_header, prefix="g")
            rearranged_header = fields[:]
            for column in csv_header:
                if column not in headers:
                    rearranged_header.append(column)
                # /if column not in headers
            # /for column in csv_header
            csv_header = rearranged_header

            ParametersRow = namedtuple_with_defaults('TableRow', csv_header)
            writer = csv.writer(si, quoting=csv.QUOTE_ALL)
            writer.writerow(csv_header)
            for historyDetails in history_dict:
                parameters = load_json(historyDetails, "parameters")
                historyDetails.update(parameters)
                for key in unused_fields:
                    historyDetails.pop(key)
                # /for key in unused_fields
                for key in ["Plastic volume", "Plastic weight", "Filament length"]:
                    if historyDetails.get(key, None):
                        historyDetails[key] = re.search(r"[\d\.]*", historyDetails[key]).group(0)
                    # /if historyDetails.get(key, None)
                # /for key in ["Plastic volume", "Plastic weight", "Filament length"]
                if historyDetails.get("Build time", None):
                    match = re.match(r"(\d+) hours (\d+) minutes", historyDetails.get("Build time", None))
                    historyDetails["Build time"] = (int(match.group(1)) * 60 + int(match.group(2))) * 60
                # /if historyDetails.get("Build time", None)
                parameters_row = ParametersRow(**prepare_dict(historyDetails))
                writer.writerow([getattr(parameters_row, field) for field in parameters_row._fields])
            # /for historyDetails in history_dict:

            response = flask.make_response(si.getvalue())
            response.headers["Content-type"] = "text/csv"
            response.headers["Content-Disposition"] = "attachment; filename=octoprint_print_history(extra)_export.csv"
>>>>>>> Stashed changes
        elif exportType == 'excel':
            import xlsxwriter

            workbook = xlsxwriter.Workbook(si)
            worksheet = workbook.add_worksheet()
<<<<<<< Updated upstream
            col = 0
            for header in headers:
                worksheet.write(0, col, header)
                col += 1

            row = 1
            for historyDetails in history_dict:
                worksheet.write(row, 0, (historyDetails["fileName"] if "fileName" in historyDetails and historyDetails["fileName"] is not None else "-"))
                worksheet.write(row, 1, (historyDetails["timestamp"] if "timestamp" in historyDetails and historyDetails["timestamp"] is not None else "-"))
                worksheet.write(row, 2, (historyDetails["success"] if "success" in historyDetails and historyDetails["success"] is not None else "-"))
                worksheet.write(row, 3, (historyDetails["printTime"] if "printTime" in historyDetails and historyDetails["printTime"] is not None else "-"))
                worksheet.write(row, 4, (historyDetails["filamentLength"] if "filamentLength" in historyDetails and historyDetails["filamentLength"] is not None else "-"))
                worksheet.write(row, 5, (historyDetails["filamentVolume"] if "filamentVolume" in historyDetails and historyDetails["filamentVolume"] is not None else "-"))

                row += 1
=======
            for column, header in enumerate(headers):
                worksheet.write(0, column, header)
            # /for column, header in enumerate(headers)

            for row, historyDetails in enumerate(history_dict):
                for column, field in enumerate(fields):
                    value = historyDetails.get(field, '-')
                    worksheet.write(row + 1, column, (value if value is not None else '-'))
                # /for column, field in enumerate(fields)
            # /for row, historyDetails in enumerate(history_dict)
>>>>>>> Stashed changes

            workbook.close()

            response = flask.make_response(si.getvalue())
            response.headers["Content-type"] = "application/vnd.ms-excel"
<<<<<<< Updated upstream
            response.headers["Content-Disposition"] = "attachment; filename=octoprint_print_history_export.xls"

=======
            response.headers["Content-Disposition"] = "attachment; filename=octoprint_print_history_export.xlsx"
        # /if exportType == 'csv':
>>>>>>> Stashed changes
        return response
    else:
        return flask.make_response("No history file", 400)
    # /if history_dict is not None
# /def exportHistoryData(self, exportType)
