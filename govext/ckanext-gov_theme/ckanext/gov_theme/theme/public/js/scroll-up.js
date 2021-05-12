

$(window).scroll(function(){
    if ($(this).scrollTop() > 700) {
        $('.btn-scroll-up').fadeIn();
    } else {
        $('.btn-scroll-up').fadeOut();
    }
});

$('.btn-scroll-up').click(function(){
    $("html, body").animate({ scrollTop: 0 }, 600);
    return false;
});
