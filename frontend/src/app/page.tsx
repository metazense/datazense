"use client";

import { useState } from "react";
import { Header } from "@/components/layout/header";
import { ChatInterface } from "@/components/chat/chat-interface";
import type { Dataset } from "@/lib/types";

export default function Home() {
  const [dataset, setDataset] = useState<Dataset>("nyc_taxi");

  return (
    <div className="flex h-dvh flex-col">
      <Header dataset={dataset} onDatasetChange={setDataset} />
      <ChatInterface dataset={dataset} />
    </div>
  );
}
