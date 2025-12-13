"""
Functions for Monte Carlo simulation of a tiebreak in a tennis match.

Functions:
----------
probabilityP1WinsTiebreak - probability that Player1 wins the tiebreak from a given score
"""

import random
from   typing import Literal

from tennis_lab.core.tiebreak       import Tiebreak
from tennis_lab.core.tiebreak_score import TiebreakScore

def probabilityP1WinsTiebreak(initScore    : TiebreakScore,
                              playerServing: Literal[1, 2],
                              probWinPoint1: float,
                              probWinPoint2: float,
                              numSims      : int) -> float:
    """
    Simulates playing multiple tiebreaks and calculates
    the probability that Player1 wins the tiebreak.
    Takes as input the probability of each player winning the point when serving.
    
    Parameters:
    -----------
    initScore     - the initial score in the tiebreak
    playerServing - which player is serving next point (1 or 2)
    probWinPoint1 - probability that Player1 wins the point when serving
    probWinPoint2 - probability that Player2 wins the point when serving
    numSims       - number of tiebreaks to simulate

    Returns:
    --------
    The fraction of tiebreaks won by Player1.
    """
    if not isinstance(initScore, TiebreakScore):
        raise ValueError(f"Invalid initScore: must be a TiebreakScore instance.")
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
        tiebreak = Tiebreak(playerServing, initScore._isSuper, initScore)
        while not tiebreak.isOver:
            server         = tiebreak.servesNext
            probWinPoint   = probWinPoint1 if server == 1 else probWinPoint2
            serverWonPoint = random.random() < probWinPoint
            pointWinner    = server if serverWonPoint else (3 - server)
            tiebreak.recordPoint(pointWinner)
        if tiebreak.winner == 1:
            numWins += 1
    return numWins / numSims
