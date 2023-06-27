#framework to perform the simulation

from skeleton.states import RoundState
import random


nodeDict = {}

class Node:
    '''
        A node is made up of action history (i.e.: 'bppbp')
        - has functions to update the strategy for that node
        - returns the average strategy for that node 
    '''
    def __init__(self, infoSet):

        #strategy is in form ()
        self.infoSet = infoSet
        self.regretSum = [0, 0]
        self.strategy = [0.5, 0.5]
        self.strategySum = [0, 0]

    def getStrategy(self, reachProbability):
        '''
            returns list: strategy for this node 
        '''
        normalizingSum = 0
        #update strategy according to action proportion in regretSum
        for actionInd in range(0,2):
            if self.regretSum[actionInd] > 0:
                self.strategy[actionInd] = self.regretSum[actionInd]
            normalizingSum += self.strategy[actionInd]

        for actionInd in range(0,2):
            if (normalizingSum >0): 
                self.strategy[actionInd] /= normalizingSum
            self.strategySum[actionInd] += reachProbability * self.strategy[actionInd]
        return self.strategy
    def getAverageStrategy(self):
        ''' 
            return list:  average strategy over all iterations
        '''
        avgStrategy = [0.5, 0.5]
        normalizingSum = 0
        #update strategy according to action proportion in regretSum
        for actionInd in range(0,2):
            normalizingSum += self.strategySum[actionInd]
        for actionInd in range(0,2):
            if (normalizingSum >0): 
                avgStrategy[actionInd] = self.strategySum[actionInd]/ normalizingSum
        return avgStrategy

    def addToRegretSum(self, actionInd, regret, reachProb):
        if actionInd == 0:
            self.regretSum[0]+= reachProb*regret
        else: self.regretSum[1]+= reachProb*regret

    def toString(self):
        #returns tuple 
        return 'Node: {infoSet}, Average Strategy: {avgStrat}'.format(infoSet = self.infoSet, avgStrat = self.getAverageStrategy())

def cfr(cards, history, p0, p1):
    '''
        - takes players cards, action history, and probablities of reaching node for player0 and player 1 as inputs
        - recursive 
        Assumes: String cards, RoundState
                double p0, p1
        
        returns utility given the current history. (This can be thought of as just returning the utiltiy for the node represented by the history inputted)
    '''

    print(cards, history, p0, p1)
    plays = len(history)
    player = plays %2
    opponent = 1-player


    #if we have reached terminal node 
    if plays >1:
        terminalPassFlag = False
        if history[-1] == 'p':
            terminalPassFlag = True  
        
        doubleBetFlag = False
        if history[-2:] == 'bb':
            doubleBetFlag = True 

        isPlayerCardHigher = False  
        if cards[player] > cards[opponent]:
            isPlayerCardHigher = True  
       
        if terminalPassFlag:
            if history == 'pp':
                if isPlayerCardHigher == True: return 1
                else: return -1
            else:
                return 1
        elif doubleBetFlag:
            if isPlayerCardHigher == True: return 2
            else: -2
    infoSet = (cards[player], history)

    #Get information set node or create if nonexistant
    if infoSet not in nodeDict.keys():
        currNode = Node(infoSet)
        nodeDict[infoSet] = currNode
    else: currNode = nodeDict[infoSet]

    #recursively call cfr with additional history and probability
    if player == 0: strategy = currNode.getStrategy(p0) 
    else: strategy = currNode.getStrategy(p1)

    util = [0, 0]
    nodeUtil = 0
    for action in range (0,2):
        if action == 0: nextHistory = history + 'p'
        else: nextHistory = history + 'b'
        
        if player == 0: util[action] = -1* cfr(cards, nextHistory, p0*strategy[action], p1) 
        else: util[action] = -1* cfr(cards, nextHistory, p0, p1*strategy[action]) 
        nodeUtil += strategy[action] * util[action]

    #compute regrets
    for actionInd in range (0,2):
        regret = util[actionInd] - nodeUtil

        if player == 0: currNode.addToRegretSum(actionInd, regret, p1)
        else: currNode.addToRegretSum(actionInd, regret, p0)
    
    return nodeUtil

def trainPoker(iterationNum):
    cards = [1,2,3]
    util = 0
    for iter in range (iterationNum):
        #shuffle cards

        # for c1 in range (len(cards) -1, -1, -1):
        #     c2 = random.randint(0, c1+1)
        #     print(c2)
        #     temp = cards[c1]
        #     cards[c1] = cards[c2]
        #     cards[c2] = temp
        random.shuffle(cards)
        util += cfr(cards, "", 1, 1)
    print("Average game value: {eV}".format(eV = util/iterationNum))
    for node in nodeDict.values():
        print(node.toString())

# if (__name__ == '__main__'):
iterationNum = 1
trainPoker(iterationNum)

