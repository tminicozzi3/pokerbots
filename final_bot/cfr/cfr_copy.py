#framework to perform the simulation

#fix isNodeinDict: DONE

#Getting some version of the bot working
#ALL TONIGHT
from skeleton.states import RoundState
import random
import eval7
import pandas as pd
import numpy as np

RANKINGSMAPPINGS = {12: "A", 11: "K", 10: "Q", 9: "J", 8: "T", 7: "9", 6: "8", 5: "7", 4: "6", 3: "5", 2: "4", 1: "3", 0: "2" }
SUITMAPPINGS = {0: "c", 1: "d", 2: "h" , 3: "s"}

nodeDict = {}
nodeHistories = [()]
deck = eval7.Deck()
deck.shuffle()

decksList = []
commCardsList = []
currDeckInd = 0
globalCurrInd = 0

class Node:
    '''
        A node is made up of action history (i.e.: 'bppbp')
        - has functions to update the strategy for that node
        - returns the average strategy for that node 
    '''
    def __init__(self, infoSet):

        #strategy is in form ()
        self.infoSet = infoSet
        self.regretSum = [0, 0, 0]
        self.strategy = [1/3, 1/3, 1/3] #[fold, stay-in, raise] -> stay-in: do whatever is legal between checking and calling.
        self.strategySum = [0, 0, 0]
        self.strategyList = []
        self.currStratInd = -1
        self.stratIndexes = {}

    def makeStrategy(self, reachProbability):
        '''
            returns list: strategy for this node 
        '''
        normalizingSum = 0
        #update strategy according to action proportion in regretSum
        for actionInd in range(0,3):
            if self.regretSum[actionInd] > 0:
                self.strategy[actionInd] = self.regretSum[actionInd]
            normalizingSum += self.strategy[actionInd]

        for actionInd in range(0,3):
            if (normalizingSum >0): 
                self.strategy[actionInd] /= normalizingSum
            self.strategySum[actionInd] += reachProbability * self.strategy[actionInd]
        self.strategyList.append(self.strategy)
        self.currStratInd += 1
        return self.strategy
        
    def setStrategyInd(self, num):
        self.currStratInd = num
    def getStrategyInd(self):
        return self.currStratInd
    def getStrategyFromList(self, ind):
        return self.strategyList[ind]
    def getStrategyList(self):
        return self.strategyList
    def getInfoSet(self):
        return self.infoSet
    def addToIndexes(self, infoSet, index):
        self.stratIndexes[infoSet] = index 
    def getIndexfromDict(self, infoSet):
        return self.stratIndexes[infoSet]
    def getIndDict(self):
        return self.stratIndexes
    def getAverageStrategy(self):
        ''' 
            return list:  average strategy over all iterations
        '''
        avgStrategy = [1/3, 1/3, 1/3]
        normalizingSum = 0
        #update strategy according to action proportion in regretSum
        for actionInd in range(0,3):
            normalizingSum += self.strategySum[actionInd]
        for actionInd in range(0,3):
            if (normalizingSum >0): 
                avgStrategy[actionInd] = self.strategySum[actionInd]/ normalizingSum
        return avgStrategy

    def addToRegretSum(self, actionInd, regret, reachProb):
        #actions = [fold, stay-in, raise]
        if actionInd == 0:
            self.regretSum[0]+= reachProb*regret
        elif actionInd == 1: self.regretSum[1]+= reachProb*regret
        else: self.regretSum[2]+= reachProb*regret

    def toString(self):
        #returns tuple 
        return 'Node: {infoSet}, Average Strategy: {avgStrat}'.format(infoSet = self.infoSet, avgStrat = self.getAverageStrategy())
    
    def cardsToString(self):
        cards = ''
        for card in self.infoSet[0]:
            cards += (str(card) + ' ')
        return cards

    def commCardsToStrings(self):
        communityStr = ''
        if len(self.infoSet) ==3:
            for card in self.infoSet[1]:
                communityStr += (str(card) + ' ')
        return communityStr

def isNodeinDict(infoSet):
    """finds if node is in the nodedictionary

        0: (Ac, Ac)
        1: (Ad, 2c)
    Args:
        bucketNumber (int): 0: pre-flop, 1: flop and onward
        infoSet (tuple): hole cards, community cards (if applicable), and action histories (also if applicable)

    Returns:
        int: index to find that node
    """


    currCards = infoSet[0]
    for node in nodeDict.keys():
        nodeCards = node[0]
        if len(infoSet) != len(node): continue
        if all([card in nodeCards for card in currCards]):
            if len(infoSet) == 2:
                return node
            elif len(infoSet) == 3:
                if (infoSet[2] == node[2]):
                    currCommCards = infoSet[1]
                    nodeCommCards = node[1]
                    if all([card in nodeCommCards for card in currCommCards]):
                        return node
    return None
        
        
    
def convertDecktoList(deck):
    '''
        takes in Deck, returns list of cards in Deck
    '''
    returnable = []
    for card in deck:
        returnable.append(card)
    
    return returnable

def findNodeinNodeHistory(infoSet,nodesHistory):

    # currCards = infoSet[0]
    # for node in nodesHistory:
    #     nodeInfoSet = node[0]
    #     nodeCards = nodeInfoSet[0]
    #     if all([card in nodeCards for card in currCards]):
    #         if len(infoSet) != len(nodeInfoSet): continue
    #         elif len(infoSet) == 2:
    #             return nodeInfoSet
    #         elif len(infoSet) == 3:
    #             if (infoSet[2] == node[2]):
    #                 currCommCards = infoSet[1]
    #                 nodeCommCards = nodeInfoSet[1]
    #                 if all([card in nodeCommCards for card in currCommCards]):
    #                     return nodeInfoSet
    # return None
    currCards = infoSet[0]
    for node in nodesHistory:
        if len(infoSet) != len(node[0]): continue
        if all([card in node[0][0] for card in currCards]): 
            if len(infoSet) ==2:
                return node[1]
            elif len(infoSet) == 3:
               if (infoSet[2] == node[0][2]):
                   currCommCards = infoSet[1]
                   nodeCommCards = node[0][1]
                   if all([card in nodeCommCards for card in currCommCards]):
                       return node[1]
    return None
def cfr(currHistoryInd, bucketNumber, currDeckInd, currCommInd, hole, chipsLeft, prevBets, cumBets, history, p0, p1):

    """ Executes counterfactual regeret minimization algorithm
            1st part: is node terminal?
            2nd part: if node is nont terminal, creates new node and executes strategy calculation
            3rd part: calls cfr for next branches of the game tree 

    Args:
        bucketNumber (int): 0: pre-flop, 1: flop and onward
        currDeckInd (int): keeps track of which version of the deck the current iteration has to use
        currCommInd (int): keeps track of which version of the community cards the current iteration has to use
        hole (list): list of player and opponent hole cards
        chipsLeft (int): number of chips left per iteration for each player
        prevBets (int): number of chips bet in the previous iteration by each player
        cumBets (int): number of money contributed by each player in the pot
        history (string): string of action histories
        p0 (float): probability of player 0 reaching current node
        p1 (float): probability of player 1 reaching current node

    Returns:
        _type_: _description_
    """

    #TO DO: update cfr method to take input deck every time

    plays = len(history)
    player = plays %2
    opponent = 1-player
    
    if len(nodeHistories) >0:
        nodeHistory = nodeHistories[currHistoryInd]
    else:
        nodeHistory = ()
        nodeHistories.append(())
    playerUtil = cumBets[player]
    OpponentUtil = cumBets[opponent]
    
    commCards = commCardsList[currCommInd]
    deck = decksList[currDeckInd]

    
    numOfCommCards = 0
    isCardRed = None
    isCardBlack = None
    isBettingOver = (history[-2:] == 'rs' or history[-2:] == 'ss')
    #if we have reached terminal node 
    if plays >0:
        numOfCommCards = len(commCards)
        if numOfCommCards >= 3:
            lastCommCard = commCards[-1]
            isCardRed = (lastCommCard.suit == 1 or lastCommCard.suit == 2)
            isCardBlack = not isCardRed
            isBettingOver = (history[-2:] == 'rs' or history[-2:] == 'ss')

        terminalFoldFlag = False
        if history[-1:] == 'f':
            terminalFoldFlag = True  
        
        isDeckEmpty = False
        if len(deck) ==0: isDeckEmpty = True
           
        doubleBetFlag = False
        isLastBettingRound = (isBettingOver and (isCardBlack and numOfCommCards>=5))
        isPlayerBroke = ((prevBets[player] > chipsLeft[player]) or (prevBets[opponent] > chipsLeft[opponent]))
        if (isLastBettingRound or isPlayerBroke):
            doubleBetFlag = True 

        #evaluate who wins the round
        isPlayerHandHigher = False  
        playerScore = eval7.evaluate(hole[player] + commCards)
        opponentScore = eval7.evaluate(hole[opponent] + commCards)
        if playerScore > opponentScore:
            isPlayerHandHigher = True 
        
        if terminalFoldFlag:
            return playerUtil
        elif doubleBetFlag or isDeckEmpty:
            if isPlayerHandHigher == True: return -1*OpponentUtil
            else: return playerUtil
    
    #create infoSet: (hole cards, commCards, history)
    if bucketNumber == 0:
        infoSet = (tuple(hole[player]), history)
    elif bucketNumber ==1:
        infoSet = (tuple(hole[player]), tuple(commCards), history)
    

    #Get information set node or create if nonexistant
    nodeVal = isNodeinDict(infoSet)
    if nodeVal == None:
        currNode = Node(infoSet)
        nodeDict[infoSet] = currNode
    else: 
        currNode = nodeDict[nodeVal]
    #DEBUG:
    
    
    #recursively call cfr with additional history and probability
    if player == 0: currNode.makeStrategy(p0) 
    else: currNode.makeStrategy(p1)

    util = [0, 0, 0]
    nodeUtil = 0
    
    AreCommCardsChanged = False
    if (isBettingOver and ((isCardRed and (numOfCommCards >=5)) or (numOfCommCards < 5))):
        AreCommCardsChanged = True
        if numOfCommCards < 3:
            newDeck = deck.copy()
            newCommCards = [newDeck.pop(), newDeck.pop(), newDeck.pop()]
        else:
            newCommCards = commCards.copy()
            newDeck = deck.copy()
            newCommCards.append(newDeck.pop())

        decksList.append(newDeck)
        commCardsList.append(newCommCards)

    newBucketNumber = bucketNumber
    if numOfCommCards >= 3: newBucketNumber = 1

    nodeHistories.insert(currHistoryInd+1, nodeHistory + ((currNode.getInfoSet(), currNode.getStrategyInd()),))
    # currNode.addToIndexes(infoSet, )
    print((nodeHistory, bucketNumber, currDeckInd, currCommInd, nodeVal, chipsLeft, prevBets, cumBets, history, p0, p1))
    # if nodeVal == ((eval7.Card("Ac"), eval7.Card("Ad")), ''):
        # print(nodeDict[nodeVal].getStrategyList())
        # print(prevBets[player], cumBets[player])
    currNode.addToIndexes(infoSet, currNode.getStrategyInd())
    print(currNode.getIndDict())
    #ADD THING!
    for action in range (0,3):
        #actions = [fold, stay-in, raise]
        # print(infoSet, nodeHistories[currHistoryInd+1])
        if action == 0:
            nextHistory = history + 'f'
            nextChipsLeft = chipsLeft
            nextBets = prevBets
            nextCumBets = cumBets
        elif action == 1: 
            #stay-in: nextBet is the opponent's prevBet
            nextHistory = history + 's'
            nextBets = (prevBets[opponent], prevBets[opponent])
            if player == 0:
                nextChipsLeft = (chipsLeft[0] - nextBets[0], chipsLeft[1])
                nextCumBets = (cumBets[0]+nextBets[0], cumBets[1])
            else:
                nextChipsLeft = (chipsLeft[0], chipsLeft[1]-nextBets[1])
                nextCumBets = (cumBets[0], cumBets[1]+nextBets[1])
        else:
            nextHistory = history + 'r'
            if player == 0:
                nextBets = (100, prevBets[opponent])
                nextChipsLeft = (chipsLeft[0] - 100, chipsLeft[1])
                nextCumBets = (cumBets[0]+nextBets[0], cumBets[1])
            else:
                nextBets = (prevBets[opponent], 100)
                nextChipsLeft = (chipsLeft[0], chipsLeft[1]-100)
                nextCumBets = (cumBets[0], cumBets[1]+nextBets[1])
        
        #update playerProfiles 
        # print('currHistoryInd: {currHistoryInd}, currNode: {currNode}, infoSet: {infoSet}, Conditional: {conditional}, '.format(currHistoryInd = currHistoryInd,currNode = currNode, infoSet = infoSet, conditional = findNodeinNodeHistory(infoSet, nodeHistories[currHistoryInd+1]))) 
        # print(nodeHistories)
        
        if AreCommCardsChanged:
            if player == 0: 
                if bucketNumber == 0:
                    util[action] = -1* cfr(currHistoryInd+1, newBucketNumber, currDeckInd +1, currCommInd +1, hole, nextChipsLeft, nextBets, nextCumBets, nextHistory, p0*currNode.getStrategyFromList(currNode.getIndexfromDict((tuple(hole[len(history)%2]), history)))[action], p1)
                    nodeUtil += currNode.getStrategyFromList(currNode.getIndexfromDict((tuple(hole[len(history)%2]), history)))[action] * util[action]
                elif bucketNumber ==1:
                    util[action] = -1* cfr(currHistoryInd+1, newBucketNumber, currDeckInd +1, currCommInd +1, hole, nextChipsLeft, nextBets, nextCumBets, nextHistory, p0*currNode.getStrategyFromList(currNode.getIndexfromDict((tuple(hole[len(history)%2]), tuple(commCardsList[currCommInd]), history)))[action], p1)
                    nodeUtil += currNode.getStrategyFromList(currNode.getIndexfromDict((tuple(hole[len(history)%2]), tuple(commCardsList[currCommInd]), history)))[action] * util[action]
            else: 
                if bucketNumber == 0:
                    util[action] = -1* cfr(currHistoryInd+1, newBucketNumber, currDeckInd +1, currCommInd +1, hole, nextChipsLeft, nextBets, nextCumBets, nextHistory, p0, p1*currNode.getStrategyFromList(currNode.getIndexfromDict((tuple(hole[len(history)%2]), history)))[action])
                    nodeUtil += currNode.getStrategyFromList(currNode.getIndexfromDict((tuple(hole[len(history)%2]), history)))[action] * util[action]
                elif bucketNumber ==1:
                    util[action] = -1* cfr(currHistoryInd+1, newBucketNumber, currDeckInd +1, currCommInd +1, hole, nextChipsLeft, nextBets, nextCumBets, nextHistory, p0, p1*currNode.getStrategyFromList(currNode.getIndexfromDict((tuple(hole[len(history)%2]), tuple(commCardsList[currCommInd]), history)))[action])
                    nodeUtil += currNode.getStrategyFromList(currNode.getIndexfromDict((tuple(hole[len(history)%2]), tuple(commCardsList[currCommInd]), history)))[action] * util[action]
        else:
            if player == 0: 
                if bucketNumber == 0:
                    util[action] = -1* cfr(currHistoryInd+1, newBucketNumber, currDeckInd, currCommInd, hole, nextChipsLeft, nextBets, nextCumBets, nextHistory, p0*currNode.getStrategyFromList(currNode.getIndexfromDict((tuple(hole[len(history)%2]), history)))[action], p1)
                    nodeUtil += currNode.getStrategyFromList(currNode.getIndexfromDict((tuple(hole[len(history)%2]), history)))[action] * util[action]
                elif bucketNumber ==1:
                    util[action] = -1* cfr(currHistoryInd+1, newBucketNumber, currDeckInd, currCommInd, hole, nextChipsLeft, nextBets, nextCumBets, nextHistory, p0*currNode.getStrategyFromList(currNode.getIndexfromDict((tuple(hole[len(history)%2]), tuple(commCardsList[currCommInd]), history)))[action], p1)
                    nodeUtil += currNode.getStrategyFromList(currNode.getIndexfromDict((tuple(hole[len(history)%2]), tuple(commCardsList[currCommInd]), history)))[action] * util[action]
            else: 
                if bucketNumber == 0:
                    util[action] = -1* cfr(currHistoryInd+1, newBucketNumber, currDeckInd, currCommInd, hole, nextChipsLeft, nextBets, nextCumBets, nextHistory, p0, p1*currNode.getStrategyFromList(currNode.getIndexfromDict((tuple(hole[len(history)%2]), history)))[action])
                    nodeUtil += currNode.getStrategyFromList(currNode.getIndexfromDict((tuple(hole[len(history)%2]), history)))[action] * util[action]
                elif bucketNumber ==1:
                    util[action] = -1* cfr(currHistoryInd+1, newBucketNumber, currDeckInd, currCommInd, hole, nextChipsLeft, nextBets, nextCumBets, nextHistory, p0, p1*currNode.getStrategyFromList(currNode.getIndexfromDict((tuple(hole[len(history)%2]), tuple(commCardsList[currCommInd]), history)))[action])
                    nodeUtil += currNode.getStrategyFromList(currNode.getIndexfromDict((tuple(hole[len(history)%2]), tuple(commCardsList[currCommInd]), history)))[action] * util[action]
        
    # nodeUtil += strategy[action] * util[action]
    
    #compute regrets
    for actionInd in range (0,3):
        regret = util[actionInd] - nodeUtil

        if player == 0: currNode.addToRegretSum(actionInd, regret, p1)
        else: currNode.addToRegretSum(actionInd, regret, p0)
    
    return nodeUtil


def trainPoker(iterationNum):

    util = 0
    holeCards = ('Ac', 'Ad')
    holeCardsList = []
    for card in holeCards:
        holeCardsList.append(eval7.Card(card))
    for i in range (iterationNum):
        #shuffle cards
        deck = eval7.Deck()
        deck.shuffle()
        #deal all cards s.t. cards = [ [HOLE_PLAYERZERO, chips_left, prevBet, cumulativeContribution], [HOLE_PLAYERONE, chips_left, prevBet, cumulativeContribution], STREET ]
        decksList.clear()
        commCardsList.clear()
        
        initialDeck = convertDecktoList(deck)
        for card in holeCardsList:
            initialDeck.remove(card)
        commCardsList.append([])
        hole = (holeCardsList, [initialDeck.pop() for card in range(2)])

        decksList.append(initialDeck)

        chipsLeft = (400,400)
        prevBets = (5,5)
        cumBets = (5,5)
            

        util += cfr(0 ,0, 0, 0, hole, chipsLeft, prevBets, cumBets, "", 1, 1)
    print("Average game value: {eV}".format(eV = util/iterationNum))
    # for node in nodeDict.values():
    #       print(node.toString())
    # print(nodeDict[((eval7.Card("Ac"), eval7.Card("Ad")), '')].getAverageStrategy())
    

if __name__ == '__main__':
    iterationNum = 1
    trainPoker(iterationNum)
    holeList = []
    commList = []
    for node in nodeDict:
            history = [node[-1]]
            holeList.append(nodeDict[node].cardsToString())
            commList.append(nodeDict[node].commCardsToStrings())
            nodeDict[node] = history + nodeDict[node].getAverageStrategy()

    
    # tuples = sorted(list(zip(*[holeList, commList, nodeDict.values()])), key=lambda elem: elem[0])
    # vals = [elem[2] for elem in tuples]
    # keys = sorted(list(zip(*[holeList, commList])), key=lambda elem: elem[0])
    # index = pd.MultiIndex.from_tuples(keys, names=["hole", "comm"])
    # df = pd.DataFrame(vals, index = index, columns = ['history', 'fold', 'stay-in', 'raise'])
    # df.to_csv('week-1-bot/cfr/nodes.csv', encoding='utf-8', index = True)
    
    
