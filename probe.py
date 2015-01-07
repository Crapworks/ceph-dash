import sys
import os
import datetime
import traceback

from threading import Thread, Event
from daemon import Daemon
from conn import CephClusterCommand

from pymongo import MongoClient

runfile = "/var/run/cephprobe/cephprobe.pid"
logfile = "/var/log/cephprobe.log"

def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

def getMongoClient():
    mongodb_host = "127.0.0.1";
    mongodb_port = 27017;

    client = MongoClient(mongodb_host, mongodb_port)
    return client

def processStatusDump(db):
    status_cmd = CephClusterCommand(prefix='status', format='json')
    status = status_cmd.run()
    db.status.update({'fsid': status['fsid']}, status, upsert=True)

def processOsdDump(db):
    osd_cmd = CephClusterCommand(prefix='osd dump', format='json')
    osddump = osd_cmd.run()
    db.osd.update({'fsid': osddump['fsid']}, osddump, upsert=True)

def processPgDump(db):
    pg_cmd = CephClusterCommand(prefix='pg dump', format='json')
    pgdump = pg_cmd.run()
    for pg in pgdump["pg_stats"]:
        db.pg.update({'pgid': pg['pgid']}, pg, upsert=True)

class Repeater(Thread):
    def __init__(self, name, event, function, args=[], period = 5.0):
        Thread.__init__(self)
        self.name = name
        self.stopped = event
        self.period = period
        self.function = function
        self.args = args
    def run(self):
        while not self.stopped.wait(self.period):
            try:
                sys.stderr.write("[" + str(datetime.datetime.now()) + "] Processing "+ self.name + ".\n")
                self.function(*self.args)
            except Exception as e:
                sys.stderr.write("[" + str(datetime.datetime.now()) + "] WARNING: " + e.__class__.__name__ + "\n")
                traceback.print_exc(file = sys.stderr)
                pass

evt = Event()

class CephProbeDaemon(Daemon):
    def __init__(self, pidfile):
        Daemon.__init__(self, pidfile, stdout = logfile, stderr = logfile)

    def run(self):
        client = getMongoClient()
        db = client["ceph"]

        status_refresh = 3
        osd_dump_refresh = 3
        pg_dump_refresh = 60

        statusThread = None
        if status_refresh > 0:
            statusThread = Repeater("StatusDump", evt, processStatusDump, [db], status_refresh)
            statusThread.start()

        if osd_dump_refresh > 0:
            osdThread = Repeater("OsdDump", evt, processOsdDump, [db], osd_dump_refresh)
            osdThread.start()

        if pg_dump_refresh > 0:
            pgThread = Repeater("PgDump", evt, processPgDump, [db], pg_dump_refresh)
            pgThread.start()


if __name__ == "__main__":
    ensure_dir(runfile)
    ensure_dir(logfile)
    daemon = CephProbeDaemon(runfile)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "Usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)

