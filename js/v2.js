/* (c) alexey pegov, 2008 */

jQuery.postJSON = function(url, data, callback) {
  $.post(url, data, callback, "json");
};

jQuery.getJSON = function(url, data, callback) {
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
            return false
        }
        if (this.value.length >= A && F.charCode > 8 && F.charCode < 63200) {
            return false
        }
        if (this.style.height != B) {
            var E = this;
            setTimeout(function() {
                if (E.value.indexOf("\n") != -1 || E.scrollTop > 0 || E.scrollLeft > 0 || E.scrollHeight > E.offsetHeight) {
                    E.style.height = B
                }
            }, 10)
        }
    });
    return this
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
    empty.select();
  }

  return empty != null;
};

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
});


clickHandlers.create = function(e) {
  var create = $('#create');
  if (create.length > 0) {
    $('#create input[type=text]:first').select();
    return;
  }
  
  $.getJSON("/new", {}, function(data) {
    var form = $(data.html);
    $('#head').after(form);
    form.find('input[type=text]').select();

    form.find('input[type=submit]').click(function(T) {
      if (!form.selectEmptyFormElement()) {
        form.find('input[type=submit]').disable();
        $.postJSON('/create', form.getFormData(), function(data) {
          // todo!!!
        });
      }
    });
  });
};

clickHandlers.cancelCreate = function(e) {
  $('#create').remove();
};

clickHandlers.remove = function(e) {
  alert('REMOVE');
};

clickHandlers.edit = function(e) {
  alert('EDIT');
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
        pl.replaceWith('<div class="c commentform">%(form)</div>'.replace('%(form)', wrapper));
      }
    }
  }

  N.find("input[type=submit]").click(function(E) {
      var note = $(E.target).parents(".note");
      if (!note.selectEmptyFormElement()) {
        note.find("input[type=submit]").disable();
        $.postJSON('/add-comment', note.getFormData(), function(data) {
          // todo!!!
        });
      }
    });

  N.find("textarea").makeExpandable(512, function() {}).focus().keypress();
};

clickHandlers.cancelComment = function(e) {
  var N = e.parents(".note");
  var cs = N.find(".c");
  if (cs.length == 1) {
    var cwl = N.find(".cwl");
    if (cwl.length) {
      var cw = cwl.prev(".cw");
      if (cw.length) {
        cwl.remove();
        cw.show();
      }
    }
  } else {
    N.find(".commentform").replaceWith('<div class="c add ll"><a href="#" class="l_comment">Добавить комментарий</a></div>');
  }
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
      CS.append('<div class="c add ll"><a href="#" class="l_comment">Добавить комментарий</a></div>');
      W.replaceWith(C);
  });
};
