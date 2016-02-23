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
# Last Modified: February 17, 2016
###############
import csv


def parse(ballot_file_path, races):
    ballots_data = []

    # Open the ballot file.
    with open(ballot_file_path, encoding="UTF-8", errors="ignore") as ballot_file:
        ballot_file_csv = csv.reader(ballot_file)
        ballot_file_data = list(ballot_file_csv)
        ballot_columns = {}
        for race in races:
            # Find all columns related to this race.
            columns = []
            for column_index in range(len(ballot_file_data[0])):
                if ballot_file_data[0][column_index] == races[race].get_extended_data()["parser_group"]:
                    columns.append(column_index)
            ballot_columns[str(races[race].get_id())] = columns

        for row in range(2, len(ballot_file_data)):
            # Process each individual voter.
            ballot_data = {}

            # Loop through each race and get preferences.
            ballot_race_data = {}
            for race in races:
                race_preferences = [None] * len(races[race].get_candidates_all())
                for column in ballot_columns[str(races[race].get_id())]:
                    try:
                        if ballot_file_data[1][column].strip() == "Write-In":
                            race_order = float(ballot_file_data[row][column])
                            if ballot_file_data[row][column+1].strip():
                                race_preferences[int(race_order)] = races[race].candidate_find(
                                                                                ballot_file_data[row][column+1].strip()
                                                                                ).get_id()
                        else:
                            race_order = float(ballot_file_data[row][column])
                            race_preferences[int(race_order)] = races[race].candidate_find(
                                                                            ballot_file_data[1][column].strip()
                                                                            ).get_id()
                    except ValueError:
                        pass
                race_preferences.pop(0)
                try:
                    preference_max = race_preferences.index(None)
                    race_preferences = race_preferences[0:preference_max]
                except ValueError:
                    pass
                ballot_race_data[str(races[race].get_id())] = race_preferences

            ballot_data["ballot_id"] = ballot_file_data[row][0]
            ballot_data["ballot_data"] = ballot_race_data

            ballots_data.append(ballot_data)

    return ballots_data
