(function($) {
  $(document).ready(function(){
    var msgSocket = new WebSocket('ws://' + window.location.host + '/ws/backend/pushmsg');

    msgSocket.onmessage = function(e) {
        var data = JSON.parse(e.data);
        console.log('msg received: ' + data)
        var message = data['message'];
        var level = data['level'];
        var timeout = data['timeout'];
        var id = data['id'];
        var submessage = data['submessage'];
        var action = data['action'];
        if (action == 'create') {
          addMessage(id, level, message, submessage,  timeout);
        } else if (action == 'remove') {
          removeMessage(id);
        } else if (action == 'update') {
          updateMessage(id, level, message, submessage, timeout);
        }
    };

    msgSocket.onclose = function(e) {
        console.error('Chat socket closed unexpectedly: ' + e);
    };
  });


  function removeMessage(id) {
    $('li#' + id).remove();
  }


  function updateMessage(id, level, message, submessage) {
    var msgEl = $('li#' + id)
    if (! msgEl) {
      return;
    }
    if (level !== undefined) {
      $(msgEl).removeClass().addClass(level);
      
    }
    if (message !== undefined) {
      $(msgEl).find('span.message').html(message);
    }
    if (submessage !== undefined) {
      $(msgEl).find('span.submessage').html(submessage);
    }
  }

  function addMessage(id, level, message, submessage, timeout) {
    //console.log('Adding message: ' + message);
    if ($('.messagelist').length == 0) {
      // console.log('messagelist created');
      $('<ul class="messagelist"></ul>').insertBefore('div#content');
    }
    $('li#' + id).remove();
    var msgEl = $('<li id=' + id + ' class="' + level + '"><span class="message">' + message + '</span><span class="submessage">' + submessage + '</span></li>').appendTo('.messagelist');
    if (timeout){
      window.setTimeout(function(){
        msgEl.remove();
      }, timeout);
    }
  }
})(django.jQuery);
