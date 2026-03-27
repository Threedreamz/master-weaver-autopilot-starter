<?php 


function getIPv4($iface = "wlan0") {
    $cmd = "ip -4 addr show " . escapeshellarg($iface) . " | awk '/inet/ {print $2}' | cut -d'/' -f1";
    return trim(shell_exec($cmd));
}
$eip = getIPv4("wlan0");
if ($eip == null||$eip == ""){
  $eip = getIPv4("eth0");
}
if ($eip == null ||$eip == ""){
  echo "EIP cant be cound";
}


?>


<!DOCTYPE html>
<html lang="de">

<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <title>Röntgen-Steuerung</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * {
      -webkit-tap-highlight-color: transparent;
    }

    body {
      font-family: 'Inter', sans-serif;
      background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
      min-height: 100vh;
      margin: 0;
      padding: 0;
      overflow-x: hidden;
      position: relative;
    }

    body::before {
      content: '';
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background:
        radial-gradient(circle at 20% 30%, rgba(59, 130, 246, 0.08) 0%, transparent 50%),
        radial-gradient(circle at 80% 70%, rgba(16, 185, 129, 0.06) 0%, transparent 50%);
      pointer-events: none;
      z-index: 0;
    }

    .app-container {
      position: relative;
      z-index: 1;
      min-height: 100vh;
      padding: clamp(1rem, 3vw, 2.5rem);
      display: flex;

      flex-direction: column;
    }

    .header {
      text-align: center;
      margin-bottom: clamp(1.5rem, 4vw, 3rem);
      animation: slideDown 0.6s ease-out;
    }

    @keyframes slideDown {
      from {
        opacity: 0;
        transform: translateY(-20px);
      }

      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .header h2 {
      font-size: clamp(1.5rem, 4vw, 2.5rem);
      font-weight: 800;
      background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 0.5rem;
      letter-spacing: -0.02em;
    }

    .header p {
      color: #94a3b8;
      font-size: clamp(0.875rem, 1.5vw, 1.125rem);
      font-weight: 400;
      max-width: 600px;
      margin: 0 auto;
    }

    .main-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: clamp(1.25rem, 3vw, 2rem);
      max-width: 1600px;
      margin: 0 auto;
      top: 0;
      width: 100%;
      animation: fadeIn 0.8s ease-out 0.2s both;
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: translateY(20px);
      }

      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @media (min-width: 1024px) {
      .main-grid {
        grid-template-columns: 1fr 1.2fr;
      }
    }

    .glass-card {
      background: rgba(15, 23, 42, 0.7);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(148, 163, 184, 0.1);
      border-radius: 20px;
      padding: clamp(1.25rem, 3vw, 2rem);
      box-shadow:
        0 20px 60px -15px rgba(0, 0, 0, 0.5),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
      transition: all 0.3s ease;
    }

    .glass-card:hover {
      border-color: rgba(148, 163, 184, 0.15);
      box-shadow:
        0 25px 70px -15px rgba(0, 0, 0, 0.6),
        inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }

    .control-section {
      display: flex;
      flex-direction: column;
      gap: clamp(1.25rem, 3vw, 1.75rem);
    }

    .section-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 1.25rem;
      font-size: clamp(1rem, 2vw, 1.2rem);
      font-weight: 600;
      color: #e2e8f0;
    }

    .section-icon {
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(16, 185, 129, 0.15));
      border-radius: 12px;
      color: #3b82f6;
      font-size: 1.1rem;
    }

    .input-group {
      position: relative;
    }

    .input-wrapper {
      display: flex;
      gap: 0.75rem;
    }

    .modern-input {
      flex: 1;
      padding: 1.125rem 1.25rem;
      background: rgba(15, 23, 42, 0.6);
      border: 1.5px solid rgba(148, 163, 184, 0.15);
      border-radius: 14px;
      color: #e2e8f0;
      font-size: clamp(1rem, 2.5vw, 1.125rem);
      font-weight: 500;
      transition: all 0.3s ease;
      outline: none;
    }

    .modern-input:focus {
      border-color: #3b82f6;
      background: rgba(15, 23, 42, 0.8);
      box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
    }

    .icon-btn {
      width: 56px;
      height: 56px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(15, 23, 42, 0.6);
      border: 1.5px solid rgba(148, 163, 184, 0.15);
      border-radius: 14px;
      color: #94a3b8;
      cursor: pointer;
      transition: all 0.3s ease;
      flex-shrink: 0;
    }

    .icon-btn:hover,
    .icon-btn:active {
      background: rgba(59, 130, 246, 0.15);
      border-color: #3b82f6;
      color: #3b82f6;
      transform: scale(0.95);
    }

    .modern-select {
      width: 100%;
      padding: 1.125rem 1.25rem;
      background: rgba(15, 23, 42, 0.6);
      border: 1.5px solid rgba(148, 163, 184, 0.15);
      border-radius: 14px;
      color: #e2e8f0;
      font-size: clamp(1rem, 2.5vw, 1.125rem);
      font-weight: 500;
      cursor: pointer;
      transition: all 0.3s ease;
      outline: none;
      appearance: none;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2394a3b8'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 1rem center;
      background-size: 1.5em;
      padding-right: 3rem;
    }

    .modern-select:focus {
      border-color: #3b82f6;
      background-color: rgba(15, 23, 42, 0.8);
      box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
    }

    .primary-button {
      width: 100%;
      padding: 1.375rem;
      font-size: clamp(1.125rem, 2.5vw, 1.25rem);
      font-weight: 700;
      border-radius: 16px;
      border: none;
      cursor: pointer;
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 1rem;
      position: relative;
      overflow: hidden;
      letter-spacing: 0.02em;
    }

    .primary-button::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent);
      transition: left 0.5s;
    }

    .primary-button:hover::before {
      left: 100%;
    }

    .btn-start {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: white;
      box-shadow: 0 10px 30px -10px rgba(16, 185, 129, 0.4);
    }

    .btn-start:hover,
    .btn-start:active {
      transform: translateY(-2px);
      box-shadow: 0 15px 40px -10px rgba(16, 185, 129, 0.5);
    }

    .btn-stop {
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      color: white;
      box-shadow: 0 10px 30px -10px rgba(239, 68, 68, 0.4);
    }

    .btn-stop:hover,
    .btn-stop:active {
      transform: translateY(-2px);
      box-shadow: 0 15px 40px -10px rgba(239, 68, 68, 0.5);
    }

    .progress-container {
      padding: 1.5rem 0;
    }

    .progress-track {
      position: relative;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .progress-line {
      position: absolute;
      top: 50%;
      left: 0;
      right: 0;
      height: 3px;
      background: rgba(148, 163, 184, 0.15);
      transform: translateY(-50%);
      z-index: 1;
    }

    .progress-fill {
      position: absolute;
      top: 0;
      left: 0;
      height: 100%;
      background: linear-gradient(90deg, #3b82f6, #10b981);
      transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
      width: 0%;
    }

    .progress-node {
      position: relative;
      z-index: 2;
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: rgba(15, 23, 42, 0.9);
      border: 3px solid rgba(148, 163, 184, 0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #64748b;
      font-weight: 700;
      font-size: 0.95rem;
      transition: all 0.4s ease;
    }

    .progress-node.active {
      background: linear-gradient(135deg, #3b82f6, #2563eb);
      border-color: #3b82f6;
      color: white;
      box-shadow: 0 0 0 6px rgba(59, 130, 246, 0.15), 0 8px 24px -8px rgba(59, 130, 246, 0.5);
      transform: scale(1.15);
    }

    .progress-node.completed {
      background: linear-gradient(135deg, #10b981, #059669);
      border-color: #10b981;
      color: white;
      box-shadow: 0 4px 12px -4px rgba(16, 185, 129, 0.4);
    }

    .progress-label {
      position: absolute;
      top: calc(100% + 12px);
      left: 50%;
      transform: translateX(-50%);
      font-size: clamp(0.7rem, 1.8vw, 0.8rem);
      color: #64748b;
      white-space: nowrap;
      font-weight: 500;
      transition: all 0.3s ease;
    }

    .progress-node.active .progress-label {
      color: #3b82f6;
      font-weight: 600;
    }

    .progress-node.completed .progress-label {
      color: #10b981;
    }

    .stream-container {
      position: relative;
      border-radius: 18px;
      overflow: hidden;
      background: #000;
      cursor: pointer;
      transition: all 0.3s ease;
      border: 2px solid rgba(148, 163, 184, 0.1);
      aspect-ratio: 16/9;
    }

    .stream-container:hover {
      border-color: rgba(59, 130, 246, 0.3);
      box-shadow: 0 20px 60px -20px rgba(59, 130, 246, 0.3);
    }

    .stream-container.expanded {
      position: fixed;
      inset: 0;
      z-index: 100;
      border-radius: 0;
      border: none;
      cursor: zoom-out;
    }

    .stream-container iframe {
      width: 100%;
      height: 100%;
      border: none;
      display: block;
    }

    .stream-overlay {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      padding: 1.5rem;
      background: linear-gradient(to top, rgba(0, 0, 0, 0.8), transparent);
      pointer-events: none;
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .live-indicator {
      width: 12px;
      height: 12px;
      background: #ef4444;
      border-radius: 50%;
      animation: livePulse 2s ease-in-out infinite;
      box-shadow: 0 0 12px rgba(239, 68, 68, 0.6);
    }

    @keyframes livePulse {

      0%,
      100% {
        opacity: 1;
        transform: scale(1);
      }

      50% {
        opacity: 0.6;
        transform: scale(1.1);
      }
    }

    .live-text {
      font-size: 0.875rem;
      font-weight: 600;
      color: white;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }

    .expand-hint {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(10px);
      padding: 1rem 1.5rem;
      border-radius: 12px;
      color: white;
      font-size: 0.875rem;
      font-weight: 500;
      opacity: 0;
      transition: opacity 0.3s ease;
      pointer-events: none;
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .stream-container:hover .expand-hint {
      opacity: 1;
    }

    .stream-container.expanded .expand-hint {
      opacity: 0;
    }

    .exit-hint {
      position: absolute;
      top: 1.5rem;
      right: 1.5rem;
      background: rgba(0, 0, 0, 0.8);
      backdrop-filter: blur(10px);
      padding: 0.75rem 1.25rem;
      border-radius: 10px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: #e2e8f0;
      font-size: 0.85rem;
      font-weight: 500;
      display: none;
      gap: 0.5rem;
      align-items: center;
    }

    .stream-container.expanded .exit-hint {
      display: flex;
    }

    .status-card {
      background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(16, 185, 129, 0.08));
      border: 1px solid rgba(59, 130, 246, 0.15);
      border-radius: 16px;
      padding: 1.25rem;
      margin-top: 0.5rem;
    }

    .status-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 0.75rem;
      color: #3b82f6;
      font-weight: 600;
      font-size: 0.95rem;
    }

    .status-text {
      color: #cbd5e1;
      font-size: clamp(0.875rem, 2vw, 0.95rem);
      line-height: 1.6;
    }

    .scan-animation {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, transparent, #10b981, transparent);
      opacity: 0;
      transition: top 8s linear;
    }

    .stream-container.scanning .scan-animation {
      opacity: 1;
      top: 100%;
    }

    .footer {
      text-align: center;
      padding: 1rem 0 1rem;
      color: #e6e5e5ff;
      font-size: 0.875rem;
      margin-top: auto;
    }

    /* Kamera-Styling */
    .camera-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-top: 20px;
    }

    .top-buttons {
      display: flex;
      gap: 10px;
      margin-bottom: 15px;
      width: 100%;
      justify-content: center;
    }

    .camera-btn {
      background: rgba(15, 23, 42, 0.6);
      border: 1.5px solid rgba(148, 163, 184, 0.15);
      padding: 6px 10px;
      border-radius: 12px;
      color: #e2e8f0;
      cursor: pointer;
      transition: all 0.3s ease;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .camera-btn:hover {
      background: rgba(59, 130, 246, 0.15);
      border-color: #3b82f6;
      color: #3b82f6;
    }

    .camera-btn.primary {
      background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
      border: none;
      color: white;
    }

    .camera-btn.success {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      border: none;
      color: white;
    }

    #preview {
      width: 100%;
      max-width: 900px;
      border-radius: 0px;
      background: #030405ff;
    }

    .overlay {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(27, 190, 136, 0.07);
      border-radius: 14px;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.3s ease;
    }

    .found {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
      background: rgba(10, 140, 20, 0.3);
      border: 1px solid rgba(10, 140, 20, 0.5);
      padding: 20px 24px;
      border-radius: 16px;
      color: #b9f2c6;
      font-weight: bold;
      box-shadow: 0 8px 20px rgba(17, 255, 156, 0.4);
    }

    .badge {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background: #10b981;
      color: #03150c;
      font-weight: 900;
      font-size: 22px;
      box-shadow: 0 8px 24px rgba(16, 185, 129, 0.45);
    }

    .buttons {
      display: flex;
      gap: 10px;
      margin-top: 10px;
    }

    /* Webcam-Stream Container */
    .webcam-container {
      margin-top: 1.5rem;
    }

    .webcam-stream {
      width: 100%;
      height: 300px;
      border-radius: 14px;
      background: #000;
      border: 1px solid rgba(148, 163, 184, 0.1);
      overflow: hidden;
    }

    @media (max-width: 640px) {
      .progress-node {
        width: 40px;
        height: 40px;
        font-size: 0.85rem;
      }

      .section-icon {
        width: 36px;
        height: 36px;
        font-size: 1rem;
      }

      .top-buttons {
        flex-direction: column;
        align-items: center;
      }

      .camera-btn {
        width: 100%;
        justify-content: center;
      }

      .webcam-stream {
        height: 250px;
      }
    }
  </style>
</head>
<style>
  body {
    background-image: url('https://<?php echo $eip; ?>/img/bg.jpg');
    background-size: cover;
    /* passt das Bild an die Fenstergröße an */
    background-position: center;
    /* zentriert das Bild */
    background-repeat: no-repeat;
    /* verhindert Kachelung */
    background-attachment: fixed;
    /* bleibt beim Scrollen stehen (optional) */
  }
</style>

<body>
  <div class="app-container">
    <!--<div class="header">
      <h2>Röntgen-Steuerung</h2>
      <p>Automatisierte Röntgenanalyse mit Live-Überwachung und QR-Erkennung</p>
    </div>
-->
    <div class="main-grid">
      <div class="control-section">
        <div class="glass-card">
          <div class="section-header">
            <div class="section-icon">
              <i class="fas fa-barcode"></i>
            </div>
            <span>Objekt-ID</span>
          </div>
          <div class="input-group">
            <div class="input-wrapper">
              <input type="text" id="objectId" class="modern-input" placeholder="OBJ-12345" value="OBJ-67834">
              <button class="icon-btn" id="refreshBtn">
                <i class="fas fa-sync"></i>
              </button>
            </div>
          </div>
          <br>
          <div class="section-header">
            <div class="section-icon">
              <i class="fas fa-barcode"></i>
            </div>
            <span>Auftrags-ID</span>
          </div>
          <div class="input-group">
            <div class="input-wrapper">
              <input type="text" id="auftragsId" class="modern-input" placeholder="t-39383" value="t-39383">

            </div>
          </div>
        </div>

        <div class="glass-card">
          <div class="section-header">
            <div class="section-icon">
              <i class="fas fa-ruler-combined"></i>
            </div>
            <span>Objektgröße</span>
          </div>
          <select id="sizeSelect" class="modern-select">
            <option value="xs">Sehr klein (XS)</option>
            <option value="s">Klein (S)</option>
            <option value="m" selected>Mittel (M)</option>
            <option value="l">Groß (L)</option>
            <option value="xl">Sehr groß (XL)</option>
          </select>
        </div>


        <div class="glass-card" style="margin-top: 0.5rem;">
          <div class="section-header">
            <div class="section-icon">
              <i class="fas fa-power-off"></i>
            </div>
            <span>Betriebsmodus</span>
          </div>
          <button id="toggleBtn" class="primary-button btn-start">
            <i class="fas fa-play"></i>
            <span>Start</span>
          </button>
        </div>

        <div class="glass-card">
          <div class="section-header">
            <div class="section-icon">
              <i class="fas fa-list-check"></i>
            </div>
            <span>Prozessstatus</span>
          </div>
          <div class="progress-container">
            <div class="progress-track">
              <div class="progress-line">
                <div class="progress-fill" id="progressFill"></div>
              </div>

              <div class="progress-node" id="step1">
                <i class="fas fa-check"></i>
                <span class="progress-label">Start</span>
              </div>
              <div class="progress-node" id="step2">
                <span>2</span>
                <span class="progress-label">Einrichtung</span>
              </div>
              <div class="progress-node" id="step3">
                <span>3</span>
                <span class="progress-label">Scannen</span>
              </div>
              <div class="progress-node" id="step4">
                <span>4</span>
                <span class="progress-label">Speichern</span>
              </div>
              <div class="progress-node" id="step5">
                <span>5</span>
                <span class="progress-label">Fertig</span>
              </div>
            </div>
          </div>
        </div>



      </div>

      <div>
        <div class="glass-card">
          <div class="section-header">
            <div class="section-icon">
              <i class="fas fa-video"></i>
            </div>
            <span>Live-Übersicht</span>
          </div>



          <!-- Front-Cam stream mit QR scanning hier-->
          <div class="stream-container" id="streamContainer">
            <div class="scan-animation" id="scanLine"></div>
            <div class="camera-container">
              <div class="top-buttons">
                <button class="camera-btn primary" id="requestPermission" style="position:absolute;">
                  <i class="fas fa-camera"></i>
                </button>
              </div>

              <video id="preview" playsinline autoplay muted></video>

              <div class="overlay" id="overlay">
                <div class="found" id="foundBox">
                  <span class="badge" id="badgeText">
                    <i class="fas fa-check"></i>
                  </span>

                </div>



                <div class="stream-overlay">
                  <div class="live-indicator"></div>
                  <span class="live-text">Front-Cam Live</span>
                </div>
                <div class="expand-hint">
                  <i class="fas fa-expand"></i>
                  <span>Zum Vergrößern klicken</span>
                </div>
                <div class="exit-hint">
                  <i class="fas fa-times"></i>
                  <span>Klicken zum Schließen • ESC</span>
                </div>
              </div>


            </div>
          </div>
  <br>
          <!-- Webcam Stream von http://192.168.2.39:8080/ -->
          <div class="stream-container" id="webcamStreamContainer">
            <img id="video_feed" src="https://<?php echo $eip; ?>:8080/" alt="Webcam Live Stream">
            <div class="stream-overlay">
              <div class="live-indicator"></div>
              <span class="live-text">Webcam Live</span>
            </div>
            <div class="expand-hint">
              <i class="fas fa-expand"></i>
              <span>Zum Vergrößern klicken</span>
            </div>
            <div class="exit-hint">
              <i class="fas fa-times"></i>
              <span>Klicken zum Schließen • ESC</span>
            </div>
          </div>


        </div>

        <div class="footer">
          © 2025 Autopilot | 3Dreamz
        </div>
      </div>
      <!-- Floating Button -->
      <div id="fab-container" class="z-[999]">
        <button id="fab-btn"
          class="fixed bottom-6 right-6 w-16 h-16 rounded-xl bg-gray-800/40 hover:bg-blue-500/50 active:scale-95 backdrop-blur-md transition-all shadow-lg flex items-center justify-center">
          <img src="/img/origami.png" alt="menu" class="w-10 h-10">
        </button>


        <!-- Menü -->
        <div id="fab-menu"
          class="fixed bottom-28 right-4  hidden flex-col gap-3 mt-3  bg-gray-800/40  border border-gray-800/50 backdrop-blur-lg rounded-2xl p-4 shadow-2xl w-56">

          <!-- Statussektion -->
          <div class="flex flex-col gap-2">
            <!-- Pie Status -->
            <label class="flex items-center justify-between bg-slate-800/70  active:scale-95 backdrop-blur-md rounded-lg px-3 py-2 text-slate-200">
              <div class="flex items-center gap-2">
                <img src="/img/pie.png" alt="Nan." class="w-5 h-5 opacity-80">
                <span class="">Pie:</span>
              </div>
              <span id="pie_label" class="text-emerald-400 font-semibold">Online</span>
            </label>

            <!-- Webcam Status -->
            <label class="flex items-center justify-between bg-slate-800/70 rounded-lg px-3 py-2 text-slate-200">
              <div class="flex items-center gap-2">
                <img src="/img/cam2.png" alt="Nan." class="w-5 h-5 opacity-80">
                <span class="">Webcam:</span>
              </div>
              <span id="webcam_label" class="text-emerald-400 font-semibold">Online</span>
            </label>

            <!-- Checkbox -->
            <div class="checkbox-wrapper-22 flex items-center gap-3">
              <label class="switch" for="checkbox">
                <input type="checkbox" id="checkbox" />
                <div class="slider round"></div>
              </label>
              <span class="text-white text-m my-4 select-none">Auto-Connect</span>
            </div>

            <style>
              .checkbox-wrapper-22 .switch {
                display: inline-block;
                height: 34px;
                position: relative;
                width: 60px;
              }

              .checkbox-wrapper-22 .switch input {
                display: none;
              }

              .checkbox-wrapper-22 .slider {
                background-color: #ccc;
                bottom: 0;
                cursor: pointer;
                left: 0;
                position: absolute;
                right: 0;
                top: 0;
                transition: .4s;
              }

              .checkbox-wrapper-22 .slider:before {
                background-color: #fff;
                bottom: 4px;
                content: "";
                height: 26px;
                left: 4px;
                position: absolute;
                transition: .4s;
                width: 26px;
              }

              .checkbox-wrapper-22 input:checked+.slider {
                background-color: #66bb6a;
              }

              .checkbox-wrapper-22 input:checked+.slider:before {
                transform: translateX(26px);
              }

              .checkbox-wrapper-22 .slider.round {
                border-radius: 34px;
              }

              .checkbox-wrapper-22 .slider.round:before {
                border-radius: 50%;
              }
            </style>

          </div>


          <hr class="border-slate-700/40 my-2">

          <!-- Action Buttons -->
          <div class="flex flex-col gap-3 p-3 border-white/70 rounded-2xl shadow-inner">
            <button
              class="flex items-center justify-center gap-2 w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white font-medium py-2.5 rounded-xl shadow-sm hover:shadow-md hover:from-blue-400 hover:to-blue-500 active:scale-[0.98] transition-all">
              <i class="fa-solid fa-clock-rotate-left"></i>
              <span>Historie</span>
            </button>

            <button
              class="flex items-center justify-center gap-2 w-full bg-gradient-to-r from-indigo-500 to-indigo-600 text-white font-medium py-2.5 rounded-xl shadow-sm hover:shadow-md hover:from-indigo-400 hover:to-indigo-500 active:scale-[0.98] transition-all">
              <i class="fa-solid fa-gear"></i>
              <span>Settings</span>
            </button>

            <button
              class="flex items-center justify-center gap-2 w-full bg-gradient-to-r from-slate-600 to-gray-700 text-white font-medium py-2.5 rounded-xl shadow-sm hover:shadow-md hover:from-slate-500 hover:to-gray-600 active:scale-[0.98] transition-all">
              <i class="fa-solid fa-terminal"></i>
              <span>Logs</span>
            </button>
          </div>
        </div>
      </div>
      <script src="https://unpkg.com/jsqr@1.4.0/dist/jsQR.js"></script>


      <script>
        // Prüft, ob URL erreichbar ist
        async function checkOnline(url) {
          try {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 2000);

            const res = await fetch(url, {
              method: "HEAD",
              cache: "no-store",
              signal: controller.signal
            });

            clearTimeout(timeout);
            return res.ok;
          } catch (err) {
            return false;
          }
        }


        const fabBtn = document.getElementById("fab-btn");
        const fabMenu = document.getElementById("fab-menu");
        const pie_label = document.getElementById("pie_label");
        const webcam_label = document.getElementById("webcam_label");
        console.log("eee");
        // Menü öffnen/schließen
        fabBtn.addEventListener("click", () => {
          console.log("eee");
          fabMenu.classList.toggle("hidden");
          fabMenu.classList.toggle("animate-fadeIn");
        });

        async function updateStatus() {
          const pieOnline = await checkOnline("https://<?php echo $eip; ?>:5007/");
          const webcamOnline = await checkOnline("https://<?php echo $eip; ?>:8080/");

          if (pie_label)
            pie_label.textContent = pieOnline ? "Online" : "Offline";
          if (webcam_label)
            webcam_label.textContent = webcamOnline ? "Online" : "Offline";

          pie_label.style.color = pieOnline ? "#10b981" : "#ef4444";
          webcam_label.style.color = webcamOnline ? "#10b981" : "#ef4444";
        }

        // Initiale Prüfung
        updateStatus();

        // Alle 3 Sekunden prüfen
        setInterval(updateStatus, 3000);











        // Ein zweiter Style-Block → neuer Name
        const statusStyle = document.createElement("style");
        statusStyle.textContent = `
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .animate-fadeIn {
    animation: fadeIn 0.25s ease-out;
  }
`;
        document.head.appendChild(statusStyle);
      </script>


      <script>
        // === Custom Confirm Modal ===
        function customConfirm(message) {
          return new Promise((resolve) => {
            // Hintergrund-Overlay
            const overlay = document.createElement("div");
            overlay.className = `
        fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[9999]
        animate-fadeIn
      `;

            // Modal-Box
            const modal = document.createElement("div");
            modal.className = `
        bg-slate-900/90 border border-slate-700/60 rounded-2xl shadow-2xl p-6 w-[90%] max-w-sm
        text-center text-slate-200 scale-95 animate-popIn
      `;
            modal.innerHTML = `
        <div class="text-lg font-semibold mb-3 text-slate-100">
          <i class="fa-solid fa-triangle-exclamation text-yellow-400 mr-2"></i>
          Bestätigung
        </div>
        <div class="text-slate-300 mb-6">${message.replace(/\n/g, "<br>")}</div>
        <div class="flex justify-center gap-3">
          <button id="confirmYes" class="px-5 py-2.5 rounded-lg font-semibold
            bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500
            text-white shadow-lg shadow-emerald-500/30 transition-all">
            Ja, Weiterführen
          </button>
          <button id="confirmNo" class="px-5 py-2.5 rounded-lg font-semibold
            bg-slate-700 hover:bg-slate-600 text-slate-100 border border-slate-600 transition-all">
            Nein, Abbrechen
          </button>
        </div>
      `;

            overlay.appendChild(modal);
            document.body.appendChild(overlay);

            // Buttons
            const yesBtn = modal.querySelector("#confirmYes");
            const noBtn = modal.querySelector("#confirmNo");

            yesBtn.addEventListener("click", () => closeModal(false));
            noBtn.addEventListener("click", () => closeModal(true));
            overlay.addEventListener("click", (e) => {
              if (e.target === overlay) closeModal(false);
            });

            function closeModal(value) {
              modal.classList.add("animate-popOut");
              overlay.classList.add("animate-fadeOut");
              setTimeout(() => overlay.remove(), 250);
              resolve(value);
            }
          });
        }

        // === Animation Styles ===
        const modalStyle = document.createElement("style");
        modalStyle.textContent = `
              @keyframes fadeIn { from {opacity:0;} to {opacity:1;} }
              @keyframes fadeOut { from {opacity:1;} to {opacity:0;} }
              @keyframes popIn { from {opacity:0; transform:scale(0.9);} to {opacity:1; transform:scale(1);} }
              @keyframes popOut { from {opacity:1; transform:scale(1);} to {opacity:0; transform:scale(0.9);} }
              .animate-fadeIn { animation: fadeIn 0.25s ease-out; }
              .animate-fadeOut { animation: fadeOut 0.25s ease-in forwards; }
              .animate-popIn { animation: popIn 0.25s ease-out; }
              .animate-popOut { animation: popOut 0.25s ease-in forwards; }
            `;
        document.head.appendChild(modalStyle);
      </script>

      <script>
        // Webcam Stream mit 10 FPS - mit Cache-Busting
        const webcamImage = document.getElementById('video_feed');
        let webcamErrorCount = 0;
        const debugging = false;

        function updateWebcamStream() {
          if (debugging) console.log('Aktualisiere Webcam-Stream');

          // Cache-Busting mit Timestamp, um das Bild jedes Mal neu zu laden
          const timestamp = new Date().getTime();

          // Wichtig: Protokoll anpassen — wenn Flask über HTTPS auf Port 8443 läuft, dann auch hier "https"
          webcamImage.src = `https://<?php echo $eip; ?>:8080/?t=${timestamp}`;
        }


        // Fehlerbehandlung für das Bild
        webcamImage.addEventListener('error', function() {
          webcamErrorCount++;
          console.warn(`Webcam-Fehler #${webcamErrorCount}`);

          if (webcamErrorCount > 5) {
            console.error('Webcam nicht erreichbar, stoppe Aktualisierung');
            clearInterval(webcamInterval);
            webcamImage.style.opacity = '0.5';
            webcamImage.alt = 'Webcam nicht verfügbar';
          }
        });

        webcamImage.addEventListener('load', function() {
          // Reset Error Count bei erfolgreichem Laden
          webcamErrorCount = 0;
          webcamImage.style.opacity = '1';
        });




        setInterval(updateWebcamStream, 200);
        const requestBtn = document.getElementById('requestPermission');
        const video = document.getElementById('preview');
        const overlay = document.getElementById('overlay');
        const badgeText = document.getElementById('badgeText');


        const objectId = document.getElementById('objectId');
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d', {
          willReadFrequently: true
        });

        let stream = null;
        let scanning = false;
        let paused = false;

        // Sicherstellen, dass mediaDevices verfügbar ist
        function ensureMediaDevices() {
          if (!navigator.mediaDevices) {
            navigator.mediaDevices = {};
          }

          if (!navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia = function(constraints) {
              const getUserMedia = navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia;

              if (!getUserMedia) {
                return Promise.reject(new Error('getUserMedia wird in diesem Browser nicht unterstützt'));
              }

              return new Promise(function(resolve, reject) {
                getUserMedia.call(navigator, constraints, resolve, reject);
              });
            };
          }
        }

        // Kamera-Status prüfen
        function isCameraSupported() {
          return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia) ||
            !!(navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia);
        }

        // Bessere Fehlerbehandlung für Kamera-Zugriff
        async function requestCameraAccess() {
          // Prüfen ob Kamera überhaupt verfügbar ist
          if (!isCameraSupported()) {
            console.warn('Kamera-API wird in diesem Browser nicht unterstützt - deaktiviere Kamera-Funktionen');
            disableCameraFeatures();
            return;
          }

          ensureMediaDevices();

          requestBtn.disabled = true;
          requestBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

          try {
            stream = await navigator.mediaDevices.getUserMedia({
              video: {
                facingMode: 'user',
                width: {
                  ideal: 1280
                },
                height: {
                  ideal: 720
                }
              },
              audio: false
            });

            video.srcObject = stream;
            await video.play();
            scanning = true;
            paused = false;
            scanLoop();
            requestBtn.style.display = 'none'; // Ausblenden nach Erfolg
          } catch (err) {
            console.warn('Kamera-Fehler:', err); // Nur warn, nicht error
            handleCameraError(err);
          }
        }

        // Behandle Kamera-Fehler ohne andere Funktionen zu stoppen
        function handleCameraError(err) {
          // Setze Button zurück
          requestBtn.innerHTML = '<i class="fas fa-camera-slash"></i>';
          requestBtn.disabled = false;

          // Deaktiviere Kamera-Features aber stoppe nicht andere JS-Funktionen
          disableCameraFeatures();

          // Optional: Zeige eine nicht-blockierende Fehlermeldung
          showNonBlockingError('Kamera nicht verfügbar - QR-Scan deaktiviert');
        }

        // Deaktiviere Kamera-Features ohne Fehler zu werfen
        function disableCameraFeatures() {
          scanning = false;
          paused = true;

          // Verstecke den Kamera-Button oder zeige deaktivierten Zustand
          if (requestBtn) {
            requestBtn.innerHTML = '<i class="fas fa-camera-slash"></i>';
            requestBtn.style.opacity = '0.5';
            requestBtn.disabled = true;
            requestBtn.title = 'Kamera nicht verfügbar';
          }

          // Zeige Platzhalter für Video
          if (video) {
            video.style.background = '#1e293b';
            video.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #64748b; flex-direction: column; gap: 10px;"><i class="fas fa-camera-slash" style="font-size: 2rem;"></i><span>Kamera nicht verfügbar</span></div>';
          }
        }

        // Zeige nicht-blockierende Fehlermeldung
        function showNonBlockingError(message) {
          const errorDiv = document.createElement('div');
          errorDiv.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #ef4444;
      color: white;
      padding: 12px 16px;
      border-radius: 8px;
      z-index: 10000;
      max-width: 300px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      animation: slideInRight 0.3s ease;
    `;
          errorDiv.innerHTML = `
      <div style="display: flex; align-items: center; gap: 8px;">
        <i class="fas fa-exclamation-triangle"></i>
        <span>${message}</span>
      </div>
    `;

          document.body.appendChild(errorDiv);

          // Automatisch nach 5 Sekunden entfernen
          setTimeout(() => {
            if (errorDiv.parentNode) {
              errorDiv.style.animation = 'slideOutRight 0.3s ease';
              setTimeout(() => errorDiv.parentNode.removeChild(errorDiv), 300);
            }
          }, 5000);
        }

        // Automatische QR-Erkennung bei Start - mit zusätzlicher Prüfung
        window.addEventListener('load', () => {
          // Prüfen ob Kamera-API verfügbar ist
          if (!isCameraSupported()) {
            console.warn('Kamera-API nicht verfügbar, überspringe automatischen Start');
            disableCameraFeatures();
            return;
          }

          // Starte Kamera automatisch nach 1 Sekunde nur wenn API verfügbar
          setTimeout(() => {
            if (!stream) {
              requestCameraAccess().catch(err => {
                console.warn('Automatischer Kamera-Start fehlgeschlagen:', err);
                // Kein throw - lasse anderen Code weiterlaufen
              });
            }
          }, 1000);
        });
        // scanning loop QR-Scanner 
        function scanLoop() {
          if (!scanning || paused) return;
          const vw = video.videoWidth;
          const vh = video.videoHeight;
          if (!vw || !vh) return requestAnimationFrame(scanLoop);
          canvas.width = vw;
          canvas.height = vh;
          ctx.drawImage(video, 0, 0, vw, vh);
          const imgData = ctx.getImageData(0, 0, vw, vh);
          const code = jsQR(imgData.data, imgData.width, imgData.height);
          if (code) {
            scanning = false;
            showFound(code.data);
            return;
          }
          requestAnimationFrame(scanLoop);
        }
        // QR-Code gefunden – erweitere showFound um zeitlich begrenzte Anzeige
        function showFound(decodedText) {
          // Overlay und Badge sichtbar machen
          overlay.style.opacity = '1';
          overlay.style.pointerEvents = 'auto';
          badgeText.textContent = decodedText;

          // Generiere neue ID mit Zeitcode und QR-Ergebnis
          const now = new Date();
          const hours = String(now.getHours()).padStart(2, '0');
          const minutes = String(now.getMinutes()).padStart(2, '0');
          const timeCode = hours + minutes;
          const newId = `OBJ-${timeCode}-${decodedText}`;

          // Setze die neue ID im Eingabefeld
          objectIdInput.value = newId;

          // Nach 10 Sekunden Overlay und Badge wieder ausblenden
          setTimeout(() => {
            overlay.style.opacity = '0';
            overlay.style.pointerEvents = 'none';
            badgeText.textContent = '';
          }, 10000); // 10 Sekunden = 10000 ms
        }



        function restartScan() {
          // 1. Scanner sofort stoppen
          scanning = false;
          paused = true;

          // 2. Overlay ausblenden
          overlay.style.opacity = '0';
          overlay.style.pointerEvents = 'none';
          badgeText.textContent = '';

          // 3. Temporäre ID setzen
          objectIdInput.value = 'Scanning...';

          // 4. Kurze Verzögerung bevor Scanner neu startet
          setTimeout(() => {
            // Prüfen ob Kamera verfügbar ist
            if (!isCameraSupported() || !stream) {
              console.warn('Kamera nicht verfügbar, kann nicht neu scannen');
              return;
            }

            // Scanner neu starten
            scanning = true;
            paused = false;
            scanLoop();

            console.log('QR-Scanner neu gestartet - zeige nun QR-Code');
          }, 800); // 800ms Verzögerung für Nutzer-Vorbereitung
        }

        if (requestBtn) {
          requestBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            requestCameraAccess().catch(err => {
              console.warn('Manueller Kamera-Start fehlgeschlagen:', err);
              // Kein throw - lasse anderen Code weiterlaufen
            });
          });
        }

        // Hauptsteuerungslogik - UNABHÄNGIG von der Kamera
        const btn = document.getElementById("toggleBtn");
        const streamContainer = document.getElementById("streamContainer");
        const webcamStreamContainer = document.getElementById("webcamStreamContainer");

        const progressFill = document.getElementById("progressFill");
        const refreshBtn = document.getElementById("refreshBtn");
        const objectIdInput = document.getElementById("objectId");
        const steps = document.querySelectorAll('.progress-node');

        let isRunning = false;
        let currentStep = 2;


        function updateSteps(step) {
          if (typeof step !== "number" || step < 0 || step > steps.length) {
            console.warn("Ungültiger Step:", step);
            return;
          }

          // Alles zurücksetzen
          steps.forEach((stepEl) => {
            stepEl.classList.remove("completed", "active");
          });

          // Wenn Step = 0 → nichts aktiv oder completed
          if (step === 0) {
            progressFill.style.width = "0%";
            console.log("🔵 Neutralzustand (Step 0)");
            return;
          }

          // Alle vorherigen Schritte completed
          for (let i = 0; i < step - 1; i++) {
            steps[i].classList.add("completed");
          }

          // Aktuellen Step aktiv setzen
          steps[step - 1].classList.add("active");

          // Fortschrittsbalken berechnen
          const progress = ((step - 1) / (steps.length - 1)) * 100;
          progressFill.style.width = `${progress}%`;

          console.log(`✅ Fortschritt auf Step ${step} gesetzt`);
        }

        async function getAuftrag() {
          const url = "https://<?php echo $eip; ?>/api.php?getAuftrag=true";

          try {
            const response = await fetch(url, {
              method: "GET",
              headers: {
                "Content-Type": "application/json"
              },
            });

            if (!response.ok) {
              console.error(`Fehler: Server antwortete mit Status ${response.status}`);
              return false;
            }

            const data = await response.json();
            const auftrag = data?.auftrag;
            return auftrag;
          } catch (error_auftrag) {
            console.error("Error auftrag: " + error_auftrag);
          }
        }
        async function checkIfExists() {
          const url = "https://<?php echo $eip; ?>/api.php?getAuftrag=true";

          try {
            const response = await fetch(url, {
              method: "GET",
              headers: {
                "Content-Type": "application/json"
              },
            });

            if (!response.ok) {
              console.error(`Fehler: Server antwortete mit Status ${response.status}`);
              return false;
            }

            const data = await response.json();
            const auftrag = data?.auftrag?.auftrag;

            // Prüfen, ob Auftrag vorhanden ist
            if (auftrag && auftrag.id) {
              console.log("⚠️ Auftrag existiert bereits:", auftrag);

              // Bestätigungsdialog anzeigen
              const proceed = await customConfirm("Es existiert bereits ein Auftrag.<br><br>Wollen Sie diesen Auftrag weiterführen?");


              return proceed; // true = weiterführen, false = neu starten
            } else {
              console.log("✅ Kein aktiver Auftrag gefunden.");
              return false;
            }

          } catch (err) {
            console.error("❌ Fehler beim Prüfen des Auftrags:", err);
            return false;
          }
        }

        async function moveToDefect() {
          const url = "https://<?php echo $eip; ?>/api.php?moveToDefect=true";

          try {
            const response = await fetch(url, {
              method: "GET",
              headers: {
                "Content-Type": "application/json"
              },
            });

            if (!response.ok) {
              console.error(`Fehler: Server antwortete mit Status ${response.status}`);
              return false;
            }

            const data = await response.json();
            console.log("🧩 moveToDefect Response:", data);
            return true;
          } catch (err) {
            console.error("❌ Fehler beim moveToDefect-Aufruf:", err);
            return false;
          }
        }

        async function updateInfo() {
          const url = "https://<?php echo $eip; ?>/api.php?getAuftrag=true";

          try {
            const response = await fetch(url, {
              method: "GET",
              headers: {
                "Content-Type": "application/json"
              },
            });

            if (!response.ok) {
              console.error(`Fehler: Server antwortete mit Status ${response.status}`);
              return;
            }

            const data = await response.json();
            const auftrag = data?.auftrag.auftrag;
            console.log(data);
            if (auftrag) {
              console.log("ID:", auftrag.id);
              console.log("Name:", auftrag.name);
              console.log("Beschreibung:", auftrag.desc);
              if (auftrag.desc.status == "ready to start") {
                console.log("waiting for start");
                updateSteps(2);
              } else if (auftrag.desc.status == "start_flow") {
                console.log("started flow")
                updateSteps(3);
              } else if (auftrag.desc.status == "success") {
                updateSteps(4);
              }
            } else {
              console.log("Kein Auftrag vorhanden.");
            }

            if (debugging) {
              console.log("Aktueller Auftrag:", data);
            }

          } catch (err) {
            console.error("Fehler beim Abrufen des Auftrags:", err);
          }
        }




        if (refreshBtn) {

          refreshBtn.addEventListener('click', () => {
            // QR-Scan neu starten
            restartScan();
            overlay.style.opacity = '0';
            overlay.style.pointerEvents = 'none';
            badgeText.textContent = '';

            // Temporäre ID setzen während gescannt wird
            objectIdInput.value = 'Scanning...';

            // Animation für den Button
            refreshBtn.style.transform = 'rotate(360deg)';
            setTimeout(() => {
              refreshBtn.style.transform = 'rotate(0deg)';
            }, 300);
          });

        }


        function toggleFullscreen(container) {
          const isExpanded = container.classList.contains('expanded');

          if (isExpanded) {
            container.classList.remove('expanded');
            if (document.fullscreenElement) {
              document.exitFullscreen().catch(() => {});
            }
          } else {
            container.classList.add('expanded');
            container.requestFullscreen().catch(() => {});
          }
        }

        if (streamContainer) {
          streamContainer.addEventListener('click', () => toggleFullscreen(streamContainer));
        }

        if (webcamStreamContainer) {
          webcamStreamContainer.addEventListener('click', () => toggleFullscreen(webcamStreamContainer));
        }

        document.addEventListener('keydown', (e) => {
          if (e.key === 'Escape') {
            document.querySelectorAll('.stream-container').forEach(container => {
              container.classList.remove('expanded');
            });
          }
        });

        document.addEventListener('fullscreenchange', () => {
          if (!document.fullscreenElement) {
            document.querySelectorAll('.stream-container').forEach(container => {
              container.classList.remove('expanded');
            });
          }
        });

        async function start_process(url) {
          const response = await fetch(url);
          if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
          }

          // Wenn die API JSON zurückgibt, z.B. { "st": true }
          const data = await response.json();
          console.log("API response:", data);
          return data;
        }

        // come back jump btn Start/Stop
        if (btn) {
          btn.addEventListener("click", async function() {
            if (!isRunning) {
              isRunning = true;
              btn.innerHTML = '<i class="fas fa-stop"></i><span>Stop</span>';
              btn.classList.remove("btn-start");
              btn.classList.add("btn-stop");

              const objectId = document.getElementById("objectId");
              const sizeSelect = document.getElementById("sizeSelect");
              const auftragsId = document.getElementById("auftragsId");
              console.log("objectId.value " + objectId.value);
              const baseUrl = "https://<?php echo $eip; ?>/api.php";
              const startUrl =
                `${baseUrl}?start=true` +
                `&objectId=${(objectId.value)}` +
                `&size=${encodeURIComponent(sizeSelect.value)}` +
                `&auftragId=${encodeURIComponent(auftragsId.value)}` +
                `&status=queued`;

              try {
                const response = await start_process(startUrl);
                console.log("Response von API:", response);
                updateSteps(1);
                // Prüfen ob ein Fehler zurückkam (bestehendem Auftrag)
                if (
                  response &&
                  response.flask_result &&
                  response.flask_result.status === "error" &&
                  response.flask_result.message === "there exists already a queue item"
                ) {
                  const confirmReplace = await customConfirm("Es existiert bereits ein aktiver Auftrag.<br><br>Sollen Sie diesen abbrechen und den jetzigen neu starten?");


                  if (confirmReplace) {
                    try {
                      // alten Auftrag / Queue leeren und neuen erstellen 
                      moveToDefect();

                      // neuen Auftrag erneut starten
                      const retryResponse = await start_process(startUrl);
                      console.log("Neuer Auftrag gestartet:", retryResponse);

                      if (
                        retryResponse &&
                        retryResponse.flask_result &&
                        retryResponse.flask_result.status !== "error"
                      ) {
                        // Intervall starten
                        console.log("Starte updateInfo Intervall...");
                        updateInterval = setInterval(updateInfo, 1000);
                      } else {
                        alert("Fehler beim Neustart des Auftrags!");
                      }
                    } catch (err) {
                      console.error("Fehler beim Entfernen oder Neustarten:", err);
                      alert("Fehler beim Neustart des Auftrags!");
                    }
                  } else {
                    console.log("Nutzer hat Neustart abgebrochen.");
                    setStop();
                  }
                } else if (
                  response &&
                  response.flask_result &&
                  response.flask_result.status !== "error"
                ) {
                  // Kein Fehler: Auftrag erfolgreich gestartet
                  console.log("Auftrag erfolgreich gestartet.");
                  updateInterval = setInterval(updateInfo, 1000);
                } else {
                  alert("Prozess konnte nicht gestartet werden (API antwortete negativ).");
                }
              } catch (err) {
                console.error("Fehler beim Starten des Prozesses:", err);
                alert("Fehler beim Starten des Prozesses!");
              }
            } else {
              //if pressing stop
              setStop();
            }
          });
        }

        function setStop() {
          isRunning = false;
          btn.innerHTML = '<i class="fas fa-play"></i><span>Start</span>';
          btn.classList.remove("btn-stop");
          btn.classList.add("btn-start");

          // Intervall stoppen, falls aktiv
          if (typeof updateInterval !== "undefined") clearInterval(updateInterval);

          currentStep = 0;
          updateSteps(0);
        }

        async function loadCheck() {
          const check = await checkIfExists(); // ← hier war das Problem!
          if (check) {
            await moveToDefect();
            auftragsId.value = "";
            sizeSelect.value = "s";
            objectId.value = "A01"
          } else {
            updateSteps(1);
            data = await getAuftrag();

            //   console.log(data.auftrag.name);
            try {
              if (!data || !data.auftrag) {
                console.warn("⚠️ Kein Auftrag im Response vorhanden:", data);
                objectId.value = "";
                sizeSelect.value = "";
                auftragsId.value = "";
                return; // Funktion hier beenden, da keine Daten vorhanden
              }
              console.log("data:  " + data);

              const name = data.auftrag.name || "";
              const descRaw = data.auftrag.desc || "{}";

              // Name sicher parsen
              const parts = name.split("|").map(s => s.trim());
              const auftragId = parts[0] || "";
              const id_data = parts[1] || "";
              const size = parts[2] || "s";

              // desc sicher parsen
              let desc;
              try {
                desc = JSON.parse(descRaw);
              } catch {
                desc = {};
              }

              console.log("🧾 Auftrag:", desc);

              // Felder setzen
              objectId.value = id_data;
              sizeSelect.value = size;
              auftragsId.value = auftragId;

            } catch (err) {
              console.error("❌ Fehler beim Verarbeiten des Auftrags:", err);
              objectId.value = "";
              sizeSelect.value = "";
              auftragsId.value = "";
            }
          }
        }
        // Initialisiere die Schritte
        updateSteps(0);
        loadCheck()
        // CSS für Fehler-Animationen hinzufügen
        const style = document.createElement('style');
        style.textContent = `
    @keyframes slideInRight {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    
    @keyframes slideOutRight {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(100%);
        opacity: 0;
      }
    }
  `;
        document.head.appendChild(style);
        window.scrollTo(0, 30); // initial setzen

      </script>
      
</body>

</html>