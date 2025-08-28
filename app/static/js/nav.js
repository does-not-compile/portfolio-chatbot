document.addEventListener("DOMContentLoaded", () => {
  const navbar = document.querySelector(".navbar");
  const navLinks = document.querySelectorAll(".nav-links a");
  const hamburger = document.querySelector(".hamburger");
  const mobileMenu = document.querySelector(".mobile-menu");
  const mobileMenuLinks = mobileMenu?.querySelectorAll("a") || [];

  const logoLink = document.querySelector(".logo a");
  logoLink?.addEventListener("click", () => toggleMobileMenu(true));

  // Detect sections from nav hrefs
  const sections = Array.from(navLinks)
    .map((link) => {
      const href = link.getAttribute("href");
      return href?.startsWith("/#")
        ? document.getElementById(href.slice(2))
        : null;
    })
    .filter(Boolean);

  const landing = document.getElementById("landing");
  const isLandingPage = !!landing;

  function updateActiveSection() {
    if (!navbar || !sections.length) return;

    let minDistance = Infinity;
    let currentSection = null;

    sections.forEach((section) => {
      const rect = section.getBoundingClientRect();
      const isPastTop = rect.top <= 0;
      const isStillOnScreen = rect.bottom > 0;

      if (isPastTop && isStillOnScreen) {
        const distance = Math.abs(rect.top);
        if (distance < minDistance) {
          minDistance = distance;
          currentSection = section;
        }
      }
    });

    if (currentSection) {
      const id = currentSection.id;
      const theme = currentSection.dataset.theme || "light";
      //console.log(theme);
      navbar.setAttribute("data-theme", theme);

      // Combine both desktop and mobile nav links
      const allLinks = [...navLinks, ...mobileMenuLinks];

      allLinks.forEach((link) => {
        const href = link.getAttribute("href") || "";
        const matches = href.endsWith(`#${id}`);
        link.classList.toggle("active", matches);
      });
    }
  }

  function toggleNavbar() {
    if (!navbar) return;

    if (isLandingPage && landing) {
      const rect = landing.getBoundingClientRect();
      const isVisible = rect.bottom > 10 && rect.top <= window.innerHeight;
      navbar.classList.toggle("visible", !isVisible);
    } else {
      navbar.classList.add("visible");
    }
  }

  function toggleMobileMenu(forceClose = false) {
    if (!hamburger || !mobileMenu) return;

    const isActive = mobileMenu.classList.contains("active");
    const shouldOpen = !isActive && !forceClose;

    hamburger.classList.toggle("open", shouldOpen);
    mobileMenu.classList.toggle("active", shouldOpen);
    document.body.style.overflow = shouldOpen ? "hidden" : "";
  }

  if (hamburger && mobileMenu) {
    hamburger.addEventListener("click", () => toggleMobileMenu());

    mobileMenuLinks.forEach((link) => {
      link.addEventListener("click", () => toggleMobileMenu(true));
    });
  }

  function onScroll() {
    updateActiveSection();
    toggleNavbar();
  }

  window.addEventListener("scroll", onScroll);
  window.addEventListener("resize", onScroll);
  onScroll(); // Initial check
});
