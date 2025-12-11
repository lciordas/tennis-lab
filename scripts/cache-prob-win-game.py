#!/usr/bin/env python3

"""
This script computes and caches the probability that the player serving wins the game, given their 
probability of winning a point on serve. This is useful because this calculation is expensive.
The script performs the calculation over a 1-D grid of point-winning probabilities, and the resulting 
game-winning probabilities are saved as an interpolated function that can be evaluated quickly. 
One such function is generated and cached for every possible starting score in the game.

Each function is saved in a separate file. Example filenames:
 + prob_win_game_20.pkl
 + prob_win_game_noad_03.pkl
where we used the following conventions:
 + "noad" indicates no-ad scoring.
 + The final two digits represent the starting score (server first).
   For example, "20" corresponds to 30-0.

Example of how to use such a cached function:

    with open('data-cache/prob_win_game_00.pkl', 'rb') as fh:
        f = pickle.load(fh)
        prob_win_point = 0.3   # the probability that the player serving wins the point
        prob_win_game  = f(prob_win_point).item()
"""
from pathlib           import Path
from scipy.interpolate import interp1d
from typing            import Literal
import os, pickle, sys
import numpy as np

# add path to the src directory if not in PYTHONPATH already
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from tennis_lab.core.game_score        import GameScore
from tennis_lab.core.match_format      import MatchFormat
from tennis_lab.paths.game_probability import probabilityServerWinsGame

# The directory where to store (pickle) the interpolated functions
DIRPATH = Path(PROJECT_ROOT, "data-cache")
DIRPATH.mkdir(exist_ok=True)

# DO NOT CHANGE THIS
# The code is not symmetric to changes 1<->2
PLAYER_SERVING: Literal[1,2] = 1

# Interpolation grid for the probability 
# that the player serving wins the point
Ps = np.linspace(0, 1, 100)

# List all possible scores in a game.
initScoresInter = [(0,0), (0,1), (0,2), (0,3),
                   (1,0), (1,1), (1,2), (1,3),
                   (2,0), (2,1), (2,2), (2,3),
                   (3,0), (3,1), (3,2), (3,3)]   # intermediate scores: the game is not over
initScoresWon   = [(4,0), (4,1), (4,2)]          # game is over: player serving won
initScoresLost  = [(0,4), (1,4), (2,4)]          # game is over: player serving lost
initScore34     = [(3,4)]                        # special score
initScore43     = [(4,3)]                        # special score
initScores      = initScoresInter + initScoresWon + initScoresLost + initScore34 + initScore43

# Match formats for regular and no-ad scoring
FORMAT_REGULAR = MatchFormat(noAdRule=False)
FORMAT_NO_AD   = MatchFormat(noAdRule=True)

# Calculate the probability of winning the game starting from all possible scores.
# Two such calculations are performed - both for when using regular scoring or the 'no ad' format.
for i, (pointsP1, pointsP2) in enumerate(initScores):
    print(f"\r[{i+1:2d}/{len(initScores):2d}] Processing score ({pointsP1}, {pointsP2})...", end="", flush=True)
    scoreRglr = GameScore(pointsP1, pointsP2, FORMAT_REGULAR)
    scoreNoAd = GameScore(pointsP1, pointsP2, FORMAT_NO_AD)

    if (pointsP1, pointsP2) in initScoresInter:
        ProbGameRGLR = [probabilityServerWinsGame(scoreRglr, PLAYER_SERVING, p) for p in Ps]  # regular scoring
        ProbGameNOAD = [probabilityServerWinsGame(scoreNoAd, PLAYER_SERVING, p) for p in Ps]  # 'no ad' scoring
    elif (pointsP1, pointsP2) in initScoresWon:
        # serving player won => prob win game is 1.0
        ProbGameRGLR = [1.0 for p in Ps]  # regular scoring
        ProbGameNOAD = [1.0 for p in Ps]  # 'no ad' scoring
    elif (pointsP1, pointsP2) in initScoresLost:
        # serving player lost => prob win game is 0.0
        ProbGameRGLR = [0.0 for p in Ps]  # regular scoring
        ProbGameNOAD = [0.0 for p in Ps]  # 'no ad' scoring
    elif (pointsP1, pointsP2) in initScore34:
        # when using 'no ad' format, serving player lost
        ProbGameRGLR = [probabilityServerWinsGame(scoreRglr, PLAYER_SERVING, p) for p in Ps]  # regular scoring
        ProbGameNOAD = [0.0 for p in Ps]
    elif (pointsP1, pointsP2) in initScore43:
        # when using 'no ad' format, serving player won
        ProbGameRGLR = [probabilityServerWinsGame(scoreRglr, PLAYER_SERVING, p) for p in Ps]  # regular scoring
        ProbGameNOAD = [1.0 for p in Ps]
    else:
        raise Exception(f"Unknown score: {scoreRglr}")

    # Save to 1-D interpolation objects, for both the regular and the 'no-ad' score format.
    probWinGameRglrInterp = interp1d(Ps, ProbGameRGLR, kind='linear', fill_value="extrapolate")
    probWinGameNoAdInterp = interp1d(Ps, ProbGameNOAD, kind='linear', fill_value="extrapolate")

    # Save the interpolated functions to file
    fnameRglr = f"prob_win_game_{pointsP1}{pointsP2}.pkl"
    with open(Path(DIRPATH, fnameRglr), 'wb') as fh:
        pickle.dump(probWinGameRglrInterp, fh)

    fnameNoAd = f"prob_win_game_noad_{pointsP1}{pointsP2}.pkl"
    with open(Path(DIRPATH, fnameNoAd), 'wb') as fh:
        pickle.dump(probWinGameNoAdInterp, fh)
print("\rDone" + 50 * ' ')

