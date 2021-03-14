import numpy as np
import random
import HelpFunctions as hf

DEFAULTELOBASE = 3

def fight(team1CR, team2CR):
    r=random.randint(0,team1CR*team1CR+team2CR*team2CR)
    return r<(team1CR*team1CR) #true if team 1 wins

def getOrdinals(votes):
    votes=np.array(votes)
    N=len(votes)
    index=np.argsort(votes)

    ordinals=np.zeros(N, dtype=np.intc)
    numVotes=0
    currentOrdinal=0
    for i in range(N):
        ind=index[i]
        newVotes=votes[ind]
        if not newVotes==numVotes:
            #new number of votes
            currentOrdinal=ind
            numVotes=newVotes
        ordinals[i]=currentOrdinal
    #print('for votes {} the ordinals are {}'.format(votes,ordinals))
    return ordinals


def updateCR(votes, CRs, eloBase=DEFAULTELOBASE):
    N=len(votes)
    ordinals=getOrdinals(votes)
    mid=int(N/2)
    #use ELO-like method to update CRs
    totalCR=np.sum(CRs)
    newCR=np.round(((totalCR-CRs)+eloBase*(mid-ordinals))/(N-1))
    return newCR

def pull(dbURL, guildID, tickets : int):
    contestants = hf.getContestants(dbURL, guildID)
    precisionFactor=8; #helps keep numeric precision
    CRs=np.array(CRs)
    names=np.array(names)
    weights=precisionFactor*CRs/tickets*np.exp((tickets-CRs)/tickets)
    print(weights)
    weightSum=np.sum(weights)
    probs=weights/weightSum
    print(probs)
    pull=np.random.choice(names,1,False,probs)
    return pull


print(fight(2,1))
print(updateCR([3,5,4],[1,2,1],3))
print(pull(3,[1,2,3,3,4,5,6],["a","b","c","d","e","f","g"]))
