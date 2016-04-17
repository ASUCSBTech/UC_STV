import json
import random
import os

RACES = {
    "academic_vp": "2",
    "executive_vp": "4",
    "external_vp": "3",
    "president": "6",
    "senator": "1",
    "student_advocate": "5"
}
RACES_CANDIDATES = {}
RACE_CANDIDATES = 30
VOTERS = 12000

def main():
    base_path = os.path.join(os.path.dirname(__file__))
    with open(os.path.normpath(os.path.join(base_path, "./data/firstname.json"))) as firstname_file:
        first_names = json.loads(firstname_file.read())
    with open(os.path.normpath(os.path.join(base_path, "./data/lastname.json"))) as lastname_file:
        last_names = json.loads(lastname_file.read())

    return_candidate_data = {}
    return_ballot_data = {
        "ballots": []
    }

    candidate_id = 1

    for race in RACES:
        # Generate candidates in race.
        return_candidate_data[race] = []
        RACES_CANDIDATES[RACES[race]] = []
        for x in range(RACE_CANDIDATES):
            race_candidate = {
                "name": random.choice(first_names) + " " + random.choice(last_names),
                "number": str(candidate_id),
                "party": random.choice(first_names) + " Party"
            }
            RACES_CANDIDATES[RACES[race]].append(str(race_candidate["number"]))
            candidate_id += 1
            return_candidate_data[race].append(race_candidate)

    for x in range(VOTERS):
        ballot = {}
        for race in RACES_CANDIDATES:
            ballot[race] = random.sample(RACES_CANDIDATES[race], random.randint(0, len(RACES_CANDIDATES[race])))
        return_ballot_data["ballots"].append(ballot)

    with open(os.path.normpath(os.path.join(base_path, "./candidates.json")), "w") as candidates_out:
        json.dump(return_candidate_data, candidates_out)

    with open(os.path.normpath(os.path.join(base_path, "./ballots.json")), "w") as ballots_out:
        json.dump(return_ballot_data, ballots_out)


if __name__ == "__main__":
    main()
