"""MatchScore class representing the score in a tennis match."""

from copy import deepcopy
from typing import Literal, Optional

from src.core.match_format import MatchFormat
from src.core.set_score    import SetScore

class MatchScore:
    """
    Represents the running score of a tennis match.

    Attributes:
    -----------
    setsPlayer1: int
        Number of sets won by Player 1.
    setsPlayer2: int
        Number of sets won by Player 2.
    currSetScore: Optional[SetScore]
        The score of the set currently in progress (None if match is over).
    isBlank: bool
        Whether the score is 'blank',  i.e. no point has been completed so far.
    isFinal: bool
        Whether the match is over.
    winner: Optional[Literal[1, 2]]
        Returns which player won the match, None if not yet decided.
    setInProgress: bool
        Whether there is a set in progress (False if we are in between sets).

    Methods:
    --------
    __init__(setsP1: int, setsP2: int, matchFormat: MatchFormat,
             setScore: Optional[SetScore]=None)
        Initialize the score to an arbitrary (but valid) initial value.
    sets(pov: Literal[1,2]) -> tuple[int, int]
        The number of sets completed by each player.
    recordPoint(pointWinner: Literal[1, 2])
        Update the score with the result of the next point.
    nextSetScores() -> Optional[tuple["MatchScore", "MatchScore"]]
        Calculates two scores, the outcome of either player winning the next set.
    __eq__(other: "MatchScore") -> bool
        Implemented the equality operation.
    __repr__() -> str
        Valid Python expression that can be used to recreate this MatchScore instance.
    __str__() -> str
        Returns a string representation of the current score.
    """

    def __init__(self,
                 setsP1     : int,
                 setsP2     : int,
                 matchFormat: MatchFormat,
                 setScore   : Optional[SetScore] = None):
        """
        Initialize the score to an arbitrary (but valid) initial value.

        Parameters:
        -----------
        setsP1      - initial number of sets won by Player1
        setsP2      - initial number of sets won by Player2
        matchFormat - describes the match format
        setScore    - initial current set score (only if initially in the middle of a set)

        Raises:
        -------
        ValueError - if any of the inputs are invalid
        """
        # validate inputs
        if not isinstance(setsP1, int) or not isinstance(setsP2, int):
            raise ValueError(f"Invalid sets: setsP1={setsP1}, setsP2={setsP2}. Must be integers.")
        if not isinstance(matchFormat, MatchFormat):
            raise ValueError(f"Invalid matchFormat: must be a MatchFormat instance.")
        if setScore is not None and not isinstance(setScore, SetScore):
            raise ValueError(f"Invalid setScore: must be None or a SetScore instance.")
        if setScore is not None and setScore.isFinal:
            raise ValueError(f"Invalid setScore: cannot be a final score (should be part of setsP1/setsP2).")
        if setScore is not None and setScore._matchFormat != matchFormat:
            raise ValueError("setScore.matchFormat must match matchFormat.")
        if not MatchScore._isValidScore(setsP1, setsP2, setScore, matchFormat):
            raise ValueError(f"Invalid initial score: {setsP1}-{setsP2}")

        self._matchFormat: MatchFormat = matchFormat

        # keep track of score
        self._setsP1     : int                = setsP1    # sets won by Player1
        self._setsP2     : int                = setsP2    # sets won by Player2
        self.currSetScore: Optional[SetScore] = None      # score of the current set
        if not self.isFinal:
            self.currSetScore = deepcopy(setScore) if setScore else SetScore(0, 0, self._isFinalSet(), matchFormat)

    @property
    def setsPlayer1(self) -> int:
        """Number of sets won by Player 1."""
        return self._setsP1

    @property
    def setsPlayer2(self) -> int:
        """Number of sets won by Player 2."""
        return self._setsP2

    @property
    def isBlank(self) -> bool:
        """
        Returns whether the current score is 0-0.
        """
        return (self._setsP1 == 0 and self._setsP2 == 0) and \
               (self.currSetScore is None or self.currSetScore.isBlank)

    @property
    def isFinal(self) -> bool:
        """
        Returns whether the match is over.
        """
        return self._playerWon(1) or self._playerWon(2)

    @property
    def winner(self) -> Optional[Literal[1, 2]]:
        """
        Returns which player won the match, None if not yet decided.
        """
        if self._playerWon(1):
            return 1
        if self._playerWon(2):
            return 2
        return None

    @property
    def setInProgress(self) -> bool:
        """
        Predicate that returns whether there is a set in progress.
        Returns 'True' only if 'in the middle' of a set. For example,
        it returns 'False' if the next point is the first point of a
        *new* set (so we are currently in between sets).
        
        """
        if self.currSetScore is None:
            return False
        return not self.currSetScore.isBlank

    def sets(self, pov: Literal[1, 2]) -> tuple[int, int]:
        """
        The number of sets completed by each player.

        We must specify the point of view (1 or 2) from which to display the score.
        For example, if we display the score from the point of view of Player1, the
        first element of the tuple will be the score of Player1, and the 2nd element
        will be the score of Player2.

        Parameter:
        ----------
        pov - point of view from which to display the score (1, 2)

        Returns:
        --------
        The current number of completed sets, as a tuple of two integers.

        Raises:
        -------
        ValueError - if pov is not 1 or 2
        """
        if pov not in (1, 2):
            raise ValueError(f"Invalid pov: {pov}. Must be 1 or 2.")
        return (self._setsP1, self._setsP2) if pov == 1 else (self._setsP2, self._setsP1)

    def nextSetScores(self) -> Optional[tuple["MatchScore", "MatchScore"]]:
        """
        Calculates two scores, the outcome of either player winning the next set.
        This is possible only if the match is not already over.
        Example: 1-1 => (2-1, 1-2)

        Note that the 'granularity' is sets, not games or points, therefore this 
        method can only be called if there is no game or tiebreaker in progress,
        so if a whole number of sets has been completed.

        Returns:
        --------
        A tuple of two MatchScore instances.
        If the match is already over, returns None.

        Raises:
        -------
        ValueError - if a set is in progress
        """
        if self.setInProgress:
            raise ValueError("Cannot call nextSetScores() while a set is in progress.")
        if self.isFinal:
            return None
        return MatchScore(self._setsP1 + 1, self._setsP2,     self._matchFormat), \
               MatchScore(self._setsP1,     self._setsP2 + 1, self._matchFormat)

    def recordPoint(self, pointWinner: Literal[1, 2]):
        """
        Update the score with the result of the next point.

        Parameters:
        -----------
        pointWinner - which player won the point (1 or 2)

        Raises:
        -------
        ValueError - if pointWinner is not 1 or 2, or if the match is already over
        """
        if pointWinner not in (1, 2):
            raise ValueError(f"Invalid pointWinner: {pointWinner}. Must be 1 or 2.")
        if self.isFinal:
            raise ValueError("Cannot record point: match is already over.")

        self.currSetScore.recordPoint(pointWinner)

        if self.currSetScore.isFinal:
            setWinner = self.currSetScore.winner
            self._setsP1 += (1 if setWinner == 1 else 0)
            self._setsP2 += (1 if setWinner == 2 else 0)
            self.currSetScore = None if self.isFinal else \
                SetScore(0, 0, self._isFinalSet(), self._matchFormat)

    def _playerWon(self, player: Literal[1, 2]) -> bool:
        """
        Tests whether a given player won the match.
        """
        playerSets = self._setsP1 if player == 1 else self._setsP2
        setsToWin  = self._matchFormat.bestOfSets // 2 + 1
        return playerSets == setsToWin

    def _isFinalSet(self) -> bool:
        """
        Returns whether the current/next set would be a final set.
        A final set is when one more set win would decide the match for either player.
        """
        setsToWin = self._matchFormat.bestOfSets // 2 + 1
        return self._setsP1 == setsToWin - 1 or self._setsP2 == setsToWin - 1

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MatchScore):
            return NotImplemented
        return (self._setsP1      == other._setsP1)      and \
               (self._setsP2      == other._setsP2)      and \
               (self.currSetScore == other.currSetScore) and \
               (self._matchFormat == other._matchFormat)

    def __repr__(self) -> str:
        """
        Valid Python expression that can be used to recreate this MatchScore instance.
        """
        return f"MatchScore(setsP1={self._setsP1}, setsP2={self._setsP2}, " + \
               f"matchFormat={repr(self._matchFormat)}, setScore={repr(self.currSetScore)})"

    def __str__(self) -> str:
        """
        Returns a string representation of the current score from Player 1's perspective.
        """
        setsFirst, setsSecond = self.sets(pov=1)
        s = f"{setsFirst}-{setsSecond}"
        if self.currSetScore is not None:
            s += f", {self.currSetScore}"
        return s

    def __hash__(self) -> int:
        return hash((self._setsP1, self._setsP2, self.currSetScore, self._matchFormat))

    @staticmethod
    def _isValidScore(initSetsP1  : int,
                      initSetsP2  : int,
                      initSetScore: Optional[SetScore],
                      matchFormat : MatchFormat) -> bool:
        """
        Check if the given score is valid.

        Parameters:
        -----------
        initSetsP1   - initial number of sets won by Player1
        initSetsP2   - initial number of sets won by Player2
        initSetScore - initial current set score
        matchFormat  - describes the match format

        Returns:
        --------
        True if the score is valid, False otherwise.
        """
        setsToWin = matchFormat.bestOfSets // 2 + 1

        if initSetsP1 < 0 or initSetsP1 > setsToWin:
            return False
        if initSetsP2 < 0 or initSetsP2 > setsToWin:
            return False

        p1WonMatch = (initSetsP1 == setsToWin)
        p2WonMatch = (initSetsP2 == setsToWin)
        isFinal = p1WonMatch or p2WonMatch

        # cannot be playing another set if the match is over
        if isFinal and initSetScore is not None:
            return False

        return True
