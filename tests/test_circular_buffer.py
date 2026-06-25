import numpy as np

from backtest.utils.circular_buffer import CircularBuffer


def test_to_array_before_full_preserves_order():
    buf = CircularBuffer(size=4)
    buf.append(1)
    buf.append(2)
    buf.append(3)
    assert np.array_equal(buf.to_array(), np.array([1, 2, 3]))


def test_to_array_wraparound_is_chronological():
    buf = CircularBuffer(size=3)
    for v in (1, 2, 3, 4, 5):
        buf.append(v)
    # oldest-to-newest of the last `size` values
    assert np.array_equal(buf.to_array(), np.array([3, 4, 5]))


def test_latest_returns_most_recent():
    buf = CircularBuffer(size=3)
    buf.append(10)
    buf.append(20)
    assert buf.latest() == 20
    buf.append(30)
    buf.append(40)  # wraps, overwrites 10
    assert buf.latest() == 40


def test_getitem_is_chronological_after_wrap():
    buf = CircularBuffer(size=3)
    for v in (1, 2, 3, 4):  # 2,3,4 retained
        buf.append(v)
    assert buf[0] == 2
    assert buf[1] == 3
    assert buf[2] == 4


def test_getitem_out_of_range_before_full():
    buf = CircularBuffer(size=3)
    buf.append(1)
    try:
        _ = buf[1]
        assert False, "expected IndexError"
    except IndexError:
        pass
