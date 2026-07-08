"use client";

import ReactMarkdown from "react-markdown";

export default function Markdown({ content }: { content: string }) {
  return (
    <div className="prose-report">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
