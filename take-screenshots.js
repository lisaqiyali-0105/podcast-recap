/**
 * take-screenshots.js
 * Generates 4 screenshots for the README:
 *   0-notebook.png   — notebook index with cards
 *   1-hero.png       — note hero section
 *   2-lesson.png     — lesson 1 (pull quote + PM Translation + In Practice)
 *   3-reflections.png — reflections section (DoorDash — has Before/After)
 *
 * Run: node take-screenshots.js
 * Requires: playwright (already installed), python3 (for local server)
 */

const { chromium } = require('playwright');
const { spawn }    = require('child_process');
const path         = require('path');
const fs           = require('fs');

const PORT    = 8765;
const BASE    = `http://localhost:${PORT}`;
const OUT_DIR = path.resolve(__dirname, 'screenshots');

if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR);

function startServer() {
  const srv = spawn('python3', ['-m', 'http.server', String(PORT), '--directory', __dirname], {
    stdio: 'ignore',
  });
  // Give the server a moment to bind
  return new Promise(resolve => setTimeout(() => resolve(srv), 800));
}

async function screenshot(page, name, clip) {
  await page.screenshot({ path: path.join(OUT_DIR, name), clip, animations: 'disabled' });
  console.log(`✓ ${name}`);
}

(async () => {
  const server = await startServer();
  const browser = await chromium.launch();

  try {
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1280, height: 900 });

    // ── 0. NOTEBOOK INDEX ───────────────────────────────────────────────
    await page.goto(`${BASE}/notebook/`, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(600);
    await screenshot(page, '0-notebook.png', { x: 0, y: 0, width: 1280, height: 900 });

    // ── Load SpaceX note ────────────────────────────────────────────────
    await page.goto(`${BASE}/notebook/notes/2026-04-09-spacex-pm-playbook.html`, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(600);

    // ── 1. HERO ─────────────────────────────────────────────────────────
    await screenshot(page, '1-hero.png', { x: 0, y: 0, width: 1280, height: 560 });

    // ── 2. LESSON 1 ──────────────────────────────────────────────────────
    await page.evaluate(() => document.getElementById('lesson-1').scrollIntoView({ block: 'start' }));
    await page.waitForTimeout(200);
    const lesson1 = await page.evaluate(() => {
      const el  = document.getElementById('lesson-1');
      const rect = el.getBoundingClientRect();
      return { y: rect.top, height: rect.height };
    });
    await screenshot(page, '2-lesson.png', {
      x: 0, y: lesson1.y, width: 1280, height: Math.min(lesson1.height, 820),
    });

    // ── 3. REFLECTIONS (DoorDash — has Before/After structure) ───────────
    await page.goto(`${BASE}/notebook/notes/2026-04-11-doordash-investor-playbook.html`, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(600);
    await page.evaluate(() => document.getElementById('reflect').scrollIntoView({ block: 'start' }));
    await page.waitForTimeout(300);
    const reflectY = await page.evaluate(() => document.getElementById('reflect').getBoundingClientRect().top);
    await screenshot(page, '3-reflections.png', { x: 0, y: reflectY, width: 1280, height: 720 });

  } finally {
    await browser.close();
    server.kill();
    console.log('\nAll screenshots saved to screenshots/');
  }
})();
