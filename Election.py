import sys
import os
import importlib
import importlib.machinery
from ElectionRace import ElectionRace
from ElectionCandidate import ElectionCandidate
from ElectionVoter import ElectionVoter
from ElectionError import ElectionError


class Election:
    def __init__(self, configuration):
        self.ballot_file = None
        self._races = []
        self._voters = []

        # Race and race ID relationship.
        self._race_id = {}

        # Parse the configuration data.
        for race in configuration["races"]:
            try:
                new_race = ElectionRace(race["race_id"], race["race_position"], int(race["race_max_winners"]),
                                        race["race_extended_data"])
                self._races.append(new_race)
                self._race_id[new_race.id()] = new_race
            except ValueError:
                raise ElectionError("Configuration error, unable to parse max winners of %s." % race["race_position"])

        parser_directory_path = os.path.abspath(configuration["general"]["parser_directory"]) + "/"
        if not os.path.isdir(parser_directory_path):
            raise ElectionError("Configuration error, parser directory is not a valid path.")

        importlib.invalidate_caches()
        self.ballot_parser = importlib.machinery.SourceFileLoader(configuration["general"]["ballot_parser"],
                                                                  parser_directory_path + configuration["general"][
                                                                      "ballot_parser"] + ".py").load_module()
        self.candidate_parser = importlib.machinery.SourceFileLoader(configuration["general"]["candidate_parser"],
                                                                     parser_directory_path + configuration["general"][
                                                                         "candidate_parser"] + ".py").load_module()

    def load_candidates(self, candidate_file_path):
        candidate_data = self.candidate_parser.parse(candidate_file_path, self._races)
        for race in candidate_data:
            for candidate in candidate_data[race]:
                target_race = self._race_id[race]
                target_race.add_candidate(ElectionCandidate(
                    candidate["candidate_id"],
                    candidate["candidate_name"],
                    candidate["candidate_party"]
                ))

    def load_ballots(self, ballot_file_path, progress_dialog=None):
        if progress_dialog:
            progress_dialog.Pulse("Parsing ballot file.")
            progress_dialog.Fit()
        ballot_data = self.ballot_parser.parse(ballot_file_path, self._races)
        if progress_dialog:
            progress_dialog.SetRange(len(ballot_data))
            progress_dialog.Update(0, "Adding " + str(len(ballot_data)) + " voters to election races.")
            progress_dialog.Fit()
        for ballot_number in range(len(ballot_data)):
            ballot = ballot_data[ballot_number]
            voter = ElectionVoter(ballot["ballot_id"])
            for race_id in ballot["ballot_data"]:
                if len(ballot["ballot_data"][race_id]) == 0:
                    continue

                current_race = self.get_race(race_id)
                voter.add_race(current_race)
                current_race.add_voter(voter)

                candidate_preferences = []
                for candidate_id in ballot["ballot_data"][race_id]:
                    candidate_preferences.append(current_race.get_candidate(candidate_id))
                voter.set_race_preferences(current_race, candidate_preferences)
            if progress_dialog and ballot_number % 5 == 0 and progress_dialog.GetValue() + 5 < progress_dialog.GetRange():
                progress_dialog.Update(progress_dialog.GetValue() + 5)

    def get_race(self, race_id):
        if race_id not in self._race_id:
            raise LookupError("Unable to locate race with given ID.")

        return self._race_id[race_id]

    def get_race_all(self):
        return self._races

    def race_run(self, race_id):
        self.get_race(race_id).run()
