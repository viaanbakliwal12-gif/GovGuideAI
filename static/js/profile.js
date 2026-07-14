document.querySelectorAll("[data-confirm], [data-confirm-key]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    const key = form.getAttribute("data-confirm-key");
    const message = form.getAttribute("data-confirm") || (key && window.GovGuideI18n?.t(key));
    if (message && !window.confirm(message)) {
      event.preventDefault();
    }
  });
});

const occupationSelect = document.querySelector("#occupationSelect");
const occupationCustomLabel = document.querySelector("#occupationCustomLabel");

function updateOccupationCustomField() {
  if (!occupationSelect || !occupationCustomLabel) {
    return;
  }
  const isOther = occupationSelect.value === "other";
  occupationCustomLabel.hidden = !isOther;
  const input = occupationCustomLabel.querySelector("input");
  if (input) {
    input.disabled = !isOther;
  }
}

occupationSelect?.addEventListener("change", updateOccupationCustomField);
updateOccupationCustomField();
