from .parse import *
from countgap.election.senate_au import Ballot
from countgap.election.senate_au import Candidate

import pymongo
from bson.dbref import DBRef

class ValuedBallot(Ballot):
    def __init__(self, id, ballots, value):
        super().__init__(id, ballots)
        self._value = value

    @property
    def value(self):
        return self._value


def import_election_files(candidates, gvt, first_prefs, btl):
    db = pymongo.Connection().federalElections

    for record in read_candidates_file(candidates):
        db.candidates.insert(record)
    num_candidates = db.candidates.count()

    for record in read_gvt_file(gvt):
        for i in range(len(record['candidates'])):
            record['candidates'][i] = DBRef('candidates', record['candidates'][i])
        db.gvt.insert(record)

    for record in read_first_prefs_by_state_file(first_prefs):
        db.firstPrefs.insert(record)

    for record in read_below_the_line_file(btl, num_candidates):
        for pref in record['preferences']:
            pref['candidate'] = DBRef('candidates', pref['candidate'])
        db.belowTheLine.insert(record)

def get_candidates():
    """Get a list and dict of the candidates
    """
    db = pymongo.Connection().federalElections
    candidate_list = []
    candidate_dict = {}
    for x in db.candidates.find():
        cand = Candidate(x['_id'], "%s %s [%s]" % (x['given_names'], x['surname'], x['party']))
        candidate_list.append(cand)
        candidate_dict[x['_id']] = cand
    return candidate_list, candidate_dict

def _split_number(total, amt):
    base = total // amt
    mod = total % amt
    o = []
    for _ in range(amt):
        x = base
        if (mod > 0):
            x +=  1
            mod -= 1
        o.append(x)
    return tuple(o)



def federal_ballots_iterator(state, candidates):
    db = pymongo.Connection().federalElections

    # Yield the above the line votes
    #i = 0
    for record in db.gvt.find({"state": state}):
        #i += 1
        votes = db.firstPrefs.find_one({"state": state, "ticket": record['ticket']})['total']
        split_votes = _split_number(votes, len(record['tickets']))

        for n, ticket in enumerate(record['tickets']):
            for j in range(len(ticket)):
                ticket[j] = candidates[ticket[j]]
            ballot = Ballot("%s (Ticket %s)" % (record['group'], n+1), ticket, split_votes[n])
            yield ballot

    # Yield the below the line votes
    for record in db.belowTheLine.find():
        prefs = record['preferences']
        _dict = {}
        for p in prefs:
            c = db.dereference(p['candidate'])
            _dict[p['preference']] = candidates[c['_id']]
        ballot = Ballot("Below the line: Batch %d Paper %d"%(record['batch'],record['paper']), _dict)
        yield ballot

# vim: sw=4:ts=4
