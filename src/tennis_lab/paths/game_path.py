"""GamePath class representing possible score progressions in a tennis game."""

from __future__ import annotations
from copy import deepcopy
from tennis_lab.core.game_score import GameScore

class GamePath:
    """
    Represents a valid score progression in a tennis game, starting from a given initial score.
    Provides tools for building all such score progressions.

    Attributes:
    -----------
    scoreHistory: list[GameScore]
       The score history of the game.

    Methods:
    --------
    __init__(initialScore: GameScore)
       Initialize the path with its initial score.
    increment() -> tuple["GamePath", "GamePath"] | "GamePath"
        Extend the path by one point, with the result of the point being a win for either player.
    generateAllPaths(initialScore: GameScore) -> list["GamePath"]
        Factory method generating all possible game score paths that start from a given initial score.
    __str__() -> str
        Returns a string representation of the score history.
    """

    def __init__(self, initialScore: GameScore):
        """
        Initialize the path with its initial score.

        Parameters:
        -----------
        initialScore - the starting score of the score progression

        Raises:
        -------
        ValueError - if initialScore is not a GameScore instance
        """
        if not isinstance(initialScore, GameScore):
            raise ValueError(f"Invalid initialScore: must be a GameScore instance.")
        self._scores: list[GameScore] = [initialScore]

    @property
    def scoreHistory(self) -> list[GameScore]:
        """
        The score history of the game.
        """
        return self._scores

    def increment(self) -> tuple["GamePath", "GamePath"] | "GamePath":
        """
        Extend the current path by one point, a win for either Player1 or Player2.
        This process creates two new paths.

        Returns:
        --------
        Two new paths if the game is not over, copy of self otherwise.
        """
        lastScore = self._scores[-1]

        # the game is over, we cannot increment this path
        if lastScore.isFinal:
            return deepcopy(self)

        # calculate the next possible two scores
        nextScores = lastScore.nextScores()

        # create two new paths, one for each possible outcome of the next point
        path1 = deepcopy(self); path1._scores.append(nextScores[0])
        path2 = deepcopy(self); path2._scores.append(nextScores[1])

        return path1, path2

    @staticmethod
    def generateAllPaths(initialScore: GameScore) -> list["GamePath"]:
        """
        Factory method generating all possible score paths that start from a given initial score.

        Parameters:
        -----------
        initialScore - the starting score for all paths
        """
        seedPath = GamePath(initialScore)
        return GamePath._extendPaths([seedPath])


    @staticmethod
    def _extendPaths(paths: list["GamePath"]) -> list["GamePath"]:
        """
        Helper method, used to extend each given score path until the game is over, or it reaches deuce.
        """
        # attempt to extend each given path by one point
        pathsIncremented = GamePath._incrementPaths(paths)

        # we are done when no input path can be incremented further
        doneExtending = len(pathsIncremented) == len(paths)

        # if we're not done, attempt to increment the paths again
        return paths if doneExtending else GamePath._extendPaths(pathsIncremented)

    @staticmethod
    def _incrementPaths(paths: list["GamePath"]) -> list["GamePath"]:
        """
        Helper method, used to increment each given path by one point, using 'self.increment()'.
        
        It imposes a cutoff: paths for which the current score is a deuce (when playing using
        standard 'advantage' rules) are not incremented, they are returned unmodified. 
        This implies that the length of the output list equals the length of the input list iff 
        none of the given paths can be incremented.        
        """
        pathsIncremented = []   # stores incremented paths
        for path in paths:
            lastScore = path._scores[-1]

            # we don't increment a path which reached 'deuce' (unless the game is played w/o adds)
            isDeuce         = lastScore.isDeuce
            standardScoring = not lastScore._matchFormat.noAdRule
            if isDeuce and standardScoring:
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
        Returns a string representation of the path, as a list of scores.
        """
        s = "["
        for score in self._scores:
            s += str(score.asPoints(pov=1)) + ", "
        return s[:-2] + "]"
