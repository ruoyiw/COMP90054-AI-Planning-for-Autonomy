# danielTeam.py
# ---------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

from captureAgents import CaptureAgent
import distanceCalculator
import random, util
from game import Directions
from util import nearestPoint
import sys

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'danielAgent2', second = 'danielAgent2'):
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
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class CaptureAgent1(CaptureAgent):
  """
  My first agent
  """
  def registerInitialState(self, gameState):
    # super(CaptureAgent1, self).registerInitialState(gameState)
    # Used for display functions
    import __main__
    if '_display' in dir(__main__):
      self.display = __main__._display

    # Tells us what team we are
    self.red = gameState.isOnRedTeam(self.index)

    # Distancer for calculating exact distances between different positions
    self.distancer = distanceCalculator.Distancer(gameState.data.layout)
    self.distancer.getMazeDistances()  # comment this out to forgo maze distance computation and use manhattan distances

    # Some relevant variables
    self.walls = gameState.getWalls()
    self.legalPositions = [p for p in self.walls.asList(False) if p[1] > 0]
    self.babies = self.getFoodYouAreDefending(gameState).asList()  # The food we are protecting, our babies
    self.beliefs = [util.Counter(), util.Counter(), util.Counter(), util.Counter()]
    self.isPacman = [gameState.getAgentState(i).isPacman for i in range(gameState.getNumAgents())]

    self.positionsStored = 10
    self.lastPositions = [(-1, -1)] * self.positionsStored
    self.lastPositionsIdx = 0

    # Initialize zero position of the opponents, beliefs of the opponents and pacman_land - ghost_land of the opponents
    w = self.walls.width
    h = self.walls.height
    if self.red:
      self.opponentZeroPos = [(w-2, h-2), (w-2, h-3), (w-2, h-4)]
      c = 0
      for idx in self.getOpponents(gameState):
        self.beliefs[idx][(w-2, 13 + c)] = 1
        c += 1
      self.ghostLand = w / 2
      self.pacmanLand = w / 2 - 1
      self.going_left = -1
    else:
      self.opponentZeroPos = [(1, 1), (1, 2), (1, 3)]
      c = 1
      for idx in self.getOpponents(gameState):
        self.beliefs[idx][(1, 1 + c)] = 1
        c -= 1
      self.ghostLand = w / 2 - 1
      self.pacmanLand = w / 2
      self.going_left = 1

    # Get list ghostlaand and pacmanland positions
    self.ghostLandPositions = []
    self.pacmanLandPositions = []
    for p in self.legalPositions:
      if p[0] == self.pacmanLand:
        self.pacmanLandPositions.append(p)
      elif p[0] == self.ghostLand:
        self.ghostLandPositions.append(p)

    # Distancer for calculating exact distances between different positions only going through defense positions
    self.distancerDefense = DefenseDistancer(gameState.data.layout)
    if self.red:
      self.distancerDefense.getMazeDistances(1, self.pacmanLand)
    else:
      self.distancerDefense.getMazeDistances(self.pacmanLand, w-2)
    # Example of use: getMazeDistanceDefense(self, p1, p2) or self.distancerDefense.getDistance(p1, p2)

    # Examine the map and divide it in rooms and doors
    self.examineMaze(gameState)
    # raw_input("Press Enter!")

  def getMazeDistanceDefense(self, p1, p2):
    """
    Get distance between two points going only through the defense land
    """
    try:
      return self.distancerDefense.getDistance(p1, p2)
    except Exception:
      return self.getMazeDistance(p1, p2)

  def examineMaze(self, gameState):
    """
    Examine map and create doors and rooms structure
    """
    w = self.walls.width
    h = self.walls.height
    walls = self.walls.deepCopy()
    food1 = self.getFoodYouAreDefending(gameState)
    food2 = self.getFood(gameState)

    # Save map as 0, 1, 2 and 3 (0:walls, 1:spaces, 2:babies, 3:food)
    for x in range(w):
      for y in range(h):
        if walls[x][y]:
          walls[x][y] = 0
        elif food1[x][y]:
          walls[x][y] = 2
        elif food2[x][y]:
          walls[x][y] = 2
        else:
          walls[x][y] = 1

    roomsDisplay = []
    # Detect doors and spaces. Spaces are now negative
    for x in range(w):
      for y in range(h):
        if walls[x][y] > 0:
          exitsNum = 0
          if walls[x][y - 1] != 0:
            exitsNum += 1
          if walls[x][y + 1] != 0:
            exitsNum += 1
          if walls[x - 1][y] != 0:
            exitsNum += 1
          if walls[x + 1][y] != 0:
            exitsNum += 1
          if exitsNum == 1 or exitsNum == 2:
            walls[x][y] = -1 * walls[x][y]
            roomsDisplay.append((x, y))
          elif exitsNum == 0:
            # We erase unaccessible cells
            walls[x][y] = 0
          else:
            # These are doors or big rooms, we leave them positive
            pass

    # Create roomsGraph: every room has a number, some cells and some doors
    roomsGraph = []
    doorsGraph = []
    for x in range(1, w - 1):
      for y in range(1, h - 1):
        if walls[x][y] < 0:
          spacesNum = 0
          if walls[x][y - 1] < 0:
            spacesNum += 1
          if walls[x][y + 1] < 0:
            spacesNum += 1
          if walls[x - 1][y] < 0:
            spacesNum += 1
          if walls[x + 1][y] < 0:
            spacesNum += 1
          if spacesNum < 2:
            endOfPath = False
            graphNode = {"path": [], "doors": [], "food": 0, "isBig": False}
            auxx = x
            auxy = y
            while not endOfPath:
              graphNode["path"].append((x, y))
              graphNode["food"] += -walls[x][y] - 1
              walls[x][y] = 0
              xx = x
              yy = y
              if walls[x][y - 1] < 0:
                yy = y - 1
              elif walls[x][y + 1] < 0:
                yy = y + 1
              elif walls[x - 1][y] < 0:
                xx = x - 1
              elif walls[x + 1][y] < 0:
                xx = x + 1
              else:
                endOfPath = True
              if walls[x][y - 1] > 0:
                if [(x, y - 1), []] not in doorsGraph:
                  graphNode["doors"].append(len(doorsGraph))
                  doorsGraph.append([(x, y - 1), []])
                else:
                  graphNode["doors"].append(doorsGraph.index([(x, y - 1), []]))
              if walls[x][y + 1] > 0:
                if [(x, y + 1), []] not in doorsGraph:
                  graphNode["doors"].append(len(doorsGraph))
                  doorsGraph.append([(x, y + 1), []])
                else:
                  graphNode["doors"].append(doorsGraph.index([(x, y + 1), []]))
              if walls[x - 1][y] > 0:
                if [(x - 1, y), []] not in doorsGraph:
                  graphNode["doors"].append(len(doorsGraph))
                  doorsGraph.append([(x - 1, y), []])
                else:
                  graphNode["doors"].append(doorsGraph.index([(x - 1, y), []]))
              if walls[x + 1][y] > 0:
                if [(x + 1, y), []] not in doorsGraph:
                  graphNode["doors"].append(len(doorsGraph))
                  doorsGraph.append([(x + 1, y), []])
                else:
                  graphNode["doors"].append(doorsGraph.index([(x + 1, y), []]))
              x = xx
              y = yy
            roomsGraph.append(graphNode)
            x = auxx
            y = auxy

    # Create doorsGraph: every door has a number, and goes to other rooms or other doors
    for j, door in enumerate(doorsGraph):
      for i, room in enumerate(roomsGraph):
        for aDoor in room["doors"]:
          if aDoor == j:
            doorsGraph[j][1] = doorsGraph[j][1] + [i]
      (x, y) = doorsGraph[j][0]
      adjacentCells = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
      adjacentDoors = []
      # Check adjacent doors and add them to the current door (door structure is [pos, adjRooms, adjDoors]
      for p in adjacentCells:
        # Skip if wall
        if self.walls[p[0]][p[1]]:
          continue
        # Skip if door
        isRoom = False
        for room in doorsGraph[j][1]:
          if p in roomsGraph[room]["path"]:
            isRoom = True
            break
        if not isRoom:
          # Add if existing door
          doorFound = False
          for i, neighborDoor in enumerate(doorsGraph):
            if neighborDoor[0] == p:
              adjacentDoors.append(i)
              doorFound = True
              break
          # Create if non existing door and add
          if not doorFound:
            adjacentDoors.append(len(doorsGraph))
            doorsGraph.append([p, []])
      doorsGraph[j].append(adjacentDoors)

    # Create doorsDistance: maps what doors can be accessed from other doors
    roomsMapper = {}
    doorsMapper = {}
    isRoom = util.Counter()
    for i, door in enumerate(doorsGraph):
      doorsMapper[door[0]] = i
      isRoom[door[0]] = 0
    for i, room in enumerate(roomsGraph):
      for p in room["path"]:
        roomsMapper[p] = i
        isRoom[p] = 1

    # Create self variables
    self.doorsGraph = doorsGraph
    self.roomsGraph = roomsGraph
    self.roomsMapper = roomsMapper
    self.doorsMapper = doorsMapper
    self.isRoom = isRoom

    # # Find dead ends (rooms with only one door)
    # deadRooms = {}
    # deadDoors = {}
    # # deaderDoors = {}
    # # deaderRooms = {}
    # for i, room in enumerate(roomsGraph):
    #   if len(room["doors"]) == 1:
    #     deadRooms[i] = room["doors"][0]
    #     deadDoors[room["doors"][0]] = 1
        # numdR = 0
        # aliveR = -1
        # for adjRoom in doorsGraph[room["doors"][0]][1]:
        #   if adjRoom not in deadRooms:
        #     numdR += 1
        #     aliveR = adjRoom
        # if numdR + len(doorsGraph[room["doors"][0]][2]) == 1:
        #   if aliveR >= 0:
        #     deaderRooms[aliveR] = room["doors"][0]
        #     for adjDoor in roomsGraph[aliveR]["doors"]:
        #       if adjDoor == room["doors"][0]:
        #         continue
        #       deaderDoors[adjDoor] = 1.0
        #   else:
        #     deaderDoors[doorsGraph[room["doors"][0]][2][0]] = 1.0


    # roomsCounter = [util.Counter(), util.Counter(), util.Counter(), util.Counter()]
    # for r in deaderRooms:
    #   for p in roomsGraph[r]["path"]:
    #     roomsCounter[0][p] = 0.4
    # for d in deaderDoors:
    #   roomsCounter[1][doorsGraph[d][0]] = 0.4
    # self.displayDistributionsOverPositions(roomsCounter)
    # raw_input("Press Enter to continue ...")


    # print deadDoors
    # print
    # print deadRooms
    # print "-----------------"

    # deadEndsChanged = True
    # while deadEndsChanged:
    #   deadEndsChanged = False
    #   for i, room in enumerate(roomsGraph):
    #     numAliveDoors = 0
    #     aliveDoor = 0
    #     deadDoor = []
    #     for door in room["doors"]:
    #       if door not in deadDoors:
    #         numAliveDoors += 1
    #         aliveDoor = door
    #       else:
    #         deadDoor.append(door)
    #     if numAliveDoors == 1:
    #       aliveRoom = 0
    #       aliveNeighborDoor = 0
    #       for door in deadDoor:
    #         # aliveNeighborDoor += len(doorsGraph[door][2])
    #         for neighborRoom in doorsGraph[door][1]:
    #           if neighborRoom not in deadRooms:
    #             aliveRoom += 1
    #       if aliveRoom == len(deadDoor):
    #         deadRooms[i] = aliveDoor
    #         deadDoors[aliveDoor] = 1
    #         deadEndsChanged = True
    #         roomsCounter = [util.Counter(), util.Counter(), util.Counter(), util.Counter()]
    #         roomsCounter[0][doorsGraph[aliveDoor][0]] = 1
    #         for p in room["path"]:
    #           roomsCounter[1][p] = 1
    #         for p in deadDoor:
    #           roomsCounter[2][doorsGraph[p][0]] = 1
    #         self.displayDistributionsOverPositions(roomsCounter)
    #         raw_input("Press Enter to continue ...")


    # Find dead ends (rooms with doors that only go to other dead ends, except one)
    # Danger, it is theoretically possible to have a map only with dead ends, which may make this crash
    # deadEndsChanged = True
    # while deadEndsChanged:
    #   deadEndsChanged = False
    #   for i, door in enumerate(doorsGraph):
    #     if i not in deadDoors:
    #       numOpenRooms = 0
    #       openRoom = 0
    #       for j, room in enumerate(door[1]):
    #         if room not in deadRooms:
    #           numOpenRooms += 1
    #           openRoom = j
    #       if numOpenRooms + len(door[2]) == 1:
    #         for room in door[1]:
    #           if room != openRoom:
    #             deadRooms[room] = i
    #         deadDoors[j] = 1
    #         deadEndsChanged = True
    #         roomsCounter = [util.Counter(), util.Counter(), util.Counter(), util.Counter()]
    #         roomsCounter[0][door[0]] = 1
    #         for rr in door[1]:
    #           print rr
    #           if rr in deadRooms:
    #             for p in roomsGraph[rr]["path"]:
    #               roomsCounter[1][p] = 1
    #           else:
    #             for p in roomsGraph[rr]["path"]:
    #               roomsCounter[3][p] = 1
    #         self.displayDistributionsOverPositions(roomsCounter)
    #         raw_input("Press Enter to continue ...")

    # print deadDoors
    # print
    # print deadRooms
    # print "-----------------"

    # roomsCounter = [util.Counter(), util.Counter(), util.Counter(), util.Counter()]
    # roomsCounter[1][(6, 9)] = 0.4
    # self.displayDistributionsOverPositions(roomsCounter)
    # raw_input("Press Enter to continue ...")

    # roomsCounter = [util.Counter(), util.Counter(), util.Counter(), util.Counter()]
    # for r in deadRooms:
    #   for p in roomsGraph[r]["path"]:
    #     roomsCounter[0][p] = 0.4
    # for d in deadDoors:
    #   roomsCounter[1][doorsGraph[d][0]] = 0.4
    # self.displayDistributionsOverPositions(roomsCounter)
    # raw_input("Press Enter to continue ...")

    # Show every room
    roomsCounter = [util.Counter(), util.Counter(), util.Counter(), util.Counter()]
    for room in roomsGraph:
      for p in room["path"]:
        if len(room["doors"]) > 1:
          roomsCounter[0][p] = 0.4
        else:
          roomsCounter[2][p] = 0.4
    # Show every door
    for door in doorsGraph:
      roomsCounter[1][door[0]] = 0.4
    # Display rooms and doors (red: rooms with at least one exit; orange: rooms with 1 exit; blue: doors
    self.displayDistributionsOverPositions(roomsCounter)
    # raw_input("Press Enter to continue ...")

  def getBeliefsCentroid(self, idx):
    """
    Get centroid (average point) of beliefs for an opponent
    """
    x = 0.0
    y = 0.0
    total = 0.0
    for p in self.beliefs[idx]:
      x += p[0]
      y += p[1]
      total += 1.0
    return (round(x / total), round(y / total))

  def getClosestPositionOpponent(self, idx, pos, defense=False):
    """
    Get closest possible position of the opponent according to beliefs (if more than one possible, picks one randomly)
    """
    minD = 10000
    opponentPos = [pos]
    for p in self.beliefs[idx]:
      if defense:
        d = self.getMazeDistanceDefense(pos, p)
      else:
        d = self.getMazeDistance(pos, p)
      if minD > d:
        minD = d
        opponentPos = [p]
      elif minD == d:
        opponentPos.append(p)
    return random.choice(opponentPos)

  def getMinimumDistanceOpponent(self, idx, pos, defense=False):
    """
    Get minimum possible distance to opponent
    """
    minD = 10000
    if defense:
      for p in self.beliefs[idx]:
        minD = min(minD, self.getMazeDistanceDefense(pos, p))
    else:
      for p in self.beliefs[idx]:
        minD = min(minD, self.getMazeDistance(pos, p))
    return minD

  def getMinimumDistancePacmanLand(self, pos):
    """
    Get minimum distance to middle of the board (my pacmanLand, opponents ghostLand)
    """
    minD = 10000
    for p in self.ghostLandPositions:
      minD = min(minD, self.getMazeDistance(pos, p))
    return minD

  def getSplitFoodList(self, gameState, margin=1):
    """
    Split food in top and bottom food, separated by median
    """
    foodList = self.getFood(gameState).asList()
    foodListY = [p[1] for p in foodList]
    med = median(foodListY)
    splitList = [[], []]
    for i, p in enumerate(foodList):
      if p[1] <= med - margin:
        splitList[0].append(p)
      elif p[1] > med + margin:
        splitList[1].append(p)
      else:
        splitList[0].append(p)
        splitList[1].append(p)
    return splitList

  def setOpponentToZeroPos(self, idx):
    """
    The opponent died, update its belief to its starting position
    """
    self.beliefs[idx] = util.Counter()
    for pos in self.opponentZeroPos:
      self.beliefs[idx][pos] = 1.0 / len(self.opponentZeroPos)

  def initializeBeliefsUniformly(self, gameState, idx):
    """
    Set all legal positions with equal probability
    """
    self.beliefs[idx] = util.Counter()
    for p in self.legalPositions:
      self.beliefs[idx][p] = 1.0
    self.beliefs[idx].normalize()

  def setBeliefs(self, position, idx):
    """
    Set beliefs of one opponent to one single position
    """
    self.beliefs[idx] = util.Counter()
    self.beliefs[idx][position] = 1.0

  def observe(self, observation, gameState, myPosition, idx):
    """
    Observe noisy distance for opponent and update beliefs according to them
    """
    noisyDistance = observation
    noZero = False
    for p in self.legalPositions:
      if self.beliefs[idx][p] <= 0:
        self.beliefs[idx].pop(p, None)
        continue
      trueDistance = util.manhattanDistance(p, myPosition)
      prob = gameState.getDistanceProb(trueDistance, noisyDistance)
      if prob > 0:
        self.beliefs[idx][p] *= prob
        noZero = True
      else:
        self.beliefs[idx].pop(p, None)
    if not noZero:
      self.initializeBeliefsUniformly(gameState, idx)
    self.beliefs[idx].normalize()

  def elapseTime(self, idx):
    """
    Update beliefs knowing that the opponent has mad a move
    """
    newBeliefs = util.Counter()
    for oldPos in self.legalPositions:
      if self.beliefs[idx][oldPos] <= 0:
        continue
      newPosDist = self.getPositionDistribution(oldPos)
      for newPos, prob in newPosDist.items():
        newBeliefs[newPos] += prob * self.beliefs[idx][oldPos]
    newBeliefs.normalize()
    self.beliefs[idx] = newBeliefs

  def getPositionDistribution(self, position):
    """
    From a position, return all the possible new positions after a move of the opponent with an
    equal probability distribution
    """
    dist = util.Counter()
    (x, y) = position
    total = 1.0
    dist[position] = 1.0

    if not self.walls[x + 1][y]:
      dist[(x + 1, y)] = 1.0
      total += 1.0
    if not self.walls[x - 1][y]:
      dist[(x - 1, y)] = 1.0
      total += 1.0
    if not self.walls[x][y + 1]:
      dist[(x, y + 1)] = 1.0
      total += 1.0
    if not self.walls[x][y - 1]:
      dist[(x, y - 1)] = 1.0
      total += 1.0
    dist[(x, y)] /= total
    if (x + 1, y) in dist.keys():
      dist[(x + 1, y)] /= total
    if (x - 1, y) in dist.keys():
      dist[(x - 1, y)] /= total
    if (x, y+ 1) in dist.keys():
      dist[(x, y + 1)] /= total
    if (x, y - 1) in dist.keys():
      dist[(x, y - 1)] /= total
    return dist

  def getEatenBabies(self, gameState):
    """
    Get the positions of the babies (the food we are protecting) that are gone (aka have been eaten by the opponent)
    and save them in eaten
    """
    eaten = []
    newFood = self.getFoodYouAreDefending(gameState)
    for pos in self.babies:
      if not newFood[pos[0]][pos[1]]:
        eaten.append(pos)
    return eaten

  def updateEatenOpponents1(self, gameState, idx):
    """
    Detect if teammate has eaten an opponent, and update beliefs accordingly
    """
    teammatePos = gameState.getAgentState((self.index + 2) % 4).getPosition()
    pos = gameState.getAgentState(idx).getPosition()
    if pos is None and len(self.beliefs[idx]) == 1 and self.beliefs[idx].keys()[0] == teammatePos:
      self.setOpponentToZeroPos(idx)
      return True
    return False

  def updateEatenOpponents2(self, gameState, chosenAction):
    """
    Detect if the agent has eaten an opponent after taking choseAction, and update beliefs accordingly
    """
    myNewPos = self.getSuccessor(gameState, chosenAction).getAgentState(self.index).getPosition()
    for idx in self.getOpponents(gameState):
      pos = gameState.getAgentState(idx).getPosition()
      if pos is not None and pos == myNewPos:
        self.setOpponentToZeroPos(idx)

  def trackGhosts(self, gameState):
    """
    Takes care of the beliefs of the opponents (updates our beliefs for every opponent)
    """

    # Get some values that we will use later
    myState = gameState.getAgentState(self.index)
    myPos = myState.getPosition()
    noisyDistances = gameState.getAgentDistances()
    eatenBabies = self.getEatenBabies(gameState)

    #  Track each opponent
    opponentFound = [False] * 4
    for idx in self.getOpponents(gameState):
      pos = gameState.getAgentState(idx).getPosition()

      # If we are close to opponents (we see them), update beliefs to one point
      if pos is not None:
        self.setBeliefs(pos, idx)
        opponentFound[idx] = True

      # If the teammate has eaten a ghost, update belief to initial position
      elif self.updateEatenOpponents1(gameState, idx):
        opponentFound[idx] = True
        print "Our teammate has eaten an opponent, yeah!"

      # If not, update beliefs taking into account opponents possible movements
      else:
        # elapseTime (update beliefs of opponent considering they have taken an action)
        self.elapseTime(idx)

        # If opponent has changed from ghost to pacman or viceversa (and haven't died), we know their x coordinate
        if self.isPacman[idx] != gameState.getAgentState(idx).isPacman:
          if self.isPacman[idx]: # Was pacman, now is ghost
            for pos in self.beliefs[idx].keys():
              if pos[0] != self.ghostLand:
                self.beliefs[idx].pop(pos, None)
          else: # Was ghost, now is pacman
            for pos in self.beliefs[idx].keys():
              if pos[0] != self.pacmanLand:
                self.beliefs[idx].pop(pos, None)
          self.beliefs[idx].normalize()

        # Get positions of me and my teammate
        pos0 = gameState.getAgentState(self.getTeam(gameState)[0]).getPosition()
        pos1 = gameState.getAgentState(self.getTeam(gameState)[1]).getPosition()
        # Remove impossible positions
        for p in self.beliefs[idx].keys():
          # We should see the opponents from there, if we don't they are not there
          if (pos0 is not None and util.manhattanDistance(p, pos0) <= 5) or (pos1 is not None and util.manhattanDistance(p, pos1) <= 5):
            self.beliefs[idx].pop(p, None)
          # There is still a food dot there, therefore the opponent is not there
          elif self.getFoodYouAreDefending(gameState)[p[0]][p[1]]:
            self.beliefs[idx].pop(p, None)
          # Our belief says the opponent could be a ghost when it is a pacman
          elif self.isPacman[idx] and p[0] * self.going_left < self.pacmanLand * self.going_left - 1:
            self.beliefs[idx].pop(p, None)
          # Our belief says the opponent could be a pacman when it is a ghost
          elif not self.isPacman[idx] and p[0] * self.going_left > self.ghostLand * self.going_left + 1:
            self.beliefs[idx].pop(p, None)

    # Calculate opponents that could have eaten the missing food
    eaters = [[], []]
    for i, pos in enumerate(eatenBabies):
      eater = []
      for idx in self.getOpponents(gameState):
        if opponentFound[idx]:
          continue
        if pos in self.beliefs[idx].keys() and self.beliefs[idx][pos] > 0:
          eater.append(idx)
      eaters[i] = eater
      if i > 1:
        break

    for idx in self.getOpponents(gameState):
      if not opponentFound[idx]:
        # If we are not close to opponents (we don't see them), check if only one ghost can have eaten the food
        newBelief = False
        # This dirty code just changes the ghost beliefs
        if len(eaters[0]) == 1:
          newBelief = True
          if len(eaters[1]) == 0:
            if eaters[0][0] == idx:
              self.setBeliefs(eatenBabies[0], idx)
            else:
              newBelief = False
          else: #1 || 2
            if eaters[0][0] == idx:
              self.setBeliefs(eatenBabies[0], idx)
            else:
              self.setBeliefs(eatenBabies[1], idx)
        elif len(eaters[1]) == 1:
          newBelief = True
          if len(eaters[0]) == 2:
            if eaters[1][0] == idx:
              self.setBeliefs(eatenBabies[1], idx)
            else:
              self.setBeliefs(eatenBabies[0], idx)
          else: # 0
            if eaters[1][0] == idx:
              self.setBeliefs(eatenBabies[1], idx)
            else:
              newBelief = False

        if not newBelief:
          # If we have not figured out the exact position, use noisy distance that we have
          self.observe(noisyDistances[idx], gameState, myPos, idx)

    # This is to see all the possible positions where the opponents may be, all probabilities are turned to one
    beliefs = [util.Counter(), util.Counter(), util.Counter(), util.Counter()]
    for idx, bel in enumerate(self.beliefs):
      for p in bel:
        if bel[p] > 0:
          beliefs[idx][p] = 1
          # beliefs[idx][p] = self.beliefs[idx][p]

    self.displayDistributionsOverPositions(beliefs)

  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a).
    """

    # Track opponents position
    self.trackGhosts(gameState)

    actions = gameState.getLegalActions(self.index)
    # actions.remove(Directions.STOP)

    # You can profile your evaluation time by uncommenting these lines
    values = [self.evaluate(gameState, a) for a in actions]

    # Trick to avoid getting stuck in the same position for too long
    okValues = []
    okActions = []
    for i, a in enumerate(actions):
      newPos = self.getSuccessor(gameState, a).getAgentState(self.index).getPosition()
      # If any newPos is in lastPositions more than twice, we remove it from the list
      if self.lastPositions.count(newPos) <= 2:
        okValues.append(values[i])
        okActions.append(a)

    # Choose best action from list of actions
    try:
        maxValue = max(okValues)
        bestActions = [a for a, v in zip(okActions, okValues) if v == maxValue]
    except ValueError:
        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]
    chosenAction = random.choice(bestActions)

    print "BEST ACTION:", chosenAction, maxValue, "\n--------------------------------------------------------------\n"
    # if chosenAction == Directions.STOP:
    #   raw_input("Stopped! Go check what happened")

    # Save current chosen position in lastPositions and advance the index
    self.lastPositions[self.lastPositionsIdx % self.positionsStored] = self.getSuccessor(gameState, chosenAction).getAgentState(self.index).getPosition()
    self.lastPositionsIdx += 1

    # If we are eating any ghost, update our future belief about it
    self.updateEatenOpponents2(gameState, chosenAction)
    # Update food eaten by opponents
    self.babies = self.getFoodYouAreDefending(gameState).asList()
    # Update self.isPacman
    self.isPacman = [self.getSuccessor(gameState, chosenAction).getAgentState(i).isPacman for i in range(gameState.getNumAgents())]

    return chosenAction

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """
    self.updateCurrentBehavior(gameState, action)
    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)
    # print "Ghost:   ", self.index
    # print "Behavior:", self.behavior
    # print "Action:  ", action
    # for f in features:
    #   if weights[f] != 0:
    #     print "{:<25}: {:<4} * {:<4} = {}".format(f, features[f], weights[f], features[f]*weights[f])
    # print "Result: ", features * weights
    # print
    return features * weights

  def updateCurrentBehavior(self, gameState, action):
    """
    Chooses the bahavior of the agent depending on the game state
    """
    self.behavior = "attack"

  def getFeatures(self, gameState, action):
    """
    Returns a counter of features for the state
    """
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)
    return features

  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate.  They can be either
    a counter or a dictionary.
    """
    return {'successorScore': 1.0}

class danielAgent2(CaptureAgent1):
  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """
  def updateCurrentBehavior(self, gameState, action):
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()
    teammateState = successor.getAgentState((self.index + 2) % 4)
    opponents = self.getOpponents(successor)
    opponentsStates = [successor.getAgentState(i) for i in self.getOpponents(successor)]

    # If I am in attack position
    if myState.isPacman:
      ghostsChasingMe = []
      for opponent in opponentsStates:
        # Opponent is close and is not scared and is a ghost (can eat us)
        if not opponent.isPacman and opponent.getPosition() is not None and opponent.scaredTimer <= 0:
          ghostsChasingMe.append(opponent.getPosition())
      # Opponents are close, better be careful
      if len(ghostsChasingMe) > 0:
        d = min([self.getMazeDistance(myPos, p) for p in ghostsChasingMe])
        if d < 5:
          self.behavior = "escape"
        else:
          self.behavior = "attack"
      # Opponents are far, better eat food as fast as possible
      else:
        self.behavior = "attack"
    # If I am in defense position
    else:
      opponentsAttacking = []
      for i, opponent in enumerate(opponentsStates):
        # Opponent is attacking and I am defending and I am not scared (I can eat opponent)
        if opponent.isPacman and myState.scaredTimer <= 0:
          opponentsAttacking.append(self.getClosestPositionOpponent(opponents[i], myPos))
      # Opponents are attacking and I am not scared and I am defending
      if len(opponentsAttacking) > 0:
        dOpponents = []
        for p in opponentsAttacking:
          dOpponents.append(self.getMazeDistanceDefense(myPos, p))
        dBorder = self.getMinimumDistancePacmanLand(myPos)
        if dBorder * 3 - sum(dOpponents) < -3:
          self.behavior = "attack"
        else:
          self.behavior = "defend"
      # Opponents are not attacking or I am scared
      else:
        self.behavior = "attack"

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    features['successorScore'] = self.getScore(successor)

    # Get features related to my team position and state
    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()
    myOldPos = gameState.getAgentState(self.index).getPosition()
    if abs(myPos[0] - myOldPos[0]) + abs(myPos[1] - myOldPos[1]) > 1:
      features["death"] = 1
    else:
      features["death"] = 0
    teammateState = successor.getAgentState((self.index + 2) % 4)
    teammatePos = teammateState.getPosition()
    features['distanceToTeammate'] = self.getMazeDistance(myPos, teammatePos)
    # If myPos is a dead room, add penalty
    if self.isRoom[myPos] == 1 and len(self.roomsGraph[self.roomsMapper[myPos]]["doors"]) == 1:
      features['positionIsDeadEnd'] = 1
    else:
      features['positionIsDeadEnd'] = 0
    if myState.isPacman: features['onDefense'] = 0
    else: features['onDefense'] = 1


    # Get features related to opponent positions
    opponents = self.getOpponents(successor)
    opponentsStates = [successor.getAgentState(i) for i in opponents]
    ghostsChasingMe = []
    for opponent in opponentsStates:
      # We are attacking and opponent is close and is not scared and is a ghost (can eat us)
      if myState.isPacman and not opponent.isPacman and opponent.getPosition() is not None and opponent.scaredTimer <= 0:
        ghostsChasingMe.append(opponent.getPosition())
    features['numDangerousDefenders'] = len(ghostsChasingMe)
    features['certainDeath'] = 0  # If we end next to an opponent so it can eat us this will be 1
    if len(ghostsChasingMe) > 0:
      dists = []
      for p in ghostsChasingMe:
        dists.append(self.getMazeDistance(myPos, p))
        if dists[-1] < 2:
          features['certainDeath'] = 1
      features['distanceDangerousDefender'] = min(dists)
    else:
      features['distanceDangerousDefender'] = 0
    # Computes distance to invaders (any opponent in defense board)
    invaders = [i for i in opponents if successor.getAgentState(i).isPacman]
    features['numInvaders'] = len(invaders)
    if len(invaders) > 0:
      dists = []
      for idx in invaders:
        # Compute distance from minimum possible distance according to beliefs
        dists.append(self.getMinimumDistanceOpponent(idx, myPos, defense=True))
      features['invaderDistance'] = min(dists)
    else:
      features['invaderDistance'] = 100
    oldOpponentPositions = [gameState.getAgentState(i).getPosition() for i in opponents]
    if myPos in oldOpponentPositions:
      print "I should have eaten someone!"
      features["opponentEaten"] = 1
    else:
      features["opponentEaten"] = 0

    # Get capsule features
    capsuleList = self.getCapsules(successor)
    if len(capsuleList) > 0:
      features["distanceToCapsule"] = min([self.getMazeDistance(myPos, capsule) for capsule in capsuleList])
    else:
      features["distanceToCapsule"] = 0
    oldCapsuleList = self.getCapsules(gameState)
    if myPos in oldCapsuleList:
      features["capsuleEaten"] = 1
    else:
      features["capsuleEaten"] = 0

    # Get food features
    foodList = self.getFood(successor).asList()
    if len(foodList) > 0: # This should always be True
      minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['distanceToFood'] = minDistance
    else:
      features['distanceToFood'] = 0
    oldFoodList = self.getFood(gameState).asList()
    if myPos in oldFoodList:
      features["foodEaten"] = 1
    else:
      features["foodEaten"] = 0

    # Get split food features (we split food in two groups, top and bottom, and we assign one to each team member)
    splitFoodList = self.getSplitFoodList(successor)
    myFoodList = splitFoodList[0]
    if self.index > 1 or len(foodList) <= 0:
      myFoodList = splitFoodList[1]
    if len(foodList) <= 0:
      myFoodList = splitFoodList[0]
    if len(myFoodList) > 0: # This should always be True
      minDistance = min([self.getMazeDistance(myPos, food) for food in myFoodList])
      features['distanceToMyFood'] = minDistance
    else:
      features['distanceToMyFood'] = 0

    # Get features for not dead food (food safe to eat)
    foodListNoDead = []
    for food in foodList:
      # If the food is not in a dead end
      if self.isRoom[food] == 0 or len(self.roomsGraph[self.roomsMapper[food]]["doors"]) > 1:
        foodListNoDead.append(food)
      # SafeFood refers to food in rooms with two exits (so we can theoretically escape if we are chased)
      try:
        features['distanceToSafeFood'] = min([self.getMazeDistance(myPos, food) for food in foodListNoDead])
      except ValueError:
        features['distanceToSafeFood'] = 100

    # Get action features
    if action == Directions.STOP: features['stop'] = 1
    else: features['stop'] = 0
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1
    else: features['reverse'] = 0

    return features

  def getWeights(self, gameState, action):
    """Weights for each state. These are the available features:
    'numInvaders'
    'invaderDistance'
    'successorScore'
    'distanceToTeammate'
    'positionIsDeadEnd'
    'numDangerousDefenders'
    'certainDeath'
    'death'
    'distanceDangerousDefender'
    'opponentEaten'
    'distanceToCapsule'
    'capsuleEaten'
    'foodEaten'
    'distanceToFood'
    'distanceToMyFood'
    'distanceToSafeFood'
    'distanceToFood'
    'stop'
    'reverse'
    """

    if self.behavior == "attack":
      return {'successorScore':            100,
              'distanceToTeammate':        0.9,
              'positionIsDeadEnd':         -0.1,
              'numInvaders':               0,
              'invaderDistance':           0,
              'numDangerousDefenders':     -1,
              'certainDeath':              -100,
              'death':                     -150,
              'distanceDangerousDefender': 1,
              'opponentEaten':             50,
              'distanceToCapsule':         -0.5,
              'capsuleEaten':              1,
              'foodEaten':                 0.9,
              'distanceToFood':            -1,
              'distanceToMyFood':          -1,
              'distanceToSafeFood':        0,
              'onDefense':                 0,
              'stop':                      -2.5,
              'reverse':                   0}

    if self.behavior == "defend":
      return {'successorScore':            0,
              'distanceToTeammate':        0.9,
              'positionIsDeadEnd':         0.1,
              'numInvaders':               -100,
              'invaderDistance':           -1,
              'numDangerousDefenders':     0,
              'certainDeath':              0,
              'death':                     -150,
              'distanceDangerousDefender': 0,
              'opponentEaten':             50,
              'distanceToCapsule':         0,
              'capsuleEaten':              0,
              'foodEaten':                 0,
              'distanceToFood':            0,
              'distanceToMyFood':          -0.2,
              'distanceToSafeFood':        0,
              'onDefense':                 10,
              'stop':                      -1.5,
              'reverse':                   -0.3}

    if self.behavior == "escape":
      return {'successorScore':            100,
              'distanceToTeammate':        0.9,
              'positionIsDeadEnd':         -1.5,
              'numInvaders':               0,
              'invaderDistance':           0,
              'numDangerousDefenders':     -2,
              'certainDeath':              -100,
              'death':                     -150,
              'distanceDangerousDefender': 2,
              'opponentEaten':             50,
              'distanceToCapsule':         -1.1,
              'capsuleEaten':              3,
              'foodEaten':                 1,
              'distanceToFood':            0,
              'distanceToMyFood':          0,
              'distanceToSafeFood':        -1,
              'onDefense':                 0,
              'stop':                      -1.5,
              'reverse':                   0}

    # Default behavior
    return {'successorScore': 100,
            'distanceToTeammate': 0,
            'positionIsDeadEnd': 0,
            'numInvaders': 0,
            'invaderDistance': 0,
            'numDangerousDefenders': 0,
            'certainDeath': 0,
            'distanceDangerousDefender': 0,
            'opponentEaten': 0,
            'distanceToCapsule': 0,
            'capsuleEaten': 0,
            'foodEaten': 0,
            'distanceToFood': 0,
            'distanceToMyFood': -1,
            'distanceToSafeFood': 0,
            'onDefense': 0,
            'stop': 0,
            'reverse': 0}


class danielAgent1(CaptureAgent1):
  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """
  def updateCurrentBehavior(self, gameState, action):
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()
    teammateState = successor.getAgentState((self.index + 2) % 4)
    teammatePos = teammateState.getPosition()
    opponents = self.getOpponents(successor)
    opponentsStates = [successor.getAgentState(i) for i in self.getOpponents(successor)]

    # If I am in attack position
    if myState.isPacman:
      ghostsChasingMe = []
      for opponent in opponentsStates:
        # Opponent is close and is not scared and is a ghost (can eat us)
        if not opponent.isPacman and opponent.getPosition() is not None and opponent.scaredTimer <= 0:
          ghostsChasingMe.append(opponent.getPosition())
      # Opponents are close, better be careful
      if len(ghostsChasingMe) > 0:
        d = min([self.getMazeDistance(myPos, p) for p in ghostsChasingMe])
        if d < 5:
          self.behavior = "escape"
        else:
          self.behavior = "attack"
      # Opponents are far, better eat food as fast as possible
      else:
        self.behavior = "attack"
    # If I am in defense position
    else:
      opponentsAttacking = []
      for i, opponent in enumerate(opponentsStates):
        # Opponent is attacking and I am defending and I am not scared (I can eat opponent)
        if opponent.isPacman and myState.scaredTimer <= 0:
          opponentsAttacking.append(self.getClosestPositionOpponent(opponents[i], myPos))
      # Opponents are attacking and I am not scared and I am defending
      if len(opponentsAttacking) > 0:
        dOpponents = []
        for p in opponentsAttacking:
          dOpponents.append(self.getMazeDistanceDefense(myPos, p))
        dBorder = self.getMinimumDistancePacmanLand(myPos)
        if dBorder * 3 - sum(dOpponents) < -3:
          self.behavior = "attack"
        else:
          self.behavior = "defend"
      # Opponents are not attacking or I am scared
      else:
        self.behavior = "attack"

  def getFeatures(self, gameState, action):
   if self.behavior == "attack":
     return self.getFeaturesAttack(gameState, action)
   if self.behavior == "defend":
     return self.getFeaturesDefend(gameState, action)
   if self.behavior == "escape":
     return self.getFeaturesEscape(gameState, action)
   # Default behavior
   return self.getFeaturesAttack(gameState, action)

  def getFeaturesAttack(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    teammateState = successor.getAgentState((self.index + 2) % 4)
    teammatePos = teammateState.getPosition()
    features['distanceToTeammate'] = self.getMazeDistance(myPos, teammatePos)

    # Compute distance to the nearest food
    # foodList = self.getFood(successor).asList()
    # if len(foodList) > 0: # This should always be True, but better safe than sorry
    #   myPos = successor.getAgentState(self.index).getPosition()
    #   minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
    #   features['distanceToFood'] = minDistance

    splitFoodList = self.getSplitFoodList(successor)
    foodList = splitFoodList[0]
    if self.index > 1 or len(foodList) <= 0:
      foodList = splitFoodList[1]
    if len(foodList) <= 0:
      foodList = splitFoodList[0]
    if len(foodList) > 0: # This should always be True, but better safe than sorry
      myPos = successor.getAgentState(self.index).getPosition()
      minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['distanceToFood'] = minDistance

    return features

  def getFeaturesEscape(self, gameState, action):
    """
    The idea is to avoid dead ends (paths that can make you get trapped) when we are being chased
    """
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    teammateState = successor.getAgentState((self.index + 2) % 4)
    teammatePos = teammateState.getPosition()
    features['distanceToTeammate'] = self.getMazeDistance(myPos, teammatePos)

    capsuleList = self.getCapsules(successor)
    if len(capsuleList) > 0:
      features["distanceToCapsule"] = min([self.getMazeDistance(myPos, capsule) for capsule in capsuleList])
    oldCapsuleList = self.getCapsules(gameState)
    if myPos in oldCapsuleList:
      features["capsuleEaten"] = 1

    # Compute distance to the nearest food
    splitFoodList = self.getSplitFoodList(successor)
    foodList = splitFoodList[0]
    if self.index > 1 or len(foodList) <= 0:
      foodList = splitFoodList[1]
    if len(foodList) <= 0:
      foodList = splitFoodList[0]

    # foodList = self.getFood(successor).asList()
    if len(foodList) > 0: # This should always be True, but better safe than sorry
      foodPositions = []
      for food in foodList:
        if self.isRoom[food] == 1:
          if len(self.roomsGraph[self.roomsMapper[food]]["doors"]) > 1:
            foodPositions.append(food)
        else:
          foodPositions.append(food)
      myPos = successor.getAgentState(self.index).getPosition()
      # If we are being chased, go only to get food in rooms with two exits (so we can theoretically escape)
      try:
        minDistance = min([self.getMazeDistance(myPos, food) for food in foodPositions])
      # If such rooms don't exist go to any food
      except ValueError:
        minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['distanceToFood'] = minDistance
      opponents = self.getOpponents(successor)
      opponentsStates = [successor.getAgentState(i) for i in opponents]

      # If myPos is a dead room, add penalty
      if myPos not in foodPositions:
        features['positionIsDeadRoom'] = 1

      ghostsChasingMe = []
      for opponent in opponentsStates:
        # Opponent is close and is not scared and is a ghost (can eat us)
        if not opponent.isPacman and opponent.getPosition() is not None and opponent.scaredTimer <= 0:
          ghostsChasingMe.append(opponent.getPosition())

      if len(ghostsChasingMe) > 0:
        dists = []
        for p in ghostsChasingMe:
          dists.append(self.getMazeDistance(myPos, p))
          if dists[-1] < 2:
            features['certainDeath'] = 1
        features['distanceToOpponent'] = min(dists)

    return features

  def getFeaturesDefend(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    teammateState = successor.getAgentState((self.index + 2) % 4)
    teammatePos = teammateState.getPosition()
    features['distanceToTeammate'] = self.getMazeDistance(myPos, teammatePos)

    # Computes whether we're on defense (1) or offense (0)
    features['onDefense'] = 1
    if myState.isPacman: features['onDefense'] = 0

    # Computes distance to invaders (any opponent in defense board
    invaders = [i for i in self.getOpponents(successor) if successor.getAgentState(i).isPacman]
    features['numInvaders'] = len(invaders)
    if len(invaders) > 0:
      dists = []
      for a in invaders:
        dists.append(self.getMinimumDistanceOpponent(a, myPos, defense=True))
      features['invaderDistance'] = min(dists)

    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    return features

  def getWeights(self, gameState, action):
    if self.behavior == "attack":
      return {'successorScore': 100, 'distanceToFood': -1, 'distanceToTeammate': 0.9}
    if self.behavior == "defend":
      return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2, 'distanceToTeammate': 0.9}
    if self.behavior == "escape":
      return {'successorScore': 100, 'distanceToFood': -1, 'certainDeath': -1000, 'distanceToOpponent': 2, 'distanceToTeammate': 0.9,
              'positionIsDeadRoom': -50, "distanceToCapsule": -1.5, "capsuleEaten": 2000}
    # Default behavior
    return {'successorScore': 100, 'distanceToFood': -1}

class OffensiveAgent1(CaptureAgent1):
  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)

    # Compute distance to the nearest food
    foodList = self.getFood(successor).asList()
    if len(foodList) > 0: # This should always be True, but better safe than sorry
      myPos = successor.getAgentState(self.index).getPosition()
      minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['distanceToFood'] = minDistance
    return features

  def getWeights(self, gameState, action):
    return {'successorScore': 100, 'distanceToFood': -1}

class DefensiveAgent1(CaptureAgent1):
  """
  A reflex agent that keeps its side Pacman-free. Again,
  this is to give you an idea of what a defensive agent
  could be like.  It is not the best or only way to make
  such an agent.
  """

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    # Computes whether we're on defense (1) or offense (0)
    features['onDefense'] = 1
    if myState.isPacman: features['onDefense'] = 0

    # Computes distance to invaders we can see
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    # directions = [a.getDirection() for a in enemies]
    features['numInvaders'] = len(invaders)
    if len(invaders) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)

    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    return features

  def getWeights(self, gameState, action):
    return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2}


class DefenseDistancer(distanceCalculator.Distancer):
  def __init__(self, layout, default=10000):
    self._distances = None
    self.default = default
    self.dc = DefenseDistanceCalculator(layout, self, default)

  def getMazeDistances(self, minX, maxX):
    self.dc.run(minX, maxX)

distanceMapDefense = {}
class DefenseDistanceCalculator(distanceCalculator.DistanceCalculator):
  def run(self, minX, maxX):
    global distanceMapDefense

    if self.layout.walls not in distanceMapDefense:
      distances = computeDistancesDefense(self.layout, minX, maxX)
      distanceMapDefense[self.layout.walls] = distances
    else:
      distances = distanceMapDefense[self.layout.walls]

    self.distancer._distances = distances

def computeDistancesDefense(layout, minX, maxX):
  allNodes = layout.walls.asList(False)

  # Remove unwanted nodes according to X coordinate
  koNodes = []
  for i, node in enumerate(allNodes):
    if node[0] < minX or node[0] > maxX:
      koNodes = [i] + koNodes
  for node in koNodes:
    allNodes.pop(node)

  # Calculate distances
  distances = {}
  for source in allNodes:
    dist = {}
    closed = {}
    for node in allNodes:
      dist[node] = sys.maxint
    import util
    queue = util.PriorityQueue()
    queue.push(source, 0)
    dist[source] = 0
    while not queue.isEmpty():
      node = queue.pop()
      if node in closed:
        continue
      closed[node] = True
      nodeDist = dist[node]
      adjacent = []
      x, y = node
      if not layout.isWall((x,y+1)):
        adjacent.append((x,y+1))
      if not layout.isWall((x,y-1)):
        adjacent.append((x,y-1) )
      if not layout.isWall((x+1,y)):
        adjacent.append((x+1,y) )
      if not layout.isWall((x-1,y)):
        adjacent.append((x-1,y))
      for other in adjacent:
        if not other in dist:
          continue
        oldDist = dist[other]
        newDist = nodeDist+1
        if newDist < oldDist:
          dist[other] = newDist
          queue.push(other, newDist)
    for target in allNodes:
      distances[(target, source)] = dist[target]
  return distances

def median(lst):
  sortedLst = sorted(lst)
  lstLen = len(lst)
  index = (lstLen - 1) // 2
  return sortedLst[index]
