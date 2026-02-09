"use client";

function formatCell(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "number") {
    if (Number.isInteger(value) && value > 10_000)
      return value.toLocaleString();
    if (typeof value === "number")
      return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }
  return String(value);
}

export function DataTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (!rows.length) return null;
  const cols = Object.keys(rows[0]);

  return (
    <div className="overflow-x-auto rounded-md border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/50">
            {cols.map((col) => (
              <th
                key={col}
                className="px-4 py-2 text-left font-medium text-muted-foreground"
              >
                {col.replace(/_/g, " ")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b last:border-0">
              {cols.map((col) => (
                <td key={col} className="px-4 py-2 tabular-nums">
                  {formatCell(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
