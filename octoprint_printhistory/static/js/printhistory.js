$(function() {
    function PrintHistoryViewModel(parameters) {
        var self = this;

        self.loginState = parameters[0];
        self.global_settings = parameters[1];
        self.users = parameters[2];

        self.totalTime = ko.observable();
        self.totalUsage = ko.observable();
        self.averageTime = ko.observable();
        self.averageUsage = ko.observable();

        self.isPrinting = ko.observable(undefined);

        self.spool_inventory = ko.observableArray([]);
        self.spool_inventory_base = ko.observableArray([]);
        self.availableCurrencies = ko.observableArray(['$', '€', '£']);

        self.itemForEditing = ko.observable();

        var HistoryItem = function(data) {
            this.id = ko.observable();
            this.fileName = ko.observable();
            this.success = ko.observable();
            this.filamentVolume = ko.observable();
            this.filamentLength = ko.observable();
            this.timestamp = ko.observable();
            this.printTime = ko.observable();
            this.note = ko.observable();
            this.spool = ko.observable();
            this.user = ko.observable();

            this.successful = ko.computed(function() {
                return this.success() == 1;
            }, this);
            this.filamentUsage = ko.computed(self.formatFilament, this);
            this.formatedDate = ko.computed(function () {
                return formatDate(this.timestamp());
            }, this);
            this.formatedTimeAgo = ko.computed(function () {
                return formatTimeAgo(this.timestamp());
            }, this);
            this.formatedDuration = ko.computed(function () {
                return formatDuration(this.printTime());
            }, this);

            this.update(data);
        }

        HistoryItem.prototype.update = function (data) {
            var updateData = data || {}

            this.id(updateData.id);
            this.fileName(updateData.fileName);
            this.success(updateData.success);
            this.filamentVolume(updateData.filamentVolume || 0);
            this.filamentLength(updateData.filamentLength || 0);
            this.timestamp(updateData.timestamp || 0);
            this.printTime(updateData.printTime || 0);
            this.note(updateData.note || "");
            this.spool(updateData.spool || "");
            this.user(updateData.user || "");
        };

        self.onHistoryTab = false;
        self.dataIsStale = true;
        self.requestingData = false;
        self.pureData = {};
        self.lastMonthGraphMinimum = ko.observable(moment(new Date()).subtract(1, 'months').valueOf());

        self.onStartup = function () {
            self.detailsDialog = $("#printhistory_details_dialog");
            self.detailsDialog.on('hidden', self.onCancelDetails);
        }

        self.onBeforeBinding = function () {
            self.settings = self.global_settings.settings.plugins.printhistory;
            self.spool_inventory(self.settings.spool_inventory.slice(0));
            self.spool_inventory_base(self.settings.spool_inventory);
        };

        self.onAfterTabChange = function(current, previous) {
            self.onHistoryTab = current == "#tab_plugin_printhistory"
            self.updatePlots();
        }

        self.fromCurrentData = function (data) {
            var isPrinting = data.state.flags.printing;

            if (isPrinting != self.isPrinting()) {
                self.requestData();
            }

            self.isPrinting(isPrinting);
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
            }).always(function () {
                self.requestingData = false;
            });
        };

        self.fromResponse = function(data) {
            var dataRows = ko.utils.arrayMap(data.history, function (data) {
                return new HistoryItem(data);
            });

            self.pureData = data.history;

            self.dataIsStale = false;
            self.listHelper.updateItems(dataRows);
            self.updatePlots();
        };

        self.removeFile = function(id) {
            $.ajax({
                url: "plugin/printhistory/history/" + id(),
                type: "DELETE",
                dataType: "json",
                success: function(data) {
                    self.fromResponse(data);
                }
            });
        };

        self.formatFilament = function() {
            var tool0 = "";
            var tool1 = "";
            var output = "";

            if (this.filamentLength() != undefined) {
                tool0 += formatFilament({length: this.filamentLength(), volume: this.filamentVolume()});
            }

            //if (data.hasOwnProperty('filamentLength2') && data.filamentLength2 != 0) {
            //    tool1 += formatFilament({length: data.filamentLength2, volume: data.filamentVolume2});
            //}

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

                if (self.pureData[key].success == 1) {
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

        /*
         * -----------
         *  SETTINGS
         * -----------
         */
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

        /*
         * -----------
         *   DETAILS
         * -----------
         */
        self.showDetailsDialog = function(selectedData) {
            if (self.detailsDialog) {
                self.itemForEditing(new HistoryItem(ko.mapping.toJS(selectedData)));

                self.detailsDialog.modal("show");
            }
        };

        self.onCancelDetails = function (event) {
            if (event.target.id == "printhistory_details_dialog") {
                self.itemForEditing(null);
            }
        }

        self.addUpdateDetails = function(event) {
            var icon = $(".btn-primary i", self.detailsDialog);
            icon.addClass("icon-spinner icon-spin");

            var payload = {
                id: self.itemForEditing().id(),
                note: self.itemForEditing().note(),
                spool: self.itemForEditing().spool(),
                user: self.itemForEditing().user(),
                success: self.itemForEditing().success(),
                filamentLength: self.itemForEditing().filamentLength(),
                filamentVolume: self.itemForEditing().filamentVolume()
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

            self.listHelper.selectNone();

            self.detailsDialog.modal("hide");
        };

        self.listHelper = new ItemListHelper(
            "historyItems",
            {
                "fileNameAsc": function (a, b) {
                    // sorts ascending
                    if (a.fileName().toLocaleLowerCase() < b.fileName().toLocaleLowerCase()) return -1;
                    if (a.fileName().toLocaleLowerCase() > b.fileName().toLocaleLowerCase()) return 1;
                    return 0;
                },
                "fileNameDesc": function (a, b) {
                    // sorts ascending
                    if (a.fileName().toLocaleLowerCase() < b.fileName().toLocaleLowerCase()) return 1;
                    if (a.fileName().toLocaleLowerCase() > b.fileName().toLocaleLowerCase()) return -1;
                    return 0;
                },
                "timestampAsc": function (a, b) {
                    // sorts descending
                    if (a.timestamp() > b.timestamp()) return 1;
                    if (a.timestamp() < b.timestamp()) return -1;
                    return 0;
                },
                "timestampDesc": function (a, b) {
                    // sorts descending
                    if (a.timestamp() > b.timestamp()) return -1;
                    if (a.timestamp() < b.timestamp()) return 1;
                    return 0;
                },
                "printTimeAsc": function (a, b) {
                    // sorts descending
                    if (a.printTime() > b.printTime()) return 1;
                    if (a.printTime() < b.printTime()) return -1;
                    return 0;
                },
                "printTimeDesc": function (a, b) {
                    // sorts descending
                    if (a.printTime() > b.printTime()) return -1;
                    if (a.printTime() < b.printTime()) return 1;
                    return 0;
                }
            },
            {
                "all": function (item) {
                    return true;
                },
                "successful": function (item) {
                    return (item.success() == 1);
                },
                "failed": function (item) {
                    return (item.success() == 0);
                }
            },
            "timestamp", ["all"], [["all", "successful", "failed"]], 10
        );

        self.listHelper.items.subscribe(function(newValue) {
            var totalTime = 0;
            var totalUsage = {
                length: 0,
                volume: 0
            };
            var averageUsage = {
                length: 0,
                volume: 0
            };

            var itemList = newValue;
            var itemListLength = itemList.length;
            for (var i = 0; i < itemListLength; i++) {
                totalTime += itemList[i].printTime();

                totalUsage.length += itemList[i].filamentLength();
                totalUsage.volume += itemList[i].filamentVolume();
            }

            self.totalTime(formatDuration(totalTime));
            self.totalUsage(formatFilament(totalUsage));

            averageUsage.length = totalUsage.length / itemListLength;
            averageUsage.volume = totalUsage.volume / itemListLength;

            self.averageTime(formatDuration(totalTime / itemListLength));
            self.averageUsage(formatFilament(averageUsage));
        });

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
    }

    ADDITIONAL_VIEWMODELS.push({
        construct: PrintHistoryViewModel,
        name: "PrintHistoryViewModel",
        dependencies: ["loginStateViewModel", "settingsViewModel", "usersViewModel"],
        elements: ["#tab_plugin_printhistory", "#settings_plugin_printhistory"]
});
});