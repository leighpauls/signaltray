import subprocess, re, time

TEST_HOST = 'facebook.com'

class PingResult:
    """Container class for AsyncPing's result"""
    pass

class AsyncPing:
    def __init__(self, hostname, num_pings=5):
        self.proc = subprocess.Popen(
            ['ping', '-q', '-c', str(num_pings), hostname],
            stdout=subprocess.PIPE)

    def isReady(self):
        """Return True iff results are ready"""
        try:
            return self.proc.poll() is not None
        except:
            # something went wrong
            return True

    def getResults(self):
        """Block until results are ready, then return them"""
        try:
            out, err = self.proc.communicate()
        except:
            return None
        if err is not None:
            return None
        match = re.search(
            """
\d+ packets transmitted, \d+ packets received, (\d+\.\d+)% packet loss
round-trip min/avg/max/stddev = \d+.\d+/(\d+.\d+)/\d+.\d+/(\d+.\d+) ms
""",
            out)
        if match is None:
            return None
        res = PingResult()
        (res.loss_pct, res.round_trip, res.stddev) = tuple(
            map(float, match.groups()))
        return res

if __name__ == '__main__':
    ping = AsyncPing(TEST_HOST)
    while not ping.isReady():
        print "waiting..."
        time.sleep(0.5)
    ping_results = ping.getResults()
    if ping_results is None:
        print 'Ping failed'
        exit()
    print "loss", ping_results.loss_pct
    print "round trip", ping_results.round_trip
    print "stddev", ping_results.stddev
