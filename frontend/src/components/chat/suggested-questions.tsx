"use client";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface Props {
  questions: string[];
  onSelect: (q: string) => void;
  variant?: "hero" | "inline";
}

const icons: Record<number, string> = {
  0: "📊",
  1: "💡",
  2: "✈️",
  3: "💳",
};

export function SuggestedQuestions({
  questions,
  onSelect,
  variant = "inline",
}: Props) {
  if (!questions.length) return null;

  if (variant === "hero") {
    return (
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {questions.map((q, i) => (
          <Card
            key={i}
            className="cursor-pointer px-4 py-3 transition-colors hover:bg-muted/60"
            onClick={() => onSelect(q)}
          >
            <div className="flex items-start gap-3">
              <span className="mt-0.5 text-lg">{icons[i] ?? "💬"}</span>
              <p className="text-sm leading-snug text-foreground/80">{q}</p>
            </div>
          </Card>
        ))}
      </div>
    );
  }

  // inline pills
  return (
    <div className="flex flex-wrap gap-2">
      {questions.map((q, i) => (
        <Button
          key={i}
          variant="outline"
          size="sm"
          className="h-auto whitespace-normal px-3 py-1.5 text-left text-xs"
          onClick={() => onSelect(q)}
        >
          {q}
        </Button>
      ))}
    </div>
  );
}
