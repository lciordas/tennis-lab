#!/usr/bin/env python3

"""
This script computes and caches the probability that *Player1* wins a set, given the
probability that each player wins a point on serve. This is useful because this calculation
is expensive. The script performs the calculation over a 2-D grid of point-winning probabilities,
and the resulting set-winning probabilities are saved as an interpolated function that can
be evaluated quickly. One such function is generated and cached for every possible starting score
in the set (that represents a game boundary), and for each player serving next.

Each function is saved in a separate file. Example filenames:
 + prob_win_set_P1_32.pkl
 + prob_win_set_P2_65.pkl
where we used the following conventions:
 + "P1"/"P2" indicates which player serves next in the set.
 + The final two digits represent the starting score (Player1's score first).
   For example, "32" corresponds to 3-2.

Example of how to use such a cached function:

    with open('data-cache/prob_win_set_P1_32.pkl', 'rb') as fh:
        f = pickle.load(fh)
        prob_P1_wins_point_serving = 0.57
        prob_P2_wins_point_serving = 0.64
        prob_P1_wins_set = f(prob_P1_wins_point_serving, prob_P2_wins_point_serving).item()
"""
from pathlib           import Path
from scipy.interpolate import RectBivariateSpline
import os, pickle, shutil, sys
import numpy as np

# add path to the src directory if not in PYTHONPATH already
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from tennis_lab.core.set_score        import SetScore
from tennis_lab.core.match_format     import MatchFormat
from tennis_lab.paths.set_probability import _probabilityP1WinsSetFromGameBoundary
from tennis_lab.paths.set_path        import SetPath

# The directory where to store (pickle) the interpolated functions
DIRPATH = Path(PROJECT_ROOT, "data-cache")
DIRPATH.mkdir(exist_ok=True)

# Interpolation grid for the probabilities that P1 and P2 win when serving
GRID_SZ = 50
P1s = np.linspace(0.0001, 0.9999, GRID_SZ)
P2s = np.linspace(0.0001, 0.9999, GRID_SZ)

# List all possible game scores in a set (except 6-6).
initScoresInter  = [(p1, p2) for p1 in range(6) for p2 in range(6)]
initScoresInter.extend([(5, 6), (6, 5)])                              # intermediate scores: the set is not over
initScoresP1Won  = [(6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (7, 5)]   # set is over: P1 won
initScoresP1Lost = [(0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (5, 7)]   # set is over: P1 lost
initScores       = initScoresInter + initScoresP1Won + initScoresP1Lost

# Match format for set score creation
FORMAT = MatchFormat()

# Calculate the probability of winning the set starting from all possible scores.
# Two such calculations are performed, to allow either Player 1 or Player 2 to serve the next game.
iteration = 0
for playerServing in (1, 2):
    for (gamesP1, gamesP2) in initScores:

        # log progress
        iteration += 1
        prefix = f"\r[{iteration:3d}/{2 * len(initScores):3d}] P{playerServing} serving, score ({gamesP1}, {gamesP2})..."
        print(prefix, end="", flush=True)

        score = SetScore(gamesP1, gamesP2, isFinalSet=False, matchFormat=FORMAT)

        if (gamesP1, gamesP2) in initScoresInter:
            
            # Pre-generate all the score path starting from this score
            paths = SetPath.generateAllPaths(score, playerServing)

            ProbWinSet = []
            for i, p1 in enumerate(P1s):
                row = []
                for j, p2 in enumerate(P2s):
                    cellNum = i * GRID_SZ + j + 1
                    print(f"{prefix} {cellNum:4d}/{GRID_SZ**2}", end="", flush=True)
                    row.append(_probabilityP1WinsSetFromGameBoundary(score, playerServing, p1, p2, paths))
                ProbWinSet.append(row)
        elif (gamesP1, gamesP2) in initScoresP1Won:
            ProbWinSet = [[1.0 for p2 in P2s] for p1 in P1s]
        elif (gamesP1, gamesP2) in initScoresP1Lost:
            ProbWinSet = [[0.0 for p2 in P2s] for p1 in P1s]
        else:
            raise Exception(f"Unknown score: {score}")

        probWinSetInterp = RectBivariateSpline(P1s, P2s, ProbWinSet)

        # Save the interpolated function to file
        fname = f"prob_win_set_P{playerServing}_{gamesP1}{gamesP2}.pkl"
        with open(Path(DIRPATH, fname), 'wb') as fh:
            pickle.dump(probWinSetInterp, fh)

# special case: set tied at 6-6
# the probability of winning the set is the probability of winning the tiebreaker
# we assume that cached results for the tiebreaker are available
try:
    shutil.copy(Path(DIRPATH, "prob_win_tbreak7_P1_00.pkl"), Path(DIRPATH, "prob_win_set_P1_66.pkl"))
    shutil.copy(Path(DIRPATH, "prob_win_tbreak7_P2_00.pkl"), Path(DIRPATH, "prob_win_set_P2_66.pkl"))
except FileNotFoundError as e:
    print(f"\nWarning: Could not copy tiebreak cache files for 6-6 score: {e}")
    print("Run cache-prob-win-tiebreak.py first to generate tiebreak cache files.")

print("\rDone" + 50 * ' ')
