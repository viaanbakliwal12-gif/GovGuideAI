(() => {
  "use strict";

  const otpLogin = document.querySelector("[data-otp-login]");
  const logoutForms = [...document.querySelectorAll("form[data-supabase-logout]")];
  const accountDeleteForms = [
    ...document.querySelectorAll("form[data-supabase-delete-account]"),
  ];
  const protectedPage = document.body.matches("[data-supabase-protected]");
  const csrfToken = document.querySelector("meta[name='csrf-token']")?.content || "";
  let supabaseClient = null;
  let resendTimer = null;
  let logoutInProgress = false;

  function authText(key, fallback) {
    return window.GovGuideI18n?.t(key) || fallback;
  }

  function setStatus(message, kind = "error") {
    const status = otpLogin?.querySelector("[data-auth-status]");
    if (!status) return;
    status.textContent = message;
    status.classList.toggle("error", kind === "error");
    status.classList.toggle("success", kind === "success");
    status.hidden = false;
  }

  function clearStatus() {
    const status = otpLogin?.querySelector("[data-auth-status]");
    if (!status) return;
    status.hidden = true;
    status.textContent = "";
    status.classList.remove("error", "success");
  }

  function setBusy(button, busy, busyText) {
    if (!button) return;
    if (busy) {
      button.dataset.originalHtml = button.innerHTML;
      button.textContent = busyText;
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
      return;
    }
    if (button.dataset.originalHtml) button.innerHTML = button.dataset.originalHtml;
    button.disabled = false;
    button.removeAttribute("aria-busy");
  }

  async function createSupabaseClient() {
    if (supabaseClient) return supabaseClient;
    if (!window.supabase?.createClient) {
      throw new Error(
        authText(
          "supabaseLibraryError",
          "The Supabase login library could not load. Check your network and refresh."
        )
      );
    }

    let response;
    try {
      response = await fetch("/api/auth/config", {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
    } catch {
      throw new Error(
        authText("networkError", "Network error. Check your connection and try again.")
      );
    }
    const config = await response.json().catch(() => ({}));
    if (
      !response.ok ||
      !config.SUPABASE_URL ||
      !config.SUPABASE_ANON_KEY
    ) {
      throw new Error(
        authText(
          "supabaseConfigError",
          "Supabase login is not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY on the server."
        )
      );
    }

    supabaseClient = window.supabase.createClient(
      config.SUPABASE_URL,
      config.SUPABASE_ANON_KEY,
      {
        auth: {
          persistSession: true,
          autoRefreshToken: true,
          detectSessionInUrl: true,
        },
      }
    );
    supabaseClient.auth.onAuthStateChange((event) => {
      if (event === "SIGNED_OUT" && protectedPage && !logoutInProgress) {
        window.setTimeout(clearServerSession, 0);
      }
    });
    window.govGuideSupabase = supabaseClient;
    return supabaseClient;
  }

  function errorMessage(error, action) {
    const raw = String(error?.message || "").toLowerCase();
    const status = Number(error?.status || 0);
    const code = String(error?.code || "").toLowerCase();
    if (status === 429 || raw.includes("rate limit") || raw.includes("too many")) {
      return authText(
        "otpRateLimited",
        "Too many code requests. Wait a minute, then try again."
      );
    }
    if (
      action === "verify" &&
      (code.includes("expired") || raw.includes("expired"))
    ) {
      return authText(
        "otpExpired",
        "That OTP has expired. Request a new code and try again."
      );
    }
    if (
      action === "verify" &&
      (status === 400 || status === 403 || raw.includes("invalid") || raw.includes("token"))
    ) {
      return authText(
        "otpInvalid",
        "That OTP is incorrect or no longer valid. Check the code or request a new one."
      );
    }
    if (raw.includes("email") && (raw.includes("invalid") || status === 422)) {
      return authText("invalidEmail", "Enter a valid email address.");
    }
    if (
      error instanceof TypeError ||
      raw.includes("fetch") ||
      raw.includes("network") ||
      raw.includes("connection")
    ) {
      return authText("networkError", "Network error. Check your connection and try again.");
    }
    if (action === "logout") {
      return authText("logoutError", "Logout failed. Check your connection and try again.");
    }
    return action === "verify"
      ? authText("otpVerifyError", "The OTP could not be verified. Please try again.")
      : authText("otpSendError", "The OTP could not be sent. Please try again.");
  }

  async function syncServerSession(session) {
    if (!session?.access_token) {
      throw new Error(authText("sessionMissing", "Supabase did not return a valid session."));
    }
    const next = document.body.dataset.authNext || "";
    const selectedLanguage = document.body.dataset.selectedLanguage || "en";
    let response;
    try {
      response = await fetch("/api/auth/session", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-CSRF-Token": csrfToken,
        },
        body: JSON.stringify({
          access_token: session.access_token,
          selected_language: selectedLanguage,
          next,
        }),
      });
    } catch {
      throw new Error(
        authText("networkError", "Network error. Check your connection and try again.")
      );
    }
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(
        payload.error ||
          authText("sessionSyncError", "GovGuideAI could not start your website session.")
      );
    }
    return payload.next || "/chat";
  }

  function startResendCooldown() {
    const resendButton = otpLogin?.querySelector("[data-resend-otp]");
    const countdown = otpLogin?.querySelector("[data-resend-countdown]");
    if (!resendButton || !countdown) return;
    window.clearInterval(resendTimer);
    const availableAt = Date.now() + 60_000;
    resendButton.disabled = true;

    const tick = () => {
      const seconds = Math.max(0, Math.ceil((availableAt - Date.now()) / 1000));
      countdown.textContent = seconds > 0 ? ` (${seconds}s)` : "";
      resendButton.disabled = seconds > 0;
      if (seconds === 0) window.clearInterval(resendTimer);
    };
    tick();
    resendTimer = window.setInterval(tick, 1000);
  }

  function showOtpStep(email) {
    const emailForm = otpLogin.querySelector("[data-email-form]");
    const otpStep = otpLogin.querySelector("[data-otp-step]");
    const emailDisplay = otpLogin.querySelector("[data-otp-email]");
    emailForm.hidden = true;
    otpStep.hidden = false;
    emailDisplay.textContent = email;
    otpLogin.querySelector("[data-otp-input]")?.focus();
  }

  function changeEmail() {
    const emailForm = otpLogin.querySelector("[data-email-form]");
    const otpStep = otpLogin.querySelector("[data-otp-step]");
    const otpInput = otpLogin.querySelector("[data-otp-input]");
    window.clearInterval(resendTimer);
    otpInput.value = "";
    otpStep.hidden = true;
    emailForm.hidden = false;
    clearStatus();
    otpLogin.querySelector("[data-auth-email]")?.focus();
  }

  async function sendOtp(email, button, isResend = false) {
    let sent = false;
    setBusy(
      button,
      true,
      authText(isResend ? "resendingOtp" : "sendingOtp", isResend ? "Resending..." : "Sending...")
    );
    clearStatus();
    try {
      const supabase = await createSupabaseClient();
      const { error } = await supabase.auth.signInWithOtp({
        email: email,
        options: {
          shouldCreateUser: true,
        },
      });
      if (error) throw error;
      showOtpStep(email);
      sent = true;
      setStatus(
        authText(
          isResend ? "otpResent" : "otpSent",
          isResend
            ? "A new six-digit OTP was sent. Check your email."
            : "OTP sent. Check your email for the six-digit code."
        ),
        "success"
      );
    } catch (error) {
      setStatus(errorMessage(error, "send"));
    } finally {
      setBusy(button, false);
    }
    if (sent) startResendCooldown();
  }

  async function verifyOtp(email, otp, button) {
    setBusy(button, true, authText("verifyingOtp", "Verifying..."));
    clearStatus();
    try {
      const supabase = await createSupabaseClient();
      const { data, error } = await supabase.auth.verifyOtp({
        email: email,
        token: otp,
        type: "email",
      });
      if (error) throw error;
      setStatus(authText("otpVerified", "OTP verified. Opening GovGuideAI..."), "success");
      const next = await syncServerSession(data.session);
      window.location.replace(next);
    } catch (error) {
      setStatus(errorMessage(error, "verify"));
      setBusy(button, false);
      otpLogin.querySelector("[data-otp-input]")?.focus();
    }
  }

  function setupOtpLogin() {
    const emailForm = otpLogin.querySelector("[data-email-form]");
    const verifyForm = otpLogin.querySelector("[data-verify-form]");
    const emailInput = otpLogin.querySelector("[data-auth-email]");
    const otpInput = otpLogin.querySelector("[data-otp-input]");
    const sendButton = otpLogin.querySelector("[data-send-otp]");
    const verifyButton = otpLogin.querySelector("[data-verify-otp]");
    const resendButton = otpLogin.querySelector("[data-resend-otp]");

    emailForm.addEventListener("submit", (event) => {
      event.preventDefault();
      emailInput.value = emailInput.value.trim();
      if (!emailInput.checkValidity()) {
        emailInput.reportValidity();
        setStatus(authText("invalidEmail", "Enter a valid email address."));
        return;
      }
      sendOtp(emailInput.value, sendButton);
    });

    otpInput.addEventListener("input", () => {
      otpInput.value = otpInput.value.replace(/\D/g, "").slice(0, 6);
      otpInput.setCustomValidity("");
    });
    otpInput.addEventListener("paste", (event) => {
      event.preventDefault();
      const digits = event.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
      otpInput.value = digits;
      otpInput.dispatchEvent(new Event("input", { bubbles: true }));
    });

    verifyForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const otp = otpInput.value.replace(/\D/g, "").slice(0, 6);
      otpInput.value = otp;
      if (otp.length !== 6) {
        otpInput.setCustomValidity(
          authText("otpLength", "Enter the complete six-digit OTP.")
        );
        otpInput.reportValidity();
        setStatus(authText("otpLength", "Enter the complete six-digit OTP."));
        return;
      }
      verifyOtp(emailInput.value, otp, verifyButton);
    });

    otpLogin.querySelector("[data-change-email]").addEventListener("click", changeEmail);
    resendButton.addEventListener("click", () => {
      if (!resendButton.disabled) sendOtp(emailInput.value, resendButton, true);
    });
  }

  async function clearServerSession() {
    try {
      await fetch("/logout", {
        method: "POST",
        headers: { "X-CSRF-Token": csrfToken },
        credentials: "same-origin",
      });
    } catch {
      // The login route remains the safe fallback if the server is unreachable.
    }
    window.location.replace("/login");
  }

  function setupLogout() {
    logoutForms.forEach((form) => {
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        logoutInProgress = true;
        const button = form.querySelector("button[type='submit']");
        setBusy(button, true, authText("loggingOut", "Logging out..."));
        try {
          const supabase = await createSupabaseClient();
          const { error } = await supabase.auth.signOut();
          if (error) throw error;
          form.submit();
        } catch (error) {
          logoutInProgress = false;
          setBusy(button, false);
          window.alert(
            errorMessage(error, "logout") ||
              authText("logoutError", "Logout failed. Check your connection and try again.")
          );
        }
      });
    });
  }

  function setupAccountDeletion() {
    accountDeleteForms.forEach((form) => {
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const confirmation = authText(
          form.dataset.confirmKey || "deleteAccountConfirm",
          "Delete your account and profile? This cannot be undone."
        );
        if (!window.confirm(confirmation)) return;

        logoutInProgress = true;
        const button = form.querySelector("button[type='submit']");
        setBusy(button, true, authText("deletingAccount", "Deleting account..."));
        try {
          const supabase = await createSupabaseClient();
          const { error } = await supabase.auth.signOut();
          if (error) throw error;
          form.submit();
        } catch (error) {
          logoutInProgress = false;
          setBusy(button, false);
          window.alert(errorMessage(error, "logout"));
        }
      });
    });
  }

  async function restoreSession() {
    try {
      const client = await createSupabaseClient();
      const { data, error } = await client.auth.getSession();
      if (error) throw error;
      if (otpLogin && data.session) {
        setStatus(authText("restoringSession", "Restoring your session..."), "success");
        const next = await syncServerSession(data.session);
        window.location.replace(next);
        return;
      }
      if (protectedPage && !data.session) {
        await clearServerSession();
      }
    } catch (error) {
      if (otpLogin) setStatus(error.message || errorMessage(error, "restore"));
    }
  }

  if (otpLogin) setupOtpLogin();
  if (logoutForms.length) setupLogout();
  if (accountDeleteForms.length) setupAccountDeletion();
  if (otpLogin || protectedPage) restoreSession();
})();
