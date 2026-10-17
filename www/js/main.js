// タイトル画面。スタートでゲーム本体（game/index.html）へ移動する。

const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const overlay = document.getElementById('overlay');
const startButton = document.getElementById('start');

let audioCtx = null;
const taps = [];

function resize() {
  const dpr = window.devicePixelRatio || 1;
  const { width, height } = canvas.getBoundingClientRect();
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

// ブラウザ・WebView ともに音声再生はユーザー操作を起点にしないと開始できない
function unlockAudio() {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) audioCtx = new AudioContextClass();
  }
  if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
}

function draw(now) {
  const { width, height } = canvas.getBoundingClientRect();
  ctx.clearRect(0, 0, width, height);
  for (let i = taps.length - 1; i >= 0; i--) {
    const age = (now - taps[i].t) / 400;
    if (age >= 1) {
      taps.splice(i, 1);
      continue;
    }
    ctx.strokeStyle = `rgba(255, 79, 139, ${1 - age})`;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(taps[i].x, taps[i].y, 20 + age * 40, 0, Math.PI * 2);
    ctx.stroke();
  }
  requestAnimationFrame(draw);
}

// pointer イベントでマウスとタッチをまとめて扱う
canvas.addEventListener('pointerdown', (e) => {
  const rect = canvas.getBoundingClientRect();
  taps.push({ x: e.clientX - rect.left, y: e.clientY - rect.top, t: performance.now() });
});

// ゲーム本体は game/ にある。?v= はゲーム更新時に上げ、古いキャッシュが残らないようにする
const GAME_URL = 'game/index.html?v=4';

startButton.addEventListener('click', () => {
  unlockAudio();
  location.href = GAME_URL;
});

// アプリのバックグラウンド移行時は音声を止める（Capacitor 化後も同じイベントで動作する）
document.addEventListener('visibilitychange', () => {
  if (!audioCtx) return;
  if (document.hidden) audioCtx.suspend();
  else audioCtx.resume();
});

window.addEventListener('resize', resize);
resize();
requestAnimationFrame(draw);
