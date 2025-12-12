"""MatchPath class representing possible score progressions in a tennis match."""

from __future__ import annotations
from copy       import deepcopy
from typing     import Literal
from tennis_lab.core.match_score import MatchScore

class MatchPath:
    """
    Represents a valid score progression in a tennis match, starting from a given initial score.
    The score progression ends when reaching a final score (one player wins the match).

    NOTE: The score granularity along the path is sets, not games or points. Each entry in the
    score history represents the match score after a complete set. The initial score cannot have
    a set in progress.

    Attributes:
    -----------
    scoreHistory: list[MatchScore]
       The score history of the match.

    Methods:
    --------
    __init__(initialScore: MatchScore)
       Initialize the path with its initial score.
    increment() -> tuple["MatchPath", "MatchPath"] | "MatchPath"
        Extend the path by one set, with the result of the set being a win for either player.
    generateAllPaths(initialScore: MatchScore) -> list["MatchPath"]
        Factory method generating all possible match score paths that start from a given initial score.
    __str__() -> str
        Returns a string representation of the score history.
    """

    def __init__(self, initialScore: MatchScore):
        """
        Initialize the path with its initial score.

        Parameters:
        -----------
        initialScore - the starting score of the score progression (must not have a set in progress)

        Raises:
        -------
        ValueError - if initialScore is not a MatchScore instance
        ValueError - if initialScore has a set in progress
        """
        if not isinstance(initialScore, MatchScore):
            raise ValueError("initialScore must be a MatchScore instance.")
        if initialScore.setInProgress:
            raise ValueError("initialScore cannot have a set in progress.")

        self._scores: list[MatchScore] = [initialScore]

    @property
    def scoreHistory(self) -> list[MatchScore]:
        """
        The score history of the match.
        """
        return self._scores

    def increment(self) -> tuple["MatchPath", "MatchPath"] | "MatchPath":
        """
        Extend the current path by one set, a win for either Player1 or Player2.
        This process creates two new paths.

        Returns:
        --------
        Two new paths if the match is not over, copy of self otherwise.
        """
        lastScore = self._scores[-1]

        # the match is over, we cannot increment this path
        if lastScore.isFinal:
            return deepcopy(self)

        # calculate the next possible two scores
        nextScores = lastScore.nextSetScores()

        # create two new paths, one for each possible outcome of the next set
        path1 = deepcopy(self)
        path1._scores.append(nextScores[0])

        path2 = deepcopy(self)
        path2._scores.append(nextScores[1])

        return path1, path2

    @staticmethod
    def generateAllPaths(initialScore: MatchScore) -> list["MatchPath"]:
        """
        Factory method generating all possible score paths that start from a given initial score.

        Parameters:
        -----------
        initialScore - the starting score for all paths
        """
        seedPath = MatchPath(initialScore)
        return MatchPath._extendPaths([seedPath])

    @staticmethod
    def _extendPaths(paths: list["MatchPath"]) -> list["MatchPath"]:
        """
        Helper method, used to extend each given score path until the match is over.
        """
        # attempt to extend each given path by one set
        pathsIncremented = MatchPath._incrementPaths(paths)

        # we are done when no input path can be incremented further
        doneExtending = len(pathsIncremented) == len(paths)

        # if we're not done, attempt to increment the paths again
        return paths if doneExtending else MatchPath._extendPaths(pathsIncremented)

    @staticmethod
    def _incrementPaths(paths: list["MatchPath"]) -> list["MatchPath"]:
        """
        Helper method, used to increment each given path by one set, using 'self.increment()'.

        A path cannot be incremented once the match is over.
        This implies that the length of the output list equals the length of the input list
        iff none of the given paths can be incremented.
        """
        pathsIncremented = []   # stores incremented paths
        for path in paths:
            lastScore = path._scores[-1]

            # increment the score unless the score is final
            if not lastScore.isFinal:
                pathsNew = path.increment()
                pathsIncremented.extend(pathsNew)
            else:
                pathsIncremented.append(deepcopy(path))

        return pathsIncremented

    def __str__(self) -> str:
        """
        Returns a string representation of the path, as a list of scores.
        """
        s = "["
        for score in self._scores:
            s += str(score.sets(pov=1)) + ", "
        return s[:-2] + "]"
