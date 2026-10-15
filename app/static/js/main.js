// small helpers: live table filter + delete confirmation
document.addEventListener('DOMContentLoaded', function () {
  var box = document.getElementById('tableFilter');
  if (box) {
    box.addEventListener('input', function () {
      var q = box.value.toLowerCase();
      document.querySelectorAll('#dataTable tbody tr').forEach(function (tr) {
        tr.style.display = tr.textContent.toLowerCase().indexOf(q) > -1 ? '' : 'none';
      });
    });
  }
  document.querySelectorAll('form[data-confirm]').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      if (!confirm(f.getAttribute('data-confirm'))) e.preventDefault();
    });
  });
});
