// 页面加载完成后执行
document.addEventListener("DOMContentLoaded", function () {
  // 获取UI元素
  const triggerButton = document.getElementById("triggerAutomation");
  const pollingToggle = document.getElementById("pollingToggle");
  const statusDiv = document.getElementById("status");
  const voiceStatus = document.getElementById("voice-status");
  const stopButtonContainer = document.getElementById("stop-button-container");
  const stopButton = document.getElementById("stopButton");

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

  // 为触发自动化按钮添加点击事件
  if (triggerButton) {
    triggerButton.addEventListener("click", function () {
      updateStatus("触发自动化操作...");

      chrome.runtime.sendMessage(
        { type: "TRIGGER_AUTOMATION" },
        function (response) {
          if (response && response.status === "triggered") {
            updateStatus("已成功触发自动化操作");
          } else {
            updateStatus("触发自动化操作失败", true);
          }
        }
      );
    });
  }

  // 为轮询开关添加变更事件
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
        { type: "TOGGLE_POLLING", enabled: enabled },
        function (response) {
          if (response) {
            updateStatus(enabled ? "已开启自动轮询" : "已关闭自动轮询");
          }
        }
      );
    });
  }

  // ✅ WebSocket connection for voice UI
  const socket = new WebSocket("ws://localhost:8000/ws/voice");

  socket.addEventListener("open", function () {
    console.log("✅ WebSocket connected");
  });

  socket.addEventListener("message", function (event) {
    const data = JSON.parse(event.data);
    console.log("Message from server:", data);

    switch (data.event) {
      case "listening":
        showListeningAnimation();
        break;
      case "processing":
        showProcessingAnimation();
        break;
      case "speaking":
        showSpeakingAnimation();
        break;
      case "idle":
        resetAnimations();
        break;
      default:
        console.log("Unknown event:", data.event);
    }
  });

  socket.addEventListener("error", function (error) {
    console.error("❌ WebSocket error:", error);
  });

  socket.addEventListener("close", function () {
    console.warn("❌ WebSocket disconnected");
  });

  window.addEventListener("beforeunload", function () {
    if (socket.readyState === WebSocket.OPEN) {
      socket.close();
    }
  });

  function showListeningAnimation() {
    if (voiceStatus) {
      voiceStatus.textContent = "🎤 Listening...";
      voiceStatus.className = "voice-status listening";
    }
    if (stopButtonContainer) {
      stopButtonContainer.style.display = "none";
    }
  }

  function showProcessingAnimation() {
    if (voiceStatus) {
      voiceStatus.textContent = "⚙️ Processing...";
      voiceStatus.className = "voice-status processing";
    }
    if (stopButtonContainer) {
      stopButtonContainer.style.display = "none";
    }
  }

  function showSpeakingAnimation() {
    if (voiceStatus) {
      voiceStatus.textContent = "🗣️ Speaking...";
      voiceStatus.className = "voice-status speaking";
    }
    if (stopButtonContainer) {
      stopButtonContainer.style.display = "block";
    }
  }

  function resetAnimations() {
    if (voiceStatus) {
      voiceStatus.textContent = "";
      voiceStatus.className = "voice-status";
    }
    if (stopButtonContainer) {
      stopButtonContainer.style.display = "none";
    }
  }

  // ✅ Stop Button Click Event
  if (stopButton) {
    stopButton.addEventListener("click", function () {
      console.log("🛑 Stop button clicked");

      // Stop any ongoing speech synthesis
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }

      // Optionally, send stop event to server if needed
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ event: "stop" }));
      }

      resetAnimations();
    });
  }
});
