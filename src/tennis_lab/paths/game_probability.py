"""
Functions for calculating game-level probabilities in tennis.

Functions:
----------
pathProbability           - probability that a given score path occurs during a game
probabilityServerWinsGame - probability that the server wins the game from a given score
loadCachedFunction        - loads a cached version of probabilityServerWinsGame
"""

import os, pickle
from copy import deepcopy

from typing import Callable, Literal, Optional
from tennis_lab.paths.game_path import GamePath
from tennis_lab.core.game_score import GameScore

def pathProbability(path         : GamePath,
                    playerServing: Literal[1,2],
                    probWinPoint : float) -> float:
    """
    Calculates the probability that a given score path occurs during a game.
    Takes as input the probability that the player serving wins a point.

    Parameters:
    -----------
    path          - the game score path whose probability we calculate
    playerServing - which player is serving this game (1 or 2)
    probWinPoint  - probability that the player serving wins a point

    Returns:
    --------
    The probability that the given score path occurs during a game.
    """
    if not isinstance(path, GamePath):
        raise ValueError("path must be a GamePath instance")
    if not isinstance(playerServing, int) or playerServing not in [1, 2]:
        raise ValueError("playerServing must be 1 or 2")
    if not isinstance(probWinPoint, (int, float)) or not (0 <= probWinPoint <= 1):
        raise ValueError("probWinPoint must be a number between 0 and 1")

    probPath = 1.0
    scores = path.scoreHistory        # the scores that make up the path
    for i in range(1, len(scores)):   # loop over score *changes*

        pointsServerCurr = scores[i  ].asPoints(pov=playerServing)[0]   # serving player # points now
        pointsServerPrev = scores[i-1].asPoints(pov=playerServing)[0]   # serving player # points previously
        serverWonPoint   = pointsServerCurr > pointsServerPrev          # did serving player win the point ?

        # multiply probs of score changes
        probPath *= probWinPoint if serverWonPoint else (1-probWinPoint)

    return probPath

def probabilityServerWinsGame(initScore     : GameScore,
                              playerServing : Literal[1, 2],
                              probWinPoint  : float) -> float:
    """
    Calculates the probability that the player serving wins the game from a given score.

    This probability is calculated the following way:
      + generate all possible game score paths starting from the given initial score
      + calculate the probability the serving player wins the game along each of these paths
      + sum up all these probabilities
    The calculation takes as input the probability that the player serving wins a point.

    NOTE:
    We don't actually generate *all* possible score paths, as - when playing using standard
    advantage rules - there is an infinite number of them. Path generation ends at deuce.
    For paths ending in deuce, we use a closed-form formula for the probability  of winning
    from deuce:
                      p^2 / (1 - 2*p*(1-p))
    where p is the probability of winning a point on serve. This formula is derived from the
    geometric series of deuce repetitions. For more details see:
        Data-Driven Tennis: The Statistics of Winning
        Part 1: How To Hold Your Serve
        https://medium.com/@nciordas25/data-driven-tennis-the-statistics-of-winning-7f1855a76a65

    Parameters:
    -----------
    initScore     - the initial score in the game
    playerServing - which player is serving this game (1 or 2)
    probWinPoint  - probability that the player serving wins a point
    """
    if not isinstance(initScore, GameScore):
        raise ValueError("initScore must be a GameScore instance")
    if not isinstance(playerServing, int) or playerServing not in [1, 2]:
        raise ValueError("playerServing must be 1 or 2")
    if not isinstance(probWinPoint, (int, float)) or not (0 <= probWinPoint <= 1):
        raise ValueError("probWinPoint must be a number between 0 and 1")

    # generate all possible game paths starting from the initial score
    allPaths = GamePath.generateAllPaths(initScore)

    # add up the probability of winning the game in each path
    probWinGame = 0.0
    for path in allPaths:

        # the probability of this path occurring
        probPath = pathProbability(path, playerServing, probWinPoint)

        # how did this path end ?
        lastScore = path.scoreHistory[-1]
        winner    = lastScore.winner
        deuce     = lastScore.isDeuce

        # the probability the serving player wins when reaching the end of this path is:
        #  1 if the path ends with the serving player winning the game
        #  0 if the path ends with the serving player losing the game
        #  p**2/(1-2*p*(1-p)) if this path ends in a deuce (this formula is proved elsewhere)
        if deuce:
            probWinFromDeuce = probWinPoint**2 / (1-2*probWinPoint*(1-probWinPoint))
            probWinPath      = probPath * probWinFromDeuce
        else:
            serverWon   = (winner == playerServing)
            probWinPath = probPath * (1.0 if serverWon else 0.0)

        probWinGame += probWinPath

    return probWinGame

def loadCachedFunction(initScore    : GameScore,
                       playerServing: Literal[1, 2])-> Optional[Callable[[float], float]]:
    """
    Loads a cached version of 'probabilityServerWinsGame()'.

    Evaluating 'probabilityServerWinsGame(...)' can be expensive, especially when called repeatedly,
    because it iterates over all possible score progressions. To avoid repeating this computation,
    the script 'scripts/cache-prob-win-game.py' pre-computes and caches the server's game-winning
    probability for every possible starting score and across a grid of point-winning probabilities.
    A 1-D interpolator is constructed from this grid and saved as a callable, which is loaded and
    returned by this function.

    Parameters:
    -----------
    initScore     - the initial score in the game
    playerServing - which player is serving this game (1 or 2)

    Returns:
    --------
    A callable that takes a single float argument (the probability that the server wins a point)
    and returns the probability that the player serving wins the game from the given initial score.
    Returns None if the cached function is not available.

    Example:
    --------
    f = loadCachedFunction(GameScore(0, 0), playerServing=1)
    prob_win_game = f(0.65)  # probability server wins game when winning 65% of points
    """
    if not isinstance(initScore, GameScore):
        raise ValueError("initScore must be a GameScore instance")
    if not isinstance(playerServing, int) or playerServing not in [1, 2]:
        raise ValueError("playerServing must be 1 or 2")

    # Cap the score to normalize deuces & advantages (e.g., 5-5 → 3-3, 5-4 → 4-3) 
    # as we only have cached data for an init score of 3-3 (but not for 4-4, 5-5, 6-6,...)
    cappedScore = deepcopy(initScore)
    cappedScore._cap_score()

    # Get the score from the server's perspective
    pointsServ, pointsRecv = cappedScore.asPoints(pov=playerServing)

    # Build the filename based on the score and scoring rules
    noAdRule = initScore._noAdRule
    fileName = f"prob_win_game_noad_{pointsServ}{pointsRecv}.pkl" if noAdRule else \
               f"prob_win_game_{pointsServ}{pointsRecv}.pkl"
               
    # Build the filepath
    DIRPATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data-cache')           
    filePath = os.path.join(DIRPATH, fileName)

    try:
        with open(filePath, "rb") as fh:
            probWinGameInterpFunction = pickle.load(fh)
            def wrapper(p: float) -> float:
                return probWinGameInterpFunction(p).item()
            return wrapper
    except Exception:
        return None
