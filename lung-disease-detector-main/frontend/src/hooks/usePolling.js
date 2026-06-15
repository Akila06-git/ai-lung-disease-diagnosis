import { useEffect, useRef, useState } from "react";

export const usePolling = (fn, { interval = 1500, maxAttempts = 40, enabled = false } = {}) => {
  const [attempts, setAttempts] = useState(0);
  const [isPolling, setIsPolling] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!enabled) {
      if (timerRef.current) clearTimeout(timerRef.current);
      setIsPolling(false);
      return;
    }

    setIsPolling(true);

    const tick = async () => {
      try {
        const shouldContinue = await fn();
        if (!shouldContinue) {
          setIsPolling(false);
          return;
        }
        setAttempts((prev) => prev + 1);
        if (attempts + 1 >= maxAttempts) {
          setIsPolling(false);
          return;
        }
        timerRef.current = setTimeout(tick, interval);
      } catch {
        setIsPolling(false);
      }
    };

    timerRef.current = setTimeout(tick, interval);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [enabled, interval, maxAttempts, fn, attempts]);

  return { isPolling, attempts };
};

