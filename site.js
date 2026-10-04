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

  var form = document.getElementById("contact-form");
  if (!form) return;

  form.addEventListener("submit", function (e) {
    if (!form.checkValidity()) return;
    e.preventDefault();
    var data = new FormData(form);
    var name = String(data.get("name") || "").trim();
    var email = String(data.get("email") || "").trim();
    var phone = String(data.get("phone") || "").trim();
    var county = String(data.get("county") || "").trim();
    var message = String(data.get("message") || "").trim();
    var body = [
      "Name: " + name,
      "Email: " + email,
      "Phone: " + phone,
      "County: " + county,
      "",
      message
    ].join("\n");
    var href = "mailto:info@phoenixrestoration.net?subject=" +
      encodeURIComponent("Project inquiry from " + name) +
      "&body=" + encodeURIComponent(body);
    var status = document.getElementById("form-status");
    if (status) {
      status.textContent = "Opening your email app with this message addressed to info@phoenixrestoration.net. If nothing opens, email that address directly. This page does not store what you typed.";
    }
    window.location.href = href;
  });
})();
