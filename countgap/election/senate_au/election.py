import election
import math

class Election(election.Election):

    """A class for counting Australian Senate Elections"""

    def __init__(self, candidates, storage=None):
        """Initialise an election

        Keyword arguments:
        candidates -- a list of election.senate_au.Candidate objects
        """
        election.Election.__init__(self, candidates, storage)
        self._winners = []

    def run(self, ballots, winners):
        """Run the election

        Keyword arguments
        ballots -- a list of election.au_senate.Ballot objects
        winners -- the number of required election seat winners
        """
        self.ballots = ballots
        self.winners_required = winners
        self._num_votes = sum([b.getValue() for b in ballots])
        self._quota = math.floor(self._num_votes / (self._winners + 1)) + 1 # S273 (8)
        # Initial allocation of ballots to candidates
        for b in self.ballots:
            self.getCandidate(b.list()[0]).current_ballots.append(b)
        complete = False
        while not complete:
            complete = self._next_round()


    def _next_round(self):
        # S273 (17)
        if self.winners_required - len(self._winners) == 1:
            if len(self.candidates) - len(self._eliminated) - len(self._winners) == 2:
                for c in self.candidates:
                    if c.id not in self_eliminated and c.id not in self._winners:
                        self._winners.append(c.id)
                return True
        # S273 (18)
        if len(self.candidates) - len(self._eliminated) == self.winners_required:
            for c in self.candidates:
                if c.id not in self_eliminated and c.id not in self._winners:
                    self._winners.append(c.id)
            return True
        while self.elect():
            # Resort candidates since we transferred some votes
            self.sortCandidates()
            # If someone is elected, check for more elections
            if len(self._winners) == self.winners_required:
                return True
        # S273 (13) Exclusions
        # What decides whether we take (a) or (b)? If (b) is possible, do we
        # always take (b)? Does it not make a difference?
        if not self.mass_exclude():
            self.exclude(self.candidates[-1])
        return False

    def exclude(self, candidate):
        self._eliminated.append(candidate.id)
        candidate.current_ballots.sort(key=lambda x:x.data['value'], reverse=True)
        for b in candidate.current_ballots:
            for pos,cand_id in b.list():
                if cand_id in _eliminated or cand_id in _winners:
                    continue
                self.getCandidate(cand_id).ballots.append(b)
                break
        candidate.ballots = []

    def mass_exclude(self):
        return False # TODO

    def sortCandidates(self):
        """Sort candidates by number of votes"""
        self.candidates.sort(key=lambda x:x.getVotes(), reverse=True)

    def setNotionalVotes(self):
        """Calculate the number of notional votes each candidate has

        Requires: Candidates must already be sorted

        """
        notional_sum = 0
        for c in reversed(self.candidates):
            notional_sum += c.getVotes()
            c.notional_votes = notional_sum

    def elect(self):
        """Elect a candidate, and transfer votes"""
        c = self.candidates[0]
        c_votes = c.getVotes()
        if c_votes < self._quota: # S273 (8)
            return False
        self._winners.append(c.id)
        surplus_votes = c_votes - quota # S273 (9a)
        transfer_value = surplus_votes/c_votes # S273 (9b)
        # Order of transfer after a candidate is elected is not specified
        for b in c.current_ballots:
            b.updateTransferValue(transfer_value) # S273 (9b)
            for pos,cand_id in b.list():
                if cand_id in _eliminated or cand_id in _winners:
                    continue
                self.getCandidate(cand_id).ballots.append(b) # S273 (9b)
                break
        c.ballots = []
        return True

    def getCandidate(self, id):
        for c in self.candidates:
            if c.id == id:
                return c
        return False
# vim: sw=4:ts=4
