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
# Last Modified: April 21, 2016
###############
import csv


class WriteInInvalid:
    pass


class CandidateDroppedOut:
    pass


def parse(ballot_file_path, races):
    ballots_data = []
    invalid_writein = WriteInInvalid()
    candidate_dropped_out = CandidateDroppedOut()

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
                # Get list of candidates that have dropped out after ballots have been cast.
                candidates_dropped_out = []
                if "parser_candidates_droppedout" in race.extended_data():
                    candidates_dropped_out = race.extended_data()["parser_candidates_droppedout"]

                # Note: The size of the race_preferences array must be calculated as:
                # 1 + number_of_candidates + number_of_write_in_spots
                #
                # This is because the race_preferences array is zero indexed, the
                # zeroth element is popped off the list prior to submitting the ballot
                # and the number_of_write_in_spots is necessary to account for their
                # indices even though there many not be any valid write-ins.

                # By default, races do not have write ins.
                write_in_count = 0
                if "parser_writein_fields" in race.extended_data():
                    write_in_count = race.extended_data()["parser_writein_fields"]
                race_preferences = [None] * (1 + len(race.candidates()) + write_in_count + len(candidates_dropped_out))
                for column in ballot_columns[race]:
                    try:
                        if ballot_file_data[1][column].strip() == "Write-In":
                            race_order = int(ballot_file_data[row][column])
                            candidate_id = ballot_file_data[row][column + 1].strip()
                            candidate = race.get_candidate(candidate_id)
                            if candidate:
                                race_preferences[race_order] = candidate.id()
                            else:
                                race_preferences[race_order] = invalid_writein
                        else:
                            race_order = int(ballot_file_data[row][column])
                            candidate_id = ballot_file_data[1][column].strip()
                            if candidate_id not in candidates_dropped_out:
                                race_preferences[race_order] = race.get_candidate(candidate_id).id()
                            else:
                                race_preferences[race_order] = candidate_dropped_out
                    except ValueError:
                        pass
                # Remove zeroth index (None) since candidates are ordered from 1 to N.
                race_preferences.pop(0)
                # Filter write-ins that are invalid.
                race_preferences = list(filter(lambda element: element is not invalid_writein, race_preferences))
                # Filter candidates that have dropped out.
                race_preferences = list(filter(lambda element: element is not candidate_dropped_out, race_preferences))
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
