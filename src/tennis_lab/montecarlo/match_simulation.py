"""
Functions for Monte Carlo simulation of a tennis match.

Functions:
----------
probabilityP1WinsMatch - probability that Player1 wins the match from a given score
"""

import random
from   typing import Literal

from tennis_lab.core.match       import Match
from tennis_lab.core.match_score import MatchScore

def probabilityP1WinsMatch(initScore    : MatchScore,
                           playerServing: Literal[1, 2],
                           probWinPoint1: float,
                           probWinPoint2: float,
                           numSims      : int) -> float:
    """
    Simulates playing multiple tennis matches and calculates the probability that Player1 wins the match.
    Takes as input the probability of each player winning the point when serving.

    Parameters:
    -----------
    initScore     - the initial score in the match
    playerServing - which player is serving next point (1 or 2)
    probWinPoint1 - probability that Player1 wins the point when serving
    probWinPoint2 - probability that Player2 wins the point when serving
    numSims       - number of matches to simulate

    Returns:
    --------
    The fraction of matches won by Player1.
    """
    if not isinstance(initScore, MatchScore):
        raise ValueError(f"Invalid initScore: must be a MatchScore instance.")
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
        match = Match(playerServing, initScore._matchFormat, initScore)
        while not match.isOver:
            server         = match.servesNext
            probWinPoint   = probWinPoint1 if server == 1 else probWinPoint2
            serverWonPoint = random.random() < probWinPoint
            pointWinner    = server if serverWonPoint else (3 - server)
            match.recordPoint(pointWinner)
        if match.winner == 1:
            numWins += 1
    return numWins / numSims
