interface Props {
  value: number;
  size?: number;
  interactive?: boolean;
  onChange?: (value: number) => void;
}

export function StarRating({ value, size = 15, interactive = false, onChange }: Props) {
  return (
    <div className="row gap-1" style={{ gap: 2 }} role={interactive ? "radiogroup" : undefined}>
      {[1, 2, 3, 4, 5].map((n) => {
        const filled = n <= Math.round(value);
        return (
          <span
            key={n}
            onClick={interactive ? () => onChange?.(n) : undefined}
            style={{
              cursor: interactive ? "pointer" : "default",
              lineHeight: 0,
              color: filled ? "#fbbf24" : "var(--text-faint)",
            }}
          >
            <svg width={size} height={size} viewBox="0 0 24 24" fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.5">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
          </span>
        );
      })}
    </div>
  );
}
