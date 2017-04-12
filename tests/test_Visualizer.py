import logging
import random
import sys
from unittest import TestCase
from hsmpy import HSM, Condition, FINAL, State, Visualizer, FAILED

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

logger = logging.getLogger(__name__)


class TestVisualizer(TestCase):
    def testSimple(self):
        class One(State):
            pass

        class Two(State):
            pass

        class Three(State):
            pass

        def sometimes():
            return random.random() > 0.5

        class Four(HSM):
            transitions = [
                {"from": One, "to": Two, "condition": {Condition.TIMEOUT: 1}},
                {"from": Two, "to": FINAL, "condition": {Condition.TIMEOUT: 1}},
                {"from": Two, "to": FAILED, "condition": sometimes},

            ]
            init_state = One

        class MyHSM(HSM):
            transitions = [
                {"from": One, "to": Two, "condition": {Condition.TIMEOUT: 1}},
                {"from": Two, "to": Three, "condition": {Condition.TIMEOUT: 1}},
                {"from": Two, "to": FAILED, "condition": sometimes},
                {"from": Three, "to": Four, "condition": sometimes},
                {"from": Three, "to": FINAL, "condition": {Condition.TIMEOUT: 1}},
                {"from": Four, "to": FINAL, "condition": {Condition.TIMEOUT: 1}},
            ]

            init_state = One

        v = Visualizer(MyHSM)
        v.save_graph("test.png")
