import React from "react";
import type { Message } from "../types";

interface Props {
  message: Message;
}

function parseMarkdown(text: string): React.ReactNode[] {
  if (!text) return [];

  // Split by code blocks first
  const blocks = text.split(/(```[\s\S]*?```)/g);
  
  return blocks.map((block, blockIdx) => {
    if (block.startsWith("```") && block.endsWith("```")) {
      const code = block.slice(3, -3).trim();
      return (
        <pre key={blockIdx} style={{ background: "rgba(0,0,0,0.25)", padding: "8px", borderRadius: "6px", overflowX: "auto", fontSize: "11px", margin: "8px 0", border: "1px solid var(--border)", fontFamily: "monospace" }}>
          <code>{code}</code>
        </pre>
      );
    }

    const lines = block.split("\n");
    let inList = false;
    let listItems: React.ReactNode[] = [];
    const elements: React.ReactNode[] = [];

    lines.forEach((line, lineIdx) => {
      const isBullet = line.trim().startsWith("- ") || line.trim().startsWith("* ");
      
      if (isBullet) {
        inList = true;
        const itemText = line.replace(/^[\s\-\*]+/, "");
        listItems.push(<li key={`li-${lineIdx}`} style={{ marginBottom: "2px" }}>{renderInlineFormatting(itemText)}</li>);
      } else {
        if (inList) {
          elements.push(
            <ul key={`ul-${lineIdx}`} style={{ paddingLeft: "18px", margin: "6px 0", listStyleType: "disc" }}>
              {listItems}
            </ul>
          );
          listItems = [];
          inList = false;
        }
        
        if (line.trim()) {
          elements.push(<p key={`p-${lineIdx}`} style={{ margin: "6px 0", lineHeight: "1.5" }}>{renderInlineFormatting(line)}</p>);
        }
      }
    });

    if (inList && listItems.length > 0) {
      elements.push(
        <ul key={`ul-end-${blockIdx}`} style={{ paddingLeft: "18px", margin: "6px 0", listStyleType: "disc" }}>
          {listItems}
        </ul>
      );
    }

    return <span key={blockIdx}>{elements}</span>;
  });
}

function renderInlineFormatting(text: string): React.ReactNode[] {
  const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={idx} style={{ color: "var(--accent)", fontWeight: "600" }}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={idx} style={{ background: "rgba(255,255,255,0.08)", padding: "2px 4px", borderRadius: "4px", fontSize: "11px", fontFamily: "monospace", border: "1px solid rgba(255,255,255,0.05)" }}>{part.slice(1, -1)}</code>;
    }
    return part;
  });
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`message ${isUser ? "message-user" : "message-ai"}`}>
      <div className="message-label">{isUser ? "You" : "BrowserBaba"}</div>
      <div className="message-content">
        {isUser ? message.content : parseMarkdown(message.content)}

        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="citations-container" style={{
            marginTop: "10px",
            paddingTop: "8px",
            borderTop: "1px solid rgba(255, 255, 255, 0.08)",
            display: "flex",
            flexDirection: "column",
            gap: "6px"
          }}>
            <div style={{ 
              fontSize: "9px", 
              fontWeight: "700", 
              textTransform: "uppercase", 
              letterSpacing: "0.8px", 
              color: "var(--text-muted)",
              marginBottom: "2px"
            }}>
              Sources
            </div>
            {message.sources.map((src, srcIdx) => (
              <a 
                key={srcIdx} 
                href={src.url} 
                target="_blank" 
                rel="noreferrer"
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  fontSize: "11px",
                  color: "var(--accent)",
                  textDecoration: "none",
                  background: "rgba(255, 255, 255, 0.02)",
                  padding: "6px 10px",
                  borderRadius: "6px",
                  border: "1px solid rgba(255, 255, 255, 0.04)",
                  transition: "all 0.2s ease"
                }}
                title={src.url}
              >
                <span style={{ 
                  overflow: "hidden", 
                  textOverflow: "ellipsis", 
                  whiteSpace: "nowrap", 
                  maxWidth: "180px", 
                  fontWeight: "500" 
                }}>
                  {src.title}
                </span>
                <span style={{ fontSize: "9px", color: "var(--text-muted)", opacity: 0.8 }}>
                  {src.score.toFixed(3)}
                </span>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
