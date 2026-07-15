function t(key) {
  return window.GovGuideI18n?.t(key) || key;
}

document.querySelectorAll("input[type='password']").forEach((input) => {
  input.addEventListener("input", () => {
    input.setCustomValidity("");
    if (input.validity.tooShort) {
      input.setCustomValidity(t("passwordMinimum"));
    }
  });
});

const authTabs = document.querySelectorAll("[data-auth-tab]");
const authPanels = document.querySelectorAll("[data-auth-panel]");
const authChannel = document.querySelector("[data-auth-channel]");

function setAuthMode(mode, focusPanel = false) {
  const selectedMode = mode === "phone" ? "phone" : "email";
  authTabs.forEach((tab) => {
    const selected = tab.dataset.authTab === selectedMode;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });
  authPanels.forEach((panel) => {
    const selected = panel.dataset.authPanel === selectedMode;
    panel.hidden = !selected;
    panel.querySelectorAll("input, select").forEach((field) => {
      field.disabled = !selected;
    });
    if (selected && focusPanel) {
      panel.querySelector("input:not([type='hidden']), select")?.focus();
    }
  });
  if (authChannel) authChannel.value = selectedMode;
}

authTabs.forEach((tab, index) => {
  tab.addEventListener("click", () => setAuthMode(tab.dataset.authTab, true));
  tab.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
    event.preventDefault();
    const offset = event.key === "ArrowRight" ? 1 : -1;
    const target = authTabs[(index + offset + authTabs.length) % authTabs.length];
    setAuthMode(target.dataset.authTab, true);
    target.focus();
  });
});

if (authTabs.length) {
  const selected = [...authTabs].find((tab) => tab.getAttribute("aria-selected") === "true");
  setAuthMode(selected?.dataset.authTab || "email");
}

document.querySelectorAll("[data-auth-code-form]").forEach((form) => {
  form.addEventListener("submit", () => {
    const button = form.querySelector("button[type='submit']");
    if (button) {
      button.disabled = true;
      button.textContent = t("sendingCode");
    }
  });
});

const otpInput = document.querySelector("#otpCode");
otpInput?.addEventListener("input", () => {
  otpInput.value = otpInput.value.replace(/\D/g, "").slice(0, 6);
  otpInput.setCustomValidity(otpInput.value.length && otpInput.value.length !== 6 ? t("sixDigitCodeRequired") : "");
});
otpInput?.addEventListener("paste", (event) => {
  const digits = event.clipboardData?.getData("text").replace(/\D/g, "").slice(0, 6);
  if (digits) {
    event.preventDefault();
    otpInput.value = digits;
    otpInput.dispatchEvent(new Event("input", { bubbles: true }));
  }
});

document.querySelectorAll("[data-resend-form]").forEach((form) => {
  const button = form.querySelector("[data-resend-button]");
  const countdown = form.querySelector("[data-countdown]");
  let remaining = Number.parseInt(form.dataset.cooldown || "0", 10) || 0;
  const render = () => {
    if (!button || !countdown) return;
    button.disabled = remaining > 0;
    countdown.textContent = remaining > 0 ? `(${remaining}s)` : "";
    if (remaining > 0) {
      remaining -= 1;
      window.setTimeout(render, 1000);
    }
  };
  render();
});
