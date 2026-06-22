import type { IngestResponse, ChatResponse, Message } from "../types";

const API_BASE = "http://127.0.0.1:8000/api";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();

    console.error("API Error:", {
      status: response.status,
      statusText: response.statusText,
      body: errorText,
    });

    throw new Error(`API Error ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

export async function ingestPage(
  url: string,
  domain: string,
  title: string,
  content: string,
): Promise<IngestResponse> {
  try {
    console.log("Sending ingest request...");

    const response = await fetch(`${API_BASE}/ingest`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        url,
        domain,
        title,
        content,
      }),
    });

    return await handleResponse<IngestResponse>(response);
  } catch (error) {
    console.error("Ingest request failed:", error);
    throw error;
  }
}

export async function askQuestion(
  url: string,
  domain: string,
  question: string,
  mode: string,
  chatHistory: Message[],
): Promise<ChatResponse> {
  try {
    console.log("Sending chat request...");

    const history = chatHistory.map((msg) => ({
      role: msg.role,
      content: msg.content,
    }));

    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        url,
        domain,
        question,
        mode,
        chat_history: history,
      }),
    });

    return await handleResponse<ChatResponse>(response);
  } catch (error) {
    console.error("Chat request failed:", error);
    throw error;
  }
}
