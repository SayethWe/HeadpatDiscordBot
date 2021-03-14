import numpy as np
import random

DEFAULTELOBASE = 3

def fight(team1CR, team2CR):
    r=random.randint(0,team1CR*team1CR+team2CR*team2CR)
    return r<(team1CR*team1CR) #true if team 1 wins

def getOrdinals(votes):
    votes=-np.array(votes)
    N=len(votes)
    index=np.argsort(votes)
    #print(f"{index} sort indices")
    ordinals=np.zeros(N, dtype=np.intc)
    numVotes=0
    currentOrdinal=0
    for i in range(N):
        ind=index[i]
        newVotes=votes[ind]

        if not newVotes==numVotes:
            #new number of votes
            currentOrdinal=i
            numVotes=newVotes
        ordinals[i]=currentOrdinal
        #print(f"position: {i}, index: {ind}, votes: {votes[ind]}, ordinal: {currentOrdinal}")
    #print('for votes {} the ordinals are {}'.format(votes,ordinals))
    return ordinals

def updateCRs(votes, CRs, eloBase=DEFAULTELOBASE):
    N=len(votes)
    ordinals=getOrdinals(votes)
    mid=int(np.max(votes)/2)
    #use ELO-like method to update CRs
    totalCR=np.sum(CRs)
    newCR=np.round(((totalCR-CRs)+eloBase*(mid-ordinals))/(N-1))
    #print("updateCR:\n{} CRs\n{} votes\n{} ordinals\n{} result".format(CRs, votes, ordinals, newCR))
    return newCR

def pull(contestants, CRs, tickets : int):
    precisionFactor=8; #helps keep numeric precision
    CRs=np.array(CRs)
    names=np.array(names)
    weights=precisionFactor*CRs/tickets*np.exp((tickets-CRs)/tickets)
    #print(weights)
    weightSum=np.sum(weights)
    probs=weights/weightSum
    #print(probs)
    pull=np.random.choice(names,1,False,probs)
    return pull
