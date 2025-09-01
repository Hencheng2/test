// static/main.js

$(document).ready(function() {
    // Open modal
    $('body').on('click', '[data-modal-url]', function(e) {
        e.preventDefault();
        var url = $(this).data('modal-url');
        $.get(url, function(data) {
            $('#modalContent').html(data);
            $('#myModal').modal('show');
        });
    });

    // Endless scroll for posts
    var page = 1;
    $(window).scroll(function() {
        if ($(window).scrollTop() + $(window).height() >= $(document).height() - 100) {
            $.get('/api/posts/' + page, function(data) {
                $('#posts-container').append(data);
                page++;
            });
        }
    });

    // Story viewing
    $('body').on('click', '.story-circle', function() {
        var storyId = $(this).data('story-id');
        $.get('/api/view_story/' + storyId, function(data) {
            $('#modalContent').html(data);
            $('#myModal').modal('show');
        });
    });

    // Swipe for stories
    var touchStartX = 0;
    var touchEndX = 0;
    $('#myModal').on('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    });
    $('#myModal').on('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        if (touchEndX < touchStartX - 50) {
            // swipe left, next story
            // implement logic to load next
        } else if (touchEndX > touchStartX + 50) {
            // swipe right, previous
        } else if (touchEndX == touchStartX) {
            // tap, pause/play if video
            var video = $('#story-video')[0];
            if (video) {
                if (video.paused) video.play();
                else video.pause();
            }
        }
    });

    // Reel pause on touch
    $('body').on('touchstart', '.reel-video', function() {
        var video = $(this)[0];
        if (video.paused) video.play();
        else video.pause();
    });

    // Search dynamic
    $('#search-bar').on('input', function() {
        var q = $(this).val();
        var tab = $('.active-tab').data('tab');
        $.get('/api/search?q=' + q + '&tab=' + tab, function(data) {
            $('#search-results').html(data);
        });
    });

    // Form submits via AJAX
    $('body').on('submit', 'form.ajax-form', function(e) {
        e.preventDefault();
        var form = $(this);
        $.post(form.attr('action'), form.serialize(), function(response) {
            if (response.success) {
                // refresh or close modal
                $('#myModal').modal('hide');
            } else {
                alert(response.error);
            }
        }, 'json');
    });

    // More interactions...
});
