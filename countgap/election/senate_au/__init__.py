import election
import math

class Candidate():

    """A candidate for an Australian Senate election"""

    def __init__(self,id,name=False):
        self.id = id
        self._name = name
        self.current_ballots = []

    def getVotes(self):
        return sum([math.floor(x.getValue()) for x in self.current_ballots])


class Ballot(election.Ballot):
    def __init__(self, id, ballot_data, count=1):
        """Initialise a ballot for an Australian Senate election

        Keyword arguments:
        ballot_data -- A list of the votes (descending order of preference).
        count -- If present, the number of on-paper ballots to be represented
                 by this Ballot.

        If two on-paper ballots are identical, they are treated exactly the
        same by S273. As such, we can reduce the required number of
        computations by treating them as one ballot that is worth double.
        """
        election.Ballot.__init__(self, id, ballot_data)
        self.data['value'] = count

    def getValue(self):
        """Get the number of votes this ballot represents """
        return self.data['value']

    def updateTransferValue(self, new_value):
        self.data['value'] *= new_value

# vim: sw=4:ts=4
