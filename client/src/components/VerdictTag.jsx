import React from "react";
import { Tag } from "primereact/tag";

const verdictSeverity = (v) => {
  const val = (v || "").toLowerCase();
  if (val.includes("high") || val.includes("malicious") || val.includes("risk")) return "danger";
  if (val.includes("medium") || val.includes("warn")) return "warning";
  if (val.includes("low") || val.includes("benign") || val.includes("clean")) return "success";
  return "info";
};

export default function VerdictTag({ verdict }) {
  return <Tag value={verdict || "—"} severity={verdictSeverity(verdict)} />;
}
