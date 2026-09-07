import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../api";
import styles from "../components/Runner.module.css";

export default function RunnerList () {
    const { file_id } = useParams();
    const navigate = useNavigate();
    const [races, setRaces] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filterCard, setFilterCard] = useState(false);
    const [checked, setChecked] = useState([]);
    const [checkedD, setCheckedD] = useState([]);
    const [distances, setDistances] = useState([]);
    const [athletes, setAthletes] = useState([]);

    // Filter athlete and distance
    const filteredRaces = races.filter(r =>
                    checked.includes(r.name) && checkedD.includes(r.distance)
                );

    function formatTime(seconds) {
    if (seconds == null || isNaN(seconds)) {
        return "00:00:00";
    }

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    const hundredths = Math.round((seconds % 1) * 100);

    return (
        String(minutes).padStart(2, "0") +
        ":" +
        String(remainingSeconds).padStart(2, "0") +
        ":" +
        String(hundredths).padStart(2, "0")
    );
}

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Send a GET request to Django to retrieve the file's data
                const res = await api.get(`/api/runnersviews/?file_id=${file_id}`)
                // res variable is a Django response with the file data, and the data can be accssed
                // though res.data
                setRaces(res.data);
                const uniqueAthletes = [...new Set(res.data.map(r => r.name))];
                const uniqueDistances = [...new Set(res.data.map(d => d.distance))]
                setAthletes(uniqueAthletes);
                setChecked(uniqueAthletes);
                setCheckedD(uniqueDistances);
                setDistances(uniqueDistances);
            }
            catch (error) { console.log(error.response?.data);}
            finally { setLoading(false) }
        }

        fetchData();
    }, [file_id])

    const toggleAllAthletes = () => {
    if (checked.length === athletes.length) {
        setChecked([]);
    } else {
        setChecked(athletes);
    }}

    const toggleAllDistances = () => {
    if (checkedD.length === distances.length) {
        setCheckedD([]);
    } else {
        setCheckedD(distances);
    }};

    function toggleChecked (value) {
      setChecked(current =>
        current.includes(value) ? current.filter(a => a !== value) : [...current, value]
      )
      }
    function toggleCheckedD (value) {
      setCheckedD(current =>
        current.includes(value) ? current.filter(a => a !== value) : [...current, value]
      )
      }

    const bestRaceInSpecificDistance = (distance) =>
    races
      .filter((race) => race.distance === distance)
      .reduce(
        (best, race) => (!best || race.time_sec < best.time_sec ? race : best),
        null
      );

    if (loading) return <p className={styles.loading}>Loading...</p>;

    return (
        <div className={styles["runner-page"]}>

      {/* Sidebar */}
      <aside className={styles.sidebar}>
        <h3>Runner Overview</h3>

        <div className={styles["stat-card"]}>
          <p>Total Races</p>
          <strong>{races.length}</strong>
        </div>

        <div className={styles["stat-card"]}>
          <p>Overall Best</p>
          <p>In Each Distance</p>

          <strong>
            800m: {bestRaceInSpecificDistance(800)?.name}
          </strong>
          <hr/>
          <strong>
            1600m: {bestRaceInSpecificDistance(1600)?.name}
          </strong>
          <hr/>
          <strong>
            3200m: {bestRaceInSpecificDistance(3200)?.name}
          </strong>
          <hr/>
          <strong>
            5K: {bestRaceInSpecificDistance(5000)?.name}
          </strong>
        </div>
      </aside>

      {/* Main */}
      <main className={styles["main-content"]}>

        {/* Header */}
        <div className={styles["filterCard"]}>
          {filterCard ? (

              <div className={styles.dropdown}>
              <label>
              <input
                type="checkbox"
                checked={
                  checked.length === athletes.length
                }
                onChange={toggleAllAthletes}
              />
              All Athletes
            </label>
            <hr />

            {athletes.map(a => (
              <label key={a}>
                <input
                type="checkbox"
                checked={checked.includes(a)}
                onChange={() => toggleChecked(a)}
                />
                {a}
              </label>
            ))}

            <hr />
            <label>
              <input
                type="checkbox"
                checked={
                  checkedD.length === distances.length
                }
                onChange={toggleAllDistances}
              />
              All Distances
            </label>

            {distances.map(a => (
              <label key={a}>
                <input
                type="checkbox"
                checked={checkedD.includes(a)}
                onChange={() => toggleCheckedD(a)}
                />
                {a}
              </label>
            ))}
            </div>
          ) : console.log("")
          }<h1>{} - filters: </h1>
          <button
            onClick={() => setFilterCard(!filterCard)}
            className={styles.filterButton}>
            +
          </button>
        </div>


        {/* Table */}
        <div className={styles.card}>
          <h2>Race History</h2>

          <table className={styles.table}>
            <thead>
              <tr>
                <th>Athlete</th>
                <th>Event</th>
                <th>Date</th>
                <th>Distance</th>
                <th>Time</th>
              </tr>
            </thead>

            <tbody>
              {/** races is a list, so we can map (go through the list) throught he races */}
              {/** and access each individual's race's attributes */}
              {filteredRaces.map(r => (
                <tr
                  key={r.id}
                  className={styles.clickableRow}
                  onClick={() => navigate(`/runner/${file_id}/${encodeURIComponent(r.name)}/${r.id}`)}
                >
                  <td>{r.name}</td>
                  <td>{r.event}</td>
                  <td>{r.date}</td>
                  <td>{r.distance}</td>
                  <td>{formatTime(r.time_sec)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </main>
    </div>
    )
}
