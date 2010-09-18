/* (c) alexey pegov, 2008-2009 */

jQuery.postJSON = function(url, data, callback, at) {
  if (at) {
    showProgress(at);
  }
   
  $.post(url, data, callback, "json");
};

jQuery.getJSON = function(url, data, callback, at) {
  if (at) {
    showProgress(at);
  }
   
  $.get(url, data, callback, "json");
};

jQuery.fn.disable = function() {
  this.attr("disabled", "disabled");
  return this
};

jQuery.fn.makeExpandable = function(A, D) {
    var B = "5em";
    this.keypress(function(F) {
      if (F.keyCode == 13 && D) {
        D(this);
        return false;
      }
      
      if (this.value.length >= A && F.charCode > 8 && F.charCode < 63200) {
        return false;
      }
      
      if (this.style.height != B) {
        var E = this;
        setTimeout(function() {
          if (E.value.indexOf("\n") != -1 || E.scrollTop > 0 || E.scrollLeft > 0 || E.scrollHeight > E.offsetHeight) {
            E.style.height = B;
          }
        }, 10);
      }
    });
    return this;
};

jQuery.fn.submitForm = function(action) {
  var C = $('<form method="post"></form>');
  C.attr("action", action);
  C.target = "_self";

  var data = this.getFormData();

  for (var name in data) {
    C.append($('<input type="hidden" name="' + name + '"/>').val(data[name]));
  }

  $("body").append(C);
  C.submit();
};

jQuery.fn.getFormData = function() {
  var result = {};

  var _element = this;
  jQuery.each(["input", "textarea", "select"], function() {
    _element.find(this.toString()).each(function() {
      var k = $(this);
      if (k.attr("type") != 'submit') {
        var key = k.attr("name");
        if (key.charAt(key.length - 1) == ']') {
          key = key.substring(0, key.length - 2);
          var existing = result[key];
          if (!existing) {
            existing = [];
            result[key] = existing;
          }

          existing.push(k.val());
        } else {
          result[k.attr("name")] = k.val();
        }
      }
    });
  });

  result.next = location.href;

  return result;
};

jQuery.fn.selectEmptyFormElement = function() {
  var empty = null;
  var _e = this;
  jQuery.each(["input", "textarea"], function() {
    if (empty != null) return;

    _e.find(this.toString()).each(function() {
      if (empty != null) return;

      var _f = $(this);
      if (-1 == jQuery.inArray(_f.attr("type"), ["submit", "hidden", "checkbox", "radio", "button"])) {
        if (!_f.val()) {
          empty = _f;
        }
      }
    });
  });

  if (empty) {
    empty.focus();
  }

  return empty != null;
};


function showProgress(at) {
  if (at && at.length > 0) {
    hideProgress();
    var offset = at.offset();
    var width = at.width();
    var pos = offset.left - 16;
    loader = $('<div id="progress" style="width: 16px; height: 16px; position: absolute; top: ' + offset.top + "px; left: " + pos + 'px; z-index:200000"><img src="/i/ajax-loader.gif?v=1" width="16" height="16" alt="' + 'Loading...' + '"/></div>');
    $(document.body).append(loader);
  }
}

function hideProgress() {
  $("#progress").remove();
}

function executeLink(T) {
  document.location = T.attr('href');
}

var keyCodes = {};

var clickHandlers = {};

$(function() {
  var handlers = window["clickHandlers"];
  $("body")["click"](function(E) {
    if (E.target.tagName == 'A') {
      for (var _e = E.target; _e; _e = _e.parentNode) {
        if (!_e.className) continue;
        
        var cl = _e.className.match(/\bl_([\w]+)\b/);
        if (!cl) continue;

        var handler = handlers[cl[1]];
        if (!handler) continue;

        $(_e).blur();
        return handler($(_e), E) ? undefined : false;
      }
    }
  });

  $('body').ajaxComplete(function(request, settings) {
    hideProgress();
  });

  $(document).keydown(function(e) {
    if (e.ctrlKey) {
      var anchor = keyCodes['' + e.keyCode];
      if (anchor) {
        executeLink(anchor);
      }
    }
  });

  $('a').each(function() {
    var a = this;
    if (!a.className) return;

    var key = a.className.match(/\bn_([0-9]+)\b/);
    if (!key) return;

    keyCodes[key[1]] = $(a);
  });
});

$(document).ready(function () {
});

clickHandlers.create = function(e) {
  var create = $('#note-form');
  if (create.length > 0) {
    $('#note-form input[type=text]:first').focus();
    return;
  }
  
  // avoid multi-processing while waiting response from server
  var existing_marker = $('#c_mark');
  if (existing_marker.length > 0) {
    return;
  }
  
  var marker = $('<div style="display: none;" id="c_mark"></div>');
  $('#head').after(marker);
  
  $.getJSON("/new", {}, function(data) {
    var form = $(data.html);
    $('#c_mark').replaceWith(form);
    form.find('input[type=text]:first').focus();

    form.find('input[type=submit]').click(function(T) {
      if (!form.selectEmptyFormElement()) {
        form.find('input[type=submit]').disable();
        $.postJSON('/create', form.getFormData(), function(data) {
          $('#note-form').remove();
          $('#notes').prepend(data.html);
        });
      }
    });
  });
};

clickHandlers.cancelCreate = function(e) {
  $('#note-form').remove();
  $('.note').show();
};

clickHandlers.remove = function(e) {
  if (confirm('Удалить заметку?')) {
    var P = e.parents(".note");
    if (!P) return;
    var id = P.find('input[type=hidden]').attr('value');
    if (!id) return;
    $.postJSON("/delete", {'note_id': id}, function(data) {
      if (data.status) {
        P.remove();
      } else {
        alert('Ошибка удаления!');
      }
    });
  }
};

clickHandlers.edit = function(e) {
  var P = e.parents(".note");
  if (!P) return;
  var id = P.find('input[type=hidden]').attr('value');
  if (!id) return;
  
  // avoid multi-processing while waiting response from server
  var existing_marker = $('#e_mark');
  if (existing_marker.length > 0) {
    return;
  }
  
  var marker = $('<div style="display: none;" id="e_mark"></div>');
  P.after(marker);
  
  $.getJSON("/edit/%(id)".replace('%(id)', id), {}, function(data) {
    P.hide();
    var form = $(data.html);
    marker.replaceWith(form);
    
    form.find('#c_text').text(data.content); // avoid content escaping
    form.find('textarea').focus();
    
    form.find('input[type=submit]').click(function(T) {
      if (!form.selectEmptyFormElement()) {
        form.find('input[type=submit]').disable();
        $.postJSON('/create', form.getFormData(), function(data) {
          P.remove();
          result = $(data.html)
          form.replaceWith(result);
          result.effect("highlight", {'color' : '#EFECCA'}, 1000);
        });
      }
    });
  });
};

clickHandlers.comment = function(e) {
  var wrapper = $('#new-comment-wrapper');

  var N = e.parents(".note");
  var cw = N.find(".cw");
  if (cw.length) {
    cw.hide();
    var t = $('<div class="cwl"><div class="ba"></div><div class="cs"><div class="c commentform"></div></div></div>');
    t.find('.commentform').append(wrapper.html());
    cw.after(t);
  } else {
    var cwl = N.find(".cwl");
    if (cwl.length) {
      var pl = cwl.find(".add");
      if (pl.length) {
        pl.hide();
        pl.before('<div class="c commentform">%(form)</div>'.replace('%(form)', wrapper.html()));
      }
    }
  }

  N.find("input[type=submit]").click(function(E) {
    submitComment(N);
  });

  N.find("textarea").makeExpandable(512, function() {}).focus().keypress();
  
  N.find("textarea").keydown(function(e) {
    switch(e.keyCode) {
      case 27:
        cancelComment(N.find('.commentform'));
        break;
      case 13:
        submitComment(N);
        break;
    }
  });
};

function submitComment(note) {
  if (!note.selectEmptyFormElement()) {
    note.find("input[type=submit]").disable();
    $.postJSON('/add-comment', note.getFormData(), function(data) {
      note.find('.cw').remove();
      note.find('.add').remove();
      
      var result = $(data.html);
      note.find('.commentform').replaceWith(result);
      // result.effect("highlight", {}, 1000);
      
      note.find('.add').show();
    }, note.find('.commentform'));
  }
};

function cancelComment(e) {
  var N = e.parents(".note");
  
  var cw = N.find('.cw');
  var cwl = N.find('.cwl');
  
  if (cw.length) {
    cw.show();
    cwl.remove();
  } else {
    cwl.find('.commentform').remove();
    cwl.find('.add').show();
  }
};

clickHandlers.cancelComment = function(e) {
  cancelComment(e);
};

clickHandlers.expand = function(e) {
  var P = e.parents(".note");
  if (!P) return;
  var id = P.find('input[type=hidden]').attr('value');
  if (!id) return;
  var W = e.parents(".cw");
  if (!W) return;

  $.postJSON("/fetch-comments", {'note_id': id}, function(data) {
      var C = $('<div class="cwl"><div class="ba"></div></div>');
      var CS = $('<div class="cs">%(data)</div>'.replace('%(data)', data.html));
      C.append(CS);
      W.replaceWith(C);
  }, P.find('.w'));
};
