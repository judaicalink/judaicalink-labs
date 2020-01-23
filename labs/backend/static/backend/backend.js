(function($) {
  $(document).ready(function(){
    var msgSocket = new WebSocket('ws://' + window.location.host + '/ws/backend/pushmsg');

    msgSocket.onmessage = function(e) {
        var data = JSON.parse(e.data);
        var message = data['message'];
        var level = data['level'];
        var timeout = data['timeout'];
        var id = data['id'];
        var submsg = data['submsg'];
        var action = data['action'];
        if (action == 'create') {
          addMessage(id, level, message, submsg, timeout);
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


  function updateMessage(id, level, message, submsg) {
    var msgEl = $('li#' + id)
    if (! msgEl) {
      return;
    }
    if (level !== undefined) {
      $(msgEl).removeClass().addClass(level);
      
    }
    if (message !== undefined) {
      $(msgEl).find('span.msg').html(message);
    }
    if (submsg !== undefined) {
      $(msgEl).find('span.submsg').html(message);
    }
  }

  function addMessage(id, level, message, submsg, timeout) {
    //console.log('Adding message: ' + message);
    if ($('.messagelist').length == 0) {
      // console.log('messagelist created');
      $('<ul class="messagelist"></ul>').insertBefore('div#content');
    }
    var msgEl = $('<li id=' + id + ' class="' + level + '"><span class="msg">' + message + '</span><span class="submsg">' + submsg + '</span></li>').appendTo('.messagelist');
    if (timeout){
      window.setTimeout(function(){
        msgEl.remove();
      }, timeout);
    }
  }
})(django.jQuery);
