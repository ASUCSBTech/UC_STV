class ElectionCandidateState:
    (RUNNING, WON, ELIMINATED) = range(3)

    def __init__(self, candidate, state):
        self.candidate = candidate
        self.state = state

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def get_candidate(self):
        return self.candidate