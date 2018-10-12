# search.py
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


"""
In search.py, you will implement generic search algorithms which are called by
Pacman agents (in searchAgents.py).
"""

# COMP90054 AI Planning for Autonomy Assignment 1
# Student name: Ruoyi Wang
# Student No.: 683436


import util

class SearchProblem:
    """
    This class outlines the structure of a search problem, but doesn't implement
    any of the methods (in object-oriented terminology: an abstract class).

    You do not need to change anything in this class, ever.
    """

    def getStartState(self):
        """
        Returns the start state for the search problem.
        """
        util.raiseNotDefined()

    def isGoalState(self, state):
        """
          state: Search state

        Returns True if and only if the state is a valid goal state.
        """
        util.raiseNotDefined()

    def getSuccessors(self, state):
        """
          state: Search state

        For a given state, this should return a list of triples, (successor,
        action, stepCost), where 'successor' is a successor to the current
        state, 'action' is the action required to get there, and 'stepCost' is
        the incremental cost of expanding to that successor.
        """
        util.raiseNotDefined()

    def getCostOfActions(self, actions):
        """
         actions: A list of actions to take

        This method returns the total cost of a particular sequence of actions.
        The sequence must be composed of legal moves.
        """
        util.raiseNotDefined()


def tinyMazeSearch(problem):
    """
    Returns a sequence of moves that solves tinyMaze.  For any other maze, the
    sequence of moves will be incorrect, so only use this for tinyMaze.
    """
    from game import Directions
    s = Directions.SOUTH
    w = Directions.WEST
    return  [s, s, w, s, w, w, s, w]

def depthFirstSearch(problem):
    """
    Search the deepest nodes in the search tree first.

    Your search algorithm needs to return a list of actions that reaches the
    goal. Make sure to implement a graph search algorithm.

    To get started, you might want to try some of these simple commands to
    understand the search problem that is being passed in:

    print "Start:", problem.getStartState()
    print "Is the start a goal?", problem.isGoalState(problem.getStartState())
    print "Start's successors:", problem.getSuccessors(problem.getStartState())
    """
    "*** YOUR CODE HERE ***"
    #util.raiseNotDefined()
    print "Start:", problem.getStartState()
    print "Is the start a goal?", problem.isGoalState(problem.getStartState())
    #print "Start's successors:", problem.getSuccessors(problem.getStartState())

    stack = util.Stack()
    startState = problem.getStartState()
    stack.push((startState, [], 0))
    visitedStates = []

    while not stack.isEmpty():
        state, totalActions, totalCost = stack.pop()
        if problem.isGoalState(state):
            #print "All actions: ", totalActions
            return totalActions
        visitedStates.append(state)
        successors = problem.getSuccessors(state)
        for nextState, action, stepCost in successors:
            if (not nextState in visitedStates):
                stack.push((nextState, totalActions + [action], totalCost + stepCost))
    # failed to find the goal
    return []



def breadthFirstSearch(problem):
    """Search the shallowest nodes in the search tree first."""
    "*** YOUR CODE HERE ***"
    # util.raiseNotDefined()
    queue = util.Queue()
    startState = problem.getStartState()
    queue.push((startState, [], 0))  # state, total actions, total cost
    visitedStates = [startState]

    while not queue.isEmpty():
        state, totalActions, totalCost = queue.pop()
        if problem.isGoalState(state):
            #print "All actions: ", totalActions
            return totalActions
        successors = problem.getSuccessors(state)
        for nextState, action, stepCost in successors:
            if (not nextState in visitedStates):
                queue.push((nextState, totalActions + [action], totalCost + stepCost))
                visitedStates.append(nextState)
    # failed to find the goal
    return []



def uniformCostSearch(problem):
    "Search the node of least total cost first. "
    "*** YOUR CODE HERE ***"
    # util.raiseNotDefined()
    pQueue = util.PriorityQueue()
    startState = problem.getStartState()
    pQueue.push((startState, [], 0), 0)
    visitedStates = [(startState, 0)]

    while not pQueue.isEmpty():
        state, totalActions, totalCost = pQueue.pop()
        if problem.isGoalState(state):
            #print "All actions: ", totalActions
            return totalActions
        successors = problem.getSuccessors(state)
        for nextState, action, stepCost in successors:
            isVisited = False
            totalCost = problem.getCostOfActions(totalActions + [action])
            for node in range(len(visitedStates)):
                existedState, existedCost = visitedStates[node]
                if (nextState == existedState) and (existedCost <= totalCost):
                    isVisited = True
            if not isVisited:
                pQueue.update((nextState, totalActions + [action], totalCost), totalCost)
                visitedStates.append((nextState, totalCost))
    # failed to find the goal
    return []



def nullHeuristic(state, problem=None):
    """
    A heuristic function estimates the cost from the current state to the nearest
    goal in the provided SearchProblem.  This heuristic is trivial.
    """
    return 0

def aStarSearch(problem, heuristic=nullHeuristic):
    """Search the node that has the lowest combined cost and heuristic first."""
    "*** YOUR CODE HERE ***"
    #util.raiseNotDefined()
    pQueue = util.PriorityQueue()
    startState = problem.getStartState()
    pQueue.push((startState, [], 0), heuristic(startState, problem))
    visitedStates = [(startState, 0 + heuristic(startState, problem))]

    while not pQueue.isEmpty():
        state, totalActions, totalCost = pQueue.pop()
        if problem.isGoalState(state):
            #print "All actions: ", totalActions
            return totalActions

        successors = problem.getSuccessors(state)
        for nextState, action, stepCost in successors:
            isVisited = False
            totalCost = problem.getCostOfActions(totalActions + [action])
            fValue = totalCost + heuristic(nextState, problem)
            for node in range(len(visitedStates)):
                existedState, existedFValue = visitedStates[node]
                if (nextState == existedState) and (fValue >= existedFValue):
                    isVisited = True
            if not isVisited:
                pQueue.update((nextState, totalActions + [action], totalCost), fValue)
                visitedStates.append((nextState, fValue))
    # failed to find the goal
    return []




# Abbreviations
bfs = breadthFirstSearch
dfs = depthFirstSearch
astar = aStarSearch
ucs = uniformCostSearch
