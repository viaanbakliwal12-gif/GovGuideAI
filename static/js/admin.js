document.querySelectorAll("[data-export-form]").forEach((form) => {
  form.addEventListener("submit", () => {
    const status = document.querySelector("[data-export-status]");
    const format = form.dataset.exportFormat || "profile";
    if (status) {
      status.textContent = `Preparing ${format} download… Your browser will save it when ready.`;
    }
  });
});
