import sys
import os
import datetime
import traceback

from threading import Thread, Event
from daemon import Daemon
from conn import CephClusterCommand

runfile = "/var/run/cephprobe/cephprobe.pid"
logfile = "/var/log/cephprobe.log"

def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

class Repeater(Thread):
    def __init__(self, name, event, function, period = 5.0):
        Thread.__init__(self)
        self.name = name
        self.stopped = event
        self.period = period
        self.function = function
    def run(self):
        while not self.stopped.wait(self.period):
            try:
                sys.stderr.write("[" + str(datetime.datetime.now()) + "] Processing "+ self.name + ".\n")
                print self.function()
            except Exception as e:
                sys.stderr.write("[" + str(datetime.datetime.now()) + "] WARNING: " + e.__class__.__name__ + "\n")
                traceback.print_exc(file = sys.stderr)
                pass

evt = Event()

class CephProbeDaemon(Daemon):
    def __init__(self, pidfile):
        Daemon.__init__(self, pidfile, stdout = logfile, stderr = logfile)

    def run(self):
        status_refresh = 3 

        statusThread = None
        status_cmd = CephClusterCommand(prefix='status', format='json')
        if status_refresh > 0:
            statusThread = Repeater("StatusDump", evt, status_cmd.run, status_refresh)
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

