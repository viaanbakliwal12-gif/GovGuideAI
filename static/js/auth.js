document.querySelectorAll("input[type='password']").forEach((input) => {
  input.addEventListener("input", () => {
    input.setCustomValidity("");
    if (input.validity.tooShort) {
      input.setCustomValidity("Use at least 8 characters.");
    }
  });
});
