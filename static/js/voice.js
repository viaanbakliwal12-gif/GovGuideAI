const micButton = document.querySelector("#micButton");
const voiceComposerStatus = document.querySelector("#voiceComposerStatus");
const voiceStatusText = document.querySelector("#voiceStatusText");
const recordingTimer = document.querySelector("#recordingTimer");
const messageInputForVoice = document.querySelector("#messageInput");

let mediaRecorder = null;
let recordingStream = null;
let recordedChunks = [];
let recordedMimeType = "audio/webm";
let recordedFilename = "voice-message.webm";
let recordingState = "idle";
let composerStatusState = "idle";
let composerStatusKey = "";
let timerId = null;
let startedAt = 0;
let discardRecording = false;

const speechCache = new Map();
let currentSpeech = null;

function t(key) {
  return window.GovGuideI18n?.t(key) || key;
}

function language() {
  return window.GovGuideChat?.selectedLanguage() || window.GovGuideI18n?.getLanguage() || "en";
}

function formatElapsed(milliseconds) {
  const elapsedSeconds = Math.max(0, Math.floor(milliseconds / 1000));
  const minutes = String(Math.floor(elapsedSeconds / 60)).padStart(2, "0");
  const seconds = String(elapsedSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function updateRecordingTimer() {
  if (recordingState === "recording" && recordingTimer) {
    recordingTimer.textContent = formatElapsed(Date.now() - startedAt);
  }
}

function clearRecordingTimer() {
  window.clearInterval(timerId);
  timerId = null;
}

function renderRecordingState() {
  if (!micButton || !voiceComposerStatus || !voiceStatusText || !recordingTimer) {
    return;
  }

  const isRecording = recordingState === "recording";
  const isTranscribing = recordingState === "transcribing";
  const labelKey = isRecording ? "stopRecording" : "startRecording";

  micButton.dataset.state = isRecording ? "recording" : isTranscribing ? "transcribing" : "idle";
  micButton.dataset.i18nTitle = labelKey;
  micButton.disabled = recordingState === "starting" || isTranscribing;
  micButton.setAttribute("aria-pressed", String(isRecording));
  micButton.setAttribute("aria-label", t(labelKey));
  micButton.title = t(labelKey);

  const defaultStatusKeys = {
    recording: "listening",
    transcribing: "transcribing",
  };
  const statusKey = composerStatusKey || defaultStatusKeys[composerStatusState] || "";
  const statusIsVisible = Boolean(statusKey) && !["idle", "starting"].includes(composerStatusState);

  voiceComposerStatus.hidden = !statusIsVisible;
  voiceComposerStatus.dataset.state = composerStatusState;
  voiceStatusText.textContent = statusIsVisible ? t(statusKey) : "";
  recordingTimer.hidden = composerStatusState !== "recording";
  if (composerStatusState !== "recording") {
    recordingTimer.textContent = "";
  }
}

function setRecordingState(state, statusKey = "") {
  recordingState = state === "error" ? "idle" : state;
  composerStatusState = state;
  composerStatusKey = statusKey;
  renderRecordingState();
}

function showRecordingError(messageKey) {
  setRecordingState("error", messageKey);
  messageInputForVoice?.focus();
}

function selectRecordingFormat() {
  const candidates = [
    { mimeType: "audio/webm;codecs=opus", filename: "voice-message.webm" },
    { mimeType: "audio/webm", filename: "voice-message.webm" },
    { mimeType: "audio/mp4", filename: "voice-message.mp4" },
  ];
  return candidates.find((item) => MediaRecorder.isTypeSupported(item.mimeType)) || { mimeType: "", filename: "voice-message.webm" };
}

function filenameForMimeType(mimeType, fallback) {
  if (mimeType.includes("mp4") || mimeType.includes("m4a")) {
    return "voice-message.mp4";
  }
  if (mimeType.includes("mpeg") || mimeType.includes("mp3")) {
    return "voice-message.mp3";
  }
  if (mimeType.includes("wav")) {
    return "voice-message.wav";
  }
  return fallback;
}

async function startRecording() {
  if (recordingState !== "idle") {
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    showRecordingError("recordingUnsupported");
    return;
  }

  setRecordingState("starting");
  try {
    recordingStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recordedChunks = [];
    discardRecording = false;

    const format = selectRecordingFormat();
    mediaRecorder = format.mimeType
      ? new MediaRecorder(recordingStream, { mimeType: format.mimeType })
      : new MediaRecorder(recordingStream);
    recordedMimeType = mediaRecorder.mimeType || format.mimeType || "audio/webm";
    recordedFilename = filenameForMimeType(recordedMimeType, format.filename);

    mediaRecorder.addEventListener("dataavailable", (event) => {
      if (event.data.size > 0) {
        recordedChunks.push(event.data);
      }
    });
    mediaRecorder.addEventListener("stop", handleRecordingStopped, { once: true });
    mediaRecorder.start();

    startedAt = Date.now();
    setRecordingState("recording");
    updateRecordingTimer();
    timerId = window.setInterval(updateRecordingTimer, 500);
  } catch (error) {
    stopRecordingTracks();
    mediaRecorder = null;
    const permissionWasDenied = ["NotAllowedError", "SecurityError"].includes(error?.name);
    showRecordingError(permissionWasDenied ? "micDenied" : "recordingFailed");
  }
}

function stopRecording() {
  if (recordingState !== "recording" || !mediaRecorder) {
    return;
  }

  clearRecordingTimer();
  setRecordingState("transcribing");
  try {
    if (mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
  } catch {
    stopRecordingTracks();
    mediaRecorder = null;
    showRecordingError("transcriptionFailed");
    return;
  }
  stopRecordingTracks();
}

function discardCurrentRecording() {
  discardRecording = true;
  clearRecordingTimer();
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
  stopRecordingTracks();
}

async function handleRecordingStopped() {
  clearRecordingTimer();
  stopRecordingTracks();
  mediaRecorder = null;

  if (discardRecording) {
    recordedChunks = [];
    setRecordingState("idle");
    return;
  }

  const blob = new Blob(recordedChunks, { type: recordedMimeType });
  recordedChunks = [];
  if (blob.size === 0) {
    showRecordingError("emptyAudio");
    return;
  }

  try {
    const transcript = await transcribe(blob, recordedFilename);
    if (!String(transcript || "").trim()) {
      throw new Error("empty transcript");
    }
    insertTranscriptIntoComposer(transcript);
    setRecordingState("idle");
    messageInputForVoice?.focus();
  } catch {
    showRecordingError("transcriptionFailed");
  }
}

async function transcribe(blob, filename) {
  const formData = new FormData();
  formData.append("audio", blob, filename);
  formData.append("preferredLanguage", language());

  const response = await fetch("/api/voice/transcribe", {
    method: "POST",
    body: formData,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || t("transcriptionFailed"));
  }
  return data.transcript;
}

function insertTranscriptIntoComposer(transcript) {
  if (!messageInputForVoice) {
    return;
  }
  const cleanTranscript = String(transcript || "").trim();
  if (!cleanTranscript) {
    return;
  }

  const existingText = messageInputForVoice.value;
  if (existingText.trim()) {
    const separator = /\s$/.test(existingText) ? "" : " ";
    messageInputForVoice.value = `${existingText}${separator}${cleanTranscript}`;
  } else {
    messageInputForVoice.value = cleanTranscript;
  }

  messageInputForVoice.dispatchEvent(new Event("input", { bubbles: true }));
  messageInputForVoice.focus();
  messageInputForVoice.setSelectionRange(messageInputForVoice.value.length, messageInputForVoice.value.length);
}

function stopRecordingTracks() {
  recordingStream?.getTracks().forEach((track) => track.stop());
  recordingStream = null;
}

function speakerIconMarkup(state) {
  if (state === "loading") {
    return '<span class="speaker-loader" aria-hidden="true"></span>';
  }
  if (state === "playing") {
    return '<svg class="speaker-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="7" y="7" width="10" height="10" rx="1.5"></rect></svg>';
  }
  return '<svg class="speaker-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M5 9.5v5h3.25L12.5 18V6L8.25 9.5H5Z"></path><path d="M15.25 9a4.25 4.25 0 0 1 0 6M17.75 6.75a7.25 7.25 0 0 1 0 10.5"></path></svg>';
}

function setSpeakerButtonState(button, state) {
  if (!button) {
    return;
  }
  const labelKeys = {
    idle: "readAnswerAloud",
    loading: "preparingAudio",
    playing: "stopReadingAloud",
  };
  const label = t(labelKeys[state] || "readAnswerAloud");
  const icon = button.querySelector(".speech-button-icon");

  button.dataset.state = state;
  button.disabled = state === "loading";
  button.setAttribute("aria-label", label);
  button.title = label;
  if (icon) {
    icon.innerHTML = speakerIconMarkup(state);
  }

  const status = button.parentElement?.querySelector("[data-speech-status]");
  if (status) {
    status.textContent = state === "loading" ? t("preparingAudio") : "";
  }
}

function resetSpeakerButton(button) {
  setSpeakerButtonState(button, "idle");
}

function stopCurrentSpeech() {
  const speech = currentSpeech;
  if (!speech) {
    return;
  }

  currentSpeech = null;
  speech.controller?.abort();
  if (speech.audio) {
    speech.audio.pause();
    try {
      speech.audio.currentTime = 0;
    } catch {
      // Some browsers do not allow seeking before audio metadata is available.
    }
  }
  resetSpeakerButton(speech.button);
}

async function playSpeechEntry(entry, article, button) {
  const audio = new Audio(entry.url);
  const speech = { article, button, audio, controller: null };
  currentSpeech = speech;

  audio.addEventListener("ended", () => {
    if (currentSpeech === speech) {
      currentSpeech = null;
      resetSpeakerButton(button);
    }
  }, { once: true });
  audio.addEventListener("error", () => {
    if (currentSpeech === speech) {
      currentSpeech = null;
      resetSpeakerButton(button);
      removeSpeechCache(article);
      window.GovGuideChat?.showSystemNotice?.(t("speechFailed"), "error");
    }
  }, { once: true });

  setSpeakerButtonState(button, "playing");
  try {
    await audio.play();
  } catch (error) {
    if (currentSpeech === speech) {
      currentSpeech = null;
      resetSpeakerButton(button);
    }
    throw error;
  }
}

async function toggleSpeechPlayback(text, article, button) {
  if (currentSpeech?.article === article) {
    stopCurrentSpeech();
    return;
  }

  stopCurrentSpeech();
  const cachedEntry = speechCache.get(article);
  if (cachedEntry) {
    try {
      await playSpeechEntry(cachedEntry, article, button);
    } catch {
      window.GovGuideChat?.showSystemNotice?.(t("speechFailed"), "error");
    }
    return;
  }

  const controller = new AbortController();
  const pendingSpeech = { article, button, audio: null, controller };
  currentSpeech = pendingSpeech;
  setSpeakerButtonState(button, "loading");

  try {
    const response = await fetch("/api/voice/speak", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        preferredLanguage: language(),
        voice: "alloy",
      }),
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error(t("speechFailed"));
    }

    const audioBlob = await response.blob();
    if (currentSpeech !== pendingSpeech) {
      return;
    }
    if (!audioBlob.size) {
      throw new Error(t("speechFailed"));
    }

    const entry = { text, url: URL.createObjectURL(audioBlob) };
    speechCache.set(article, entry);
    currentSpeech = null;
    await playSpeechEntry(entry, article, button);
  } catch (error) {
    if (currentSpeech === pendingSpeech) {
      currentSpeech = null;
      resetSpeakerButton(button);
    }
    if (error?.name !== "AbortError") {
      window.GovGuideChat?.showSystemNotice?.(t("speechFailed"), "error");
    }
  }
}

function removeSpeechCache(article) {
  if (currentSpeech?.article === article) {
    stopCurrentSpeech();
  }
  const entry = speechCache.get(article);
  if (entry?.url) {
    URL.revokeObjectURL(entry.url);
  }
  speechCache.delete(article);
}

function clearSpeechCache() {
  stopCurrentSpeech();
  speechCache.forEach((entry) => {
    if (entry.url) {
      URL.revokeObjectURL(entry.url);
    }
  });
  speechCache.clear();
}

function enhanceAssistantMessage(article, text) {
  if (!article || article.querySelector(".message-speech-control")) {
    return;
  }

  let footer = article.querySelector(".message-footer");
  if (!footer) {
    footer = document.createElement("div");
    footer.className = "message-footer";
    article.querySelector(".message-body")?.appendChild(footer);
  }

  const control = document.createElement("div");
  control.className = "message-speech-control";

  const button = document.createElement("button");
  button.type = "button";
  button.className = "speech-button";
  const icon = document.createElement("span");
  icon.className = "speech-button-icon";
  button.appendChild(icon);
  button.addEventListener("click", () => {
    toggleSpeechPlayback(text, article, button);
  });

  const status = document.createElement("span");
  status.className = "speech-status";
  status.setAttribute("aria-live", "polite");
  status.setAttribute("data-speech-status", "");

  control.append(button, status);
  footer.appendChild(control);
  resetSpeakerButton(button);
}

function refreshTranslatedVoiceLabels() {
  renderRecordingState();
  document.querySelectorAll(".speech-button").forEach((button) => {
    setSpeakerButtonState(button, button.dataset.state || "idle");
  });
}

micButton?.addEventListener("click", () => {
  if (recordingState === "recording") {
    stopRecording();
  } else {
    startRecording();
  }
});

window.addEventListener("beforeunload", () => {
  discardCurrentRecording();
  clearSpeechCache();
});

window.addEventListener("govguideai:languagechange", refreshTranslatedVoiceLabels);

document.querySelectorAll(".assistant-message:not(.notice-message):not(.error-message)").forEach((article) => {
  const text = article.querySelector(".bubble")?.innerText.trim();
  if (text) {
    enhanceAssistantMessage(article, text);
  }
});

try {
  window.localStorage.removeItem("govguideaiVoiceReplies");
} catch {
  // Voice playback no longer relies on saved automatic-playback preferences.
}

setRecordingState("idle");

window.GovGuideVoice = {
  startRecording,
  stopRecording,
  setRecordingState,
  insertTranscriptIntoComposer,
  toggleSpeechPlayback,
  stopCurrentSpeech,
  resetSpeakerButton,
  enhanceAssistantMessage,
  removeSpeechCache,
  clearSpeechCache,
};
