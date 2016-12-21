$(function() {
    function PrintHistoryViewModel(parameters) {
        var self = this;

        self.loginState = parameters[0];
        self.global_settings = parameters[1];
        self.users = parameters[2];

        self.totalTime = ko.observable();
        self.totalUsage = ko.observable();
        self.isPrinting = ko.observable(undefined);

        self.spool_inventory = ko.observableArray([]);
        self.spool_inventory_base = ko.observableArray([]);
        self.availableCurrencies = ko.observableArray(['$', '€', '£']);

        self.selectedItem = ko.observable({fileName: ""});
        self.selectedItemId = ko.observable(undefined);
        self.selectedItemNote = ko.observable(undefined);
        self.selectedItemSpool = ko.observable(undefined);
        self.selectedItemUser = ko.observable(undefined);

        self.selectedItem.subscribe(function(newValue) {
            if (newValue === undefined) {
                self.selectedItemId(undefined);
                self.selectedItemNote(undefined);
                self.selectedItemSpool(undefined);
                self.selectedItemUser(undefined);
            } else {
                self.selectedItemId(newValue.id);
                self.selectedItemNote(newValue.note);
                self.selectedItemSpool(newValue.spool);
                self.selectedItemUser(newValue.user);
            }
        });

        self.onHistoryTab = false;
        self.dataIsStale = true;
        self.requestingData = false;
        self.pureData = {};
        self.lastMonthGraphMinimum = ko.observable(moment(new Date()).subtract(1, 'months').valueOf());

        self.onStartup = function () {
            self.detailsDialog = $("#printhistory_details_dialog");
        }

        self.onBeforeBinding = function () {
            self.settings = self.global_settings.settings.plugins.printhistory;
            self.spool_inventory(self.settings.spool_inventory.slice(0));
            self.spool_inventory_base(self.settings.spool_inventory);
        };

        self.listHelper = new ItemListHelper(
            "historyItems",
            {
                "fileNameAsc": function (a, b) {
                    // sorts ascending
                    if (a["fileName"].toLocaleLowerCase() < b["fileName"].toLocaleLowerCase()) return -1;
                    if (a["fileName"].toLocaleLowerCase() > b["fileName"].toLocaleLowerCase()) return 1;
                    return 0;
                },
                "fileNameDesc": function (a, b) {
                    // sorts ascending
                    if (a["fileName"].toLocaleLowerCase() < b["fileName"].toLocaleLowerCase()) return 1;
                    if (a["fileName"].toLocaleLowerCase() > b["fileName"].toLocaleLowerCase()) return -1;
                    return 0;
                },
                "timestampAsc": function(a, b) {
                    // sorts descending
                    if (a["timestamp"] > b["timestamp"]) return 1;
                    if (a["timestamp"] < b["timestamp"]) return -1;
                    return 0;
                },
                "timestampDesc": function(a, b) {
                    // sorts descending
                    if (a["timestamp"] > b["timestamp"]) return -1;
                    if (a["timestamp"] < b["timestamp"]) return 1;
                    return 0;
                },
                "printTimeAsc": function(a, b) {
                    // sorts descending
                    if (typeof (a["printTime"]) === 'undefined') return 1;
                    if (typeof (b["printTime"]) === 'undefined') return 0;

                    if (a["printTime"] > b["printTime"]) return 1;
                    if (a["printTime"] < b["printTime"]) return -1;
                    return 0;
                },
                "printTimeDesc": function(a, b) {
                    // sorts descending
                    if (typeof (a["printTime"]) === 'undefined') return 1;
                    if (typeof (b["printTime"]) === 'undefined') return 0;

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

        self.fileNameSort = function() {
            if (self.listHelper.currentSorting() == "fileNameAsc") {
                self.listHelper.changeSorting("fileNameDesc");
            } else {
                self.listHelper.changeSorting("fileNameAsc");
            }
        };

        self.timeStampSort = function() {
            if (self.listHelper.currentSorting() == "timestampDesc") {
                self.listHelper.changeSorting("timestampAsc");
            } else {
                self.listHelper.changeSorting("timestampDesc");
            }
        };

        self.printTimeSort = function() {
            if (self.listHelper.currentSorting() == "printTimeDesc") {
                self.listHelper.changeSorting("printTimeAsc");
            } else {
                self.listHelper.changeSorting("printTimeDesc");
            }
        };

        self.sortOrder = function(orderType) {
            var order = "";

            if (orderType == "fileName") {
                order = (self.listHelper.currentSorting() == 'fileNameAsc') ? '(' + _('ascending') + ')' : (self.listHelper.currentSorting() == 'fileNameDesc') ? '(' + _('descending') + ')' : '';
            } else if (orderType == "timestamp") {
                order = (self.listHelper.currentSorting() == 'timestampAsc') ? '(' + _('ascending') + ')' : (self.listHelper.currentSorting() == 'timestampDesc') ? '(' + _('descending') + ')' : '';
            } else {
                order = (self.listHelper.currentSorting() == 'printTimeAsc') ? '(' + _('ascending') + ')' : (self.listHelper.currentSorting() == 'printTimeDesc') ? '(' + _('descending') + ')' : '';
            }

            return order;
        };

        self.fromCurrentData = function (data) {
            var isPrinting = data.state.flags.printing;

            if (isPrinting != self.isPrinting()) {
                self.requestData();
            }

            self.isPrinting(isPrinting);
        };

        self.removeFile = function(id) {
            //console.log('PrintHistory - remove file: ' + id);

            $.ajax({
                url: "plugin/printhistory/history/" + id,
                type: "DELETE",
                dataType: "json",
                success: self.requestData
            });
        };

        self.requestData = function(params) {
            var force = false;

            if (_.isObject(params)) {
                force = params.force;
            }

            if (!self.onHistoryTab) {
                self.dataIsStale = true;
                return;
            }
            //console.log('PrintHistory - request data');
            if (self.requestingData) {
                return;
            }
            self.requestingData = true;

            $.ajax({
                url: "plugin/printhistory/history",
                type: "GET",
                data: {force: force},
                dataType: "json",
                success: self.fromResponse
            }).always(function() { self.requestingData = false; });
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
                    id: self.pureData[key].id,
                    fileName: self.pureData[key].fileName,
                    success: (self.pureData[key].success == 1),
                    filamentUsage: self.formatFilament(self.pureData[key]),
                    timestamp: (self.pureData[key].timestamp != null) ? self.pureData[key].timestamp : "",
                    printTime: (self.pureData[key].printTime != null) ? self.pureData[key].printTime : "",
                    note: (self.pureData[key].note != null) ? self.pureData[key].note : "",
                    spool: (self.pureData[key].spool != null) ? self.pureData[key].spool : "",
                    user: (self.pureData[key].user != null) ? self.pureData[key].user : ""
                });

                totalTime += (self.pureData[key].printTime !== undefined) ? self.pureData[key].printTime : 0;
                if (self.pureData[key].success == true) {
                    if (self.pureData[key].hasOwnProperty('filamentLength')) {
                        totalUsage["length"] += self.pureData[key].filamentLength;
                        totalUsage["volume"] += self.pureData[key].filamentVolume;
                    }

                    if (self.pureData[key].hasOwnProperty('filamentLength2')) {
                        totalUsage["length"] += self.pureData[key].filamentLength2;
                        totalUsage["volume"] += self.pureData[key].filamentVolume2;
                    }
                }
            });

            self.dataIsStale = false;

            self.totalTime(formatDuration(totalTime));
            self.totalUsage(formatFilament(totalUsage));

            self.listHelper.updateItems(dataRows);

            self.updatePlots();
        };

        self.formatFilament = function(data) {
            var tool0 = "";
            var tool1 = "";
            var output = "";

            if (data.hasOwnProperty('filamentLength') && data.filamentLength != 0) {
                tool0 += formatFilament({length: data.filamentLength, volume: data.filamentVolume});
            }

            if (data.hasOwnProperty('filamentLength2') && data.filamentLength2 != 0) {
                tool1 += formatFilament({length: data.filamentLength2, volume: data.filamentVolume2});
            }

            if (tool0 !== "" && tool1 !== "") {
                output = "Tool0: " + tool0 + "<br>Tool1: " + tool1;
            } else {
                if (tool0 !== "") {
                    output = tool0;
                } else {
                    output = tool1;
                }
            }

            return output;
        };

        self.export = function(type) {
            if (self.listHelper.items().length > 0) {
                return "plugin/printhistory/export/" + type + "?apikey=" + UI_API_KEY;
            } else {
                return false;
            }
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
            if (!self.onHistoryTab) {
                return;
            }

            if (self.dataIsStale) {
                self.requestData();
                return;
            }

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
            self.onHistoryTab = current == "#tab_plugin_printhistory"
            self.updatePlots();
        }

        self.addNewSpool = function() {
            self.spool_inventory.push({name: "New", price:0, currency: "$"});
        };

        self.removeSpool = function(spool) {
            self.spool_inventory.remove(spool);
        };

        self.onSettingsHidden = function() {
            self.spool_inventory(self.spool_inventory_base.slice(0));
        };

        self.onSettingsBeforeSave = function () {
            self.global_settings.settings.plugins.printhistory.spool_inventory(self.spool_inventory.slice(0));
        }

        self.showDetailsDialog = function(selectedData) {
            if (self.detailsDialog) {
                self.selectedItem(selectedData);

                self.detailsDialog.modal("show");
            }
        };

        self.addUpdateDetails = function(event) {
            var icon = $(".btn-primary i", self.detailsDialog);
            icon.addClass("icon-spinner icon-spin");

            var payload = {
                id: ko.toJS(self.selectedItemId),
                note: ko.toJS(self.selectedItemNote),
                spool: ko.toJS(self.selectedItemSpool),
                user: ko.toJS(self.selectedItemUser)
            }

            $.ajax({
                url: "plugin/printhistory/details",
                type: "PUT",
                data: JSON.stringify(payload),
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                success: self.closeDetails
            }).always(function() {
                icon.removeClass("icon-spinner icon-spin");
            });
        };

        self.closeDetails = function(data) {
            self.fromResponse(data);

            self.selectedItem(undefined);

            self.detailsDialog.modal("hide");
        };
    }

    ADDITIONAL_VIEWMODELS.push({
        construct: PrintHistoryViewModel,
        name: "PrintHistoryViewModel",
        dependencies: ["loginStateViewModel", "settingsViewModel", "usersViewModel"],
        elements: ["#tab_plugin_printhistory", "#settings_plugin_printhistory"]
});
});