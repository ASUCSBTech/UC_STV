class ElectionCandidate:
    def __init__(self, id, name, party):
        self.id = id
        self.name = name
        self.party = party

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_party(self):
        return self.party

    def __hash__(self):
        return hash((self.id, self.name, self.party))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               (self.id, self.name, self.party) == (other.id, other.name, other.party)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name