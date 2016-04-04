###############
# Ballot Parser for Qualtrics
#
# This ballot parser has been tailored to the ballot
# system used by UCSB. If you use another software
# to define ballots, ensure the data returned by the
# ballot parser returns data in the following fashion:
#
# [
#    {
#        "ballot_id": "unique_ballot_id",
#        "ballot_data": {
#            "race_id": [
#                "candidate_id",
#                "candidate_id",
#                ...
#            ],
#            "race_id": [
#                "candidate_id",
#                "candidate_id",
#                ...
#           ],
#           ...
#        }
#    },
#    {
#        "ballot_id": "unique_ballot_id",
#        "ballot_data": {
#            "race_id": [
#                "candidate_id",
#                "candidate_id",
#                ...
#            ],
#            "race_id": [
#                "candidate_id",
#                "candidate_id",
#                ...
#           ],
#           ...
#        }
#    },
#    ...
# ]
#
# The race_id value should correspond to the value
# specified in the configuration file.
#
# Each list identified by the race_id should be in
# voting-choice order, where the first candidate
# within the list corresponds to the ballot's first
# choice vote.
#
# The candidate_id should correspond to the value
# returned by the election candidate parser.
#
# Last Modified: February 24, 2016
###############
import csv


def parse(ballot_file_path, races):
    ballots_data = []

    # Open the ballot file.
    with open(ballot_file_path, encoding="UTF-8", errors="ignore") as ballot_file:
        ballot_file_csv = csv.reader(ballot_file)
        ballot_file_data = list(ballot_file_csv)
        ballot_columns = {}

        parser_groups = {}
        for race in races:
            parser_groups[race.extended_data()["parser_group"]] = race
            ballot_columns[race] = []

        for column_index in range(len(ballot_file_data[0])):
            if ballot_file_data[0][column_index] in parser_groups:
                ballot_columns[parser_groups[ballot_file_data[0][column_index]]].append(column_index)

        for row in range(2, len(ballot_file_data)):
            # Process each individual voter.
            ballot_data = {}

            # Loop through each race and get preferences.
            ballot_race_data = {}
            for race in races:
                race_preferences = [None] * len(race.candidates())
                for column in ballot_columns[race]:
                    try:
                        if ballot_file_data[1][column].strip() == "Write-In":
                            race_order = float(ballot_file_data[row][column])
                            if ballot_file_data[row][column + 1].strip():
                                race_preferences[int(race_order)] = race.get_candidate(ballot_file_data[row][column + 1].strip()).id()
                        else:
                            race_order = float(ballot_file_data[row][column])
                            race_preferences[int(race_order)] = race.get_candidate(ballot_file_data[1][column].strip()).id()
                    except ValueError:
                        pass
                # Remove zeroth index (None) since candidates are ordered from 1 to N.
                race_preferences.pop(0)
                try:
                    preference_max = race_preferences.index(None)
                    race_preferences = race_preferences[0:preference_max]
                except ValueError:
                    pass
                ballot_race_data[race.id()] = race_preferences

            ballot_data["ballot_id"] = ballot_file_data[row][0]
            ballot_data["ballot_data"] = ballot_race_data

            ballots_data.append(ballot_data)

    return ballots_data
