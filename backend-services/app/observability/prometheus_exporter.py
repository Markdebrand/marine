from __future__ import annotations

from typing import Dict, Tuple

# Exportador simple de Prometheus (formato de texto) a partir de app.utils.metrics
# Nota: Este exportador no usa prom-client. Es ligero y sin dependencias.

from app.utils.metrics import export_raw


def _format_labels(labels: Tuple[Tuple[str, str], ...]) -> str:
    if not labels:
        return ""
    # Escapar comillas y backslashes según referencia de Prometheus exposition format
    def esc(s: str) -> str:
        return s.replace("\\", r"\\").replace("\n", r"\n").replace('"', r'\"')
    inner = ",".join(f"{k}=\"{esc(v)}\"" for k, v in labels)
    return f"{{{inner}}}"


def render_prometheus_text() -> str:
    counters, timings = export_raw()
    # counters: Dict[(name, labels_tuple), int]
    # timings: Dict[(name, labels_tuple), float]  acumulado en segundos
    lines: list[str] = []

    # Emitir HELP/TYPE para familias detectadas
    seen_counter: set[str] = set()
    seen_summary: set[str] = set()

    for (name, _labels), _ in counters.items():
        if name not in seen_counter:
            lines.append(f"# HELP {name} Counter metric")
            lines.append(f"# TYPE {name} counter")
            seen_counter.add(name)

    for (name, _labels), _ in timings.items():
        # Usaremos sufijos: _seconds_total y _seconds_count para una aproximación de summary
        base = f"{name}_seconds"
        if base not in seen_summary:
            lines.append(f"# HELP {base} Total observed seconds (accumulated)")
            lines.append(f"# TYPE {base}_total counter")
            lines.append(f"# TYPE {base}_count counter")
            seen_summary.add(base)

    # Counters
    for (name, labels), value in counters.items():
        lbl = _format_labels(labels)
        lines.append(f"{name}{lbl} {int(value)}")

    # Timings (como total acumulado y conteo de observaciones si hay contador paralelo)
    # No llevamos número de observaciones en el util de métricas; expondremos solo total acumulado.
    # Para compatibilidad con scrapers, añadimos _total como acumulado y omitimos _count.
    for (name, labels), total_seconds in timings.items():
        base = f"{name}_seconds"
        lbl = _format_labels(labels)
        lines.append(f"{base}_total{lbl} {float(total_seconds):.6f}")

    return "\n".join(lines) + "\n"
