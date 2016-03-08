from ElectionCandidateState import ElectionCandidateState
from ElectionRaceRound import ElectionRaceRound
from ElectionRaceError import ElectionRaceError


class ElectionRace:
    (ADDING, TABULATING, COMPLETE) = range(3)

    def __init__(self, election_id, election_position, election_max_winners, election_extended_data):
        self._id = election_id
        self._position = election_position
        self._max_winners = election_max_winners
        self._extended_data = election_extended_data
        self._state = self.ADDING

        self._voters = []
        self._rounds = []
        self._winners = []
        self._candidates = []
        self._transfer_voters = []

        # Candidate and candidate ID relationship.
        self._candidate_id = {}

    def id(self):
        return str(self._id)

    def position(self):
        return str(self._position)

    def extended_data(self):
        return self._extended_data

    def candidates(self):
        return self._candidates

    def winners(self):
        return self._winners

    def state(self):
        return self._state

    def rounds(self):
        return self._rounds

    def max_winners(self):
        return self._max_winners

    def droop_quota(self):
        if self._max_winners > 1:
            return int((float(len(self._voters)) / (self._max_winners + 1)) + 1)
        elif self._max_winners == 1:
            return int(float(len(self._voters) + 1) / 2)

    def add_voter(self, voter):
        if self._state is not self.ADDING:
            raise ElectionRaceError("Election voter adding phase has completed.")

        # Ignore voters that are already added.
        if voter in self._voters:
            return

        self._voters.append(voter)

    def add_candidate(self, candidate):
        if self._state is not self.ADDING:
            raise ElectionRaceError("Election candidate adding phase has completed.")

        if candidate in self._candidates:
            raise ElectionRaceError("Candidate is already part of this race.")

        self._candidate_id[candidate.id()] = candidate
        self._candidates.append(candidate)

    def get_candidate(self, candidate_id):
        if candidate_id not in self._candidate_id:
            return None

        return self._candidate_id[candidate_id]

    def get_round_latest(self):
        if not self._rounds:
            return None

        return self._rounds[-1]

    def get_round_previous(self, election_round):
        current_round_index = self._rounds.index(election_round)
        if current_round_index == 0:
            return None
        return self._rounds[current_round_index - 1]

    def run(self):
        if self._state is self.COMPLETE:
            return

        self._state = self.TABULATING

        current_round = self.get_round_latest()

        # If the current round does not exist, this race just began
        # so create a new round.
        if current_round is None:
            new_round = ElectionRaceRound(self, 1)
            # Add candidates to round.
            for candidate in self._candidates:
                new_round.add_candidate(candidate,
                                        ElectionCandidateState(new_round, candidate, ElectionCandidateState.RUNNING))
            self._rounds.append(new_round)
            self._transfer_voters = self._voters[:]
            return

        # If there are voters to cast their ballots for the current
        # round of the race, take the first voter in the list
        # and cast their ballot.
        if self._transfer_voters:
            transfer_voter = self._transfer_voters.pop(0)
            current_round.add_ballot(transfer_voter.get_race_voter_ballot(self, current_round,
                                                                          current_round.get_candidates_by_state(
                                                                              ElectionRaceRound.CANDIDATE_PRE_STATE)[
                                                                              ElectionCandidateState.RUNNING]))
            return

        # There are no more voters to cast their ballots in the round,
        # so it's time to tabulate the round results.

        # Ensure that the candidate scores when doing this have NOT
        # been cached just in case a stale cache state is somehow
        # not properly recorded.
        current_round_scores = current_round.get_candidates_score()
        current_round_winners = []

        running_candidates = current_round.get_candidates_by_state(ElectionRaceRound.CANDIDATE_PRE_STATE)[
            ElectionCandidateState.RUNNING]

        # Calculate the maximum number of winners that can be taken this round.
        max_round_winners = self._max_winners - len(self._winners)

        # Check if the number of running candidates is less than or equal to the number of maximum
        # round winners.
        if len(running_candidates) <= max_round_winners:
            # Add all the candidates that are still running to the winning candidates list.
            for candidate in running_candidates:
                current_round_winners.append(candidate)
        else:
            # Check for a candidate that has managed to meet the droop quota.
            for candidate in sorted(current_round_scores, key=current_round_scores.get, reverse=True):
                if candidate in running_candidates and current_round_scores[candidate] >= self.droop_quota():
                    current_round_winners.append(candidate)

        # Check if current round winners is greater than available spots.
        while len(current_round_winners) > max_round_winners:
            # Check the last couple of round winners.
            if current_round_scores[current_round_winners[-1]] != current_round_scores[current_round_winners[-2]]:
                # The two scores are not the same, so remove
                # the lowest of the two candidates.
                del current_round_winners[-1]
            else:
                # Check the last round winners to see how many of them have
                # the same lowest score.
                lowest_winner_score = current_round_scores[current_round_winners[-1]]
                lowest_winners = []

                for candidate in current_round_winners:
                    if current_round_scores[candidate] == lowest_winner_score:
                        lowest_winners.append(candidate)

                # Order the lowest winners by their score in previous round.
                previous_round = self.get_round_previous(current_round)
                while len(current_round_winners) > max_round_winners:
                    previous_round_scores = previous_round.get_candidates_score()
                    previous_round_lowest_winners = sorted(lowest_winners,
                                                           key=lambda sort_candidate: previous_round_scores[
                                                               sort_candidate], reverse=True)

                    if previous_round_scores[previous_round_lowest_winners[-1]] != previous_round_scores[
                        previous_round_lowest_winners[-2]]:
                        current_round_winners.remove(previous_round_lowest_winners[-1])
                        lowest_winners.remove(previous_round_lowest_winners[-1])
                    else:
                        previous_round = self.get_round_previous(previous_round)
                        if previous_round is None:
                            raise ElectionRaceError(
                                "Unable to resolve tie in round winners, candidates tied the entire race.")

        # Set winners in round.
        for candidate in current_round_winners:
            current_round.set_candidate_state(candidate,
                                              ElectionCandidateState(current_round, candidate,
                                                                     ElectionCandidateState.WON))
            candidate_voters = current_round.get_candidate_voters(candidate)
            candidate_ballots = current_round.get_candidate_ballots(candidate)

            # Check if the candidate was added because the candidate met the droop quota
            # or if the candidate was added because the number of candidates running
            # was less than or equal to the max number of winners.
            candidate_score = current_round_scores[candidate]
            surplus = candidate_score - self.droop_quota()
            transfer_value = 1
            if surplus > 0:
                transfer_value = float(surplus) / candidate_score

            # Set transfer value for each voter.
            for ballot in candidate_ballots:
                ballot.voter().set_race_voter_value(self, current_round, ballot.value() * transfer_value)

            self._transfer_voters.extend(candidate_voters)
            self._winners.append(candidate)

        # Check to see if there were any winners in the round.
        if current_round_winners:
            # Check if the number of race winners has been reached.
            # If so, the race is complete.
            if len(self._winners) == self._max_winners:
                # Eliminate any remaining candidates.
                for candidate in current_round.get_candidates_by_state()[ElectionCandidateState.RUNNING]:
                    current_round.set_candidate_state(candidate, ElectionCandidateState(current_round, candidate,
                                                      ElectionCandidateState.ELIMINATED))

                # End the current round.
                current_round.complete()

                # Set the current state of the race to be complete.
                self._state = self.COMPLETE
                return

            # Complete the current round.
            current_round.complete()

            # Get candidates that changed states in this round.
            current_round_changed = current_round.get_candidates_changed()

            # Create a new round and add the candidates in.
            new_round = ElectionRaceRound(self, current_round.round() + 1)
            for candidate in self._candidates:
                new_round.add_candidate(candidate, current_round.get_candidate_state(candidate))

            # Add ballots for candidates that have NOT changed.
            for candidate in self._candidates:
                # Candidate changed, ignore ballots.
                if candidate in current_round_changed:
                    continue

                transferable_ballots = current_round.get_candidate_ballots(candidate)
                for ballot in transferable_ballots:
                    new_round.add_ballot(ballot)

            # Transfer none ballots.
            transferable_ballots = current_round.get_candidate_ballots(None)
            for ballot in transferable_ballots:
                new_round.add_ballot(ballot)

            # Append the new round to the list of rounds.
            self._rounds.append(new_round)
            return

        # There were no round winners, now remove running candidates with a
        # zero score in the round and the running candidates with the lowest
        # non-zero score.
        eliminated_candidates = []
        for candidate in running_candidates:
            if current_round_scores[candidate] == 0:
                eliminated_candidates.append(candidate)

        # Find the lowest candidates with lowest candidate score.
        lowest_candidates = [running_candidates[0]]

        for candidate in running_candidates:
            if current_round_scores[candidate] < current_round_scores[lowest_candidates[0]]:
                lowest_candidates = [candidate]
            elif current_round_scores[candidate] == current_round_scores[
                lowest_candidates[0]] and candidate not in lowest_candidates:
                lowest_candidates.append(candidate)

        eliminated_candidates.extend(lowest_candidates)

        # Eliminate candidates.
        for candidate in eliminated_candidates:
            current_round.set_candidate_state(candidate, ElectionCandidateState(current_round, candidate,
                                                                                ElectionCandidateState.ELIMINATED))
            self._transfer_voters.extend(current_round.get_candidate_voters(candidate))

        # Complete the current round.
        current_round.complete()

        # Get any candidates that changed states in this round.
        current_round_changed = current_round.get_candidates_changed()

        # Create a new round and add the candidates in.
        new_round = ElectionRaceRound(self, current_round.round() + 1)
        for candidate in self._candidates:
            new_round.add_candidate(candidate, current_round.get_candidate_state(candidate))

        # Add ballots for candidates that have NOT changed.
        for candidate in self._candidates:
            # Candidate changed, ignore ballots.
            if candidate in current_round_changed:
                continue

            transferable_ballots = current_round.get_candidate_ballots(candidate)
            for ballot in transferable_ballots:
                new_round.add_ballot(ballot)

        # Transfer none ballots.
        transferable_ballots = current_round.get_candidate_ballots(None)
        for ballot in transferable_ballots:
            new_round.add_ballot(ballot)

        # Append the new round to the list of rounds.
        self._rounds.append(new_round)
        return

    def __str__(self):
        return str(self._position)

    def __repr__(self):
        return str(self._position)
