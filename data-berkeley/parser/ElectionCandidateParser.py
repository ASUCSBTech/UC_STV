###############
# Candidate Parser for UC Berkeley
#
# This candidate parser has been tailored to the ballot
# system used by UCB. If you use another software
# to define ballots, ensure the data returned by the
# candidate parser returns data in the following fashion:
#
# {
#   "race_id": [
#       {
#           "candidate_id": "unique_candidate_id",
#           "candidate_name": "candidate_full_name",
#           "candidate_party": "candidate_party"
#       },
#       {
#           "candidate_id": "unique_candidate_id",
#           "candidate_name": "candidate_full_name",
#           "candidate_party": "candidate_party"
#       },
#       ...
#   ],
#   "race_id": [
#       {
#           "candidate_id": "unique_candidate_id",
#           "candidate_name": "candidate_full_name",
#           "candidate_party": "candidate_party"
#       },
#       {
#           "candidate_id": "unique_candidate_id",
#           "candidate_name": "candidate_full_name",
#           "candidate_party": "candidate_party"
#       },
#       ...
#   ],
#   ...
# }
#
# The race_id value should correspond to the value
# specified in the configuration file.
#
# Each list identified by the race_id should contain
# candidates in each race.
#
# The candidate_id value should be unique to
# each candidate in each race. The candidate_id should
# NOT be repeated in another race.
#
# Last Modified: February 24, 2016
###############
import json


def parse(candidate_file_path, races):
    candidates_data = {}

    # Open the ballot file.
    with open(candidate_file_path, encoding="UTF-8", errors="ignore") as candidate_file:
        candidate_file_data = json.loads(candidate_file.read())

        for race in races:
            race_candidates_data = []
            candidate_file_race_data = candidate_file_data[race.extended_data()["parser_group"]]
            for race_data_candidate in candidate_file_race_data:
                race_candidates_data.append({
                    "candidate_id": race_data_candidate["number"],
                    "candidate_name": race_data_candidate["name"],
                    "candidate_party": race_data_candidate["party"]
                })
            candidates_data[race.id()] = race_candidates_data

    return candidates_data
