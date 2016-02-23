from ElectionCandidateState import ElectionCandidateState
from ElectionRaceRound import ElectionRaceRound


class ElectionRace:
    (COMPLETE, INCOMPLETE) = range(2)

    def __init__(self, id, position, max_winners, extended_data):
        self.id = id
        self.position = position
        self.max_winners = max_winners
        self.extended_data = extended_data
        self.state = self.INCOMPLETE

        self.candidates = []
        self.voters = []
        self.rounds = []
        self.winners = []

    def get_id(self):
        return self.id

    def get_position(self):
        return self.position

    def get_extended_data(self):
        return self.extended_data

    def get_candidates_all(self):
        return self.candidates

    def get_winners(self):
        return self.winners

    def get_state(self):
        return self.state

    def get_max_winners(self):
        return self.max_winners

    def get_droop_quota(self):
        if self.max_winners > 1:
            return (float(len(self.voters)) / (self.max_winners + 1)) + 1
        elif self.max_winners == 1:
            return float(len(self.voters) + 1)/2

    def voter_add(self, voter):
        if voter in self.voters:
            return

        self.voters.append(voter)

    def candidate_add(self, candidate):
        if candidate in self.candidates:
            return

        self.candidates.append(candidate)

    def candidate_find(self, candidate_id):
        for candidate in self.candidates:
            if candidate_id == candidate.get_id():
                return candidate
        return None

    def round_add(self):
        new_round = ElectionRaceRound(self, len(self.rounds) + 1)
        self.rounds.append(new_round)

        for candidate in self.candidates:
            previous_round = self.round_get_previous(new_round)
            if previous_round is None:
                new_round.candidate_add(candidate, ElectionCandidateState(candidate, ElectionCandidateState.RUNNING))
                continue
            new_round.candidate_add(candidate, previous_round.candidate_state_get(candidate))

        return new_round

    def round_get_latest(self):
        if not self.rounds:
            return None

        return self.rounds[-1]

    def round_get_previous(self, round):
        current_round_index = self.rounds.index(round)
        if current_round_index == 0:
            return None
        return self.rounds[current_round_index - 1]

    def run(self):
        # Check if the race is complete.
        if self.state == self.COMPLETE:
            return

        # Get the latest round.
        current_round = self.round_get_latest()
        if current_round is None or current_round.state_get() == ElectionRaceRound.COMPLETE:
            current_round = self.round_add()

        # Add voters to this round.
        if current_round.voter_count() < len(self.voters):
            current_round.voter_add(self.voters[current_round.voter_count()])
            return

        # The round is now done with adding ballot count.
        current_round.tabulate()
        self.winners = current_round.winners_get()
        if len(self.winners) == self.max_winners:
            self.state = self.COMPLETE

        for candidate in self.candidates:
            if current_round.candidate_state_get(candidate).get_state() == ElectionCandidateState.RUNNING:
                return

        self.state = self.COMPLETE