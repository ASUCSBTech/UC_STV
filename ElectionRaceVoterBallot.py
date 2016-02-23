class ElectionRaceVoterBallot:
    def __init__(self, voter, candidate, value):
        self.voter = voter
        self.candidate = candidate
        self.value = value

    def get_voter(self):
        return self.voter

    def get_candidate(self):
        return self.candidate

    def get_value(self):
        return self.value
