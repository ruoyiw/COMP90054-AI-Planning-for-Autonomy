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
from game import Directions
import game
import distanceCalculator
from util import nearestPoint
from game import Actions
from __builtin__ import list
from _ast import List
import sys

sys.path.append('teams/Pass/')


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'DefendAgent', second = 'ReflexCaptureAgent'):
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

class DefendAgent(CaptureAgent):
    """
    A Dummy agent to serve as an example of the necessary agent structure.
    You should look at baselineTeam.py for more details about how to
    create an agent as this is the bare minimum.
    """

    def registerInitialState(self, gameState):
        """
        This method handles the initial setup of the
        agent to populate useful fields (such as what team
        we're on).
    
        A distanceCalculator instance caches the maze distances
        between each pair of positions, so your agents can use:
        self.distancer.getDistance(p1, p2)
    
        IMPORTANT: This method may run for at most 15 seconds.
        """
    
        '''
        Make sure you do not delete the following line. If you would like to
        use Manhattan distances instead of maze distances in order to save
        on initialization time, please take a look at
        CaptureAgent.registerInitialState in captureAgents.py.
        '''
        
        CaptureAgent.registerInitialState(self, gameState)
        
        self.previousFoodList = self.getFoodYouAreDefending(gameState).asList()
        self.targetFood = None
        self.targetCenter = None
        self.centralX = (gameState.getWalls().width - 2) / 2
        self.centralY = (gameState.getWalls().height - 2) / 2
        if self.red :
            self.centralX = self.centralX - 1
        else:
            self.centralX = self.centralX + 2
        
        self.centralPoints = []
        for y in range(3, gameState.getWalls().height - 3):
            if not gameState.hasWall(self.centralX, y):
                self.centralPoints.append((self.centralX, y))
        
        self.distanceToFood = {} 
        
        
        '''
        Your initialization code goes here, if you need any.
        '''


    def chooseAction(self, gameState):
        """
        Picks among actions randomly.
        """
        start = time.time()
        self.calculateMinFoodDistance(gameState)
        current_pos = self.getCurrentObservation().getAgentPosition(self.index)

        if current_pos == self.targetFood:
            self.targetFood = None
        if current_pos == self.targetCenter:
            self.targetCenter = None
        
        actions = gameState.getLegalActions(self.index)
        
        
        if len(self.getVisibleInvaders(gameState)) > 0 and gameState.getAgentState(self.index).scaredTimer > 0:
            self.targetCenter = None
            action = self.avoidInvaders(gameState)
            print 'eval time for offensive agent %d: %.4f' % (self.index, time.time() - start)
            return action
        
        elif len(self.getVisibleInvaders(gameState)) > 0:

            self.targetCenter = None
            action = self.catchInvaders(gameState)
            print 'eval time for offensive agent %d: %.4f' % (self.index, time.time() - start)
            return action
        
        self.currentLostFood(gameState)
        if self.targetFood != None:
            action = self.towardEatenFood(gameState)
            print 'eval time for offensive agent %d: %.4f' % (self.index, time.time() - start)
            return action
        
        if len(self.getVisibleEnemiesPos(gameState)) > 0:
            
            self.targetCenter = None
            minDistance, position = min([(self.getMazeDistance(current_pos, enemy), enemy) for enemy in self.getVisibleEnemiesPos(gameState)])
            if minDistance > 1 and minDistance < 5:
                action = self.aStarSearchEnemy(gameState, [position])
                successor = gameState.generateSuccessor(self.index, action)
                if not successor.getAgentState(self.index).isPacman:
                    print 'eval time for offensive agent %d: %.4f' % (self.index, time.time() - start)
                    return action
        
        
        if len(self.getFoodYouAreDefending(gameState).asList()) < 5:
            action = self.defendFood(gameState)
            print 'eval time for offensive agent %d: %.4f' % (self.index, time.time() - start)
            return action 
        
        if self.targetCenter == None:
            self.targetCenter = self.selectPosition(gameState)
        
        if self.targetCenter != None:
            action = self.defendAtCenter(gameState)
            print 'eval time for offensive agent %d: %.4f' % (self.index, time.time() - start)
            return action
        '''
        You should change this in your own agent.
        '''
       
        return random.choice(actions)
    
    def calculateMinFoodDistance(self, gameState):
        currentFoodPosList = self.getFoodYouAreDefending(gameState).asList()
        currentEnemiesList = self.getVisibleEnemiesPos(gameState)
        currentFoodPosList.extend(currentEnemiesList)
        sum = 0
        
        for p in self.centralPoints:
            
            distance = []
            for foodPos in currentFoodPosList:
                distance.append(self.distancer.getDistance(p, foodPos))
            minDistance = min(distance) + 3
            
            # closer to the food, the position has a higher probability to choose
            self.distanceToFood[p] = 1.0 / minDistance
            
            sum += self.distanceToFood[p]
        
        for p in self.distanceToFood.keys():
            self.distanceToFood[p] = self.distanceToFood[p] / sum
    
    def selectPosition(self, gameState):
        r = random.random()

        sum = 0
        for p in self.distanceToFood.keys():
            if sum < r:
                sum += self.distanceToFood[p]
            else:
                return p
        return self.centralPoints[len(self.centralPoints) - 1]
     
    def currentLostFood(self, gameState):
        currentFoodList = self.getFoodYouAreDefending(gameState).asList()
        lostFoodList = []
        for food in self.previousFoodList:
            if not food in currentFoodList:
                lostFoodList.append(food)

        if(lostFoodList != []):
            self.calculateMinFoodDistance(gameState)
            self.targetFood = random.choice(lostFoodList)
        self.previousFoodList = currentFoodList
        
       
    def towardEatenFood(self, gameState):
        if(self.targetFood != None):
            #print(self.targetFood)
            return self.aStarSearch(gameState, [self.targetFood])
        else:
            return "Stop"
        
    
    def defendFood(self, gameState):
        self.findFood(gameState)
        
    
    def defendAtCenter(self, gameState):
        return self.aStarSearch(gameState, [self.targetCenter])

    def catchInvaders(self, gameState):
        opponentsPos = self.getVisibleInvadersPos(gameState)
        return self.aStarSearch(gameState, opponentsPos)  
    
    def findFood(self, gameState): 
        foodList = self.getFood(gameState).asList()
        foodList.extend(self.getCapsules(gameState))
        return self.aStarSearchFood(gameState, foodList)
    
    def getInvaders(self, gameState):
        opponentsIndics = self.getOpponents(gameState)
        opponents = [gameState.getAgentState(i) for i in opponentsIndics]
        
        invaders = []
        for opponent in opponents:
            
            if opponent.isPacman:
                
                invaders.append(opponent)        
        return invaders
    
    def getVisibleInvaders(self, gameState):        
        visibleInvaders = []
        for invader in self.getInvaders(gameState):
            
            if invader.getPosition() != None:
               
                visibleInvaders.append(invader)        
        return visibleInvaders
    
    def getVisibleInvadersPos(self, gameState):
        invadersPos = []
        for invader in self.getVisibleInvaders(gameState):
            x, y = invader.getPosition()
            invadersPos.append((x, y))
        return invadersPos
    
    def avoidInvaders(self, gameState):
        opponentsPos = self.getVisibleInvadersPos(gameState)
        current_pos = self.getCurrentObservation().getAgentPosition(self.index)
        for opponentPos in opponentsPos:
            distance = self.distancer.getDistance(opponentPos, current_pos)
            if(distance < 4):
                return self.aStarSearchScared(gameState, [opponentPos]) 
             
        return self.aStarSearch(gameState, opponentsPos)
    
   #reuse the code in the assignment 1 to calculate the best action by aStar
    def aStarSearch(self, gameState, targets):
        states = []
        for target in targets:
            current_pos = self.getCurrentObservation().getAgentPosition(self.index)
            
            # create a priority queue 
            open_list = util.PriorityQueue()
            open_list.push( (current_pos, []), 
                            self.distancer.getDistance(current_pos, target))
            # store visited points
            closed_list = set()
            
            while not open_list.isEmpty():   
                position, paths = open_list.pop()
                
                if position == target:
                    if(len(paths) != 0):
                        states.append((len(paths), paths[0]))
                    break
                # check duplication
                if position not in closed_list :
                    closed_list.add(position)
                    # add successors of the node
                    successors = self.getSuccessors(position, gameState)

                    for successor in successors:
                        new_paths = paths + [successor[1]]
                        if self.isOnGrid(gameState, successor[0]) and  self.isOnGrid(gameState, target):
                            cost = (len(new_paths) + self.distancer.getDistance(successor[0], target))
                            open_list.push((successor[0], new_paths), cost)
        
        if (len(states) == 0):
            states.append((0, "Stop"))
        bestAction = "Stop"
        shortestDistance = 999999
        for distance, action in states:
            if distance < shortestDistance:
                bestAction = action
                shortestDistance = distance
        if len(self.getVisibleInvaders(gameState)) > 0 and shortestDistance < 3:
            self.targetFood = None
        return bestAction
    
    #reuse the code in the assignment 1 to calculate the best action by aStar
    def aStarSearchScared(self, gameState, targets):
        states = []
        for target in targets:
            current_pos = self.getCurrentObservation().getAgentPosition(self.index)
            
            # create a priority queue 
            open_list = util.PriorityQueue()
            open_list.push( (current_pos, []), 
                            -self.distancer.getDistance(current_pos, target))
            # store visited points
            closed_list = set()
            
            while not open_list.isEmpty():   
                position, paths = open_list.pop()
                
                if position == target:
                    if(len(paths) == 0):
                        states.append((0, "Stop"))
                    else:
                        states.append((len(paths), paths[0]))
                    break
                # check duplication
                if position not in closed_list :
                    closed_list.add(position)
                    # add successors of the node
                    successors = self.getSuccessors(position, gameState)

                    for successor in successors:
                        new_paths = paths + [successor[1]]
                        if self.isOnGrid(gameState, successor[0]) and  self.isOnGrid(gameState, target):
                            cost = (-len(new_paths) - self.distancer.getDistance(successor[0], target))
                            open_list.push((successor[0], new_paths), cost)
        
        bestAction = "Stop"
        longestDistance = 0
        for distance, action in states:
            if distance > longestDistance:
                bestAction = action
                longestDistance = distance
        return bestAction
    
     #reuse the code in the assignment 1 to calculate the best action by aStar
    def aStarSearchEnemy(self, gameState, targets):
        states = []
        for target in targets:
            current_pos = self.getCurrentObservation().getAgentPosition(self.index)
            
            # create a priority queue 
            open_list = util.PriorityQueue()
            open_list.push( (current_pos, []), 
                            self.distancer.getDistance(current_pos, target))
            # store visited points
            closed_list = set()
            
            while not open_list.isEmpty():   
                position, paths = open_list.pop()
                
                if position == target:
                    if(len(paths) != 0):
                        states.append((len(paths), paths[0]))
                    break
                # check duplication
                if position not in closed_list :
                    closed_list.add(position)
                    # add successors of the node
                    successors = self.getSuccessorsEnemy(position, gameState)

                    for successor in successors:
                        new_paths = paths + [successor[1]]
                        if self.isOnGrid(gameState, successor[0]) and  self.isOnGrid(gameState, target):
                            cost = (len(new_paths) + self.distancer.getDistance(successor[0], target))
                            open_list.push((successor[0], new_paths), cost)
        
        if (len(states) == 0):
            states.append((0, "Stop"))
        bestAction = "Stop"
        shortestDistance = 999999
        for distance, action in states:
            if distance < shortestDistance:
                bestAction = action
                shortestDistance = distance
        return bestAction
    
    # return the next position and its action
    def getSuccessors(self, currentPos, gameState):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        actions = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]
        successors = []
        
        for action in actions:
            dx, dy = Actions.directionToVector(action)
            x, y = int(currentPos[0]+dx), int(currentPos[1]+dy)
            
            if self.isOnGrid(gameState, (x, y)) and not (gameState.hasWall(x, y))and self.side(gameState, (x, y)):
                if(action == Directions.NORTH):
                    action = "North"
                elif (action == Directions.SOUTH):
                    action = "South"
                elif (action == Directions.EAST):
                    action = "East"
                elif (action == Directions.WEST):
                    action = "West"
                else:
                    action = "Stop"
                
                successors.append(((x, y), action))
                                 
        return successors
    # return the next position and its action
    def getSuccessorsEnemy(self, currentPos, gameState):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        actions = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]
        successors = []
        
        for action in actions:
            dx, dy = Actions.directionToVector(action)
            x, y = int(currentPos[0]+dx), int(currentPos[1]+dy)
            
            if self.isOnGrid(gameState, (x, y)) and not (gameState.hasWall(x, y)):
                if(action == Directions.NORTH):
                    action = "North"
                elif (action == Directions.SOUTH):
                    action = "South"
                elif (action == Directions.EAST):
                    action = "East"
                elif (action == Directions.WEST):
                    action = "West"
                else:
                    action = "Stop"
                
                successors.append(((x, y), action))
                                 
        return successors
    
    def side(self, gameState, pos):
        x, y = pos
        if self.red:
            if x <= ((gameState.getWalls().width - 2) / 2):
                return True
            else:
                return False
        else:
            if x > ((gameState.getWalls().width - 2) / 2):
                return True
            else:
                return False
    
    def isOnGrid(self, gameState, position):
        x, y = position
        return x < gameState.getWalls().width and y < gameState.getWalls().height and x > 0 and y > 0
    
    
    def getVisibleEnemiesPos(self, gameState):
        invadersPos = []
        opponentsIndics = self.getOpponents(gameState)
        opponents = [gameState.getAgentState(i) for i in opponentsIndics]
        
        for invader in opponents:
            if invader.getPosition() != None:
                x, y = invader.getPosition()
                invadersPos.append((x, y))
        return invadersPos

        
class ReflexCaptureAgent(CaptureAgent):
    """
    A Dummy agent to serve as an example of the necessary agent structure.
    You should look at baselineTeam.py for more details about how to
    create an agent as this is the bare minimum.
    """
    def registerInitialState(self, gameState):
        """
        This method handles the initial setup of the
        agent to populate useful fields (such as what team
        we're on).
    
        A distanceCalculator instance caches the maze distances
        between each pair of positions, so your agents can use:
        self.distancer.getDistance(p1, p2)
    
        IMPORTANT: This method may run for at most 15 seconds.
        """
    
        '''
        Make sure you do not delete the following line. If you would like to
        use Manhattan distances instead of maze distances in order to save
        on initialization time, please take a look at
        CaptureAgent.registerInitialState in captureAgents.py.
        '''
        
        CaptureAgent.registerInitialState(self, gameState)
        
        self.start = gameState.getAgentPosition(self.index)
        self.isCenter = False
        self.x = gameState.getWalls().width / 2
        self.y = gameState.getWalls().height / 2
        self.center = (self.x, self.y)
        self.stayWithGhostTimer = 0
    
        '''
        Your initialization code goes here, if you need any.
        '''   

    def chooseAction(self, gameState):
        """
        Picks among actions randomly.
        """      
        start = time.time()
        current_pos = self.getCurrentObservation().getAgentPosition(self.index)
        actions = gameState.getLegalActions(self.index)
        if not gameState.getAgentState(self.index).isPacman:
            if len(self.getVisibleGhostsPos(gameState))> 0:
                self.stayWithGhostTimer += 1
            else:
                self.stayWithGhostTimer = 0
            
            mcTreeValue = []    
            actions = gameState.getLegalActions(self.index)
            actions = self.removeStopAction(actions)
            
            for action in actions:
                sum = 0
                for i in range(1, 24):
                    value = self.simulation(gameState.generateSuccessor(self.index, action), 10)
                    sum += value
                mcTreeValue.append(sum)
        
            maxValue = max(mcTreeValue)
            bestActions = [action for action, value in zip(actions, mcTreeValue)if value == maxValue]
            bestAction = random.choice(bestActions)
            print 'eval time for offensive agent %d: %.4f' % (self.index, time.time() - start)
            return bestAction
        elif len(self.getVisibleGhost(gameState)) > 0 and gameState.getAgentState(self.index).isPacman and (not self.isPowered(gameState)):
            action = self.chooseAttackAction(gameState)
            print 'eval time for offensive agent %d: %.4f' % (self.index, time.time() - start)
            return action 
        elif len(self.getVisibleGhost(gameState)) == 0 and gameState.getAgentState(self.index).isPacman and (not self.isPowered(gameState)):
            action = self.chooseFoodAction(gameState)
            print 'eval time for offensive agent %d: %.4f' % (self.index, time.time() - start)
            return action
        elif self.isPowered(gameState):
            action = self.choosePoweredAction(gameState)
            print 'eval time for offensive agent %d: %.4f' % (self.index, time.time() - start)
            return action
                           
        return random.choice(actions)

    def isPowered(self, gameState):
        opponentsIndics = self.getOpponents(gameState)
        opponents = [gameState.getAgentState(i) for i in opponentsIndics]
        self.poweredTime = opponents[0].scaredTimer
        
        if self.poweredTime > 0:
            return True
        else:
            return False 
        
        
    def chooseFoodAction(self, gameState):
        currentFoodList = self.getFood(gameState).asList()
        current_pos = self.getCurrentObservation().getAgentPosition(self.index)
        carriedFood = gameState.getAgentState(self.index).numCarrying
        successors = self.getPecmanSuccessors(current_pos, gameState)
        list = []
        oldHomeDist = self.gohome(gameState, current_pos)
        if len(currentFoodList) > 0:
            minFood, minFoodDis = self.searchClosestFood(currentFoodList, current_pos)      
        for s in successors:
            searchFoodAction = False
            position, action = s
            foodList = currentFoodList[:]
            newCarriedFood = carriedFood
            if position in currentFoodList:
                newCarriedFood = carriedFood + 1
                foodList.remove(position)
            if len(currentFoodList) > 0:
                newMinFoodDis = self.getMazeDistance(minFood, position)
                if newMinFoodDis < minFoodDis:
                    searchFoodAction = True
#            seachFoodAction = self.aStarSearchFood(gameState, foodList)
            newValue = self.foodEvaluate(gameState, currentFoodList, position, searchFoodAction, newCarriedFood, oldHomeDist)
            newList = self.getFoodValue(gameState, foodList, position, action, newCarriedFood, newValue, 0)
            list = list + newList
        bestValue = 0
        bestAction = "Stop"
        for a in list:
            if bestValue < a[0]:
                bestValue = a[0]
                bestAction = a[1]

        return bestAction
        
    def getFoodValue(self, gameState, foodList, position, firstAction, carriedFood, preValue, num):
        list = []
        if num == 4:
            list = list + [(preValue, firstAction)]
        else:
            num = num + 1
            successors = self.getPecmanSuccessors(position, gameState)
            oldHomeDist = self.gohome(gameState, position)
            if len(foodList) > 0:
                minFood, minFoodDis = self.searchClosestFood(foodList, position)                
            for s in successors:
                searchFoodAction = False
                newPosition, newAction = s
                newFoodList = foodList[:]
                newCarriedFood = carriedFood
                if newPosition in foodList:
                    newCarriedFood = carriedFood + 1
                    newFoodList.remove(newPosition)
                if len(foodList) > 0:
                    newMinFoodDis = self.getMazeDistance(minFood, newPosition)
                    if newMinFoodDis < minFoodDis:
                        searchFoodAction = True
#                seachFoodAction = self.aStarSearchFood(gameState, newFoodList)
                newValue = self.foodEvaluate(gameState, foodList, newPosition, searchFoodAction, newCarriedFood, oldHomeDist)
                newValuePro = pow(0.9, num) * newValue + preValue
                newList = self.getFoodValue(gameState, newFoodList, newPosition, firstAction, newCarriedFood, newValuePro, num)
                list = list + newList
        return list
                
    def searchClosestFood(self, foodList, position):
        minFoodDis = 10000
        minFood = foodList[0]
        for f in foodList: 
            foodDis = self.getMazeDistance(f, position)
            if foodDis < minFoodDis:
                minFoodDis = foodDis
                minFood = f
        return(minFood, minFoodDis)
                                
    
    def foodEvaluate(self, gameState, foodList, position, searchFoodAction, carriedFood, oldHomeDist):
        features = self.getFoodFeatures(gameState, foodList, position, searchFoodAction, oldHomeDist)
        weights = self.getFoodWeights(gameState, carriedFood)
        return features * weights
        
    def getFoodFeatures(self, gameState, foodList, position, searchFoodAction, oldHomeDist):
        features = util.Counter()            
        features['collectFood'] = 0
        if position in foodList:
            features['collectFood'] = 1
            
        features['eatCapsule'] = 0
        capsules = self.getCapsules(gameState)
        if len(capsules) > 0:
            if capsules[0] == position:
                features['eatCapsule'] = 1
            
        if self.gohome(gameState, position) < oldHomeDist:
            features['goHome'] = 1
        elif self.gohome(gameState, position) == oldHomeDist:
            features['goHome'] = 0
        else:
            features['goHome'] = -1
            
        if self.red:
            if position[0] < 16:
                features['beHome'] = 1
                features['goHome'] = 0
            else:
                features['beHome'] = 0
        else:
            if position[0] > 15:
                features['beHome'] = 1
                features['goHome'] = 0
            else:
                features['beHome'] = 0
                
        if searchFoodAction:
            features['closeToFood'] = 1
        else:
            features['closeToFood'] = 0
        return features
            
    def getFoodWeights(self, gameState, carriedFood):
        goHomeWeight = carriedFood * 5
        beHomeWeight = carriedFood * 20
        if carriedFood == 0:
            beHomeWeight = - 50
        return {'collectFood': 10, 'eatCapsule': 1000, 'goHome': goHomeWeight, 'beHome': beHomeWeight, 'closeToFood': 1}
        
    
    def chooseAttackAction(self, gameState):
        current_pos = self.getCurrentObservation().getAgentPosition(self.index)
        ghostLists = self.hasVisibleGhost(gameState)
        ghostPossiblePos = None
        needToRun = False
        closestGhost = None
        corner = None
        oldRunToCorner = None
        
        line = []
        if (len(ghostLists)>0) and gameState.getAgentState(self.index).isPacman:
            ghostPossiblePos = self.visibleGhostPos(gameState)
            closestGhost = self.closestGhost(gameState)
            if(self.wallsNum(current_pos, gameState) > 1):
                corners = self.straightLine(current_pos, gameState, line)
                if self.isDeadLine(corners):
                    corner = self.getDeadLineCorner(corners)
                    cornerDist = self.getMazeDistance(current_pos, corner)
                    if closestGhost[0] < (cornerDist*2+2):
                        needToRun = True
                        oldRunToCorner = self.getMazeDistance(current_pos, corner)
                
        oldHomeDist = self.gohome(gameState, current_pos)
        successors = self.getPecmanSuccessors(current_pos, gameState) 
#        foodList = self.getFood(gameState).asList()
#        foodList.extend(self.getCapsules(gameState))
#        seachFoodAction = self.aStarSearchFood(gameState, foodList)
        
        bestValue = -10000
        bestActions = []
        valueActions = []
        for suc in successors:
            newPosition, action = suc
            value = self.evaluate(gameState, current_pos, newPosition, action, oldHomeDist, ghostPossiblePos, needToRun, corner, oldRunToCorner, closestGhost)
            valueActions.append((value, action))
            if bestValue < value:
                bestValue = value
        for va in valueActions:
            if va[0] == bestValue:
                bestActions.append(va[1])
        
        return random.choice(bestActions)

    
    def evaluate(self, gameState, oldPosition, newPosition, action, oldHomeDist, ghostPositions, needToRun, corner, oldRunToCorner, closestGhost):
        features = self.getFeatures(gameState, oldPosition, newPosition, action, oldHomeDist, ghostPositions, needToRun, corner, oldRunToCorner, closestGhost)
        weights = self.getWeights(gameState, action)
        return features * weights
    
    def getWeights(self, gameState, action):
        self.foodNum = gameState.getAgentState(self.index).numCarrying
        weightFood = self.foodNum * 5
        if self.foodNum == 0:
            weightFood = -10
        return {'collectFood': 10, 'eatCapsule': 1000, 'runToCorner': 500, 'avoidGhost': 100, 'avoidDeadLine': 100, 'nearGhost': 1100, 'goHome': weightFood}
    
    def getFeatures(self, gameState, oldPosition, newPosition, action, oldHomeDist, ghostPositions, needToRun, corner, oldRunToCorner, closestGhost):
        features = util.Counter()            
        features['nearGhost'] = 0
        if (ghostPositions != None):
            for g in ghostPositions:
                if newPosition == g:
                    features['nearGhost'] = -1
        
        features['avoidGhost'] = 0
        if closestGhost != None:
            newGhostDist = self.getMazeDistance(newPosition, closestGhost[1])
            if closestGhost[0] > newGhostDist:
                features['avoidGhost'] = -1/closestGhost[0]      
                
        line = []
        activeDir = 0        
        features['avoidDeadLine'] = 0  
        if closestGhost != None:
            if (self.wallsNum(newPosition, gameState) > 1):
                corners = self.straightLine(newPosition, gameState, line)
                if self.isDeadLine(corners):
                    for g in ghostPositions:
                        if self.getMazeDistance(g, oldPosition) < 6:
                            features['avoidDeadLine'] = -1
                    
        if needToRun == True:
            features['avoidGhost'] = 0
            newRunDist = self.getMazeDistance(newPosition, corner)
            if newRunDist >= oldRunToCorner:
                features['runToCorner'] = -1
            else:
                features['runToCorner'] = 0
        else:
            features['runToCorner'] = 0
        
        features['eatCapsule'] = 0
        capsules = self.getCapsules(gameState)
        if len(capsules) > 0: 
            if capsules[0] == newPosition:
                features['eatCapsule'] = 1
        
        successor = self.getSuccessor(gameState, action)
        actions = gameState.getLegalActions(self.index)
        actions.remove(Directions.STOP)
        rev = Directions.REVERSE[successor.getAgentState(self.index).configuration.direction]
        # if only leaving the reverse direction, should not delete it
        if rev in actions and len(actions) > 1:
            actions.remove(rev)
        if len(self.getVisibleGhosts(gameState)):
            if(len(actions) <= 1):
               features['deadEnd'] = -1.0
            else:
               features['deadEnd'] = 0.0    
               
            
        if self.red:
            if gameState.hasFood(newPosition[0], newPosition[1]) and (newPosition[0] > 15):
                features['collectFood'] = 1
            else:
                features['collectFood'] = 0
        else:
            if gameState.hasFood(newPosition[0], newPosition[1]) and (newPosition[0] < 16):
                features['collectFood'] = 1
            else:
                features['collectFood'] = 0
                
        if self.gohome(gameState, newPosition) < oldHomeDist:
            features['goHome'] = 1
        elif self.gohome(gameState, newPosition) == oldHomeDist:
            features['goHome'] = 0
        else:
            features['goHome'] = -1

        return features
    
    def hasVisibleGhost(self, gameState):
        current_pos = self.getCurrentObservation().getAgentPosition(self.index)
#        runDist, runCorner = self.getPecmanRunAction(gameState)
        visibleGhosts = self.getVisibleGhost(gameState)
        ghostDists = []
        for v in visibleGhosts:
            ghostDist = self.getMazeDistance(current_pos, v.getPosition())
            ghostDists.append((ghostDist, v.getPosition()))
        return ghostDists
    
    def closestGhost(self, gameState):
        ghostDists = self.hasVisibleGhost(gameState)
        closestGhostPos = None
        closestGhostDist = 9999
        if len(ghostDists)>0:        
            for g in ghostDists:
                if g[0] < closestGhostDist:
                    closestGhostDist = g[0]
                    closestGhostPos = g[1]
        return (closestGhostDist, closestGhostPos)
        
    def visibleGhostPos(self, gameState):
        ghostDists = self.hasVisibleGhost(gameState)
        if len(ghostDists)>0:
            ghostPositions = []
            for gh in ghostDists:
                ghostSuccessors = self.getPecmanSuccessors(gh[1], gameState)
                ghostPositions.append(gh[1])
                for gs in ghostSuccessors:
                     ghostPositions.append(gs[0])
        else:
            ghostPositions = None
        return ghostPositions
                    
    def getPecmanSuccessors(self, currentPos, gameState):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        actions = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]
        successors = []
        
        for action in actions:
            dx, dy = Actions.directionToVector(action)
            x, y = int(currentPos[0]+dx), int(currentPos[1]+dy)
            if not (gameState.hasWall(x, y)):
                if(action == Directions.NORTH):
                    action = "North"
                elif (action == Directions.SOUTH):
                    action = "South"
                elif (action == Directions.EAST):
                    action = "East"
                else:
                    action = "West"
                successors.append(((x, y), action))
                                 
        return successors
    
    def isDeadLine(self, corners):
        for c in corners:
            position, description = c
            if description == "deadline":
                return True
        return False
    
    def getDeadLineCorner(self, corners):
        for c in corners:
            position, description = c
            if description == "corner":
                return position
        return False
            
    def straightLine(self, position, gameState, line):
        line.append(position)
        successors = self.getPecmanSuccessors(position, gameState)
        for successor in successors:
            sucPosition, sucAction = successor
            if sucPosition not in line:
                line.append(sucPosition)
            else:
                successors.remove(successor)                        
        corners = []
        
        if(self.wallsNum(position, gameState) == 3):
            corners.append((position, "deadline"))
            
        for s in successors:
            sPosition, sAction = s
            if (self.wallsNum(sPosition, gameState) == 3):
                corners.append((sPosition, "deadline"))
            elif(self.wallsNum(sPosition, gameState) < 2):
                corners.append((sPosition, "corner"))
            elif(self.wallsNum(sPosition, gameState) == 2):
                corners = corners + self.straightLine(sPosition, gameState, line)
        return corners
                
        
    def wallsNum(self, position, gameState):
        actions = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]
        wall = 0        
        for action in actions:
            dx, dy = Actions.directionToVector(action)
            x, y = int(position[0]+dx), int(position[1]+dy)
            if (gameState.hasWall(x, y)):
                wall = wall + 1
        return wall
    
    def gohome(self, gameState, current_pos):
#        current_pos = self.getCurrentObservation().getAgentPosition(self.index)
        x = gameState.getWalls().width 
        y = gameState.getWalls().height
        if self.red:
            goRed = []
            centerLine = (x-2)/2
            for i in range(1, (y-2)):
                if(not (gameState.hasWall(centerLine, i))):
                    distanceHome = self.getMazeDistance(current_pos, (centerLine, i))
                    goRed.append(distanceHome)
            closestHome = min(goRed)
        else:
            goBlue = []
            centerLine = (x-2)/2+1
            for i in range(1, (y-2)):
                if(not (gameState.hasWall(centerLine, i))):
                    distanceHome = self.getMazeDistance(current_pos, (centerLine, i))
                    goBlue.append(distanceHome)
            closestHome = min(goBlue)
        return closestHome
    
    def getVisibleGhost(self, gameState):
        visibleGhosts = []
        for ghost in self.getOpponentGhost(gameState):
            if ghost.getPosition() != None:
                visibleGhosts.append(ghost)        
        return visibleGhosts

    
    def getOpponentGhost(self, gameState):
        opponentsIndics = self.getOpponents(gameState)
        opponents = [gameState.getAgentState(i) for i in opponentsIndics]
        
        ghosts = []
        for opponent in opponents:
            if not opponent.isPacman:
                ghosts.append(opponent)        
        return ghosts
    
    def aStarSearchFood(self, gameState, targets):
        states = []
        for target in targets:
            current_pos = self.getCurrentObservation().getAgentPosition(self.index)
            
            # create a priority queue 
            open_list = util.PriorityQueue()
            open_list.push( (current_pos, []), 
                            self.distancer.getDistance(current_pos, target))
            # store visited points
            closed_list = set()
            
            while not open_list.isEmpty():   
                position, paths = open_list.pop()
                
                if position == target:
                    if(len(paths) == 0):
                        states.append((0, "Stop"))
                    else:
                        states.append((len(paths), paths[0]))
                    break
                # check duplication
                if position not in closed_list :
                    closed_list.add(position)
                    # add successors of the node
                    successors = self.getSuccessorsFood(position, gameState)

                    for successor in successors:
                        new_paths = paths + [successor[1]]
                        if self.isOnGrid(gameState, successor[0]) and  self.isOnGrid(gameState, target):
                            cost = (len(new_paths) + self.distancer.getDistance(successor[0], target))
                            open_list.push((successor[0], new_paths), cost)
        
        bestAction = "Stop"
        shortestDistance = 999999
        for distance, action in states:
            if distance < shortestDistance:
                bestAction = action
                shortestDistance = distance
        return bestAction

     
    # return the next position and its action
    def getSuccessorsFood(self, currentPos, gameState):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        actions = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]
        successors = []
        
        for action in actions:
            dx, dy = Actions.directionToVector(action)
            x, y = int(currentPos[0]+dx), int(currentPos[1]+dy)
            if self.isOnGrid(gameState, (x, y)) and not (gameState.hasWall(x, y)):
                if(action == Directions.NORTH):
                    action = "North"
                elif (action == Directions.SOUTH):
                    action = "South"
                elif (action == Directions.EAST):
                    action = "East"
                else:
                    action = "West"
                successors.append(((x, y), action))
                                 
        return successors
    
    def isOnGrid(self, gameState, position):
        x, y = position
        return x < gameState.getWalls().width and y < gameState.getWalls().height and x > 0 and y > 0
    
    def choosePoweredAction(self, gameState):
        currentFoodList = self.getFood(gameState).asList()
        current_pos = self.getCurrentObservation().getAgentPosition(self.index)
        carriedFood = gameState.getAgentState(self.index).numCarrying
        ghostLists = self.hasVisibleGhost(gameState)
        ghostPossiblePos = None
        if (len(ghostLists)>0):
            ghostPossiblePos = self.visibleGhostPos(gameState)
        successors = self.getPecmanSuccessors(current_pos, gameState)
        list = []
        oldHomeDist = self.gohome(gameState, current_pos)
        if len(currentFoodList) > 0:
            minFood, minFoodDis = self.searchClosestFood(currentFoodList, current_pos)    
        for s in successors:
            searchFoodAction = False
            position, action = s
            foodList = currentFoodList[:]
            newCarriedFood = carriedFood
            if position in currentFoodList:
                newCarriedFood = carriedFood + 1
                foodList.remove(position)
            if len(currentFoodList) > 0:
                newMinFoodDis = self.getMazeDistance(minFood, position)
                if newMinFoodDis < minFoodDis:
                    searchFoodAction = True
#            seachFoodAction = self.aStarSearchFood(gameState, foodList)
            newValue = self.powerEvaluate(gameState, currentFoodList, position, action, searchFoodAction, newCarriedFood, oldHomeDist, ghostPossiblePos)
            newList = self.getPowerValue(gameState, foodList, position, action, newCarriedFood, newValue, 0, ghostPossiblePos)
            list = list + newList
        bestValue = 0
        bestAction = "Stop"
        for a in list:
            if bestValue < a[0]:
                bestValue = a[0]
                bestAction = a[1]

        return bestAction
        
    def getPowerValue(self, gameState, foodList, position, firstAction, carriedFood, preValue, num, ghostPossiblePos):
        list = []
        if num == 4:
#            print("????????")
            list = list + [(preValue, firstAction)]
        else:
            num = num + 1
            successors = self.getPecmanSuccessors(position, gameState)
            oldHomeDist = self.gohome(gameState, position)
            if len(foodList) > 0:
                minFood, minFoodDis = self.searchClosestFood(foodList, position)    
            for s in successors:
                searchFoodAction = False
                newPosition, newAction = s
                newFoodList = foodList[:]
                newCarriedFood = carriedFood
                if newPosition in foodList:
                    newCarriedFood = carriedFood + 1
                    newFoodList.remove(newPosition)
                if len(foodList) > 0:
                    newMinFoodDis = self.getMazeDistance(minFood, newPosition)
                    if newMinFoodDis < minFoodDis:
                        searchFoodAction = True
#                seachFoodAction = self.aStarSearchFood(gameState, newFoodList)
                newValue = self.powerEvaluate(gameState, foodList, newPosition, newAction, searchFoodAction, newCarriedFood, oldHomeDist, ghostPossiblePos)
                newValuePro = pow(0.9, num) * newValue + preValue
                newList = self.getPowerValue(gameState, newFoodList, newPosition, firstAction, newCarriedFood, newValuePro, num, ghostPossiblePos)
                list = list + newList
        return list
                
                
    
    def powerEvaluate(self, gameState, foodList, position, action, seachFoodAction, carriedFood, oldHomeDist, ghostPossiblePos):
        features = self.getPoweredFeatures(gameState, foodList, position, action, seachFoodAction, oldHomeDist, ghostPossiblePos)
        weights = self.getPoweredWeights(gameState, carriedFood)
        return features * weights
        
    def getPoweredFeatures(self, gameState, foodList, position, action, seachFoodAction, oldHomeDist, ghostPossiblePos):
        features = util.Counter()            
        features['collectFood'] = 0
        if position in foodList:
            features['collectFood'] = 1
            
        features['eatGhost'] = 0
        if ghostPossiblePos != None:
            if position in ghostPossiblePos:
                features['eatGhost'] = 1
            
        if self.gohome(gameState, position) < oldHomeDist:
            features['goHome'] = 1
        elif self.gohome(gameState, position) == oldHomeDist:
            features['goHome'] = 0
        else:
            features['goHome'] = -1
                
        if seachFoodAction:
            features['closeToFood'] = 1
        else:
            features['closeToFood'] = 0
        return features
            
    def getPoweredWeights(self, gameState, carriedFood):
        opponentsIndics = self.getOpponents(gameState)
        opponents = [gameState.getAgentState(i) for i in opponentsIndics]
        poweredTime = opponents[0].scaredTimer
        eatGhost = poweredTime * 2
        goHomeWeight = carriedFood * 20 / poweredTime
        return {'collectFood': 20, 'goHome': goHomeWeight, 'closeToFood': 5, 'eatGhost': 5}
    
    def getATKFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        current_pos = successor.getAgentState(self.index).getPosition()
        nextFoodList = self.getFood(successor).asList()
        actions = successor.getLegalActions(self.index)
        
        features['successorScore'] = -len(nextFoodList)
           
        if(action == Directions.STOP):
           features['stop'] = 1.0
        else:
           features['stop'] = 0.0
        
        actions.remove(Directions.STOP)
        rev = Directions.REVERSE[successor.getAgentState(self.index).configuration.direction]
        # if only leaving the reverse direction, should not delete it
        if rev in actions and len(actions) > 1:
            actions.remove(rev)
        if(len(actions) <= 1):
           features['deadEnd'] = 1.0
        else:
           features['deadEnd'] = 0.0    
           
        if len(nextFoodList) > 0: 
            minDistance = min([self.getMazeDistance(current_pos, food) for food in nextFoodList])
            features['distanceToFood'] = minDistance 
        else:
            features['distanceToFood'] = 0
        
        if len(self.getVisibleGhosts(gameState)) > 0:
            minDistance = min([self.getMazeDistance(current_pos, ghost) for ghost in self.getVisibleGhostsPos(gameState)])
            if minDistance < 5 and minDistance > 0:
                features['distanceToGhost'] = 4.0/minDistance
            elif minDistance >= 5:
                features['distanceToGhost'] = 1.0
            else:
                features['distanceToGhost'] = 50.0
        else:
            features['distanceToGhost'] = 0
        
        if len(self.getVisibleInvaders(gameState)) > 0:
            minDistance = min([self.getMazeDistance(current_pos, invader) for invader in self.getVisibleInvadersPos(gameState)])
            if minDistance < 5 and minDistance > 0:
                features['distanceToInvader'] = 4.0/minDistance
            elif minDistance >= 5:
                features['distanceToInvader'] = 1.0
            else:
                features['distanceToInvader'] = 50.0
        else:
            features['distanceToInvader'] = 0
            
        if len(self.getCapsules(gameState)) > 0:
            minDistance = min([self.getMazeDistance(current_pos, capsule) for capsule in self.getCapsules(gameState)])
            if minDistance != 0:
                features['distanceToCapsule'] = 4.0/minDistance
        else:
            features['distanceToCapsule'] = 0
            
        
        features['numCarrying'] = gameState.getAgentState(self.index).numCarrying
        
        features['stayWithGhostTimer'] = self.stayWithGhostTimer
        
        features['score'] = self.getScore(successor)
        
        teamIndics = self.getTeam(gameState)
        for index in teamIndics:
            if (index != self.index):
                teammate = gameState.getAgentState(index)
                teammatePos = teammate.getPosition()
                distance = self.getMazeDistance(current_pos, teammatePos)
                features['distanceToTeammate'] = distance
                      
        line = []
        activeDir = 0        
        features['avoidDeadLine'] = 0  
        if (self.wallsNum(current_pos, gameState) > 1):
            corners = self.straightLine(current_pos, gameState, line)
            if self.isDeadLine(corners):
                features['avoidDeadLine'] = -1
            elif(self.wallsNum(current_pos, gameState) < 2):
                directions = self.getPecmanSuccessors(current_pos, gameState)
                for d in directions:
                    line2 = []
                    corner2 = self.straightLine(d[0], gameState, line2)
                    if not self.isDeadLine(corner2):
                        activeDir = activeDir + 1
                if activeDir < 2:
                    features['avoidDeadLine'] = -1

  
        return features
        
    def getATKWeights(self, gameState, action):
        successor = gameState.generateSuccessor(self.index, action)
        isPacman = self.isPacman(successor)
        if isPacman == False:
            if self.scaredTimer(gameState) > 0:
                return {'distanceToInvader': -50,'successorScore': 400, 'stop': -100, 'deadEnd': -50, 'distanceToFood': -10, 'distanceToGhost': -60, 'distanceToCapsule': -50,'numCarrying': 0, 'stayWithGhostTimer': -2, 'score': 100}
            else:
                return {'distanceToTeammate':2,'distanceToInvader': -1000,'successorScore': 400, 'stop': -100, 'deadEnd': -50, 'distanceToFood': -10, 'distanceToGhost': -60, 'distanceToCapsule': -50,'numCarrying': 0, 'stayWithGhostTimer': -2, 'score': 100}
        else:
            if self.isPowered(gameState):
                if self.poweredTime > 5:
                    return {'distanceToInvader': 100,'successorScore': 400, 'stop': -100, 'deadEnd': 0, 'distanceToFood': -20, 'distanceToGhost': 20, 'distanceToCapsule': 0,'numCarrying': -110, 'score': 100}
                else:
                    return {'distanceToInvader': 100, 'successorScore': 400, 'stop': -100, 'deadEnd': 0, 'distanceToFood': -10, 'distanceToGhost': -5, 'distanceToCapsule': 0,'numCarrying': -200, 'score': 100}
            else:
                return {'distanceToInvader': 100, 'successorScore': 400, 'stop': -10, 'deadEnd': -100, 'distanceToFood': -5, 'distanceToGhost': -25, 'distanceToCapsule': -70, 'numCarrying': -350,'stayWithGhostTimer': -2, 'score': 100}      
    
    def aTKevaluate(self, gameState, action):  
        features = self.getATKFeatures(gameState, action)
        weights = self.getATKWeights(gameState, action)
        return features * weights
    
    def simulation(self, gameState, depth):
        state = gameState.deepCopy()
        while depth > 0:
            depth -= 1
            actions = state.getLegalActions(self.index)
            actions.remove(Directions.STOP)
            rev = Directions.REVERSE[state.getAgentState(self.index).configuration.direction]
            # if only leaving the reverse direction, should not delete it
            if rev in actions and len(actions) > 1:
                actions.remove(rev)
            action = random.choice(actions)
            state = state.generateSuccessor(self.index, action)
        return self.aTKevaluate(state, Directions.STOP)
    
    def scaredTimer(self, gameState):
        return gameState.getAgentState(self.index).scaredTimer
    
    def removeStopAction(self,actions):
        newActions = []
        for a in actions:
            if a != "Stop":
                newActions.append(a)
        return newActions
      
    
    def isPacman(self, gameState):
        return gameState.getAgentState(self.index).isPacman
    
    #reuse the code in the baseline
    def getSuccessor(self, gameState, action):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        if pos != nearestPoint(pos):
            return successor.generateSuccessor(self.index, action)
        else:
            return successor
    
    def getVisibleGhostsPos(self, gameState):
        invadersPos = []
        for invader in self.getVisibleGhosts(gameState):
            if invader.getPosition() != None:
                x, y = invader.getPosition()
                invadersPos.append((x, y))
        return invadersPos
    
    def getVisibleGhosts(self, gameState):
        opponentsIndics = self.getOpponents(gameState)
        opponents = [gameState.getAgentState(i) for i in opponentsIndics]
        
        invaders = []
        for opponent in opponents:   
            if not opponent.isPacman and opponent.getPosition() != None:              
                invaders.append(opponent)        
        return invaders
    def getInvaders(self, gameState):
        opponentsIndics = self.getOpponents(gameState)
        opponents = [gameState.getAgentState(i) for i in opponentsIndics]
        
        invaders = []
        for opponent in opponents:
            
            if opponent.isPacman:
                
                invaders.append(opponent)        
        return invaders
    
    def getVisibleInvaders(self, gameState):        
        visibleInvaders = []
        for invader in self.getInvaders(gameState):
            
            if invader.getPosition() != None:
               
                visibleInvaders.append(invader)        
        return visibleInvaders
    def getVisibleInvadersPos(self, gameState):
        invadersPos = []
        for invader in self.getVisibleInvaders(gameState):
            x, y = invader.getPosition()
            invadersPos.append((x, y))
        return invadersPos
    