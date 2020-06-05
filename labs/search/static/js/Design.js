
/*-------------------SIDEBAR-------------------------*/
$(document).ready(function () {
            $("#sidebar").mCustomScrollbar({
                theme: "minimal"
            });

            $('#sidebarCollapse').on('click', function () {
                $('#sidebar, #content').toggleClass('active');
                $('.collapse.in').toggleClass('in');
                $('a[aria-expanded=true]').attr('aria-expanded', 'false');
            });
        });

/*------------Sidebar active page highlighting---------------*/
/*$(document).on('click', 'ul li', function(){
                $(this).addClass('active').siblings().removeClass('active')
                })
/*---------------------------------------------------*/
/*let ul = document.querySelector('ul');
let li = document.querySelector('li');

li.forEach(el => {
    el.addEventListener('click',function(){
        ul.querySelector('.active').classList.
            remove('active');

        el.classList.add('active');
        });
    });*/
/*---------------------------------------------------*/
/*$(document).on('click', 'ul li', function(){
                $(this).addClass('current').siblings().removeClass('current')
                })*/
