export function severityLabel(level: "low"|"medium"|"high") {
  return level === "high" ? "High" : level === "medium" ? "Medium" : "Low";
}
