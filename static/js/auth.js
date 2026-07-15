function authText(key, fallback) {
  return window.GovGuideI18n?.t(key) || fallback;
}

function clearFieldError(field) {
  field.setCustomValidity("");
  field.removeAttribute("aria-invalid");
  const label = field.closest("label");
  label?.querySelectorAll("[data-auth-error]").forEach((error) => error.remove());
  document.querySelectorAll(".notice[data-auth-error]").forEach((error) => error.remove());
}

document.querySelectorAll("[data-auth-field]").forEach((field) => {
  field.addEventListener("input", () => clearFieldError(field));
  field.addEventListener("change", () => clearFieldError(field));
});

document.querySelectorAll("[data-signup-form]").forEach((form) => {
  const password = form.querySelector("[data-new-password]");
  const confirmation = form.querySelector("[data-confirm-password]");

  const validatePassword = () => {
    if (!password) return;
    password.setCustomValidity("");
    if (password.value.length > 0 && password.value.length < 10) {
      password.setCustomValidity(
        authText("passwordMinimum", "Use at least 10 characters.")
      );
    } else if (
      password.value.length > 0 &&
      (!/[A-Za-z]/.test(password.value) || !/\d/.test(password.value))
    ) {
      password.setCustomValidity(
        authText("passwordLetterNumber", "Include at least one letter and one number.")
      );
    }
  };

  const validateConfirmation = () => {
    if (!confirmation || !password) return;
    confirmation.setCustomValidity(
      confirmation.value && confirmation.value !== password.value
        ? authText("passwordMismatch", "Passwords do not match.")
        : ""
    );
  };

  password?.addEventListener("input", () => {
    validatePassword();
    validateConfirmation();
  });
  confirmation?.addEventListener("input", validateConfirmation);
  form.addEventListener("submit", () => {
    validatePassword();
    validateConfirmation();
  });
});
