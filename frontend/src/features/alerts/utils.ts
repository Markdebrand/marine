export function severityLabel(level: "low"|"medium"|"high") {
  return level === "high" ? "Alta" : level === "medium" ? "Media" : "Baja";
}
