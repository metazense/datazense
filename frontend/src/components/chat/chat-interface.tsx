"use client";

import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessage } from "./chat-message";
import { ChatInput } from "./chat-input";
import { SuggestedQuestions } from "./suggested-questions";
import { useChat } from "@/hooks/use-chat";
import type { Dataset } from "@/lib/types";

const STARTER_QUESTIONS: Record<Dataset, string[]> = {
  nyc_taxi: [
    "What is total revenue by borough?",
    "Why are Manhattan tips higher than other boroughs?",
    "How do airport trips compare to regular trips?",
    "What payment methods are most common and why?",
  ],
  healthcare: [
    "What conditions drive the most cost?",
    "How do outcomes vary by demographics?",
    "Why are emergency visits more frequent for certain groups?",
    "What is the relationship between income and healthcare utilization?",
  ],
};

interface Props {
  dataset: Dataset;
}

export function ChatInterface({ dataset }: Props) {
  const { messages, isLoading, send } = useChat(dataset);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const isEmpty = messages.length === 0;
  const questions = STARTER_QUESTIONS[dataset];
  return (
    <div className="flex h-full flex-col">
      {isEmpty ? (
        /* ── Hero / empty state ──────────────────────────────────── */
        <div className="flex flex-1 flex-col items-center justify-center px-4">
          <div className="mx-auto max-w-lg text-center">
            <h2 className="font-display text-3xl font-medium tracking-tight">
              Ask your data <span className="gradient-text">WHY</span>,
              <br />
              not just <span className="text-muted-foreground">WHAT</span>
            </h2>
            <p className="mt-3 text-muted-foreground">
              Three AI layers — Technical, Semantic, and Ontology — combine
              to give you answers with real business context.
            </p>
            <div className="mt-8">
              <SuggestedQuestions
                questions={questions}
                onSelect={send}
                variant="hero"
              />
            </div>
          </div>
        </div>
      ) : (
        /* ── Chat messages ───────────────────────────────────────── */
        <ScrollArea className="flex-1 px-4 py-6">
          <div className="mx-auto max-w-3xl space-y-6">
            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                onSuggestionClick={isLoading ? undefined : send}
              />
            ))}
            <div ref={bottomRef} />
          </div>
        </ScrollArea>
      )}

      {/* ── Input bar ──────────────────────────────────────────── */}
      <div className="border-t bg-background px-4 py-3">
        <div className="mx-auto max-w-3xl">
          <ChatInput onSend={send} disabled={isLoading} dataset={dataset} />
        </div>
      </div>
    </div>
  );
}
