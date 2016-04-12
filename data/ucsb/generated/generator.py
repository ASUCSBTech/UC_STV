import random
import os
import json
import csv
import uuid

VOTERS = 7200

def main():
    base_path = os.path.join(os.path.dirname(__file__))
    with open(os.path.normpath(os.path.join(base_path, "./data/firstname.json"))) as firstname_file:
        first_names = json.loads(firstname_file.read())
    with open(os.path.normpath(os.path.join(base_path, "./data/lastname.json"))) as lastname_file:
        last_names = json.loads(lastname_file.read())
    with open(os.path.normpath(os.path.join(base_path, "./configuration.json"))) as configuration_file:
        configuration = json.loads(configuration_file.read())

    return_candidate_data = []

    races = {}
    for race in configuration["races"]:
        current_race = races[race["race_extended_data"]["parser_group"]] = {
            "candidates": [],
            "write-ins": [],
            "write-in-fields": 0,
            "columns": []
        }
        candidate_count = race["race_max_winners"] + random.randint(5, 15)
        if "parser_writein_fields" in race["race_extended_data"]:
            current_race["write-in-fields"] = race["race_extended_data"]["parser_writein_fields"]
            current_race["write-ins"] = race["race_extended_data"]["parser_writein_whitelist"]
        for x in range(candidate_count):
            current_race["candidates"].append(random.choice(first_names) + " " + random.choice(last_names) + " - " + random.choice(first_names) + " Party")

    return_candidate_data.append(["V1"])
    return_candidate_data.append(["ResponseID"])

    for race in races:
        for candidate in races[race]["candidates"]:
            return_candidate_data[0].append(race)
            return_candidate_data[1].append(candidate)
            races[race]["columns"].append(len(return_candidate_data[1]) - 1)
        for x in range(races[race]["write-in-fields"]):
            return_candidate_data[0].append(race)
            return_candidate_data[1].append("Write-In")
            races[race]["columns"].append(len(return_candidate_data[1]) - 1)
            return_candidate_data[0].append(race)
            return_candidate_data[1].append("Write-In-TEXT")

    for x in range(VOTERS):
        row_data = [""] * len(return_candidate_data[1])
        row_data[0] = uuid.uuid4()
        for race in races:
            # Choose candidate order:
            candidate_options = races[race]["candidates"] + ["WRITE-IN"] * races[race]["write-in-fields"]
            candidate_choices = random.sample(candidate_options, random.randint(0, len(candidate_options)))
            candidate_writein_possible = races[race]["write-ins"][:] + ["", ""]
            random.shuffle(candidate_writein_possible)
            for column in races[race]["columns"]:
                if return_candidate_data[1][column] == "Write-In":
                    try:
                        candidate_choice_index = candidate_choices.index("WRITE-IN")
                        row_data[column] = candidate_choice_index + 1
                        candidate_choices[candidate_choice_index] = ""
                        # Choose a write in candidate:
                        row_data[column + 1] = candidate_writein_possible.pop(0)
                    except ValueError:
                        pass
                else:
                    try:
                        candidate_choice_index = candidate_choices.index(return_candidate_data[1][column])
                        row_data[column] = candidate_choice_index + 1
                    except ValueError:
                        pass
        return_candidate_data.append(row_data)

    with open(os.path.normpath(os.path.join(base_path, "./ballot_data.csv")), "w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file, quoting=csv.QUOTE_ALL)
        for row in return_candidate_data:
            csv_writer.writerow(row)

if __name__ == "__main__":
    main()