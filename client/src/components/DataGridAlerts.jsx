import React, { useMemo, useState } from "react";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Card } from "primereact/card";
import ConfidenceCircle from "./ConfidenceCircle";
import VerdictTag from "./VerdictTag";
import DetailsDialog from "./DetailsDialog";

const TimestampBody = (row) =>
  row.timestamp ? new Date(row.timestamp).toLocaleString() : "—";

const ConfidenceBody = (row) => (
  <ConfidenceCircle value={Number(row.verdict_confidence) || 0} />
);

export default function DataGridAlerts({ data }) {
  const [selected, setSelected] = useState(null);
  const [visible, setVisible] = useState(false);

  const derived = useMemo(() => {
    return (data || []).map((row) => {
      let logCount = null;
      let alertName = row.alert_name || "—";
      try {
        const parsed = JSON.parse(row.raw_logs || "null");
        if (Array.isArray(parsed)) {
          logCount = parsed.length;
          if (parsed[0]?.alert_name) alertName = parsed[0].alert_name;
        } else if (parsed && typeof parsed === "object") {
          logCount = 1;
          if (parsed.alert_name) alertName = parsed.alert_name;
        }
      } catch (e) {
        logCount = null;
      }
      return { ...row, log_count: logCount, alert_name: alertName };
    });
  }, [data]);

  const openDialog = (row) => {
    setSelected(row);
    setVisible(true);
  };

  const actionBody = (row) => (
    <button className="pill-btn" onClick={() => openDialog(row)}>
      View
    </button>
  );

  return (
    <Card className="table-card">
      <DataTable
        value={derived}
        paginator
        rows={5}
        responsiveLayout="stack"
        size="small"
        stripedRows
      >
        <Column header="" body={actionBody} style={{ width: "90px" }} />
        <Column field="timestamp" header="Timestamp" body={TimestampBody} sortable />
        <Column field="alert_name" header="Alert Name" />
        <Column field="verdict" header="Verdict" body={(row) => <VerdictTag verdict={row.verdict} />} />
        <Column field="verdict_confidence" header="Confidence" body={ConfidenceBody} />
        <Column field="log_count" header="Log Count" />
      </DataTable>

      <DetailsDialog visible={visible} onHide={() => setVisible(false)} row={selected} />
    </Card>
  );
}
