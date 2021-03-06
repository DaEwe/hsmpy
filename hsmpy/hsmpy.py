import json
import threading as thr
import queue
from queue import Queue
from collections import defaultdict
import time
import logging
import enum

logger = logging.getLogger(__name__)


class Condition(enum.Enum):
    ON_FAILED = 1
    ON_FINAL = 2
    EVENT_TYPE = 3
    TIMEOUT = 4


class Event:

    def __init__(self, type_, value):
        self.value = value
        self.type = type_

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = value

    @property
    def type(self):
        return self.__type

    @type.setter
    def type(self, type_):
        self.__type = type_

    def __str__(self):
        return json.dumps({"value": self.value, "type": self.type})

class State:
    def __init__(self, uber, **kwargs):
        self.uber = uber
        for k, v in kwargs.items():
            if callable(v):
                if "self" in v.__code__.co_varnames:
                    v = v(self)
                else:
                    v = v()
            setattr(self, k, v)

    def enter(self):
        logger.debug("Entered State '{}'".format(type(self).__name__))

    def loop(self, event):
        if event:
            logger.debug("Received Event {}".format(event))
        pass

    def final(self):
        logger.debug("Finalizing State '{}'".format(type(self).__name__))


class FINAL(State):
    def enter(self, **kwargs):
        logger.debug("Entered FINAL")


class FAILED(State):
    def enter(self, **kwargs):
        logger.debug("Entered FAILED")


class HSM(thr.Thread, State):
    transitions = []

    init_state = None

    def __init__(self, uber=None, init_state=None, loop_time=0.01, **kwargs):
        State.__init__(self, uber, **kwargs)
        thr.Thread.__init__(self,daemon=True    )
        self.state_changed_at = None
        self.event_queue = Queue()
        self.exit = thr.Event()
        self.current_state = init_state(self.uber) if init_state else self.init_state(self.uber)
        self.states = set()
        self._transitions = defaultdict(list)
        self.loop_time = loop_time
        self._load_transitions()

    def _load_transitions(self):
        for t in self.transitions:
            self.add_transition(t)

    def add_transition(self, transition):
        self.states.add(transition["from"])
        self.states.add(transition["to"])
        self._transitions[transition["from"]].append(transition)

    def send_event(self, event):
        self.event_queue.put(event)

    def enter(self):
        State.enter(self)
        self.state_changed_at = time.time()
        self.current_state.enter()

    def loop(self, event):
        self.check_transitions(event)
        self.current_state.loop(event)

    def final(self):
        State.final(self)
        pass

    def run(self, **kwargs):
        self.state_changed_at = time.time()
        self.current_state.enter(**kwargs)
        while not self.exit.is_set() and not isinstance(self.current_state, FINAL):
            loop_start = time.time()
            try:
                event = self.event_queue.get(block=False)
            except queue.Empty:
                event = None
            self.loop(event)
            time.sleep(max(self.loop_time - (time.time() - loop_start), 0))

    def shutdown(self):
        self.exit.set()

    def check_transitions(self, event):
        c_trans = self._transitions[type(self.current_state)]

        for trans in c_trans:
            if self._test(trans["condition"], event):
                self.current_state.final()
                self.current_state = trans["to"](self.uber, **trans["args"] if "args" in trans.keys() else {})
                self.state_changed_at = time.time()
                self.current_state.enter()
                return

    def _test(self, condition, event):
        if callable(condition):
            if "self" in condition.__code__.co_varnames:
                return condition(self.current_state)
            else:
                return condition()
        if isinstance(condition, Condition):
            if condition == Condition.ON_FAILED:
                return isinstance(self.current_state.current_state, FAILED)
            if condition == Condition.ON_FINAL:
                return isinstance(self.current_state.current_state, FINAL)
        elif isinstance(condition, bool):
            return condition
        else:
            if Condition.TIMEOUT in condition.keys():
                return condition[Condition.TIMEOUT] < self._get_time_since_state_change()
            if Condition.EVENT_TYPE in condition.keys():
                return event and condition[Condition.EVENT_TYPE] == event.type

        raise ValueError("unsupported Condition: {}".format(condition))

    def _get_time_since_state_change(self):
        return time.time() - self.state_changed_at
