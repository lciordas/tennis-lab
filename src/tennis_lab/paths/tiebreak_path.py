"""TiebreakPath class representing possible score progressions in a tennis tiebreak."""

from __future__  import annotations
from collections import namedtuple
from copy        import deepcopy
from typing      import Literal
from tennis_lab.core.tiebreak_score import TiebreakScore

class TiebreakPath:
    """
    Represents a valid score progression in a tennis tiebreak, starting from a given initial score.
    Provides tools for building all such score progressions.

    Attributes:
    -----------
    scoreHistory: list[PathEntry]
       The score history of the tiebreak (including which player serves each point).

    Methods:
    --------
    __init__(initialScore: TiebreakScore, playerServing: Literal[1,2])
       Initialize the path with its initial score.
    increment() -> tuple["TiebreakPath", "TiebreakPath"] | "TiebreakPath"
        Extend the path by one point, with the result of the point being a win for either player.
    generateAllPaths(initialScore: TiebreakScore, playerServing: Literal[1,2]) -> list["TiebreakPath"]
        Factory method generating all possible tiebreak score paths that start from a given initial score.
    __str__() -> str
        Returns a string representation of the score history.
    """

    # A "path entry" bundles together two items:
    #  + the tiebreak score (an instance of TiebreakScore)
    #  + which player serves this point (1 or 2)
    PathEntry = namedtuple('PathEntry', ('score', 'playerServing'))

    def __init__(self, initialScore: TiebreakScore, playerServing: Literal[1, 2]):
        """
        Initialize the path with its initial score.

        Parameters:
        -----------
        initialScore  - the starting score of the score progression
        playerServing - which player is serving the next point

        Raises:
        -------
        ValueError - if initialScore is not a TiebreakScore instance
        ValueError - if playerServing is not 1 or 2
        """
        if not isinstance(initialScore, TiebreakScore):
            raise ValueError(f"Invalid initialScore: must be a TiebreakScore instance.")
        if not isinstance(playerServing, int) or playerServing not in [1, 2]:
            raise ValueError("playerServing must be 1 or 2")

        self._entries: list[TiebreakPath.PathEntry] = [
            TiebreakPath.PathEntry(score=initialScore, playerServing=playerServing)
        ]

    @property
    def scoreHistory(self) -> list[PathEntry]:
        """
        The score history of the tiebreak (including which player serves each point).
        """
        return self._entries

    def increment(self) -> tuple["TiebreakPath", "TiebreakPath"] | "TiebreakPath":
        """
        Extend the current path by one point, a win for either Player1 or Player2.
        This process creates two new paths.

        Returns:
        --------
        Two new paths if the tiebreak is not over, copy of self otherwise.
        """
        lastEntry = self._entries[-1]
        lastScore = lastEntry.score

        # the tiebreak is over, we cannot increment this path
        if lastScore.isFinal:
            return deepcopy(self)

        # calculate the next possible two scores
        nextScores = lastScore.nextScores()

        # decide which player will serve from the next score position
        # In tiebreaks: first player serves 1 point, then alternate every 2 points
        # After 1 point: switch. After 2: same. After 3: switch. etc.
        # Switch occurs when (pointsPlayed + 1) is odd, i.e., pointsPlayed is even
        pointsP1, pointsP2 = lastScore.asPoints(pov=1)
        pointsPlayed       = pointsP1 + pointsP2
        switchServe        = pointsPlayed % 2 == 0
        playerServingNext  = (3 - lastEntry.playerServing) if switchServe else lastEntry.playerServing

        # create two new paths, one for each possible outcome of the next point
        path1 = deepcopy(self)
        path1._entries.append(TiebreakPath.PathEntry(score=nextScores[0], playerServing=playerServingNext))

        path2 = deepcopy(self)
        path2._entries.append(TiebreakPath.PathEntry(score=nextScores[1], playerServing=playerServingNext))

        return path1, path2

    @staticmethod
    def generateAllPaths(initialScore: TiebreakScore,
                         playerServing: Literal[1, 2]) -> list["TiebreakPath"]:
        """
        Factory method generating all possible score paths that start from a given initial score.

        Parameters:
        -----------
        initialScore  - the starting score for all paths
        playerServing - which player is serving the next point
        """
        seedPath = TiebreakPath(initialScore, playerServing)
        return TiebreakPath._extendPaths([seedPath])

    @staticmethod
    def _extendPaths(paths: list["TiebreakPath"]) -> list["TiebreakPath"]:
        """
        Helper method, used to extend each given score path until the tiebreak is over,
        or it reaches the cutoff score (6-6 for regular, 9-9 for super-tiebreak).
        """
        # attempt to extend each given path by one point
        pathsIncremented = TiebreakPath._incrementPaths(paths)

        # we are done when no input path can be incremented further
        doneExtending = len(pathsIncremented) == len(paths)

        # if we're not done, attempt to increment the paths again
        return paths if doneExtending else TiebreakPath._extendPaths(pathsIncremented)

    @staticmethod
    def _incrementPaths(paths: list["TiebreakPath"]) -> list["TiebreakPath"]:
        """
        Helper method, used to increment each given path by one point, using 'self.increment()'.

        It imposes a cutoff: paths for which the current score is tied at 'pointsToWin-1'
        (6-6 for regular, 9-9 for super-tiebreak) are not incremented, they are returned
        unmodified.
        This implies that the length of the output list equals the length of the input list
        iff none of the given paths can be incremented.
        """
        pathsIncremented = []   # stores incremented paths
        for path in paths:
            lastScore = path._entries[-1].score

            # don't increment a path which reaches the cutoff score (e.g., 6-6 or 9-9)
            if lastScore.isDeuce:
                pathsIncremented.append(deepcopy(path))
                continue

            # increment the score unless the score is final
            if not lastScore.isFinal:
                pathsNew = path.increment()
                pathsIncremented.extend(pathsNew)
            else:
                pathsIncremented.append(deepcopy(path))

        return pathsIncremented

    def __str__(self) -> str:
        """
        Returns a string representation of the path, as a list of
        tuples: (pointsP1, pointsP2, playerServing).
        """
        s = "["
        for entry in self._entries:
            p1, p2 = entry.score.asPoints(pov=1)
            s += str((p1, p2, entry.playerServing)) + ", "
        return s[:-2] + "]"
