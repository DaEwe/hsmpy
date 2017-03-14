from multiprocessing import Queue, Process, Event
import queue
from collections import defaultdict
import time
import logging


logger = logging.getLogger(__name__)


class HSM(Process):
    def __init__(self, init_state):
        super().__init__()
        self.state_changed_at = None
        self.event_queue = Queue()
        self.exit = Event()
        self.current_state = init_state()
        self.states = set()
        self.transitions = defaultdict(list)

    def add_state(self, state):
        self.states.add(state)

    def add_transition(self, transition):
        self.states.add(transition["from"])
        self.states.add(transition["to"])
        self.transitions[transition["from"]].append(transition)

    def send_event(self, event):
        self.event_queue.put(event)

    def run(self):
        self.state_changed_at = time.time()
        while not self.exit.is_set() and not isinstance(self.current_state, FINAL):
            self.check_transitions()
            self.current_state.loop()
            time.sleep(0.1)

    def shutdown(self):
        self.exit.set()

    def check_transitions(self):
        c_trans = self.transitions[type(self.current_state)]
        c_events = []
        while not self.event_queue.empty():
            try:
                c_events.append(self.event_queue.get())
            except queue.Empty:
                break

        for trans in c_trans:
            if self._test(trans["condition"], c_events):
                self.current_state.final()
                self.current_state = trans["to"]()
                self.state_changed_at = time.time()
                self.current_state.enter()
                return

    def _test(self, condition, events):
        if callable(condition):
            return condition()
        if "timeout" in condition.keys():
            return condition["timeout"] < self._get_time_since_state_change()
        if "event" in condition.keys():
            return condition["event"] in events

    def _get_time_since_state_change(self):
        return time.time() - self.state_changed_at


class State:
    def enter(self):
        pass

    def loop(self):
        pass

    def final(self):
        pass


class FINAL(State):
    def enter(self):
        logger.debug("Entered FINAL")
