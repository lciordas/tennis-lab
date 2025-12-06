"""GameScore class representing the score in a tennis game."""

from typing import Literal, Optional


class GameScore:
    """
    Represents the running score of a tennis game.

    Attributes & Properties:
    -------------------------
    isBlank: bool
        Whether the current score is 0-0.
    isDeuce: bool
        Whether the current score is 'deuce'.
    playerWithAdvantage: Optional[Literal[1, 2]]
        Returns which player has 'advantage', None if n/a.
    winner: Optional[Literal[1, 2]]
        Returns which player won the game, None if game is not over.

    Methods:
    --------
    __init__(pointsP1: int, pointsP2: int)
        Initialize the score to an arbitrary (but valid) initial value.
    isOver(noAdRule: bool) -> bool:
        Returns whether the game is over.
    playerWon(player: Literal[1, 2], noAdRule: bool) -> bool:
        Returns whether a given player won the game given the current score.
    normalize():
        Represent all deuces as 3-3 and all adds as 3-4 or 4-3.
    updateOnPointOver(pointWinner: Literal[1, 2])
        Update the score with the result of the next point.
    asPoints(pov: Literal[1,2]) -> tuple[int, int]
        Get the current score, as a tuple of two integers.
    asTraditional(pov: Literal[1,2]) -> str
        Get the current score, expressed in the traditional tennis convention of 0, 15, 30, 40.
    nextScores(noAddRule: bool) -> Optional[tuple["GameScore", "GameScore"]]
        Calculates two scores, the outcome of either player winning the next point.
    __eq__(other: "GameScore") -> bool
        Implemented the equality operation.
    __repr__() -> str
        Valid Python expression that can be used to recreate this GameScore instance.
    __str__() -> str
        Returns the traditional score format for display.
    """

    def __init__(self, pointsP1: int, pointsP2: int):
        """
        Initialize the score to an arbitrary (but valid) initial value.
        The score is represented as two integers, the number of points won by each
        player, and not by the more traditional tennis convention of 0, 15, 30, 40.
        Example: the score 30-15 is represented as 2,1.

        Parameters:
        -----------
        pointsP1 - initial number of points for Player1
        pointsP2 - initial number of points for Player2

        Raises:
        -------
        ValueError - if the score is not valid
        """
        if not GameScore._isValidScore((pointsP1, pointsP2)):
            raise ValueError(f"Invalid initial score: {(pointsP1, pointsP2)}")

        # keep track of the current score
        self._currPointsP1: int = pointsP1
        self._currPointsP2: int = pointsP2

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
        """
        return (self._currPointsP1 == self._currPointsP2) and (self._currPointsP1 >= 3)

    def isOver(self, noAdRule: bool) -> bool:
        """
        Returns whether the game is over.
        """
        return self.playerWon(1, noAdRule) or self.playerWon(2, noAdRule)

    @property
    def playerWithAdvantage(self) -> Optional[Literal[1, 2]]:
        """
        Returns which player has 'advantage', None if n/a.
        """
        if (self._currPointsP1 - self._currPointsP2 == 1) and (self._currPointsP1 >= 4):
            return 1
        if (self._currPointsP2 - self._currPointsP1 == 1) and (self._currPointsP2 >= 4):
            return 2
        return None

    @property
    def winner(self) -> Optional[Literal[1, 2]]:
        """
        Returns which player won the game, None if game is not over.
        Uses standard advantage rules (not no-ad).
        """
        if self.playerWon(1, noAdRule=False):
            return 1
        if self.playerWon(2, noAdRule=False):
            return 2
        return None

    def playerWon(self, player: Literal[1, 2], noAdRule: bool) -> bool:
        """
        Returns whether a given player won the game, considering the current score.

        Parameters:
        -----------
        player   - the player for whom we are carrying out the test
        noAdRule - if True, the game is played under the no-ad rule

        Returns:
        --------
        Whether the given player won the game given the current score.

        Raises:
        -------
        ValueError - if player is not 1 or 2
        """
        if player not in (1, 2):
            raise ValueError(f"Invalid player: {player}. Must be 1 or 2.")

        if noAdRule:
            P1_won = (self._currPointsP1 == 4)
            P2_won = (self._currPointsP2 == 4)
        else:
            P1_won = (self._currPointsP1 >= 4) and (self._currPointsP1 - self._currPointsP2 > 1)
            P2_won = (self._currPointsP2 >= 4) and (self._currPointsP2 - self._currPointsP1 > 1)

        return P1_won if player == 1 else P2_won

    def normalize(self):
        """
        Normalizing the score means representing all deuces as 3-3,
        and all adds as 3-4 or 4-3. Without normalization, if there
        are multiple deuces, the score grows unbounded, which can be
        problematic for some applications.
        """
        if self.isDeuce:
            self._currPointsP1 = self._currPointsP2 = 3
        elif self.playerWithAdvantage == 1:
            self._currPointsP1 = 4
            self._currPointsP2 = 3
        elif self.playerWithAdvantage == 2:
            self._currPointsP1 = 3
            self._currPointsP2 = 4

    def updateOnPointOver(self, pointWinner: Literal[1, 2]):
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

    def nextScores(self, noAdRule: bool) -> Optional[tuple["GameScore", "GameScore"]]:
        """
        Calculates two scores, the outcome of either player winning
        the next point from the current score. This is possible only
        if the game is not already over.

        Parameters:
        -----------
        noAddRule - if True, the game is played under the no-ad rule

        Returns:
        --------
        A tuple of two GameScore instances, the first representing the
        score if Player1 wins the next point, the second representing
        the score if Player2 wins the next point.
        If the game is already over, returns None.
        """

        game_over = self.playerWon(1, noAdRule) or self.playerWon(2, noAdRule)
        if game_over:
            return None

        return GameScore(self._currPointsP1+1, self._currPointsP2), \
               GameScore(self._currPointsP1, self._currPointsP2+1)

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
        if p1 <= 3 and p2 <= 3:
            return True

        # game over before reaching deuce
        if (p1 == 4 and p2 <= 2) or (p2 == 4 and p1 <= 2):
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
        if pFirst <= 3 and pSecond <= 3:
            return f"{score_map[pFirst]}-{score_map[pSecond]}"
        elif pFirst < 3 and pSecond == 4:
            return f"{score_map[pFirst]}-win"
        elif pSecond < 3 and pFirst == 4:
            return f"win-{score_map[pSecond]}"
        elif pFirst >= 3 and pSecond >= 3:
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
        return (self._currPointsP1 == other._currPointsP1) and \
               (self._currPointsP2 == other._currPointsP2)

    def __repr__(self) -> str:
        """
        Valid Python expression that can be used to recreate this GameScore instance.
        """
        return f"GameScore(pointsP1={self._currPointsP1}, pointsP2={self._currPointsP2})"

    def __str__(self) -> str:
        """
        Returns the traditional score format for display (from Player 1's perspective).
        """
        return self.asTraditional(pov=1)

    def __hash__(self) -> int:
        return hash((self._currPointsP1, self._currPointsP2))
