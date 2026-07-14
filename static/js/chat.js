const chatForm = document.querySelector("#chatForm");
const messageInput = document.querySelector("#messageInput");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#sendButton");
const clearButton = document.querySelector("#clearButton");
const promptButtons = document.querySelectorAll("[data-prompt]");
const chatStatus = document.querySelector("#chatStatus");
const chatStatusText = document.querySelector("#chatStatusText");
const chatEmptyState = document.querySelector("#chatEmptyState");

const userId = window.govGuideUserId || "guest";
const conversationKey = `govguideaiConversationId:${userId}`;
let conversationId = window.localStorage.getItem(conversationKey) || "";
let hasConversationMessages = false;

function t(key) {
  return window.GovGuideI18n?.t(key) || key;
}

function selectedLanguage() {
  return window.GovGuideI18n?.getLanguage() || window.govGuideProfileLanguage || "en";
}

function scrollToLatest() {
  messages.scrollTop = messages.scrollHeight;
}

function resizeInput() {
  messageInput.style.height = "auto";
  messageInput.style.height = `${Math.min(messageInput.scrollHeight, 180)}px`;
}

function resetComposer() {
  messageInput.value = "";
  resizeInput();
}

function setChatEmptyState(isVisible) {
  if (chatEmptyState) {
    chatEmptyState.hidden = !isVisible;
  }
}

function setChatStatus(status) {
  if (!chatStatus || !chatStatusText) {
    return;
  }
  if (!status) {
    chatStatus.hidden = true;
    chatStatus.dataset.status = "idle";
    return;
  }
  const labels = {
    sending: "sending",
    thinking: "thinking",
    web_search: "searchingWeb",
    official_sources: "checkingSources",
    preparing: "preparingResponse",
  };
  chatStatus.hidden = false;
  chatStatus.dataset.status = status;
  chatStatusText.textContent = t(labels[status] || "thinking");
}

function setBusy(isBusy) {
  sendButton.disabled = isBusy;
  messageInput.disabled = isBusy;
}

function isSafeHttpUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function normalizeUrlToken(token) {
  return token.replace(/[),.;\]]+$/g, "");
}

function extractUrls(text) {
  const urls = new Set();
  const matches = text.match(/https?:\/\/[^\s<>"']+/g) || [];
  matches.forEach((match) => {
    const url = normalizeUrlToken(match);
    if (isSafeHttpUrl(url)) {
      urls.add(url);
    }
  });
  return [...urls];
}

function appendInlineText(parent, text) {
  const urlPattern = /(https?:\/\/[^\s<>"']+)/g;
  let cursor = 0;
  let match;

  while ((match = urlPattern.exec(text)) !== null) {
    appendEmphasis(parent, text.slice(cursor, match.index));
    const rawUrl = normalizeUrlToken(match[0]);
    const trailing = match[0].slice(rawUrl.length);
    if (isSafeHttpUrl(rawUrl)) {
      const link = document.createElement("a");
      link.href = rawUrl;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = readableUrlLabel(rawUrl);
      parent.appendChild(link);
    } else {
      parent.appendChild(document.createTextNode(match[0]));
    }
    if (trailing) {
      parent.appendChild(document.createTextNode(trailing));
    }
    cursor = match.index + match[0].length;
  }

  appendEmphasis(parent, text.slice(cursor));
}

function appendEmphasis(parent, text) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  parts.forEach((part) => {
    if (!part) {
      return;
    }
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      const strong = document.createElement("strong");
      strong.textContent = part.slice(2, -2);
      parent.appendChild(strong);
    } else {
      parent.appendChild(document.createTextNode(part));
    }
  });
}

function readableUrlLabel(value) {
  try {
    const url = new URL(value);
    return url.hostname.replace(/^www\./, "");
  } catch {
    return value;
  }
}

function appendParagraph(container, lines) {
  const text = lines.join(" ").trim();
  if (!text) {
    return;
  }
  const paragraph = document.createElement("p");
  appendInlineText(paragraph, text);
  container.appendChild(paragraph);
}

function appendList(container, items, ordered = false) {
  if (!items.length) {
    return;
  }
  const list = document.createElement(ordered ? "ol" : "ul");
  items.forEach((item) => {
    const li = document.createElement("li");
    appendInlineText(li, item);
    list.appendChild(li);
  });
  container.appendChild(list);
}

function appendAdvisory(container, line) {
  const note = document.createElement("div");
  note.className = "answer-note";
  appendInlineText(note, line);
  container.appendChild(note);
}

function renderAssistantContent(text) {
  const content = document.createElement("div");
  content.className = "message-content assistant-content";

  const lines = String(text || "").replace(/\r\n/g, "\n").split("\n");
  let paragraphLines = [];
  let listItems = [];
  let orderedItems = [];

  const flush = () => {
    appendParagraph(content, paragraphLines);
    paragraphLines = [];
    appendList(content, listItems, false);
    listItems = [];
    appendList(content, orderedItems, true);
    orderedItems = [];
  };

  lines.forEach((rawLine) => {
    const line = rawLine.trim();
    if (!line) {
      flush();
      return;
    }

    const heading = line.match(/^#{1,3}\s+(.+)$/);
    const bullet = line.match(/^[-*•]\s+(.+)$/);
    const numbered = line.match(/^\d+[.)]\s+(.+)$/);
    const shortHeading = line.match(/^([A-Z][A-Za-z0-9 /&-]{2,48}):$/);
    const advisory = line.match(/^(Important|Note|Warning|Caution):\s+(.+)$/i);

    if (heading || shortHeading || advisory) {
      flush();
    }

    if (heading) {
      const h = document.createElement("h3");
      appendInlineText(h, heading[1]);
      content.appendChild(h);
      return;
    }

    if (shortHeading) {
      const h = document.createElement("h3");
      h.textContent = shortHeading[1];
      content.appendChild(h);
      return;
    }

    if (advisory) {
      appendAdvisory(content, line);
      return;
    }

    if (bullet) {
      appendParagraph(content, paragraphLines);
      paragraphLines = [];
      appendList(content, orderedItems, true);
      orderedItems = [];
      listItems.push(bullet[1]);
      return;
    }

    if (numbered) {
      appendParagraph(content, paragraphLines);
      paragraphLines = [];
      appendList(content, listItems, false);
      listItems = [];
      orderedItems.push(numbered[1]);
      return;
    }

    paragraphLines.push(line);
  });

  flush();

  if (!content.childElementCount) {
    const paragraph = document.createElement("p");
    paragraph.textContent = text || "";
    content.appendChild(paragraph);
  }

  return content;
}

function renderUserContent(text) {
  const content = document.createElement("div");
  content.className = "message-content user-content";
  String(text || "").split(/\n{2,}/).forEach((block) => {
    const paragraph = document.createElement("p");
    paragraph.textContent = block.trim();
    if (paragraph.textContent) {
      content.appendChild(paragraph);
    }
  });
  return content;
}

function toolLabel(tool) {
  const normalized = String(tool || "").toLowerCase().replace(/[_-]/g, " ");
  if (normalized.includes("web")) return "Web Search";
  if (normalized.includes("scheme")) return "Scheme Search";
  if (normalized.includes("word")) return "Word Count";
  return String(tool || "").replace(/[_-]/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function renderToolBadges(toolsUsed = []) {
  if (!toolsUsed.length) {
    return null;
  }
  const row = document.createElement("div");
  row.className = "tool-badge-row";
  row.setAttribute("aria-label", t("toolUsed"));
  toolsUsed.forEach((tool) => {
    const badge = document.createElement("span");
    badge.className = "tool-badge";
    badge.textContent = toolLabel(tool);
    row.appendChild(badge);
  });
  return row;
}

function sourceFromUrl(url) {
  return {
    url,
    label: readableUrlLabel(url),
  };
}

function renderSources(answerText, explicitSources = []) {
  const sources = [...explicitSources];
  extractUrls(answerText).forEach((url) => {
    if (!sources.some((source) => source.url === url)) {
      sources.push(sourceFromUrl(url));
    }
  });

  const safeSources = sources.filter((source) => source?.url && isSafeHttpUrl(source.url));
  if (!safeSources.length) {
    return null;
  }

  const section = document.createElement("section");
  section.className = "source-section";
  section.setAttribute("aria-label", t("sourceSection"));

  const title = document.createElement("h4");
  title.textContent = t("sourceSection");
  section.appendChild(title);

  const list = document.createElement("div");
  list.className = "source-list";
  safeSources.forEach((source) => {
    const card = document.createElement("a");
    card.className = "source-card";
    card.href = source.url;
    card.target = "_blank";
    card.rel = "noopener noreferrer";

    const label = document.createElement("span");
    label.className = "source-label";
    label.textContent = source.label || readableUrlLabel(source.url);

    const meta = document.createElement("span");
    meta.className = "source-meta";
    meta.textContent = source.lastVerified
      ? `${t("officialSource")} • ${t("lastVerified")}: ${source.lastVerified}`
      : t("officialSource");

    const action = document.createElement("span");
    action.className = "source-action";
    action.textContent = t("openOfficialPortal");

    card.append(label, meta, action);
    list.appendChild(card);
  });

  section.appendChild(list);
  return section;
}

function appendDetail(card, label, value) {
  if (!value || (Array.isArray(value) && value.length === 0)) {
    return;
  }
  const details = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = label;
  details.appendChild(summary);

  if (Array.isArray(value)) {
    const list = document.createElement("ul");
    value.forEach((item) => {
      const li = document.createElement("li");
      appendInlineText(li, String(item));
      list.appendChild(li);
    });
    details.appendChild(list);
  } else {
    const paragraph = document.createElement("p");
    appendInlineText(paragraph, String(value));
    details.appendChild(paragraph);
  }
  card.appendChild(details);
}

function renderSchemeCards(schemes = []) {
  if (!Array.isArray(schemes) || !schemes.length) {
    return null;
  }
  const grid = document.createElement("div");
  grid.className = "scheme-card-grid";

  schemes.forEach((scheme) => {
    const card = document.createElement("article");
    card.className = "scheme-card";

    const title = document.createElement("h4");
    title.textContent = scheme.name || scheme.title || "Scheme";
    card.appendChild(title);

    ["matchReason", "whyItMatches", "benefitSummary", "keyEligibility"].forEach((key) => {
      if (scheme[key]) {
        const paragraph = document.createElement("p");
        appendInlineText(paragraph, String(scheme[key]));
        card.appendChild(paragraph);
      }
    });

    appendDetail(card, "Eligibility", scheme.eligibility || scheme.fullEligibility);
    appendDetail(card, "Documents", scheme.documents || scheme.requiredDocuments);
    appendDetail(card, "Application steps", scheme.applicationSteps || scheme.steps);

    const schemeUrl = scheme.officialSource || scheme.sourceUrl;
    if (schemeUrl && isSafeHttpUrl(schemeUrl)) {
      const link = document.createElement("a");
      link.className = "scheme-source-button";
      link.href = schemeUrl;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = t("openOfficialPortal");
      card.appendChild(link);
    }

    if (scheme.lastVerified) {
      const verified = document.createElement("p");
      verified.className = "scheme-verified";
      verified.textContent = `${t("lastVerified")}: ${scheme.lastVerified}`;
      card.appendChild(verified);
    }

    grid.appendChild(card);
  });

  return grid;
}

function renderMessage(role, text, options = {}) {
  const article = document.createElement("article");
  article.className = `message ${role}-message`;
  if (options.variant) {
    article.classList.add(`${options.variant}-message`);
  }

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = role === "assistant" ? "G" : "You";

  const body = document.createElement("div");
  body.className = "message-body";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.appendChild(role === "assistant" ? renderAssistantContent(text) : renderUserContent(text));
  body.appendChild(bubble);

  if (role === "assistant") {
    const schemes = renderSchemeCards(options.schemes || []);
    if (schemes) {
      body.appendChild(schemes);
    }

    const footer = document.createElement("div");
    footer.className = "message-footer";
    const sources = renderSources(text, options.sources || []);
    const tools = renderToolBadges(options.toolsUsed || []);
    if (sources) footer.appendChild(sources);
    if (tools) footer.appendChild(tools);
    body.appendChild(footer);
  }

  article.append(avatar, body);
  messages.appendChild(article);

  if (role === "assistant" && !options.variant && window.GovGuideVoice?.enhanceAssistantMessage) {
    window.GovGuideVoice.enhanceAssistantMessage(article, text);
  }

  hasConversationMessages = true;
  setChatEmptyState(false);
  scrollToLatest();
  return article;
}

function addMessage(role, text, toolsUsed = [], options = {}) {
  return renderMessage(role, text, { ...options, toolsUsed });
}

function showSystemNotice(text, variant = "notice") {
  return renderMessage("assistant", text, { variant });
}

function parseChatStreamLine(line, currentResult) {
  if (!line.trim()) {
    return currentResult;
  }

  const event = JSON.parse(line);
  if (event.type === "status") {
    setChatStatus(event.status);
  } else if (event.type === "error") {
    throw new Error(event.error || "Something went wrong.");
  } else if (event.type === "result") {
    return event;
  }

  return currentResult;
}

async function readChatStream(response) {
  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("This browser could not read the chat response.");
  }

  const decoder = new TextDecoder();
  let buffer = "";
  let result = null;

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });

    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    lines.forEach((line) => {
      result = parseChatStreamLine(line, result);
    });

    if (done) {
      break;
    }
  }

  result = parseChatStreamLine(buffer, result);
  if (!result) {
    throw new Error("GovGuideAI did not return a completed response.");
  }
  return result;
}

async function sendMessage(message) {
  renderMessage("user", message);
  setBusy(true);
  setChatStatus("thinking");

  try {
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        conversationId,
        selectedLanguage: selectedLanguage(),
      }),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || "Something went wrong.");
    }
    const data = await readChatStream(response);

    conversationId = data.conversationId;
    window.localStorage.setItem(conversationKey, conversationId);
    const article = renderMessage("assistant", data.answer, {
      toolsUsed: data.toolsUsed || [],
      sources: data.sources || [],
      schemes: data.schemes || [],
    });

    return { answer: data.answer, article };
  } catch (error) {
    showSystemNotice(error.message, "error");
    throw error;
  } finally {
    setBusy(false);
    setChatStatus("");
    messageInput.focus();
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();

  const message = messageInput.value.trim();
  if (!message) {
    return;
  }

  resetComposer();
  setChatStatus("sending");
  sendMessage(message).catch(() => {});
});

messageInput.addEventListener("input", resizeInput);

messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

clearButton.addEventListener("click", async () => {
  if (conversationId) {
    await fetch("/api/clear", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ conversationId }),
    });
  }

  conversationId = "";
  hasConversationMessages = false;
  window.localStorage.removeItem(conversationKey);
  window.GovGuideVoice?.clearSpeechCache?.();
  messages.querySelectorAll(".message").forEach((message) => message.remove());
  setChatEmptyState(true);
  setChatStatus("");
  messageInput.focus();
});

promptButtons.forEach((button) => {
  button.addEventListener("click", () => {
    messageInput.value = button.dataset.prompt;
    resizeInput();
    messageInput.focus();
  });
});

window.addEventListener("govguideai:languagechange", () => {
  document.querySelectorAll("[data-language-name]").forEach((element) => {
    const option = window.GovGuideI18n?.languageOptions.find((item) => item.code === selectedLanguage());
    element.textContent = option?.name || "English";
  });
  document.querySelectorAll("[data-occupation-value]").forEach((element) => {
    const key = element.dataset.occupationValue?.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
    if (key && window.GovGuideI18n?.t(key)) {
      element.textContent = window.GovGuideI18n.t(key);
    }
  });
});

resizeInput();
setChatEmptyState(!hasConversationMessages);
window.dispatchEvent(new CustomEvent("govguideai:languagechange"));

window.GovGuideChat = {
  addMessage,
  renderMessage,
  renderAssistantContent,
  renderSources,
  renderToolBadges,
  selectedLanguage,
  sendMessage,
  setChatStatus,
  resetComposer,
  showSystemNotice,
};
