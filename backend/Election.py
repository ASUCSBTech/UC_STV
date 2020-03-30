import hashlib
import importlib
import importlib.machinery
import json
import jsonschema
import logging
import os
import sys

from backend.ElectionCandidate import ElectionCandidate
from backend.ElectionError import ElectionError
from backend.ElectionRace import ElectionRace
from backend.ElectionVoter import ElectionVoter


class Election:
    def __init__(self, configuration_file_path):
        self.ballot_file = None
        self._races = []
        self._voters = []

        self._configuration_schema = None
        self._candidate_schema = None
        self._ballot_schema = None

        # Race and race ID relationship.
        self._race_id = {}

        self.logger = logging.getLogger("election")

        configuration = None

        # Load validation schemas, if this process fails, log it and then continue.
        base_path = os.path.normpath(os.path.join(os.path.join(os.path.dirname(__file__)), "../schemas/"))
        if os.path.isdir(base_path):
            try:
                with open(os.path.normpath(os.path.join(base_path, "./configuration_schema.json"))) as configuration_schema_file:
                    self._configuration_schema = json.loads(configuration_schema_file.read())

                with open(os.path.normpath(os.path.join(base_path, "./candidate_schema.json"))) as candidate_schema_file:
                    self._candidate_schema = json.loads(candidate_schema_file.read())

                with open(os.path.normpath(os.path.join(base_path, "./ballot_schema.json"))) as ballot_schema_file:
                    self._ballot_schema = json.loads(ballot_schema_file.read())
            except Exception:
                self.logger.warning("Unable to setup validation schemas, skipping validation.")

        self.logger.info("Parsing configuration file at `%s`. (SHA-512 Hash: `%s`)", configuration_file_path, hashlib.sha512(open(configuration_file_path, "rb").read()).hexdigest())
        with open(configuration_file_path, encoding="utf-8") as configuration_file:
            self._configuration = json.loads(configuration_file.read())
            if self._configuration_schema:
                try:
                    jsonschema.validate(self._configuration, self._configuration_schema)
                except jsonschema.exceptions.ValidationError as e:
                    self.logger.error("Configuration error, provided configuration file does not conform to configuration specifications.")
                    raise ElectionError("Configuration error, provided configuration file does not conform to configuration specifications.") from e
            configuration = self._configuration

        # Parse the configuration data.
        for race in configuration["races"]:
            try:
                new_race = ElectionRace(race["race_id"], race["race_position"], int(race["race_max_winners"]), race["race_extended_data"])
                self._races.append(new_race)
                self._race_id[new_race.id()] = new_race
            except ValueError as e:
                self.logger.error("Unable to parse max winners of %s.", race["race_position"], exc_info=sys.exc_info())
                raise ElectionError("Configuration error, unable to parse max winners of %s." % race["race_position"]) from e

        self.logger.info("Loaded %d races in configuration.", len(self._races))

        parser_directory_path = os.path.normpath(os.path.join(os.path.dirname(configuration_file_path), configuration["general"]["parser_directory"])) + "/"
        if not os.path.isdir(parser_directory_path):
            self.logger.error("Parser directory is not a valid path.", exc_info=sys.exc_info())
            raise ElectionError("Configuration error, parser directory is not a valid path.")

        importlib.invalidate_caches()
        self.ballot_parser = importlib.machinery.SourceFileLoader(configuration["general"]["ballot_parser"], parser_directory_path + configuration["general"]["ballot_parser"] + ".py").load_module()
        self.candidate_parser = importlib.machinery.SourceFileLoader(configuration["general"]["candidate_parser"], parser_directory_path + configuration["general"]["candidate_parser"] + ".py").load_module()

    def configuration(self):
        return self._configuration

    def load_candidates(self, candidate_file_path):
        self.logger.info("Parsing candidate file at `%s`. (SHA-512 Hash: `%s`)", candidate_file_path, hashlib.sha512(open(candidate_file_path, "rb").read()).hexdigest())
        candidate_data = self.candidate_parser.parse(candidate_file_path, self._races)
        if self._candidate_schema:
            try:
                jsonschema.validate(candidate_data, self._candidate_schema)
            except jsonschema.exceptions.ValidationError:
                self.logger.error("Candidate parsing error, provided candidate data does not conform to candidate data specifications.")
                raise ElectionError("Candidate parsing error, provided candidate data does not conform to candidate data specifications.")
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
        self.logger.info("Parsing ballot file at `%s`. (SHA-512 Hash: `%s`)", ballot_file_path, hashlib.sha512(open(ballot_file_path, "rb").read()).hexdigest())
        ballot_data = self.ballot_parser.parse(ballot_file_path, self._races)
        if self._ballot_schema:
            try:
                jsonschema.validate(ballot_data, self._ballot_schema)
            except jsonschema.exceptions.ValidationError:
                self.logger.error("Ballot parsing error, provided ballot data does not conform to ballot data specifications.")
                raise ElectionError("Ballot parsing error, provided ballot data does not conform to ballot data specifications.")
        ballot_count = len(ballot_data)
        if progress_dialog:
            progress_dialog.Update(0, "Adding %d voter(s) to election races." % ballot_count)
            progress_dialog.Fit()
        self.logger.info("Adding %d voters to election.", ballot_count)
        for ballot_number in range(ballot_count):
            self.logger.debug("Processing ballot for voter #%d.", ballot_number)
            ballot = ballot_data[ballot_number]
            voter = ElectionVoter(ballot["ballot_id"])
            for race_id in ballot["ballot_data"]:
                current_race = self.get_race(race_id)

                if len(ballot["ballot_data"][race_id]) == 0:
                    self.logger.debug("Voter `%s` did not vote in `%s` race.", voter, current_race)
                    continue

                voter.add_race(current_race)
                current_race.add_voter(voter)

                candidate_preferences = []
                self.logger.debug("Adding voter `%s`'s `%s` race preferences.", voter, current_race)
                for candidate_id in ballot["ballot_data"][race_id]:
                    candidate_preferences.append(current_race.get_candidate(candidate_id))
                voter.set_race_preferences(current_race, candidate_preferences)

            if progress_dialog and ballot_number % 5 == 0:
                progress_dialog.Update(int((ballot_number / ballot_count) * 100))

    def get_race(self, race_id):
        if race_id not in self._race_id:
            raise LookupError("Unable to locate race with given ID.")

        return self._race_id[race_id]

    def get_race_all(self):
        return self._races

