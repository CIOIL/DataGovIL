$('.sel').each(function() {
  var $current = $(this);

  $(this).find('option').each(function(i) {
    if ($(this).is(':selected')) {
      $current.prepend($('<div>', {
        class: $current.attr('class').replace(/sel/g, 'sel__box')
      }));

      var placeholder = $(this).text();
      $current.prepend($('<span>', {
        class: $current.attr('class').replace(/sel/g, 'sel__placeholder'),
        text: placeholder
      }));

      $current.children('div').append($('<span>', {
        class: $current.attr('class').replace(/sel/g, 'sel__box__options'),
        text: $(this).text()
      }));

      $('.sel__box').find('span').addClass("selected");
    }
  });

  $(this).find('option').each(function(i) {
    if(!$(this).is(':selected')){
      $current.children('div').append($('<span>', {
      class: $current.attr('class').replace(/sel/g, 'sel__box__options'),
      text: $(this).text()
      }));
    }
  });

  $current.children('div').find('span').each(function() {
    $(this).append('<i class="check-icon">');
  });
});

// Toggling the `.active` state on the `.sel`.
$('.sel').click(function() {
  $(this).toggleClass('active');
});

// Toggling the `.selected` state on the options.
$('.sel__box__options').click(function() {
  var txt = $(this).text();
  var index = $(this).index();

  $(this).siblings('.sel__box__options').removeClass('selected');
  $(this).addClass('selected');

  var $currentSel = $(this).closest('.sel');
  $currentSel.children('.sel__placeholder').text(txt);
  $currentSel.children('select').prop('selectedIndex', index + 1);

  $('select').find('option').removeAttr("selected");
  $('select option:contains(' + txt + ')').attr('selected', 'selected');
  $('select option:contains(' + txt + ')').change();
});
