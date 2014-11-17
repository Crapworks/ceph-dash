import sys
import os
import time
from daemon import Daemon

runfile = "/var/run/cephprobe/cephprobe.pid"
logfile = "/var/log/cephprobe.log"

def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

class CephProbeDaemon(Daemon):
    def __init__(self, pidfile):
        Daemon.__init__(self, pidfile, stdout = logfile, stderr = logfile)

    def run(self):
        while True:
            sys.stderr.write("Working!\n")
            time.sleep(3)

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

