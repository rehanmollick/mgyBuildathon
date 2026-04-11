"use client";

import { useEffect, useRef, useState } from "react";

import { narrate } from "@/lib/api";

export interface VerdictPlayerProps {
  readonly verdict: string;
}

export function VerdictPlayer({ verdict }: VerdictPlayerProps): JSX.Element {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [source, setSource] = useState<"stub" | "vibevoice" | null>(null);

  useEffect(() => {
    if (!verdict) return;
    let cancelled = false;
    setLoading(true);
    narrate({ verdict_text: verdict })
      .then((response) => {
        if (cancelled) return;
        setAudioUrl(response.audio_url);
        setSource(response.source);
      })
      .catch(() => {
        if (!cancelled) setAudioUrl(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [verdict]);

  const togglePlay = (): void => {
    const el = audioRef.current;
    if (!el) return;
    if (isPlaying) {
      el.pause();
    } else {
      void el.play().catch(() => setIsPlaying(false));
    }
  };

  return (
    <section className="animate-fade-in rounded-lg border border-bg-border bg-bg-card p-5">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white">Narrated verdict</h3>
          <p className="text-xs text-muted">
            {source === "vibevoice"
              ? "Voiced by VibeVoice-1.5B"
              : "Narrator stub — swap in VibeVoice when it is ready"}
          </p>
        </div>
        <button
          type="button"
          onClick={togglePlay}
          disabled={!audioUrl || loading}
          className="rounded-md border border-profit px-4 py-2 text-xs font-semibold text-profit transition-colors hover:bg-profit hover:text-black disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading ? "Loading…" : isPlaying ? "Pause" : "Play"}
        </button>
      </div>
      <p className="text-sm leading-relaxed text-white">{verdict}</p>
      {audioUrl && (
        <audio
          ref={audioRef}
          src={audioUrl}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onEnded={() => setIsPlaying(false)}
          preload="none"
        />
      )}
    </section>
  );
}
