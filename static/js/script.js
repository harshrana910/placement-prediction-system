/* =============================================================
   PLACEMENT PREDICTION SYSTEM — Premium JavaScript
   Author: Harsh Rana
   ============================================================= */

'use strict';

// ── Mesh / Particle Background ──────────────────────────────
(function initMeshBackground() {
  const canvas = document.getElementById('mesh-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let W, H, particles;

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function createParticles() {
    const count = Math.min(Math.floor((W * H) / 18000), 60);
    particles = Array.from({ length: count }, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      r: Math.random() * 1.5 + 0.5,
      dx: (Math.random() - 0.5) * 0.4,
      dy: (Math.random() - 0.5) * 0.4,
      opacity: Math.random() * 0.5 + 0.1,
    }));
  }

  function drawLine(p1, p2, dist, maxDist) {
    const alpha = (1 - dist / maxDist) * 0.12;
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.strokeStyle = `rgba(99,130,246,${alpha})`;
    ctx.lineWidth = 0.8;
    ctx.stroke();
  }

  function animate() {
    ctx.clearRect(0, 0, W, H);
    const maxDist = 140;

    particles.forEach((p, i) => {
      p.x += p.dx;
      p.y += p.dy;
      if (p.x < 0 || p.x > W) p.dx *= -1;
      if (p.y < 0 || p.y > H) p.dy *= -1;

      // Draw dot
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(99,130,246,${p.opacity})`;
      ctx.fill();

      // Connect nearby particles
      for (let j = i + 1; j < particles.length; j++) {
        const q = particles[j];
        const dist = Math.hypot(p.x - q.x, p.y - q.y);
        if (dist < maxDist) drawLine(p, q, dist, maxDist);
      }
    });

    requestAnimationFrame(animate);
  }

  window.addEventListener('resize', () => { resize(); createParticles(); });
  resize();
  createParticles();
  animate();
})();

// ── Navbar scroll effect ────────────────────────────────────
(function initNavbar() {
  const nav = document.querySelector('.navbar');
  if (!nav) return;
  window.addEventListener('scroll', () => {
    nav.style.boxShadow = window.scrollY > 20
      ? '0 4px 24px rgba(0,0,0,0.5)'
      : 'none';
  }, { passive: true });
})();

// ── Form loading state & submit ─────────────────────────────
(function initForm() {
  const form = document.getElementById('predict-form');
  if (!form) return;

  const btn = form.querySelector('.btn-predict');

  form.addEventListener('submit', function (e) {
    if (!form.checkValidity()) return;
    btn.classList.add('loading');
    btn.disabled = true;
    // Re-enable after 8s in case of server error
    setTimeout(() => {
      btn.classList.remove('loading');
      btn.disabled = false;
    }, 8000);
  });
})();

// ── Result Card Animation & Probability Bar ──────────────────
(function initResult() {
  const resultCard = document.getElementById('result-card');
  if (!resultCard) return;

  // Show the card (hidden by default in CSS)
  resultCard.classList.add('show');

  // Animate probability bar
  const fill = resultCard.querySelector('.prob-fill');
  const probVal = resultCard.dataset.prob;
  if (fill && probVal) {
    setTimeout(() => {
      fill.style.width = probVal + '%';
    }, 300);
  }

  // Smooth scroll to result
  setTimeout(() => {
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, 200);
})();

// ── Dashboard: Animated Counters ────────────────────────────
(function initCounters() {
  const counters = document.querySelectorAll('[data-count]');
  if (!counters.length) return;

  function animateCount(el) {
    const target = parseFloat(el.dataset.count);
    const isInt = Number.isInteger(target);
    const duration = 1200;
    const start = performance.now();

    function step(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = eased * target;
      el.textContent = isInt ? Math.round(current) : current.toFixed(1);
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  // Use IntersectionObserver to trigger when visible
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCount(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  counters.forEach(el => observer.observe(el));
})();

// ── Dashboard: Ratio Bar ────────────────────────────────────
(function initRatioBar() {
  const fill = document.querySelector('.ratio-fill');
  if (!fill) return;
  const pct = parseFloat(fill.dataset.pct) || 0;

  const observer = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) {
      setTimeout(() => { fill.style.width = pct + '%'; }, 200);
      observer.disconnect();
    }
  }, { threshold: 0.5 });
  observer.observe(fill);
})();

// ── Dashboard: Mini Prob Bars ───────────────────────────────
(function initMiniProbBars() {
  const fills = document.querySelectorAll('.mini-prob-fill');
  if (!fills.length) return;

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const pct = entry.target.dataset.pct || 0;
        setTimeout(() => { entry.target.style.width = pct + '%'; }, 100);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  fills.forEach(f => observer.observe(f));
})();

// ── Input field hints & validation ─────────────────────────
(function initInputHints() {
  // CGPA validation (0–10)
  const cgpa = document.getElementById('input-cgpa');
  if (cgpa) {
    cgpa.addEventListener('input', () => {
      const v = parseFloat(cgpa.value);
      if (v < 0 || v > 10) {
        cgpa.style.borderColor = 'var(--clr-danger)';
      } else {
        cgpa.style.borderColor = '';
      }
    });
  }

  // SoftSkillsRating validation (1–10)
  const soft = document.getElementById('input-softskills');
  if (soft) {
    soft.addEventListener('input', () => {
      const v = parseInt(soft.value);
      if (v < 1 || v > 10) {
        soft.style.borderColor = 'var(--clr-danger)';
      } else {
        soft.style.borderColor = '';
      }
    });
  }

  // AptitudeScore validation (0–100)
  const apt = document.getElementById('input-aptitude');
  if (apt) {
    apt.addEventListener('input', () => {
      const v = parseInt(apt.value);
      if (v < 0 || v > 100) {
        apt.style.borderColor = 'var(--clr-danger)';
      } else {
        apt.style.borderColor = '';
      }
    });
  }
})();

// ── Smooth fade-in for elements ─────────────────────────────
(function initFadeIn() {
  const els = document.querySelectorAll('.tech-card, .stat-card');
  if (!els.length) return;

  const observer = new IntersectionObserver(entries => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        entry.target.style.animationDelay = (i * 60) + 'ms';
        entry.target.classList.add('fade-in');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  els.forEach(el => observer.observe(el));
})();
