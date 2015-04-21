$(function() {
    function PrintHistoryViewModel() {
        var self = this;

        self.totalTime = ko.observable();
        self.totalUsage = ko.observable();
        self.rows = ko.observableArray([]);

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
                    filamentUsage: formatFilament({length: pureData[key].filamentLength, volume: pureData[key].filamentVolume}),
                    timestamp: formatTimeAgo(pureData[key].timestamp),
                    formattedDate: formatDate(pureData[key].timestamp),
                    printTime: formatDuration(pureData[key].printTime)
                });

                totalTime += pureData[key].printTime;
                totalUsage["length"] += pureData[key].filamentLength;
                totalUsage["volume"] += pureData[key].filamentVolume;
            });

            self.totalTime(formatDuration(totalTime));
            self.totalUsage(formatFilament(totalUsage));
            self.rows(dataRows);
        };

        self.onBeforeBinding = function () {
            self.requestData();
        };
    }

    ADDITIONAL_VIEWMODELS.push([
        PrintHistoryViewModel,
        [],
        ["#tab_plugin_printhistory"]
    ]);
});