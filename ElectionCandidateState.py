class ElectionCandidateState:
    (RUNNING, WON, ELIMINATED) = range(3)
    state_string = ["RUNNING", "WON", "ELIMINATED"]

    def __init__(self, election_round, election_candidate, candidate_state):
        self._round = election_round
        self._candidate = election_candidate
        self._state = candidate_state

    def round(self):
        return self._round

    def candidate(self):
        return self._candidate

    def state(self):
        return self._state

    def set_state(self, state):
        self._state = state

    def __repr__(self):
        return self.state_string[self._state]
