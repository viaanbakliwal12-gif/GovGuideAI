const menuToggle = document.querySelector("#menuToggle");
const topActions = document.querySelector("#topActions");
const contextToggle = document.querySelector("#contextToggle");
const contextPanel = document.querySelector("#contextPanel");
const contextBackdrop = document.querySelector("#contextBackdrop");
const contextClose = document.querySelector("#contextClose");

function setMenuOpen(isOpen) {
  if (!menuToggle || !topActions) return;
  menuToggle.setAttribute("aria-expanded", String(isOpen));
  topActions.dataset.open = String(isOpen);
}

function setContextOpen(isOpen) {
  if (!contextToggle || !contextPanel) return;
  contextToggle.setAttribute("aria-expanded", String(isOpen));
  contextPanel.dataset.open = String(isOpen);
  document.body.classList.toggle("context-panel-open", isOpen);
  if (contextBackdrop) {
    contextBackdrop.hidden = !isOpen;
  }
  if (isOpen) {
    contextPanel.querySelector("a, button, select")?.focus();
  } else {
    contextToggle.focus();
  }
}

menuToggle?.addEventListener("click", () => {
  setMenuOpen(menuToggle.getAttribute("aria-expanded") !== "true");
});

contextToggle?.addEventListener("click", () => {
  setContextOpen(contextToggle.getAttribute("aria-expanded") !== "true");
});

contextBackdrop?.addEventListener("click", () => setContextOpen(false));
contextClose?.addEventListener("click", () => setContextOpen(false));

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    if (contextToggle?.getAttribute("aria-expanded") === "true") {
      setContextOpen(false);
    }
    if (menuToggle?.getAttribute("aria-expanded") === "true") {
      setMenuOpen(false);
      menuToggle.focus();
    }
  }
});

window.addEventListener("resize", () => {
  if (window.matchMedia("(min-width: 721px)").matches) {
    setMenuOpen(false);
  }
  if (window.matchMedia("(min-width: 941px)").matches && contextPanel) {
    contextPanel.dataset.open = "false";
    document.body.classList.remove("context-panel-open");
    if (contextBackdrop) contextBackdrop.hidden = true;
  }
});
