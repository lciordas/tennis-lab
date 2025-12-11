"""Tests for the Set class."""

import pytest
from tennis_lab.core.set           import Set
from tennis_lab.core.set_score     import SetScore
from tennis_lab.core.game_score    import GameScore
from tennis_lab.core.tiebreak_score import TiebreakScore
from tennis_lab.core.match_format  import MatchFormat, SetEnding

# Default match format for most tests
DEFAULT_FORMAT = MatchFormat(bestOfSets=3)
NO_AD_FORMAT   = MatchFormat(bestOfSets=3, noAdRule=True)


# Helper function: points needed to win a game (server wins all points)
def win_game(s: Set, player: int):
    """Record 4 points for the given player to win a game."""
    s.recordPoints([player] * 4)


# Helper function: points to get to 6-6 (tiebreak)
def get_to_tiebreak(s: Set):
    """Play games until the set reaches 6-6."""
    # P1 wins games 1, 3, 5, 7, 9, 11 (when serving)
    # P2 wins games 2, 4, 6, 8, 10, 12 (when serving)
    for game_num in range(12):
        if game_num % 2 == 0:
            win_game(s, 1)
        else:
            win_game(s, 2)
    assert s.score.games(1) == (6, 6)


class TestSetInit:
    """Tests for Set initialization."""

    def test_init_default_score(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        assert s.servesNext == 1
        assert s.score.games(1) == (0, 0)
        assert s.gameHistory == []
        assert not s.isOver
        assert s.winner is None
        assert s.currentGame is not None
        assert s.tiebreaker is None

    def test_init_player2_serves(self):
        s = Set(playerServing=2, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        assert s.servesNext == 2

    def test_init_final_set(self):
        s = Set(playerServing=1, isFinalSet=True, matchFormat=DEFAULT_FORMAT)
        assert s._isFinalSet is True

    def test_init_non_final_set(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        assert s._isFinalSet is False

    def test_init_with_custom_score(self):
        init_score = SetScore(3, 2, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        s = Set(playerServing=1, isFinalSet=False, initScore=init_score)
        assert s.score.games(1) == (3, 2)

    def test_init_invalid_server(self):
        with pytest.raises(ValueError):
            Set(playerServing=0, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            Set(playerServing=3, isFinalSet=False, matchFormat=DEFAULT_FORMAT)

    def test_init_invalid_isFinalSet_type(self):
        with pytest.raises(ValueError):
            Set(playerServing=1, isFinalSet="yes", matchFormat=DEFAULT_FORMAT)

    def test_init_invalid_score_type(self):
        with pytest.raises(ValueError):
            Set(playerServing=1, isFinalSet=False, initScore="invalid", matchFormat=DEFAULT_FORMAT)

    def test_init_missing_matchFormat(self):
        with pytest.raises(ValueError):
            Set(playerServing=1, isFinalSet=False)

    def test_init_mismatched_isFinalSet(self):
        init_score = SetScore(3, 2, isFinalSet=True, matchFormat=DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            Set(playerServing=1, isFinalSet=False, initScore=init_score)

    def test_init_mismatched_matchFormat(self):
        init_score = SetScore(3, 2, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            Set(playerServing=1, isFinalSet=False, initScore=init_score, matchFormat=NO_AD_FORMAT)

    def test_init_deep_copies_score(self):
        init_score = SetScore(1, 0, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        s = Set(playerServing=1, isFinalSet=False, initScore=init_score)
        win_game(s, 1)  # Make P1 win another game
        # Original should be unchanged
        assert init_score.games(1) == (1, 0)
        assert s.score.games(1) == (2, 0)


class TestSetRecordPoint:
    """Tests for recordPoint method."""

    def test_record_single_point(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        s.recordPoint(1)
        assert s.currentGame.score.asPoints(1) == (1, 0)
        assert s.pointHistory == [1]

    def test_record_multiple_points(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        s.recordPoints([1, 2, 1])
        assert s.currentGame.score.asPoints(1) == (2, 1)
        assert s.pointHistory == [1, 2, 1]

    def test_record_point_invalid(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            s.recordPoint(0)
        with pytest.raises(ValueError):
            s.recordPoint(3)

    def test_record_point_after_set_over(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        # P1 wins 6-0
        for _ in range(6):
            win_game(s, 1)
        assert s.isOver
        initial_history = s.pointHistory.copy()

        # Additional points should be ignored
        s.recordPoint(2)
        assert s.pointHistory == initial_history


class TestSetRecordPoints:
    """Tests for recordPoints method."""

    def test_record_points_basic(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        s.recordPoints([1, 2, 1, 2])
        assert s.pointHistory == [1, 2, 1, 2]

    def test_record_points_win_game(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        s.recordPoints([1, 1, 1, 1])
        assert s.score.games(1) == (1, 0)
        assert len(s.gameHistory) == 1

    def test_record_points_win_set(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        # P1 wins 6 games straight (24 points total)
        for _ in range(6):
            s.recordPoints([1, 1, 1, 1])
        assert s.isOver
        assert s.winner == 1


class TestSetProperties:
    """Tests for Set properties."""

    def test_is_over_not_over(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        assert not s.isOver
        win_game(s, 1)
        assert not s.isOver

    def test_is_over_standard_win(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        for _ in range(6):
            win_game(s, 1)
        assert s.isOver

    def test_winner_none_when_not_over(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        assert s.winner is None
        for _ in range(5):
            win_game(s, 1)
        assert s.winner is None

    def test_winner_player1(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        for _ in range(6):
            win_game(s, 1)
        assert s.winner == 1

    def test_winner_player2(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        for _ in range(6):
            win_game(s, 2)
        assert s.winner == 2

    def test_is_tied_at_6_6(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        get_to_tiebreak(s)
        assert s.isTied

    def test_is_not_tied_at_5_5(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        for _ in range(5):
            win_game(s, 1)
            win_game(s, 2)
        assert not s.isTied


class TestSetServerRotation:
    """Tests for server rotation in a set."""

    def test_server_alternates_after_game(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        assert s.servesNext == 1
        win_game(s, 1)
        assert s.servesNext == 2
        win_game(s, 2)
        assert s.servesNext == 1

    def test_server_after_set_ends(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        # P1 wins 6-0, serving games 1, 3, 5
        for _ in range(6):
            win_game(s, 1)
        assert s.isOver
        # After set ends with P2 serving game 6, next server should be P1
        # Wait, P1 wins but who served? Let's trace:
        # Game 1: P1 serves, wins -> P2 serves next
        # Game 2: P2 serves, P1 wins -> P1 serves next
        # Game 3: P1 serves, wins -> P2 serves next
        # Game 4: P2 serves, P1 wins -> P1 serves next
        # Game 5: P1 serves, wins -> P2 serves next
        # Game 6: P2 serves, P1 wins -> P1 serves next set
        assert s.servesNext == 1

    def test_server_rotation_player2_starts(self):
        s = Set(playerServing=2, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        assert s.servesNext == 2
        win_game(s, 2)
        assert s.servesNext == 1
        win_game(s, 1)
        assert s.servesNext == 2


class TestSetGameHistory:
    """Tests for game history tracking."""

    def test_game_history_empty_initially(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        assert s.gameHistory == []

    def test_game_history_after_one_game(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        win_game(s, 1)
        assert len(s.gameHistory) == 1
        assert s.gameHistory[0].winner == 1

    def test_game_history_after_multiple_games(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        win_game(s, 1)
        win_game(s, 2)
        win_game(s, 1)
        assert len(s.gameHistory) == 3
        assert s.gameHistory[0].winner == 1
        assert s.gameHistory[1].winner == 2
        assert s.gameHistory[2].winner == 1


class TestSetPointHistory:
    """Tests for point history tracking."""

    def test_point_history_empty_initially(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        assert s.pointHistory == []

    def test_point_history_within_game(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        s.recordPoints([1, 2, 1])
        assert s.pointHistory == [1, 2, 1]

    def test_point_history_across_games(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        win_game(s, 1)  # 4 points
        s.recordPoints([2, 2])  # 2 more points
        assert len(s.pointHistory) == 6
        assert s.pointHistory[:4] == [1, 1, 1, 1]
        assert s.pointHistory[4:] == [2, 2]


class TestSetTotalPoints:
    """Tests for total points tracking."""

    def test_total_points_initial(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        assert s.totalPoints == (0, 0)

    def test_total_points_after_game(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        win_game(s, 1)
        assert s.totalPoints == (4, 0)

    def test_total_points_mixed(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        s.recordPoints([1, 2, 1, 2, 1, 1])  # P1 wins 4-2
        assert s.totalPoints == (4, 2)


class TestSetTiebreak:
    """Tests for tiebreak scenarios."""

    def test_tiebreak_starts_at_6_6(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        get_to_tiebreak(s)
        assert s.tiebreaker is not None
        assert s.currentGame is None

    def test_tiebreak_p1_wins(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        get_to_tiebreak(s)
        # P1 wins tiebreak 7-0
        s.recordPoints([1] * 7)
        assert s.isOver
        assert s.winner == 1
        assert s.score.games(1) == (7, 6)

    def test_tiebreak_p2_wins(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        get_to_tiebreak(s)
        # P2 wins tiebreak 7-0
        s.recordPoints([2] * 7)
        assert s.isOver
        assert s.winner == 2
        assert s.score.games(1) == (6, 7)

    def test_tiebreak_extended(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        get_to_tiebreak(s)
        # Get to 6-6 in tiebreak
        s.recordPoints([1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2])
        assert not s.isOver
        # P1 wins 8-6
        s.recordPoints([1, 1])
        assert s.isOver
        assert s.winner == 1

    def test_tiebreak_in_game_history(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        get_to_tiebreak(s)
        s.recordPoints([1] * 7)
        # Tiebreak should be last item in game history
        assert len(s.gameHistory) == 13  # 12 games + 1 tiebreak
        from tennis_lab.core.tiebreak import Tiebreak
        assert isinstance(s.gameHistory[-1], Tiebreak)


class TestSetWinConditions:
    """Tests for various set win conditions."""

    def test_win_6_0(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        for _ in range(6):
            win_game(s, 1)
        assert s.isOver
        assert s.score.games(1) == (6, 0)

    def test_win_6_4(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        # Alternate wins: P1, P2, P1, P2, P1, P2, P1, P2, P1, P1
        for i in range(10):
            if i < 8:
                win_game(s, (i % 2) + 1)
            else:
                win_game(s, 1)
        assert s.isOver
        assert s.score.games(1) == (6, 4)

    def test_win_7_5(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        # Get to 5-5
        for _ in range(5):
            win_game(s, 1)
            win_game(s, 2)
        assert s.score.games(1) == (5, 5)
        # P1 wins 2 more
        win_game(s, 1)
        win_game(s, 1)
        assert s.isOver
        assert s.score.games(1) == (7, 5)

    def test_win_7_6_tiebreak(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        get_to_tiebreak(s)
        s.recordPoints([1] * 7)
        assert s.isOver
        assert s.score.games(1) == (7, 6)


class TestSetStr:
    """Tests for __str__ method."""

    def test_str_initial(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        assert "Player1 to serve at 0-0" in str(s)

    def test_str_mid_game(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        s.recordPoints([1, 2])
        assert "Player1 to serve at 0-0, 15-15" == str(s)

    def test_str_between_games(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        win_game(s, 1)
        assert "Player2 to serve at 0-1, 0-0" == str(s)

    def test_str_set_over(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        for _ in range(6):
            win_game(s, 1)
        assert "Player1 wins set: 6-0" == str(s)

    def test_str_tiebreak_win(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        get_to_tiebreak(s)
        s.recordPoints([1] * 7)
        result = str(s)
        assert "Player1 wins set: 7-6" in result
        assert "(7-0)" in result


class TestSetRepr:
    """Tests for __repr__ method."""

    def test_repr_contains_set(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        assert "Set" in repr(s)

    def test_repr_contains_server(self):
        s = Set(playerServing=2, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        assert "playerServing=2" in repr(s)

    def test_repr_contains_isFinalSet(self):
        s = Set(playerServing=1, isFinalSet=True, matchFormat=DEFAULT_FORMAT)
        assert "isFinalSet=True" in repr(s)

    def test_repr_contains_score(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        win_game(s, 1)
        repr_str = repr(s)
        assert "initScore=" in repr_str
        assert "SetScore" in repr_str

    def test_repr_recreates_set(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        win_game(s, 1)
        win_game(s, 2)
        recreated = eval(repr(s))
        assert recreated.score.games(1) == s.score.games(1)


class TestSetScoreHistory:
    """Tests for scoreHistory method."""

    def test_score_history_initial(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        history = s.scoreHistory()
        assert "Game" in history or history == ""

    def test_score_history_after_game(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        win_game(s, 1)
        history = s.scoreHistory()
        assert "Game 1" in history
        assert "P1 wins game" in history

    def test_score_history_set_complete(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        for _ in range(6):
            win_game(s, 1)
        history = s.scoreHistory()
        assert "P1 wins set" in history

    def test_score_history_tiebreak(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        get_to_tiebreak(s)
        s.recordPoints([1] * 7)
        history = s.scoreHistory()
        assert "Tiebreak" in history


class TestSetWithInitialScore:
    """Tests for sets starting at non-zero scores."""

    def test_start_at_3_2(self):
        init_score = SetScore(3, 2, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        s = Set(playerServing=1, isFinalSet=False, initScore=init_score)

        assert s.score.games(1) == (3, 2)
        assert s.gameHistory == []

        # P1 wins 3 more games
        for _ in range(3):
            win_game(s, 1)
        assert s.isOver
        assert s.winner == 1
        assert s.score.games(1) == (6, 2)

    def test_start_at_5_5(self):
        init_score = SetScore(5, 5, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        s = Set(playerServing=1, isFinalSet=False, initScore=init_score)

        # P1 wins 2 games
        win_game(s, 1)
        win_game(s, 1)
        assert s.isOver
        assert s.score.games(1) == (7, 5)

    def test_start_at_6_6_tiebreak(self):
        init_score = SetScore(6, 6, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        s = Set(playerServing=1, isFinalSet=False, initScore=init_score)

        assert s.tiebreaker is not None
        assert s.currentGame is None

        # P2 wins tiebreak
        s.recordPoints([2] * 7)
        assert s.isOver
        assert s.winner == 2


class TestSetNoAdRule:
    """Tests for sets with no-ad rule."""

    def test_no_ad_game_ends_at_deuce(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=NO_AD_FORMAT)
        # Get to deuce (40-40)
        s.recordPoints([1, 1, 1, 2, 2, 2])
        # Next point wins
        s.recordPoint(1)
        assert s.currentGame is None or s.currentGame.score.asPoints(1) == (0, 0)
        assert s.score.games(1) == (1, 0)


class TestSetFinalSetRules:
    """Tests for final set specific rules."""

    def test_final_set_flag_preserved(self):
        s = Set(playerServing=1, isFinalSet=True, matchFormat=DEFAULT_FORMAT)
        assert s._isFinalSet is True
        win_game(s, 1)
        assert s._isFinalSet is True

    def test_non_final_set_flag_preserved(self):
        s = Set(playerServing=1, isFinalSet=False, matchFormat=DEFAULT_FORMAT)
        assert s._isFinalSet is False
        win_game(s, 1)
        assert s._isFinalSet is False
