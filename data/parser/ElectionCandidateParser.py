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
# Last Modified: February 17, 2016
###############
import csv


def parse(candidate_file_path, races):
    candidates_data = {}

    # Open the ballot file.
    with open(candidate_file_path, encoding="UTF-8", errors="ignore") as candidate_file:
        candidate_file_csv = csv.reader(candidate_file)
        candidate_file_data = list(candidate_file_csv)
        for race in races:
            # Find all columns related to this race.
            columns = []
            for column_index in range(len(candidate_file_data[0])):
                if candidate_file_data[0][column_index] == races[race].get_extended_data()["parser_group"]:
                    columns.append(column_index)

            candidates = []
            candidates_write_ins = []
            for column in columns:
                if candidate_file_data[1][column].startswith("Write-In"):
                    # Process write in candidates.
                    if candidate_file_data[1][column].endswith("TEXT"):
                        for row in range(2, len(candidate_file_data)):
                            candidate_id = candidate_file_data[row][column].strip()
                            if candidate_id and candidate_id not in candidates_write_ins:
                                candidates.append({
                                    "candidate_id": candidate_id,
                                    "candidate_name": candidate_id,
                                    "candidate_party": "Independent"
                                })
                                candidates_write_ins.append(candidate_id)
                    continue

                (candidate_name, candidate_party) = candidate_file_data[1][column].rsplit("-", 1)
                candidates.append({
                    "candidate_id": candidate_file_data[1][column],
                    "candidate_name": candidate_name.strip(),
                    "candidate_party": candidate_party.strip()
                })
            candidates_data[str(races[race].get_id())] = candidates

    return candidates_data
