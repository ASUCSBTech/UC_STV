class ElectionRaceVoterBallot:
    def __init__(self, race, voter, candidate, value):
        self._race = race
        self._voter = voter
        self._candidate = candidate
        self._value = value

    def race(self):
        return self._race

    def voter(self):
        return self._voter

    def candidate(self):
        return self._candidate

    def value(self):
        return self._value

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               (self.race, self.voter, self.candidate) == (other.race, other.voter, other.candidate)
