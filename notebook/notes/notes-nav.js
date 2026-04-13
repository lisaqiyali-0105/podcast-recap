// ── SHARED NAV SCRIPT ──
// Used by all notes in library/notes/. Edit here to update all notes.

(function () {
  const navDots = document.querySelectorAll('.nav-dot');
  const navLabel = document.querySelector('.nav-label');

  navDots.forEach(dot => {
    dot.addEventListener('click', () => {
      const el = document.getElementById(dot.dataset.target);
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    });
  });

  const sections = document.querySelectorAll('section[id]');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        navDots.forEach(d => d.classList.remove('active'));
        const active = document.querySelector(`.nav-dot[data-target="${entry.target.id}"]`);
        if (active) {
          active.classList.add('active');
          if (navLabel) navLabel.textContent = active.getAttribute('aria-label');
        }
      }
    });
  }, { rootMargin: '-20% 0px -70% 0px' });

  sections.forEach(s => observer.observe(s));
})();
