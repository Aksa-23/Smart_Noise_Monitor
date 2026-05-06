

"""
Simple forecasting logic for the Smart Noise Monitor backend.

This module uses recent noise readings to calculate a moving average
and estimate the short-term noise trend.
"""


def calculate_moving_average(values):
    """
    Calculate the average value from a list of noise readings.

    Args:
        values: A list of numeric dB values.

    Returns:
        The moving average value, or None if the list is empty.
    """

    if not values:
        return None

    return sum(values) / len(values)


def detect_trend(values, tolerance=2.0):
    """
    Detect whether the noise level is increasing, decreasing, or stable.

    The trend is estimated by comparing the average of the first half
    of the values with the average of the second half.

    Args:
        values: A list of numeric dB values ordered from oldest to newest.
        tolerance: Minimum difference required to treat the trend as changed.

    Returns:
        "increasing", "decreasing", "stable", or "not_enough_data".
    """

    if len(values) < 4:
        return "not_enough_data"

    mid_point = len(values) // 2

    first_half = values[:mid_point]
    second_half = values[mid_point:]

    first_avg = calculate_moving_average(first_half)
    second_avg = calculate_moving_average(second_half)

    difference = second_avg - first_avg

    if difference > tolerance:
        return "increasing"

    if difference < -tolerance:
        return "decreasing"

    return "stable"


def generate_forecast(readings):
    """
    Generate a simple forecast summary from recent database readings.

    Args:
        readings: A list of database rows from noise_readings.
                  Each row follows the table format:
                  id, avg_db, peak_db, status, mode, event_marker, muted, timestamp

    Returns:
        A dictionary containing forecast_db, trend, and sample_size.
    """

    if not readings:
        return {
            "forecast_db": None,
            "trend": "not_enough_data",
            "sample_size": 0
        }

    ordered_readings = list(reversed(readings))
    avg_values = [row[1] for row in ordered_readings]

    forecast_db = calculate_moving_average(avg_values)
    trend = detect_trend(avg_values)

    return {
        "forecast_db": round(forecast_db, 2),
        "trend": trend,
        "sample_size": len(avg_values)
    }