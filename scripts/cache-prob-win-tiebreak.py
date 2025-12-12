#!/usr/bin/env python3

"""
This script computes and caches the probability that *Player1* wins the tiebreak, given the
probability that each player wins a point on serve. This is useful because this calculation
is expensive. The script performs the calculation over a 2-D grid of point-winning probabilities,
and the resulting tiebreak-winning probabilities are saved as an interpolated function that can
be evaluated quickly. One such function is generated and cached for every possible starting score
in the tiebreak, and for each player serving next.

Each function is saved in a separate file. Example filenames:
 + prob_win_tbreak7_P1_32.pkl
 + prob_win_tbreak10_P2_32.pkl
where we used the following conventions:
 + "tbreak7"/"tbreak10" indicates a regular vs a super tiebreak.
 + "P1"/"P2" indicates which player serves next in the tiebreak.
 + The final two digits represent the starting score (Player1's score first).
   For example, "32" corresponds to 3-2.

Example of how to use such a cached function:

    with open('data-cache/prob_win_tbreak7_P1_32.pkl', 'rb') as fh:
        f = pickle.load(fh)
        prob_P1_wins_point_serving = 0.57
        prob_P2_wins_point_serving = 0.64
        prob_P1_wins_tbreak = f(prob_P1_wins_point_serving, prob_P2_wins_point_serving).item()

WARNING:
This is a very long-running script. To control whether we generate cache files for a regular
tiebreak (7 points to win) or a super tiebreak (10 points to win), set the IS_SUPER variable
below. It defaults to False (regular tiebreak).
"""
from pathlib           import Path
from scipy.interpolate import RectBivariateSpline
import os, pickle, sys
import numpy as np

# add path to the src directory if not in PYTHONPATH already
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from tennis_lab.core.tiebreak_score        import TiebreakScore
from tennis_lab.core.match_format          import MatchFormat, POINTS_TO_WIN_TIEBREAK, POINTS_TO_WIN_SUPERTIEBREAK
from tennis_lab.paths.tiebreak_probability import probabilityP1WinsTiebreak

# The directory where to store (pickle) the interpolated functions
DIRPATH = Path(PROJECT_ROOT, "data-cache")
DIRPATH.mkdir(exist_ok=True)

# Whether we are running the script for a regular or a super-tiebreak
IS_SUPER    = False
pointsToWin = POINTS_TO_WIN_SUPERTIEBREAK if IS_SUPER else POINTS_TO_WIN_TIEBREAK

# Interpolation grid for the probabilities that P1 and P2 win when serving
GRID_SZ = 50
P1s = np.linspace(0.0001, 0.9999, GRID_SZ)
P2s = np.linspace(0.0001, 0.9999, GRID_SZ)

# List all possible scores in the tiebreak.
initScoresInter  = [(p1, p2) for p1 in range(pointsToWin) for p2 in range(pointsToWin)]  # the tiebreak is not over
initScoresP1Won  = [(pointsToWin, p1) for p1 in range(pointsToWin-1)]                    # tiebreak over: P1 won
initScoresP1Lost = [(p1, pointsToWin) for p1 in range(pointsToWin-1)]                    # tiebreak over: P1 lost
initScores       = initScoresInter + initScoresP1Won + initScoresP1Lost

# Calculate the probability of winning the tiebreak starting from all possible scores.
# Two such calculations are performed, to allow either Player 1 or Player 2 to serve the next point.
iteration = 0
for playerServing in (1, 2):
    for (pointsP1, pointsP2) in initScores:
        
        # log progress
        iteration += 1
        prefix = f"\r[{iteration:3d}/{2 * len(initScores):3d}] P{playerServing} serving, score ({pointsP1}, {pointsP2})..."
        print(prefix, end="", flush=True)
        
        score = TiebreakScore(pointsP1, pointsP2, IS_SUPER)

        if (pointsP1, pointsP2) in initScoresInter:
            ProbWinTB = []
            for i, p1 in enumerate(P1s):
                row = []
                for j, p2 in enumerate(P2s):
                    cellNum = i * GRID_SZ + j + 1
                    print(f"{prefix} {cellNum:4d}/{GRID_SZ**2}", end="", flush=True)
                    row.append(probabilityP1WinsTiebreak(score, playerServing, p1, p2))
                ProbWinTB.append(row)
        elif (pointsP1, pointsP2) in initScoresP1Won:
            ProbWinTB = [[1.0 for p2 in P2s] for p1 in P1s]
        elif (pointsP1, pointsP2) in initScoresP1Lost:
            ProbWinTB = [[0.0 for p2 in P2s] for p1 in P1s]
        else:
            raise Exception(f"Unknown score: {score}")

        probWinTBreakInterp = RectBivariateSpline(P1s, P2s, ProbWinTB)

        # Save the interpolated function to file
        fname = f"prob_win_tbreak{pointsToWin}_P{playerServing}_{pointsP1}{pointsP2}.pkl"
        with open(Path(DIRPATH, fname), 'wb') as fh:
            pickle.dump(probWinTBreakInterp, fh)

print("\rDone" + 50 * ' ')
