"""Set class representing a set in a tennis match."""

from copy   import deepcopy
from typing import List, Literal, Optional

from tennis_lab.core.game         import Game
from tennis_lab.core.match_format import MatchFormat
from tennis_lab.core.set_score    import SetScore
from tennis_lab.core.tiebreak     import Tiebreak

class Set:
    """
    Represents a set in a tennis match.
    
    The set need not start at 0-0; any valid initial score may be specified.
    Its state is updated incrementally, one point at a time. Based on these
    updates, the Set instance updates the current score, keeping track of games,
    potential tiebreaker, and the set itself. The current score, as well as the
    score history, can be queried at any time.

    Attributes:
    -----------
    score: SetScore
        The current score of the set.
    servesNext: Literal[1, 2]
        Which player serves the next point.
    isOver: bool
        Whether the set is over
    isTied: bool
        Whether the set is tied at 6-6.
    winner: Optional[Literal[1,2]]
        Which player won the set (1 or 2, but 'None' if the set is not over)
    currentGame: Optional[Game]
        The game in progress (if any).
    tiebreaker: Optional[Tiebreak]
        The tiebreaker in progress (if any).
    totalPoints: tuple[int, int]
        Current total # points won in this set by each player.
    gameHistory: list[Game|Tiebreak]
        The games that have been completed so far (including the tiebreaker) in this set.
    pointHistory: list[Literal[1,2]]
        Which player won each point ex: [1, 1, 2, ...]

    Methods:
    --------
    recordPoint(pointWinner: Literal[1, 2])
        Updates the set state with the result of the next point.
    recordPoints(self, pointWinners: List[Literal[1, 2]])
        Update the game state with the result of multiple points.
    scoreHistory() -> str
        Formatted string representation of the set score history.
    __str__() -> str
        Formatted string representation of the current set state.
    __repr__() -> str
        Valid Python expression that can be used to recreate this Set instance.
    """

    def __init__(self,
                 playerToServe : Literal[1, 2],
                 isFinalSet    : bool,
                 initScore     : Optional[SetScore]    = None,
                 matchFormat   : Optional[MatchFormat] = None,
                _shareInitScore: bool                  = False):
        """
        Initialize a set - any valid initial score may be specified.

        Parameters:
        -----------
        playerToServe  - which player serves next in the set (1 or 2)
        isFinalSet     - whether this is the final set of the match
        initScore      - initial set score; if None, the score is initialized to 0-0
        matchFormat    - describes the match format; required if 'initScore' is None
       _shareInitScore - whether to share the initScore object (use default value unless
                         you know what you are doing)

        Raises:
        -------
        ValueError - if any of the inputs are invalid or mismatched
        """
        if playerToServe not in (1, 2):
            raise ValueError(f"Invalid playerToServe: {playerToServe}. Must be 1 or 2.")
        if not isinstance(isFinalSet, bool):
            raise ValueError(f"Invalid isFinalSet: {isFinalSet}. Must be a boolean.")
        if initScore is not None and not isinstance(initScore, SetScore):
            raise ValueError(f"Invalid initScore: must be None or a SetScore instance.")
        if matchFormat is not None and not isinstance(matchFormat, MatchFormat):
            raise ValueError(f"Invalid matchFormat: must be None or a MatchFormat instance.")
        if initScore is None and matchFormat is None:
            raise ValueError("matchFormat is required when initScore is None.")
        if initScore is not None and initScore._isFinalSet != isFinalSet:
            raise ValueError(f"initScore.isFinalSet ({initScore._isFinalSet}) must match isFinalSet ({isFinalSet}).")
        if initScore is not None and matchFormat is not None:
            if initScore._matchFormat != matchFormat:
                raise ValueError("initScore.matchFormat must match matchFormat.")

        self._isFinalSet : bool        = isFinalSet
        self._matchFormat: MatchFormat = matchFormat if matchFormat else initScore._matchFormat

        # figure out the starting score
        if initScore: scoreStart = initScore if _shareInitScore else deepcopy(initScore)
        else:         scoreStart = SetScore(0, 0, isFinalSet, matchFormat)

        self.score     : SetScore = scoreStart            # keeps track of the current score
        self._initScore: SetScore = deepcopy(initScore)   # remember the initial score

        # object that represents the game being played next (if any)
        # Note the '_shareInitScore=True' argument.
        self.currentGame: Optional[Game] = None
        if self.score.nextPointIsGame:
            self.currentGame = Game(playerToServe, self.score.currGameScore, self._matchFormat, _shareInitScore=True)

        # object that represents the tiebreak being played next (if any)
        # Note the '_shareInitScore=True' argument.
        self.tiebreaker: Optional[Tiebreak] = None
        if self.score.nextPointIsTiebreak:
            self.tiebreaker = Tiebreak(playerToServe, self.score.tiebreakScore._isSuper,
                                       self.score.tiebreakScore, self._matchFormat, _shareInitScore=True)

        self.gameHistory: List[Game|Tiebreak] = []   # completed Game/Tiebreak instances

    @property
    def servesNext(self) -> Literal[1, 2]:
        """Which player serves the next point."""

        # if the next point is part of a game, query the Game object
        if self.score.nextPointIsGame:
            return self.currentGame.server

        # if the next point is part of a tiebreak, query the Tiebreak object
        elif self.score.nextPointIsTiebreak:
            return self.tiebreaker.servesNext

        # it must be that the set is over, it ended either with a game or a tiebreaker.
        # query that object for who served and flip it to the other player.
        else:
            server = None
            item   = self.gameHistory[-1]
            if isinstance(item, Game):     server = 3 - item.server
            if isinstance(item, Tiebreak): server = 3 - item._servedFirst
            return server

    @property
    def isOver(self) -> bool:
        """Predicate which indicates whether the set is over."""
        return self.score.isFinal

    @property
    def isTied(self) -> bool:
        """Predicate which indicates whether the set is tied at 6-6."""
        return self.score.isTied

    @property
    def winner(self) -> Optional[Literal[1, 2]]:
        """Which player won the set (1 or 2), or None if the set is not over."""
        return self.score.winner

    @property
    def pointHistory(self) -> list[Literal[1, 2]]:
        """
        Which player won each point ex: [1, 1, 2, ...]
        """
        points = [item.pointHistory for item in self.gameHistory]
        if self.currentGame is not None:
            points.append(self.currentGame.pointHistory)
        if self.tiebreaker is not None:
            points.append(self.tiebreaker.pointHistory)
        return sum(points, [])  # sum of lists is a list

    @property
    def totalPoints(self) -> tuple[int, int]:
        """
        Current total # points won in this set by each player.
        """
        scores = [items.score.asPoints(pov=1) for items in self.gameHistory]

        total1 = sum([s[0] for s in scores])
        if self.currentGame is not None:
            total1 += self.currentGame.score.asPoints(pov=1)[0]
        if self.tiebreaker is not None:
            total1 += self.tiebreaker.score.asPoints(pov=1)[0]

        total2 = sum([s[1] for s in scores])
        if self.currentGame is not None:
            total2 += self.currentGame.score.asPoints(pov=2)[0]
        if self.tiebreaker is not None:
            total2 += self.tiebreaker.score.asPoints(pov=2)[0]

        return total1, total2

    def recordPoint(self, pointWinner: Literal[1, 2]):
        """
        Updates the set state with the result of the next point.
        pointWinner - which player won the point (1 or 2)
        """
        if pointWinner not in (1, 2):
            raise ValueError(f"Invalid pointWinner: {pointWinner}. Must be 1 or 2.")
        if self.isOver:
            return

        # check that either a regular game or a tiebreaker
        # is in progress, but not both at the same time
        if not ((self.currentGame is not None) ^ (self.tiebreaker is not None)):
            raise RuntimeError("Invalid state: exactly one of 'currentGame' or 'tiebreaker' attributes must be set.")

        # notify the appropriate sub-object to do its own point recording
        # NOTE: the 'score: SetScore' attribute of this Set instance *shares* the GameScore/TiebreakScore
        #       attribute of the Game or Tiebreak sub-object, so it does not need to be updates explicitly.
        if self.currentGame is not None:
            self.currentGame.recordPoint(pointWinner)
            gameOver = self.currentGame.isOver
        else:
            self.tiebreaker.recordPoint(pointWinner)
            gameOver = self.tiebreaker.isOver

        # handle game/tiebreak completion 
        if gameOver:
            if self.currentGame is not None:
                self._onGameOver()
            else:
                self._onTiebreakOver()

    def recordPoints(self, pointWinners: list[Literal[1, 2]]):
        """
        Update the set state with the result of multiple points.
        pointWinners - which player won each point (1 or 2)
        """
        for pointWinner in pointWinners:
            self.recordPoint(pointWinner)

    def scoreHistory(self) -> str:
        """
        Formatted string representation of the set score history.
        """
        MARGIN = 3 * ' '
        s = ""
        games1, games2 = self._initScore.games(pov=1) if self._initScore else (0, 0)

        # add the details of each *game* in the set;
        # if there is a tiebreaker at the end, skip it for now
        for item in self.gameHistory:
            if isinstance(item, Tiebreak):
                continue
            game = item

            if game.winner == 1: games1 += 1
            else:                games2 += 1

            s += MARGIN + f"Game {games1 + games2}: "
            s += game.scoreHistory.replace("\n", "\n" + MARGIN)
            s += f", score {games1}-{games2} for P1\n\n"

        # if the set ended in a tiebreaker, add its score history
        if len(self.gameHistory) > 0 and isinstance(self.gameHistory[-1], Tiebreak):
            tiebreaker = self.gameHistory[-1]
            s += MARGIN + "Tiebreak: "
            s += tiebreaker.scoreHistory.replace("\n", "\n" + MARGIN) + "\n\n"

        # if we are in the middle of playing a game add its details
        # (an incomplete game is not yet part of 'self.gamesHistory')
        if self.currentGame is not None:
            s += MARGIN + f"Game {games1 + games2}: "
            s += self.currentGame.scoreHistory.replace("\n", "\n" + MARGIN)

        # if we are in the middle of playing a tiebreaker add its details
        # (an incomplete tiebreaker is not yet part of 'self.gamesHistory')
        if self.tiebreaker is not None:
            s += MARGIN + "Tiebreak: "
            s += self.tiebreaker.scoreHistory.replace("\n", "\n" + MARGIN) + "\n\n"

        if self.isOver:
            s += f"P{self.winner} wins set"
        return s

    def _onGameOver(self):
        """
        Updates the set state when a game completes.
        """
        # archive the completed game and determine next server
        self.gameHistory.append(self.currentGame)
        servingNext = 3 - self.currentGame.server

        # update the set score at the game/tiebreaker granularity level
        # NOTE: at the point level, it has been updated via the shared GameScore object
        self.score._recordGame(self.currentGame.winner)

        # update Set-specific state based on what SetScore decided
        if self.score.isFinal:
            self.currentGame = None
            self.tiebreaker  = None

        elif self.score.nextPointIsTiebreak:
            self.tiebreaker  = Tiebreak(servingNext, self.score.tiebreakScore._isSuper,
                                        self.score.tiebreakScore, self._matchFormat,
                                       _shareInitScore=True)
            self.currentGame = None

        else:
            self.currentGame = Game(servingNext, self.score.currGameScore,
                                    self._matchFormat, _shareInitScore=True)
            self.tiebreaker  = None

    def _onTiebreakOver(self):
        """
        Updates the set state when a tiebreak completes.
        """
        # archive the completed tiebreak
        self.gameHistory.append(self.tiebreaker)

        # update the set score at the game/tiebreaker granularity level
        # NOTE: at the point level, it has been updated via the shared TiebreakScore object
        self.score._recordTiebreak(self.tiebreaker.winner)

        # the set is over after a tiebreak
        self.tiebreaker = None

    def __str__(self) -> str:
        """
        Formatted string representation of the current set state.
        """
        if self.isOver:
            pov = self.winner
            s = f"Player{self.winner} wins set: "
        else:
            pov = self.servesNext
            s = f"Player{pov} to serve at "

        # get the game score
        gamesFirst, gamesSecond = self.score.games(pov)
        s += f"{gamesFirst}-{gamesSecond}"

        # we need to also include a point score if
        #  + the set is not over
        #  + the set is over, and it ended in a tiebreaker
        if self.currentGame is not None:
            pointScoreStr = self.currentGame.score.asTraditional(pov)
            s += ", " + pointScoreStr
        if self.tiebreaker is not None:
            pointScore = self.tiebreaker.score.asPoints(pov)
            s += f", {pointScore[0]}-{pointScore[1]}"
        if self.isOver and (gamesFirst == 7 or gamesSecond == 7):
            tiebreaker = self.gameHistory[-1]
            pointScore = tiebreaker.score.asPoints(pov)
            s += f" ({pointScore[0]}-{pointScore[1]})"

        return s

    def __repr__(self) -> str:
        """
        Valid Python expression that can be used to recreate this Set instance.
        """
        return f"Set(playerToServe={self.servesNext}, isFinalSet={self._isFinalSet}, " \
               f"matchFormat={repr(self._matchFormat)}, initScore={repr(self.score)})"
