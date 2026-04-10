/**
 * take-screenshots.js
 * Generates 3 screenshots of spacex-pm-playbook.html for the README.
 * Run: node take-screenshots.js
 */

const { chromium } = require('playwright');
const path = require('path');

const HTML_FILE = path.resolve(__dirname, 'library/playbooks/2026-04-09-spacex-pm-playbook.html');
const OUT_DIR   = path.resolve(__dirname, 'screenshots');
const FILE_URL  = `file://${HTML_FILE}`;

async function screenshot(page, name, clip, { waitFor } = {}) {
  if (waitFor) await page.evaluate(waitFor);
  await page.screenshot({
    path: path.join(OUT_DIR, name),
    clip,
    animations: 'disabled',
  });
  console.log(`✓ ${name}`);
}

(async () => {
  const browser = await chromium.launch();
  const page    = await browser.newPage();

  // 1280×900 — looks like a real browser window
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto(FILE_URL, { waitUntil: 'networkidle' });

  // Wait for web fonts to load
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(600); // short extra settle for Quill CDN

  // ── 1. HERO ─────────────────────────────────────────────────────────
  // Capture from top: header (52px) + full hero section
  await screenshot(page, '1-hero.png', { x: 0, y: 0, width: 1280, height: 580 });

  // ── 2. LESSON (Lesson 1) ─────────────────────────────────────────────
  // Scroll to lesson-1 section and capture it
  await page.evaluate(() => {
    document.getElementById('lesson-1').scrollIntoView({ block: 'start' });
  });
  await page.waitForTimeout(200);

  const lesson1 = await page.evaluate(() => {
    const el = document.getElementById('lesson-1');
    const rect = el.getBoundingClientRect();
    return { y: rect.top, height: rect.height };
  });

  // Clamp height to a readable window — lesson can be tall
  const lessonH = Math.min(lesson1.height, 820);
  await screenshot(page, '2-lesson.png', { x: 0, y: lesson1.y, width: 1280, height: lessonH });

  // ── 3. REFLECTIONS ───────────────────────────────────────────────────
  await page.evaluate(() => {
    document.getElementById('reflect').scrollIntoView({ block: 'start' });
  });
  await page.waitForTimeout(300);

  const reflectY = await page.evaluate(() => {
    return document.getElementById('reflect').getBoundingClientRect().top;
  });

  await screenshot(page, '3-reflections.png', { x: 0, y: reflectY, width: 1280, height: 680 });

  await browser.close();
  console.log('\nAll screenshots saved to screenshots/');
})();
