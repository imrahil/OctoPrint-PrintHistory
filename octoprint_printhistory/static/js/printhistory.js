$(function() {
    function PrintHistoryViewModel(parameters) {
        var self = this;

        self.loginState = parameters[0];

        self.totalTime = ko.observable();
        self.totalUsage = ko.observable();
        self.isPrinting = ko.observable(undefined);

        self.pureData = {};
        self.lastMonthGraphMinimum = ko.observable(moment(new Date()).subtract(1, 'months').valueOf());

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

        self.removeFile = function(key) {
            $.ajax({
                url: "plugin/printhistory/history/" + key,
                type: "DELETE",
                dataType: "json",
                success: self.requestData
            });
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
            self.pureData = data.history;
            var totalTime = 0;
            var totalUsage = {};

            totalUsage["length"] = 0;
            totalUsage["volume"] = 0;

            _.each(_.keys(self.pureData), function(key) {
                dataRows.push({
                    key: key,
                    fileName: self.pureData[key].fileName,
                    success: self.pureData[key].success,
                    filamentUsage: (self.pureData[key].success == true) ? formatFilament({length: self.pureData[key].filamentLength, volume: self.pureData[key].filamentVolume}) : "-",
                    timestamp: self.pureData[key].timestamp,
                    printTime: self.pureData[key].printTime
                });

                totalTime += self.pureData[key].printTime;
                totalUsage["length"] += (self.pureData[key].success == true) ? self.pureData[key].filamentLength : 0;
                totalUsage["volume"] += (self.pureData[key].success == true) ? self.pureData[key].filamentVolume : 0;
            });

            self.totalTime(formatDuration(totalTime));
            self.totalUsage(formatFilament(totalUsage));

            self.listHelper.updateItems(dataRows);

            self.updatePlots();
        };

        self.export = function(type) {
            return "plugin/printhistory/export/" + type;
        };

        self.onBeforeBinding = function () {
            self.requestData();
        };

        self.editAnnotation = function (key) {

        };

        self.changeGraphRange = function (range) {
            if (range == 'week') {
                self.lastMonthGraphMinimum(moment(new Date()).subtract(1, 'weeks').valueOf());
            } else {
                self.lastMonthGraphMinimum(moment(new Date()).subtract(1, 'months').valueOf());
            }

            self.updatePlots();
        };


        function labelFormatter(label, series) {
            return "<div style='font-size:8pt; text-align:center; padding:2px; color: #666666;'>" + label + "<br/>" + Math.round(series.percent) + "%</div>";
        }

        self.updatePlots = function() {
            var lastmonth_graph = $("#printhistory-lastmonth-graph");
            var success_graph = $("#printhistory-success-graph");

            var successCount = 0;
            var failureCount = 0;
            var lastmonth_data = [];
            var agreggateData = {};

            var lastmonthGraphOptions = {
                series: {
                    bars: {
                        show: true,
                        barWidth: 1000*60*60*24*0.6,
                        lineWidth: 0,
                        fillColor: '#31C448',
                        align: "center"
                    }
                },
                yaxis: {
                    tickDecimals: 0
                },
                xaxis: {
                    mode: "time",
                    minTickSize: [1, "day"],
                    min: self.lastMonthGraphMinimum(),
                    max: new Date().getTime(),
                    timeformat: "%m-%d"
                },
                legend: {
                    show: false
                }
            };

            var successGraphOptions = {
                series: {
                    pie: {
                        show: true,
                        radius: 1,
                        label: {
                            show: true,
                            radius: 1/2,
                            formatter: labelFormatter,
                            background: {
                                opacity: 0.5
                            }
                        }
                    }
                },
                legend: {
                    show: false
                }
            };

            _.each(_.keys(self.pureData), function(key) {
                successCount += (self.pureData[key].success == true) ? 1 : 0;
                failureCount += (self.pureData[key].success != true) ? 1 : 0;

                var day = moment.unix(self.pureData[key].timestamp).format('YYYY-MM-DD');
                if (!agreggateData.hasOwnProperty(day)) {
                    agreggateData[day] = 0;
                }
                agreggateData[day] += 1;
            });

            _.each(_.keys(agreggateData), function(key) {
                var day = moment(key).valueOf();
                lastmonth_data.push([day, agreggateData[key]]);
            });

            var success_data = [
                { label: "Success", color: '#00FF00', data: successCount},
                { label: "Failure", color: '#FF0000', data: failureCount}
            ];

            $.plot(lastmonth_graph, [lastmonth_data], lastmonthGraphOptions);
            $.plot(success_graph, success_data, successGraphOptions);
        };

        self.onAfterTabChange = function(current, previous) {
            if (current != "#tab_plugin_printhistory") {
                return;
            }
            self.updatePlots();
        }
    }

    ADDITIONAL_VIEWMODELS.push([
        PrintHistoryViewModel,
        ["loginStateViewModel"],
        ["#tab_plugin_printhistory"]
    ]);
});