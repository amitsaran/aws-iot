jQuery(function ($) {
  $(function () {   
    $('a').bind('click', function (event) {

      if ($(this).parents('.page-links').length) {
        $('.page-links .active').removeClass('active');
        $(this).closest('li').addClass('active');
      }
    });
  });

  $(".navbar-light .navbar-nav .nav-link").on('click', function () {
    $(".navbar-collapse").removeClass('show');
  });

});
