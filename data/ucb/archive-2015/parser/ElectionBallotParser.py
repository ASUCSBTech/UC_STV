###############
# Ballot Parser for UC Berkeley Results
#
# This ballot parser has been tailored to the ballot
# system used by UCB. If you use another software
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
import json
import uuid


def parse(ballot_file_path, races):
    ballots_data = []

    # Open the ballot file.
    with open(ballot_file_path, encoding="UTF-8", errors="ignore") as ballot_file:
        ballot_file_data = json.loads(ballot_file.read())
        for ballot in ballot_file_data["ballots"]:
            ballot_data = {}
            ballot_data["ballot_id"] = str(uuid.uuid4())
            ballot_data["ballot_data"] = {}

            for race in races:
                ballot_data["ballot_data"][race.id()] = ballot[race.id()]
            ballots_data.append(ballot_data)

    return ballots_data
