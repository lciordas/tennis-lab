"""
Functions for Monte Carlo simulation of a game in a tennis match.

Functions:
----------
probabilityServerWinsGame - probability that the server wins the game from a given score
"""

import random
from   typing import Literal

from tennis_lab.core.game       import Game
from tennis_lab.core.game_score import GameScore

def probabilityServerWinsGame(initScore    : GameScore,
                              playerServing: Literal[1, 2],
                              probWinPoint : float,
                              numSims      : int) -> float:
    """
    Simulates playing multiple games and calculates the probability that the player serving wins the game.
    Takes as input the probability that the player serving wins a point.

    Parameters:
    -----------
    initScore     - the initial score in the game
    playerServing - which player is serving this game (1 or 2)
    probWinPoint  - probability that the player serving wins a point
    numSims       - number of games to simulate

    Returns:
    --------
    The fraction of games won by the player serving.
    """
    if not isinstance(initScore, GameScore):
        raise ValueError(f"Invalid initScore: must be a GameScore instance.")
    if playerServing not in (1, 2):
        raise ValueError(f"Invalid playerServing: {playerServing}. Must be 1 or 2.")
    if not (0 <= probWinPoint <= 1):
        raise ValueError(f"Invalid probWinPoint: {probWinPoint}. Must be between 0 and 1.")
    if not isinstance(numSims, int) or numSims <= 0:
        raise ValueError(f"Invalid numSims: {numSims}. Must be a positive integer.")

    numWins = 0
    for _ in range(numSims):
        game = Game(playerServing, initScore)
        while not game.isOver:
            serverWonPoint = random.random() < probWinPoint
            game.recordPoint(playerServing if serverWonPoint else (3 - playerServing))
        if game.winner == playerServing:
            numWins += 1
    return numWins / numSims
