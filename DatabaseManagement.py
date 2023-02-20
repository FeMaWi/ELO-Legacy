
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 27 11:24:09 2022

@author: Felix
"""

from datetime import datetime

import ZODB
import ZODB.FileStorage
import ZODB.DB
import transaction
from persistent import Persistent
import matplotlib.pyplot as plt

import ELO
import TM_util
import GitHubInterface



"Class administrating the database connection"
class dbConnection:
    
    def __init__(self, dbName):
        self.dbName = dbName
        self.storage = ZODB.FileStorage.FileStorage(self.dbName)
        self.db = ZODB.DB(self.storage)
        self.connection = self.db.open()
        self.root = self.connection.root()
        print("Connection established")
    
    "Connects to GitRepo storing the database"
    def upload(self, access):
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        commit_message = "Database Update: " + now
        files_to_upload = [self.dbName, "Leaderboard.json"]
        
        GitHubInterface.uploadDatabase(access, files_to_upload, commit_message)
    
    "Downloads the Filestorage -> split environment and content"
    def download(self):
        GitHubInterface.downloadDatabase(self.dbName)
        
    def __del__(self):
        self.close()
        
    def close(self):
        self.connection.close()
        self.db.close()
        print("Connection closed")

"A match is defined by date, number of players and the list of player names ordered by placement"
class Match(Persistent):
    
    def __init__(self, matchDate, listOfPlaces, score="None", additionalPlayerInfo="None", expansions="None"):
        self.matchDate      = matchDate
        self.endResult      = []
        self.expansions     = []
        for player in listOfPlaces:
            self.endResult.append([player])
        self.playerCount    = len(self.endResult)
        
        "If scores are passed, add them to the players"
        if score!="None":
            if type(score)==list:
                if len(score)==len(listOfPlaces):
                    for idx, x in enumerate(score):
                        self.endResult[idx].append(x)
                else:
                    print("Mismatch of players and number of scores.")
                    
        if additionalPlayerInfo!="None":
            if type(additionalPlayerInfo)==list:
                if len(additionalPlayerInfo)==len(listOfPlaces):
                    for idx, x in enumerate(additionalPlayerInfo):
                        self.endResult[idx].append(x)
                else:
                    print("Mismatch of players and number of additional info entries.")
                    
        "An optional list of expansions used for the match"
        if expansions!="None":
            if type(expansions)==list:
                self.expansions     = expansions
            
    "For example for print() calls" 
#    def __repr__(self):
#        return f'Match({self.matchDate},{self.endResult})'
    
    def __repr__(self):
        return str(self.__dict__)
    
    "Returns only the names of the Players"
    def getResult(self):
        return [player[0] for player in self.endResult]
    
    def getExpansions(self):
        return self.expansions
    
    def printMatch(self):
        print()
        print("Date: %s" % self.matchDate)
        for player in self.endResult:
            print(f'{player[0]:15} {player[1]:4} {player[2]:20}')
    
    "Returns the Match data ready to be entered in a CSV file"
    "Format: date, all the places with score and additional info, expansions"
    def csvOutput (self, maxPlayers=5):
        outputList = [self.matchDate]
        for playerResult in self.endResult:
            for entry in playerResult:
                outputList.append(entry)
        for i in range(3*(maxPlayers - len(self.endResult))):
            outputList.append("")
        for i in range(1,5):
            outputList.append(TM_util.nameOfExpansions[i] in self.getExpansions())
        outputList.append([x for x in self.getExpansions() if x not in list(TM_util.nameOfExpansions.values())][0])
        return outputList
        
    
"A player is defined by name, history of rank and number of matches"
class Player(Persistent):
    
    def __init__(self, name):
        self.name           = name
        self.ELOrank        = [1500]
        self.nbrOfMatches   = 0
        
#    def __repr__(self):
#        return repr((self.name,self.ELOrank[-1],self.nbrOfMatches))

    def __repr__(self):
        return str(self.__dict__)
    
    def currentRank(self):
        return self.ELOrank[-1]


class LeaderBoard(Persistent):
    """Head Object that gathers players and matches"""
        
    def __init__(self, nameOfGame, rankingSystem='ELO'):
        self.nameOfGame     = nameOfGame
        self.rankingSystem  = rankingSystem
        "List of Matches"
        self.matchHistory   = []
        "Dict of Players"
        self.playerList     = {}
    
    "Prints the name of the leaderboard"
    def __call__(self):
       return self.nameOfGame
        
    def __repr__(self):
        return f'Leaderboard for {self.nameOfGame} with {len(self.playerList)} Players and {len(self.matchHistory)} Matches.'

    "Returns a list of all players, decendingly sorted by rank/matches"
    def sortedPlayerList(self, ordering="rank"):
        if ordering=="rank":
            sortedList = sorted(list(self.playerList.values()), key = lambda player : player.ELOrank[-1], reverse = True)
        elif ordering=="matches":
            sortedList = sorted(list(self.playerList.values()), key = lambda player : player.nbrOfMatches, reverse = True)
        return sortedList
    
    "Shows a list of players with respective ELO rank"
    def showPlayer(self):
        print()
        print("The game %s currently has %d players and %d matches played:" % (self.nameOfGame, len(self.playerList), len(self.matchHistory)))
        sortedByRank = self.sortedPlayerList("rank")
        for i in sortedByRank:
            print("Player: %s with Rank %d" % (i.name, i.ELOrank[-1]))
          
    "Plots the development of the ELO number of specific players in a leaderboard"
    def plotSpecELO(self, playersToPlotList, normalized = True):
        playerObjectList = map(lambda player: self.playerList[player], playersToPlotList)
        fig, ax = plt.subplots()
        for player in playerObjectList:
            "Only plot players that have played at least one game"
            if normalized and len(player.ELOrank)==1:
                continue
            Yaxis = player.ELOrank
            if normalized:
                nbrPoints = len(Yaxis)
                Xaxis = list(range(nbrPoints))
                for i in range(nbrPoints):
                    Xaxis[i] /= nbrPoints-1
                ax.plot(Xaxis, Yaxis, label=player.name)
            else:
                ax.plot(Yaxis, label=player.name)
            plt.ion()
        
        if normalized:
            ax.set_xlabel("Number of matches normalized to 1")
        else:
            ax.set_xlabel("Number of matches")
        ax.set_ylabel("ELO")
        ax.set_title("Player Ranks for %s" % self.nameOfGame)
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0.)
        plt.show()
        return
    
    "Plots the development of the ELO number of all players in a leaderboard"
    def plotELO(self, normalized = True):
        self.plotSpecELO(list(self.playerList.keys()),normalized)
        return
    
    
    "Deletes the last added game in case of typos and stuff"
    def deleteLastMatch (self):
        if len(self.matchHistory) > 0:
            deletedGame = self.matchHistory.pop()
            for player in deletedGame.getResult():
                self.playerList[player].ELOrank.pop()
                self.playerList[player].nbrOfMatches -= 1
            self._p_changed = True
            transaction.commit()
            print("Match %s between players %s was deleted!" % (deletedGame.matchDate, deletedGame.getResult()))
            return
        else:
            print("No more Matches to delete")
    
    "Add a new player to the list of players"
    def addPlayer (self, name):
        if name=="":
            print()
            print("A player needs a name")
            print()
        elif name in self.playerList:
            print()
            print("A player of that name already exists")
            print()
        else:
            self.playerList[name] = Player(name)
            self._p_changed = True
            print()
            print("Player %s added to the player list for %s" % (name, self.nameOfGame))
            transaction.commit()

    "Add a new Match to the match history and" 
    "calculate the new ranks for the players that took part"
    def addMatch (self, date, listOfPlaces, score="None", additionalPlayerInfo="None", expansions="None"):
        if len(listOfPlaces) < 2 :
            print("A match needs at least two players!")
            return
        for player in listOfPlaces:
            if player not in self.playerList:
                print("Player %s is not in the list of players for %s." % (player, self.nameOfGame))
                print("Add the player to the player list and try again.")
                return
        newMatch = Match(date, listOfPlaces, score, additionalPlayerInfo, expansions)
        self.matchHistory.append(newMatch)
        self.calcNewRank(newMatch)
        self._p_changed = True
        transaction.commit()
        print("New Match with %d players added." % newMatch.playerCount)

    "Calculates and adjusts the player ranks. Takes a Match"
    def calcNewRank (self, match):
        resultList  = match.getResult()
        resultLen   = len(resultList)
        rankUpdates = {}
        for i in resultList:
            rankUpdates[i] = 0
            self.playerList[i].nbrOfMatches += 1
        "Go through every individual matchup"
        matchups = [(x,y) for x in range(0,resultLen) for y in range(x,resultLen) if x!=y]
        for individual in matchups:
            winner      = resultList[individual[0]]
            loser       = resultList[individual[1]]
            winnerGames = "None" if self.playerList[winner].nbrOfMatches > ELO.provGameNbr else self.playerList[winner].nbrOfMatches
            loserGames  = "None" if self.playerList[loser].nbrOfMatches > ELO.provGameNbr else self.playerList[loser].nbrOfMatches
            updateTemp  = ELO.rankUpdate(self.playerList[winner].currentRank(), 1, self.playerList[loser].currentRank(), winnerGames, loserGames)
            rankUpdates[winner] += updateTemp[0]
            rankUpdates[loser]  += updateTemp[1]
        for i in rankUpdates:
            self.playerList[i].ELOrank.append(rankUpdates[i]/(resultLen-1))

    "Predicts the outcome of a matchup from the ELO rating of the players"
    def compareMatchup (self, player1, player2):
        rankPlayer1 = self.playerList[player1].currentRank()
        rankPlayer2 = self.playerList[player2].currentRank()
        winPercentage = round(100*ELO.winProbability(rankPlayer1, rankPlayer2))
        print("Predicted winrates: %s %d : %d %s" %(player1, winPercentage, 100-winPercentage, player2))

    def jointMatch (self, player1, player2, nbrOfMatches=10):
        i = 0
        for match in list(reversed(self.matchHistory)):
            if (player1 in match.getResult() and player2 in match.getResult()):
                if i >= nbrOfMatches: break
                i += 1
                match.printMatch() 
        if i == 0:
            print("No joint matches between %s and %s so far." % (player1, player2))        

    def getJSON(self):
        for player in self.playerList.values():
            if (player.name == None):
                continue
        for matches in self.matchHistory:
            if matches.matchDate == None:
                continue
        JSONstring = str(self.__dict__)
        JSONstring = JSONstring.replace("'",'"')
        return JSONstring
    
    def storeJSON(self, filename="Leaderboard.json"):
        f = open(filename, "w")
        f.write(self.getJSON())
        f.close()
    
"Creates a new leaderboard"
def createLeaderBoard(dbRoot, newBoard = "None"):
    if newBoard == "None":
        print("What is the name of the game?")
        newBoard = input("Game: ")
        
    if newBoard in dbRoot:
        print("A leaderboard for this game already exists!")
    else:
        dbRoot[newBoard] = LeaderBoard(newBoard)
        print("Leaderboard for %s created." % newBoard)
        transaction.commit()
    return

"Opens a dialog to select a game"
def selectLeaderBoard(dbRoot, selectBoard = "None"):
    
    if selectBoard != "None":
        if selectBoard in dbRoot:
            selected = dbRoot[selectBoard]
            print("You are now logged into %s's Leaderbord." % selected.nameOfGame)
            return selected
        else:
            print("%s does not appear in the list of available Leaderboards." % selectBoard)
            
    numberOfBoards = len(dbRoot)
    if numberOfBoards == 0:
        print("No Leaderboard.")
        print("To create a new Leaderboard, type the name of the game: ")
        usrInp = input()
        createLeaderBoard(dbRoot, usrInp)
        selected = dbRoot[usrInp]
    elif numberOfBoards == 1:
        print("There is only one available board.")
        selected, = dbRoot.values()
    else:
        print()
        print("Available Games:")
        print()
        for i in dbRoot:
            print(i)
        gameInput = input("Which Leaderboard would you like to open? ")   
        try:
            selected = dbRoot[gameInput]
        except KeyError:
            print()
            print("No such Leaderboard")
            print()
            return
        print()
    print("You are now logged into %s's Leaderbord" % selected.nameOfGame)
    return selected

if  __name__=="__main__":
    
    database = dbConnection('TheRealShit.fs')
    selected = selectLeaderBoard(database.root)
    
    while 1:
        
        print()
        choice=input("Press 'M' to add a detailed match, "
                     "'S' to show the leaderboard, "
                     "'H' for additional commands or 'Q' to quit: ")
        choice=choice.lower()
        
        if choice=="m-":
            date = input("What date/catch phrase of the match: ")
            inputPlaces = []
            nameOfPlaces = {1:"First place: ", 2: "Second place: ", 3:"Third place: ", 4:"Forth place: ", 5:"Fifth place: ", 6:"Sixth place: "}
            while True:
                nextPlace = input(nameOfPlaces[len(inputPlaces)+1])
                if nextPlace == "": break
                inputPlaces.append(nextPlace)
            selected.addMatch(date,inputPlaces)
            
        elif choice=="m":
            date = input("What date/catch phrase of the match: ")
            inputPlaces = []
            inputScore = []
            inputAdditionalInfo = []
            inputExpansions = []
            nameOfPlaces = {1:"First place: ", 2: "Second place: ", 3:"Third place: ", 4:"Forth place: ", 5:"Fifth place: ", 6:"Sixth place: "}
            while True:
                nextPlace = input(nameOfPlaces[len(inputPlaces)+1])
                if nextPlace == "": break
                nextScore = input("Score: ")
                nextInfo = input("Additional Information: ")
                inputPlaces.append(nextPlace)
                inputScore.append(nextScore)
                inputAdditionalInfo.append(nextInfo)
            while True:
                nextExpansion = input("Add an expansion: ")
                if nextExpansion == "": break
                inputExpansions.append(nextExpansion)
            selected.addMatch(date, inputPlaces, score=inputScore, additionalPlayerInfo=inputAdditionalInfo, expansions=inputExpansions)
            
        elif choice=="s":
            selected.showPlayer()
            
        elif choice=="a":
            newPlayer = input("New player for %s: " % selected.nameOfGame)
            selected.addPlayer(newPlayer)
            
        elif choice=="p":
            selected.plotELO(False)
            
        elif choice=="c":
            print("Select two players to compare winrates!")
            player1 = input("First player: ")
            player2 = input("Second player: ")
            try:
                selected.compareMatchup(player1,player2)
            except KeyError:
                print("One of the players does not exist")
            
        elif choice=="v":
            player = input("View rank history of player: ")
            try:
                print(selected.playerList[player].ELOrank)
            except KeyError:
                print("Player does not exist")
                
        elif choice=="j":
            print("List of games shared by two players!")
            player1 = input("First player: ")
            player2 = input("Second player: ")
            try:
                selected.jointMatch(player1,player2)
            except KeyError:
                print("One of the players does not exist")
            
        elif  choice=="h":
            print("List of all commands:")
            print("m : Add a match with detailed information")
            print("m-: Add a match fast")
            print("s : Show the leaderboard")
            print("p : Plot the leaderboard")
            print("v : View a players ELO history")
            print("a : Add a player")
            print("c : Compare win probabilites of two players")
            print("j : Show joint match history of two players")
            print("c : Change leaderboard")
            print("l : Create new leaderboard")
            print("q : Exit")
        
        elif choice=="c":
            selected=selectLeaderBoard()
            
        elif choice=="l":
            createLeaderBoard()
            
        elif choice=="delete":
            selected.deleteLastMatch()
            
        elif choice=="q":
            break

    # close database
    #database.__del__()