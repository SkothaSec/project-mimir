import React, { useEffect, useState } from "react";

const chipClass = (verdict) => {
  const v = (verdict || "").toLowerCase();
  if (v.includes("low") || v.includes("benign") || v.includes("clean")) return "chip good";
  if (v.includes("medium") || v.includes("warn")) return "chip warn";
  if (v.includes("high") || v.includes("malicious") || v.includes("risk")) return "chip danger";
  return "chip";
};

function Row({ r }) {
  return (
    <tr>
      <td>{r.timestamp ? new Date(r.timestamp).toLocaleString() : "—"}</td>
      <td><span className={chipClass(r.verdict)}>{r.verdict || "—"}</span></td>
      <td>{r.verdict_confidence || "—"}</td>
      <td>{r.notes || "—"}</td>
      <td>{r.apophenia || "—"}</td>
      <td>{r.anchoring || "—"}</td>
      <td>{r.abduction || "—"}</td>
      <td className="mono">{r.alert_group_id || "—"}</td>
    </tr>
  );
}

export default function App() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("/api/results")
      .then((r) => r.json())
      .then((data) => {
        setRows(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.toString());
        setLoading(false);
      });
  }, []);

  return (
    <div className="wrap">
      <header>
        <div>
          <h1>Mimir Investigator</h1>
          <p className="subtitle">Latest Vertex assessments (last 5)</p>
        </div>
      </header>

      {loading && <div className="muted">Loading…</div>}
      {error && <div className="error">{error}</div>}

      {!loading && !error && (
        <div className="table-card">
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Verdict</th>
                <th>Confidence</th>
                <th>Notes</th>
                <th>Apophenia</th>
                <th>Anchoring</th>
                <th>Abduction</th>
                <th>Group</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <Row key={i} r={r} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
