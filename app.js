const menuButton = document.querySelector('[data-menu-button]');
const drawer = document.querySelector('[data-drawer]');

if (menuButton && drawer) {
  menuButton.addEventListener('click', () => {
    const isOpen = drawer.classList.toggle('is-open');
    menuButton.setAttribute('aria-expanded', String(isOpen));
  });

  drawer.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      drawer.classList.remove('is-open');
      menuButton.setAttribute('aria-expanded', 'false');
    });
  });
}

const observer = 'IntersectionObserver' in window
  ? new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 })
  : null;

document.querySelectorAll('.reveal').forEach((node) => {
  if (observer) {
    observer.observe(node);
  } else {
    node.classList.add('is-visible');
  }
});
