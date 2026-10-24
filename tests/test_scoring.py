from elfa.model.reconcile import fantasy_points


def test_win_bonus_matches_platform_examples():
    assert fantasy_points(19, True) == 20.9      # Efes player, MD6 win
    assert fantasy_points(17, True) == 18.7
    assert fantasy_points(5, True) == 5.5
    assert fantasy_points(26, False) == 26       # loss: plain PIR
    assert fantasy_points(-2, False) == -2
    assert fantasy_points(-5, True) == -4.5      # bonus on absolute value
