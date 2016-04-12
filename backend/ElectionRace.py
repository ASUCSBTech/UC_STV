import logging
import math
import sys

import terminaltables

from backend.ElectionCandidateState import ElectionCandidateState
from backend.ElectionRaceError import ElectionRaceError
from backend.ElectionRaceRound import ElectionRaceRound


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

        self.logger = logging.getLogger("election")

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
            return_value =  int((float(len(self._voters)) / (self._max_winners + 1)) + 1)
        elif self._max_winners == 1:
            return_value = int(float(len(self._voters) + 1) / 2)

        return return_value if return_value > 0 else 1

    def add_voter(self, voter):
        if self._state is not self.ADDING:
            raise ElectionRaceError("(Race: %s) Election voter adding phase has completed." % self)

        # Ignore voters that are already added.
        if voter in self._voters:
            return

        self._voters.append(voter)

    def add_candidate(self, candidate):
        if self._state is not self.ADDING:
            raise ElectionRaceError("(Race: %s) Election candidate adding phase has completed." % self)

        if candidate in self._candidates:
            raise ElectionRaceError("(Race: %s) Candidate is already part of this race." % self)

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

    @staticmethod
    def get_data_table(election_round):
        _candidate_states = {
            ElectionCandidateState.WON: "WON",
            ElectionCandidateState.RUNNING: "RUNNING",
            ElectionCandidateState.ELIMINATED: "ELIMINATED"
        }

        table_data = []

        def round_down(value, places):
            return math.floor(value * (10 ** places)) / float(10 ** places)

        if election_round.state() is ElectionRaceRound.INCOMPLETE:
            candidate_states = election_round.get_candidates_state(ElectionRaceRound.CANDIDATE_PRE_STATE)
            candidate_state_groups = election_round.get_candidates_by_state(ElectionRaceRound.CANDIDATE_PRE_STATE)
        else:
            candidate_states = election_round.get_candidates_state(ElectionRaceRound.CANDIDATE_POST_STATE)
            candidate_state_groups = election_round.get_candidates_by_state(ElectionRaceRound.CANDIDATE_POST_STATE)

        candidate_scores = election_round.get_candidates_score()

        droop_quota = election_round.parent().droop_quota()

        score_resolution = 4

        table_group_won = sorted(candidate_state_groups[ElectionCandidateState.WON], key=lambda sort_candidate: (-1 * (election_round.round() - candidate_states[sort_candidate].round().round()), -1 * (candidate_states[sort_candidate].round().get_candidate_score(sort_candidate)), sort_candidate.party(), sort_candidate.name()))
        for _candidate in table_group_won:
            _candidate_score = candidate_states[_candidate].round().get_candidate_score(_candidate)
            table_data.append([
                _candidate.name(),
                _candidate.party(),
                _candidate_states[ElectionCandidateState.WON],
                str(droop_quota) + " (" + str(round_down(_candidate_score, score_resolution)) + ")",
                str(_candidate_score / droop_quota)
            ])

        table_group_running = sorted(candidate_state_groups[ElectionCandidateState.RUNNING], key=lambda sort_candidate: (-1 * candidate_scores[sort_candidate], sort_candidate.party(), sort_candidate.name()))
        for _candidate in table_group_running:
            _candidate_score = candidate_scores[_candidate]
            table_data.append([
                _candidate.name(),
                _candidate.party(),
                _candidate_states[ElectionCandidateState.RUNNING],
                str(round_down(_candidate_score, score_resolution)),
                str(_candidate_score / droop_quota)
            ])

        table_group_eliminated = sorted(candidate_state_groups[ElectionCandidateState.ELIMINATED], key=lambda sort_candidate: (-1 * (candidate_states[sort_candidate].round().round()), -1 * (candidate_states[sort_candidate].round().get_candidate_score(sort_candidate)), sort_candidate.party(), sort_candidate.name()))
        for _candidate in table_group_eliminated:
            _candidate_score = candidate_states[_candidate].round().get_candidate_score(_candidate)
            table_data.append([
                _candidate.name(),
                _candidate.party(),
                _candidate_states[ElectionCandidateState.ELIMINATED],
                "0 (" + str(round_down(_candidate_score, score_resolution)) + ")",
                "0"
            ])

        return table_data

    def run(self):
        # Reusable run components.
        def create_new_round():
            # Get candidates that changed states in this round.
            current_round_changed = current_round.get_candidates_changed()

            # Create a new round and add the candidates in.
            self.logger.info("(Race: %s) Previous round completed, creating new round.", self)
            _new_round = ElectionRaceRound(self, current_round.round() + 1)
            for _candidate in self._candidates:
                self.logger.info("(Race: %s, Round: %s) Adding candidate `%s` to the new round. (New Round: %s)", self, current_round, _candidate, _new_round)
                _new_round.add_candidate(_candidate, current_round.get_candidate_state(_candidate))

            # Add ballots for candidates that have NOT changed.
            for _candidate in self._candidates:
                # Candidate changed, ignore ballots.
                if _candidate in current_round_changed:
                    continue

                transferable_ballots = current_round.get_candidate_ballots(_candidate)
                self.logger.info("(Race: %s, Round: %s) Transferring %d reusable ballots from candidate `%s` to new round. (New Round: %s)", self, current_round, len(transferable_ballots), _candidate, _new_round)
                for _ballot in transferable_ballots:
                    _new_round.add_ballot(_ballot)

            # Transfer none ballots.
            transferable_ballots = current_round.get_candidate_ballots(None)
            self.logger.info("(Race: %s, Round: %s) Transferring %d depleted ballots to new round. (New Round: %s)", self, current_round, len(transferable_ballots), _new_round)
            for _ballot in transferable_ballots:
                _new_round.add_ballot(_ballot)

            # Append the new round to the list of rounds.
            self._rounds.append(_new_round)

        def complete_current_round():
            current_round.complete()

            if not self.logger.isEnabledFor(logging.INFO):
                # Complete the current round.
                self.logger.info("(Race: %s, Round: %s) Round has completed.", self, current_round)
            else:
                try:
                    table_data = self.get_data_table(current_round)
                    table_data[:0] = [[
                        "Candidate",
                        "Party",
                        "Status",
                        "Score",
                        "Quota Percentage"
                    ]]

                    table = terminaltables.DoubleTable(table_data, title=" Final Round Results ")
                    table.inner_row_border = True
                    self.logger.info("(Race: %s, Round: %s) Round has completed.\n%s\nCandidates Affected: %s", self, current_round, table.table, ", ".join(map(str, current_round.get_candidates_changed())))
                except Exception as e:
                    self.logger.error(e, exc_info=sys.exc_info())

        if self._state is self.COMPLETE:
            return

        self._state = self.TABULATING

        current_round = self.get_round_latest()

        # If the current round does not exist, this race just began
        # so create a new round.
        if current_round is None:
            self.logger.info("(Race: %s) Latest round not found, creating new round.", self)
            new_round = ElectionRaceRound(self, 1)
            # Add candidates to round.
            for candidate in self._candidates:
                self.logger.info("(Race: %s, Round: %s) Adding candidate `%s` to the round.", self, new_round, candidate)
                new_round.add_candidate(candidate, ElectionCandidateState(new_round, candidate, ElectionCandidateState.RUNNING))
            self._rounds.append(new_round)
            self._transfer_voters = self._voters[:]
            return

        # Check if the round is complete, if it is, then create a new round.
        if current_round.state() == ElectionRaceRound.COMPLETE:
            create_new_round()
            return

        # If there are voters to cast their ballots for the current
        # round of the race, take the first voter in the list
        # and cast their ballot.
        if self._transfer_voters:
            transfer_voter = self._transfer_voters.pop(0)
            self.logger.info("(Race: %s, Round: %s) Adding voter `%s` ballot into the round. (Remaining Voters: %d)", self, current_round, transfer_voter, len(self._transfer_voters))
            current_round.add_ballot(transfer_voter.get_race_voter_ballot(self, current_round, current_round.get_candidates_by_state(ElectionRaceRound.CANDIDATE_PRE_STATE)[ElectionCandidateState.RUNNING]))
            return

        # There are no more voters to cast their ballots in the round,
        # so it's time to tabulate the round results.

        # Ensure that the candidate scores when doing this have NOT
        # been cached just in case a stale cache state is somehow
        # not properly recorded.
        current_round_scores = current_round.get_candidates_score()
        current_round_winners = []

        running_candidates = current_round.get_candidates_by_state(ElectionRaceRound.CANDIDATE_PRE_STATE)[ElectionCandidateState.RUNNING]

        # Check if there are any remaining candidates that are still running.
        if len(running_candidates) == 0:
            self.logger.info("(Race: %s) Race has completed, no candidates remaining in race. (Total Rounds: %d)", self, len(self._rounds))
            self._state = self.COMPLETE

        # Check a special condition of no voters being in this race.
        if len(self._voters) == 0:
            current_round.complete()
            self.logger.info("(Race: %s) Race has completed, no votes were cast in the race.", self)
            self._state = self.COMPLETE

        # Calculate the maximum number of winners that can be taken this round.
        max_round_winners = self._max_winners - len(self._winners)

        # Check if the number of running candidates is less than or equal to the number of maximum
        # round winners.
        if len(running_candidates) <= max_round_winners:
            self.logger.info("(Race: %s, Round: %s) Total number of remaining running candidates is less than or equal to remaining spots.", self, current_round)
            # Add all the candidates that are still running to the winning candidates list.
            for candidate in running_candidates:
                current_round_winners.append(candidate)
        else:
            # Check for a candidate that has managed to meet the droop quota.
            for candidate in sorted(current_round_scores, key=current_round_scores.get, reverse=True):
                if candidate in running_candidates and current_round_scores[candidate] >= self.droop_quota():
                    self.logger.info("(Race: %s, Round: %s) Candidate `%s` has met the droop quota of %d.", self, current_round, candidate, self.droop_quota())
                    current_round_winners.append(candidate)

        # Check if current round winners is greater than available spots.
        while len(current_round_winners) > max_round_winners:
            self.logger.info("(Race: %s, Round: %s) Number of possible winners exceeds %d available spots.", self, current_round, max_round_winners)
            # Check the last couple of round winners.
            if current_round_scores[current_round_winners[-1]] != current_round_scores[current_round_winners[-2]]:
                # The two scores are not the same, so remove
                # the lowest of the two candidates.
                self.logger.info("(Race: %s, Round: %s) Candidate `%s` had less votes than candidate `%s` and has been removed from the list of possible winners.", self, current_round, current_round_winners[-1], current_round_winners[-2])
                del current_round_winners[-1]
            else:
                self.logger.info("(Race: %s, Round: %s) Finding candidates in the list of potential winners that have the lowest score.", self, current_round)
                # Check the last round winners to see how many of them have
                # the same lowest score.
                lowest_winner_score = current_round_scores[current_round_winners[-1]]
                lowest_winners = []

                for candidate in current_round_winners:
                    if current_round_scores[candidate] == lowest_winner_score:
                        lowest_winners.append(candidate)

                self.logger.info("(Race: %s, Round: %s) Found %d candidates within the list of potential winners that had the lowest score of %d.", self, current_round, len(lowest_winners), lowest_winner_score)

                # Order the lowest winners by their score in previous round.
                previous_round = self.get_round_previous(current_round)
                if previous_round is None:
                    self.logger.critical("(Race: %s, Round: %s) Candidates are tied and there are no previous rounds available to compare. Unable to continue.", self, current_round)
                    raise ElectionRaceError("Unable to resolve tie in round winners, candidates tied the entire race.")

                while len(current_round_winners) > max_round_winners:
                    self.logger.info("(Race: %s, Round: %s) Comparing candidate scores from previous round. (Previous Round: %s)", self, current_round, previous_round)
                    previous_round_scores = previous_round.get_candidates_score()
                    previous_round_lowest_winners = sorted(lowest_winners, key=lambda sort_candidate: previous_round_scores[sort_candidate], reverse=True)

                    if previous_round_scores[previous_round_lowest_winners[-1]] != previous_round_scores[previous_round_lowest_winners[-2]]:
                        self.logger.info("(Race: %s, Round: %s) Candidate `%s` had less votes than candidate `%s` in the previous round and has been removed from the list of potential winners.", self, current_round, previous_round_lowest_winners[-1], previous_round_lowest_winners[-2])
                        current_round_winners.remove(previous_round_lowest_winners[-1])
                        lowest_winners.remove(previous_round_lowest_winners[-1])
                    else:
                        previous_round = self.get_round_previous(previous_round)
                        self.logger.info("(Race: %s, Round: %s) Candidates are still tied, moving to previous round.", self)
                        if previous_round is None:
                            self.logger.critical("(Race: %s, Round: %s) Candidates are still tied and has exhausted available rounds to compare. Unable to continue.", self, current_round)
                            raise ElectionRaceError("Unable to resolve tie in round winners, candidates tied the entire race.")

        # Set winners in round.
        for candidate in current_round_winners:
            self.logger.info("(Race: %s, Round: %s) Candidate `%s` has been elected with a score of %f.", self, current_round, candidate, current_round_scores[candidate])
            current_round.set_candidate_state(candidate, ElectionCandidateState(current_round, candidate, ElectionCandidateState.WON))
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
            else:
                surplus = 0

            self.logger.info("(Race: %s, Round: %s) Candidate `%s`'s vote transfer value is %f. (Surplus: %f)", self, current_round, candidate, transfer_value, surplus)

            # Set transfer value for each voter.
            for ballot in candidate_ballots:
                ballot.voter().set_race_voter_value(self, current_round, ballot.value() * transfer_value)

            self._transfer_voters.extend(candidate_voters)
            self._winners.append(candidate)

        # Check to see if there were any winners in the round.
        if current_round_winners:
            # Check if the number of race winners has been reached.
            # If so, eliminate the remaining candidates.
            if len(self._winners) == self._max_winners:
                # Eliminate any remaining candidates.
                eliminate_candidates = current_round.get_candidates_by_state()[ElectionCandidateState.RUNNING]
                self.logger.info("(Race: %s, Round: %s) Max number of winners elected, eliminating remaining candidates. (Remaining Candidates: %d)", self, current_round, len(eliminate_candidates))
                for candidate in eliminate_candidates:
                    self.logger.info("(Race: %s, Round: %s) Eliminating candidate `%s`.", self, current_round, candidate)
                    current_round.set_candidate_state(candidate, ElectionCandidateState(current_round, candidate, ElectionCandidateState.ELIMINATED))

            complete_current_round()

            # Check to see if the race still has candidates that are running.
            if len(current_round.get_candidates_by_state()[ElectionCandidateState.RUNNING]) == 0:
                # Set the current state of the race to be complete.
                self.logger.info("(Race: %s) Race completed with %d winner(s). (Total Rounds: %d)", self, len(self._winners), len(self._rounds))
                self._state = self.COMPLETE

            return

        # There were no round winners, now remove running candidates with a
        # zero score in the round and the running candidates with the lowest
        # non-zero score.
        eliminated_candidates = []
        for candidate in running_candidates:
            if current_round_scores[candidate] == 0:
                eliminated_candidates.append(candidate)

        lowest_candidates = []

        # Find a candidate that is not already eliminated.
        for candidate in running_candidates:
            if candidate not in eliminated_candidates:
                lowest_candidates = [candidate]
                break

        # Find the lowest candidates with lowest candidate score.
        for candidate in running_candidates:
            if current_round_scores[candidate] < current_round_scores[lowest_candidates[0]]:
                lowest_candidates = [candidate]
            elif current_round_scores[candidate] == current_round_scores[lowest_candidates[0]] and candidate not in lowest_candidates:
                lowest_candidates.append(candidate)

        eliminated_candidates.extend(lowest_candidates)

        # Eliminate candidates.
        for candidate in eliminated_candidates:
            self.logger.info("(Race: %s, Round: %s) Eliminating candidate `%s`.", self, current_round, candidate)
            current_round.set_candidate_state(candidate, ElectionCandidateState(current_round, candidate, ElectionCandidateState.ELIMINATED))

            # Transfer voters that were part of that candidate.
            self._transfer_voters.extend(current_round.get_candidate_voters(candidate))

        complete_current_round()
        return

    def __str__(self):
        return str(self._position)

    def __repr__(self):
        return str(self._position)
