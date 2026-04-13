"use client";

import { useEffect, useRef, useState } from "react";

import { narrate } from "@/lib/api";

export interface VerdictPlayerProps {
  readonly verdict: string;
}

type VoiceSource = "vibevoice" | "browser" | "stub" | null;

function pickBrowserVoice(): SpeechSynthesisVoice | null {
  if (typeof window === "undefined" || !window.speechSynthesis) return null;
  const voices = window.speechSynthesis.getVoices();
  if (voices.length === 0) return null;
  const preferred = [
    "Google UK English Male",
    "Microsoft Guy Online",
    "Daniel",
    "Alex",
    "Google US English",
    "Samantha",
  ];
  for (const name of preferred) {
    const match = voices.find((v) => v.name === name);
    if (match) return match;
  }
  return voices.find((v) => v.lang.startsWith("en")) ?? voices[0] ?? null;
}

export function VerdictPlayer({ verdict }: VerdictPlayerProps): JSX.Element {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [source, setSource] = useState<VoiceSource>(null);
  const [browserVoiceReady, setBrowserVoiceReady] = useState<boolean>(false);

  useEffect(() => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    const check = (): void => {
      if (window.speechSynthesis.getVoices().length > 0) {
        setBrowserVoiceReady(true);
      }
    };
    check();
    window.speechSynthesis.onvoiceschanged = check;
    return () => {
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, []);

  useEffect(() => {
    if (!verdict) return;
    let cancelled = false;
    setLoading(true);
    setAudioUrl(null);
    narrate({ verdict_text: verdict })
      .then((response) => {
        if (cancelled) return;
        if (response.source === "vibevoice") {
          setAudioUrl(response.audio_url);
          setSource("vibevoice");
        } else {
          setSource(browserVoiceReady ? "browser" : "stub");
        }
      })
      .catch(() => {
        if (!cancelled) setSource(browserVoiceReady ? "browser" : "stub");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, [verdict, browserVoiceReady]);

  const speakInBrowser = (): void => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(verdict);
    const voice = pickBrowserVoice();
    if (voice) utterance.voice = voice;
    utterance.rate = 0.98;
    utterance.pitch = 0.95;
    utterance.onstart = () => setIsPlaying(true);
    utterance.onend = () => setIsPlaying(false);
    utterance.onerror = () => setIsPlaying(false);
    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  };

  const togglePlay = (): void => {
    if (source === "vibevoice") {
      const el = audioRef.current;
      if (!el) return;
      if (isPlaying) {
        el.pause();
      } else {
        void el.play().catch(() => setIsPlaying(false));
      }
      return;
    }
    if (isPlaying) {
      window.speechSynthesis?.cancel();
      setIsPlaying(false);
      return;
    }
    speakInBrowser();
  };

  const canPlay = !loading && (source === "vibevoice" ? audioUrl !== null : browserVoiceReady);
  const label =
    source === "vibevoice"
      ? "Voiced by VibeVoice-1.5B"
      : source === "browser"
        ? "Voiced by your browser's speech synthesizer"
        : "Narrator warming up…";

  return (
    <section className="animate-fade-in rounded-lg border border-bg-border bg-bg-card p-5">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white">Narrated verdict</h3>
          <p className="text-xs text-muted">{label}</p>
        </div>
        <button
          type="button"
          onClick={togglePlay}
          disabled={!canPlay}
          className="rounded-md border border-profit px-4 py-2 text-xs font-semibold text-profit transition-colors hover:bg-profit hover:text-black disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading ? "Loading…" : isPlaying ? "Pause" : "Play"}
        </button>
      </div>
      <p className="text-sm leading-relaxed text-white">{verdict}</p>
      {audioUrl && source === "vibevoice" && (
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
