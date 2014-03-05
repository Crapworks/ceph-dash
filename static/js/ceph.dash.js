$(function () {
    //
    // Convert bytes to human readable form
    //
    function fmtBytes(bytes) {
        if (bytes==0) { return "0 bytes"; }
        var s = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'];
        var e = Math.floor(Math.log(bytes) / Math.log(1024));
        return (bytes / Math.pow(1024, e)).toFixed(2) + " " + s[e];
    }

    //
    // Gauge chart configuration options
    //
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

    //
    // Pie chart configuration options
    //
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

    // 
    // GENERIC AJAX WRAPER
    //
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

    //
    // CREATE A ALERT MESSAGE
    //
    function message(severity, msg) {
        if (severity == 'success') { icon = 'ok' }
        if (severity == 'warning') { icon = 'flash' }
        if (severity == 'danger') { icon = 'remove' }
        return '<div class="alert alert-' + severity + '"><strong><span class="glyphicon glyphicon-' + icon + '">&nbsp;</span>' + msg + '</strong></div>';
    }

    //
    // MAPPING CEPH TO BOOTSTRAP
    //
    var ceph2bootstrap = {
        HEALTH_OK: 'success',
        HEALTH_WARN: 'warning',
        HEALTH_ERR: 'danger'
    }

    //
    // WORKER FUNCTION (UPDATED)
    //
    function worker() {
        callback = function(data, status, xhr) {
            bytesTotal = data['pgmap']['bytes_total'];
            bytesUsed = data['pgmap']['bytes_used'];
            percentUsed = Math.round((bytesUsed / bytesTotal) * 100);

            // Update storage utilization gauge
            $("#utilization").dxCircularGauge($.extend(true, {}, gauge_options, {
                value: percentUsed
            }));
            $("#utilization_info").html(fmtBytes(bytesUsed) + " / " + fmtBytes(bytesTotal) + " (" + percentUsed + "%)");

            // update placement group chart
            $("#pg_status").dxPieChart($.extend(true, {}, chart_options, {
                dataSource: data['pgmap']['pgs_by_state'],
            }));
            $("#pg_status_info").html(data['pgmap']['num_pgs'] + "  placementgroups in cluster");

            // Update current throughput values
            $("#operations_per_second").html(data['pgmap']['op_per_sec'] || 0);
            $("#write_bytes").html(fmtBytes(data['pgmap']['write_bytes_sec'] || 0));
            $("#read_bytes").html(fmtBytes(data['pgmap']['read_bytes_sec'] || 0));

            // Update OSD states
            $("#num_osds").html(data['osdmap']['osdmap']['num_osds'] || 0);
            $("#num_in_osds").html(data['osdmap']['osdmap']['num_in_osds'] || 0);
            $("#num_up_osds").html(data['osdmap']['osdmap']['num_up_osds'] || 0);
            $("#unhealthy_osds").html(data['osdmap']['osdmap']['num_osds'] - data['osdmap']['osdmap']['num_up_osds'] || 0);

            // Update overall cluster state
            $("#overall_status").empty();
            $("#overall_status").append(message(ceph2bootstrap[data['health']['overall_status']], 'Cluster Status:' + data['health']['overall_status']));

            // Update overall cluster status details
            $("#overall_status").append('<ul class="list-group">');
            $.each(data['health']['summary'], function(index, obj) {
                $("#overall_status").append('<li class="list-group-item active"><span class="glyphicon glyphicon-flash"></span>' + obj['summary'] + '</li>');
            });
            $("#overall_status").append('</ul>');

            // Update monitor status
            $("#monitor_status").empty();
            $.each(data['health']['health']['health_services'][0]['mons'], function(index, mon) {
                msg = 'Monitor ' + mon['name'].toUpperCase() + ': ' + mon['health'];
                $("#monitor_status").append('<div class="col-md-4">' + message(ceph2bootstrap[mon['health']], msg) + '</div>');
            });
        }

        ajaxCall('/', callback);
    };
    worker();
})
