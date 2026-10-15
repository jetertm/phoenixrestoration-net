(function () {
  var toggle = document.getElementById("nav-toggle");
  var nav = document.getElementById("site-nav");

  function setOpen(open) {
    if (!toggle || !nav) return;
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    nav.classList.toggle("is-open", open);
    document.body.classList.toggle("nav-open", open);
  }

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });
    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        setOpen(false);
      });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") setOpen(false);
    });
  }

  var year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());

  var LOCAL_TEST_SITEKEY = "1x00000000000000000000AA";
  var quoteWidgetId = null;
  var turnstileApiReady = false;

  window.phoenixTurnstileReady = function () {
    turnstileApiReady = true;
    renderQuoteWidget();
  };

  function renderQuoteWidget() {
    var slot = document.getElementById("turnstile-slot");
    var form = document.getElementById("quote-form");
    if (!slot || !form || !form.dataset.sitekey || !turnstileApiReady || !window.turnstile) return;
    if (quoteWidgetId !== null) return;
    quoteWidgetId = window.turnstile.render("#turnstile-slot", {
      sitekey: form.dataset.sitekey,
      action: "quote",
      theme: "light",
    });
  }

  function resetQuoteWidget() {
    if (quoteWidgetId !== null && window.turnstile) {
      window.turnstile.reset(quoteWidgetId);
    }
  }

  function loadTurnstile() {
    if (document.getElementById("turnstile-api")) {
      renderQuoteWidget();
      return;
    }
    var script = document.createElement("script");
    script.id = "turnstile-api";
    script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit&onload=phoenixTurnstileReady";
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
  }

  function isLocalPreview() {
    return location.hostname === "localhost" || location.hostname === "127.0.0.1";
  }

  async function quoteSiteKey() {
    try {
      var response = await fetch("/api/turnstile-sitekey", { headers: { accept: "application/json" } });
      if (response.ok) {
        var data = await response.json();
        if (data && data.sitekey) return data.sitekey;
      }
    } catch (error) {
      /* Static preview has no function. Localhost falls back to the test widget. */
    }
    return isLocalPreview() ? LOCAL_TEST_SITEKEY : "";
  }

  var quoteForm = document.getElementById("quote-form");
  if (quoteForm) {
    var status = document.getElementById("quote-status");
    var thanks = document.getElementById("quote-thanks");
    var submit = quoteForm.querySelector("[type=submit]");

    quoteSiteKey().then(function (sitekey) {
      if (!sitekey) {
        if (status) {
          status.textContent = "The quote form's security check isn't set up on this copy of the site yet. Call (334) 327-7450 and we'll take the details.";
        }
        if (submit) submit.disabled = true;
        return;
      }
      quoteForm.dataset.sitekey = sitekey;
      loadTurnstile();
    });

    quoteForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      if (!quoteForm.reportValidity()) return;
      var photo = quoteForm.querySelector("#photo");
      if (photo && photo.files && photo.files[0] && photo.files[0].size > 2 * 1024 * 1024) {
        if (status) status.textContent = "Photo must be 2 MB or smaller.";
        return;
      }
      if (status) status.textContent = "";
      if (submit) submit.disabled = true;

      try {
        var response = await fetch("/api/quote", {
          method: "POST",
          body: new FormData(quoteForm),
          headers: { accept: "application/json" },
        });
        var data = {};
        try {
          data = await response.json();
        } catch (error) {
          data = {};
        }
        if (response.ok && data.ok) {
          quoteForm.hidden = true;
          if (thanks) {
            thanks.hidden = false;
            var heading = thanks.querySelector("h2");
            if (heading) heading.focus();
          }
          return;
        }
        if (status) {
          status.textContent = data.message || "We couldn't send that. Please call (334) 327-7450.";
        }
        resetQuoteWidget();
      } catch (error) {
        if (status) status.textContent = "We couldn't send that. Please call (334) 327-7450.";
        resetQuoteWidget();
      } finally {
        if (submit && !quoteForm.hidden) submit.disabled = false;
      }
    });
  }

  var recent = document.getElementById("recent-work");
  if (recent) {
    var jobsUrl = recent.getAttribute("data-jobs");
    fetch(jobsUrl)
      .then(function (response) {
        if (!response.ok) throw new Error("jobs");
        return response.json();
      })
      .then(function (data) {
        renderRecentWork(recent, data && data.jobs);
      })
      .catch(function () {
        if (!recent.children.length) {
          recent.textContent = "Recent photos will show here once they're added.";
        }
      });
  }

  function safeAssetPath(value) {
    if (typeof value !== "string") return "";
    if (!/^assets\/[A-Za-z0-9._/-]+$/.test(value)) return "";
    if (value.indexOf("..") !== -1) return "";
    return value;
  }

  function renderRecentWork(root, jobs) {
    root.textContent = "";
    if (!Array.isArray(jobs) || !jobs.length) {
      root.textContent = "Recent photos will show here once they're added.";
      return;
    }
    jobs.forEach(function (job) {
      var before = safeAssetPath(job.before);
      var after = safeAssetPath(job.after);
      if (!before || !after) return;
      var card = document.createElement("article");
      card.className = "job-card";

      var heading = document.createElement("h3");
      heading.textContent = job.title || "Recent job";
      card.appendChild(heading);

      var meta = document.createElement("p");
      meta.className = "job-meta";
      var bits = [];
      if (job.trade) bits.push(job.trade);
      if (job.town) bits.push(job.town);
      meta.textContent = bits.join(" · ");
      if (bits.length) card.appendChild(meta);

      var pair = document.createElement("div");
      pair.className = "pair";
      pair.appendChild(shot(before, job.beforeAlt || "Before", "Before"));
      pair.appendChild(shot(after, job.afterAlt || "After", "After"));
      card.appendChild(pair);
      root.appendChild(card);
    });
    if (!root.children.length) {
      root.textContent = "Recent photos will show here once they're added.";
    }
  }

  function shot(src, alt, label) {
    var figure = document.createElement("figure");
    var img = document.createElement("img");
    img.src = src;
    img.alt = alt;
    img.loading = "lazy";
    img.width = 960;
    img.height = 720;
    var caption = document.createElement("figcaption");
    caption.textContent = label;
    figure.appendChild(img);
    figure.appendChild(caption);
    return figure;
  }
})();
