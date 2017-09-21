# coding=utf-8

__author__ = "Jarek Szczepanski <imrahil@imrahil.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2014 Jarek Szczepanski - Released under terms of the AGPLv3 License"

def exportHistoryData(self, exportType):
    import flask
    import unicodecsv as csv
    import StringIO
    import re
    from utils import namedtuple_with_defaults, prepare_dict, load_json, rename_duplicates

    history_dict = self._getHistoryDict()

    if history_dict is not None:
        si = StringIO.StringIO()

        headers = ['File name', 'Timestamp', 'Success', 'Print time', 'Spool', 'Filament length', 'Filament volume', 'User']
        fields = ['fileName', 'timestamp', 'success', 'printTime', 'spool', 'filamentLength', 'filamentVolume', 'user']
        if exportType == 'csv':
            writer = csv.writer(si, quoting=csv.QUOTE_ALL, encoding='utf-8')
            writer.writerow(headers)

            for historyDetails in history_dict:
                output = list()
                for field in fields:
                   value = historyDetails.get(field, '-')
                   if field == "timestamp":
                      output.append(formatTimestamp(value))
                   elif field == "printTime":
                      output.append(formatPrintTime(value))
                   else:
                      output.append(value if value is not None else '-')
                writer.writerow(output);

            response = flask.make_response(si.getvalue())
            response.headers["Content-type"] = "text/csv"
            response.headers["Content-Disposition"] = "attachment; filename=octoprint_print_history_export.csv"
        elif exportType == 'csv_extra':
            fields = ['fileName', 'timestamp', 'success', 'printTime', 'spool', 'filamentLength', 'filamentVolume', 'user']
            unused_fields = ["note", "id", "parameters"]
            csv_header = set(fields)

            for historyDetails in history_dict:
                parameters = load_json(historyDetails, "parameters")
                csv_header |= set(parameters.keys())

            csv_header = map(lambda x: x.replace(" ", "_"), csv_header)
            csv_header = rename_duplicates(fields, csv_header, prefix="g")
            rearranged_header = fields[:]
            for column in csv_header:
                if column not in headers:
                    rearranged_header.append(column)
            csv_header = rearranged_header

            ParametersRow = namedtuple_with_defaults('TableRow', csv_header)
            writer = csv.writer(si, quoting=csv.QUOTE_ALL, encoding='utf-8')
            writer.writerow(csv_header)
            for historyDetails in history_dict:
                parameters = load_json(historyDetails, "parameters")
                historyDetails.update(parameters)
                for key in unused_fields:
                    historyDetails.pop(key)
                for key in ["Plastic volume", "Plastic weight", "Filament length"]:
                    if historyDetails.get(key, None):
                        historyDetails[key] = re.search(r"[\d\.]*", historyDetails[key]).group(0)
                if historyDetails.get("Build time", None):
                    match = re.match(r"(\d+) hours (\d+) minutes", historyDetails.get("Build time", None))
                    historyDetails["Build time"] = (int(match.group(1)) * 60 + int(match.group(2))) * 60
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

            for row, historyDetails in enumerate(history_dict):
                for column, field in enumerate(fields):
                    if field == "timestamp":
					    value = formatTimestamp(historyDetails.get(field, '-'))
                    elif field == "printTime":
						value = formatPrintTime(historyDetails.get(field, '-'))
                    else:
                        value = historyDetails.get(field, '-')
                    worksheet.write(row + 1, column, (value if value is not None else '-'))
		
            workbook.close()

            response = flask.make_response(si.getvalue())
            response.headers["Content-type"] = "application/vnd.ms-excel"
            response.headers["Content-Disposition"] = "attachment; filename=octoprint_print_history_export.xlsx"

        return response
    else:
        return flask.make_response("No history file", 400)

def formatPrintTime(valueInSeconds):
     if valueInSeconds is not None:
	tmp = valueInSeconds
        hours = int(tmp/3600)
        tmp = tmp % 3600
        minutes = int(tmp / 60)
        tmp = tmp % 60
        seconds = int(tmp)

        return str(hours).zfill(3) + ":" + str(minutes).zfill(2) + ":" + str(seconds).zfill(2)
     else:
        return "-"

def formatTimestamp(millis):
     import datetime
     if millis is not None:
        return datetime.datetime.fromtimestamp(int(millis)).strftime('%Y-%m-%d %H:%M:%S')
     else:
        return '-'
