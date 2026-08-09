// The backend deliberately doesn't try to parse/preserve each template's
// literal numbering markers (too fragile across 11 differently-formatted
// legal documents) — it just records nesting depth. This derives display
// markers from that depth, restarting the count within each parent,
// following the decimal → decimal → alpha → roman convention the source
// templates themselves use (e.g. DPA.md: "1." / nested "1." / "a." / "i.").

function toAlpha(n: number): string {
  let value = n;
  let result = "";
  while (value > 0) {
    value -= 1;
    result = String.fromCharCode(97 + (value % 26)) + result;
    value = Math.floor(value / 26);
  }
  return result;
}

const ROMAN_TABLE: [number, string][] = [
  [1000, "m"],
  [900, "cm"],
  [500, "d"],
  [400, "cd"],
  [100, "c"],
  [90, "xc"],
  [50, "l"],
  [40, "xl"],
  [10, "x"],
  [9, "ix"],
  [5, "v"],
  [4, "iv"],
  [1, "i"],
];

function toRoman(n: number): string {
  let value = n;
  let result = "";
  for (const [amount, symbol] of ROMAN_TABLE) {
    while (value >= amount) {
      result += symbol;
      value -= amount;
    }
  }
  return result;
}

function formatMarker(depth: number, count: number): string {
  if (depth <= 1) return `${count}.`;
  if (depth === 2) return `${toAlpha(count)}.`;
  return `${toRoman(count)}.`;
}

export function computeMarkers(body: { depth: number }[]): string[] {
  const counters: number[] = [];
  return body.map((item) => {
    counters[item.depth] = (counters[item.depth] ?? 0) + 1;
    counters.length = item.depth + 1; // drop deeper counters — we've moved past their scope
    return formatMarker(item.depth, counters[item.depth]);
  });
}
