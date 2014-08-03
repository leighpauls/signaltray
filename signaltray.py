import objc, re, os
from Foundation import *
from AppKit import *
from PyObjCTools import NibClassBuilder, AppHelper

import ping

icon_neutral = 'icons/neutral.png'
icon_good = 'icons/good.png'
icon_slow = 'icons/slow.png'
icon_bad = 'icons/bad.png'
icon_disconnected = 'icons/disconnected.png'

GOOD_STATE_ID = 0
SLOW_STATE_ID = 1
BAD_STATE_ID = 2
DISCONNECTED_STATE_ID = 3

start_time = NSDate.date()

def evaluatePing(ping_results):
    """Evaluates the results of AsyncPing, returning the *_STATE_ID appropriate
    to these results"""
    # TODO: these benchmarks are highly subjective, and should be user-tunable
    if ping_results is None or ping_results.loss_pct > 99:
        return DISCONNECTED_STATE_ID
    # a rough estimate of the 95th percentile round trip ping
    p95_ping = ping_results.round_trip + ping_results.stddev * 3
    # 100ms is the magic number for unnoticable latency
    if ping_results.loss_pct < 25 and p95_ping < 100:
        return GOOD_STATE_ID
    # these numbers are arbitrary
    if ping_results.loss_pct < 25 and p95_ping < 300:
        return SLOW_STATE_ID
    return BAD_STATE_ID

def makePing():
    return ping.AsyncPing('google.com')

class Signaltray(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        statusbar = NSStatusBar.systemStatusBar()
        # Create the statusbar item
        self.status_item = \
            statusbar.statusItemWithLength_(NSVariableStatusItemLength)

        # Set initial image
        self.status_item.setImage_(
            NSImage.alloc().initByReferencingFile_(icon_neutral))

        # Load the active images
        self.state_images = [
            NSImage.alloc().initByReferencingFile_(icon_good),
            NSImage.alloc().initByReferencingFile_(icon_slow),
            NSImage.alloc().initByReferencingFile_(icon_bad),
            NSImage.alloc().initByReferencingFile_(icon_disconnected)]

        # Let it highlight upon clicking
        self.status_item.setHighlightMode_(1)

        # Set a tooltip
        initial_status = 'Waiting for ping...'
        self.status_item.setToolTip_(initial_status)

        # Build a very simple menu
        menu = NSMenu.alloc().init()
        self.status_menu_item = NSMenuItem.alloc() \
            .initWithTitle_action_keyEquivalent_(initial_status, None, '')
        menu.addItem_(self.status_menu_item)

        menu_item = NSMenuItem.alloc() \
            .initWithTitle_action_keyEquivalent_('Quit', 'terminate:', '')
        menu.addItem_(menu_item)

        self.status_item.setMenu_(menu)

        # Start the first asynchronous ping process
        self.ping = makePing()

        # Get the timer going
        self.timer = NSTimer.alloc() \
            .initWithFireDate_interval_target_selector_userInfo_repeats_(
                start_time,
                2.0,
                self,
                'tick:',
                None,
                True)
        NSRunLoop.currentRunLoop().addTimer_forMode_(
            self.timer,
            NSDefaultRunLoopMode)
        self.timer.fire()

    def tick_(self, notification):
        if not self.ping.isReady():
            return
        ping_results = self.ping.getResults()

        self.status_item.setImage_(
            self.state_images[evaluatePing(ping_results)])

        status_string = 'No connection' if ping_results is None else '\n'.join([
            "Packet Loss: " + str(int(ping_results.loss_pct)) + "%",
            "Ping: " + str(int(ping_results.round_trip)) + " ms",
            "Ping stddev: " + str(int(ping_results.stddev)) + " ms"])
        self.status_item.setToolTip_(status_string)
        self.status_menu_item.setAttributedTitle_(
            NSAttributedString.alloc().initWithString_(status_string))

        # start a new ping
        self.ping = makePing()

if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    delegate = Signaltray.alloc().init()
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()
