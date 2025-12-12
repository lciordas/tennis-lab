"""Tests for the Game class."""

import pytest
from tennis_lab.core.game         import Game
from tennis_lab.core.game_score   import GameScore
from tennis_lab.core.match_format import MatchFormat, SetEnding

# Default match format for most tests
DEFAULT_FORMAT = MatchFormat(bestOfSets=3)
NO_AD_FORMAT   = MatchFormat(bestOfSets=3, noAdRule=True)


class TestGameInit:
    """Tests for Game initialization."""

    def test_init_default_score(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        assert game.server == 1
        assert game.score.asPoints(1) == (0, 0)
        assert game.pointHistory == []
        assert not game.isOver
        assert game.winner is None

    def test_init_player2_serves(self):
        game = Game(playerServing=2, matchFormat=DEFAULT_FORMAT)
        assert game.server == 2

    def test_init_with_custom_score(self):
        init_score = GameScore(2, 1, DEFAULT_FORMAT)
        game = Game(playerServing=1, initScore=init_score)
        assert game.score.asPoints(1) == (2, 1)

    def test_init_invalid_server(self):
        with pytest.raises(ValueError):
            Game(playerServing=0, matchFormat=DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            Game(playerServing=3, matchFormat=DEFAULT_FORMAT)

    def test_init_invalid_score_type(self):
        with pytest.raises(ValueError):
            Game(playerServing=1, initScore="invalid", matchFormat=DEFAULT_FORMAT)

    def test_init_default_matchFormat(self):
        # When both initScore and matchFormat are None, a default MatchFormat is used
        game = Game(playerServing=1)
        assert game.server == 1
        assert game.score.asPoints(1) == (0, 0)
        assert not game.isOver
        # Verify it uses standard scoring (not no-ad)
        game.recordPoints([1, 1, 1, 2, 2, 2])  # Get to deuce
        assert game.score.isDeuce
        game.recordPoint(1)  # Advantage
        assert not game.isOver  # Should need 2 points to win from deuce

    def test_init_mismatched_matchFormat(self):
        init_score = GameScore(2, 1, DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            Game(playerServing=1, initScore=init_score, matchFormat=NO_AD_FORMAT)

    def test_init_deep_copies_score(self):
        init_score = GameScore(1, 0, DEFAULT_FORMAT)
        game = Game(playerServing=1, initScore=init_score)
        game.recordPoint(1)
        # Original should be unchanged
        assert init_score.asPoints(1) == (1, 0)
        assert game.score.asPoints(1) == (2, 0)

    def test_init_with_no_ad_rule(self):
        init_score = GameScore(3, 3, NO_AD_FORMAT)
        game = Game(playerServing=1, initScore=init_score)
        game.recordPoint(1)
        assert game.isOver
        assert game.winner == 1


class TestGameRecordPoint:
    """Tests for recordPoint method."""

    def test_record_single_point(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        game.recordPoint(1)
        assert game.score.asPoints(1) == (1, 0)
        assert game.pointHistory == [1]

    def test_record_multiple_points(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        game.recordPoint(1)
        game.recordPoint(2)
        game.recordPoint(1)
        assert game.score.asPoints(1) == (2, 1)
        assert game.pointHistory == [1, 2, 1]

    def test_record_point_invalid(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            game.recordPoint(0)
        with pytest.raises(ValueError):
            game.recordPoint(3)

    def test_record_point_after_game_over(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        # P1 wins 4-0
        for _ in range(4):
            game.recordPoint(1)
        assert game.isOver
        initial_history = game.pointHistory.copy()

        # Additional points should be ignored
        game.recordPoint(2)
        assert game.pointHistory == initial_history
        assert game.score.asPoints(1) == (4, 0)


class TestGameRecordPoints:
    """Tests for recordPoints method."""

    def test_record_points_basic(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        game.recordPoints([1, 2, 1, 2])
        assert game.score.asPoints(1) == (2, 2)
        assert game.pointHistory == [1, 2, 1, 2]

    def test_record_points_to_win(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        game.recordPoints([1, 1, 1, 1])
        assert game.isOver
        assert game.winner == 1

    def test_record_points_stops_at_game_over(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        # Try to record 6 points, but game ends at 4
        game.recordPoints([1, 1, 1, 1, 1, 1])
        assert game.pointHistory == [1, 1, 1, 1]
        assert game.score.asPoints(1) == (4, 0)


class TestGameProperties:
    """Tests for Game properties."""

    def test_is_over_not_over(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        assert not game.isOver
        game.recordPoint(1)
        assert not game.isOver

    def test_is_over_standard_win(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        game.recordPoints([1, 1, 1, 1])
        assert game.isOver

    def test_is_over_deuce_win(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        # 40-40, then ad-40, then win
        game.recordPoints([1, 1, 1, 2, 2, 2, 1, 1])
        assert game.isOver
        assert game.winner == 1

    def test_winner_none_when_not_over(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        assert game.winner is None
        game.recordPoints([1, 1, 1])
        assert game.winner is None

    def test_winner_player1(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        game.recordPoints([1, 1, 1, 1])
        assert game.winner == 1

    def test_winner_player2(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        game.recordPoints([2, 2, 2, 2])
        assert game.winner == 2


class TestGameScoreHistory:
    """Tests for scoreHistory property."""

    def test_score_history_initial(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        history = game.scoreHistory
        assert "P1 serves" in history
        assert "0-0" in history

    def test_score_history_after_points(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        game.recordPoint(1)
        history = game.scoreHistory
        assert "15-0" in history

    def test_score_history_server_score_first(self):
        game = Game(playerServing=2, matchFormat=DEFAULT_FORMAT)
        game.recordPoint(1)  # P1 wins point, but P2 serves
        history = game.scoreHistory
        # Server (P2) score should be first, so 0-15
        assert "0-15" in history

    def test_score_history_complete_game(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        game.recordPoints([1, 1, 1, 1])
        history = game.scoreHistory
        assert "P1 wins game" in history

    def test_score_history_no_trailing_comma(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        game.recordPoint(1)
        history = game.scoreHistory
        assert not history.endswith(", ")
        assert not history.endswith(",")


class TestGameRepr:
    """Tests for __repr__ method."""

    def test_repr_contains_game(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        assert "Game" in repr(game)

    def test_repr_contains_server(self):
        game = Game(playerServing=2, matchFormat=DEFAULT_FORMAT)
        assert "playerServing=2" in repr(game)

    def test_repr_contains_score(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        game.recordPoints([1, 2])
        repr_str = repr(game)
        assert "initScore=" in repr_str
        assert "GameScore" in repr_str

    def test_repr_eval(self):
        # repr should produce valid Python
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        game.recordPoints([1, 2])
        recreated = eval(repr(game))
        assert recreated.score.asPoints(1) == game.score.asPoints(1)


class TestGameStr:
    """Tests for __str__ method."""

    def test_str_not_over(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        assert "Player1 to serve at 0-0" == str(game)

    def test_str_not_over_with_score(self):
        game = Game(playerServing=2, matchFormat=DEFAULT_FORMAT)
        game.recordPoints([1, 2])
        assert "Player2 to serve at 15-15" == str(game)

    def test_str_game_over(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        game.recordPoints([1, 1, 1, 1])
        assert "Player1 wins game" in str(game)

    def test_str_player2_wins(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        game.recordPoints([2, 2, 2, 2])
        assert "Player2 wins game" in str(game)


class TestGameDeuceScenarios:
    """Tests for deuce and advantage scenarios."""

    def test_deuce_then_player1_wins(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        # Get to deuce
        game.recordPoints([1, 1, 1, 2, 2, 2])
        assert game.score.isDeuce

        # P1 gets advantage then wins
        game.recordPoints([1, 1])
        assert game.isOver
        assert game.winner == 1

    def test_deuce_back_and_forth(self):
        game = Game(playerServing=1, matchFormat=DEFAULT_FORMAT)
        # Get to deuce
        game.recordPoints([1, 1, 1, 2, 2, 2])

        # Ad P1, back to deuce
        game.recordPoint(1)
        assert game.score.playerWithAdvantage == 1
        game.recordPoint(2)
        assert game.score.isDeuce

        # Ad P2, back to deuce
        game.recordPoint(2)
        assert game.score.playerWithAdvantage == 2
        game.recordPoint(1)
        assert game.score.isDeuce

        # P2 wins
        game.recordPoints([2, 2])
        assert game.isOver
        assert game.winner == 2


class TestGameNoAdRule:
    """Tests for no-ad rule games."""

    def test_no_ad_win_at_deuce(self):
        init_score = GameScore(3, 3, NO_AD_FORMAT)
        game = Game(playerServing=1, initScore=init_score)

        game.recordPoint(1)
        assert game.isOver
        assert game.winner == 1

    def test_no_ad_player2_wins(self):
        init_score = GameScore(3, 3, NO_AD_FORMAT)
        game = Game(playerServing=1, initScore=init_score)

        game.recordPoint(2)
        assert game.isOver
        assert game.winner == 2

    def test_no_ad_standard_win(self):
        game = Game(playerServing=1, matchFormat=NO_AD_FORMAT)

        game.recordPoints([1, 1, 1, 1])
        assert game.isOver
        assert game.winner == 1
        assert game.score.asPoints(1) == (4, 0)


class TestGameWithInitialScore:
    """Tests for games starting at non-zero scores."""

    def test_start_at_30_15(self):
        init_score = GameScore(2, 1, DEFAULT_FORMAT)
        game = Game(playerServing=1, initScore=init_score)

        assert game.score.asPoints(1) == (2, 1)
        assert game.pointHistory == []

        game.recordPoints([1, 1])
        assert game.isOver
        assert game.winner == 1
        assert game.pointHistory == [1, 1]

    def test_start_at_advantage(self):
        init_score = GameScore(4, 3, DEFAULT_FORMAT)
        game = Game(playerServing=1, initScore=init_score)

        game.recordPoint(1)
        assert game.isOver
        assert game.winner == 1
        assert game.pointHistory == [1]

    def test_start_at_game_point(self):
        init_score = GameScore(3, 0, DEFAULT_FORMAT)
        game = Game(playerServing=2, initScore=init_score)

        # P1 wins next point
        game.recordPoint(1)
        assert game.isOver
        assert game.winner == 1
