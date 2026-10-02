import math

import numpy as np
import pandas as pd
import datetime
from dataclasses import dataclass

def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
 ------ Builds a data model that calculates and holds the coefficients for the athlete ------
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

@dataclass
class AthleteModel:
    coefs: np.ndarray
    features: list
    # Each entry is (distance in metres, ideal-equivalent seconds, date).  Keeping
    # the observations is deliberate: a runner's small race history is much too
    # small to safely estimate a separate weather, surface, elevation, and
    # distance coefficient.
    performances: list
    distance_exponent: float = 1.06

    @property
    def coef_dict(self):
        return dict(zip(self.features, self.coefs))

def design_matrix(distance_list, temp_list, hum_list, elev_list, surface_list=None):
    ## Turn list values into np arrays
    dist = np.asarray(distance_list, dtype=float)
    logd = np.log(dist)
    heat_above60 = np.maximum(0.0, np.asarray(temp_list, dtype=float) - 60.0)
    hum_above60 = np.maximum(0.0, np.asarray(hum_list, dtype=float) - 60.0)
    elev_gain = np.maximum(0.0, np.asarray(elev_list, dtype=float))

    ## Surface encoding: track=0, grass=1, trail=2
    grass_flag = []
    trail_flag = []
    if surface_list is not None:
        for s in surface_list:
            s = (s or "").strip().lower()
            grass_flag.append(1.0 if s == "grass" else 0.0)
            trail_flag.append(1.0 if s == "trail" else 0.0)
    else:
        grass_flag = [0.0] * len(dist)
        trail_flag = [0.0] * len(dist)

    ## Create matrix of coefficients for each feature => coeficient vector
    X = np.column_stack([
        np.ones_like(logd),  # 1
        logd,                # ln(d)
        heat_above60,        # H
        hum_above60,         # U
        elev_gain,
        grass_flag,          # G
        trail_flag           # T
        ])
    feature_names = ["intercept", "logd", "heat_above60", "hum_above60", "elev_gain", "grass", "trail"]
    return X, feature_names
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
 ------ Utility functions for data parsing & conversion   -------
 - parse_time_to_seconds: convert a "M:SS" or "M:SS.ss" string into total seconds (float)
 - seconds_to_time: format a float number of seconds back into "M:SS.ss" string
 - to_int_safe: safely convert a value to int (returns default if it fails)
 - to_float_safe: safely convert a value to float (returns default if it fails)
 - to_date_safe: parse a date string ("M/D/YYYY") into a datetime.date object

 These functions keep input handling robust by catching bad/missing values,
 ensuring the rest of the modeling code always works with clean, numeric data.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def parse_time_to_seconds(time_str):
    """
    Accepts formats like '12:34.56' or '12:34' and returns total seconds as float.
    """
    if not time_str or ":" not in time_str:
        raise ValueError(f"Invalid time string: {time_str}")
    m_str, s_str = time_str.strip().split(":")
    return int(m_str) * 60 + float(s_str)

def seconds_to_time(seconds):
    """
    Converts seconds (float) to 'M:SS.ss' format.
    """
    if seconds is None:
        return None
    seconds = float(seconds)
    minutes = int(seconds // 60)
    remaining_seconds = seconds - minutes * 60
    return f"{minutes}:{remaining_seconds:05.2f}"  # zero-pad seconds to at least 2 digits

def to_int_safe(v, default=None):
    try:
        return int(str(v).strip())
    except Exception:
        return default

def to_float_safe(v, default=None):
    try:
        return float(str(v).strip())
    except Exception:
        return default

def to_date_safe(date_str, default=None):
    """
    Expects M/D/YYYY or MM/DD/YYYY
    """
    try:
        month, day, year = map(int, date_str.strip().split("/"))
        return datetime.date(year, month, day)
    except Exception:
        return default


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  ------ Time predicting functions -------
  - The data model of the athlete created are used to predict the time of the runner in ideal, perfect conditions
  - The Gascon Model is a model for predicting race times across different distances
  - A heuristic approach is taken if their is an insufficient amount of data to use the default model
 """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


def _condition_multiplier(temp, humidity, elev, surface):
    """Return a conservative, dimensionless adjustment for race conditions.

    These are intentionally small population-level adjustments.  Estimating
    them from a single athlete's handful of races was the source of the large
    and erratic predictions in the previous model.
    """
    temp = to_float_safe(temp, 60)
    humidity = to_float_safe(humidity, 60)
    elev = max(0.0, to_float_safe(elev, 0))
    surface = (surface or "track").strip().lower()

    weather = 0.0015 * max(0.0, temp - 60.0)
    weather += 0.0003 * max(0.0, humidity - 60.0)
    elevation = 0.00004 * elev
    surface_penalty = {"grass": 0.010, "trail": 0.020}.get(surface, 0.0)
    return 1.0 + weather + elevation + surface_penalty


def _weighted_median(values, weights):
    order = np.argsort(values)
    values = np.asarray(values, dtype=float)[order]
    weights = np.asarray(weights, dtype=float)[order]
    return float(values[np.searchsorted(np.cumsum(weights), weights.sum() / 2.0)])


def fit_athlete_performance_model(runners, athlete, min_samples=3, alpha=None):
    dist, temp, hum, elev, surface, times, dates = [], [], [], [], [], [], []

    for r in runners:
        if r.name.strip() != athlete.strip():
            continue
        d = to_float_safe(r.distance)
        t = to_float_safe(r.temperature)
        h = to_float_safe(r.humidity)
        e = to_float_safe(r.elevation)
        # time_sec is already stored as total seconds (float) on the Race model,
        # not a "M:SS" string, so just read it directly.
        time_sec = to_float_safe(r.time_sec)
        if d and d > 0 and t is not None and h is not None and e is not None and time_sec is not None:
            dist.append(d); temp.append(t); hum.append(h); elev.append(e)
            surface.append(r.surface); times.append(time_sec); dates.append(to_date_safe(r.date))
    if len(times) < min_samples:
        return None

    # Convert every result to an ideal-condition equivalent, then project each
    # one to the requested distance with the well-established Riegel exponent.
    # This needs only a few races and cannot invent extreme coefficients.
    performances = []
    for d, t, h, e, s, time_sec, date in zip(dist, temp, hum, elev, surface, times, dates):
        performances.append((d, time_sec / _condition_multiplier(t, h, e, s), date))

    # Retain these fields for backwards compatibility with callers that inspect
    # coef_dict.  Condition handling is multiplicative, so coefficients are no
    # longer used to generate the prediction.
    return AthleteModel(
        coefs=np.zeros(7),
        features=["intercept", "logd", "heat_above60", "hum_above60", "elev_gain", "grass", "trail"],
        performances=performances,
    )

def predict_time(model, distance, temp, humidity, elev, surface):
    """
    Predict the athlete's race time under the given conditions.

    Uses the learned linear model:
        y = Xβ
    where:
        X = feature vector for this race
        β = learned regression coefficients
    """
    distance = to_float_safe(distance)
    if distance is None or distance <= 0 or not model.performances:
        return None

    latest_date = max((date for _, _, date in model.performances if date), default=None)
    projections, weights = [], []
    for source_distance, ideal_seconds, race_date in model.performances:
        projected = ideal_seconds * (distance / source_distance) ** model.distance_exponent
        # Nearby race distances are more informative; recent races get up to
        # twice the weight of races roughly six months older.
        distance_weight = np.exp(-abs(np.log(distance / source_distance)) / 0.55)
        days_old = (latest_date - race_date).days if latest_date and race_date else 0
        recency_weight = 0.5 ** (days_old / 180.0)
        projections.append(projected)
        weights.append(distance_weight * recency_weight)

    ideal_prediction = _weighted_median(projections, weights)
    return float(ideal_prediction * _condition_multiplier(temp, humidity, elev, surface))

def ideal_time_for_distance(model, distance):
    """
    The athlete's predicted time for this distance with every condition
    penalty zeroed out: 60F, 60% humidity, no elevation gain, on a track.
    """
    return predict_time(model, distance, 60, 60, 0, "track")

def model_residual_std(model, runners, athlete):
    """
    Standard deviation of (actual time - model-predicted time) across the
    athlete's races. A rough measure of how consistent/predictable the
    athlete's performances are relative to the model's fit.
    """
    dist, temp, hum, elev, surface, times = [], [], [], [], [], []
    for r in runners:
        if r.name.strip() != athlete.strip():
            continue
        d = to_float_safe(r.distance)
        t = to_float_safe(r.temperature)
        h = to_float_safe(r.humidity)
        e = to_float_safe(r.elevation)
        time_sec = to_float_safe(r.time_sec)
        if d and d > 0 and t is not None and h is not None and e is not None and time_sec is not None:
            dist.append(d); temp.append(t); hum.append(h); elev.append(e)
            surface.append(r.surface); times.append(time_sec)

    if len(times) < 2:
        return None

    residuals = []
    athlete_races = [r for r in runners if r.name.strip() == athlete.strip()]
    for held_out in athlete_races:
        training = [r for r in athlete_races if r is not held_out]
        leave_one_out_model = fit_athlete_performance_model(training, athlete)
        if leave_one_out_model is None:
            continue
        prediction = predict_time(
            leave_one_out_model, held_out.distance, held_out.temperature,
            held_out.humidity, held_out.elevation, held_out.surface,
        )
        if prediction is not None:
            residuals.append(to_float_safe(held_out.time_sec) - prediction)

    # Root mean squared leave-one-out error is an honest uncertainty estimate;
    # the old in-sample residual standard deviation was artificially optimistic.
    if not residuals:
        return None
    return float(np.sqrt(np.mean(np.square(residuals))))

def athlete_progress_history(model, runners, athlete, distance):
    """
    For every one of the athlete's races at this distance, return the actual
    time alongside a condition-adjusted 'ideal-equivalent' time (what that
    same race would have looked like at 60F/60% humidity/no elevation/track),
    sorted chronologically. Powers the progress graph.
    """
    distance = to_float_safe(distance)
    if distance is None:
        return []

    ideal_baseline = ideal_time_for_distance(model, distance)
    rows = []
    for r in runners:
        if r.name.strip() != athlete.strip():
            continue
        if to_float_safe(r.distance) != distance:
            continue
        actual = to_float_safe(r.time_sec)
        if actual is None:
            continue
        t = to_float_safe(r.temperature, 60)
        h = to_float_safe(r.humidity, 60)
        e = to_float_safe(r.elevation, 0)
        predicted_actual_conditions = predict_time(model, distance, t, h, e, r.surface)
        # Shift the real time by however much the model says these conditions
        # cost (or helped), landing on an ideal-equivalent time.
        ideal_equivalent = actual - (predicted_actual_conditions - ideal_baseline)
        rows.append({
            "event": r.event,
            "date": r.date,
            "time_sec": actual,
            "ideal_time_sec": ideal_equivalent,
        })

    rows.sort(key=lambda row: to_date_safe(row["date"]) or datetime.date.min)
    return rows

def calculate_vdot(distance: float, time: float):
    """
    Calculate Daniels & Gilbert VO₂ and VDOT.

    Returns:
        (vo2_est, percent_vo2max, vdot)
    """
    if distance <= 0 or time <= 0:
        raise ValueError("Distance and time must be positive.")
    # Average running speed (m/min)
    speed = distance / time * 60
    # Estimated oxygen cost of running at this speed
    vo2_est = (
        0.182258 * speed
        + 0.000104 * speed**2
        + 3.5
    )
    # Sustainable fraction of VO₂max for the race duration
    minutes = time / 60
    percent = (
        0.8
        + 0.1894393 * math.exp(-0.012778 * minutes)
        + 0.2989558 * math.exp(-0.1932605 * minutes)
    )
    # Daniels VDOT estimate
    vdot = vo2_est / percent

    return round(vo2_est, 2), round(percent, 4), round(vdot, 2)

def normalize_time(model, actual_time, temp, humidity, elev, surface):
    """
    Convert an actual race time to its equivalent under ideal conditions.
    """
    actual_time = to_float_safe(actual_time)
    if actual_time is None:
        return None
    return actual_time / _condition_multiplier(temp, humidity, elev, surface)

def heuristic(time_sec, distance_m, temp_f, humidity, elevation_gain_m, athlete=None, runners=None):

    pass


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  ------ Averaging functions -------
  - These functions calculate different averages according to the race times
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def average_ideal_for_distance(runners, athlete, distance):
    distance = to_int_safe(distance, None)
    if distance is None:
        return None
    times = []
    for r in runners:
        try:
            if r.name.strip() == athlete.strip() and to_int_safe(r.distance) == distance:
                total_sec = to_float_safe(r.time_sec)
                temp = to_float_safe(r.temperature, 60)
                hum = to_float_safe(r.humidity, 60)
                elev = to_float_safe(r.elevation, 0)
                normal = normalize_time(None, total_sec, temp, hum, elev, r.surface)
                if normal is not None:
                    times.append(normal)
        except Exception:
            continue
    if not times:
        return None
    return float(np.mean(times))

def average_time_for_distance(runners, athlete, distance):
    distance = to_int_safe(distance, None)
    if distance is None:
        return None

    times = []
    for r in runners:
        if r.name.strip() == athlete.strip() and to_int_safe(r.distance) == distance:
            try:
                total_sec = to_float_safe(r.time_sec)
                times.append(total_sec)
            except Exception:
                continue
    if not times:
        return None
    return float(np.mean(times))

def cumulative_averages(runners, athlete, distance):
    distance = to_int_safe(distance, None)
    if distance is None:
        return [], [], []

    raw_times = []
    ideal_times = []
    raw_averages = []
    ideal_averages = []
    events = []

    # Sort by date to make cumulative meaningful
    rows = [
        (to_date_safe(r.date),r) for r in runners if r.name.strip() == athlete.strip()
        and to_int_safe(r.distance) == distance
    ]
    rows.sort(key=lambda x: (x[0] is None, x[0]))  # None dates last, but included

    for _, r in rows:
        try:
            total_sec = to_float_safe(r.time_sec)
            temp = to_float_safe(r.temperature, 60)
            hum = to_float_safe(r.humidity, 60)
            elev = to_float_safe(r.elevation, 0)
            normal = normalize_time(None, total_sec, temp, hum, elev, r.surface)

            if total_sec is None or normal is None:
                continue

            raw_times.append(total_sec)
            ideal_times.append(normal)
            raw_averages.append(float(np.mean(raw_times)))
            ideal_averages.append(float(np.mean(ideal_times)))
            events.append(r.event.strip())
        except Exception:
            continue

    return raw_averages, ideal_averages, events

def gascon_model(distances, times, race_days_ago):
    """
    T(d) = a + b * ln(d) + c * ln(d)^2  ==>>  a,b,c: learned model coefficeints
    """
    ## Turn lists into np arrays
    distances = np.asarray(distances, dtype=float)
    times = np.asarray(times, dtype=float)
    decay_lambda = 0.0026

    decay_weights = np.exp(-decay_lambda * np.array(race_days_ago))
    W = np.diag(decay_weights)
    ## Create a model matrix representing 'a', 'b', and 'c' constants in equation
    X = np.column_stack([
            np.ones(len(distances)), ## Represents a'
            np.log(distances), ## Represents 'b'
            np.log(distances)**2 ## Represents 'c'
            ])

    beta = np.linalg.solve(
    X.T @ W @ X,
    X.T @ W @ times
)
    a, b, c = beta
    x = np.log(distances)

    return a + b*x + c*x*x

def weighted(runners, athlete, distance):
    distance = to_int_safe(distance, None)
    if distance is None:
        return []

    events, times, dates = [], [], []
    for r in runners:
        try:
            if r.name.strip() == athlete.strip() and to_int_safe(r.distance) == distance:
                total_sec = to_float_safe(r.time_sec)
                date = to_date_safe(r.date)
                # Skip rows without valid date or time
                if date is None or total_sec is None:
                    continue
                times.append(total_sec)
                dates.append(date)
                events.append(r.event.strip())
        except Exception:
            continue

    if not times:
        return []

    df = pd.DataFrame({"Race": events, "Time (s)": times, "Date": dates})
    df = df.sort_values("Date")
    today = df["Date"].max()
    df["WeeksAgo"] = df["Date"].apply(lambda d: (today - d).days / 7.0)
    lambda_val = 0.05  # decay rate per week
    df["Weight"] = np.exp(-lambda_val * df["WeeksAgo"])

    weighted_series = []
    for i in range(1, len(df) + 1):
        weighted_avg = np.average(df["Time (s)"].iloc[:i], weights=df["Weight"].iloc[:i])
        weighted_series.append(float(weighted_avg))

    return weighted_series
