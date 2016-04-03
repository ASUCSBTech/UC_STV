from ElectionCandidateState import ElectionCandidateState
from ElectionRaceError import ElectionRaceError


class ElectionRaceRound:
    (INCOMPLETE, COMPLETE) = range(2)
    (CANDIDATE_PRE_STATE, CANDIDATE_POST_STATE) = range(2)
    (CACHE_STALE, CACHE_OK) = range(2)

    def __init__(self, election_parent, election_round):
        self._round = election_round
        self._parent = election_parent
        self._voters = []
        self._ballots = []
        self._candidates = []

        # Voter ballot relationship.
        self._voter_ballot = {}

        # Candidate ballot relationship.
        self._candidate_ballot = {None: []}

        # Candidate score relationship.
        self._candidate_score = {None: 0}

        # Candidate states before and after tabulation.
        self._candidate_pre_state = {}
        self._candidate_post_state = {}

        # Candidates pre-state cache.
        self._cache_candidate_pre_state = self.CACHE_STALE
        self._cache_candidate_pre = None

        # Candidates post-state cache.
        self._cache_candidate_post_state = self.CACHE_STALE
        self._cache_candidate_post = None

        self._state = self.INCOMPLETE

    def round(self):
        return self._round

    def parent(self):
        return self._parent

    def voters(self):
        return self._voters

    def ballots(self):
        return self._ballots

    def candidates(self):
        return self._candidates

    def state(self):
        return self._state

    def add_ballot(self, ballot):
        # The round can only be modified prior to completion.
        if self._state is self.COMPLETE:
            raise ElectionRaceError("Election round is already complete.")

        if ballot.voter() in self._voters:
            raise ElectionRaceError("Ballot already exists for voter.")

        if ballot.candidate() is not None and ballot.candidate() not in self._candidates:
            raise ElectionRaceError("Candidate is not a valid candidate for election round.")

        self._voters.append(ballot.voter())
        self._ballots.append(ballot)
        self._voter_ballot[ballot.voter()] = ballot
        self._candidate_ballot[ballot.candidate()].append(ballot)
        self._candidate_score[ballot.candidate()] += ballot.value()

    def add_candidate(self, candidate, state):
        # The round can only be modified prior to completion.
        if self._state is self.COMPLETE:
            raise ElectionRaceError("Election round is already complete.")

        if candidate in self._candidates:
            raise ElectionRaceError("Candidate already added to election round.")

        self._candidates.append(candidate)
        self._candidate_ballot[candidate] = []
        self._candidate_score[candidate] = 0
        self._set_candidate_state(candidate, state, state_type=self.CANDIDATE_PRE_STATE)

    def set_candidate_state(self, candidate, state):
        # The round can only be modified prior to completion.
        if self._state is self.COMPLETE:
            raise ElectionRaceError("Election round is already complete.")

        self._set_candidate_state(candidate, state, self.CANDIDATE_POST_STATE)

    def _set_candidate_state(self, candidate, state, state_type=None):
        # The round can only be modified prior to completion.
        if self._state is self.COMPLETE:
            raise ElectionRaceError("Election round is already complete.")

        # The default state type is post state.
        if state_type is None:
            state_type = self.CANDIDATE_POST_STATE

        if state_type is self.CANDIDATE_PRE_STATE:
            self._candidate_pre_state[candidate] = state
            self._cache_candidate_pre_state = self.CACHE_STALE
        elif state_type is self.CANDIDATE_POST_STATE:
            self._candidate_post_state[candidate] = state
            self._cache_candidate_post_state = self.CACHE_STALE
        else:
            raise TypeError("State type must be either CANDIDATE_PRE_STATE or CANDIDATE_POST_STATE.")

    def get_candidate_state(self, candidate, state_type=None):
        # Check that the candidate is in the round.
        if candidate not in self._candidates:
            raise ElectionRaceError("Candidate is not participating in this race.")

        # The default state type is post state.
        if state_type is None:
            state_type = self.CANDIDATE_POST_STATE

        if state_type is self.CANDIDATE_PRE_STATE:
            return self._candidate_pre_state[candidate]
        elif state_type is self.CANDIDATE_POST_STATE:
            # Post state is an override of the candidate pre-state,
            # if the candidate has no overridden state, then the
            # pre-state is returned.
            if candidate not in self._candidate_post_state:
                return self._candidate_pre_state[candidate]

            return self._candidate_post_state[candidate]
        else:
            raise TypeError("State type must be either CANDIDATE_PRE_STATE or CANDIDATE_POST_STATE.")

    def get_candidates_state(self, state_type=None):
        if state_type is None:
            state_type = self.CANDIDATE_POST_STATE

        candidates_state = {}
        for candidate in self._candidates:
            candidates_state[candidate] = self.get_candidate_state(candidate, state_type)

        return candidates_state

    # Gets candidates grouped by the state of each candidate.
    def get_candidates_by_state(self, state_type=None, use_cache=True):
        if state_type is None:
            state_type = self.CANDIDATE_POST_STATE

        if use_cache and (state_type is self.CANDIDATE_PRE_STATE) and \
                (self._cache_candidate_pre_state is not self.CACHE_STALE) and \
                (self._cache_candidate_pre is not None):
            return self._cache_candidate_pre

        if use_cache and (state_type is self.CANDIDATE_POST_STATE) and \
                (self._cache_candidate_post_state is not self.CACHE_STALE) and \
                (self._cache_candidate_post is not None):
            return self._cache_candidate_post

        candidate_group_states = {ElectionCandidateState.RUNNING: [], ElectionCandidateState.WON: [],
                                  ElectionCandidateState.ELIMINATED: []}

        for candidate in self._candidates:
            candidate_group_states[self.get_candidate_state(candidate, state_type).state()].append(candidate)

        if state_type is self.CANDIDATE_PRE_STATE:
            self._cache_candidate_pre = candidate_group_states
            self._cache_candidate_pre_state = self.CACHE_OK
        elif state_type is self.CANDIDATE_POST_STATE:
            self._cache_candidate_post = candidate_group_states
            self._cache_candidate_post_state = self.CACHE_OK

        return candidate_group_states

    # Gets candidate that have had their state changed.
    def get_candidates_changed(self):
        candidates = []

        for candidate in self._candidate_post_state:
            candidates.append(candidate)

        return candidates

    def get_candidate_score(self, candidate):
        if candidate is not None and candidate not in self._candidates:
            raise LookupError("Unable to locate candidate.")

        return self._candidate_score[candidate]

    def get_candidates_score(self):

        candidate_scores = {}

        for candidate in self._candidates:
            candidate_scores[candidate] = self.get_candidate_score(candidate)

        # Also include the number of votes that have been exhausted.
        candidate_scores[None] = self.get_candidate_score(None)

        return candidate_scores

    def get_candidate_voters(self, candidate):
        if candidate is not None and candidate not in self._candidates:
            raise LookupError("Unable to locate candidate.")

        voters = []

        for ballot in self.get_candidate_ballots(candidate):
            voters.append(ballot.voter())

        return voters

    def get_candidate_ballots(self, candidate):
        if candidate is not None and candidate not in self._candidates:
            raise LookupError("Unable to locate candidate.")

        return self._candidate_ballot[candidate]

    def complete(self):
        # The state is set to complete once the round is
        # considered done; this locks all changes allowed
        # to the round's data.
        self._state = self.COMPLETE

    def __str__(self):
        return str(self._round)

    def __repr__(self):
        return str(self._round)