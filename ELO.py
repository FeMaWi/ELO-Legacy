# -*- coding: utf-8 -*-
"""
Created on Wed Oct 19 12:57:14 2022

@author: Felix
"""


"Variables"

"Max win/loss rating change"
kValue = 32

"How much impact has the rank difference on the win prob"
scaleValue = 400

"Number of provisional games to be played in order to become established"
provGameNbr = 8

"Discriminate if provisional ELO calculation is needed"
def rankUpdate (rankA, result, rankB, nbrOfMatchesA="None", nbrOfMatchesB="None"):
    updateRankA = 0
    updateRankB = 0
    resultS = 2*(result-0.5)
    if nbrOfMatchesA == "None" and nbrOfMatchesB == "None":
        updateRankA, updateRankB = fullEstablishedUpdate(rankA, result, rankB)
        
    elif nbrOfMatchesA == "None" and type(nbrOfMatchesB) == int:
        updateRankA = establishedPlayerUpdate(rankA, result, rankB, nbrOfMatchesB)
        updateRankB = provisionalPlayerUpdate(rankB, nbrOfMatchesB, -resultS, rankA)
        
    elif type(nbrOfMatchesA) == int and nbrOfMatchesB == "None":
        updateRankA = provisionalPlayerUpdate(rankA, nbrOfMatchesA, resultS ,rankB)
        updateRankB = establishedPlayerUpdate(rankB, 1-result ,rankA, nbrOfMatchesA)
        
    else:
        updateRankA, updateRankB = fullProvisionalUpdate(rankA, resultS, rankB, nbrOfMatchesA, nbrOfMatchesB)
        
    return updateRankA, updateRankB
        
"Calculation of the win probabilities depending on rank difference"
def winProbability(rankA, rankB):
    winProb = 1/(1+pow(10,((rankB-rankA)/scaleValue)))
    return winProb

"Normal update for established players"
"result : [1, 0.5, 0] for win/draw/loss of player A"
"return : list of updated ranks for player A and B depending on the result"

def fullEstablishedUpdate (rankA, result, rankB):
    winProb = winProbability(rankA, rankB)
    updateRankA = rankA + round(kValue * (result - winProb))
    updateRankB = rankB + round(kValue * (winProb - result))
    return updateRankA, updateRankB


"Update for two provisional players"
def fullProvisionalUpdate(rankA, resultS, rankB, nbrOfMatchesA, nbrOfMatchesB):
    updateRankA = round((rankA*nbrOfMatchesA + (rankA+rankB)/2 + 100*resultS)/(nbrOfMatchesA+1))
    updateRankB = round((rankB*nbrOfMatchesB + (rankB+rankA)/2 - 100*resultS)/(nbrOfMatchesB+1))
    return updateRankA, updateRankB

"""Update rules for one provisional and one established player"""
"Update for the provisional player"
def provisionalPlayerUpdate(rankProv, nbrOfMatchesProv, resultS, rankEst):
    updateProv = round((rankProv*nbrOfMatchesProv + rankEst + 200*resultS)/(nbrOfMatchesProv+1))
    return updateProv

"Update for the established player"
def establishedPlayerUpdate(rankEst, result, rankProv, nbrOfMatchesProv):
    winProb = winProbability(rankEst, rankProv)
    updateEst = round(rankEst + kValue * (nbrOfMatchesProv/provGameNbr) * (result - winProb))
    return updateEst