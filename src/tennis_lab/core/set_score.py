"""SetScore class representing the score in a tennis set."""

from copy import deepcopy
from typing import Literal, Optional

from tennis_lab.core.game_score     import GameScore
from tennis_lab.core.match_format   import MatchFormat, SetEnding
from tennis_lab.core.tiebreak_score import TiebreakScore

class SetScore:
    """
    Represents the running score of a tennis set.

    Attributes:
    -----------
    gamesP1: int
        Number of games won by Player 1.
    gamesP2: int
        Number of games won by Player 2.
    currGameScore: Optional[GameScore]
        The score of the current game (None if playing no more games).
    tiebreakScore: Optional[TiebreakScore]
        The score of the tiebreak, if one in progress, else None.
    isBlank: bool
        Whether the score is 'blank',  i.e. no point has been completed so far.
    isTied: bool
        Whether the set is tied (e.g., 6-6 for standard sets).
    isFinal: bool
        Whether this is a final score (set decided).
    endsInTiebreak: bool
        Whether this set ends in a tiebreak when tied.
    winner: Optional[Literal[1, 2]]
        Returns which player won the set, None if not yet decided.
    nextPointIsGame: bool
        Whether the next point is part of a regular game.
    nextPointIsTiebreak: bool
        Whether the next point is part of a tiebreak.
    gameInProgress: bool
        Whether there is a game in progress (False if a game is next but has not started).
    tiebreakInProgress: bool
        Whether there is a tiebreak in progress (False if tiebreak is next but has not started).

    Methods:
    --------
    __init__(gamesP1: int, gamesP2: int, isFinalSet: bool, matchFormat: Optional[MatchFormat]=None,
             gameScore: Optional[GameScore]=None, tiebreakScore: Optional[TiebreakScore]=None)
        Initialize the score to an arbitrary (but valid) initial value.
    games(pov: Literal[1,2]) -> tuple[int, int]
        The number of games completed by each player.
    recordPoint(pointWinner: Literal[1, 2])
        Update the score with the result of the next point.
    nextGameScores() -> Optional[tuple["SetScore", "SetScore"]]
        Calculates two scores, the outcome of either player winning the next game.        
    __eq__(other: "SetScore") -> bool
        Implemented the equality operation.
    __repr__() -> str
        Valid Python expression that can be used to recreate this SetScore instance.
    __str__() -> str
        Returns the score in "X-Y" format from Player 1's perspective.
    """

    def __init__(self,
                 gamesP1      : int,
                 gamesP2      : int,
                 isFinalSet   : bool,
                 matchFormat  : Optional[MatchFormat]   = None,
                 gameScore    : Optional[GameScore]     = None,
                 tiebreakScore: Optional[TiebreakScore] = None):
        """
        Initialize the score to an arbitrary (but valid) initial value.

        Parameters:
        -----------
        gamesP1       - initial number of games won by Player1
        gamesP2       - initial number of games won by Player2
        isFinalSet    - whether this is the final set of the match
        matchFormat   - describes the match format (can be derived from gameScore or tiebreakScore if not provided)
        gameScore     - current game initial score (only if initially in the middle of a game)
        tiebreakScore - current tiebreak initial score (only if initially in the middle of a tiebreak)

        Raises:
        -------
        ValueError - if any of the inputs are invalid or if matchFormats are inconsistent
        """
        if not isinstance(gamesP1, int) or not isinstance(gamesP2, int):
            raise ValueError(f"Invalid games: gamesP1={gamesP1}, gamesP2={gamesP2}. Must be integers.")
        if not isinstance(isFinalSet, bool):
            raise ValueError(f"Invalid isFinalSet: {isFinalSet}. Must be a boolean.")
        if matchFormat is not None and not isinstance(matchFormat, MatchFormat):
            raise ValueError(f"Invalid matchFormat: must be None or a MatchFormat instance.")
        if gameScore is not None and not isinstance(gameScore, GameScore):
            raise ValueError(f"Invalid gameScore: must be None or a GameScore instance.")
        if gameScore is not None and gameScore.isFinal:
            raise ValueError(f"Invalid gameScore: cannot be a final score (should be part of gamesP1/gamesP2).")
        if tiebreakScore is not None and not isinstance(tiebreakScore, TiebreakScore):
            raise ValueError(f"Invalid tiebreakScore: must be None or a TiebreakScore instance.")
        if tiebreakScore is not None and tiebreakScore.isFinal:
            raise ValueError(f"Invalid tiebreakScore: cannot be a final score (should be part of gamesP1/gamesP2).")

        # Derive matchFormat from gameScore or tiebreakScore if not provided directly
        if matchFormat is None:
            if gameScore is not None:
                matchFormat = gameScore._matchFormat
            elif tiebreakScore is not None:
                matchFormat = tiebreakScore._matchFormat
            else:
                matchFormat = MatchFormat()

        # Validate that all provided matchFormats are consistent
        if gameScore is not None and gameScore._matchFormat != matchFormat:
            raise ValueError("gameScore.matchFormat must match matchFormat.")
        if tiebreakScore is not None and tiebreakScore._matchFormat != matchFormat:
            raise ValueError("tiebreakScore.matchFormat must match matchFormat.")

        self._matchFormat: MatchFormat = matchFormat
        self._isFinalSet : bool        = isFinalSet

        if not self.endsInTiebreak and tiebreakScore is not None:
            raise ValueError("tiebreakScore must be None when set ending is not tiebreak.")
        if not SetScore._isValidScore(gamesP1, gamesP2, gameScore, tiebreakScore, matchFormat.setLength, self.endsInTiebreak):
            raise ValueError(f"Invalid initial score: {gamesP1}-{gamesP2}")

        # keep track of score
        self._gamesP1     : int                     = gamesP1   # games won by Player1
        self._gamesP2     : int                     = gamesP2   # games won by Player2
        self.currGameScore: Optional[GameScore]     = None      # score of current game
        self.tiebreakScore: Optional[TiebreakScore] = None      # score of current tiebreak

        # if the next point is part of a regular game, initialize the score for that game
        if self.nextPointIsGame:
            self.currGameScore = deepcopy(gameScore) if gameScore else GameScore(0, 0, matchFormat)

        # if the next point is part of a regular tiebreak, initialize the score for that tiebreak
        if self.nextPointIsTiebreak:
            if tiebreakScore:
                self.tiebreakScore = deepcopy(tiebreakScore)
            else:
                ending  = self._matchFormat.finalSetEnding if self._isFinalSet else self._matchFormat.setEnding
                isSuper = ending == SetEnding.SUPERTIEBREAK
                self.tiebreakScore = TiebreakScore(0, 0, isSuper=isSuper, matchFormat=matchFormat)

    @property
    def gamesPlayer1(self) -> int:
        """Number of games won by Player 1."""
        return self._gamesP1

    @property
    def gamesPlayer2(self) -> int:
        """Number of games won by Player 2."""
        return self._gamesP2

    @property
    def isBlank(self) -> bool:
        """
        Whether the score is 'blank',  i.e. no point has been completed so far.
        """
        return (self.gamesPlayer1 == self.gamesPlayer2 == 0) and \
               (self.currGameScore is None or self.currGameScore.isBlank) and \
               (self.tiebreakScore is None or self.tiebreakScore.isBlank)

    @property
    def isTied(self) -> bool:
        """
        Returns whether the set is tied (e.g., 6-6 for standard sets).
        """
        return self.gamesPlayer1 == self.gamesPlayer2 == self._matchFormat.setLength

    @property
    def isFinal(self) -> bool:
        """
        Returns whether this is a final score (set decided).
        """
        return self._playerWon(1) or self._playerWon(2)

    @property
    def endsInTiebreak(self) -> bool:
        """
        Returns whether this set ends in a tiebreak when tied.
        """
        ending = self._matchFormat.finalSetEnding if self._isFinalSet else self._matchFormat.setEnding
        return ending != SetEnding.ADVANTAGE

    @property
    def winner(self) -> Optional[Literal[1, 2]]:
        """
        Returns which player won the set, None if not yet decided.
        """
        if self._playerWon(1):
            return 1
        if self._playerWon(2):
            return 2
        return None

    @property
    def nextPointIsGame(self) -> bool:
        """
        Returns whether the next point is part of a regular game.
        """
        return (not self.isTied or not self.endsInTiebreak) and not self.isFinal

    @property
    def nextPointIsTiebreak(self) -> bool:
        """
        Returns whether the next point is part of a tiebreak.
        """
        return (self.isTied and self.endsInTiebreak) and not self.isFinal

    @property
    def gameInProgress(self) -> bool:
        """
        Predicate that returns whether there is a game in progress.
        Returns 'True' only if 'in the middle' of a game. For example,
        it return 'False' if the next point is the first point of a
        new game (so we are currently in between games).
        """
        return self.nextPointIsGame and not self.currGameScore.isBlank

    @property
    def tiebreakInProgress(self) -> bool:
        """
        Predicate that returns whether there is a tiebreak in progress.
        Returns 'False' if the tiebreak has not started, even if the
        next point is part of the tiebreak.
        """
        return self.nextPointIsTiebreak and not self.tiebreakScore.isBlank

    def games(self, pov: Literal[1, 2]) -> tuple[int, int]:
        """
        The number of games completed by each player from a given point of view.

        We must specify the point of view (1 or 2) from which to display the score.
        For example, if we display the score from the point of view of Player1, the
        first element of the tuple will be the score of Player1, and the 2nd element
        will be the score of Player2.

        Parameter:
        ----------
        pov - point of view from which to display the score (1, 2)

        Returns:
        --------
        The current number of completed games, as a tuple of two integers.

        Raises:
        -------
        ValueError - if pov is not 1 or 2
        """
        if pov not in (1, 2):
            raise ValueError(f"Invalid pov: {pov}. Must be 1 or 2.")
        return (self.gamesPlayer1, self.gamesPlayer2) if pov == 1 else (self.gamesPlayer2, self.gamesPlayer1)

    def nextGameScores(self) -> Optional[tuple["SetScore", "SetScore"]]:
        """
        Calculates two scores, the outcome of either player winning the next game.
        This is possible only if the set is not already over.
        Example: 3-3 => (4-3, 3-4)

        Note that the 'granularity' here is 'game' not 'point', therefore this 
        method can only be called if there is no game or tiebreaker in progress,
        so if a whole number of games has been completed.

        Returns:
        --------
        A tuple of two SetScore instances.
        If the set is already over, returns None.

        Raises:
        -------
        ValueError - if a game or tiebreak is in progress
        """
        if self.gameInProgress:
            raise ValueError("Cannot call nextGameScores() while a game is in progress.")
        if self.tiebreakInProgress:
            raise ValueError("Cannot call nextGameScores() while a tiebreak is in progress.")

        if self.isFinal:
            return None

        return SetScore(self.gamesPlayer1+1, self.gamesPlayer2,   self._isFinalSet, self._matchFormat), \
               SetScore(self.gamesPlayer1,   self.gamesPlayer2+1, self._isFinalSet, self._matchFormat)

    def recordPoint(self, pointWinner: Literal[1, 2]):
        """
        Update the score with the result of the next point.

        Parameters:
        -----------
        pointWinner - which player won the point (1 or 2)

        Raises:
        -------
        ValueError - if pointWinner is not 1 or 2, or if the set is already over
        RuntimeError - if set is in an invalid state (not exactly one of game/tiebreak in progress)
        """
        if pointWinner not in (1, 2):
            raise ValueError(f"Invalid pointWinner: {pointWinner}. Must be 1 or 2.")
        if self.isFinal:
            raise ValueError("Cannot record point: set is already over.")

        # error check - the point must have been part of a either game or a tiebreak.
        playingGame     = self.currGameScore is not None
        playingTiebreak = self.tiebreakScore is not None
        if playingGame and playingTiebreak:
            raise RuntimeError("Invalid state: either playing a game or a tiebreak.")

        if playingGame:
            self.currGameScore.recordPoint(pointWinner)
            if self.currGameScore.isFinal:
                self._recordGame(self.currGameScore.winner)
        else:
            self.tiebreakScore.recordPoint(pointWinner)
            if self.tiebreakScore.isFinal:
                self._recordTiebreak(self.tiebreakScore.winner)

    def _recordGame(self, gameWinner: Literal[1, 2]):
        """
        Update the score with the result of the current game.
        """
        self._gamesP1 += (1 if gameWinner == 1 else 0)
        self._gamesP2 += (1 if gameWinner == 2 else 0)

        if self.nextPointIsGame:
            self.currGameScore = GameScore(0, 0, self._matchFormat)
        else:
            self.currGameScore = None

        if self.nextPointIsTiebreak:
            ending  = self._matchFormat.finalSetEnding if self._isFinalSet else self._matchFormat.setEnding
            isSuper = ending == SetEnding.SUPERTIEBREAK
            self.tiebreakScore = TiebreakScore(0, 0, isSuper=isSuper, matchFormat=self._matchFormat)
        else:
            self.tiebreakScore = None

    def _recordTiebreak(self, tiebreakWinner: Literal[1, 2]):
        """
        Update the score with the result of the tiebreak.
        """
        self._gamesP1 += (1 if tiebreakWinner == 1 else 0)
        self._gamesP2 += (1 if tiebreakWinner == 2 else 0)

        # the set is over once the tiebreak completes
        self.currGameScore = None
        self.tiebreakScore = None

    def _playerWon(self, player: Literal[1, 2]) -> bool:
        """
        Tests whether a given player won the set, considering the current score.
        """
        playerGames   = self.gamesPlayer1 if player == 1 else self.gamesPlayer2
        opponentGames = self.gamesPlayer2 if player == 1 else self.gamesPlayer1
        n = self._matchFormat.setLength

        # if the set can be decided by tiebreak, there are two ways to win:
        # win by two or win by tiebreak.
        if self.endsInTiebreak:
            wonByTwo    = (playerGames >= n)   and (opponentGames <= playerGames-2)
            wonTiebreak = (playerGames == n+1) and (opponentGames == n)
            return wonTiebreak or wonByTwo

        # the only way to win is by two (there is no tiebreak).
        else:
            wonByTwo = (playerGames >= n) and (opponentGames <= playerGames-2)
            return wonByTwo

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SetScore):
            return NotImplemented
        return (self.gamesPlayer1       == other.gamesPlayer1)       and \
               (self.gamesPlayer2       == other.gamesPlayer2)       and \
               (self.currGameScore == other.currGameScore) and \
               (self.tiebreakScore == other.tiebreakScore)

    def __repr__(self) -> str:
        """
        Valid Python expression that can be used to recreate this SetScore instance.
        """
        return f"SetScore(gamesP1={self.gamesPlayer1}, gamesP2={self.gamesPlayer2}, " + \
               f"isFinalSet={self._isFinalSet}, matchFormat={repr(self._matchFormat)}, " + \
               f"gameScore={repr(self.currGameScore)}, tiebreakScore={repr(self.tiebreakScore)})"

    def __str__(self) -> str:
        """
        Returns the score in "X-Y" format from Player 1's perspective.
        """
        gamesFirst, gamesSecond = self.games(pov=1)
        s = f"{gamesFirst}-{gamesSecond}"
        if self.currGameScore is not None:
            s += f", {self.currGameScore.asTraditional(pov=1)}"
        if self.tiebreakScore is not None:
            pFirst, pSecond = self.tiebreakScore.asPoints(pov=1)
            s += f", {pFirst}-{pSecond}"
        return s

    def __hash__(self) -> int:
        return hash((self.gamesPlayer1, self.gamesPlayer2, self.currGameScore, self.tiebreakScore))

    @staticmethod
    def _isValidScore(initGamesP1      : int,
                      initGamesP2      : int,
                      initGameScore    : Optional[GameScore],
                      initTiebreakScore: Optional[TiebreakScore],
                      setLength        : int = 6,
                      tiebreakSet      : bool = True) -> bool:
        """
        Checks that a given set score is valid.

        Parameters:
        -----------
        initGamesP1       - initial number of games won by Player1
        initGamesP2       - initial number of games won by Player2
        initGameScore     - initial current game score
        initTiebreakScore - initial current tiebreak score
        setLength         - number of games needed to win the set (default: 6)
        tiebreakSet       - whether a tiebreak is played at n-n (default: True)

        Returns:
        --------
        True if the score is valid, else False.
        """
        n = setLength
        if not isinstance(initGamesP1, int) or not isinstance(initGamesP2, int):
            return False
        if initGameScore is not None and not isinstance(initGameScore, GameScore):
            return False
        if initTiebreakScore is not None and not isinstance(initTiebreakScore, TiebreakScore):
            return False

        # Tiebreak set: games capped at n+1
        if tiebreakSet:
            if initGamesP1 < 0 or initGamesP1 > n + 1:
                return False
            if initGamesP2 < 0 or initGamesP2 > n + 1:
                return False
            if initGamesP1 == n + 1 and initGamesP2 < n - 1:
                return False
            if initGamesP2 == n + 1 and initGamesP1 < n - 1:
                return False

            p1WonSet = (initGamesP1 == n and initGamesP2 <= n - 2) or \
                       (initGamesP1 == n + 1 and initGamesP2 in (n - 1, n))
            p2WonSet = (initGamesP2 == n and initGamesP1 <= n - 2) or \
                       (initGamesP2 == n + 1 and initGamesP1 in (n - 1, n))

        # No tiebreak: games can go beyond n, need 2-game lead to win        
        else:
            if initGamesP1 < 0 or initGamesP2 < 0:
                return False

            p1WonSet = initGamesP1 >= n and (initGamesP1 - initGamesP2) >= 2
            p2WonSet = initGamesP2 >= n and (initGamesP2 - initGamesP1) >= 2

        isOver = p1WonSet or p2WonSet
        isTied = (initGamesP1 == initGamesP2 == n)

        # cannot be playing either another game or a tiebreak if the set is over
        if isOver and (initGameScore is not None or initTiebreakScore is not None):
            return False

        # cannot be playing a regular game when the set is tied (tiebreak set only)
        if tiebreakSet and isTied and initGameScore is not None:
            return False

        # cannot be playing a tiebreak unless the set is tied and it's a tiebreak set
        if initTiebreakScore is not None and (not isTied or not tiebreakSet):
            return False

        return True
