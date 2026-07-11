const chatForm = document.querySelector("#chatForm");
const messageInput = document.querySelector("#messageInput");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#sendButton");
const clearButton = document.querySelector("#clearButton");
const promptButtons = document.querySelectorAll("[data-prompt]");

const userId = window.govGuideUserId || "guest";
const conversationKey = `govguideaiConversationId:${userId}`;
let conversationId = window.localStorage.getItem(conversationKey) || "";
let typingMessage = null;

function scrollToLatest() {
  messages.scrollTop = messages.scrollHeight;
}

function resizeInput() {
  messageInput.style.height = "auto";
  messageInput.style.height = `${messageInput.scrollHeight}px`;
}

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function linkify(text) {
  return text.replace(
    /(https?:\/\/[^\s<]+)/g,
    '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
  );
}

function formatText(text) {
  const lines = text.trim().split(/\n{2,}/);
  return lines
    .map((line) => `<p>${linkify(escapeHtml(line)).replace(/\n/g, "<br>")}</p>`)
    .join("");
}

function addMessage(role, text, toolsUsed = []) {
  const article = document.createElement("article");
  article.className = `message ${role}-message`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = role === "assistant" ? "G" : "You";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = formatText(text);

  if (toolsUsed.length > 0) {
    const toolNote = document.createElement("div");
    toolNote.className = "tool-note";
    toolNote.textContent = `Tool used: ${toolsUsed.join(", ")}`;
    bubble.appendChild(toolNote);
  }

  article.append(avatar, bubble);
  messages.appendChild(article);
  scrollToLatest();

  return article;
}

function showTyping() {
  typingMessage = addMessage("assistant", "GovGuideAI is checking this for you...");
  typingMessage.classList.add("typing");
}

function hideTyping() {
  if (typingMessage) {
    typingMessage.remove();
    typingMessage = null;
  }
}

function setBusy(isBusy) {
  sendButton.disabled = isBusy;
  messageInput.disabled = isBusy;
}

async function sendMessage(message) {
  addMessage("user", message);
  showTyping();
  setBusy(true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        conversationId,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Something went wrong.");
    }

    conversationId = data.conversationId;
    window.localStorage.setItem(conversationKey, conversationId);
    hideTyping();
    addMessage("assistant", data.answer, data.toolsUsed || []);
  } catch (error) {
    hideTyping();
    addMessage("assistant", error.message);
  } finally {
    setBusy(false);
    messageInput.focus();
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();

  const message = messageInput.value.trim();
  if (!message) {
    return;
  }

  messageInput.value = "";
  resizeInput();
  sendMessage(message);
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
  window.localStorage.removeItem(conversationKey);
  messages.innerHTML = "";
  addMessage("assistant", "Conversation memory is cleared. Please ask your next question.");
  messageInput.focus();
});

promptButtons.forEach((button) => {
  button.addEventListener("click", () => {
    messageInput.value = button.dataset.prompt;
    resizeInput();
    messageInput.focus();
  });
});

resizeInput();
