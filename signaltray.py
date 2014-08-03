import objc, re, os
from Foundation import *
from AppKit import *
from PyObjCTools import NibClassBuilder, AppHelper

import ping

icon_background = 'icon_background.png'

start_time = NSDate.date()

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
            NSImage.alloc().initByReferencingFile_(icon_background))

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
        status = 'No connection' if ping_results is None else '\n'.join([
            "Packet Loss: " + str(int(ping_results.loss_pct)) + "%",
            "Ping: " + str(int(ping_results.round_trip)) + " ms",
            "Ping stddev: " + str(int(ping_results.stddev)) + " ms"])
        self.status_item.setToolTip_(status)
        attributed_status = NSAttributedString \
            .alloc() \
            .initWithString_(status)
        self.status_menu_item.setAttributedTitle_(attributed_status)
        self.ping = makePing()

if __name__ == "__main__":
  app = NSApplication.sharedApplication()
  delegate = Signaltray.alloc().init()
  app.setDelegate_(delegate)
  AppHelper.runEventLoop()
