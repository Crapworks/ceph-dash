$(function () {
    // Gauge chart configuration options {{{
    var gauge_options = {
        palette: 'Soft Pastel',
        animation: {
            enabled: false
        },
        valueIndicator: {
            type: 'triangleNeedle',
            color: '#7a8288'
        },
        title: {
             text: 'Cluster storage utilization',
             font: { size: 18, color: '#c8c8c8', family: 'Helvetica' },
             position: 'bottom-center'
        },
        geometry: {
            startAngle: 180, 
            endAngle: 0
        },
        margin: {
            top: 0,
            right: 10
        },
        rangeContainer: {
            ranges: [
                { startValue: 0, endValue: 60, color: '#62c462' },
                { startValue: 60, endValue: 80, color: '#f89406' },
                { startValue: 80, endValue: 100, color: '#ee5f5b' }
            ]
        },
        scale: {
            startValue: 0, 
            endValue: 100,
            majorTick: {
                tickInterval: 20
            },
            label: {
                customizeText: function (arg) {
                    return arg.valueText + ' %';
                }
            }
        }
    };
    // }}}

    // Graphite to flot configuration options {{{
    var flot_options = {
        colors: [ "#62c462", "#f89406", "#ee5f5b", "#5bc0de" ],
        grid: {
            show: true
        },
        xaxis: {
            tickFormatter: function() { return ""; }
        },
        legend: {
            show: true
        },
        yaxis: {
            //tickFormatter: function() { return ""; }
            min: 0,
        }
    }

    // TODO: Test more graphs / alignment
    function updatePlot(index, graphite_url, targets, from, labels, colors, mode) {
        combined_targets = "";
        $.each(targets, function(index, target) {
            combined_targets += "&target=" + target;
        });
        var query_url = graphite_url + "/render?format=json&from=" + from + combined_targets;

        var series = [ ];
        $.getJSON(query_url, function(targets) {
            if (targets.length > 0) {
                $.each(targets, function(index, target) {
                    var datapoints = target.datapoints;
                    var xzero = datapoints[0][1];
                    var data = $.map(target.datapoints, function(value) {
                    if (value[0] === null) return null;
                        return [[ value[1]-xzero, value[0] ]];
                    });

                    // replace null value with previous item value
                    for (var i = 0; i < data.length; i++) {
                        if (i > 0 && data[i] === null) data[i] = data[-i];
                    }

                    series.push({
                        data: data,
                        label: labels[index],
                        lines: { fill: true }
                    });
                });
                // update plot
                if (typeof mode != undefined) {
                    flot_options.yaxis.mode = mode
                }
                if (typeof color != undefined) {
                    flot_options.colors = colors
                }
                $.plot("#graphite" + index, series, flot_options);
            }
        });
    }
    // }}}

    // Pie chart configuration options {{{
    var chart_options = {
        animation: {
            enabled: false
        },
        tooltip: {
            enabled: true,
            format:"decimal",
            percentPrecision: 2,
            font: { size: 14, color: '#1c1e22', family: 'Helvetica' },
            arrowLength: 10,
            customizeText: function() { 
                return this.valueText + " - " + this.argumentText + " (" + this.percentText + ")";
            }
        },
        customizePoint: function (point) {
            if (point.argument.indexOf('active+clean') >= 0) {
                return {
                    color: '#62c462'
                }
            } else if (point.argument.indexOf('active') >= 0) {
                return {
                    color: '#f89406'
                }
            } else {
                return {
                    color: '#ee5f5b'
                }
            }
        },
        size: {
            height: 350,
            width: 315
        },
        legend: {
            visible: false
        },
        series: [{
            type: "doughnut",
            argumentField: "state_name",
            valueField: "count",
            label: {
                visible: false,
            }
        }]
    };
    // }}}

    // Convert bytes to human readable form {{{
    function fmtBytes(bytes) {
        if (bytes==0) { return "0 bytes"; }
        var s = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'];
        var e = Math.floor(Math.log(bytes) / Math.log(1024));
        return (bytes / Math.pow(1024, e)).toFixed(2) + " " + s[e];
    }
    // }}}

    // MAKE SECTION COLLAPSABLE {{{
    $('.cd-collapsable').on("click", function (e) {
        if ($(this).hasClass('cd-collapsed')) {
            // expand the panel
            $(this).parents('.panel').find('.panel-body').slideDown();
            $(this).removeClass('cd-collapsed');
        }
        else {
            // collapse the panel
            $(this).parents('.panel').find('.panel-body').slideUp();
            $(this).addClass('cd-collapsed');
        }
    });
    // }}}

    // GENERIC AJAX WRAPER {{{
    function ajaxCall(url, callback) {
        $.ajax({
          url: url,
          dataType: 'json',
          type: 'GET',
          data: null,
          contentType: 'application/json',
          success: callback,
          complete: function() {
            setTimeout(worker, 5000);
          }
        });
    }
    // }}}

    // CREATE A ALERT MESSAGE {{{
    function message(severity, msg) {
        if (severity == 'success') { icon = 'ok' }
        if (severity == 'warning') { icon = 'flash' }
        if (severity == 'danger') { icon = 'remove' }
        return '<div class="alert alert-' + severity + '"><strong><span class="glyphicon glyphicon-' + icon + '">&nbsp;</span>' + msg + '</strong></div>';
    }
    // }}}

    // CREATE PANEL {{{
    function panel(severity, titel, message) {
        tmp = '<div class="panel panel-' + severity + '">';
        tmp = tmp + '<div class="panel-heading">' + titel + '</div>';
        tmp = tmp + '<div class="panel-body" align="center">';
        tmp = tmp + '<h1>' + message + '</h1>';
        tmp = tmp + '</div>';
        tmp = tmp + '</div>';
        return tmp;
    }
    // }}}

    // MAPPING CEPH TO BOOTSTRAP {{{
    var ceph2bootstrap = {
        HEALTH_OK: 'success',
        HEALTH_WARN: 'warning',
        HEALTH_ERR: 'danger'
    }
    // }}}

    // INITIALIZE EMPTY PIE CHART {{{
    $("#pg_status").dxPieChart($.extend(true, {}, chart_options, {
        dataSource: []
    }));
    // }}}

    // WORKER FUNCTION (UPDATED) {{{
    function worker() {
        callback = function(data, status, xhr) {
            // Update cluster fsid
            $("#cluster_fsid").html(data['fsid']);

            // load all relevant data from retrieved json {{{
            // ----------------------------------------------------------------
            // *storage capacity*
            bytesTotal = data['pgmap']['bytes_total'];
            bytesUsed = data['pgmap']['bytes_used'];
            percentUsed = Math.round((bytesUsed / bytesTotal) * 100);

            // *placement groups*
            pgsByState = data['pgmap']['pgs_by_state'];
            numPgs = data['pgmap']['num_pgs'];

            // *recovery status*
            recoverBytes = data['pgmap']['recovering_bytes_per_sec'];
            recoverKeys = data['pgmap']['recovering_keys_per_sec'];
            recoverObjects = data['pgmap']['recovering_objects_per_sec'];

            // *throughput* 
            opsPerSec = data['pgmap']['op_per_sec'] || 0;
            writesPerSec = fmtBytes(data['pgmap']['write_bytes_sec'] || 0);
            readsPerSec = fmtBytes(data['pgmap']['read_bytes_sec'] || 0);

            // *osd state*
            numOSDtotal = data['osdmap']['osdmap']['num_osds'] || 0;
            numOSDin = data['osdmap']['osdmap']['num_in_osds'] || 0;
            numOSDup = data['osdmap']['osdmap']['num_up_osds'] || 0;
            numOSDunhealthy = data['osdmap']['osdmap']['num_osds'] - data['osdmap']['osdmap']['num_up_osds'] || 0;
            osdFull = data['osdmap']['osdmap']['full'];
            osdNearFull = data['osdmap']['osdmap']['nearfull'];

            // *overall status*
            clusterStatusOverall = data['health']['overall_status'];
            clusterHealthSummary = data['health']['summary'];

            // *monitor state*
            monmapMons = data['monmap']['mons'];
            timechekMons = data['health']['timechecks']['mons'];
            // }}}

            // Update Content {{{
            // ----------------------------------------------------------------
            // update storage capacity
            $("#utilization").dxCircularGauge($.extend(true, {}, gauge_options, {
                value: percentUsed
            }));
            $("#utilization_info").html(fmtBytes(bytesUsed) + " / " + fmtBytes(bytesTotal) + " (" + percentUsed + "%)");

            // update placement group chart
            var chart = $("#pg_status").dxPieChart("instance");
            chart.option('dataSource', pgsByState);

            $("#pg_status_info").html(numPgs + "  placementgroups in cluster");

            // update recovering status
            if (typeof(recoverBytes) != 'undefined') {
                $("#recovering_bytes").html(panel('warning', 'Recovering bytes / second', fmtBytes(recoverBytes)));
            } else {
                $("#recovering_bytes").empty();
            }
            if (typeof(recoverKeys) != 'undefined') {
                $("#recovering_keys").html(panel('warning', 'Recovering keys / second', recoverKeys));
            } else {
                $("#recovering_keys").empty();
            }
            if (typeof(recoverObjects) != 'undefined') {
                $("#recovering_objects").html(panel('warning', 'Recovering objects / second', recoverObjects));
            } else {
                 $("#recovering_objects").empty();
            }

            // update current throughput values
            $("#operations_per_second").html(opsPerSec);
            $("#write_bytes").html(writesPerSec);
            $("#read_bytes").html(readsPerSec);

            // update OSD states
            $("#num_osds").html(numOSDtotal);
            $("#num_in_osds").html(numOSDin);
            $("#num_up_osds").html(numOSDup);
            $("#unhealthy_osds").html(numOSDunhealthy);

            // update osd full / nearfull warnings
            $("#osd_warning").empty();
            if (osdFull == "true") {
                $("#osd_warning").append(message('danger', 'OSD FULL ERROR'));
            }
            if (osdNearFull == "true") {
                $("#osd_warning").append(message('warning', 'OSD NEARFULL WARNING'));
            }

            // update overall cluster state
            $("#overall_status").empty();
            $("#overall_status").append(message(ceph2bootstrap[clusterStatusOverall], 'Cluster Status:' + clusterStatusOverall));

            // update overall cluster status details
            $("#overall_status").append('<ul class="list-group">');
            $.each(clusterHealthSummary, function(index, obj) {
                $("#overall_status").append('<li class="list-group-item active"><span class="glyphicon glyphicon-flash"></span><strong>' + obj['summary'] + '</strong></li>');
            });
            $("#overall_status").append('</ul>');

            // update monitor status
            $("#monitor_status").empty();
            $.each(monmapMons, function(index, mon) {
                health = 'HEALTH_ERR'
                $.each(timechekMons, function(index, mon_health) {
                    if (mon['name'] == mon_health['name']) {
                        health = mon_health['health'];
                    }
                });
                msg = 'Monitor ' + mon['name'].toUpperCase() + ': ' + health;
                $("#monitor_status").append('<div class="col-md-4">' + message(ceph2bootstrap[health], msg) + '</div>');
            });

            if ($('#graphite1').length > 0) {
                // update graphite if available
                $.each(config.graphite.metrics, function(index, metric) {
                    updatePlot(index + 1, config.graphite.url, metric.targets, metric.from, metric.labels, metric.colors, metric.mode);
                });
            }
            // }}}
        }

        ajaxCall(window.location.pathname, callback);
    };
    worker();
    // }}}
})

// vim: set foldmethod=marker foldlevel=0 ts=4 sts=4 filetype=javascript fileencoding=utf-8 formatoptions+=ro expandtab:
