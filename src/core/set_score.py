"""SetScore class representing the score in a tennis set."""

from typing import Literal, Optional

from src.core.game_score     import GameScore
from src.core.tiebreak_score import TiebreakScore

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
    __init__(gamesP1: int, gamesP2: int, 
             gameScore: Optional[GameScore]=None,
             tiebreakScore: Optional[TiebreakScore]=None, 
             noAdRule: bool=False, normalize: bool=False, setLength: int=6, tiebreakSet: bool=True)
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
                 gamesP1      : int = 0,
                 gamesP2      : int = 0,
                 gameScore    : Optional[GameScore] = None,
                 tiebreakScore: Optional[TiebreakScore] = None,
                 noAdRule     : bool = False,
                 normalize    : bool = False,
                 setLength    : int = 6,
                 tiebreakSet  : bool = True):
        """
        Initialize the score to an arbitrary (but valid) initial value.

        Parameters:
        -----------
        gamesP1       - initial number of games won by Player1 (default 0)
        gamesP2       - initial number of games won by Player2 (default 0)
        gameScore     - current game initial score; if None, initialized to 0-0
        tiebreakScore - current tiebreak initial score; if None, initialized to 0-0
        noAdRule      - if True, games are played under the no-ad rule (default: False)
        normalize     - if True, cap point scores (default: False)
        setLength     - number of games needed to win the set (default: 6)
        tiebreakSet   - if True, a tiebreak is played at 6-6 (default: True);
                        if False, games continue until one player wins by 2

        Raises:
        -------
        ValueError - if any of the inputs are invalid
        """
        if not isinstance(gamesP1, int) or not isinstance(gamesP2, int):
            raise ValueError(f"Invalid games: gamesP1={gamesP1}, gamesP2={gamesP2}. Must be integers.")
        if gameScore is not None and not isinstance(gameScore, GameScore):
            raise ValueError(f"Invalid gameScore: must be None or a GameScore instance.")
        if gameScore is not None and gameScore.isFinal:
            raise ValueError(f"Invalid gameScore: cannot be a final score (should be part of gamesP1/gamesP2).")
        if tiebreakScore is not None and not isinstance(tiebreakScore, TiebreakScore):
            raise ValueError(f"Invalid tiebreakScore: must be None or a TiebreakScore instance.")
        if tiebreakScore is not None and tiebreakScore.isFinal:
            raise ValueError(f"Invalid tiebreakScore: cannot be a final score (should be part of gamesP1/gamesP2).")
        if not isinstance(noAdRule, bool):
            raise ValueError(f"Invalid noAdRule: {noAdRule}. Must be a boolean.")
        if not isinstance(normalize, bool):
            raise ValueError(f"Invalid normalize: {normalize}. Must be a boolean.")
        if not isinstance(setLength, int) or setLength < 1:
            raise ValueError(f"Invalid setLength: {setLength}. Must be a positive integer.")
        if not isinstance(tiebreakSet, bool):
            raise ValueError(f"Invalid tiebreakSet: {tiebreakSet}. Must be a boolean.")
        if not tiebreakSet and tiebreakScore is not None:
            raise ValueError("tiebreakScore must be None when tiebreakSet is False.")
        if gameScore is not None and gameScore._noAdRule != noAdRule:
            raise ValueError(f"gameScore.noAdRule ({gameScore._noAdRule}) must match noAdRule ({noAdRule}).")
        if gameScore is not None and gameScore._normalize != normalize:
            raise ValueError(f"gameScore.normalize ({gameScore._normalize}) must match normalize ({normalize}).")
        if tiebreakScore is not None and tiebreakScore._normalize != normalize:
            raise ValueError(f"tiebreakScore.normalize ({tiebreakScore._normalize}) must match normalize ({normalize}).")
        if not SetScore._isValidScore(gamesP1, gamesP2, gameScore, tiebreakScore, setLength, tiebreakSet):
            raise ValueError(f"Invalid initial score: {gamesP1}-{gamesP2}")

        self._noAdRule   : bool = noAdRule      # whether to use the 'no-ad' rule for games
        self._normalize  : bool = normalize     # auto-normalize point scores (cap them)
        self._setLength  : int  = setLength     # number of games needed to win
        self._tiebreakSet: bool = tiebreakSet   # whether to play a tiebreak if the set is tied
        
        # keep track of score
        self.gamesP1      : int                     = gamesP1   # games won by Player1
        self.gamesP2      : int                     = gamesP2   # games won by Player2
        self.currGameScore: Optional[GameScore]     = None      # score of current game
        self.tiebreakScore: Optional[TiebreakScore] = None      # score of current tiebreak

        # if the next point is part of a regular game, initialize the score for that game
        if self.nextPointIsGame:
            self.currGameScore = gameScore if gameScore else GameScore(0, 0, noAdRule=noAdRule, normalize=normalize)

        # if the next point is part of a regular tiebreak, initialize the score for that tiebreak
        if self.nextPointIsTiebreak:
            self.tiebreakScore = tiebreakScore if tiebreakScore else TiebreakScore(0, 0, isSuper=False, normalize=normalize)

    @property
    def isBlank(self) -> bool:
        """
        Whether the score is 'blank',  i.e. no point has been completed so far.
        """
        return (self.gamesP1 == self.gamesP2 == 0) and \
               (self.currGameScore is None or self.currGameScore.isBlank) and \
               (self.tiebreakScore is None or self.tiebreakScore.isBlank)

    @property
    def isTied(self) -> bool:
        """
        Returns whether the set is tied (e.g., 6-6 for standard sets).
        """
        return self.gamesP1 == self.gamesP2 == self._setLength

    @property
    def isFinal(self) -> bool:
        """
        Returns whether this is a final score (set decided).
        """
        return self._playerWon(1) or self._playerWon(2)

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
        return (not self.isTied or not self._tiebreakSet) and not self.isFinal

    @property
    def nextPointIsTiebreak(self) -> bool:
        """
        Returns whether the next point is part of a tiebreak.
        """
        return (self.isTied and self._tiebreakSet) and not self.isFinal

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
        return (self.gamesP1, self.gamesP2) if pov == 1 else (self.gamesP2, self.gamesP1)

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
        
        return SetScore(self.gamesP1+1, self.gamesP2,   noAdRule=self._noAdRule, normalize=self._normalize, setLength=self._setLength, tiebreakSet=self._tiebreakSet), \
               SetScore(self.gamesP1,   self.gamesP2+1, noAdRule=self._noAdRule, normalize=self._normalize, setLength=self._setLength, tiebreakSet=self._tiebreakSet)

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
        self.gamesP1 += (1 if gameWinner == 1 else 0)
        self.gamesP2 += (1 if gameWinner == 2 else 0)

        if self.nextPointIsGame:
            self.currGameScore = GameScore(0, 0, noAdRule=self._noAdRule, normalize=self._normalize)
        else:
            self.currGameScore = None

        if self.nextPointIsTiebreak:
            self.tiebreakScore = TiebreakScore(0, 0, isSuper=False, normalize=self._normalize)
        else:
            self.tiebreakScore = None

    def _recordTiebreak(self, tiebreakWinner: Literal[1, 2]):
        """
        Update the score with the result of the tiebreak.
        """
        self.gamesP1 += (1 if tiebreakWinner == 1 else 0)
        self.gamesP2 += (1 if tiebreakWinner == 2 else 0)

        # the set is over once the tiebreak completes
        self.currGameScore = None
        self.tiebreakScore = None

    def _playerWon(self, player: Literal[1, 2]) -> bool:
        """
        Tests whether a given player won the set, considering the current score.
        """
        playerGames   = self.gamesP1 if player == 1 else self.gamesP2
        opponentGames = self.gamesP2 if player == 1 else self.gamesP1
        n = self._setLength

        # if the set can be decided by tiebreak, there are two ways to win:
        # win by two or win by tiebreak.
        if self._tiebreakSet:
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
        return (self.gamesP1       == other.gamesP1)       and \
               (self.gamesP2       == other.gamesP2)       and \
               (self.currGameScore == other.currGameScore) and \
               (self.tiebreakScore == other.tiebreakScore)

    def __repr__(self) -> str:
        """
        Valid Python expression that can be used to recreate this SetScore instance.
        """
        return f"SetScore(gamesP1={self.gamesP1}, gamesP2={self.gamesP2}, " + \
               f"gameScore={repr(self.currGameScore)}, tiebreakScore={repr(self.tiebreakScore)}, " + \
               f"noAdRule={self._noAdRule}, normalize={self._normalize}, setLength={self._setLength}, " + \
               f"tiebreakSet={self._tiebreakSet})"

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
        return hash((self.gamesP1, self.gamesP2, self.currGameScore, self.tiebreakScore))

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
