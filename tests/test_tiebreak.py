"""Tests for the Tiebreak class."""

import pytest
from src.core.tiebreak import Tiebreak
from src.core.tiebreak_score import TiebreakScore


class TestTiebreakInit:
    """Tests for Tiebreak initialization."""

    def test_init_default_score(self):
        tb = Tiebreak(playerToServe=1)
        assert tb.server == 1
        assert tb.score.asPoints(1) == (0, 0)
        assert tb.pointHistory == []
        assert not tb.isOver
        assert tb.winner is None

    def test_init_player2_serves(self):
        tb = Tiebreak(playerToServe=2)
        assert tb.server == 2

    def test_init_super_tiebreak(self):
        tb = Tiebreak(playerToServe=1, isSuper=True)
        assert tb.score._isSuper is True
        assert tb.score.pointsToWin == 10

    def test_init_with_custom_score(self):
        init_score = TiebreakScore(3, 2, isSuper=False)
        tb = Tiebreak(playerToServe=1, initScore=init_score)
        assert tb.score.asPoints(1) == (3, 2)

    def test_init_with_custom_super_score(self):
        init_score = TiebreakScore(5, 4, isSuper=True)
        tb = Tiebreak(playerToServe=1, initScore=init_score, isSuper=True)
        assert tb.score.asPoints(1) == (5, 4)
        assert tb.score._isSuper is True

    def test_init_invalid_server(self):
        with pytest.raises(ValueError):
            Tiebreak(playerToServe=0)
        with pytest.raises(ValueError):
            Tiebreak(playerToServe=3)

    def test_init_invalid_score_type(self):
        with pytest.raises(ValueError):
            Tiebreak(playerToServe=1, initScore="invalid")

    def test_init_invalid_isSuper_type(self):
        with pytest.raises(ValueError):
            Tiebreak(playerToServe=1, isSuper="yes")

    def test_init_mismatched_isSuper(self):
        # initScore is regular tiebreak, but isSuper=True
        init_score = TiebreakScore(3, 2, isSuper=False)
        with pytest.raises(ValueError):
            Tiebreak(playerToServe=1, initScore=init_score, isSuper=True)

        # initScore is super tiebreak, but isSuper=False
        init_score = TiebreakScore(3, 2, isSuper=True)
        with pytest.raises(ValueError):
            Tiebreak(playerToServe=1, initScore=init_score, isSuper=False)

    def test_init_deep_copies_score(self):
        init_score = TiebreakScore(1, 0, isSuper=False)
        tb = Tiebreak(playerToServe=1, initScore=init_score)
        tb.recordPoint(1)
        # Original should be unchanged
        assert init_score.asPoints(1) == (1, 0)
        assert tb.score.asPoints(1) == (2, 0)


class TestTiebreakRecordPoint:
    """Tests for recordPoint method."""

    def test_record_single_point(self):
        tb = Tiebreak(playerToServe=1)
        tb.recordPoint(1)
        assert tb.score.asPoints(1) == (1, 0)
        assert tb.pointHistory == [1]

    def test_record_multiple_points(self):
        tb = Tiebreak(playerToServe=1)
        tb.recordPoint(1)
        tb.recordPoint(2)
        tb.recordPoint(1)
        assert tb.score.asPoints(1) == (2, 1)
        assert tb.pointHistory == [1, 2, 1]

    def test_record_point_invalid(self):
        tb = Tiebreak(playerToServe=1)
        with pytest.raises(ValueError):
            tb.recordPoint(0)
        with pytest.raises(ValueError):
            tb.recordPoint(3)

    def test_record_point_after_tiebreak_over(self):
        tb = Tiebreak(playerToServe=1)
        # P1 wins 7-0
        for _ in range(7):
            tb.recordPoint(1)
        assert tb.isOver
        initial_history = tb.pointHistory.copy()

        # Additional points should be ignored
        tb.recordPoint(2)
        assert tb.pointHistory == initial_history
        assert tb.score.asPoints(1) == (7, 0)


class TestTiebreakRecordPoints:
    """Tests for recordPoints method."""

    def test_record_points_basic(self):
        tb = Tiebreak(playerToServe=1)
        tb.recordPoints([1, 2, 1, 2])
        assert tb.score.asPoints(1) == (2, 2)
        assert tb.pointHistory == [1, 2, 1, 2]

    def test_record_points_to_win(self):
        tb = Tiebreak(playerToServe=1)
        tb.recordPoints([1, 1, 1, 1, 1, 1, 1])
        assert tb.isOver
        assert tb.winner == 1

    def test_record_points_stops_at_tiebreak_over(self):
        tb = Tiebreak(playerToServe=1)
        # Try to record 10 points, but tiebreak ends at 7
        tb.recordPoints([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        assert tb.pointHistory == [1, 1, 1, 1, 1, 1, 1]
        assert tb.score.asPoints(1) == (7, 0)


class TestTiebreakProperties:
    """Tests for Tiebreak properties."""

    def test_is_over_not_over(self):
        tb = Tiebreak(playerToServe=1)
        assert not tb.isOver
        tb.recordPoint(1)
        assert not tb.isOver

    def test_is_over_standard_win(self):
        tb = Tiebreak(playerToServe=1)
        tb.recordPoints([1, 1, 1, 1, 1, 1, 1])
        assert tb.isOver

    def test_is_over_extended_tiebreak(self):
        tb = Tiebreak(playerToServe=1)
        # 6-6, then 7-6, then 8-6
        tb.recordPoints([1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1])
        assert tb.isOver
        assert tb.winner == 1

    def test_winner_none_when_not_over(self):
        tb = Tiebreak(playerToServe=1)
        assert tb.winner is None
        tb.recordPoints([1, 1, 1, 1, 1, 1])
        assert tb.winner is None

    def test_winner_player1(self):
        tb = Tiebreak(playerToServe=1)
        tb.recordPoints([1, 1, 1, 1, 1, 1, 1])
        assert tb.winner == 1

    def test_winner_player2(self):
        tb = Tiebreak(playerToServe=1)
        tb.recordPoints([2, 2, 2, 2, 2, 2, 2])
        assert tb.winner == 2


class TestTiebreakServerRotation:
    """Tests for server rotation in tiebreak."""

    def test_server_after_first_point(self):
        tb = Tiebreak(playerToServe=1)
        assert tb.server == 1
        tb.recordPoint(1)
        # After first point, server switches
        assert tb.server == 2

    def test_server_rotation_pattern(self):
        tb = Tiebreak(playerToServe=1)
        # P1 serves first point
        assert tb.server == 1
        tb.recordPoint(1)  # 1-0
        # P2 serves points 2-3
        assert tb.server == 2
        tb.recordPoint(2)  # 1-1
        assert tb.server == 2
        tb.recordPoint(1)  # 2-1
        # P1 serves points 4-5
        assert tb.server == 1
        tb.recordPoint(1)  # 3-1
        assert tb.server == 1
        tb.recordPoint(2)  # 3-2
        # P2 serves points 6-7
        assert tb.server == 2

    def test_server_rotation_player2_starts(self):
        tb = Tiebreak(playerToServe=2)
        assert tb.server == 2
        tb.recordPoint(1)  # 1-0
        assert tb.server == 1
        tb.recordPoint(2)  # 1-1
        assert tb.server == 1
        tb.recordPoint(1)  # 2-1
        assert tb.server == 2


class TestTiebreakScoreHistory:
    """Tests for scoreHistory property."""

    def test_score_history_initial(self):
        tb = Tiebreak(playerToServe=1)
        history = tb.scoreHistory
        assert "P1 serves 1st" in history
        assert "0-0" in history

    def test_score_history_after_points(self):
        tb = Tiebreak(playerToServe=1)
        tb.recordPoint(1)
        history = tb.scoreHistory
        assert "1-0" in history

    def test_score_history_server_score_first(self):
        tb = Tiebreak(playerToServe=2)
        tb.recordPoint(1)  # P1 wins point, but P2 served first
        history = tb.scoreHistory
        # First server (P2) score should be first, so 0-1
        assert "0-1" in history

    def test_score_history_complete_tiebreak(self):
        tb = Tiebreak(playerToServe=1)
        tb.recordPoints([1, 1, 1, 1, 1, 1, 1])
        history = tb.scoreHistory
        assert "P1 wins tiebreak" in history

    def test_score_history_no_trailing_comma(self):
        tb = Tiebreak(playerToServe=1)
        tb.recordPoint(1)
        history = tb.scoreHistory
        assert not history.endswith(", ")
        assert not history.endswith(",")


class TestTiebreakRepr:
    """Tests for __repr__ method."""

    def test_repr_contains_tiebreak(self):
        tb = Tiebreak(playerToServe=1)
        assert "Tiebreak" in repr(tb)

    def test_repr_contains_server(self):
        tb = Tiebreak(playerToServe=2)
        assert "playerToServe=2" in repr(tb)

    def test_repr_contains_score(self):
        tb = Tiebreak(playerToServe=1)
        tb.recordPoints([1, 2])
        repr_str = repr(tb)
        assert "initScore=" in repr_str
        assert "TiebreakScore" in repr_str

    def test_repr_contains_isSuper(self):
        tb = Tiebreak(playerToServe=1, isSuper=True)
        assert "isSuper=True" in repr(tb)

    def test_repr_recreates_tiebreak(self):
        tb = Tiebreak(playerToServe=1)
        tb.recordPoints([1, 2, 1])
        recreated = eval(repr(tb))
        assert recreated.score.asPoints(1) == tb.score.asPoints(1)
        assert recreated.server == tb.server


class TestTiebreakStr:
    """Tests for __str__ method."""

    def test_str_not_over(self):
        tb = Tiebreak(playerToServe=1)
        assert "Player1 to serve at 0-0" == str(tb)

    def test_str_not_over_with_score(self):
        tb = Tiebreak(playerToServe=1)
        tb.recordPoints([1, 2])
        # After 2 points, server is still P2 (points 2-3 are P2's serve)
        assert "Player2 to serve at 1-1" == str(tb)

    def test_str_tiebreak_over(self):
        tb = Tiebreak(playerToServe=1)
        tb.recordPoints([1, 1, 1, 1, 1, 1, 1])
        assert "Player1 wins tiebreak: 7-0" == str(tb)

    def test_str_player2_wins(self):
        tb = Tiebreak(playerToServe=1)
        tb.recordPoints([2, 2, 2, 2, 2, 2, 2])
        assert "Player2 wins tiebreak: 7-0" == str(tb)


class TestTiebreakExtendedScenarios:
    """Tests for extended tiebreak scenarios (beyond 6-6)."""

    def test_extended_tiebreak_p1_wins(self):
        tb = Tiebreak(playerToServe=1)
        # Get to 6-6
        tb.recordPoints([1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2])
        assert not tb.isOver

        # 7-6, then 8-6
        tb.recordPoints([1, 1])
        assert tb.isOver
        assert tb.winner == 1
        assert tb.score.asPoints(1) == (8, 6)

    def test_extended_tiebreak_back_and_forth(self):
        tb = Tiebreak(playerToServe=1)
        # Get to 6-6
        tb.recordPoints([1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2])

        # 7-6, 7-7, 8-7, 8-8
        tb.recordPoints([1, 2, 1, 2])
        assert not tb.isOver

        # P2 wins 10-8
        tb.recordPoints([2, 2])
        assert tb.isOver
        assert tb.winner == 2


class TestSuperTiebreak:
    """Tests for super-tiebreak (first to 10)."""

    def test_super_tiebreak_win_at_10(self):
        tb = Tiebreak(playerToServe=1, isSuper=True)
        # P1 wins 10-0
        tb.recordPoints([1] * 10)
        assert tb.isOver
        assert tb.winner == 1
        assert tb.score.asPoints(1) == (10, 0)

    def test_super_tiebreak_not_over_at_7(self):
        tb = Tiebreak(playerToServe=1, isSuper=True)
        # 7-0 is not enough in super tiebreak
        tb.recordPoints([1] * 7)
        assert not tb.isOver

    def test_super_tiebreak_extended(self):
        tb = Tiebreak(playerToServe=1, isSuper=True)
        # Get to 9-9
        tb.recordPoints([1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2])
        assert not tb.isOver

        # 10-9, 11-9
        tb.recordPoints([1, 1])
        assert tb.isOver
        assert tb.winner == 1
        assert tb.score.asPoints(1) == (11, 9)


class TestTiebreakWithInitialScore:
    """Tests for tiebreaks starting at non-zero scores."""

    def test_start_at_5_4(self):
        init_score = TiebreakScore(5, 4, isSuper=False)
        tb = Tiebreak(playerToServe=1, initScore=init_score)

        assert tb.score.asPoints(1) == (5, 4)
        assert tb.pointHistory == []

        # P1 wins 2 more points
        tb.recordPoints([1, 1])
        assert tb.isOver
        assert tb.winner == 1
        assert tb.pointHistory == [1, 1]

    def test_start_at_match_point(self):
        init_score = TiebreakScore(6, 4, isSuper=False)
        tb = Tiebreak(playerToServe=2, initScore=init_score)

        # P1 wins next point
        tb.recordPoint(1)
        assert tb.isOver
        assert tb.winner == 1
        assert tb.pointHistory == [1]

    def test_start_near_end_super(self):
        init_score = TiebreakScore(9, 8, isSuper=True)
        tb = Tiebreak(playerToServe=1, initScore=init_score, isSuper=True)

        # P1 wins next point (10-8)
        tb.recordPoint(1)
        assert tb.isOver
        assert tb.winner == 1
