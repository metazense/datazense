"use client";

import { useState, type KeyboardEvent } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import type { Dataset } from "@/lib/types";

const PLACEHOLDERS: Record<Dataset, string> = {
  nyc_taxi: "Ask about NYC taxi data\u2026",
  healthcare: "Ask about healthcare data\u2026",
};

interface Props {
  onSend: (message: string) => void;
  disabled?: boolean;
  dataset?: Dataset;
}

export function ChatInput({ onSend, disabled, dataset = "nyc_taxi" }: Props) {
  const [value, setValue] = useState("");

  function submit() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }

  function handleKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="flex gap-2">
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKey}
        placeholder={PLACEHOLDERS[dataset]}
        disabled={disabled}
        className="flex-1"
      />
      <Button onClick={submit} disabled={disabled || !value.trim()}>
        {disabled ? (
          <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
        ) : (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M5 12h14" />
            <path d="m12 5 7 7-7 7" />
          </svg>
        )}
      </Button>
    </div>
  );
}
