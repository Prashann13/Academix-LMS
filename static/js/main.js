
document.addEventListener("DOMContentLoaded", function () {

  var sidebar = document.getElementById("sidebar");
  var backdrop = document.getElementById("sidebarBackdrop");
  var sidebarToggle = document.getElementById("sidebarToggle");

  function closeSidebar() {
    sidebar.classList.remove("open");
    backdrop.classList.remove("show");
  }

  if (sidebar && backdrop && sidebarToggle) {
    sidebarToggle.addEventListener("click", function () {
      sidebar.classList.toggle("open");
      backdrop.classList.toggle("show");
    });
    backdrop.addEventListener("click", closeSidebar);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeSidebar();
    });
  }

  var path = window.location.pathname;
  document.querySelectorAll(".sidebar .nav-item").forEach(function (link) {
    if (link.getAttribute("href") === path) {
      link.classList.add("active");
    }
  });

  document.querySelectorAll("[data-table-search]").forEach(function (table) {
    var wrapper = document.createElement("div");
    wrapper.className = "mb-3 position-relative";

    var icon = document.createElement("i");
    icon.className = "bi bi-search position-absolute";
    icon.style.cssText = "top:11px;left:12px;color:var(--lms-text-muted);";

    var input = document.createElement("input");
    input.type = "text";
    input.className = "form-control ps-5";
    input.placeholder = "Type to filter rows…";
    input.setAttribute("aria-label", "Filter table rows");

    var counter = document.createElement("span");
    counter.className = "form-text d-block mt-1";

    var tableParent = table.parentNode;
    tableParent.insertBefore(wrapper, table);
    wrapper.appendChild(input);
    wrapper.appendChild(counter);
    input.insertAdjacentElement("beforebegin", icon);

    var rows = Array.prototype.slice.call(
      table.querySelectorAll("tbody tr:not(.empty-row)")
    );

    function filter() {
      var q = input.value.trim().toLowerCase();
      var visible = 0;
      rows.forEach(function (row) {
        var text = row.textContent.toLowerCase();
        var show = !q || text.indexOf(q) !== -1;
        row.classList.toggle("hide-by-filter", !show);
        if (show) visible++;
      });
      counter.textContent =
        rows.length === 0
          ? ""
          : "Showing " + visible + " of " + rows.length + " rows";
    }

    input.addEventListener("input", filter);
    filter();
  });

  document.querySelectorAll("table").forEach(function (table) {
    var sortableHeaders = table.querySelectorAll("th[data-sortable='true']");
    if (!sortableHeaders.length) return;
    var tbody = table.querySelector("tbody");

    sortableHeaders.forEach(function (th) {
      th.classList.add("sortable");

      th.addEventListener("click", function () {
        var colIndex = Array.prototype.indexOf.call(th.parentNode.children, th);
        var isAsc = th.classList.contains("sorted-asc");

        sortableHeaders.forEach(function (h) {
          h.classList.remove("sorted-asc", "sorted-desc");
        });
        th.classList.add(isAsc ? "sorted-desc" : "sorted-asc");

        var rows = Array.prototype.slice.call(
          tbody.querySelectorAll("tr:not(.empty-row)")
        );

        rows.sort(function (a, b) {
          var aText = (a.children[colIndex] || "").textContent.trim();
          var bText = (b.children[colIndex] || "").textContent.trim();
          var aNum = parseFloat(aText);
          var bNum = parseFloat(bText);

          var cmp;
          if (!isNaN(aNum) && !isNaN(bNum) && aText !== "" && bText !== "") {
            cmp = aNum - bNum;
          } else {
            cmp = aText.localeCompare(bText, undefined, { numeric: true });
          }
          return isAsc ? -cmp : cmp;
        });

        rows.forEach(function (row) { tbody.appendChild(row); });
      });
    });
  });

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  document.querySelectorAll("[data-counter]").forEach(function (el) {
    var target = parseInt(el.getAttribute("data-counter"), 10) || 0;
    if (reduceMotion || target === 0) {
      el.textContent = target;
      return;
    }
    var duration = 800;
    var start = null;

    function step(timestamp) {
      if (start === null) start = timestamp;
      var progress = Math.min((timestamp - start) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(eased * target);
      if (progress < 1) requestAnimationFrame(step);
    }
    el.textContent = "0";
    requestAnimationFrame(step);
  });

  document.querySelectorAll(".lms-alert").forEach(function (alertEl) {
    var isError =
      alertEl.classList.contains("alert-danger") ||
      alertEl.classList.contains("alert-warning");
    if (isError) return;

    setTimeout(function () {
      alertEl.classList.add("fade");
      alertEl.style.transition = "opacity 0.5s ease";
      alertEl.style.opacity = "0";
      setTimeout(function () { alertEl.remove(); }, 500);
    }, 4000);
  });

  document.querySelectorAll('input[type="password"]').forEach(function (input) {
    input.classList.add("pe-5");
    var wrap = document.createElement("div");
    wrap.className = "position-relative";
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-sm position-absolute";
    btn.style.cssText = "top:50%;right:4px;transform:translateY(-50%);border:none;";
    btn.setAttribute("aria-label", "Toggle password visibility");
    btn.innerHTML = '<i class="bi bi-eye"></i>';

    btn.addEventListener("click", function () {
      var show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.innerHTML = show ? '<i class="bi bi-eye-slash"></i>' : '<i class="bi bi-eye"></i>';
    });

    wrap.appendChild(btn);
  });

  var confirmBtn = document.querySelector("[data-confirm]");
  if (confirmBtn) {
    confirmBtn.addEventListener("click", function (e) {
      if (!confirmBtn.classList.contains("armed")) {
        e.preventDefault();
        confirmBtn.classList.add("armed");
        confirmBtn.innerHTML =
          '<i class="bi bi-exclamation-triangle me-1"></i> Click again to confirm';
      }
    });
  }

  var content = document.querySelector(".content, .auth-body");
  if (content && !reduceMotion) {
    content.classList.add("fade-in");
  }

});
