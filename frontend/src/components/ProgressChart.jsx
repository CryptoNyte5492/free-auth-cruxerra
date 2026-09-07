import styles from "./Runner.module.css";

function formatTime(seconds) {
  if (seconds == null || Number.isNaN(seconds) || !Number.isFinite(seconds)) {
    return "--";
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}`;
}

/**
 * Simple, dependency-free SVG line chart plotting an athlete's actual race
 * times against their condition-adjusted "ideal-equivalent" times over time.
 * The y-axis is inverted (faster times higher) so an upward-trending line
 * reads naturally as improvement.
 */
export default function ProgressChart({ history }) {
  if (!history || history.length < 2) {
    return (
      <p className={styles.loading}>
        Not enough races at this distance yet to chart progress.
      </p>
    );
  }

  const width = 640;
  const height = 260;
  const padding = { top: 20, right: 20, bottom: 36, left: 56 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  const allTimes = history.flatMap((h) => [h.time_sec, h.ideal_time_sec]);
  const minTime = Math.min(...allTimes);
  const maxTime = Math.max(...allTimes);
  const timeRange = maxTime - minTime || 1;
  const pad = timeRange * 0.1;

  const xFor = (i) =>
    history.length === 1
      ? padding.left + plotWidth / 2
      : padding.left + (i / (history.length - 1)) * plotWidth;

  // Inverted: faster (smaller) times plot higher on the chart.
  const yFor = (t) =>
    padding.top +
    ((t - (minTime - pad)) / (timeRange + pad * 2)) * plotHeight;

  const actualPoints = history.map((h, i) => [xFor(i), yFor(h.time_sec)]);
  const idealPoints = history.map((h, i) => [xFor(i), yFor(h.ideal_time_sec)]);

  const toPath = (points) =>
    points.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x},${y}`).join(" ");

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" role="img" aria-label="Progress over time">
        {/* Gridlines */}
        {[0, 0.25, 0.5, 0.75, 1].map((frac) => {
          const y = padding.top + frac * plotHeight;
          const t = maxTime + pad - frac * (timeRange + pad * 2);
          return (
            <g key={frac}>
              <line
                x1={padding.left}
                x2={width - padding.right}
                y1={y}
                y2={y}
                stroke="var(--border, #e2e2e2)"
                strokeWidth="1"
              />
              <text x={padding.left - 8} y={y + 4} fontSize="10" textAnchor="end" fill="currentColor">
                {formatTime(t)}
              </text>
            </g>
          );
        })}

        {/* Ideal-equivalent line */}
        <path d={toPath(idealPoints)} fill="none" stroke="#4c9be8" strokeWidth="2" strokeDasharray="4 3" />
        {/* Actual line */}
        <path d={toPath(actualPoints)} fill="none" stroke="#e8794c" strokeWidth="2" />

        {actualPoints.map(([x, y], i) => (
          <circle key={`actual-${i}`} cx={x} cy={y} r="3.5" fill="#e8794c" />
        ))}
        {idealPoints.map(([x, y], i) => (
          <circle key={`ideal-${i}`} cx={x} cy={y} r="3" fill="#4c9be8" />
        ))}

        {history.map((h, i) => (
          <text
            key={`label-${i}`}
            x={xFor(i)}
            y={height - padding.bottom + 16}
            fontSize="10"
            textAnchor="middle"
            fill="currentColor"
          >
            {h.date}
          </text>
        ))}
      </svg>

      <div className={styles.legend}>
        <span>
          <i style={{ background: "#e8794c" }} /> Actual time
        </span>
        <span>
          <i style={{ background: "#4c9be8" }} /> Ideal-equivalent time
        </span>
      </div>
    </div>
  );
}
