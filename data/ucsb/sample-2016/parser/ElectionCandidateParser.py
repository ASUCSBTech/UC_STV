###############
# Candidate Parser for Qualtrics
#
# This candidate parser has been tailored to the ballot
# system used by UCSB. If you use another software
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
import csv


def parse(candidate_file_path, races):
    candidates_data = {}

    # Open the ballot file.
    with open(candidate_file_path, encoding="UTF-8", errors="ignore") as candidate_file:
        candidate_file_csv = csv.reader(candidate_file)
        candidate_file_data = list(candidate_file_csv)
        race_columns = {}

        parser_groups = {}
        for race in races:
            parser_groups[race.extended_data()["parser_group"]] = race
            race_columns[race] = []

        for column_index in range(len(candidate_file_data[0])):
            if candidate_file_data[0][column_index] in parser_groups:
                race_columns[parser_groups[candidate_file_data[0][column_index]]].append(column_index)

        for race in races:
            candidates = []
            if "parser_writein_whitelist" in race.extended_data():
                write_in_whitelist = race.extended_data()["parser_writein_whitelist"]
                for candidate in write_in_whitelist:
                    candidates.append({
                        "candidate_id": candidate,
                        "candidate_name": candidate,
                        "candidate_party": "Independent"
                    })

            for column_index in race_columns[race]:
                if candidate_file_data[1][column_index].startswith("Write-In"):
                    continue

                (candidate_name, candidate_party) = candidate_file_data[1][column_index].rsplit("-", 1)
                candidates.append({
                    "candidate_id": candidate_file_data[1][column_index],
                    "candidate_name": candidate_name.strip(),
                    "candidate_party": candidate_party.strip()
                })

            candidates_data[race.id()] = candidates

    return candidates_data
