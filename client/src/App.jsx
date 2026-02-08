import React, { useEffect, useState } from "react";
import { ProgressSpinner } from "primereact/progressspinner";
import DataGridAlerts from "./components/DataGridAlerts";

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
          <h1>Project Mimir</h1>
          <p className="subtitle">Latest Vertex assessments (last 5)</p>
        </div>
      </header>

      {loading && (
        <div className="centered">
          <ProgressSpinner />
        </div>
      )}
      {error && <div className="error">{error}</div>}

      {!loading && !error && <DataGridAlerts data={rows} />}
    </div>
  );
}
