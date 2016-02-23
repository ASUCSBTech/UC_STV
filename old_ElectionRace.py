from ElectionRaceRound import ElectionRaceRound
from ElectionCandidateState import ElectionCandidateState


class ElectionRace:
    def __init__(self, id, position, max_winners, extended_data):
        self.id = id
        self.position = position
        self.max_winners = max_winners
        self.extended_data = extended_data
        self.candidates = {}
        self.voters = []
        self.rounds = []
        self.winners = []

    def get_id(self):
        return self.id

    def get_extended_data(self):
        return self.extended_data

    def get_droop_quota(self):
        if self.max_winners > 1:
            return (float(len(self.voters)) / (self.max_winners + 1)) + 1
        elif self.max_winners == 1:
            return float(len(self.voters) + 1)/2

    def get_rounds_all(self):
        return self.rounds

    def get_rounds_latest(self):
        if len(self.rounds) == 0:
            return None
        return self.rounds[len(self.rounds) - 1]

    def get_rounds_previous(self, round):
        current_round_index = self.rounds.index(round)
        if current_round_index == 0:
            return None
        return self.rounds[current_round_index - 1]

    def get_candidates_all(self):
        return self.candidates

    def candidate_add(self, candidate):
        candidate_data = {
            "candidate": candidate,
            "state": ElectionCandidateState(candidate, ElectionCandidateState.RUNNING)
        }
        self.candidates[str(candidate.get_id())] = candidate_data

    def voter_add(self, voter):
        if voter in self.voters:
            return
        self.voters.append(voter)

    def candidate_find(self, candidate_id):
        try:
            return self.candidates[candidate_id]["candidate"]
        except ValueError:
            return None

    def round_add(self):
        # Round number begins at 1.
        new_round = ElectionRaceRound(self, len(self.rounds) + 1)
        for candidate in self.candidates:
            if self.candidates[candidate]["state"].get_state() == ElectionCandidateState.RUNNING:
                new_round.add_candidate(self.candidates[candidate]["candidate"])
        self.rounds.append(new_round)
        return new_round

    def run_step(self):
        # Get the latest round when running a step.
        current_round = self.get_rounds_latest()
        if current_round is None:
            current_round = self.round_add()

        # If there are voters that haven't been included in the round,
        # then add that voter into the round and end step.
        if len(current_round.get_voters()) != len(self.voters):
            voter = self.voters[len(current_round.get_voters())]
            current_round.add_voter(voter)
            if current_round.get_round() == 1:
                voter.set_voter_round_value(self, current_round, 1)
            return

        # If we are here, that means all votes have been tabulated.

        # Check to see if there are winners in this round.
        round_winners = current_round.get_winning_candidates()
        for round_winner in round_winners:
            self.candidates[str(round_winner.get_id())]["state"].set_state(ElectionCandidateState.WON)

        # If there were no winners in this round, then this round
        # is an elimination round and we will remove the lowest scoring
        # candidate.

    def __hash__(self):
        return hash((self.id, self.position))

    def __eq__(self, other):
        return (self.id, self.position) == (other.id, other.position)