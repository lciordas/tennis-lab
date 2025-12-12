"""
Functions for calculating set-level probabilities in tennis.

Functions:
----------
pathProbability      - probability that a given score path occurs during a set
probabilityP1WinsSet - probability that P1 wins the set from a given score
"""

import numpy as np
import numpy.typing as npt
import os, pickle
from typing import Callable, Iterator, Literal, Optional

from tennis_lab.paths.set_path             import SetPath
from tennis_lab.paths.game_probability     import loadCachedFunction as loadCachedFunction_Game
from tennis_lab.paths.game_probability     import probabilityServerWinsGame
from tennis_lab.paths.tiebreak_probability import loadCachedFunction as loadCachedFunction_Tiebreak
from tennis_lab.paths.tiebreak_probability import probabilityP1WinsTiebreak
from tennis_lab.core.game_score            import GameScore
from tennis_lab.core.set_score             import SetScore
from tennis_lab.core.tiebreak_score        import TiebreakScore

def pathProbability(path          : SetPath,
                    probWinPointP1: float,
                    probWinPointP2: float) -> float:
    """
    Calculates the probability that a given score path occurs during a set.
    Takes as input each player's probability of winning a point on their serve.

    This function operates at game-level granularity: each step in the path represents
    a completed game, not individual points. Point-winning probabilities are converted
    to game-winning probabilities internally.

    NOTE: The path consists only of regular games, not tiebreaks. If the set reaches
    6-6 (tied), the path ends there - a tiebreak (or more games) are not included in
    the path.

    Parameters:
    -----------
    path           - the set score path whose probability we calculate
    probWinPointP1 - probability that Player1 wins the point when serving
    probWinPointP2 - probability that Player2 wins the point when serving

    Returns:
    --------
    The probability that the given score path occurs during a set.
    """
    if not isinstance(path, SetPath):
        raise ValueError("path must be a SetPath instance")
    if not isinstance(probWinPointP1, (int, float)) or not (0 <= probWinPointP1 <= 1):
        raise ValueError("probWinPointP1 must be a number between 0 and 1")
    if not isinstance(probWinPointP2, (int, float)) or not (0 <= probWinPointP2 <= 1):
        raise ValueError("probWinPointP2 must be a number between 0 and 1")

    # We need to calculate the probability of winning the game when serving from the 
    # probability of winning the point when serving. We try to load this data from 
    # the cache first; if not available, we fall back to calculating it directly.
    # Since we are starting the game from 0-0, it does not matter which player serves.
    initScore = GameScore(0, 0)
    cachedFunction = loadCachedFunction_Game(initScore, playerServing=1)
    if cachedFunction is not None:
        probWinGameFunction = cachedFunction
    else:
        probWinGameFunction = lambda p: probabilityServerWinsGame(initScore, 1, p)

    probPath = 1.0
    entries  = path.scoreHistory          # the entries that make up the path
    for i in range(1, len(entries)):      # loop over score *changes*

        gamesP1Curr = entries[i  ].score.games(pov=1)[0]   # Player1 # of games now
        gamesP1Prev = entries[i-1].score.games(pov=1)[0]   # Player1 # of games previously
        P1served    = entries[i-1].playerServing == 1      # did Player1 serve this game?
        P1wonGame   = gamesP1Curr > gamesP1Prev            # did Player1 win the game?
        P2wonGame   = not P1wonGame

        # calculate the probability of this score change
        if P1served:
            probWinGameP1   = probWinGameFunction(probWinPointP1)
            probScoreChange = probWinGameP1 if P1wonGame else (1 - probWinGameP1)
        else:
            probWinGameP2   = probWinGameFunction(probWinPointP2)
            probScoreChange = probWinGameP2 if P2wonGame else (1 - probWinGameP2)

        # multiply probs of score changes
        probPath *= probScoreChange

    return probPath

def probabilityP1WinsSet(initScore      : SetScore,
                         playerServing  : Literal[1, 2],
                         probWinPointP1s: Iterator[float],
                         probWinPointP2 : float) -> npt.NDArray[np.floating]:
    """
    Calculates the probability that Player1 wins the set from a given score.
    The initial score does not need to represent a game boundary.

    The probability of winning the set is calculated as:
        P(win set) = P(win game) * P(win set | won game) + P(lose game) * P(win set | lost game)

    If the set reached the tiebreak stage, the probability of winning the set equals the 
    probability of winning the tiebreak.

    Parameters:
    -----------
    initScore       - the initial score in the set
    playerServing   - which player is serving next point (1 or 2)
    probWinPointP1s - iterable of probabilities that Player1 wins the point when serving
    probWinPointP2  - probability that Player2 wins the point when serving

    Returns:
    --------
    An array of probabilities that Player1 wins the set, one for each value in probWinPointP1s.
    """
    if not isinstance(initScore, SetScore):
        raise ValueError("initScore must be a SetScore instance")
    if not isinstance(playerServing, int) or playerServing not in [1, 2]:
        raise ValueError("playerServing must be 1 or 2")
    if not isinstance(probWinPointP2, (int, float)) or not (0 <= probWinPointP2 <= 1):
        raise ValueError("probWinPointP2 must be a number between 0 and 1")

    # Convert iterator to list, since we need to iterate multiple times over it
    probWinPointP1s = list(probWinPointP1s)
    for p in probWinPointP1s:
        if not isinstance(p, (int, float)) or not (0 <= p <= 1):
            raise ValueError("all probWinPointP1s must be numbers between 0 and 1")

    # the number of games completed so far by the two players
    gamesP1, gamesP2 = initScore.games(pov=1)

    # Case 1: we are in the middle of a game
    # Calculate probability using conditional probabilities on game outcome
    if initScore.gameInProgress:
        gameScore = initScore.currGameScore

        # calculate the probability that the player serving wins the game in progress
        cachedGameFunc = loadCachedFunction_Game(gameScore, playerServing)
        if cachedGameFunc is not None:
            probWinPoint = [p1 if playerServing == 1 else probWinPointP2 for p1 in probWinPointP1s]
            probServerWinsGame = np.array([cachedGameFunc(p) for p in probWinPoint])
        else:
            probWinPoint = [p1 if playerServing == 1 else probWinPointP2 for p1 in probWinPointP1s]
            probServerWinsGame = np.array([probabilityServerWinsGame(gameScore, playerServing, p) for p in probWinPoint])

        # convert to probability that Player1 wins the game
        probP1WinsGame = probServerWinsGame if playerServing == 1 else (1 - probServerWinsGame)

        # after this game, the other player serves
        nextServer = 3 - playerServing

        # P(win set | won game)
        scoreIfWon = SetScore(gamesP1 + 1, gamesP2, initScore._isFinalSet, initScore._matchFormat)
        cachedSetFuncWon = _loadCachedFunction(scoreIfWon, nextServer)
        if cachedSetFuncWon is not None:
            pP1WinsSetWon = np.array([cachedSetFuncWon(p1, probWinPointP2) for p1 in probWinPointP1s])
        else:
            pP1WinsSetWon = np.array([_probabilityP1WinsSetFromGameBoundary(scoreIfWon, nextServer, p1, probWinPointP2) for p1 in probWinPointP1s])

        # P(win set | lost game)
        scoreIfLost = SetScore(gamesP1, gamesP2 + 1, initScore._isFinalSet, initScore._matchFormat)
        cachedSetFuncLost = _loadCachedFunction(scoreIfLost, nextServer)
        if cachedSetFuncLost is not None:
            pP1WinsSetLost = np.array([cachedSetFuncLost(p1, probWinPointP2) for p1 in probWinPointP1s])
        else:
            pP1WinsSetLost = np.array([_probabilityP1WinsSetFromGameBoundary(scoreIfLost, nextServer, p1, probWinPointP2) for p1 in probWinPointP1s])

        # total probability
        return probP1WinsGame * pP1WinsSetWon + (1 - probP1WinsGame) * pP1WinsSetLost

    # Case 2: we are in the middle of a tiebreak
    # Probability of winning the set equals probability of winning the tiebreak
    elif initScore.tiebreakInProgress:
        tiebreakScore = initScore.tiebreakScore
        cachedTiebreakFunc = loadCachedFunction_Tiebreak(tiebreakScore, playerServing)
        if cachedTiebreakFunc is not None:
            return np.array([cachedTiebreakFunc(p1, probWinPointP2) for p1 in probWinPointP1s])
        else:
            return np.array([probabilityP1WinsTiebreak(tiebreakScore, playerServing, p1, probWinPointP2) for p1 in probWinPointP1s])

    # Case 3: we are at a game boundary (not in the middle of a game or tiebreak)
    else:
        cachedSetFunc = _loadCachedFunction(initScore, playerServing)
        if cachedSetFunc is not None:
            return np.array([cachedSetFunc(p1, probWinPointP2) for p1 in probWinPointP1s])
        else:
            return np.array([_probabilityP1WinsSetFromGameBoundary(initScore, playerServing, p1, probWinPointP2) for p1 in probWinPointP1s])

def _probabilityP1WinsSetFromGameBoundary(initScore      : SetScore,
                                          playerServing  : Literal[1, 2],
                                          probWinPointP1 : float,
                                          probWinPointP2 : float,
                                          paths          : Optional[list[SetPath]] = None) -> float:
    """
    Calculates the probability that Player1 wins the set from a given game boundary.
    
    The initial score being a "game boundary"  means that it cannot represent a moment
    in the middle of a game (e.g., 3-4, 15-30) or of a tiebreak (e.g., 6-6, 4-3).
    Valid examples (as number of games): 0-0, 3-4, 5-5, 6-6 (with no tiebreak points played yet).
    This probability is calculated the following way:
      + generate all possible score paths starting from the given initial score (at 'game' granularity)
      + calculate the probability that Player1 wins the set along each path
      + sum up all these probabilities
    The calculation takes as input each player's probability of winning a point on their serve.

    For efficiency, pre-generated score paths can be passed in via the 'paths' parameter, to avoid 
    regenerating them on each call. If not provided, all possible score paths that start from the 
    initial score are generated internally. 
    
    Parameters:
    -----------
    initScore      - the initial score in the set
    playerServing  - which player is serving the next game (1 or 2)
    probWinPointP1 - probability that Player1 wins the point when serving
    probWinPointP2 - probability that Player2 wins the point when serving
    paths          - list of paths to sum over (optional, see above)

    Returns:
    --------
    The probability that Player1 wins the set from the given score.
    """
    if not isinstance(initScore, SetScore):
        raise ValueError("initScore must be a SetScore instance")
    if initScore.gameInProgress or initScore.tiebreakInProgress:
        raise ValueError("initScore cannot have a game or tiebreak in progress")
    if not isinstance(playerServing, int) or playerServing not in [1, 2]:
        raise ValueError("playerServing must be 1 or 2")
    if not isinstance(probWinPointP1, (int, float)) or not (0 <= probWinPointP1 <= 1):
        raise ValueError("probWinPointP1 must be a number between 0 and 1")
    if not isinstance(probWinPointP2, (int, float)) or not (0 <= probWinPointP2 <= 1):
        raise ValueError("probWinPointP2 must be a number between 0 and 1")

    # If paths are provided, check that they all start with 'initScore'
    if paths is not None:
        for path in paths:
            if path.scoreHistory[0].score != initScore:
                raise ValueError("all paths must start with 'initScore'")

    # Generate all possible paths starting from the initial score
    # (unless we were given a pre-calculated list of paths)
    # NOTE: if given a set of paths, we do not check whether they
    #       represent *all* the score paths that start with 'initScore'
    allPaths = paths if paths else SetPath.generateAllPaths(initScore, playerServing)

    # We need the probability of each player winning a tiebreak.
    # We try to load this data from the cache first; if not available, 
    # we fall back to calculating it directly.
    tiebreakInitScore = TiebreakScore(0, 0, isSuper=False)
    cachedTiebreakFunc_P1Serves = loadCachedFunction_Tiebreak(tiebreakInitScore, playerServing=1)
    cachedTiebreakFunc_P2Serves = loadCachedFunction_Tiebreak(tiebreakInitScore, playerServing=2)
    if cachedTiebreakFunc_P1Serves is not None and cachedTiebreakFunc_P2Serves is not None:
        def probP1WinsTiebreakFunc(server, p1, p2):
            return cachedTiebreakFunc_P1Serves(p1, p2) if server == 1 else cachedTiebreakFunc_P2Serves(p1, p2)
    else:
        def probP1WinsTiebreakFunc(server, p1, p2):
            return probabilityP1WinsTiebreak(tiebreakInitScore, server, p1, p2)

    # add up the probability of winning the set along each path
    probWinSet = 0.0
    for path in allPaths:

        # the probability of this path occurring
        probPath = pathProbability(path, probWinPointP1, probWinPointP2)

        # how did this path end?
        lastEntry = path.scoreHistory[-1]
        lastScore = lastEntry.score
        P1won     = lastScore.winner == 1
        isTied    = lastScore.isTied

        # the probability that Player1 wins the set when it reaches the end of this path is:
        #  1 if the path ends with P1 winning the set
        #  0 if the path ends with P1 losing the set
        #  the probability that Player1 wins a tiebreaker if the score is tied at 6-6
        if isTied:
            tiebreakServer = lastEntry.playerServing
            probP1WinsTB   = probP1WinsTiebreakFunc(tiebreakServer, probWinPointP1, probWinPointP2)
            probWinPath    = probPath * probP1WinsTB
        else:
            probWinPath = probPath * (1.0 if P1won else 0.0)

        probWinSet += probWinPath

    return probWinSet

def _loadCachedFunction(initScore    : SetScore,
                       playerServing: Literal[1, 2]) -> Optional[Callable[[float, float], float]]:
    """
    Loads a cached version of '_probabilityP1WinsSetFromGameBoundary()'.

    Evaluating '_probabilityP1WinsSetFromGameBoundary(...)' can be expensive, especially when called
    repeatedly, because it iterates over all possible score progressions. To avoid repeating this
    computation, the script 'scripts/cache-prob-win-set.py' pre-computes and caches the Player1's
    set-winning probability for every possible starting score and across a grid of point-winning
    probabilities. A 2-D interpolator is constructed from this grid and saved as a callable, which
    is loaded and returned by this function.

    The initial score must represent a "game boundary", meaning that it cannot represent a moment in 
    the middle of a game (e.g., 3-4, 15-30) or of a tiebreak (e.g., 6-6, 4-3).
    Valid examples as number of games: 0-0, 3-4, 5-5, 6-6 (with no tiebreak points played yet).

    Parameters:
    -----------
    initScore     - the initial score in the set
    playerServing - which player is serving the next game (1 or 2)

    Returns:
    --------
    A callable that takes two float arguments (the probability that P1 wins a point when serving,
    and the probability that P2 wins a point when serving) and returns the probability that P1
    wins the set from the given initial score.
    Returns None if the cached function is not available.

    Example:
    --------
    f = loadCachedFunction(SetScore(0, 0, False, MatchFormat()), playerServing=1)
    prob_win_set = f(0.65, 0.60)  # P1 wins 65% on serve, P2 wins 60% on serve
    """
    if not isinstance(initScore, SetScore):
        raise ValueError("initScore must be a SetScore instance")
    if initScore.gameInProgress or initScore.tiebreakInProgress:
        raise ValueError("initScore cannot have a game or tiebreak in progress")
    if not isinstance(playerServing, int) or playerServing not in [1, 2]:
        raise ValueError("playerServing must be 1 or 2")

    gamesP1, gamesP2 = initScore.games(pov=1)

    # Build the filename based on the score
    fileName = f"prob_win_set_P{playerServing}_{gamesP1}{gamesP2}.pkl"

    # Build the filepath
    DIRPATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data-cache')
    filePath = os.path.join(DIRPATH, fileName)

    try:
        with open(filePath, "rb") as fh:
            probP1WinSetInterpFunction = pickle.load(fh)
            def wrapper(p1: float, p2: float) -> float:
                return probP1WinSetInterpFunction(p1, p2).item()
            return wrapper
    except Exception:
        return None
