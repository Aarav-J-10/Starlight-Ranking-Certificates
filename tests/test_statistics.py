import pytest

from starlight.statistics import clopper_pearson, ols, paired_interval, quantile


def test_quantile_and_ols():
    assert quantile([0, 10], .95) == 9.5
    assert ols([0, 1, 2], [2, 5, 8])["slope"] == 3
    with pytest.raises(ValueError):
        quantile([], .95)


@pytest.mark.parametrize("k,n", [(0, 10), (10, 10), (3, 10), (160, 204)])
def test_cp_against_scipy_exact(k, n):
    scipy = pytest.importorskip("scipy.stats")
    trusted = scipy.binomtest(k, n).proportion_ci(method="exact")
    assert clopper_pearson(k, n) == pytest.approx((trusted.low, trusted.high), abs=1e-10)


def test_confirmation_witnesses_and_family_correction():
    pytest.importorskip("scipy")
    assert paired_interval(90, 6, 8000, .01, 8) == pytest.approx((.518, 1.576), abs=.00051)
    assert paired_interval(59, 293, 8000, .01, 8) == pytest.approx((-3.982, -1.861), abs=.00051)
    narrower = paired_interval(90, 6, 8000, .01, 1)
    wider = paired_interval(90, 6, 8000, .01, 8)
    assert wider[0] < narrower[0] < narrower[1] < wider[1]
    with pytest.raises(ValueError):
        paired_interval(5, 6, 10, .01, 8)
