"""TiebreakerScore class representing the score in a tiebreaker or super-tiebreaker."""

from typing import Literal, Optional

class TiebreakerScore:
    """
    Represents the running score of a tiebreaker or super-tiebreaker.

    Class Constants:
    ----------------
    POINTS_TO_WIN_TIEBREAKER : int
        Points needed to win a standard tiebreaker (7).
    POINTS_TO_WIN_SUPER_TIEBREAKER : int
        Points needed to win a super-tiebreaker (10).

    Attributes:
    -----------
    isBlank: bool
        Whether the current score is 0-0.
    isDeuce: bool
        Whether the current score is 'deuce'.
    isFinal: bool
        Whether this is a final score (tiebreaker decided).
    winner: Optional[Literal[1, 2]]
        Returns which player won the tiebreaker, None if not yet decided.
    playerWithAdvantage: Optional[Literal[1, 2]]
        Returns which player has 'advantage', None if n/a.
    pointsToWin: int
        Number of points needed to win (7 for tiebreaker, 10 for super-tiebreaker).

    Methods:
    --------
    __init__(pointsP1: int, pointsP2: int, isSuper: bool, normalize: bool = False)
        Initialize the score to an arbitrary (but valid) initial value.
    recordPoint(pointWinner: Literal[1, 2])
        Update the score with the result of the next point.
    asPoints(pov: Literal[1,2]) -> tuple[int, int]
        Get the current score, as a tuple of two integers.
    nextScores() -> Optional[tuple["TiebreakerScore", "TiebreakerScore"]]
        Calculates two scores, the outcome of either player winning the next point.
    __eq__(other: "TiebreakerScore") -> bool
        Implemented the equality operation.
    __repr__() -> str
        Valid Python expression that can be used to recreate this TiebreakerScore instance.
    __str__() -> str
        Returns the score in "X-Y" format from Player 1's perspective.
    """

    POINTS_TO_WIN_TIEBREAKER       =  7
    POINTS_TO_WIN_SUPER_TIEBREAKER = 10

    def __init__(self, pointsP1: int, pointsP2: int, isSuper: bool, normalize: bool = False):
        """
        Initialize the score to an arbitrary (but valid) initial value.

        Parameters:
        -----------
        pointsP1  - initial number of points for Player1
        pointsP2  - initial number of points for Player2
        isSuper   - True if this is a super-tiebreaker
        normalize - if True, automatically normalize the score after initialization
                    and after each point update (default: False)

        Raises:
        -------
        ValueError - if isSuper is not a boolean or the score is not valid
        """
        if not isinstance(isSuper, bool):
            raise ValueError(f"Invalid isSuper: {isSuper}. Must be a boolean.")
        if not TiebreakerScore._isValidScore((pointsP1, pointsP2), isSuper):
            raise ValueError(f"Invalid initial score: {(pointsP1, pointsP2)}")

        self._currPointsP1: int  = pointsP1
        self._currPointsP2: int  = pointsP2
        self._isSuper     : bool = isSuper
        self._normalize   : bool = normalize

        if self._normalize:
            self._normalize_score()

    @property
    def isBlank(self) -> bool:
        """
        Returns whether the current score is 0-0.
        """
        return self._currPointsP1 == self._currPointsP2 == 0

    @property
    def isDeuce(self) -> bool:
        """
        While there is no official 'deuce' for a tiebreaker or super-tiebreaker,
        we define the 'deuce' for a tiebreaker or super-tiebreaker in the same way
        it is defined for a regular game.
        This predicate tests whether a (super-)tiebreaker score has reached 'deuce'.
        """
        return (self._currPointsP1 == self._currPointsP2) and (self._currPointsP1 >= self.pointsToWin - 1)

    @property
    def isFinal(self) -> bool:
        """
        Returns whether this is a final score (tiebreaker decided).
        """
        return self._playerWon(1) or self._playerWon(2)

    @property
    def playerWithAdvantage(self) -> Optional[Literal[1, 2]]:
        """
        Returns which player has 'advantage', None if n/a.
        Technically, there is no such thing when playing a tiebreaker or super-tiebreaker.
        However, we define 'advantage' for a player the same way it is defined for a regular game.
        """
        if (self._currPointsP1 - self._currPointsP2 == 1) and (self._currPointsP1 >= self.pointsToWin):
            return 1
        if (self._currPointsP2 - self._currPointsP1 == 1) and (self._currPointsP2 >= self.pointsToWin):
            return 2
        return None

    @property
    def winner(self) -> Optional[Literal[1, 2]]:
        """
        Returns which player won the tiebreaker, None if not yet decided.
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
        ValueError - if pointWinner is not 1 or 2
        """
        if pointWinner not in (1, 2):
            raise ValueError(f"Invalid pointWinner: {pointWinner}. Must be 1 or 2.")
        self._currPointsP1 += (1 if pointWinner == 1 else 0)
        self._currPointsP2 += (1 if pointWinner == 2 else 0)

        if self._normalize:
            self._normalize_score()

    def asPoints(self, pov: Literal[1,2]) -> tuple[int, int]:
        """
        Get the current tiebreaker score, as a tuple of two integers, the number of
        points won by each player.

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

    def nextScores(self) -> Optional[tuple["TiebreakerScore", "TiebreakerScore"]]:
        """
        Calculates two scores, the outcome of either player winning
        the next point from the current score. This is possible only
        if the tiebreaker is not already over.

        Returns:
        --------
        A tuple of two TiebreakerScore instances, the first representing the
        score if Player1 wins the next point, the second representing the
        score if Player2 wins the next point.
        If the tiebreaker is already over, returns None.
        """
        if self.isFinal:
            return None

        return TiebreakerScore(self._currPointsP1+1, self._currPointsP2,   self._isSuper, self._normalize), \
               TiebreakerScore(self._currPointsP1,   self._currPointsP2+1, self._isSuper, self._normalize)

    @property
    def pointsToWin(self) -> int:
        """Returns the number of points needed to win based on tiebreaker type."""
        return self.POINTS_TO_WIN_SUPER_TIEBREAKER if self._isSuper else self.POINTS_TO_WIN_TIEBREAKER

    def _playerWon(self, player: Literal[1, 2]) -> bool:
        """
        Tests whether a given player won the tiebreaker, considering the current score.
        """
        P1_won = (self._currPointsP1 >= self.pointsToWin) and (self._currPointsP1 - self._currPointsP2 > 1)
        P2_won = (self._currPointsP2 >= self.pointsToWin) and (self._currPointsP2 - self._currPointsP1 > 1)

        return P1_won if player == 1 else P2_won

    def _normalize_score(self):
        """
        Normalizing the score means representing all deuces as 6-6 (9-9 if super),
        and all adds as 6-7 or 7-6 (or 9-10, 10-9). Without normalization, if there
        are multiple deuces, the score grows unbounded, which can be problematic for
        some applications.
        """
        if self.isDeuce:
            self._currPointsP1 = self._currPointsP2 = self.pointsToWin - 1
        elif self.playerWithAdvantage == 1:
            self._currPointsP1 = self.pointsToWin
            self._currPointsP2 = self.pointsToWin - 1
        elif self.playerWithAdvantage == 2:
            self._currPointsP1 = self.pointsToWin - 1
            self._currPointsP2 = self.pointsToWin

    @staticmethod
    def _isValidScore(score: tuple[int, int], isSuper: bool) -> bool:
        """
        Checks that a given tiebreaker score is valid.

        Parameters:
        -----------
        score   - tiebreaker score, as points won by each player
        isSuper - True if this is a super-tiebreaker

        Returns:
        --------
        True if the score is valid, else False.
        """
        pointsToWin = TiebreakerScore.POINTS_TO_WIN_SUPER_TIEBREAKER if isSuper else TiebreakerScore.POINTS_TO_WIN_TIEBREAKER
        p1, p2 = score
        if not isinstance(p1, int) or not isinstance(p2, int):
            return False
        if p1 < 0 or p2 < 0:
            return False
        if p1 <= pointsToWin and p2 <= pointsToWin:
            return True
        else:
            return abs(p1 - p2) <= 2

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TiebreakerScore):
            return NotImplemented
        return (self._currPointsP1 == other._currPointsP1) and \
               (self._currPointsP2 == other._currPointsP2) and \
               (self._isSuper == other._isSuper)

    def __repr__(self) -> str:
        """
        Valid Python expression that can be used to recreate this TiebreakerScore instance.
        """
        return f"TiebreakerScore(pointsP1={self._currPointsP1}, pointsP2={self._currPointsP2}, isSuper={self._isSuper}, normalize={self._normalize})"

    def __str__(self) -> str:
        """
        Returns the score in "X-Y" format from Player 1's perspective.
        """
        return f"{self._currPointsP1}-{self._currPointsP2}"

    def __hash__(self) -> int:
        return hash((self._currPointsP1, self._currPointsP2, self._isSuper))
