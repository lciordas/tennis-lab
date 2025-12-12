"""Game class representing a tennis game."""

from copy                  import deepcopy
from typing                import List, Literal, Optional
from tennis_lab.core.game_score   import GameScore
from tennis_lab.core.match_format import MatchFormat

class Game:
    """
    Represents a game in a tennis match.

    The game need not start at 0-0; any valid initial score may be specified via
    the 'initScore' parameter. Scoring rules (standard or 'no-ad') are determined by
    the 'matchFormat' parameter or, if 'initScore' is provided, by its match format.
    If neither is provided, a default MatchFormat is used.

    Attributes:
    -----------
    server: Literal[1,2]
        Which player serves this game
    score: GameScore
        The current score of the game
    isOver: bool
        Whether the game is over
    winner: Optional[Literal[1,2]]
        Which player won the game (1 or 2, but 'None' if the game is not over)
    scoreHistory: str
        Formatted string representation of the game score history.
    matchFormat: MatchFormat
        The match format for this game.
    pointHistory: list[Literal[1,2]]
        Which player won each point (following the initial score); ex: [1, 1, 2, 1, 1]

    Methods:
    --------
    __init__(playerServing, initScore=None, matchFormat=None)
        Initialize a game - any valid initial score may be specified.
    recordPoint(pointWinner)
        Updates the game state with the result of the next point.
    recordPoints(pointWinners)
        Update the game state with the result of multiple points.
    __str__() -> str
        Formatted string representation of the current game state.
    __repr__() -> str
        Valid Python expression that can be used to recreate this Game instance.
    """

    def __init__(self,
                 playerServing : Literal[1, 2],
                 initScore     : Optional[GameScore]   = None,
                 matchFormat   : Optional[MatchFormat] = None,
                _shareInitScore: bool = False):
        """
        Initialize a game - any valid initial score may be specified.

        Parameters:
        -----------
        playerServing  - which player serves this game (1 or 2)
        initScore      - initial game score; if None, the score is initialized to 0-0
        matchFormat    - describes the match format (if not provided the match format from 'initScore' is used, if available)
       _shareInitScore - whether to share the initScore object (use default value unless
                         you know what you are doing)

        Raises:
        -------
        ValueError - if inputs are invalid or inconsistent
        """
        if playerServing not in (1, 2):
            raise ValueError(f"Invalid playerServing: {playerServing}. Must be 1 or 2.")
        if initScore is not None and not isinstance(initScore, GameScore):
            raise ValueError(f"Invalid initScore: must be None or a GameScore instance.")
        if matchFormat is not None and not isinstance(matchFormat, MatchFormat):
            raise ValueError(f"Invalid matchFormat: must be None or a MatchFormat instance.")
        if initScore is not None and matchFormat is not None:
            if initScore._matchFormat != matchFormat:
                raise ValueError("initScore.matchFormat must match matchFormat.")

        # figure out the starting score
        if initScore: scoreStart = initScore if _shareInitScore else deepcopy(initScore)
        else:         scoreStart = GameScore(0, 0, matchFormat)

        self.score       : GameScore              = scoreStart        # keeps track of the current score
        self.pointHistory: List[Literal[1,2]]     = []                # which player won each point following 'initScore'
        self.server      : Literal[1,2]           = playerServing     # which player serves this game

        # string representation of the score history
        self._scoreHistory: str = (f"P{playerServing} serves\nP{playerServing} "
                                   f"score: {self.score.asTraditional(self.server)}, ")

    @property
    def isOver(self) -> bool:
        """Whether the game is over."""
        return self.score.isFinal

    @property
    def winner(self) -> Optional[Literal[1, 2]]:
        """Which player won the game (1 or 2), or None if the game is not over."""
        return self.score.winner

    @property
    def scoreHistory(self) -> str:
        """Formatted string representation of the game score history, server score is displayed first."""
        return self._scoreHistory[:-2]

    @property
    def matchFormat(self) -> MatchFormat:
        """The match format for this game."""
        return self.score._matchFormat

    def recordPoint(self, pointWinner: Literal[1, 2]):
        """
        Update the game state with the result of the next point.

        Parameters:
        -----------
        pointWinner - which player won the point (1 or 2)
        """
        if pointWinner not in (1, 2):
            raise ValueError(f"Invalid pointWinner: {pointWinner}. Must be 1 or 2.")
        if self.isOver:
            return

        # update the current score and the point history
        self.score.recordPoint(pointWinner)
        self.pointHistory.append(pointWinner)

        # incrementally built the string representation of the score history
        self._scoreHistory += self.score.asTraditional(self.server) + ", "
        if self.isOver:
            self._scoreHistory  = self._scoreHistory[:-2] + "\n"
            self._scoreHistory += f"P{self.winner} wins game  "

    def recordPoints(self, pointWinners: list[Literal[1, 2]]):
        """
        Update the game state with the result of multiple points.
        pointWinners - which player won each point (1 or 2)
        """
        for pointWinner in pointWinners:
            self.recordPoint(pointWinner)

    def __repr__(self) -> str:
        """
        String representation for debugging.
        Note: eval(repr(game)) recreates the game at its current score, but not the full point history.
        """
        return f"Game(playerServing={self.server}, initScore={repr(self.score)})"

    def __str__(self) -> str:
        """
        Formatted string representation of the current game state.
        """
        if not self.isOver:
            return f"Player{self.server} to serve at {self.score.asTraditional(self.server)}"
        else:
            return f"Player{self.winner} wins game: {self.score.asTraditional(self.server)}"
