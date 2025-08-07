let isSpeechInitializing = false;

async function initSpeech() {
  try {
    console.log("Initializing Web Speech API...");
    const recognition = new (window.SpeechRecognition ||
      window.webkitSpeechRecognition)();
    if (!recognition) {
      throw new Error("Web Speech API is not supported in this browser.");
    }
    console.log("Web Speech API initialized");

    // Request microphone access
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    console.log("Microphone access granted");

    recognition.continuous = true; // Keep listening until stopped
    recognition.interimResults = true; // Get interim results for real-time feedback
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          transcript += event.results[i][0].transcript;
        }
      }
      if (transcript) {
        console.log("Recognized text:", transcript);
        const input = document.getElementById("user-input");
        if (input) input.value = transcript;
        const form = document.querySelector(".typing-form");
        if (form) {
          const event = new SubmitEvent("submit", {
            bubbles: true,
            cancelable: true,
            submitter: document.getElementById("send-message-button"),
          });
          form.dispatchEvent(event);
        }
      }
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
    };

    recognition.onend = () => {
      console.log("Speech recognition ended");
      stream.getTracks().forEach((track) => track.stop());
    };

    recognition.start();
    console.log("Speech recognition started");

    setTimeout(() => {
      recognition.stop();
      console.log("Speech recognition timed out");
    }, 5000);
  } catch (error) {
    console.error("Speech initialization failed:", error);
    alert(
      `Failed to start speech recognition: ${error.message}. Ensure your browser supports the Web Speech API (e.g., Chrome, Edge).`
    );
  }
}

// Single event listener to avoid multiple triggers
document.getElementById("mic-button")?.addEventListener("click", () => {
  if (isSpeechInitializing) return;
  console.log("Microphone button clicked");
  isSpeechInitializing = true;
  initSpeech().finally(() => {
    isSpeechInitializing = false;
  });
});
