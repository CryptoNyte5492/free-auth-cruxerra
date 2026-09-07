import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../api";
import styles from "../components/Runner.module.css";
import ProgressChart from "../components/ProgressChart";

function formatTime(seconds) {
  if (seconds == null || Number.isNaN(seconds) || !Number.isFinite(seconds)) {
    return "--";
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  const hundredths = Math.round((seconds % 1) * 100);

  return `${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}.${String(hundredths).padStart(2, "0")}`;
}

function formatSeconds(seconds) {
  if (seconds == null || Number.isNaN(seconds) || !Number.isFinite(seconds)) {
    return "--";
  }
  return `${seconds.toFixed(2)}s`;
}

function parseRaceDate(value) {
  const [month, day, year] = String(value).split("/").map(Number);
  return new Date(year, month - 1, day);
}

function formatDistance(distance) {
  if (distance === 5000) return "5K";
  if (distance === 10000) return "10K";
  return `${distance}m`;
}

export default function RunnerDetail() {
  const { athlete, file_id, race_id } = useParams();
  const navigate = useNavigate();
  const athleteName = decodeURIComponent(athlete);
  const [races, setRaces] = useState([]);
  const [prediction, setPrediction] = useState(null);
  const [predictionError, setPredictionError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const raceRes = await api.get(
          `/api/runnersviews/?file_id=${file_id}&athlete=${encodeURIComponent(athleteName)}`
        );

        setRaces(
          [...raceRes.data].sort((a, b) => parseRaceDate(b.date) - parseRaceDate(a.date))
        );

        const predictionRes = await api.get(
          `/api/runners/prediction/?file_id=${file_id}&athlete=${athlete}&race_id=${race_id}`
        );

        setPrediction(predictionRes.data);
        setPredictionError(null);
      } catch (error) {
        setPredictionError(error.response?.data?.error || "Unable to load prediction.");
        console.log(error.response?.data || error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [athlete, athleteName, file_id, race_id]);

  const selectedRace = useMemo(
    () => races.find((race) => String(race.id) === String(race_id)) || null,
    [races, race_id]
  );
  const selectedDistance = selectedRace?.distance;
  const bestRaceInSpecificDistance = (distance) =>
  races
    .filter((race) => race.distance === distance)
    .reduce(
      (best, race) => (!best || race.time_sec < best.time_sec ? race : best),
      null
    );
  const bestRaceAtDistance = useMemo(() => {
    if (!selectedDistance) return null;
    return races
      .filter((race) => race.distance === selectedDistance)
      .reduce((best, race) => (!best || race.time_sec < best.time_sec ? race : best), null);
  }, [races, selectedDistance]);

  if (loading) return <p className={styles.loading}>Loading...</p>;

  return (
    <div className={styles["runner-page"]}>
      <aside className={styles.sidebar}>
        <button className={styles.backButton} type="button" onClick={() => navigate(`/runner/${file_id}`)}>
          Back
        </button>
        <h3>{athleteName}</h3>

        <div className={styles["stat-card"]}>
          <p>Total Races</p>
          <strong>{races.length}</strong>
        </div>

        <div className={styles["stat-card"]}>
          <p>Personal Bests</p>

          <strong>
            800m: {formatTime(bestRaceInSpecificDistance(800)?.time_sec)}
          </strong>
          <hr/>
          <strong>
            1600m: {formatTime(bestRaceInSpecificDistance(1600)?.time_sec)}
          </strong>
          <hr/>
          <strong>
            3200m: {formatTime(bestRaceInSpecificDistance(3200)?.time_sec)}
          </strong>
          <hr/>
          <strong>
            5K: {formatTime(bestRaceInSpecificDistance(5000)?.time_sec)}
          </strong>
        </div>

        <div className={styles["stat-card"]}>
          <p>{selectedDistance ? `${formatDistance(selectedDistance)} Personal Best` : "Personal Best"}</p>
          <strong>{bestRaceAtDistance ? formatTime(bestRaceAtDistance.time_sec) : "--"}</strong>
        </div>

        <div className={styles["stat-card"]}>
          <p>{selectedDistance ? `${formatDistance(selectedDistance)} Prediction` : "Prediction"}</p>
          <strong>{prediction ? formatTime(prediction.prediction) : "--"}</strong>
        </div>
      </aside>

      <main className={styles["main-content"]}>
        <div className={styles.header}>
          <h1>{athleteName}</h1>
          <p>Progress, race history, and next-race estimate</p>
        </div>

        <div className={styles.card}>
          <h2>Next Race Prediction</h2>
          {predictionError && <p>{predictionError}</p>}
          {prediction && (
            <div className={styles.predictionGrid}>
              <div>
                <p>Predicted Time</p>
                <strong>{formatTime(prediction.prediction)}</strong>
              </div>
              <div>
                <p>Ideal Time (no conditions)</p>
                <strong>{formatTime(prediction.ideal_time)}</strong>
              </div>
              <div>
                <p>Typical prediction error</p>
                <strong>
                  {prediction.std_dev != null ? formatSeconds(prediction.std_dev) : "--"}
                </strong>
              </div>
            </div>
          )}
        </div>

        <div className={styles.card}>
          <h2>Progress Over Time</h2>
          <ProgressChart history={prediction?.history} />
        </div>

        <div className={styles.card}>
          <h2>Race History</h2>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Event</th>
                <th>Date</th>
                <th>Distance</th>
                <th>Time</th>
                <th>Surface</th>
                <th>Weather</th>
              </tr>
            </thead>
            <tbody>
              {prediction?.file_races?.map((race) => (
                <tr key={race.id}>
                  <td>{race.event}</td>
                  <td>{race.date}</td>
                  <td>{race.distance}m</td>
                  <td>{formatTime(race.time_sec)}</td>
                  <td>{race.surface}</td>
                  <td>
                    {race.temperature}F / {race.humidity}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
