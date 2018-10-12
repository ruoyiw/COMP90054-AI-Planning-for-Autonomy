# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from captureAgents import CaptureAgent
import random, time, util
from game import Directions, Actions
import game
from util import nearestPoint
import sys

sys.path.append('teams/RealDaddy/')


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first='Attacker', second='Defender'):
    """
    This function should return a list of two agents that will form the
    team, initialized using firstIndex and secondIndex as their agent
    index numbers.  isRed is True if the red team is being created, and
    will be False if the blue team is being created.

    As a potentially helpful development aid, this function can take
    additional string-valued keyword arguments ("first" and "second" are
    such arguments in the case of this function), which will come from
    the --redOpts and --blueOpts command-line arguments to capture.py.
    For the nightly contest, however, your team will be created without
    any extra arguments, so you should make sure that the default
    behavior is what you want for the nightly contest.
    """

    # The following line is an example only; feel free to change it.
    return [eval(first)(firstIndex), eval(second)(secondIndex)]


##########
# Agents #
##########

class BasedAgent(CaptureAgent):
    def getSuccessor(self, gameState, action):

        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        if pos != nearestPoint(pos):
            return successor.generateSuccessor(self.index, action)
        else:
            return successor

    def evaluate(self, gameState, action):

        features = self.getFeatures(gameState, action)
        weights = self.getWeights(gameState, action)
        return features * weights

    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        features['successorScore'] = self.getScore(successor)
        return features

    def getWeights(self, gameState, action):
        return {'successorScore': 1.0}

class Node:
    def __init__(self, data):
        self.data = data
        self.children = []


    def getData(self):
        return self.data

    def setData(self, data):
        self.data = data

    def getChildren(self):
        return self.children

    def add(self, node):
        if len(self.children) == 4:
            return False
        else:
            self.children.append(node)


    def go(self, data):
        for child in self.children:
            if child.getData() == data:
                return child
        return None

class Tree:

    def __init__(self, head):
        self.head = Node(head)
        self.num = 0

    def linkToHead(self, node):
        self.head.add(node)

    def insert(self, path, data):
        cur = self.head
        for step in path:
            if cur.go(step) == None:
                return False
            else:
                cur = cur.go(step)
        cur.add(Node(data))
        return True

    def searchAndUpdate(self, path, data):
        cur = self.head
        for step in path:
            if cur.go(step) == None:
                return None
            else:
                cur = cur.go(step)
                dataTmp = cur.data
                if data > dataTmp[2]:
                    dataTmp[2] = data
                cur.setData(dataTmp)
        return cur
        
        
        

class Attacker(BasedAgent):


    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        foodList = self.getFood(successor).asList()
        features['successorScore'] = -len(foodList)
        features['return'] = self.getScore(successor)
        
        if len(foodList) > 0:
            myPos = successor.getAgentState(self.index).getPosition()
            minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
            features['distanceToFood'] = minDistance
        myPos = successor.getAgentState(self.index).getPosition()
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        inRange = filter(lambda x: not x.isPacman and x.getPosition() != None, enemies)
        if len(inRange) > 0:
            positions = [agent.getPosition() for agent in inRange]
            closest = min(positions, key=lambda x: self.getMazeDistance(myPos, x))
            closestDist = self.getMazeDistance(myPos, closest)
            if closestDist <= 5:
                features['distanceToGhost'] = closestDist
        if successor.getAgentState(self.index).isPacman:
            features['isPacman'] = 1
        else:
            features['isPacman'] = 0

        if len(successor.getLegalActions(self.index)) <= 1:
            features['deadEnd'] = 1
        else:
            features['deadEnd'] = 0

        return features

    def getWeights(self, gameState, action):


        if self.hanging > 80:
            return {'return':100, 'successorScore': 150, 'distanceToFood': -5, 'distanceToGhost': 2, 'isPacman': 1000}


        successor = self.getSuccessor(gameState, action)
        myPos = successor.getAgentState(self.index).getPosition()
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        inRange = filter(lambda x: not x.isPacman and x.getPosition() != None, enemies)
        if len(inRange) > 0:
            positions = [agent.getPosition() for agent in inRange]
            closestPos = min(positions, key=lambda x: self.getMazeDistance(myPos, x))
            closest_enemies = filter(lambda x: x[0] == closestPos, zip(positions, inRange))
            for agent in closest_enemies:
                if agent[1].scaredTimer > 0:
                    return {'return':100, 'successorScore': 150, 'distanceToFood': -5, 'distanceToGhost': -5, 'isPacman': 0}
        return {'return':100, 'successorScore': 150, 'distanceToFood': -5, 'distanceToGhost': 2, 'isPacman': 0, 'deadEnd': -1}

    def simulation(self, depth, gameState):

        new_state = gameState.deepCopy()
        while depth > 0:

            actions = new_state.getLegalActions(self.index)

            actions.remove(Directions.STOP)
            current_direction = new_state.getAgentState(self.index).configuration.direction
            reversed_direction = Directions.REVERSE[current_direction]
            if reversed_direction in actions and len(actions) > 1:
                actions.remove(reversed_direction)
            a = random.choice(actions)
            new_state = new_state.generateSuccessor(self.index, a)
            depth -= 1
        return self.evaluate(new_state, Directions.STOP)


    def backPropagate(self, depth, gameState, tree):
        newState = gameState.deepCopy()
        totalEva = 0
        head = tree.head
        path = [head]
        while depth > 0:
            currentBestAction = []

            actions = newState.getLegalActions(self.index)
            actions.remove('Stop')
            currentDirection = newState.getAgentState(self.index).configuration.direction
            reversedDirection = Directions.REVERSE[newState.getAgentState(self.index).configuration.direction]
            if reversedDirection in actions and len(actions) > 1:
                actions.remove(reversedDirection)

            action = None
            if util.flipCoin(0.1):
                action = random.choice(actions)
            else:

                bestVal = self.evaluate(newState, actions[0])
                for action in actions:
                    if self.evaluate(newState, action) >= bestVal:
                        currentBestAction.append(action)
                action = random.choice(currentBestAction)

            totalEva += self.evaluate(newState, action)
            bestNode = Node((newState, action, self.evaluate(newState, action)))

            head.add(bestNode)
            path.append(bestNode)
            newState = newState.generateSuccessor(self.index, action)
            head = bestNode

            depth -= 1
        head = tree.head
        tree.searchAndUpdate(path, totalEva)
        #return path, totalEva

    
    '''

    def chooseAction(self, gameState):

        currentEnemyFood = len(self.getFood(gameState).asList())
        if self.numEnemyFood != currentEnemyFood:
            self.numEnemyFood = currentEnemyFood
            self.hanging = 0
        else:
            self.hanging += 1

        if gameState.getInitialAgentPosition(self.index) == gameState.getAgentState(self.index).getPosition():
            self.hanging = 0

 

        tree = Tree((gameState, None, 0))
        newState = gameState.deepCopy()
        for i in range(30):
            path, totalVal = self.randomSimulation(5, newState, tree)
            pathLen = len(path)
            tree.searchAndUpdate(path, totalVal)


        finalActions = []
        maxVal = tree.head.children[0].getData()[2]

        for child in tree.head.children:
            if child.getData()[2] >= maxVal:
                finalActions.append(child.getData()[1])
        return random.choice(finalActions)
'''
        


    def eatFoodInSteps(self, gameState, action, depth):

        if depth == 0:
            return False
        new_state = gameState.generateSuccessor(self.index, action)
        old_score = gameState.getAgentState(self.index).numCarrying
        new_score = new_state.getAgentState(self.index).numCarrying
        if old_score < new_score:
            return False
        actions = new_state.getLegalActions(self.index)
        actions.remove(Directions.STOP)
        reversed_direction = Directions.REVERSE[new_state.getAgentState(self.index).configuration.direction]
        if reversed_direction in actions:
            actions.remove(reversed_direction)
        if len(actions) == 0:
            return True
        for a in actions:
            if not self.eatFoodInSteps(new_state, a, depth - 1):
                return False
        return True

    def __init__(self, index):
        CaptureAgent.__init__(self, index)

        self.numEnemyFood = "+inf"
        self.hanging = 0


    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.distancer.getMazeDistances()


    def chooseAction(self, gameState):

        start = time.time()
        tree = Tree((gameState, None, 0))

        currentEnemyFood = len(self.getFood(gameState).asList())
        if self.numEnemyFood != currentEnemyFood:
            self.numEnemyFood = currentEnemyFood
            self.hanging = 0
        else:
            self.hanging += 1
        if gameState.getInitialAgentPosition(self.index) == gameState.getAgentState(self.index).getPosition():
            self.hanging = 0
        all_actions = gameState.getLegalActions(self.index)
        all_actions.remove(Directions.STOP)
        actions = []
        for a in all_actions:
            if not self.eatFoodInSteps(gameState, a, 10):
                actions.append(a)
        if len(actions) == 0:
            actions = all_actions

        values = []
        for a in actions:
            new_state = gameState.generateSuccessor(self.index, a)
            value = 0
            for i in range(1, 31):
                value += self.simulation(20, new_state)
                self.backPropagate(0, new_state, tree)
            values.append(value)

        best = max(values)
        bestActions = filter(lambda x: x[0] == best, zip(values, actions))
        bestAction = random.choice(bestActions)[1]

        print 'eval time for offensive agent %d: %.4f' % (self.index, time.time() - start)
        return bestAction


class Defender(CaptureAgent):


    def foodDis(self, gameState):

        food = self.getFoodYouAreDefending(gameState).asList()
        total = 0

        for position in self.positionWithoutWalls:
            closestFoodDist = 99999
            for foodPos in food:
                dist = self.getMazeDistance(position, foodPos)
                if dist < closestFoodDist:
                    closestFoodDist = dist
            if closestFoodDist == 0:
                closestFoodDist = 1
            self.foodsNeedToProtect[position] = 1.0 / float(closestFoodDist)
            total += self.foodsNeedToProtect[position]
        if total == 0:
            total = 1
        for x in self.foodsNeedToProtect.keys():
            self.foodsNeedToProtect[x] = float(self.foodsNeedToProtect[x]) / float(total)

    def selectPatrolfoodToProtect(self):
        return random.choice(self.foodsNeedToProtect.keys())

    def __init__(self, index):
        CaptureAgent.__init__(self, index)
        self.foodToProtect = None
        self.allFoodsLastTime = None
        self.foodsNeedToProtect = {}
        
        
    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.distancer.getMazeDistances()
        if self.red:
            centralX = (gameState.data.layout.width - 2) / 2
        else:
            centralX = ((gameState.data.layout.width - 2) / 2) + 1
        self.positionWithoutWalls = []
        for i in range(1, gameState.data.layout.height - 1):
            if not gameState.hasWall(centralX, i):
                self.positionWithoutWalls.append((centralX, i))

        while len(self.positionWithoutWalls) > (gameState.data.layout.height - 2) / 2:
            self.positionWithoutWalls.pop(0)
            self.positionWithoutWalls.pop(len(self.positionWithoutWalls) - 1)
        self.foodDis(gameState)


    def chooseAction(self, gameState):
        # start = time.time()
        if self.allFoodsLastTime and len(self.allFoodsLastTime) != len(self.getFoodYouAreDefending(gameState).asList()):
            self.foodDis(gameState)
        curPos = gameState.getAgentPosition(self.index)
        if curPos == self.foodToProtect:
            self.foodToProtect = None
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        invaders = filter(lambda x: x.isPacman and x.getPosition() != None, enemies)
        if len(invaders) > 0:
            positions = [agent.getPosition() for agent in invaders]
            self.foodToProtect = min(positions, key=lambda x: self.getMazeDistance(curPos, x))
        elif self.allFoodsLastTime != None:
            eaten = set(self.allFoodsLastTime) - set(self.getFoodYouAreDefending(gameState).asList())
            if len(eaten) > 0:
                self.foodToProtect = eaten.pop()
        self.allFoodsLastTime = self.getFoodYouAreDefending(gameState).asList()

        if self.foodToProtect == None and len(self.getFoodYouAreDefending(gameState).asList()) <= 4:
            food = self.getFoodYouAreDefending(gameState).asList() + self.getCapsulesYouAreDefending(gameState)
            self.foodToProtect = random.choice(food)
        elif self.foodToProtect == None:
            self.foodToProtect = self.selectPatrolfoodToProtect()


        actions = gameState.getLegalActions(self.index)
        goodActions = []
        values = []
        for a in actions:
            new_state = gameState.generateSuccessor(self.index, a)
            if not new_state.getAgentState(self.index).isPacman and not a == Directions.STOP:
                newPos = new_state.getAgentPosition(self.index)
                goodActions.append(a)
                values.append(self.getMazeDistance(newPos, self.foodToProtect))


        bestVal = min(values)
        bestActions = filter(lambda x: x[0] == bestVal, zip(values, goodActions))

        # print 'eval time for defender agent %d: %.4f' % (self.index, time.time() - start)
        return random.choice(bestActions)[1]
