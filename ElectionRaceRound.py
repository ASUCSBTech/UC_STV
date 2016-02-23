from ElectionCandidateState import ElectionCandidateState
from ElectionRaceError import ElectionRaceError


class ElectionRaceRound:
    (INCOMPLETE, COMPLETE) = range(2)

    def __init__(self, parent, round):
        self.round = round
        self.parent = parent
        self.voters = []
        self.candidates = {}
        self.candidates_tabulation = {}
        self.state = self.INCOMPLETE

    def voter_add(self, voter):
        self.voters.append(voter)

    def voter_count(self):
        return len(self.voters)

    def get_voters(self):
        return self.voters

    def get_round(self):
        return self.round

    def get_running_candidates(self):
        running_candidates = []
        for candidate in self.candidates:
            if self.candidate_state_get(candidate, tabulation=False).get_state() == ElectionCandidateState.RUNNING:
                running_candidates.append(candidate)
        return running_candidates

    def state_get(self):
        return self.state

    def candidate_add(self, candidate, state):
        self.candidates[candidate] = state

    def candidate_state_get(self, candidate, tabulation=True):
        if tabulation and candidate in self.candidates_tabulation:
            return self.candidates_tabulation[candidate]
        return self.candidates[candidate]

    def get_round_votes(self):
        results = {}

        ballots = self.get_round_ballots()

        for candidate in self.candidates:
            candidate_state = self.candidate_state_get(candidate, tabulation=False)
            if candidate_state.get_state() == ElectionCandidateState.RUNNING:
                ballot_total_value = 0
                for ballot in ballots:
                    if ballot.get_candidate() != candidate:
                        continue
                    ballot_total_value += ballot.get_value()
                results[candidate] = ballot_total_value
            elif candidate_state.get_state() == ElectionCandidateState.ELIMINATED:
                results[candidate] = 0
            elif candidate_state.get_state() == ElectionCandidateState.WON:
                results[candidate] = self.parent.get_droop_quota()

        # Check for exhausted ballots.
        exhausted_vote_value = 0
        for ballot in ballots:
            if ballot.get_candidate() is None:
                exhausted_vote_value += ballot.get_value()
        results[None] = exhausted_vote_value

        return results

    def get_round_ballots(self):
        eligible_candidates = []
        for candidate in self.candidates:
            if self.candidate_state_get(candidate, tabulation=False).get_state() == ElectionCandidateState.RUNNING:
                eligible_candidates.append(candidate)

        ballots = []
        for voter in self.voters:
            ballots.append(voter.race_get_voter_round_ballot(self.parent, self, eligible_candidates))

        return ballots

    def get_previous_round_lowest(self, candidate_a, candidate_b):
        previous_round = self.parent.round_get_previous(self)

        # If there is no previous round, then raise an error.
        if previous_round is None:
            raise ElectionRaceError()

        previous_round_votes = previous_round.get_round_votes()
        if previous_round_votes[candidate_a] > previous_round_votes[candidate_b]:
            return candidate_a
        elif previous_round_votes[candidate_a] < previous_round_votes[candidate_b]:
            return candidate_b
        elif previous_round_votes[candidate_a] == previous_round_votes[candidate_b]:
            return previous_round.get_previous_round_lowest(candidate_a, candidate_b)

    def tabulate(self):
        # Check for winners.
        previous_winners = self.parent.get_winners()
        remaining_spots = self.parent.get_max_winners() - len(previous_winners)

        round_votes = self.get_round_votes()
        ballot_results = self.get_round_ballots()
        running_candidates = self.get_running_candidates()

        # If running candidates remaining equals the number of remaining spots,
        # immediately elect them all.
        if len(running_candidates) <= remaining_spots:
            for candidate in running_candidates:
                self.candidates_tabulation[candidate] = ElectionCandidateState(candidate, ElectionCandidateState.WON)
            self.state = self.COMPLETE
            return

        winning_candidates = []
        for candidate in running_candidates:
            if round_votes[candidate] >= self.parent.get_droop_quota():
                winning_candidates.append(candidate)

        # Automatically eliminate candidates that are still running but received zero votes.
        for candidate in running_candidates:
            if round_votes[candidate] == 0:
                self.candidates_tabulation[candidate] = ElectionCandidateState(candidate,
                                                                               ElectionCandidateState.ELIMINATED)
                running_candidates.remove(candidate)

        # If there are no winning candidates, this becomes a elimination round.
        if not winning_candidates:
            lowest_candidate_score = round_votes[running_candidates[0]]
            lowest_candidates = [running_candidates[0]]

            for candidate in running_candidates:
                if round_votes[candidate] < lowest_candidate_score:
                    lowest_candidate_score = round_votes[candidate]
                    lowest_candidates = [candidate]
                elif round_votes[candidate] == lowest_candidate_score:
                    lowest_candidates.append(candidate)

            for candidate in lowest_candidates:
                self.candidates_tabulation[candidate] = ElectionCandidateState(candidate,
                                                                               ElectionCandidateState.ELIMINATED)
            self.state = self.COMPLETE
            return

        # Sort winning candidates by descending order of votes.
        winning_candidates = sorted(winning_candidates, key=lambda winning_candidate: round_votes[winning_candidate])

        # Check to see if there are enough spots to add all the winners
        if len(winning_candidates) > remaining_spots:
            # Remove individuals not in the top X number of spots
            # where X is the number of remaining spots.
            winning_candidates = winning_candidates[:remaining_spots]
            # TODO: Resolve issue where there may be "winning" candidates at the end with the same score

        for candidate in winning_candidates:
            self.candidates_tabulation[candidate] = ElectionCandidateState(candidate, ElectionCandidateState.WON)
            surplus = round_votes[candidate] - self.parent.get_droop_quota()
            transfer_value = surplus / round_votes[candidate]
            for ballot in ballot_results:
                if ballot.get_candidate() == candidate:
                    ballot_voter = ballot.get_voter()
                    ballot_voter.race_set_voter_value(self.parent, self, ballot.get_value() * transfer_value)

        self.state = self.COMPLETE

    def winners_get(self):
        winning_candidates = []
        for candidate in self.candidates:
            if self.candidate_state_get(candidate).get_state() == ElectionCandidateState.WON:
                winning_candidates.append(candidate)
        return winning_candidates
