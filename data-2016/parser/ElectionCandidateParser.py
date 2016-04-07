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
import os


def parse(candidate_file_path, races):
    candidates_data = {}

    whitelist_file_path = os.path.normpath(os.path.join(os.path.join(os.path.dirname(__file__)), "../whitelist_candidates.txt"))

    with open(whitelist_file_path, encoding="UTF-8", errors="ignore") as whitelist_file:
        write_in_whitelist = [line.strip() for line in whitelist_file]

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
            candidates_write_ins = []
            for column_index in race_columns[race]:
                if candidate_file_data[1][column_index].startswith("Write-In"):
                    # Process write in candidates.
                    if candidate_file_data[1][column_index].endswith("TEXT"):
                        for row in range(2, len(candidate_file_data)):
                            candidate_id = candidate_file_data[row][column_index].strip()
                            if candidate_id and candidate_id in write_in_whitelist and candidate_id not in candidates_write_ins:
                                candidates.append({
                                    "candidate_id": candidate_id,
                                    "candidate_name": candidate_id,
                                    "candidate_party": "Independent"
                                })
                                candidates_write_ins.append(candidate_id)
                    continue

                (candidate_name, candidate_party) = candidate_file_data[1][column_index].rsplit("-", 1)
                candidates.append({
                    "candidate_id": candidate_file_data[1][column_index],
                    "candidate_name": candidate_name.strip(),
                    "candidate_party": candidate_party.strip()
                })
            candidates_data[race.id()] = candidates

    return candidates_data
