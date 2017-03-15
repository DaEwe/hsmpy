from unittest import TestCase

import logging

import sys

import time

from hsmpy import HSM, State, FINAL
import multiprocessing

mpl = multiprocessing.log_to_stderr()
mpl.setLevel(logging.INFO)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

logger = logging.getLogger(__name__)


class TestHSM(TestCase):
    def setUp(self):
        class S1(State):
            def __init__(self):
                self.loops = 0

            def enter(self):
                logger.debug("Entered State 1")

            def loop(self):
                logger.debug("Looping {}".format(self.loops))
                self.loops += 1

            def final(self):
                logger.debug("Leaving State 1")

        class S2(State):
            def __init__(self):
                self.loops = 0

            def enter(self):
                logger.debug("Entered State 2")

            def loop(self):
                logger.debug("Looping {}".format(self.loops))
                self.loops += 1

            def final(self):
                logger.debug("Leaving State 2")

            def counts_exceeded(self):
                return self.loops > 42

        def test():
            logger.debug(time.clock())
            return time.clock() > 0.1

        self.hsm = HSM(init_state=S1)
        self.hsm.add_transition({"from": S1, "to": S2, "condition": {"timeout": 5}})
        self.hsm.add_transition({"from": S2, "to": S1, "condition": {"event": "wah"}})
        self.hsm.add_transition({"from": S1, "to": S2, "condition": test})
        self.hsm.add_transition({"from": S2, "to": FINAL, "condition": S2.counts_exceeded})

    def test_run(self):
        logger.debug("Starting hsm...")
        self.hsm.start()
        logger.debug("Started.")
        time.sleep(7)
        self.hsm.send_event("wah")
        self.hsm.join()
        logger.debug("Final")
