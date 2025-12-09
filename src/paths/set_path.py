"""SetPath class representing possible score progressions in a tennis set."""

from __future__  import annotations
from collections import namedtuple
from copy        import deepcopy
from typing      import Literal
from src.core.set_score import SetScore

class SetPath:
    """
    Represents a valid score progression in a tennis set, starting from a given initial score.
    Provides tools for building all such score progressions.

    NOTE: The score granularity along the path is games, not points. Each entry in the
    score history represents the set score after a complete game. The initial score
    cannot have a game or tiebreak in progress.

    Attributes:
    -----------
    scoreHistory: list[PathEntry]
       The score history of the set (including which player is serving next game).

    Methods:
    --------
    __init__(initialScore: SetScore, playerToServe: Literal[1,2])
       Initialize the path with its initial score.
    increment() -> tuple["SetPath", "SetPath"] | "SetPath"
        Extend the path by one game, with the result of the game being a win for either player.
    generateAllPaths(initialScore: SetScore, playerToServe: Literal[1,2]) -> list["SetPath"]
        Factory method generating all possible set score paths that start from a given initial score.
    __str__() -> str
        Returns a string representation of the score history.
    """

    # A "path entry" bundles together two items:
    #  + the set score (an instance of SetScore)
    #  + which player serves next game (1 or 2)
    PathEntry = namedtuple('PathEntry', ('score', 'playerToServe'))

    def __init__(self, initialScore: SetScore, playerToServe: Literal[1, 2]):
        """
        Initialize the path with its initial score.

        Parameters:
        -----------
        initialScore  - the starting score of the score progression (must not have a
                        game or tiebreak in progress)
        playerToServe - which player is serving the next game

        Raises:
        -------
        ValueError - if initialScore is not a SetScore instance
        ValueError - if initialScore has a game or tiebreak in progress
        ValueError - if playerToServe is not 1 or 2
        """
        if not isinstance(initialScore, SetScore):
            raise ValueError("initialScore must be a SetScore instance.")
        if initialScore.gameInProgress or initialScore.tiebreakInProgress:
            raise ValueError("initialScore cannot have a game or tiebreak in progress.")
        if not isinstance(playerToServe, int) or playerToServe not in [1, 2]:
            raise ValueError("playerToServe must be 1 or 2")

        self._entries: list[SetPath.PathEntry] = [
            SetPath.PathEntry(score=initialScore, playerToServe=playerToServe)
        ]

    @property
    def scoreHistory(self) -> list[PathEntry]:
        """
        The score history of the set (including which player is serving next game).
        """
        return self._entries

    def increment(self) -> tuple["SetPath", "SetPath"] | "SetPath":
        """
        Extend the current path by one game, a win for either Player1 or Player2.
        This process creates two new paths.

        Returns:
        --------
        Two new paths if the set is not over, copy of self otherwise.
        """
        lastEntry = self._entries[-1]
        lastScore = lastEntry.score

        # the set is over, we cannot increment this path
        if lastScore.isFinal:
            return deepcopy(self)

        # calculate the next possible two scores
        nextScores = lastScore.nextGameScores()

        # in sets, serve alternates every game
        playerServingNext = 3 - lastEntry.playerToServe

        # create two new paths, one for each possible outcome of the next game
        path1 = deepcopy(self)
        path1._entries.append(SetPath.PathEntry(score=nextScores[0], playerToServe=playerServingNext))

        path2 = deepcopy(self)
        path2._entries.append(SetPath.PathEntry(score=nextScores[1], playerToServe=playerServingNext))

        return path1, path2

    @staticmethod
    def generateAllPaths(initialScore: SetScore,
                         playerToServe: Literal[1, 2]) -> list["SetPath"]:
        """
        Factory method generating all possible score paths that start from a given initial score.

        Parameters:
        -----------
        initialScore  - the starting score for all paths
        playerToServe - which player is serving next game
        """
        seedPath = SetPath(initialScore, playerToServe)
        return SetPath._extendPaths([seedPath])

    @staticmethod
    def _extendPaths(paths: list["SetPath"]) -> list["SetPath"]:
        """
        Helper method, used to extend each given score path until the set is over,
        or it reaches the tied score (e.g., 6-6).
        """
        # attempt to extend each given path by one game
        pathsIncremented = SetPath._incrementPaths(paths)

        # we are done when no input path can be incremented further
        doneExtending = len(pathsIncremented) == len(paths)

        # if we're not done, attempt to increment the paths again
        return paths if doneExtending else SetPath._extendPaths(pathsIncremented)

    @staticmethod
    def _incrementPaths(paths: list["SetPath"]) -> list["SetPath"]:
        """
        Helper method, used to increment each given path by one game, using 'self.increment()'.

        It imposes a cutoff: paths for which the current score is tied (e.g., 6-6)
        are not incremented, they are returned unmodified.
        This implies that the length of the output list equals the length of the input list
        iff none of the given paths can be incremented.
        """
        pathsIncremented = []   # stores incremented paths
        for path in paths:
            lastScore = path._entries[-1].score

            # don't increment a path which reaches the tied score (e.g., 6-6)
            if lastScore.isTied:
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
        tuples: (gamesP1, gamesP2, playerToServe).
        """
        s = "["
        for entry in self._entries:
            p1, p2 = entry.score.games(pov=1)
            s += str((p1, p2, entry.playerToServe)) + ", "
        return s[:-2] + "]"