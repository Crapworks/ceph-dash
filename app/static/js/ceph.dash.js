$(function () {
    // global variable to configure refresh interval and timeout (in seconds!)
    var refreshInterval = 5;
    var refreshTimeout = 3;

    // calculate outdated warning thresholds
    var outDatedWarning = (refreshInterval * 3);
    var outDatedError = (refreshInterval * 10);

    // last updated timestamp global variable
    var lastUpdatedTimestamp = 0;

    // add a endsWith function to strings
    String.prototype.endsWith = function(suffix) {
        return this.indexOf(suffix, this.length - suffix.length) !== -1;
    };

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
        grid: {
            show: true
        },
        xaxis: {
            mode: "time",
            timezone: "browser"
        },
        legend: {
            show: true
        },
        grid: {
            hoverable: true,
            clickable: true
        },
        tooltip: true,
        tooltipOpts: {
            id: "tooltip",
            defaultTheme: false,
            content: "%s: %y"
        },
        yaxis: {
            min: 0
        },
        colors: [ "#62c462", "#f89406", "#ee5f5b", "#5bc0de" ]
    }

    function updatePlot(backend) {
        if (window.location.pathname.endsWith('/')) {
            var endpoint = window.location.pathname + backend +'/';
        } else {
            var endpoint = window.location.pathname + '/' +  backend +'/';
        }

        $.getJSON(endpoint, function(data) {
            $.each(data.results, function(index, series) {
                //// set the yaxis mode
                flot_options.yaxis.mode = (typeof series[0].mode != "undefined") ? series[0].mode : null;

                //// update plot
                $.plot('#' + backend + (index+1), series, flot_options);
            });
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

    // Initialize unhealthy osd popover {{{
    $("#unhealthy_osds").popover({
        html: true,
        placement: 'bottom',
        trigger: 'hover'
    });
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
          error: function() {
              // refresh last updated timestamp
              timeStamp = Math.floor(Date.now() / 1000);
              timeDiff = timeStamp - lastUpdatedTimestamp;

              if (lastUpdatedTimestamp == 0) {
                  lastUpdatedTimestamp = timeStamp - refreshInterval;
                  timeDiff = refreshInterval;
              }


              if (timeDiff > outDatedWarning) {
                  msg = 'Content has last been refreshed more than ' + timeDiff + ' seconds before';
                  $('#last_update').show();
                  $('#last_update').tooltip({
                      placement: 'bottom',
                  });
                  $('#last_update').attr('data-original-title', msg);
              }
          },
          timeout: (refreshTimeout * 1000)
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
        HEALTH_ERR: 'danger',
        down: 'warning',
        out: 'danger'
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
            // refresh last updated timestamp
            timeStamp = Math.floor(Date.now() / 1000);
            lastUpdatedTimestamp = timeStamp;
            $('#last_update').hide();

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

            writesPerSec = fmtBytes(data['pgmap']['write_bytes_sec'] || 0);
            readsPerSec = fmtBytes(data['pgmap']['read_bytes_sec'] || 0);

            // *osd state*
            numOSDtotal = data['osdmap']['osdmap']['num_osds'] || 0;
            numOSDin = data['osdmap']['osdmap']['num_in_osds'] || 0;
            numOSDup = data['osdmap']['osdmap']['num_up_osds'] || 0;
            numOSDunhealthy = data['osdmap']['osdmap']['num_osds'] - data['osdmap']['osdmap']['num_up_osds'] || 0;
            unhealthyOSDDetails = data['osdmap']['details'];
            osdFull = data['osdmap']['osdmap']['full'];
            osdNearFull = data['osdmap']['osdmap']['nearfull'];

            var $parent = $("#unhealthy_osds").parent('.panel');

            if (numOSDunhealthy == '0') {
                $parent.removeClass('panel-danger');
                $parent.addClass('panel-success');
            } else {
                $parent.removeClass('panel-success');
                $parent.addClass('panel-danger');
            }

            // *overall status*
            clusterStatusOverall = data['health']['overall_status'];
            clusterHealthSummary = data['health']['summary'];

            // *monitor state*
            monmapMons = data['monmap']['mons'];
            if (monmapMons.length > 1) {
                timechekMons = data['health']['timechecks']['mons'];
            } else {
                timechekMons = data['health']['health']['health_services'][0]['mons'];
            }
            // }}}

            // Update Content {{{
            // ----------------------------------------------------------------
            // update current throughput values
            if ('op_per_sec' in data['pgmap']) {
                $("#operations_per_second").html(data['pgmap']['op_per_sec'] || 0);
                $("#ops_container").show();
            } else {
                if (!('write_op_per_sec' in data['pgmap'] || 'read_op_per_sec' in data['pgmap'])) {
                    $("#operations_per_second").html(0);
                    $("#ops_container").show();
                } else {
                    $("#ops_container").hide();
                }
            }

            if ('write_op_per_sec' in data['pgmap'] || 'read_op_per_sec' in data['pgmap']) {
                $("#write_operations_per_second").html(data['pgmap']['write_op_per_sec'] || 0);
                $("#read_operations_per_second").html(data['pgmap']['read_op_per_sec'] || 0);
                $("#write_ops_container").show();
                $("#read_ops_container").show();
            } else {
                $("#read_ops_container").hide();
                $("#write_ops_container").hide();
            }

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

            $("#write_bytes").html(writesPerSec);
            $("#read_bytes").html(readsPerSec);

            // update OSD states
            $("#num_osds").html(numOSDtotal);
            $("#num_in_osds").html(numOSDin);
            $("#num_up_osds").html(numOSDup);
            $("#unhealthy_osds").html(numOSDunhealthy);

            // update unhealthy osd popover if there are any unhealthy osds
            osdPopover = $('#unhealthy_osds').data('bs.popover');
            osdPopover.options.content = '';
            if (typeof(unhealthyOSDDetails) != 'undefined') {
                osdPopover.options.content += '<table class="table table-condensed">';
                $.each(unhealthyOSDDetails, function(index, osd_stats) {
                    osdPopover.options.content += '<tr>';
                    osdPopover.options.content += '<td class="text-' + ceph2bootstrap[osd_stats.status] + '">' + osd_stats.status + '</td>';
                    osdPopover.options.content += '<td>' + osd_stats.name + '</td>';
                    osdPopover.options.content += '<td>' + osd_stats.host + '</td>';
                    osdPopover.options.content += '</tr>';
                });
                osdPopover.options.content += '</table>';
            }

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
                // update graphite graphs if available
                updatePlot('graphite');
            }
            if ($('#influxdb1').length > 0) {
                // update influxdb graphs if available
                updatePlot('influxdb');
            }
            // }}}
        }

        ajaxCall(window.location.pathname, callback);
    };
    worker();
    setInterval(worker, (refreshInterval * 1000));
    // }}}
})

// vim: set foldmethod=marker foldlevel=0 ts=4 sts=4 filetype=javascript fileencoding=utf-8 formatoptions+=ro expandtab:
