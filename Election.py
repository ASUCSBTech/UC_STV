import sys
import os
from ElectionRace import ElectionRace
from ElectionCandidate import ElectionCandidate
from ElectionVoter import ElectionVoter


class Election:
    def __init__(self, configuration):
        self.ballot_file = None
        self.races = {}
        self.voters = []

        # Parse the configuration data.
        for race in configuration["races"]:
            try:
                self.races[str(race["race_id"])] = ElectionRace(race["race_id"], race["race_position"],
                                                                int(race["race_max_winners"]),
                                                                race["race_extended_data"])
            except ValueError:
                print("Configuration error, unable to parse race_max_winners of " + race["race_position"],
                      file=sys.stderr)
                sys.exit(2)

        if os.path.isdir(os.path.abspath(configuration["general"]["parser_directory"])):
            sys.path[0:0] = [os.path.abspath(configuration["general"]["parser_directory"])]
        else:
            print("Configuration error, parser directory is not a valid path", file=sys.stderr)
            sys.exit(2)

        self.ballot_parser = __import__(configuration["general"]["ballot_parser"])
        self.candidate_parser = __import__(configuration["general"]["candidate_parser"])

    def load_candidates(self, candidate_file_path):
        candidate_data = self.candidate_parser.parse(candidate_file_path, self.races)
        for race in candidate_data:
            for candidate in candidate_data[race]:
                target_race = self.races[race]
                target_race.candidate_add(ElectionCandidate(
                    candidate["candidate_id"],
                    candidate["candidate_name"],
                    candidate["candidate_party"]
                ))

    def load_ballots(self, ballot_file_path):
        ballot_data = self.ballot_parser.parse(ballot_file_path, self.races)
        for ballot in ballot_data:
            voter = ElectionVoter(ballot["ballot_id"])
            for race in ballot["ballot_data"]:
                if len(ballot["ballot_data"][race]) == 0:
                    continue

                voter.race_add(self.races[race])
                candidate_preferences = []
                for candidate in ballot["ballot_data"][race]:
                    candidate_preferences.append(self.races[race].candidate_find(candidate))
                voter.race_preferences_set(self.races[race], candidate_preferences)

            for race in self.races:
                if voter.race_participating(self.races[race]):
                    self.races[race].voter_add(voter)

    def race_get_all(self):
        return self.races

    def race_run(self, race_id):
        self.races[race_id].run()