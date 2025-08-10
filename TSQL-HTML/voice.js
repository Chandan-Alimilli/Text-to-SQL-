let isSpeechInitializing = false;

async function initSpeech() {
  try {
    console.log("Initializing speech-to-text via API...");
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error("Microphone access not supported in this browser.");
    }
    console.log("Microphone access initializing");

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    console.log("Microphone access granted");
    const audioContext = new AudioContext();
    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(1024, 1, 1); // Note: Deprecated, consider AudioWorkletNode for future
    const chunks = [];

    processor.onaudioprocess = (e) => {
      const inputData = e.inputBuffer.getChannelData(0);
      const buffer = new Int16Array(inputData.length);
      for (let i = 0; i < inputData.length; i++) {
        buffer[i] = Math.min(1, Math.max(-1, inputData[i])) * 32767;
      }
      chunks.push(buffer);
    };

    source.connect(processor);
    processor.connect(audioContext.destination);
    console.log("Audio processing started");

    // Record for 10 seconds to capture more speech
    await new Promise((resolve) => setTimeout(resolve, 10000));

    processor.disconnect();
    source.disconnect();
    audioContext.close();
    stream.getTracks().forEach((track) => track.stop());
    console.log("Audio processing stopped");

    // Convert chunks to a single audio buffer
    const audioData = new Int16Array(
      chunks.reduce((acc, val) => acc.concat(Array.from(val)), [])
    );
    const blob = new Blob([audioData.buffer], { type: "audio/wav" });

    // Send audio to backend API
    const formData = new FormData();
    formData.append("audio", blob, "audio.wav");

    const response = await fetch("http://localhost:8000/recognize", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (response.ok) {
      const transcript = data.transcript || "No transcription received";
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
    } else {
      throw new Error(data.error || "Recognition failed");
    }
  } catch (error) {
    console.error("Speech-to-text initialization failed:", error);
    alert(
      `Failed to start speech-to-text: ${error.message}. Ensure the backend API is running at http://localhost:8000.`
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
