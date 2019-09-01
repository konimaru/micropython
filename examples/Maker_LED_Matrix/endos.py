import usocket, uselect
import utime

DEFAULT_TRGT = ('230.0.0.1', 7000)  # multicast
DEFAULT_SINK = ('', 0)              # INADDR_ANY

LINK_TIMEOUT = 10 *1000             # ms

class Listener(object):
    def __init__(self, user=None, *, target=DEFAULT_TRGT, sink=DEFAULT_SINK):
        self.target = target
        self.status = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)
        self.status.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
        self.status.bind(sink)

        self.timeout = 0
        self.leave   = False
        self.user    = user or self

    def run(self):
        p = uselect.poll()
        p.register(self.status, uselect.POLLIN)
 
        # data before timeout
        start = utime.ticks_ms()

        # listener
        while not self.leave:
            try:
                ready = p.poll(self.timeout)

                # timeout
                if not ready:
                    # send beacon
                    self.status.sendto(b'beacon', self.target)

                    # user indicator
                    self.user.action(0)

                    # reset timeout & start time
                    self.timeout = LINK_TIMEOUT
                    start = utime.ticks_ms()

                # status report
                elif self.status == ready[0][0]:
                    if ready[0][1] & (uselect.POLLHUP | uselect.POLLERR):
                        break

                    payload, address = self.status.recvfrom(2048)
                    if not payload:
                        break

                    # process payload
                    self.user(payload)

                    # adjust timeout, don't touch start time
                    duration = utime.ticks_diff(utime.ticks_ms(), start)
                    self.timeout = max(0, LINK_TIMEOUT - duration)

            except OSError as e:
                break

        # closing listener
        p.unregister(self.status)
        self.status.close()

        # exit status
        return self.leave

    def shutdown(self):
        self.leave = True

    # ---

    def __call__(self, payload):
        pass

    def action(self, parameter):
        pass

