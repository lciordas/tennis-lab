"""
Functions for Monte Carlo simulation of a set in a tennis match.

Functions:
----------
probabilityP1WinsSet - probability that Player1 wins the set from a given score
"""

import random
from   typing import Literal

from tennis_lab.core.set       import Set
from tennis_lab.core.set_score import SetScore

def probabilityP1WinsSet(initScore    : SetScore,
                         playerServing: Literal[1, 2],
                         probWinPoint1: float,
                         probWinPoint2: float,
                         numSims      : int) -> float:
    """
    Simulates playing multiple sets and calculates the probability that Player1 wins the set.
    Takes as input the probability of each player winning the point when serving.

    Parameters:
    -----------
    initScore     - the initial score in the set
    playerServing - which player is serving next point (1 or 2)
    probWinPoint1 - probability that Player1 wins the point when serving
    probWinPoint2 - probability that Player2 wins the point when serving
    numSims       - number of sets to simulate

    Returns:
    --------
    The fraction of sets won by Player1.
    """
    if not isinstance(initScore, SetScore):
        raise ValueError(f"Invalid initScore: must be a SetScore instance.")
    if playerServing not in (1, 2):
        raise ValueError(f"Invalid playerServing: {playerServing}. Must be 1 or 2.")
    if not (0 <= probWinPoint1 <= 1):
        raise ValueError(f"Invalid probWinPoint1: {probWinPoint1}. Must be between 0 and 1.")
    if not (0 <= probWinPoint2 <= 1):
        raise ValueError(f"Invalid probWinPoint2: {probWinPoint2}. Must be between 0 and 1.")
    if not isinstance(numSims, int) or numSims <= 0:
        raise ValueError(f"Invalid numSims: {numSims}. Must be a positive integer.")

    numWins = 0
    for _ in range(numSims):
        tennisSet = Set(playerServing, initScore._isFinalSet, initScore)
        while not tennisSet.isOver:
            server         = tennisSet.servesNext
            probWinPoint   = probWinPoint1 if server == 1 else probWinPoint2
            serverWonPoint = random.random() < probWinPoint
            pointWinner    = server if serverWonPoint else (3 - server)
            tennisSet.recordPoint(pointWinner)
        if tennisSet.winner == 1:
            numWins += 1
    return numWins / numSims
