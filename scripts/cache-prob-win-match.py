#!/usr/bin/env python3

"""
This script computes and caches the probability that *Player1* wins a match, given the
probability that each player wins a point on serve. This is useful because this calculation
is expensive. The script performs the calculation over a 2-D grid of point-winning probabilities,
and the resulting match-winning probabilities are saved as an interpolated function that can
be evaluated quickly. One such function is generated and cached for every possible starting score
in the match (at set boundaries only).

Each function is saved in a separate file. Example filenames:
 + prob_win_match_bo3_11.pkl
 + prob_win_match_bo5_02.pkl
where we used the following conventions:
 + "bo3"/"bo5" indicates best-of-3 vs best-of-5 match format.
 + The final two digits represent the starting score (Player1's sets first).
   For example, "11" corresponds to 1-1.

Example of how to use such a cached function:

    with open('data-cache/prob_win_match_bo5_11.pkl', 'rb') as fh:
        f = pickle.load(fh)
        prob_P1_wins_point_serving = 0.57
        prob_P2_wins_point_serving = 0.64
        prob_P1_wins_match = f(prob_P1_wins_point_serving, prob_P2_wins_point_serving).item()
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

from tennis_lab.core.match_score        import MatchScore
from tennis_lab.core.match_format       import MatchFormat
from tennis_lab.paths.match_probability import _probabilityP1WinsMatchFromSetBoundary
from tennis_lab.paths.match_path        import MatchPath

# The directory where to store (pickle) the interpolated functions
DIRPATH = Path(PROJECT_ROOT, "data-cache")
DIRPATH.mkdir(exist_ok=True)

# Interpolation grid for the probabilities that P1 and P2 win when serving
GRID_SZ = 50
P1s = np.linspace(0.0001, 0.9999, GRID_SZ)
P2s = np.linspace(0.0001, 0.9999, GRID_SZ)

# ==============================================================
FORMAT3 = MatchFormat(bestOfSets=3)

# list all possible set scores in a match when playing best of 3
initScores3Inter  = [(0,0), (1,0),
                     (0,1), (1,1)]   # intermediate scores: the match is not over
initScores3P1Won  = [(2,0), (2,1)]   # match is over: P1 won
initScores3P1Lost = [(0,2), (1,2)]   # match is over: P1 lost
initScores3       = initScores3Inter + initScores3P1Won + initScores3P1Lost

iteration = 0
for (setsP1, setsP2) in initScores3:

    # log progress
    iteration += 1
    prefix = f"\r[{iteration:3d}/{len(initScores3):3d}] best of 3, score ({setsP1}, {setsP2})..."
    print(prefix, end="", flush=True)

    score = MatchScore(setsP1, setsP2, FORMAT3)

    if (setsP1, setsP2) in initScores3Inter:

        # Pre-generate all the score paths starting from this score
        paths = MatchPath.generateAllPaths(score)

        ProbWinMatch = []
        for i, p1 in enumerate(P1s):
            row = []
            for j, p2 in enumerate(P2s):
                cellNum = i * GRID_SZ + j + 1
                print(f"{prefix} {cellNum:4d}/{GRID_SZ**2}", end="", flush=True)
                row.append(_probabilityP1WinsMatchFromSetBoundary(score, p1, p2, paths))
            ProbWinMatch.append(row)
    elif (setsP1, setsP2) in initScores3P1Won:
        ProbWinMatch = [[1.0 for p2 in P2s] for p1 in P1s]
    else:
        ProbWinMatch = [[0.0 for p2 in P2s] for p1 in P1s]

    probWinMatch3Interp = RectBivariateSpline(P1s, P2s, ProbWinMatch)

    # Save the interpolated function to file
    fname = f"prob_win_match_bo3_{setsP1}{setsP2}.pkl"
    with open(Path(DIRPATH, fname), 'wb') as fh:
        pickle.dump(probWinMatch3Interp, fh)

# ==============================================================
FORMAT5 = MatchFormat(bestOfSets=5)

# list all possible set scores in a match when playing best of 5
initScores5Inter  = [(0,0), (1,0), (2,0),
                     (0,1), (1,1), (2,1),
                     (0,2), (1,2), (2,2)]   # intermediate scores: the match is not over
initScores5P1Won  = [(3,0), (3,1), (3,2)]   # match is over: P1 won
initScores5P1Lost = [(0,3), (1,3), (2,3)]   # match is over: P1 lost
initScores5       = initScores5Inter + initScores5P1Won + initScores5P1Lost

iteration = 0
for (setsP1, setsP2) in initScores5:

    # log progress
    iteration += 1
    prefix = f"\r[{iteration:3d}/{len(initScores5):3d}] best of 5, score ({setsP1}, {setsP2})..."
    print(prefix, end="", flush=True)

    score = MatchScore(setsP1, setsP2, FORMAT5)

    if (setsP1, setsP2) in initScores5Inter:

        # Pre-generate all the score paths starting from this score
        paths = MatchPath.generateAllPaths(score)

        ProbWinMatch = []
        for i, p1 in enumerate(P1s):
            row = []
            for j, p2 in enumerate(P2s):
                cellNum = i * GRID_SZ + j + 1
                print(f"{prefix} {cellNum:4d}/{GRID_SZ**2}", end="", flush=True)
                row.append(_probabilityP1WinsMatchFromSetBoundary(score, p1, p2, paths))
            ProbWinMatch.append(row)
    elif (setsP1, setsP2) in initScores5P1Won:
        ProbWinMatch = [[1.0 for p2 in P2s] for p1 in P1s]
    else:
        ProbWinMatch = [[0.0 for p2 in P2s] for p1 in P1s]

    probWinMatch5Interp = RectBivariateSpline(P1s, P2s, ProbWinMatch)

    # Save the interpolated function to file
    fname = f"prob_win_match_bo5_{setsP1}{setsP2}.pkl"
    with open(Path(DIRPATH, fname), 'wb') as fh:
        pickle.dump(probWinMatch5Interp, fh)

print("\rDone" + 50 * ' ')
