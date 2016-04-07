import logging
from backend.ElectionRaceVoterBallot import ElectionRaceVoterBallot


class ElectionVoter:
    def __init__(self, id):
        self._id = id
        self._races = []
        self._race_preferences = {}
        self._race_value = {}
        self.logger = logging.getLogger("application.election.voter")

    def add_race(self, election_race):
        self._races.append(election_race)
        self._race_value[election_race] = []

    def get_race_participating(self, election_race):
        return election_race in self._races

    def set_race_preferences(self, election_race, election_candidates):
        self._race_preferences[election_race] = election_candidates

    def get_race_voter_ballot(self, election_race, election_round, election_candidates):
        ballot_candidate = self._get_voter_preference(election_race, election_candidates)

        ballot_value = self.get_race_voter_value(election_race, election_round)
        if ballot_value is None:
            ballot_value = 1

        self.logger.debug("(Race: %s, Round: %s, Voter: %s) Generating ballot.", election_race, election_round, self)

        return ElectionRaceVoterBallot(election_race, self, ballot_candidate, ballot_value)

    def set_race_voter_value(self, election_race, election_round, voter_value):
        if not self.get_race_participating(election_race):
            raise LookupError("Voter not participating in race.")

        new_value = {
            "value": voter_value,
            "round": election_round
        }

        self._race_value[election_race].append(new_value)

    def get_race_voter_value(self, election_race, election_round):
        # Attempt to find the last value assigned to the race
        # prior to the round given.
        for value in reversed(self._race_value[election_race]):
            if value["round"].round() < election_round.round():
                return value["value"]
        return None

    def _get_voter_preference(self, race, candidates):
        return next((preferred_candidate for preferred_candidate in self._race_preferences[race] if preferred_candidate in candidates), None)

    def __str__(self):
        return str(self._id)

    def __repr__(self):
        return str(self._id)
