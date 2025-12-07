"""GameScore class representing the score in a tennis game."""

from typing import Literal, Optional
from src.core.match_format import MatchFormat

class GameScore:
    """
    Represents the running score of a tennis game.

    Class Constants:
    ----------------
    NUM_POINTS_WIN: int
        Number of points needed to win a game.

    Attributes:
    -----------
    isBlank: bool
        Whether the current score is 0-0.
    isDeuce: bool
        Whether the current score is 'deuce'.
    isFinal: bool
        Whether this is a final score (game decided).
    winner: Optional[Literal[1, 2]]
        Returns which player won the game, None if score is not final.
    playerWithAdvantage: Optional[Literal[1, 2]]
        Returns which player has 'advantage', None if n/a.

    Methods:
    --------
    __init__(pointsP1: int, pointsP2: int, matchFormat: MatchFormat)
        Initialize the score to an arbitrary (but valid) initial value.
    recordPoint(pointWinner: Literal[1, 2])
        Update the score with the result of the next point.
    asPoints(pov: Literal[1,2]) -> tuple[int, int]
        Get the current score, as a tuple of two integers.
    asTraditional(pov: Literal[1,2]) -> str
        Get the current score, expressed in the traditional tennis convention of 0, 15, 30, 40.
    nextScores() -> Optional[tuple["GameScore", "GameScore"]]
        Calculates two scores, the outcome of either player winning the next point.
    __eq__(other: "GameScore") -> bool
        Implemented the equality operation.
    __repr__() -> str
        Valid Python expression that can be used to recreate this GameScore instance.
    __str__() -> str
        Returns the traditional score format for display.
    """

    # Number of points needed to win a game
    NUM_POINTS_WIN = 4

    def __init__(self,
                 pointsP1   : int,
                 pointsP2   : int,
                 matchFormat: MatchFormat):
        """
        Initialize the score to an arbitrary (but valid) initial value.

        The score is represented as two integers, the number of points won by each
        player, and not by the more traditional tennis convention of 0, 15, 30, 40.
        Example: the score 30-15 is represented as (2,1).

        Parameters:
        -----------
        pointsP1    - initial number of points for Player1
        pointsP2    - initial number of points for Player2
        matchFormat - describes the match format (example: whether using 'no ad' rule)

        Raises:
        -------
        ValueError - if the score is not valid
        """
        if not GameScore._isValidScore((pointsP1, pointsP2)):
            raise ValueError(f"Invalid initial score: {(pointsP1, pointsP2)}")

        # keep track of the current score as number of points
        self._currPointsP1: int           = pointsP1
        self._currPointsP2: int           = pointsP2
        self._matchFormat : "MatchFormat" = matchFormat
        self._noAdRule    : bool          = matchFormat.noAdRule
        self._capPoints   : bool          = matchFormat.capPoints

        if self._capPoints:
            self._cap_score()

    @property
    def isBlank(self) -> bool:
        """
        Returns whether the current score is 0-0.
        """
        return self._currPointsP1 == self._currPointsP2 == 0

    @property
    def isDeuce(self) -> bool:
        """
        Returns whether the current score is 'deuce'.

        Deuce is defined as both players having the same number of points (more than two).
        For example 30-30 is not deuce.
        """
        return (self._currPointsP1 == self._currPointsP2) and (self._currPointsP1 >= GameScore.NUM_POINTS_WIN - 1)

    @property
    def isFinal(self) -> bool:
        """
        Returns whether this is a final score (game decided).
        """
        return self._playerWon(1) or self._playerWon(2)

    @property
    def playerWithAdvantage(self) -> Optional[Literal[1, 2]]:
        """
        Returns which player has 'advantage', None if n/a.
        """
        if (self._currPointsP1 - self._currPointsP2 == 1) and (self._currPointsP1 >= GameScore.NUM_POINTS_WIN):
            return 1
        if (self._currPointsP2 - self._currPointsP1 == 1) and (self._currPointsP2 >= GameScore.NUM_POINTS_WIN):
            return 2
        return None

    @property
    def winner(self) -> Optional[Literal[1, 2]]:
        """
        Returns which player won the game, None if score is not final.
        """
        if self._playerWon(1):
            return 1
        if self._playerWon(2):
            return 2
        return None

    def recordPoint(self, pointWinner: Literal[1, 2]):
        """
        Update the score with the result of the next point.

        Parameters:
        ----------
        pointWinner - which player won the point (1 or 2)

        Raises:
        -------
        ValueError - if pointWinner is not 1 or 2, or if the game is already over
        """
        if pointWinner not in (1, 2):
            raise ValueError(f"Invalid pointWinner: {pointWinner}. Must be 1 or 2.")
        if self.isFinal:
            raise ValueError("Cannot record point: game is already over.")

        self._currPointsP1 += (1 if pointWinner == 1 else 0)
        self._currPointsP2 += (1 if pointWinner == 2 else 0)

        if self._capPoints:
            self._cap_score()

    def asPoints(self, pov: Literal[1, 2]) -> tuple[int, int]:
        """
        Get the current score of the game, as a tuple of two integers, the number of
        points won by each player. Example: the score 30-15 is represented as (2, 1).

        We must specify the point of view (1 or 2) from which to display the score.
        For example, if we display the score from the point of view of Player1, the
        first element of the tuple will be the score of Player1, and the 2nd element
        will be the score of Player2.

        Parameter:
        ----------
        pov - point of view from which to display the score (1, 2)

        Returns:
        --------
        The current score of the game, as a tuple of two integers.

        Raises:
        -------
        ValueError - if pov is not 1 or 2
        """
        if pov not in (1, 2):
            raise ValueError(f"Invalid pov: {pov}. Must be 1 or 2.")
        pointsFirst, pointsSecond = (self._currPointsP1, self._currPointsP2) if pov == 1 else \
                                    (self._currPointsP2, self._currPointsP1)
        return pointsFirst, pointsSecond

    def asTraditional(self, pov: Literal[1, 2]) -> str:
        """
        Returns the current score of the game, expressed in the traditional tennis
        convention of 0, 15, 30, 40.

        We must specify the point of view (1 or 2) from which to display the score.
        For example, if we display the score from the point of view of Player1, the
        first element of the tuple will be the score of Player1, and the 2nd element
        will be the score of Player2.

        Parameter:
        ----------
        pov - point of view from which to display the score (1, 2)

        Returns:
        --------
        The current score of the game, in traditional format.

        Raises:
        -------
        ValueError - if pov is not 1 or 2
        """
        if pov not in (1, 2):
            raise ValueError(f"Invalid pov: {pov}. Must be 1 or 2.")
        return GameScore._convertScore(self.asPoints(pov))

    def nextScores(self) -> Optional[tuple["GameScore", "GameScore"]]:
        """
        Calculates two scores, the outcome of either player winning
        the next point from the current score. This is possible only
        if the score is not already final.

        Returns:
        --------
        A tuple of two GameScore instances, the first representing the
        score if Player1 wins the next point, the second representing
        the score if Player2 wins the next point.
        If the score is already final, returns None.
        """
        if self.isFinal:
            return None

        return GameScore(self._currPointsP1+1, self._currPointsP2  , self._matchFormat), \
               GameScore(self._currPointsP1  , self._currPointsP2+1, self._matchFormat)

    def _playerWon(self, player: Literal[1, 2]) -> bool:
        """
        Tests whether a given player won the game, considering the current score.
        """
        if self._noAdRule:
            P1_won = (self._currPointsP1 == GameScore.NUM_POINTS_WIN) and (self._currPointsP2 < GameScore.NUM_POINTS_WIN)
            P2_won = (self._currPointsP2 == GameScore.NUM_POINTS_WIN) and (self._currPointsP1 < GameScore.NUM_POINTS_WIN)
        else:
            P1_won = (self._currPointsP1 >= GameScore.NUM_POINTS_WIN) and (self._currPointsP1 - self._currPointsP2 > 1)
            P2_won = (self._currPointsP2 >= GameScore.NUM_POINTS_WIN) and (self._currPointsP2 - self._currPointsP1 > 1)

        return P1_won if player == 1 else P2_won

    def _cap_score(self):
        """
        Normalizing the score means representing all deuces as 3-3,
        and all adds as 3-4 or 4-3. Without normalization, if there
        are multiple deuces, the score grows unbounded, which can be
        problematic for some applications.
        """
        if self.isDeuce:
            self._currPointsP1 = self._currPointsP2 = GameScore.NUM_POINTS_WIN - 1
        elif self.playerWithAdvantage == 1:
            self._currPointsP1 = GameScore.NUM_POINTS_WIN
            self._currPointsP2 = GameScore.NUM_POINTS_WIN - 1
        elif self.playerWithAdvantage == 2:
            self._currPointsP1 = GameScore.NUM_POINTS_WIN - 1
            self._currPointsP2 = GameScore.NUM_POINTS_WIN

    @staticmethod
    def _isValidScore(score: tuple[int, int]) -> bool:
        """
        Checks that a given game score is valid.

        Parameters:
        -----------
        score - the game score, as points won by each player

        Returns:
        --------
        True if the score is valid, else False.
        """
        p1, p2 = score
        if not isinstance(p1, int) or not isinstance(p2, int):
            return False
        if p1 < 0 or p2 < 0:
            return False

        # score below or at 40-40
        if p1 <= GameScore.NUM_POINTS_WIN - 1 and p2 <= GameScore.NUM_POINTS_WIN - 1:
            return True

        # game over before reaching deuce
        if (p1 == GameScore.NUM_POINTS_WIN and p2 <= GameScore.NUM_POINTS_WIN - 2) or \
           (p2 == GameScore.NUM_POINTS_WIN and p1 <= GameScore.NUM_POINTS_WIN - 2):
            return True

        # the score reached deuce
        return abs(p1 - p2) <= 2

    @staticmethod
    def _convertScore(score: tuple[int, int]) -> str:
        """
        Converts the score of a game, expressed as points won by each
        player, to the traditional tennis convention of 0, 15, 30, 40.

        Parameters:
        -----------
        score - the score of the game, as points won by each player

        Returns:
        --------
        The point score in its traditional representation, as string.
        """
        score_map = {0: "0", 1: "15", 2: "30", 3: "40"}
        pFirst, pSecond = score
        N = GameScore.NUM_POINTS_WIN
        if pFirst <= N - 1 and pSecond <= N - 1:
            return f"{score_map[pFirst]}-{score_map[pSecond]}"
        elif pFirst < N - 1 and pSecond == N:
            return f"{score_map[pFirst]}-win"
        elif pSecond < N - 1 and pFirst == N:
            return f"win-{score_map[pSecond]}"
        elif pFirst >= N - 1 and pSecond >= N - 1:
            if pFirst == pSecond:
                return "deuce"
            elif pFirst == pSecond + 1:
                return "ad-40"
            elif pFirst == pSecond - 1:
                return "40-ad"
            elif pFirst >= pSecond + 2:
                return "win-40"
            elif pFirst <= pSecond - 2:
                return "40-win"
            else:
                return "error"
        else:
            return "error"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GameScore):
            return NotImplemented
        return (self._currPointsP1 == other._currPointsP1 and
                self._currPointsP2 == other._currPointsP2 and
                self._noAdRule     == other._noAdRule)

    def __repr__(self) -> str:
        """
        Valid Python expression that can be used to recreate this GameScore instance.
        """
        return f"GameScore(pointsP1={self._currPointsP1}, pointsP2={self._currPointsP2}, matchFormat={repr(self._matchFormat)})"

    def __str__(self) -> str:
        """
        Returns the traditional score format for display (from Player 1's perspective).
        """
        return self.asTraditional(pov=1)

    def __hash__(self) -> int:
        return hash((self._currPointsP1, self._currPointsP2, self._noAdRule))
