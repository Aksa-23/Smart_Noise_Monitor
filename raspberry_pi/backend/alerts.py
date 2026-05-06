"""
Alert logic for the Smart Noise Monitor backend.

This module decides whether a noise reading should be treated as NORMAL
or ALERT based on the selected operating mode.
"""


THRESHOLDS = {
    "Study": 50,
    "Normal": 70,
    "Event": 85,
}


DEFAULT_MODE = "Normal"


def evaluate_noise(avg_db, mode):
    """
    Evaluate the noise level and return a status string.

    Args:
        avg_db: Average decibel value from the sensor.
        mode: Current user-selected mode, such as Study, Normal, or Event.

    Returns:
        "NORMAL" or "ALERT".
    """

    selected_mode = mode if mode in THRESHOLDS else DEFAULT_MODE
    threshold = THRESHOLDS[selected_mode]

    if avg_db >= threshold:
        return "ALERT"

    return "NORMAL"


def is_alert(status):
    """
    Check whether the current status should trigger an alert action.
    """

    return status == "ALERT"