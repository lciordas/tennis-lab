"""
Functions for calculating tiebreak-level probabilities in tennis.

Functions:
----------
pathProbability           - probability that a given score path occurs during a tiebreak
probabilityP1WinsTiebreak - probability that P1 wins the tiebreak from a given score
loadCachedFunction        - loads a cached version of probabilityP1WinsTiebreak
"""

import os, pickle
from copy import deepcopy
from typing import Callable, Literal, Optional
from tennis_lab.paths.tiebreak_path import TiebreakPath
from tennis_lab.core.tiebreak_score import TiebreakScore

def pathProbability(path          : TiebreakPath,
                    probWinPointP1: float,
                    probWinPointP2: float) -> float:
    """
    Calculates the probability that a given score path occurs during a tiebreak.
    Takes as input the probability that each player wins the point when serving.

    Parameters:
    -----------
    path           - the tiebreak score path whose probability we calculate
    probWinPointP1 - probability that Player1 wins the point when serving
    probWinPointP2 - probability that Player2 wins the point when serving

    Returns:
    --------
    The probability that the given score path occurs during a tiebreak.
    """
    if not isinstance(path, TiebreakPath):
        raise ValueError("path must be a TiebreakPath instance")
    if not isinstance(probWinPointP1, (int, float)) or not (0 <= probWinPointP1 <= 1):
        raise ValueError("probWinPointP1 must be a number between 0 and 1")
    if not isinstance(probWinPointP2, (int, float)) or not (0 <= probWinPointP2 <= 1):
        raise ValueError("probWinPointP2 must be a number between 0 and 1")

    probPath = 1.0
    entries  = path.scoreHistory          # the entries that make up the path
    for i in range(1, len(entries)):      # loop over score *changes*

        pointsP1Curr = entries[i  ].score.asPoints(pov=1)[0]   # Player1 # of points now
        pointsP1Prev = entries[i-1].score.asPoints(pov=1)[0]   # Player1 # of points previously
        P1served     = entries[i-1].playerServing == 1         # did Player1 serve for the point?
        P1wonPoint   = pointsP1Curr > pointsP1Prev             # did Player1 win the point?
        P2wonPoint   = not P1wonPoint

        # calculate the probability of this score change
        if P1served:
            probScoreChange = probWinPointP1 if P1wonPoint else (1 - probWinPointP1)
        else:
            probScoreChange = probWinPointP2 if P2wonPoint else (1 - probWinPointP2)

        # multiply probs of score changes
        probPath *= probScoreChange

    return probPath

def probabilityP1WinsTiebreak(initScore      : TiebreakScore,
                              playerServing  : Literal[1, 2],
                              probWinPointP1 : float,
                              probWinPointP2 : float) -> float:
    """
    Calculates the probability that Player1 wins the tiebreak from a given score.

    This probability is calculated the following way:
      + generate all possible tiebreak score paths starting from the given initial score
      + calculate the probability that Player1 wins the tiebreak along each path
      + sum up all these probabilities
    The calculation takes as input the probability that each player wins a point when serving.

    NOTE:
    We don't actually generate *all* possible score paths, as there is an infinite number
    of them (due to deuce repetitions). Path generation ends at 6-6 (regular) or 9-9 (super).
    For paths ending in deuce, we use a closed-form formula for the probability of winning
    from deuce. For details see:
        Data-Driven Tennis: The Statistics of Winning
        Part 2: How To Win a Set
        https://medium.com/@nciordas25/data-driven-tennis-the-statistics-of-winning-2f16ae57739a

    Parameters:
    -----------
    initScore      - the initial score in the tiebreak
    playerServing  - which player is serving the next point (1 or 2)
    probWinPointP1 - probability that Player1 wins the point when serving
    probWinPointP2 - probability that Player2 wins the point when serving

    Returns:
    --------
    The probability that Player1 wins the tiebreak from the given score.
    """
    if not isinstance(initScore, TiebreakScore):
        raise ValueError("initScore must be a TiebreakScore instance")
    if not isinstance(playerServing, int) or playerServing not in [1, 2]:
        raise ValueError("playerServing must be 1 or 2")
    if not isinstance(probWinPointP1, (int, float)) or not (0 <= probWinPointP1 <= 1):
        raise ValueError("probWinPointP1 must be a number between 0 and 1")
    if not isinstance(probWinPointP2, (int, float)) or not (0 <= probWinPointP2 <= 1):
        raise ValueError("probWinPointP2 must be a number between 0 and 1")

    # generate all possible paths starting from the initial score
    allPaths = TiebreakPath.generateAllPaths(initScore, playerServing)

    # add up the probability of P1 winning the tiebreak along each path
    probWinTiebreak = 0.0
    for path in allPaths:

        # the probability of this path occurring
        probPath = pathProbability(path, probWinPointP1, probWinPointP2)

        # how did this path end ?
        lastScore = path.scoreHistory[-1].score
        winner    = lastScore.winner
        deuce     = lastScore.isDeuce

        # the probability that P1 wins when reaching the end of this path is:
        #  1 if the path ends with P1 winning the tiebreak
        #  0 if the path ends with P1 losing the tiebreak
        #  _probabilityP1WinsTie(...) if this path ends in a tie (6-6 or 9-9)
        if deuce:
            probWinFromDeuce = _probabilityP1WinsTie(probWinPointP1, probWinPointP2)
            probWinPath      = probPath * probWinFromDeuce
        else:
            P1won       = (winner == 1)
            probWinPath = probPath * (1.0 if P1won else 0.0)

        probWinTiebreak += probWinPath

    return probWinTiebreak

def _probabilityP1WinsTie(probWinPointP1: float,
                          probWinPointP2: float) -> float:
    """
    Calculates the probability that Player1 wins a tiebreak from a 6-6 (or 9-9) tie.

    This formula is derived from analyzing the infinite series of possible deuce
    outcomes. For details see:
        Data-Driven Tennis: The Statistics of Winning
        Part 1: How To Win a Set
        https://medium.com/@nciordas25/data-driven-tennis-the-statistics-of-winning-2f16ae57739a
    The result doesn't depend on which player serves first after reaching the tie.

    Parameters:
    -----------
    probWinPointP1 - probability that Player1 wins a point when serving
    probWinPointP2 - probability that Player2 wins a point when serving

    Returns:
    --------
    The probability that Player1 wins a tiebreak from a tie (6-6 or 9-9).
    """
    if not isinstance(probWinPointP1, (int, float)) or not (0 <= probWinPointP1 <= 1):
        raise ValueError("probWinPointP1 must be a number between 0 and 1")
    if not isinstance(probWinPointP2, (int, float)) or not (0 <= probWinPointP2 <= 1):
        raise ValueError("probWinPointP2 must be a number between 0 and 1")

    # Handle edge case where both players win all points on serve
    eps = 1e-10
    if abs(1.0 - probWinPointP1) < eps and abs(1.0 - probWinPointP2) < eps:
        return 0.5

    num = probWinPointP1 * (1 - probWinPointP2)
    den = 1 - probWinPointP1 * probWinPointP2 - (1 - probWinPointP1) * (1 - probWinPointP2)
    return num / den

def loadCachedFunction(initScore    : TiebreakScore,
                       playerServing: Literal[1, 2]) -> Optional[Callable[[float, float], float]]:
    """
    Loads a cached version of 'probabilityP1WinsTiebreak()'.

    Evaluating 'probabilityP1WinsTiebreak(...)' can be expensive, especially when called repeatedly,
    because it iterates over all possible score progressions. To avoid repeating this computation,
    the script 'scripts/cache-prob-win-tiebreak.py' pre-computes and caches the P1's tiebreak-winning
    probability for every possible starting score and across a grid of point-winning probabilities.
    A 2-D interpolator is constructed from this grid and saved as a callable, which is loaded and
    returned by this function.

    Parameters:
    -----------
    initScore     - the initial score in the tiebreak
    playerServing - which player is serving the next point (1 or 2)

    Returns:
    --------
    A callable that takes two float arguments (the probability that P1 wins a point when serving,
    and the probability that P2 wins a point when serving) and returns the probability that P1
    wins the tiebreak from the given initial score.
    Returns None if the cached function is not available.

    Example:
    --------
    f = loadCachedFunction(TiebreakScore(0, 0, False), playerServing=1)
    prob_win_tiebreak = f(0.65, 0.60)  # P1 wins 65% on serve, P2 wins 60% on serve
    """
    if not isinstance(initScore, TiebreakScore):
        raise ValueError("initScore must be a TiebreakScore instance")
    if not isinstance(playerServing, int) or playerServing not in [1, 2]:
        raise ValueError("playerServing must be 1 or 2")

    # Cap the score to normalize deuces & advantages (e.g., 8-8 → 6-6)
    cappedScore = deepcopy(initScore)
    cappedScore._cap_score()
    pointsP1, pointsP2 = cappedScore.asPoints(pov=1)

    # Further adjust advantages: _cap_score() gives 7-6/6-7, but cache has only 6-5/5-6
    pointsToWin = cappedScore.pointsToWin
    if pointsP1 == pointsToWin and pointsP2 == pointsToWin - 1:
        pointsP1, pointsP2 = pointsToWin - 1, pointsToWin - 2  # 7-6 → 6-5 (or 10-9 → 9-8)
    elif pointsP2 == pointsToWin and pointsP1 == pointsToWin - 1:
        pointsP1, pointsP2 = pointsToWin - 2, pointsToWin - 1  # 6-7 → 5-6 (or 9-10 → 8-9)

    # Build the filename based on the score
    fileName = f"prob_win_tbreak{pointsToWin}_P{playerServing}_{pointsP1}{pointsP2}.pkl"

    # Build the filepath
    DIRPATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data-cache')
    filePath = os.path.join(DIRPATH, fileName)

    try:
        with open(filePath, "rb") as fh:
            probP1WinTBreakInterpFunction = pickle.load(fh)
            def wrapper(p1: float, p2: float) -> float:
                return probP1WinTBreakInterpFunction(p1, p2).item()
            return wrapper
    except Exception:
        return None
