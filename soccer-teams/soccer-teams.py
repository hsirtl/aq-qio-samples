#!/usr/bin/env python
# coding: utf-8

import json
from typing import List
from re import T 
from azure.quantum.optimization import Term, Problem, ProblemType
from azure.quantum import Workspace
from azure.quantum.optimization import SimulatedAnnealing, ParallelTempering, Tabu, HardwarePlatform, QuantumMonteCarlo


# Copy the settings for your workspace below
with open('appsettings.json') as f:
    config = json.load(f)
    workspace = Workspace (
        subscription_id = config.get("workspace").get("subscription_id"),
        resource_group = config.get("workspace").get("resource_group"),
        name = config.get("workspace").get("name"),
        location = config.get("workspace").get("location")
)


def getProblemData():
    with open('problem.json') as f:
        problemJson = json.load(f)
    problemData = problemJson.get("problem").get("data")
    return problemData


def getHamiltonianForSumOfWeights(listOfIndices, listOfWeights, sumOfWeights) -> List[Term]:
    numOfIndices = len(listOfIndices)
    terms: List[Term] = []

    for i in range(numOfIndices):
        terms.append(Term(c = 2 * listOfWeights[i] * listOfWeights[i], indices = [listOfIndices[i], listOfIndices[i]]))

    for i in range(numOfIndices-1):
        for j in range(i+1, numOfIndices):
            terms.append(Term(c = 2 * listOfWeights[i] * listOfWeights[j], indices = [listOfIndices[i], listOfIndices[j]]))

    for i in range(numOfIndices):
        terms.append(Term(c = - 2 * sumOfWeights * listOfWeights[i] - 2 * listOfWeights[i] * listOfWeights[i], indices = [listOfIndices[i]]))

    return terms


def getObjectiveTerms(problemData) -> List[Term]:
    terms:  List[Term] = []
    players = problemData.get("players")
    numberOfTeams = len(problemData.get("teams"))
    numberOfPlayers = len(problemData.get("players"))
    strengths = [player.get("strength") for player in players]

    for team in range(numberOfTeams):
        teamTerms = getHamiltonianForSumOfWeights([i for i in range(team * numberOfPlayers, team * numberOfPlayers + numberOfPlayers)], strengths, sum(strengths) / numberOfTeams)
        terms.extend(teamTerms)

    return terms


def getMaxOneOutOfTwoTerms(i, j, penalty):
    terms = []
    terms.append ( Term ( c = penalty, indices = [ i , j ] ) )

    return terms 


def getOnePlayerInOneTeamConstraintTerms(problemData):
    terms = []
    players = problemData.get("players")
    numberOfTeams = len(problemData.get("teams"))
    numberOfPlayers = len(players)
    penalty = 100

    for i in range(numberOfPlayers):
        for j in range(numberOfTeams - 1):
            for k in range(j + 1, numberOfTeams):
                idx1 = j * numberOfPlayers + i
                idx2 = k * numberOfPlayers + i
                terms.extend(getMaxOneOutOfTwoTerms(idx1, idx2, penalty))

    return terms


def getOneGoalkeeperPerTeamTerms(problemData):
    terms = []
    players = problemData.get("players")
    numberOfTeams = len(problemData.get("teams"))
    numberOfPlayers = len(players)
    goalkeeperIndices = []
    penalty = 100

    for i in range(numberOfPlayers):
        if players[i].get("isGoalkeeper") == "True":
            goalkeeperIndices.append(i)

    for team in range(numberOfTeams):
        for i in range(len(goalkeeperIndices) - 1):
            for j in range(i + 1, len(goalkeeperIndices)):
                idx1 = team * numberOfPlayers + goalkeeperIndices[i]
                idx2 = team * numberOfPlayers + goalkeeperIndices[j]
                terms.extend(getMaxOneOutOfTwoTerms(idx1, idx2, penalty))

    return terms


# create a cost function based on a problem statement
def createCostFunction(problemData):
    terms = []

    objectiveTerms = getObjectiveTerms(problemData)
    terms.extend(objectiveTerms)

    constraintTerms = getOnePlayerInOneTeamConstraintTerms(problemData)
    terms.extend(constraintTerms)

    constraintTerms = getOneGoalkeeperPerTeamTerms(problemData)
    terms.extend(constraintTerms)

    return terms


def extractSolution(problemData, result):
    config = result.get("configuration")
    players = problemData.get("players")
    teams = problemData.get("teams")
    numberOfPlayers = len(players)
    numberOfTeams = len(problemData.get("teams"))
    solution = {}
    solution["teams"] = []

    for teamidx in range(numberOfTeams):
        team = {}
        team["name"] = teams[teamidx]
        teamplayers = []
        teamstrength = 0
        for playeridx in range(numberOfPlayers):
            if (config[str(playeridx + teamidx * numberOfPlayers)] == 1):
                teamplayers.append(players[playeridx])
                teamstrength = teamstrength + players[playeridx].get("strength")
        team["players"] = teamplayers
        team["strength"] = teamstrength
        solution["teams"].append(team)

    return solution


def validateSolution(problem, solution):
    conflicts = False
    return not(conflicts)


def printProblem(problem):
    print(problem)


def printSolution(solution):
    teams = solution.get("teams")
    for team in teams:
        print("Team    :", team.get("name"))
        print("Strength:", team.get("strength"))
        print("Players : id     name        strength  isGoalkeeper")
        for player in team.get("players"):
            print("          {:<5}  {:10}  {:>8}  {:8}".format(player.get("id"), player.get("name"), player.get("strength"), player.get("isGoalkeeper")))


# read problem data
problemData = getProblemData()

isValidSolution = False

# create a cost function out of the problem data
terms = createCostFunction(problemData)

# submit the cost function to a solver
problem = Problem(name="problem", problem_type=ProblemType.pubo, terms=terms)
solver = SimulatedAnnealing(workspace, platform=HardwarePlatform.FPGA, timeout=5)
job = solver.submit(problem)
job.refresh()

# get the result
result = job.get_results()

# extract the solution generated by the solver
solution = extractSolution(problemData, result)

# validate the solution
isValidSolution = validateSolution(problemData, solution)
if isValidSolution:
    print ("Solution is valid.")
else:
    print ("Solution is not valid.")

# print the solution
printSolution(solution)
