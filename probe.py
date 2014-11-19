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

def processStatus(db):
    status_cmd = CephClusterCommand(prefix='status', format='json')
    status = status_cmd.run()
    db.status.update({'fsid': status['fsid']}, status, upsert=True)

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

        statusThread = None
        status_cmd = CephClusterCommand(prefix='status', format='json')
        if status_refresh > 0:
            statusThread = Repeater("StatusDump", evt, processStatus, [db], status_refresh)
            statusThread.start()


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

