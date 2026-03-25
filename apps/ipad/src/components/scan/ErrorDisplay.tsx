"use client";

interface ErrorDisplayProps {
  errorBoxes?: {
    left: [number, number, number];
    right: [number, number, number];
  };
  errorMessage?: string;
  className?: string;
}

export function ErrorDisplay({
  errorBoxes,
  errorMessage,
  className = "",
}: ErrorDisplayProps) {
  const hasErrors =
    errorMessage ||
    (errorBoxes &&
      ([...errorBoxes.left, ...errorBoxes.right].some((v) => v !== 0)));

  if (!hasErrors) return null;

  return (
    <div
      className={`p-4 bg-red-950 border border-red-800 rounded-xl ${className}`}
    >
      {errorMessage && (
        <p className="text-red-300 font-semibold mb-2">{errorMessage}</p>
      )}
      {errorBoxes && (
        <div className="flex gap-6 text-sm">
          <div>
            <span className="text-gray-400">Links: </span>
            <span className="text-red-300 font-mono">
              [{errorBoxes.left.join(", ")}]
            </span>
          </div>
          <div>
            <span className="text-gray-400">Rechts: </span>
            <span className="text-red-300 font-mono">
              [{errorBoxes.right.join(", ")}]
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
