from ElectionRaceVoterBallot import ElectionRaceVoterBallot

class ElectionVoter:
    def __init__(self, id):
        self.id = id
        self.races = {}
        self.race_preferences = {}
        self.race_value = {}

    def race_add(self, race):
        self.races[str(race.get_id())] = race
        self.race_value[race] = []

    def race_participating(self, race):
        return str(race.get_id()) in self.races

    def race_preferences_set(self, race, candidates):
        self.race_preferences[race] = candidates

    def race_get_voter_preference(self, race, candidates):
        # Return the preferred candidate.
        for preferred_candidate in self.race_preferences[race]:
            if preferred_candidate in candidates:
                return preferred_candidate

        # Exhausted voter's candidate selection, no candidate choice available.
        return None

    def race_get_voter_round_ballot(self, race, round, candidates):
        ballot_candidate = self.race_get_voter_preference(race, candidates)
        ballot_value = self.race_get_voter_value(race, round)
        if ballot_value is None:
            ballot_value = 1
        return ElectionRaceVoterBallot(self, ballot_candidate, ballot_value)

    def race_set_voter_value(self, race, round, value):
        if not self.race_participating(race):
            raise LookupError

        new_value = {
            "value": value,
            "round": round
        }
        self.race_value[race].append(new_value)

    def race_get_voter_value(self, race, round):
        # Attempt to find the last value assigned to the race
        # prior to the round given.
        for value in reversed(self.race_value[race]):
            if value["round"].get_round() < round.get_round():
                return value["value"]
        return None