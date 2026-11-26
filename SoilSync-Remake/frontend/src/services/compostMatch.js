import { useEffect, useState } from "react";
import { api } from "./api";

export function useCompostMatch(scanId) {
  const [result, setResult] = useState(null);
  useEffect(() => {
    if (!scanId) return;
    const request = new AbortController();
    api(`/scans/${scanId}/method-match`, { signal: request.signal })
      .then((match) => setResult({ ...match, scanId }))
      .catch((error) => {
        if (error.name !== "AbortError") setResult({ error: error.message, scanId });
      });
    return () => request.abort();
  }, [scanId]);
  return result?.scanId === scanId ? result : null;
}
