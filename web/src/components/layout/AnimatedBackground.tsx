import { useEffect, useRef } from "react";
import "./animated-background.css";

/**
 * Ambient full-page backdrop: slow-drifting blurred gradient blobs plus a radial
 * "spotlight" that tracks the cursor. Pure CSS-driven (transform/opacity only) so it
 * stays smooth without a canvas/WebGL dependency.
 */
export function AnimatedBackground() {
  const spotlightRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onMove(e: MouseEvent) {
      const el = spotlightRef.current;
      if (!el) return;
      el.style.setProperty("--mx", `${e.clientX}px`);
      el.style.setProperty("--my", `${e.clientY}px`);
    }
    window.addEventListener("pointermove", onMove);
    return () => window.removeEventListener("pointermove", onMove);
  }, []);

  return (
    <div className="ambient" aria-hidden="true">
      <div className="ambient-blob ambient-blob--a" />
      <div className="ambient-blob ambient-blob--b" />
      <div className="ambient-blob ambient-blob--c" />
      <div className="ambient-grid" />
      <div ref={spotlightRef} className="ambient-spotlight" />
    </div>
  );
}
