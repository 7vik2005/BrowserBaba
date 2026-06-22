import { Readability } from "@mozilla/readability";

function extractLegacyContent(): string {
  try {
    const clone = document.body.cloneNode(true) as HTMLElement;

    const selectorsToRemove = [
      "script",
      "style",
      "noscript",
      "iframe",
      "svg",
      "nav",
      "footer",
      "header",
      "aside",
      "[aria-hidden='true']",
    ];

    selectorsToRemove.forEach((selector) => {
      clone.querySelectorAll(selector).forEach((el) => el.remove());
    });

    const text = clone.innerText || clone.textContent || "";
    return text.replace(/\s+/g, " ").trim();
  } catch (error) {
    console.error("Legacy content extraction failed:", error);
    return "";
  }
}

function extractPageContent(): { content: string; title: string } {
  try {
    // Clone document to preserve runtime DOM states of the visible tab
    const docClone = document.cloneNode(true) as Document;
    const reader = new Readability(docClone);
    const article = reader.parse();

    if (article && article.textContent && article.textContent.trim().length > 100) {
      console.log("BrowserBaba: Readability parsed main article body successfully.");
      return {
        content: article.textContent.replace(/\s+/g, " ").trim(),
        title: article.title || document.title,
      };
    }
  } catch (error) {
    console.error("BrowserBaba: Readability extraction failed, trying legacy fallback...", error);
  }

  // Fallback to legacy clean text logic
  const legacyText = extractLegacyContent();
  return {
    content: legacyText,
    title: document.title,
  };
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type !== "EXTRACT_CONTENT") {
    return false;
  }

  try {
    const { content, title } = extractPageContent();

    sendResponse({
      success: true,
      url: window.location.href,
      title: title || document.title,
      content,
      contentLength: content.length,
    });
  } catch (error) {
    console.error("Message handler error:", error);

    sendResponse({
      success: false,
      error: String(error),
    });
  }

  return true;
});

console.log("BrowserBaba content script loaded:", window.location.href);
