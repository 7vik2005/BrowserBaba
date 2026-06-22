import { useState, useEffect } from "react";
import ChatWindow from "./ChatWindow";
import { ingestPage } from "../services/api";
import type { Message, PageInfo } from "../types";
import "../styles/popup.css";

type Status = "idle" | "extracting" | "ingesting" | "ready" | "error";

export default function App() {
  const [status, setStatus] = useState<Status>("idle");
  const [pageInfo, setPageInfo] = useState<PageInfo | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [error, setError] = useState("");
  const [chunksStored, setChunksStored] = useState(0);
  const [currentUrl, setCurrentUrl] = useState<string | null>(null);
  const [mode, setMode] = useState<"page" | "website">("page");

  // Query active tab URL on mount and restore state from local storage
  useEffect(() => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tab = tabs[0];
      if (tab?.url) {
        setCurrentUrl(tab.url);
        const urlKey = `baba_tab_${tab.url}`;
        chrome.storage.local.get([urlKey], (res) => {
          const saved = res[urlKey];
          if (saved) {
            setStatus(saved.status || "idle");
            setPageInfo(saved.pageInfo || null);
            setMessages(saved.messages || []);
            setChunksStored(saved.chunksStored || 0);
            setMode(saved.mode || "page");
          }
        });
      }
    });
  }, []);

  // Persist state to local storage whenever status, pageInfo, messages, or chunks change
  useEffect(() => {
    if (!currentUrl) return;
    const urlKey = `baba_tab_${currentUrl}`;
    chrome.storage.local.set({
      [urlKey]: {
        status,
        pageInfo,
        messages,
        chunksStored,
        mode,
      },
    });
  }, [status, pageInfo, messages, chunksStored, currentUrl, mode]);

  const extractContent = () => {
    setStatus("extracting");
    setError("");

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tab = tabs[0];
      if (!tab?.id) {
        setError("No active tab found");
        setStatus("error");
        return;
      }

      chrome.tabs.sendMessage(tab.id, { type: "EXTRACT_CONTENT" }, (response) => {
        if (chrome.runtime.lastError || !response) {
          setError("Could not extract page content. Try refreshing the page.");
          setStatus("error");
          return;
        }

        // Align currentUrl and save response
        if (response.url) {
          setCurrentUrl(response.url);
        }
        setPageInfo(response);
        handleIngest(response);
      });
    });
  };

  const handleIngest = async (info: PageInfo) => {
    setStatus("ingesting");
    try {
      const domain = new URL(info.url).hostname;
      const result = await ingestPage(info.url, domain, info.title, info.content);
      setChunksStored(result.chunks_stored);
      setStatus("ready");
    } catch {
      setError("Backend not reachable. Make sure it's running on 127.0.0.1:8000");
      setStatus("error");
    }
  };

  const truncate = (str: string, len: number) =>
    str.length > len ? str.slice(0, len) + "..." : str;

  return (
    <div className="app">
      <div className="header">
        <div className="logo">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 16v-4" />
            <path d="M12 8h.01" />
          </svg>
          <span>BrowserBaba</span>
        </div>
        <div className={`status-dot ${status === "ready" ? "active" : ""}`} />
      </div>

      {status === "idle" && (
        <div className="start-screen">
          <p>Analyze the current page with AI</p>
          <button className="btn-primary" onClick={extractContent}>
            Scan Page
          </button>
        </div>
      )}

      {status === "extracting" && (
        <div className="loading-screen">
          <div className="spinner" />
          <p>Extracting content...</p>
        </div>
      )}

      {status === "ingesting" && (
        <div className="loading-screen">
          <div className="spinner" />
          <p>Processing page...</p>
        </div>
      )}

      {status === "error" && (
        <div className="error-screen">
          <p className="error-text">{error}</p>
          <button className="btn-primary" onClick={extractContent}>
            Retry
          </button>
        </div>
      )}

      {status === "ready" && pageInfo && (
        <>
          <div className="page-info">
            <span className="page-title" title={pageInfo.title}>{truncate(pageInfo.title, 24)}</span>
            <select 
              className="mode-select" 
              value={mode} 
              onChange={(e) => setMode(e.target.value as "page" | "website")}
              style={{
                background: "rgba(255, 255, 255, 0.05)",
                border: "1px solid var(--border)",
                borderRadius: "6px",
                color: "var(--text)",
                padding: "2px 6px",
                fontSize: "11px",
                outline: "none",
                cursor: "pointer"
              }}
            >
              <option value="page" style={{ background: "#1c1c1e" }}>Page Mode</option>
              <option value="website" style={{ background: "#1c1c1e" }}>Website Mode</option>
            </select>
            <span className="page-meta">{chunksStored} chunks</span>
          </div>
          <ChatWindow url={pageInfo.url} mode={mode} messages={messages} setMessages={setMessages} />
        </>
      )}
    </div>
  );
}
