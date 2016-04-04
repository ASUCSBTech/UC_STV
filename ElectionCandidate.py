class ElectionCandidate:
    def __init__(self, candidate_id, candidate_name, candidate_party):
        self._id = candidate_id
        self._name = candidate_name
        self._party = candidate_party

    def id(self):
        return self._id

    def name(self):
        return self._name

    def party(self):
        return self._party

    def __hash__(self):
        return hash((self._id, self._name, self._party))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               (self.id(), self.name(), self.party()) == (other.id(), other.name(), other.party())

    def __str__(self):
        return self._name + " - " + self._party

    def __repr__(self):
        return self._name + " - " + self._party