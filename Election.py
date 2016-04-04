import sys
import os
import importlib
import importlib.machinery
import logging
import json
from ElectionRace import ElectionRace
from ElectionCandidate import ElectionCandidate
from ElectionVoter import ElectionVoter
from ElectionError import ElectionError


class Election:
    def __init__(self, configuration_file_path):
        self.ballot_file = None
        self._races = []
        self._voters = []

        # Race and race ID relationship.
        self._race_id = {}

        self.logger = logging.getLogger("application.election")

        with open(configuration_file_path, encoding="utf-8") as configuration_file:
            self._configuration = json.loads(configuration_file.read())
            configuration = self._configuration

        # Parse the configuration data.
        for race in configuration["races"]:
            try:
                new_race = ElectionRace(race["race_id"], race["race_position"], int(race["race_max_winners"]),
                                        race["race_extended_data"])
                self._races.append(new_race)
                self._race_id[new_race.id()] = new_race
            except ValueError:
                self.logger.error("Unable to parse max winners of %s.", race["race_position"], exc_info=sys.exc_info())
                raise ElectionError("Configuration error, unable to parse max winners of %s." % race["race_position"])

        self.logger.info("Loaded %d races in configuration.", len(self._races))

        parser_directory_path = os.path.normpath(os.path.join(os.path.dirname(configuration_file_path), configuration["general"]["parser_directory"])) + "/"
        if not os.path.isdir(parser_directory_path):
            self.logger.error("Parser directory is not a valid path.", exc_info=sys.exc_info())
            raise ElectionError("Configuration error, parser directory is not a valid path.")

        importlib.invalidate_caches()
        self.ballot_parser = importlib.machinery.SourceFileLoader(configuration["general"]["ballot_parser"],
                                                                  parser_directory_path + configuration["general"][
                                                                      "ballot_parser"] + ".py").load_module()
        self.candidate_parser = importlib.machinery.SourceFileLoader(configuration["general"]["candidate_parser"],
                                                                     parser_directory_path + configuration["general"][
                                                                         "candidate_parser"] + ".py").load_module()

    def configuration(self):
        return self._configuration

    def load_candidates(self, candidate_file_path):
        self.logger.info("Parsing candidate file at `%s`.", candidate_file_path)
        candidate_data = self.candidate_parser.parse(candidate_file_path, self._races)
        self.logger.info("Parsing %d races in candidate file.", len(candidate_data))
        for race in candidate_data:
            target_race = self._race_id[race]
            self.logger.info("Parsing %d candidates in %s race.", len(candidate_data[race]), target_race)
            for candidate in candidate_data[race]:
                target_candidate = ElectionCandidate(
                    candidate["candidate_id"],
                    candidate["candidate_name"],
                    candidate["candidate_party"]
                )
                self.logger.info("Adding %s candidate to %s race.", target_candidate, target_race)
                target_race.add_candidate(target_candidate)

    def load_ballots(self, ballot_file_path, progress_dialog=None):
        if progress_dialog:
            progress_dialog.Pulse("Parsing ballot file.")
            progress_dialog.Fit()
        self.logger.info("Parsing ballot file at `%s`.", ballot_file_path)
        ballot_data = self.ballot_parser.parse(ballot_file_path, self._races)
        if progress_dialog:
            progress_dialog.SetRange(len(ballot_data))
            progress_dialog.Update(0, "Adding " + str(len(ballot_data)) + " voters to election races.")
            progress_dialog.Fit()
        self.logger.info("Adding %d voters to election.", len(ballot_data))
        for ballot_number in range(len(ballot_data)):
            self.logger.debug("Processing ballot for voter #%d.", ballot_number)
            ballot = ballot_data[ballot_number]
            voter = ElectionVoter(ballot["ballot_id"])
            for race_id in ballot["ballot_data"]:
                current_race = self.get_race(race_id)

                if len(ballot["ballot_data"][race_id]) == 0:
                    self.logger.debug("Voter %s did not vote in %s race.", voter, current_race)
                    continue

                voter.add_race(current_race)
                current_race.add_voter(voter)

                candidate_preferences = []
                self.logger.debug("Adding voter %s's %s race preferences.", voter, current_race)
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
