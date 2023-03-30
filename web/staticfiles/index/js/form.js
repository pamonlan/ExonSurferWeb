var fieldGroups = document.querySelectorAll('.field-group');

fieldGroups.forEach(function(fieldGroup) {
  var header = fieldGroup.querySelector('.field-group-header');
  var content = fieldGroup.querySelector('.field-group-content');

  header.addEventListener('click', function() {
    fieldGroup.classList.toggle('expanded');
    /* If value of content's display is 'none', set it to 'block', otherwise set it to 'none' */
    if (content.style.display === 'none') {
      content.style.display = 'block';
    } else {
      content.style.display = 'none';
    }
  });
});
