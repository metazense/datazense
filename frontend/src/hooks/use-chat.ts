"use client";

import { useCallback, useEffect, useState } from "react";
import { sendMessage } from "@/lib/api";
import type { Dataset, Message } from "@/lib/types";

let nextId = 0;
function uid() {
  return `msg-${++nextId}-${Date.now()}`;
}

export function useChat(dataset: Dataset = "nyc_taxi") {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Reset messages when dataset changes
  useEffect(() => {
    setMessages([]);
  }, [dataset]);

  const send = useCallback(
    async (content: string) => {
      const userMsg: Message = { id: uid(), role: "user", content };
      const placeholderId = uid();
      const placeholder: Message = {
        id: placeholderId,
        role: "assistant",
        content: "",
        isLoading: true,
      };

      setMessages((prev) => [...prev, userMsg, placeholder]);
      setIsLoading(true);

      try {
        const data = await sendMessage(content, dataset);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === placeholderId
              ? { ...m, content: data.answer, data, isLoading: false }
              : m,
          ),
        );
      } catch (err) {
        const errMsg = err instanceof Error ? err.message : "Unknown error";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === placeholderId
              ? {
                  ...m,
                  content: "Sorry, something went wrong. Please try again.",
                  data: {
                    answer: "Sorry, something went wrong. Please try again.",
                    chart: null,
                    table: null,
                    insights: [],
                    sources: [],
                    tools_used: [],
                    suggestions: [],
                    error: errMsg,
                  },
                  isLoading: false,
                }
              : m,
          ),
        );
      } finally {
        setIsLoading(false);
      }
    },
    [dataset],
  );

  const reset = useCallback(() => {
    setMessages([]);
  }, []);

  return { messages, isLoading, send, reset };
}
