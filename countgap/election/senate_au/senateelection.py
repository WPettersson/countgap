import countgap.election
import math

class SenateElection(countgap.election.Election):

    """A class for counting Australian Senate Elections"""

    def __init__(self, candidate_list, candidate_hash, storage=None):
        """Initialise an election

        Keyword arguments:
        candidate_list -- a list of election.senate_au.Candidate objects
        candidate_dict -- a dictof the same objects
        """
        countgap.election.Election.__init__(self, candidate_list, storage)
        self.candidate_hash = candidate_hash
        self._winners = []

    def run(self, ballots, winners):
        """Run the election

        Keyword arguments
        ballots -- an iterable object of election.au_senate.Ballot objects
        winners -- the number of required election seat winners
        """

        self.verbose = False
        self.ballots = ballots
        self.winners_required = winners
        self._eliminated = []
        self._num_votes = 0
        # Initial allocation of ballots to candidates
        for b in self.ballots:
            b.list[0].current_ballots.append(b)
            self._num_votes += b.get_value()
        self._quota = math.floor(self._num_votes / (self.winners_required + 1)) + 1 # S273 (8)
        for c in self.candidates:
            c.set_votes()
        print "Quota is %d"%(self._quota)
        complete = False
        self.sort_candidates()
        for c in self.candidates:
            v = c.get_votes()
            if v > 0:
                print "%s: %s"%(c._name, v)
        round_number = 0
        while not complete:
            round_number += 1
            print "Round %d"%(round_number)
            complete = self._next_round()


    def _next_round(self):
        # S273 (17)
        if self.winners_required - len(self._winners) == 1:
            if len(self.candidates) - len(self._eliminated) - len(self._winners) == 2:
                for c in self.candidates:
                    if c not in self._eliminated and c not in self._winners:
                        self._winners.append(c)
                return True
        # S273 (18)
        if len(self.candidates) - len(self._eliminated) + len(self._winners) == self.winners_required:
            for c in self.candidates:
                if c not in self._eliminated and c not in self._winners:
                    self._winners.append(c)
            return True
        elected = []
        c = self.elect()
        while c:
            elected.append(c)
            c = self.elect()
            if len(self._winners) == self.winners_required:
                return True
        # Transfer votes of elected senators
        self.transfer(elected)
        # Resort votes of candidates who were elected
        self.sort_candidates()
        # S273 (13) Exclusions
        # What decides whether we take (a) or (b)? If (b) is possible, do we
        # always take (b)? Does it not make a difference?
        if len(elected) == 0:
            if not self.mass_exclude():
                for c in reversed(self.candidates):
                    if not (c in self._eliminated or c in self._winners):
                        self.exclude(c)
                        break
        for c in self.candidates:
            v = c.get_votes()
            if v > 0:
                print "%s: %s"%(c._name, v)
        return False

    def exclude(self, candidate):
        print "Eliminated %s"%(candidate._name)
        self._eliminated.append(candidate)
        candidate.current_ballots.sort(key=lambda x:x.data['value'], reverse=True)
        if self.verbose:
            print "%d votes to transfer"%(candidate.get_votes())
        trans = {}
        for dest in self.candidates:
            trans[dest] = 0
        for b in candidate.current_ballots:
            for cand in b.list:
                if cand in self._eliminated or cand in self._winners:
                    continue
                cand.current_ballots.append(b)
                trans[cand] += b.get_value()
                if self.verbose:
                    print "%f transferred to %s"%(b.get_value(), cand._name)
                break
        total_transferred = 0
        for dest in self.candidates:
            if trans[dest] > 0:
                print "%d transferred to %s"%(trans[dest], dest._name)
                dest.num_votes += int(trans[dest])
                total_transferred += int(trans[dest])
        candidate.num_votes = 0
        print "%d total transferred"%(total_transferred)
        if self.verbose:
            print "Elimination complete"
        candidate.current_ballots = []

    def mass_exclude(self):
        return False # TODO

    def sort_candidates(self):
        """Sort candidates by number of votes"""
        self.candidates.sort(key=lambda x:x.get_votes(), reverse=True)

    def set_notional_votes(self):
        """Calculate the number of notional votes each candidate has

        Requires: Candidates must already be sorted

        """
        notional_sum = 0
        for c in reversed(self.candidates):
            notional_sum += c.get_votes()
            c.notional_votes = notional_sum

    def elect(self):
        """Elect a candidate, and transfer votes"""
        for c in self.candidates:
            if not c in self._winners:
                break
        if c.get_votes() < self._quota: # S273 (8)
            return False
        print "Elected %s"%(c._name)
        self._winners.append(c)
        return c

    def transfer(self, elected):
        trans = {}
        elected.sort(cmp = lambda x,y: x.get_votes() < y.get_votes())
        for c in elected:
            for dest in self.candidates:
                trans[dest] = 0
            c_votes = c.get_votes()
            surplus_votes = c_votes - self._quota # S273 (9a)
            transfer_value = surplus_votes/c_votes # S273 (9b)
            print "%d votes of %s to transfer at %f value"%(surplus_votes, c._name,transfer_value)
            # Order of transfer after a candidate is elected is not specified
            for b in c.current_ballots:
                b.update_transfer_value(transfer_value) # S273 (9b)
                for cand in b.list:
                    if cand in self._eliminated or cand in self._winners:
                        continue
                    cand.current_ballots.append(b) # S273 (9b)
                    trans[cand] += b.get_value()
                    #if self.verbose:
                    #print "%d transferred to %s"%(b.get_value(), cand._name)
                    break
            c.current_ballots = []
            total_transferred = 0
            for dest in self.candidates:
                t = int(trans[dest])
                if t != 0:
                    print "%d transferred to %s"%(t, dest._name)
                    dest.num_votes += t
                    total_transferred += t
            c.num_votes = self._quota
            print "%d lost to fractional votes"%(surplus_votes - total_transferred)
            for c in self.candidates:
                v = c.get_votes()
                if v > 0:
                    print "%s: %s"%(c._name, v)


    def get_candidate(self, id):
        """ Given a candidate ID, returns the candidate object"""
        return self.candidate_hash[id]
        #for c in self.candidates:
        #    if c.id == id:
        #        return c
        #return False

    def print_results(self):
        """ Prints the winners of the election, in elected order"""
        for c in self._winners:
            print "Elected %s"%(c._name)

    def print_partial_results(self, count=False):
        """ Prints the current number of votes for each candidate"""
        num=0
        for c in self.candidates:
            if c in self._winners:
                status = "Elected"
            elif c in self._eliminated:
                status = "Excluded"
            else:
                status = c.get_votes()
            print "%s \t%s"%(c._name, status)
            num+=1
            if count and num == count:
                return

    def print_ballots(self, c, count=3):
        """ Prints the ballots of a candidate"""
        for b in c.current_ballots:
            self.print_ballot(b,count)

    def print_ballot(self, b, count=3):
        """ Prints an individual ballot"""
        print "Ballot worth %f"%(b.get_value())
        num = 0
        for cand in b.list:
            print "%s"%(cand._name)
            num+=1
            if num==count:
                return

# vim: sw=4:ts=4
