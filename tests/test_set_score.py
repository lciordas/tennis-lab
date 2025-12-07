"""Tests for the SetScore class."""

import pytest
from src.core.set_score import SetScore
from src.core.game_score import GameScore
from src.core.tiebreak_score import TiebreakScore


class TestSetScoreInit:
    """Tests for SetScore initialization."""

    def test_init_blank_score(self):
        score = SetScore()
        assert score.gamesP1 == 0
        assert score.gamesP2 == 0
        assert score.isBlank

    def test_init_with_games(self):
        score = SetScore(3, 2)
        assert score.gamesP1 == 3
        assert score.gamesP2 == 2
        assert score.currGameScore is not None
        assert score.currGameScore.isBlank

    def test_init_with_game_score(self):
        game_score = GameScore(2, 1)
        score = SetScore(3, 2, gameScore=game_score)
        assert score.gamesP1 == 3
        assert score.gamesP2 == 2
        assert score.currGameScore.asPoints(1) == (2, 1)

    def test_init_at_tiebreak(self):
        score = SetScore(6, 6)
        assert score.isTied
        assert score.currGameScore is None
        assert score.tiebreakScore is not None
        assert score.tiebreakScore.isBlank

    def test_init_with_tiebreak_score(self):
        tb_score = TiebreakScore(3, 2, isSuper=False)
        score = SetScore(6, 6, tiebreakScore=tb_score)
        assert score.tiebreakScore.asPoints(1) == (3, 2)

    def test_init_invalid_non_integer_games(self):
        with pytest.raises(ValueError):
            SetScore(3.5, 2)
        with pytest.raises(ValueError):
            SetScore(3, "2")

    def test_init_invalid_negative_games(self):
        with pytest.raises(ValueError):
            SetScore(-1, 0)
        with pytest.raises(ValueError):
            SetScore(0, -1)

    def test_init_invalid_game_score_type(self):
        with pytest.raises(ValueError):
            SetScore(3, 2, gameScore="not a GameScore")

    def test_init_invalid_final_game_score(self):
        final_game = GameScore(4, 0)  # This is a final score
        with pytest.raises(ValueError):
            SetScore(3, 2, gameScore=final_game)

    def test_init_invalid_tiebreak_score_type(self):
        with pytest.raises(ValueError):
            SetScore(6, 6, tiebreakScore="not a TiebreakScore")

    def test_init_invalid_final_tiebreak_score(self):
        final_tb = TiebreakScore(7, 3, isSuper=False)  # This is a final score
        with pytest.raises(ValueError):
            SetScore(6, 6, tiebreakScore=final_tb)

    def test_init_invalid_set_length(self):
        with pytest.raises(ValueError):
            SetScore(0, 0, setLength=0)
        with pytest.raises(ValueError):
            SetScore(0, 0, setLength=-1)
        with pytest.raises(ValueError):
            SetScore(0, 0, setLength="six")

    def test_init_tiebreak_score_without_tiebreak_set(self):
        with pytest.raises(ValueError):
            SetScore(6, 6, tiebreakScore=TiebreakScore(1, 0, isSuper=False), tiebreakSet=False)

    def test_init_game_score_no_ad_mismatch(self):
        game_score = GameScore(2, 1, noAdRule=True)
        with pytest.raises(ValueError):
            SetScore(3, 2, gameScore=game_score, noAdRule=False)

    def test_init_game_score_normalize_mismatch(self):
        game_score = GameScore(2, 1, normalize=True)
        with pytest.raises(ValueError):
            SetScore(3, 2, gameScore=game_score, normalize=False)

    def test_init_tiebreak_score_normalize_mismatch(self):
        tb_score = TiebreakScore(2, 1, isSuper=False, normalize=True)
        with pytest.raises(ValueError):
            SetScore(6, 6, tiebreakScore=tb_score, normalize=False)

    def test_init_custom_set_length(self):
        # 4-game set (like some junior formats)
        score = SetScore(4, 2, setLength=4)
        assert score.isFinal
        assert score.winner == 1

    def test_init_no_tiebreak_set(self):
        # At 6-6 without tiebreak, game continues
        score = SetScore(6, 6, tiebreakSet=False)
        assert not score.isFinal
        assert score.currGameScore is not None
        assert score.tiebreakScore is None


class TestSetScoreProperties:
    """Tests for SetScore properties."""

    def test_is_blank(self):
        assert SetScore().isBlank
        assert SetScore(0, 0).isBlank
        # Not blank if games have been played
        assert not SetScore(1, 0).isBlank
        # Not blank if current game has points
        score = SetScore()
        score.recordPoint(1)
        assert not score.isBlank

    def test_is_tied(self):
        assert not SetScore(5, 5).isTied
        assert SetScore(6, 6).isTied
        assert not SetScore(6, 5).isTied
        # Custom set length
        assert SetScore(4, 4, setLength=4).isTied

    def test_is_final_win_by_two(self):
        assert SetScore(6, 0).isFinal
        assert SetScore(6, 4).isFinal
        assert SetScore(0, 6).isFinal
        assert SetScore(4, 6).isFinal
        assert not SetScore(6, 5).isFinal
        assert not SetScore(5, 6).isFinal

    def test_is_final_tiebreak_win(self):
        assert SetScore(7, 6).isFinal
        assert SetScore(6, 7).isFinal

    def test_winner(self):
        assert SetScore(6, 4).winner == 1
        assert SetScore(4, 6).winner == 2
        assert SetScore(7, 6).winner == 1
        assert SetScore(6, 7).winner == 2
        assert SetScore(5, 5).winner is None
        assert SetScore(6, 6).winner is None

    def test_next_point_is_game(self):
        # Regular game in progress
        assert SetScore(3, 2).nextPointIsGame
        # At tiebreak, not a regular game
        assert not SetScore(6, 6).nextPointIsGame
        # Set is over
        assert not SetScore(6, 4).nextPointIsGame
        # No tiebreak set at 6-6: still playing games
        assert SetScore(6, 6, tiebreakSet=False).nextPointIsGame

    def test_next_point_is_tiebreak(self):
        assert not SetScore(5, 5).nextPointIsTiebreak
        assert SetScore(6, 6).nextPointIsTiebreak
        # Set is over
        assert not SetScore(7, 6).nextPointIsTiebreak
        # No tiebreak set
        assert not SetScore(6, 6, tiebreakSet=False).nextPointIsTiebreak

    def test_game_in_progress(self):
        # At start of game, not in progress
        assert not SetScore(3, 2).gameInProgress
        # After a point, game is in progress
        score = SetScore(3, 2)
        score.recordPoint(1)
        assert score.gameInProgress

    def test_tiebreak_in_progress(self):
        # At start of tiebreak, not in progress
        assert not SetScore(6, 6).tiebreakInProgress
        # After a point, tiebreak is in progress
        score = SetScore(6, 6)
        score.recordPoint(1)
        assert score.tiebreakInProgress


class TestGamesMethod:
    """Tests for games() method."""

    def test_games_pov1(self):
        score = SetScore(4, 2)
        assert score.games(1) == (4, 2)

    def test_games_pov2(self):
        score = SetScore(4, 2)
        assert score.games(2) == (2, 4)

    def test_games_invalid_pov(self):
        score = SetScore(3, 2)
        with pytest.raises(ValueError):
            score.games(0)
        with pytest.raises(ValueError):
            score.games(3)


class TestRecordPoint:
    """Tests for recordPoint method."""

    def test_record_point_basic(self):
        score = SetScore()
        score.recordPoint(1)
        assert score.currGameScore.asPoints(1) == (1, 0)

    def test_record_point_invalid(self):
        score = SetScore()
        with pytest.raises(ValueError):
            score.recordPoint(0)
        with pytest.raises(ValueError):
            score.recordPoint(3)

    def test_record_point_set_over(self):
        score = SetScore(6, 4)
        with pytest.raises(ValueError):
            score.recordPoint(1)

    def test_record_point_completes_game(self):
        score = SetScore()
        # P1 wins 4 points (game)
        for _ in range(4):
            score.recordPoint(1)
        assert score.gamesP1 == 1
        assert score.gamesP2 == 0
        assert score.currGameScore.isBlank

    def test_record_point_completes_set(self):
        score = SetScore(5, 0)
        # P1 wins 4 points (game) to win set 6-0
        for _ in range(4):
            score.recordPoint(1)
        assert score.gamesP1 == 6
        assert score.gamesP2 == 0
        assert score.isFinal
        assert score.winner == 1

    def test_record_point_tiebreak(self):
        score = SetScore(6, 6)
        score.recordPoint(1)
        assert score.tiebreakScore.asPoints(1) == (1, 0)

    def test_record_point_completes_tiebreak(self):
        score = SetScore(6, 6)
        # P1 wins 7 points (tiebreak)
        for _ in range(7):
            score.recordPoint(1)
        assert score.gamesP1 == 7
        assert score.gamesP2 == 6
        assert score.isFinal
        assert score.winner == 1

    def test_record_point_game_transitions_to_tiebreak(self):
        score = SetScore(5, 5)
        # P1 wins a game to make it 6-5
        for _ in range(4):
            score.recordPoint(1)
        assert score.gamesP1 == 6
        assert score.gamesP2 == 5
        assert score.currGameScore is not None
        # P2 wins a game to make it 6-6
        for _ in range(4):
            score.recordPoint(2)
        assert score.gamesP1 == 6
        assert score.gamesP2 == 6
        assert score.tiebreakScore is not None
        assert score.currGameScore is None


class TestNextGameScores:
    """Tests for nextGameScores method."""

    def test_next_game_scores_basic(self):
        score = SetScore(3, 2)
        next_p1, next_p2 = score.nextGameScores()
        assert next_p1.gamesP1 == 4
        assert next_p1.gamesP2 == 2
        assert next_p2.gamesP1 == 3
        assert next_p2.gamesP2 == 3

    def test_next_game_scores_final(self):
        score = SetScore(6, 4)
        assert score.nextGameScores() is None

    def test_next_game_scores_game_in_progress(self):
        score = SetScore(3, 2)
        score.recordPoint(1)  # Now game is in progress
        with pytest.raises(ValueError):
            score.nextGameScores()

    def test_next_game_scores_tiebreak_in_progress(self):
        score = SetScore(6, 6)
        score.recordPoint(1)  # Now tiebreak is in progress
        with pytest.raises(ValueError):
            score.nextGameScores()

    def test_next_game_scores_propagates_flags(self):
        score = SetScore(3, 2, noAdRule=True, normalize=True, setLength=6, tiebreakSet=True)
        next_p1, next_p2 = score.nextGameScores()
        # Verify flags are propagated (check via _noAdRule etc.)
        assert next_p1._noAdRule == True
        assert next_p1._normalize == True
        assert next_p1._setLength == 6
        assert next_p1._tiebreakSet == True


class TestNoTiebreakSet:
    """Tests for sets without tiebreak."""

    def test_no_tiebreak_at_6_6(self):
        score = SetScore(6, 6, tiebreakSet=False)
        assert not score.isFinal
        assert score.currGameScore is not None
        assert score.tiebreakScore is None

    def test_no_tiebreak_win_by_two(self):
        score = SetScore(8, 6, tiebreakSet=False)
        assert score.isFinal
        assert score.winner == 1

    def test_no_tiebreak_not_final_at_7_6(self):
        score = SetScore(7, 6, tiebreakSet=False)
        assert not score.isFinal

    def test_no_tiebreak_continues_past_6_6(self):
        score = SetScore(6, 6, tiebreakSet=False)
        # P1 wins a game
        for _ in range(4):
            score.recordPoint(1)
        assert score.gamesP1 == 7
        assert score.gamesP2 == 6
        assert not score.isFinal
        # P2 wins a game
        for _ in range(4):
            score.recordPoint(2)
        assert score.gamesP1 == 7
        assert score.gamesP2 == 7
        assert not score.isFinal


class TestEquality:
    """Tests for __eq__ and __hash__."""

    def test_equal_scores(self):
        assert SetScore(3, 2) == SetScore(3, 2)

    def test_unequal_games(self):
        assert SetScore(3, 2) != SetScore(2, 3)

    def test_equal_with_game_score(self):
        gs1 = GameScore(2, 1)
        gs2 = GameScore(2, 1)
        assert SetScore(3, 2, gameScore=gs1) == SetScore(3, 2, gameScore=gs2)

    def test_unequal_game_score(self):
        gs1 = GameScore(2, 1)
        gs2 = GameScore(1, 2)
        assert SetScore(3, 2, gameScore=gs1) != SetScore(3, 2, gameScore=gs2)

    def test_hash_consistency(self):
        s1 = SetScore(3, 2)
        s2 = SetScore(3, 2)
        assert hash(s1) == hash(s2)

        # Can use in sets/dicts
        score_set = {s1, s2}
        assert len(score_set) == 1


class TestReprAndStr:
    """Tests for __repr__ and __str__."""

    def test_repr(self):
        score = SetScore(3, 2, noAdRule=True, normalize=True, setLength=6, tiebreakSet=True)
        repr_str = repr(score)
        assert "SetScore" in repr_str
        assert "gamesP1=3" in repr_str
        assert "gamesP2=2" in repr_str
        assert "noAdRule=True" in repr_str
        assert "normalize=True" in repr_str

    def test_repr_eval(self):
        # repr should produce valid Python
        score = SetScore(3, 2)
        recreated = eval(repr(score))
        assert recreated.gamesP1 == 3
        assert recreated.gamesP2 == 2

    def test_str_basic(self):
        assert str(SetScore(3, 2)) == "3-2, 0-0"
        assert str(SetScore(6, 4)) == "6-4"

    def test_str_with_game_score(self):
        score = SetScore(3, 2)
        score.recordPoint(1)
        score.recordPoint(1)
        assert str(score) == "3-2, 30-0"

    def test_str_with_tiebreak_score(self):
        score = SetScore(6, 6)
        score.recordPoint(1)
        score.recordPoint(2)
        assert str(score) == "6-6, 1-1"


class TestPlayFullSet:
    """Integration tests for playing a full set."""

    def test_p1_wins_set_6_0(self):
        score = SetScore()
        for game in range(6):
            for point in range(4):
                score.recordPoint(1)
        assert score.isFinal
        assert score.winner == 1
        assert score.gamesP1 == 6
        assert score.gamesP2 == 0

    def test_p2_wins_set_6_4(self):
        score = SetScore()
        # P1 wins 4 games
        for game in range(4):
            for point in range(4):
                score.recordPoint(1)
        # P2 wins 6 games
        for game in range(6):
            for point in range(4):
                score.recordPoint(2)
        assert score.isFinal
        assert score.winner == 2
        assert score.gamesP1 == 4
        assert score.gamesP2 == 6

    def test_tiebreak_7_6(self):
        score = SetScore()
        # Each player wins 6 games alternately
        for game in range(6):
            for point in range(4):
                score.recordPoint(1)
            for point in range(4):
                score.recordPoint(2)
        assert score.gamesP1 == 6
        assert score.gamesP2 == 6
        assert score.tiebreakScore is not None
        # P1 wins tiebreak 7-0
        for point in range(7):
            score.recordPoint(1)
        assert score.isFinal
        assert score.winner == 1
        assert score.gamesP1 == 7
        assert score.gamesP2 == 6

    def test_tiebreak_extended(self):
        score = SetScore(6, 6)
        # Each player wins 6 points
        for _ in range(6):
            score.recordPoint(1)
            score.recordPoint(2)
        assert not score.isFinal
        assert score.tiebreakScore.asPoints(1) == (6, 6)
        # P1 wins 2 more to win 8-6
        score.recordPoint(1)
        score.recordPoint(1)
        assert score.isFinal
        assert score.winner == 1
