#!/usr/bin/env python
# coding: utf-8

import json
from re import T
from azure.quantum.optimization import Term, Problem, ProblemType
from azure.quantum import Workspace
from azure.quantum.optimization import SimulatedAnnealing # Change this line to match the Azure Quantum Optimization solver type you wish to use


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


# create a cost function based on a problem statement
def createCostFunction(problemData):
    print("createCostFunction")
    terms = []
    terms.append(Term(c = 1, indices = [0]))

    return terms


def extractSolution(result):
    print("extractSolution")
    config = result.get("configuration")

    result = {}

    return result


def validateSolution(problem, solution):
    print("validateSolution")
    conflicts = False

    return not(conflicts)


def printProblem(problem):
    print("printProblem")
    print(problem)


def printSolution(solution):
    print("printSolution")
    print(solution)


# read problem data
problemData = getProblemData()

isValidSolution = False

# create a cost function out of the problem data
terms = createCostFunction(problemData)

# submit the cost function to a solver
problem = Problem(name="problem", problem_type=ProblemType.pubo, terms=terms)
solver = SimulatedAnnealing(workspace, timeout=100, seed=22)
job = solver.submit(problem)
job.refresh()

# get the result
result = job.get_results()

# extract the solution generated by the solver
solution = extractSolution(result)

# validate the solution
isValidSolution = validateSolution(problemData, solution)
if isValidSolution:
    print ("Solution is valid.")
else:
    print ("Solution is not valid.")

# print the solution
printSolution(solution)
