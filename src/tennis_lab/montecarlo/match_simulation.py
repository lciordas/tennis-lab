"""
Functions for Monte Carlo simulation of a tennis match.

Functions:
----------
probabilityP1WinsMatch - probability that Player1 wins the match from a given score
"""

import random
from   typing import Literal

import numpy as np
import numpy.typing as npt

from tennis_lab.core.match        import Match
from tennis_lab.core.match_format import MatchFormat
from tennis_lab.core.match_score  import MatchScore
from tennis_lab.paths.match_probability import probabilityP1WinsMatch as probabilityP1WinsMatchAnalytic

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

def simulateMatchWinProbabilityEvolution(matchFormat: MatchFormat,
                                         P1actual   : float, 
                                         P2actual   : float,
                                         P1prior    : float, alpha1: float,
                                         P2prior    : float, alpha2: float) \
        -> tuple[npt.NDArray[np.floating], npt.NDArray[np.floating],
                 npt.NDArray[np.floating], npt.NDArray[np.floating]]:
    """
    This method simulates a full tennis match, tracking how Player1's probability
    of winning the match evolves over time. Here's a breakdown of how it works:

    # Match Simulation #
    The match starts at 0-0 and progresses point by point.
    The outcome of each point is determined randomly based on predefined probabilities:
        + probability that Player1 wins a point when serving.
        + probability that Player2 wins a point when serving.
    These probabilities represent the "true" underlying skill levels of the players.

    # Probability Tracking #
    After each point, the function calculates Player1's probability of winning the match
    given the current score. These probabilities are saved in a list, showing how Player1's
    chances fluctuate as the match progresses.

    # Using Estimates Instead of True Values #
    In reality, we don't know the probability of each player winning the point when serving.
    Instead, we start with an initial estimate of these probabilities and use it to compute
    Player1's match-winning probability. As the match progresses, we refine this estimate using
    Bayesian statistics, incorporating observed serve outcomes to improve our understanding of
    each player's serving ability.

    We model the prior distribution of the probability of winning a point on serve using a Beta
    distribution. This distribution is characterized by two parameters:
        mode  - our best guess for the probability value.
        alpha - controls the width of the distribution, representing the uncertainty in our estimate;
                a value of 100 means the distribution falls to essentially 0 at +/-0.1 of the mode

    Parameters:
    -----------
    matchFormat - the match format
    P1actual    - the true probability that Player1 wins a point when serving
    P2actual    - the true probability that Player2 wins a point when serving
    P1prior     - the mode  of the Beta distribution describing the prior for P1actual
    alpha1      - the width of the Beta distribution describing the prior for P1actual
    P2prior     - the mode  of the Beta distribution describing the prior for P2actual
    alpha2      - the width of the Beta distribution describing the prior for P2actual

    Returns:
    --------
    A total of 4 arrays.
    First two arrays store the probability of Player1 winning the match after each point.
    Last  two arrays store the most recent Bayesian update for the probability the Player1/2
    win the point when serving.

    1st array: calculated using fixed (static) probabilities for each player winning a point on serve.
    2nd array: calculated using probabilities that are dynamically updated with Bayesian statistics
               based on observed serve outcomes.
    3rd array: the most recent Bayesian update for the probability that Player1 wins the point when serving
    4th array: the most recent Bayesian update for the probability that Player2 wins the point when serving
    """

    # from 'alpha' and 'mode' calculate the 'beta' parameter of the Beta distribution
    # that describes the probability that a player wins a point when serving
    beta1 = ((1 - P1prior) * alpha1 + 2 * P1prior - 1) / P1prior
    beta2 = ((1 - P2prior) * alpha2 + 2 * P2prior - 1) / P2prior

    # since we haven't observed any data,
    # the posterior is equal to the prior
    P1postr = P1prior
    P2postr = P2prior

    # create a new object representing a tennis match;
    # it is initialized with a score of 0-0
    # which player serves first is irrelevant
    match = Match(playerServing=1, matchFormat=matchFormat)

    # these two arrays store the probability that Player1 wins the match, 
    # calculated for each point in the match.
    # we add here the first entry: the probability the Player1 wins the match at 0-0
    probWinsMatchStatic  = [probabilityP1WinsMatchAnalytic(match.score, 1, [P1prior], P2prior)[0]]
    probWinsMatchDynamic = [probabilityP1WinsMatchAnalytic(match.score, 1, [P1postr], P2postr)[0]]

    # these two arrays store the most recent Bayesian update for the probability that a player wins on serve
    P1updated = [P1prior]
    P2updated = [P2prior]

    # start playing the match until its over
    while True:

        # simulate playing the next point
        # this is done using the 'true' probability values
        server = match.servesNext
        p = P1actual if server == 1 else P2actual
        serverWonPoint = True if random.random() < p else False
        p1Won = ((server == 1) and serverWonPoint) or \
                ((server == 2) and not serverWonPoint)
        match.recordPoint(1 if p1Won else 2)
        if match.isOver:
            break

        # calculate the new probability of Player1 winning the match
        # this is the 'static' calculation based on frozen initial estimates for P1actual and P2actual
        pStatic = probabilityP1WinsMatchAnalytic(match.score, match.servesNext, [P1prior], P2prior)[0]
        probWinsMatchStatic.append(pStatic)

        # update the posterior distribution
        if server == 1:
            if p1Won:
                alpha1 += 1
            else:
                beta1 += 1
            P1postr = (alpha1 - 1) / (alpha1 + beta1 - 2)
        else:
            if p1Won:
                beta2 += 1
            else:
                alpha2 += 1
            P2postr = (alpha2 - 1) / (alpha2 + beta2 - 2)

        # calculate the new probability of Player1 winning the match
        # this is the 'dynamic' calculation based on updated estimates for P1actual and P2actual
        pDynamic = probabilityP1WinsMatchAnalytic(match.score, match.servesNext, [P1postr], P2postr)[0]
        probWinsMatchDynamic.append(pDynamic)

        # remember the history of posterior updates
        P1updated.append(P1postr)
        P2updated.append(P2postr)

    # add one final data point, once we know the match result
    probWinsMatchStatic.append (1 if match.winner == 1 else 0)
    probWinsMatchDynamic.append(1 if match.winner == 1 else 0)

    return np.array(probWinsMatchStatic), np.array(probWinsMatchDynamic), np.array(P1updated), np.array(P2updated)