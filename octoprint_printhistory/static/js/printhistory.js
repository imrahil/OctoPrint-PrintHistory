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
            10
        );

        self.fromCurrentData = function (data) {
            var isPrinting = data.state.flags.printing;

            if (isPrinting != self.isPrinting()) {
                self.requestData();
            }

            self.isPrinting(isPrinting);
        };

        self.removeFile = function(key) {
            //console.log('PrintHistory - remove file: ' + key);

            $.ajax({
                url: "plugin/printhistory/history/" + key,
                type: "DELETE",
                dataType: "json",
                success: self.requestData
            });
        };

        self.requestData = function() {
            //console.log('PrintHistory - request data');

            $.ajax({
                url: "plugin/printhistory/history",
                type: "GET",
                dataType: "json",
                success: self.fromResponse
            });
        };

        self.fromResponse = function(data) {
            //console.log('Callback - data: ' + data);

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
                    printTime: self.pureData[key].printTime,
                    note: self.pureData[key].hasOwnProperty('note') ? self.pureData[key].note : ""
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
            if (self.listHelper.items().length > 0) {
                return "plugin/printhistory/export/" + type + "?apikey=" + UI_API_KEY;
            } else {
                return false;
            }
        };

        self.onStartupComplete = function () {
            self.requestData();
        };

        self.editAnnotation = function (key) {
            // TODO - add some additional info about each print
        };

        self.changeGraphRange = function (range) {
            if (range == 'week') {
                self.lastMonthGraphMinimum(moment(new Date()).subtract(1, 'weeks').valueOf());
            } else if (range == 'month'){
                self.lastMonthGraphMinimum(moment(new Date()).subtract(1, 'months').valueOf());
            } else {
                self.lastMonthGraphMinimum(moment(new Date()).subtract(1, 'quarter').valueOf());
            }

            self.updatePlots();
        };


        function printhistoryLabelFormatter(label, series) {
            return "<div style='font-size:8pt; text-align:center; padding:2px; color: #666666;'>" + label + "<br/>" + Math.round(series.percent) + "%</div>";
        }

        self.updatePlots = function() {
            var lastmonth_graph = $("#printhistory-lastmonth-graph");
            var success_graph = $("#printhistory-success-graph");

            var lastmonthGraphOptions = {
                series: {
                    stack: 0,
                    bars: {
                        show: true,
                        barWidth: 1000*60*60*24*0.6,
                        lineWidth: 0,
                        fill: 1,
                        align: "center"
                    }
                },
                yaxis: {
                    tickDecimals: 0,
                    min: 0
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
                            formatter: printhistoryLabelFormatter,
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

            var successCount = 0;
            var failureCount = 0;

            var agreggateSuccess = {};
            var agreggateFailure = {};

            _.each(_.keys(self.pureData), function(key) {
                var day = moment.unix(self.pureData[key].timestamp).hour(0).minute(0).second(0).millisecond(0).valueOf();

                if (self.pureData[key].success == true) {
                    successCount += 1;

                    if (!agreggateSuccess.hasOwnProperty(day)) {
                        agreggateSuccess[day] = 0;
                    }
                    agreggateSuccess[day] += 1;
                } else {
                    failureCount += 1;

                    if (!agreggateFailure.hasOwnProperty(day)) {
                        agreggateFailure[day] = 0;
                    }
                    agreggateFailure[day] += 1;
                }
            });

            var successArr = [];
            var failureArr = [];

            _.each(_.keys(agreggateSuccess), function(key) {
                successArr.push([key, agreggateSuccess[key]]);
            });

            _.each(_.keys(agreggateFailure), function(key) {
                failureArr.push([key, agreggateFailure[key]]);
            });

            var lastmonth_data = [
                { label: "Success", color: '#31C448', data: successArr},
                { label: "Failure", color: '#FF0000', data: failureArr}
            ];

            var success_data = [
                { label: "Success", color: '#31C448', data: successCount},
                { label: "Failure", color: '#FF0000', data: failureCount}
            ];

            $.plot(lastmonth_graph, lastmonth_data, lastmonthGraphOptions);
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