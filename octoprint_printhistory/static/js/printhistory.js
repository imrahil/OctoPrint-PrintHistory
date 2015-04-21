$(function() {
    function PrintHistoryViewModel(parameters) {
        var self = this;

        self.loginState = parameters[0];

        self.totalTime = ko.observable();
        self.totalUsage = ko.observable();

        self.isPrinting = ko.observable(undefined);

        self.listHelper = new ItemListHelper(
            "historyItems",
            {
                "fileName": function(a, b) {
                    // sorts ascending
                    if (a["fileName"].toLocaleLowerCase() < b["fileName"].toLocaleLowerCase()) return -1;
                    if (a["fileName"].toLocaleLowerCase() > b["fileName"].toLocaleLowerCase()) return 1;
                    return 0;
                },
                "timestamp": function(a, b) {
                    // sorts descending
                    if (a["timestamp"] > b["timestamp"]) return -1;
                    if (a["timestamp"] < b["timestamp"]) return 1;
                    return 0;
                },
                "printTime": function(a, b) {
                    // sorts descending
                    if (a["printTime"] > b["printTime"]) return -1;
                    if (a["printTime"] < b["printTime"]) return 1;
                    return 0;
                }
            },
            {
                "successful": function(file) {
                    return (file["success"] == true);
                }
            },
            "timestamp",
            [],
            ["successful"],
            15
        );

        self.fromCurrentData = function (data) {
            var isPrinting = data.state.flags.printing;

            if (isPrinting != self.isPrinting()) {
                self.requestData();
            }

            self.isPrinting(isPrinting);
        };

        self.requestData = function() {
            $.ajax({
                url: "plugin/printhistory/history",
                type: "GET",
                dataType: "json",
                success: self.fromResponse
            });
        };

        self.fromResponse = function(data) {
            var dataRows = [];
            var pureData = data.history;
            var totalTime = 0;
            var totalUsage = {};

            totalUsage["length"] = 0;
            totalUsage["volume"] = 0;

            _.each(_.keys(pureData), function(key) {
                dataRows.push({
                    fileName: pureData[key].fileName,
                    success: pureData[key].success,
                    filamentUsage: (pureData[key].success == true) ? formatFilament({length: pureData[key].filamentLength, volume: pureData[key].filamentVolume}) : "-",
                    timestamp: pureData[key].timestamp,
                    formattedDate: formatDate(pureData[key].timestamp),
                    printTime: pureData[key].printTime
                });

                totalTime += pureData[key].printTime;
                totalUsage["length"] += (pureData[key].success == true) ? pureData[key].filamentLength : 0;
                totalUsage["volume"] += (pureData[key].success == true) ? pureData[key].filamentVolume : 0;
            });

            self.totalTime(formatDuration(totalTime));
            self.totalUsage(formatFilament(totalUsage));

            self.listHelper.updateItems(dataRows);
        };

        self.onBeforeBinding = function () {
            self.requestData();
        };
    }

    ADDITIONAL_VIEWMODELS.push([
        PrintHistoryViewModel,
        ["loginStateViewModel"],
        ["#tab_plugin_printhistory"]
    ]);
});