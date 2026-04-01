// ===========================
//  IRONCODE — Coding Club JS
// ===========================

// --- Hamburger Menu ---
const hamburger = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobileMenu');

hamburger.addEventListener('click', () => {
  mobileMenu.classList.toggle('open');
});

function closeMenu() {
  mobileMenu.classList.remove('open');
}

// Close menu when clicking outside
document.addEventListener('click', (e) => {
  if (!hamburger.contains(e.target) && !mobileMenu.contains(e.target)) {
    mobileMenu.classList.remove('open');
  }
});


// --- Navbar scroll shadow ---
const navbar = document.getElementById('navbar');

window.addEventListener('scroll', () => {
  if (window.scrollY > 40) {
    navbar.style.boxShadow = '0 4px 24px rgba(0,0,0,0.5)';
  } else {
    navbar.style.boxShadow = 'none';
  }
});


// --- Scroll reveal ---
// Adds .reveal class to sections so they animate in when scrolled to
const revealTargets = document.querySelectorAll(
  '.card, .lesson-item, .project-card, .info-row, .join-form, .section h2, .section-sub, .section-tag'
);

revealTargets.forEach(el => el.classList.add('reveal'));

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      // Stagger each element slightly
      setTimeout(() => {
        entry.target.classList.add('visible');
      }, 80 * i);
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });

revealTargets.forEach(el => observer.observe(el));


// --- Signup form ---
function signup() {
  const name  = document.getElementById('nameInput').value.trim();
  const year  = document.getElementById('yearInput').value.trim();
  const msg   = document.getElementById('formMsg');
  const btn   = document.getElementById('signupBtn');

  if (!name) {
    msg.style.color = '#ff6b6b';
    msg.textContent = '⚠ Please enter your name.';
    return;
  }

  if (!year) {
    msg.style.color = '#ff6b6b';
    msg.textContent = '⚠ Please enter your year group.';
    return;
  }

  // Success state
  btn.textContent = 'REGISTERED ✓';
  btn.style.background = '#28c840';
  btn.style.cursor = 'default';
  btn.onclick = null;

  msg.style.color = '#28c840';
  msg.textContent = `✓ Welcome aboard, ${name}! See you Wednesday.`;

  document.getElementById('nameInput').disabled = true;
  document.getElementById('yearInput').disabled = true;
}

// Allow Enter key to submit
document.getElementById('nameInput').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') document.getElementById('yearInput').focus();
});

document.getElementById('yearInput').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') signup();
});


// --- Active nav link highlight on scroll ---
const sections = document.querySelectorAll('section[id], .section[id]');
const navLinks = document.querySelectorAll('.nav-links a, .mobile-menu a');

window.addEventListener('scroll', () => {
  let current = '';
  sections.forEach(section => {
    const top = section.offsetTop - 100;
    if (window.scrollY >= top) {
      current = section.getAttribute('id');
    }
  });

  navLinks.forEach(link => {
    link.style.color = '';
    if (link.getAttribute('href') === `#${current}`) {
      link.style.color = '#e8ff00';
    }
  });
});


// --- Smooth scroll for all anchor links ---
document.querySelectorAll('a[href^="#"]').forEach(link => {
  link.addEventListener('click', (e) => {
    const target = document.querySelector(link.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth' });
    }
  });
});