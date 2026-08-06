(function () {
  const root = document.documentElement;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  root.classList.add("js-enabled");

  function revealSections() {
    const targets = Array.from(document.querySelectorAll(".reveal"));
    if (!targets.length) return;
    if (reduceMotion || !("IntersectionObserver" in window)) {
      targets.forEach((item) => item.classList.add("is-visible"));
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    targets.forEach((item) => observer.observe(item));
  }

  function countMetrics() {
    const counters = Array.from(document.querySelectorAll(".js-count"));
    if (!counters.length) return;
    const setFinal = (item) => {
      item.textContent = item.dataset.value || item.textContent;
    };
    if (reduceMotion || !("IntersectionObserver" in window)) {
      counters.forEach(setFinal);
      return;
    }
    const animate = (item) => {
      const rawValue = item.dataset.value || item.textContent;
      const target = Number(rawValue.replace(/[^\d]/g, ""));
      const suffix = rawValue.includes("+") ? "+" : "";
      const hasComma = rawValue.includes(",");
      if (!Number.isFinite(target)) {
        setFinal(item);
        return;
      }
      const start = performance.now();
      const duration = 460;
      const tick = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = Math.round(target * eased);
        item.textContent = (hasComma ? value.toLocaleString("en-US") : String(value)) + suffix;
        if (progress < 1) {
          requestAnimationFrame(tick);
        } else {
          item.textContent = rawValue;
        }
      };
      requestAnimationFrame(tick);
    };
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          animate(entry.target);
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.6 }
    );
    counters.forEach((item) => observer.observe(item));
  }

  function setupLightbox() {
    const triggers = Array.from(document.querySelectorAll("[data-lightbox-src]"));
    if (!triggers.length || typeof HTMLDialogElement === "undefined") return;
    const dialog = document.createElement("dialog");
    dialog.className = "figure-dialog";
    dialog.innerHTML = '<button class="figure-dialog-close" type="button" aria-label="Close figure">Close</button><img alt="">';
    document.body.appendChild(dialog);
    const image = dialog.querySelector("img");
    const close = dialog.querySelector("button");
    let activeTrigger = null;

    triggers.forEach((trigger) => {
      trigger.addEventListener("click", () => {
        activeTrigger = trigger;
        image.src = trigger.getAttribute("data-lightbox-src");
        image.alt = trigger.getAttribute("data-lightbox-alt") || trigger.textContent.trim() || "Research figure";
        dialog.showModal();
        close.focus();
      });
    });

    close.addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
    dialog.addEventListener("close", () => {
      if (activeTrigger) activeTrigger.focus();
    });
  }

  function setupResearchMap() {
    const maps = Array.from(document.querySelectorAll("[data-research-map]"));
    if (!maps.length) return;
    maps.forEach((map) => {
      const question = map.querySelector(".map-question");
      const defaultText = question ? question.textContent : "";
      const nodes = Array.from(map.querySelectorAll(".map-node"));
      const activate = (node) => {
        nodes.forEach((item) => item.classList.toggle("is-active", item === node));
        if (question) question.textContent = node.dataset.question || defaultText;
      };
      const clear = () => {
        nodes.forEach((item) => item.classList.remove("is-active"));
        if (question) question.textContent = defaultText;
      };
      nodes.forEach((node) => {
        node.addEventListener("mouseenter", () => activate(node));
        node.addEventListener("focus", () => activate(node));
        node.addEventListener("mouseleave", clear);
        node.addEventListener("blur", clear);
      });
    });
    if (reduceMotion || !("IntersectionObserver" in window)) {
      maps.forEach((map) => map.classList.add("is-visible"));
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.26 }
    );
    maps.forEach((map) => observer.observe(map));
  }

  function setupResearchTimeline() {
    const timelines = Array.from(document.querySelectorAll("[data-research-timeline]"));
    if (!timelines.length) return;
    timelines.forEach((timeline) => {
      const stages = Array.from(timeline.querySelectorAll("article"));
      if (!stages.length) return;
      if (reduceMotion || !("IntersectionObserver" in window)) {
        stages.forEach((stage) => stage.classList.add("is-current"));
        return;
      }
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            stages.forEach((stage) => {
              const current = stage === entry.target;
              stage.classList.toggle("is-current", current);
              if (current) stage.classList.add("is-past");
            });
          });
        },
        { threshold: 0.58, rootMargin: "-18% 0px -30% 0px" }
      );
      stages.forEach((stage) => observer.observe(stage));
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    revealSections();
    countMetrics();
    setupLightbox();
    setupResearchMap();
    setupResearchTimeline();
  });
})();
