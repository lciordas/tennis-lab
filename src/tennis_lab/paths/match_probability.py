"""
Functions for calculating match-level probabilities in tennis.

Functions:
----------
pathProbability - probability that a given score path occurs during a match
"""

import os
import pickle
import numpy as np
import numpy.typing as npt
from typing import Callable, Iterator, Literal, Optional

from tennis_lab.core.match_format     import MatchFormat
from tennis_lab.core.match_score      import MatchScore
from tennis_lab.core.set_score        import SetScore
from tennis_lab.paths.match_path      import MatchPath
from tennis_lab.paths.set_probability import probabilityP1WinsSet, _loadCachedFunction as loadCachedFunction_Set

def pathProbability(path          : MatchPath,
                    probWinPointP1: float,
                    probWinPointP2: float) -> float:
    """
    Calculates the probability that a given score path occurs during a match.
    Takes as input each player's probability of winning a point on their serve.

    This function operates at set-level granularity: each step in the path represents
    a completed set, not individual games or points. Point-winning probabilities are
    converted to set-winning probabilities internally.

    Parameters:
    -----------
    path           - the match score path whose probability we calculate
    probWinPointP1 - probability that Player1 wins the point when serving
    probWinPointP2 - probability that Player2 wins the point when serving

    Returns:
    --------
    The probability that the given score path occurs during a match.
    """
    if not isinstance(path, MatchPath):
        raise ValueError("path must be a MatchPath instance")
    if not isinstance(probWinPointP1, (int, float)) or not (0 <= probWinPointP1 <= 1):
        raise ValueError("probWinPointP1 must be a number between 0 and 1")
    if not isinstance(probWinPointP2, (int, float)) or not (0 <= probWinPointP2 <= 1):
        raise ValueError("probWinPointP2 must be a number between 0 and 1")
    
    # We need to calculate the probability of winning the set from the probability 
    # of winning the point when serving. We try to load this data from the cache first; 
    # if not available, we fall back to calculating it directly.
    # Since we are starting the game from 0-0, it does not matter which player serves.    
    initScore = SetScore(0, 0, False, MatchFormat())
    cachedFunction = loadCachedFunction_Set(initScore, playerServing=1)
    if cachedFunction is not None:
        probP1WinsSetFunction = cachedFunction
    else:
        probP1WinsSetFunction = lambda p1, p2: probabilityP1WinsSet(initScore, 1, [p1], p2)[0]

    probPath = 1.0
    scores   = path.scoreHistory          # the scores that make up the path
    for i in range(1, len(scores)):       # loop over score *changes*

        setsP1Curr = scores[i  ].sets(pov=1)[0]    # Player1 # of sets now
        setsP1Prev = scores[i-1].sets(pov=1)[0]    # Player1 # of sets previously
        P1wonSet   = setsP1Curr > setsP1Prev       # did Player1 win the set?

        # calculate the probability of this score change
        if P1wonSet:
            probScoreChange = probP1WinsSetFunction(probWinPointP1, probWinPointP2)
        else:
            probScoreChange = 1 - probP1WinsSetFunction(probWinPointP1, probWinPointP2)

        # multiply probs of score changes
        probPath *= probScoreChange

    return probPath

def probabilityP1WinsMatch(initScore      : MatchScore,
                           playerServing  : Literal[1, 2],
                           probWinPointP1s: Iterator[float],
                           probWinPointP2 : float) -> npt.NDArray[np.floating]:
    """
    Calculates the probability that Player1 wins the match from a given score.
    The initial score does not need to represent a set boundary.

    The probability of winning the match is calculated as:
        P(win match) = P(win set) * P(win match | won set) + P(lose set) * P(win match | lost set)

    Parameters:
    -----------
    initScore       - the initial score in the match
    playerServing   - which player is serving next point (1 or 2)
    probWinPointP1s - iterable of probabilities that Player1 wins the point when serving
    probWinPointP2  - probability that Player2 wins the point when serving

    Returns:
    --------
    An array of probabilities that Player1 wins the match, one for each value in probWinPointP1s.
    """
    if not isinstance(initScore, MatchScore):
        raise ValueError("initScore must be a MatchScore instance")
    if not isinstance(playerServing, int) or playerServing not in [1, 2]:
        raise ValueError("playerServing must be 1 or 2")
    if not isinstance(probWinPointP2, (int, float)) or not (0 <= probWinPointP2 <= 1):
        raise ValueError("probWinPointP2 must be a number between 0 and 1")

    # Convert iterator to list, since we need to iterate multiple times over it
    probWinPointP1s = list(probWinPointP1s)
    for p in probWinPointP1s:
        if not isinstance(p, (int, float)) or not (0 <= p <= 1):
            raise ValueError("all probWinPointP1s must be numbers between 0 and 1")

    # the number of sets completed so far by the two players
    setsP1, setsP2 = initScore.sets(pov=1)
    matchFormat    = initScore._matchFormat

    # Case 1: we are in the middle of a set
    # Calculate probability using conditional probabilities on set outcome
    if initScore.setInProgress:
        setScore = initScore.currSetScore

        # calculate the probability that Player1 wins the set in progress
        pP1WinsSet = probabilityP1WinsSet(setScore, playerServing, probWinPointP1s, probWinPointP2)

        # P(win match | won set)
        scoreIfWon = MatchScore(setsP1 + 1, setsP2, matchFormat)
        cachedMatchFuncWon = _loadCachedFunction(scoreIfWon)
        if cachedMatchFuncWon is not None:
            pP1WinsMatchWon = np.array([cachedMatchFuncWon(p1, probWinPointP2) for p1 in probWinPointP1s])
        else:
            pP1WinsMatchWon = np.array([_probabilityP1WinsMatchFromSetBoundary(scoreIfWon, p1, probWinPointP2) for p1 in probWinPointP1s])

        # P(win match | lost set)
        scoreIfLost = MatchScore(setsP1, setsP2 + 1, matchFormat)
        cachedMatchFuncLost = _loadCachedFunction(scoreIfLost)
        if cachedMatchFuncLost is not None:
            pP1WinsMatchLost = np.array([cachedMatchFuncLost(p1, probWinPointP2) for p1 in probWinPointP1s])
        else:
            pP1WinsMatchLost = np.array([_probabilityP1WinsMatchFromSetBoundary(scoreIfLost, p1, probWinPointP2) for p1 in probWinPointP1s])

        # total probability
        return pP1WinsSet * pP1WinsMatchWon + (1 - pP1WinsSet) * pP1WinsMatchLost

    # Case 2: we are at a set boundary (not in the middle of a set)
    else:
        cachedMatchFunc = _loadCachedFunction(initScore)
        if cachedMatchFunc is not None:
            return np.array([cachedMatchFunc(p1, probWinPointP2) for p1 in probWinPointP1s])
        else:
            return np.array([_probabilityP1WinsMatchFromSetBoundary(initScore, p1, probWinPointP2) for p1 in probWinPointP1s])

def _probabilityP1WinsMatchFromSetBoundary(initScore     : MatchScore,
                                           probWinPointP1: float,
                                           probWinPointP2: float,
                                           paths         : Optional[list[MatchPath]] = None) -> float:
    """
    Calculates the probability that Player1 wins the match from a given set boundary.

    The initial score being a "set boundary" means that it cannot represent a moment
    in the middle of a set. Valid examples (as number of sets): 0-0, 1-0, 1-1, 2-1 
    (with no set in progress).

    This probability is calculated the following way:
      + generate all possible score paths starting from the given initial score (at 'set' granularity)
      + calculate the probability that Player1 wins the match along each path
      + sum up all these probabilities
    The calculation takes as input each player's probability of winning a point on their serve.

    For efficiency, pre-generated score paths can be passed in via the 'paths' parameter, to avoid
    regenerating them on each call. If not provided, all possible score paths that start from the
    initial score are generated internally.

    Parameters:
    -----------
    initScore      - the initial score in the match
    probWinPointP1 - probability that Player1 wins the point when serving
    probWinPointP2 - probability that Player2 wins the point when serving
    paths          - list of paths to sum over (optional, see above)

    Returns:
    --------
    The probability that Player1 wins the match from the given score.
    """
    if not isinstance(initScore, MatchScore):
        raise ValueError("initScore must be a MatchScore instance")
    if initScore.setInProgress:
        raise ValueError("initScore cannot have a set in progress")
    if not isinstance(probWinPointP1, (int, float)) or not (0 <= probWinPointP1 <= 1):
        raise ValueError("probWinPointP1 must be a number between 0 and 1")
    if not isinstance(probWinPointP2, (int, float)) or not (0 <= probWinPointP2 <= 1):
        raise ValueError("probWinPointP2 must be a number between 0 and 1")

    # If paths are provided, check that they all start with 'initScore'
    if paths is not None:
        for path in paths:
            if path.scoreHistory[0] != initScore:
                raise ValueError("all paths must start with 'initScore'")

    # Generate all possible paths starting from the initial score
    # (unless we were given a pre-calculated list of paths)
    # NOTE: if given a set of paths, we do not check whether they
    #       represent *all* the score paths that start with 'initScore'
    allPaths = paths if paths else MatchPath.generateAllPaths(initScore)

    # add up the probability of winning the match along each path
    probWinMatch = 0.0
    for path in allPaths:

        # the probability of this path occurring
        probPath = pathProbability(path, probWinPointP1, probWinPointP2)

        # how did this path end?
        lastScore = path.scoreHistory[-1]
        P1won     = lastScore.winner == 1

        # the probability that Player1 wins the match when it reaches the end of this path is:
        #  1 if the path ends with P1 winning the match
        #  0 if the path ends with P1 losing the match
        probWinPath = probPath * (1.0 if P1won else 0.0)

        probWinMatch += probWinPath

    return probWinMatch

def _loadCachedFunction(initScore: MatchScore) -> Optional[Callable[[float, float], float]]:
    """
    Loads a cached version of '_probabilityP1WinsMatchFromSetBoundary()'.

    Evaluating '_probabilityP1WinsMatchFromSetBoundary(...)' can be expensive, especially when called
    repeatedly, because it iterates over all possible score progressions. To avoid repeating this
    computation, the script 'scripts/cache-prob-win-match.py' pre-computes and caches the Player1's
    match-winning probability for every possible starting score and across a grid of point-winning
    probabilities. A 2-D interpolator is constructed from this grid and saved as a callable, which
    is loaded and returned by this function.

    The initial score must represent a "set boundary", meaning that it cannot represent a moment in
    the middle of a set. Valid examples (as number of sets): 0-0, 1-0, 1-1, 2-1.

    Parameters:
    -----------
    initScore - the initial score in the match

    Returns:
    --------
    A callable that takes two float arguments (the probability that P1 wins a point when serving,
    and the probability that P2 wins a point when serving) and returns the probability that P1
    wins the match from the given initial score.
    Returns None if the cached function is not available.

    Example:
    --------
    f = _loadCachedFunction(MatchScore(0, 0, MatchFormat(bestOfSets=3)))
    prob_win_match = f(0.65, 0.60)  # P1 wins 65% on serve, P2 wins 60% on serve
    """
    if not isinstance(initScore, MatchScore):
        raise ValueError("initScore must be a MatchScore instance")
    if initScore.setInProgress:
        raise ValueError("initScore cannot have a set in progress")

    setsP1, setsP2 = initScore.sets(pov=1)
    bestOf = initScore._matchFormat.bestOfSets

    # Build the filename based on the score
    fileName = f"prob_win_match_bo{bestOf}_{setsP1}{setsP2}.pkl"

    # Build the filepath
    DIRPATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data-cache')
    filePath = os.path.join(DIRPATH, fileName)

    try:
        with open(filePath, "rb") as fh:
            probP1WinMatchInterpFunction = pickle.load(fh)
            def wrapper(p1: float, p2: float) -> float:
                return probP1WinMatchInterpFunction(p1, p2).item()
            return wrapper
    except Exception:
        return None
