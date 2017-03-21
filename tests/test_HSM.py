import logging
import multiprocessing
import sys
import time
from unittest import TestCase

from hsmpy import HSM, State, FINAL, Condition

mpl = multiprocessing.log_to_stderr()
mpl.setLevel(logging.INFO)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

logger = logging.getLogger(__name__)


class TestHSM(TestCase):
    def test_run(self):
        class S1(State):
            def __init__(self):
                self.loops = 0

            def enter(self, **kwargs):
                logger.debug("Entered State 1")

            def loop(self, event):
                logger.debug("Looping {}".format(self.loops))
                self.loops += 1

            def final(self):
                logger.debug("Leaving State 1")

        class S2(State):
            def __init__(self):
                self.loops = 0

            def enter(self, **kwargs):
                logger.debug("Entered State 2")

            def loop(self, event):
                logger.debug("Looping {}".format(self.loops))
                self.loops += 1

            def final(self):
                logger.debug("Leaving State 2")

            def counts_exceeded(self):
                return self.loops > 42

        self.hsm = HSM(init_state=S1)

        def test():
            logger.debug(time.clock())
            return time.clock() > 0.1

        self.hsm.add_transition({"from": S1, "to": S2, "condition": {"timeout": 5}})
        self.hsm.add_transition({"from": S2, "to": S1, "condition": {"event": "wah"}})
        self.hsm.add_transition({"from": S1, "to": S2, "condition": test})
        self.hsm.add_transition({"from": S2, "to": FINAL, "condition": S2.counts_exceeded})

        logger.debug("Starting hsm...")
        self.hsm.start()
        logger.debug("Started.")
        time.sleep(7)
        self.hsm.send_event("wah")
        self.hsm.join()
        logger.debug("Final")

    def test_class_based_run(self):
        class S1(State):
            def __init__(self):
                self.loops = 0

            def enter(self, **kwargs):
                logger.debug("Entered State 1")

            def loop(self, event):
                logger.debug("Looping {}".format(self.loops))
                self.loops += 1

            def final(self):
                logger.debug("Leaving State 1")

        class S2(State):
            def __init__(self):
                self.loops = 0

            def enter(self, **kwargs):
                logger.debug("Entered State 2")

            def loop(self, event):
                logger.debug("Looping {}".format(self.loops))
                self.loops += 1

            def final(self):
                logger.debug("Leaving State 2")

            def counts_exceeded(self):
                return self.loops > 42

        def test():
            return time.clock() > 0.1

        class MyHSM(HSM):
            transitions = [
                {"from": S1, "to": S2, "condition": {"timeout": 5}},
                {"from": S2, "to": S1, "condition": {"event": "wah"}},
                {"from": S1, "to": S2, "condition": test},
                {"from": S2, "to": FINAL, "condition": S2.counts_exceeded},
            ]

            init_state = S1

        mhsm = MyHSM()
        logger.debug("Starting mhsm...")
        logger.debug(len(mhsm._transitions))
        mhsm.start()
        logger.debug("Started.")
        time.sleep(7)
        mhsm.send_event("wah")
        mhsm.join()
        logger.debug("Final")

    def test_hierarchical_run(self):
        class S1(State):
            pass

        class S2(State):
            pass

        class S3(State):
            pass

        class S4(State):
            pass

        class S5(State):
            pass

        class InnerHSM(HSM):
            transitions = [
                {"from": S1, "to": S2, "condition": {"timeout": 2}},
                {"from": S2, "to": S3, "condition": {"timeout": 2}},
                {"from": S3, "to": FINAL, "condition": {"timeout": 2}},
            ]

            init_state = S1

        class OuterHSM(HSM):
            transitions = [
                {"from": S4, "to": S5, "condition": {"timeout": 2}},
                {"from": S5, "to": InnerHSM, "condition": {"timeout": 2}},
                {"from": InnerHSM, "to": FINAL, "condition": Condition.ON_FINAL},
            ]

            init_state = S4

        ohsm = OuterHSM()
        ohsm.start()
        ohsm.join()

    def test_hierarchical_with_event_run(self):
        class S1(State):
            pass

        class S2(State):
            def loop(self, event):
                if event:
                    logger.debug("S2 received Event {}".format(event))

        class S3(State):
            def loop(self, event):
                if event:
                    logger.debug("S3 received Event {}".format(event))

        class S4(State):
            pass

        class S5(State):
            pass

        class InnerHSM(HSM):
            transitions = [
                {"from": S1, "to": S2, "condition": {"event": "drei"}},
                {"from": S1, "to": S3, "condition": {"event": "vier"}},
                {"from": S1, "to": FINAL, "condition": {"timeout": 5}},
                {"from": S3, "to": FINAL, "condition": {"timeout": 2}},
                {"from": S2, "to": FINAL, "condition": {"timeout": 2}},
            ]

            init_state = S1

        class OuterHSM(HSM):
            transitions = [
                {"from": S4, "to": S5, "condition": {"event": "eins"}},
                {"from": S5, "to": InnerHSM, "condition": {"event": "zwei"}},
                {"from": InnerHSM, "to": FINAL, "condition": Condition.ON_FINAL},
            ]

            init_state = S4

        ohsm = OuterHSM()
        ohsm.start()
        time.sleep(2)
        for e in ["eins", "zwei", "drei", "vier"]:
            ohsm.send_event(e)
        ohsm.join()

    def test_state_arguments(self):

        class S1(State):
            def loop(self, event):
                logger.debug([self.x, self.y, self.z])
                self.x += 1

        class Init(State):
            pass

        class MyHSM(HSM):
            transitions = [
                {"from": Init, "to": S1, "condition": True, "args": {"x": 1, "y": 2, "z": 3 }},
                {"from": S1, "to": FINAL, "condition": {"timeout": 5}}
            ]

            init_state = Init

        hsm = MyHSM()
        hsm.start()
        hsm.join()
