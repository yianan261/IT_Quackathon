// 页面加载完成后执行
document.addEventListener("DOMContentLoaded", function () {
  // 获取UI元素
  const triggerButton = document.getElementById("triggerAutomation");
  const pollingToggle = document.getElementById("pollingToggle");
  const statusDiv = document.getElementById("status");
  const voiceStatus = document.getElementById("voice-status");
  const stopButtonContainer = document.getElementById("stop-button-container");
  const stopButton = document.getElementById("stopButton");

  let isSpeaking = false; // Track speaking state

  // 更新状态函数
  function updateStatus(message, isError = false) {
    statusDiv.textContent = message;
    statusDiv.className = isError ? "error" : "success";

    // 3秒后清除状态
    setTimeout(() => {
      statusDiv.textContent = "";
      statusDiv.className = "";
    }, 3000);
  }

  // 触发自动化按钮
  if (triggerButton) {
    triggerButton.addEventListener("click", function () {
      updateStatus("触发自动化操作...");

      chrome.runtime.sendMessage(
        { type: "TRIGGER_AUTOMATION" },
        function (response) {
          if (response?.status === "triggered") {
            updateStatus("已成功触发自动化操作");
          } else {
            updateStatus("触发自动化操作失败", true);
          }
        }
      );
    });
  }

  // 轮询开关
  if (pollingToggle) {
    chrome.storage.local.get(["pollingEnabled"], function (result) {
      if (result.hasOwnProperty("pollingEnabled")) {
        pollingToggle.checked = result.pollingEnabled;
      }
    });

    pollingToggle.addEventListener("change", function () {
      const enabled = this.checked;

      chrome.storage.local.set({ pollingEnabled: enabled });
      chrome.runtime.sendMessage(
        { type: "TOGGLE_POLLING", enabled },
        function (response) {
          if (response) {
            updateStatus(enabled ? "已开启自动轮询" : "已关闭自动轮询");
          }
        }
      );
    });
  }

  // ✅ WebSocket connection
  const socket = new WebSocket("ws://localhost:8000/ws/voice");

  socket.addEventListener("open", () => {
    console.log("✅ WebSocket connected");
  });

  socket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data);
    console.log("Message from server:", data);

    switch (data.event) {
      case "listening":
        showListeningAnimation();
        isSpeaking = false;
        break;
      case "processing":
        showProcessingAnimation();
        isSpeaking = false;
        break;
      case "speaking":
        showSpeakingAnimation();
        isSpeaking = true;
        break;
      case "idle":
        resetAnimations();
        isSpeaking = false;
        break;
      default:
        console.log("Unknown event:", data.event);
    }
  });

  socket.addEventListener("error", (error) => {
    console.error("❌ WebSocket error:", error);
  });

  socket.addEventListener("close", () => {
    console.warn("❌ WebSocket disconnected");
  });

  window.addEventListener("beforeunload", () => {
    if (socket.readyState === WebSocket.OPEN) {
      socket.close();
    }
  });

  // UI state handlers
  function showListeningAnimation() {
    updateVoiceUI("🎤 Listening...", "listening", false);
  }

  function showProcessingAnimation() {
    updateVoiceUI("⚙️ Processing...", "processing", false);
  }

  function showSpeakingAnimation() {
    updateVoiceUI("🗣️ Speaking...", "speaking", true);
  }

  function resetAnimations() {
    updateVoiceUI("", "", false);
  }

  function updateVoiceUI(text, className, showStopButton) {
    if (voiceStatus) {
      voiceStatus.textContent = text;
      voiceStatus.className = "voice-status " + className;
    }
    if (stopButtonContainer) {
      stopButtonContainer.style.display = showStopButton ? "block" : "none";
    }
  }

  // ✅ Stop Button handler
  if (stopButton) {
    stopButton.addEventListener("click", function () {
      console.log("🛑 Stop button clicked");

      // Stop any ongoing speech synthesis
      if (window.speechSynthesis && window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
        console.log("🛑 Speech synthesis cancelled");
      }

      // Send stop event to backend
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ event: "stop" }));
      }

      resetAnimations();
      updateStatus("🛑 Assistant stopped");
      isSpeaking = false;
    });
  }
});
