import React from "react";
import { Dialog } from "primereact/dialog";
import BiasList from "./BiasList";

const formatTs = (ts) => (ts ? new Date(ts).toLocaleString() : "—");

export default function DetailsDialog({ visible, onHide, row }) {
  return (
    <Dialog
      header="Details"
      visible={visible}
      style={{ width: "70vw", maxWidth: "900px" }}
      onHide={onHide}
      className="dialog-content"
    >
      {row && (
        <div className="dialog-grid">
          <div>
            <strong>Timestamp:</strong> {formatTs(row.timestamp)}
          </div>
          <div>
            <strong>Group:</strong> {row.alert_group_id || "—"}
          </div>
          <div>
            <strong>Alert Name:</strong> {row.alert_name || "—"}
          </div>
          <div>
            <strong>Verdict:</strong> {row.verdict || "—"} ({row.verdict_confidence || "—"})
          </div>
          <div>
            <strong>Notes:</strong> {row.notes || "—"}
          </div>
          <div>
            <BiasList
              apophText={row.apophenia}
              anchText={row.anchoring}
              abductText={row.abduction}
            />
           </div>
          <div>
            <strong>Raw Logs:</strong>
            <div className="mono-block">{row.raw_logs || "—"}</div>
          </div>
          <div>
            <strong>Bias JSON:</strong>
            <div className="mono-block">{row.bias_analysis || "—"}</div>
          </div>
        </div>
      )}
    </Dialog>
  );
}
