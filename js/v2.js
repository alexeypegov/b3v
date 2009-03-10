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

function submitForm(action, data) {
    var C = $('<form method="post"></form>');
    C.attr("action", action);
    C.target = "_self";
    data.next = location.href;
    for (var name in data) {
      C.append($('<input type="hidden" name="' + name + '"/>').val(data[name]))
    }
    $("body").append(C);
    C.submit()
}

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
  $.getJSON("/create", {}, function(data) {
    $('#head').after(data.html);
  });
};

clickHandlers.comment = function(e) {
  var form = '<div class="area"><textarea name="comment" rows="1"></textarea></div>' + 
      '<div class="auth">' + 
      '<div class="form"><select name="type">' + 
      '<option value="0">OpenID</option>' + 
      '<option value="1">LiveJournal</option>' + 
      '<option value="2">Wordpress</option>' +
      '<option value="3">Dairy.ru</option>' +
      '<option value="4">Liveinternet.ru</option>' +
      '</select><input type="text" class="uname openid" name="user" value="user.yourprovider.com"/>' + 
      '<input type="checkbox" checked="true"/><label for="">Запомнить меня на этом компьютере</label>' + 
      '</div></div>' +
      '<div class="buttons ll"><input type="submit" value="Войти и все дела..."/>' + 
      '<a href="#" class="l_cancelComment">Отменить</a></div>';

  if (currentUserId) {
    form = '<div class="area"><textarea name="comment" rows="1"></textarea></div><div class="buttons ll"><input type="submit" value="Добавить"/><a href="#" class="l_cancelComment">Отменить</a></div>';
  }

  var N = e.parents(".note");
  var cw = N.find(".cw");
  if (cw.length) {
    cw.hide();
    cw.after('<div class="cwl"><div class="ba"></div><div class="cs"><div class="c commentform">%(form)</div></div></div>'.replace('%(form)', form));
  } else {
    var cwl = N.find(".cwl");
    if (cwl.length) {
      var pl = cwl.find(".add");
      if (pl.length) {
        pl.replaceWith('<div class="c commentform">%(form)</div>'.replace('%(form)', form));
      }
    }
  }

  N.find("input[type=submit]").click(function(E) {
      var note = $(E.target).parents(".note");
      var t = note.find("textarea");
      if (!t.val()) {
        t.select();
        return false
      }

      var u = note.find("input[type=text]");
      if (u && !u.val()) {
        u.select();
        return false
      }

      // todo: submit
      note.find("input[type=submit]").disable();
      submitForm("/session/create", {});
    });

  N.find("textarea").makeExpandable(512, function() {}).focus().keypress();

  var s = N.find("select");
  if (s) {
    s.change(function() {
        var u = N.find(".uname");
        var _name = "username";
        var _oname = "user.yourprovider.com";
        var current = u.val();
        u.attr("class", "uname");
        switch (this.value) {
          case "0": 
            if (current == _name || current == '') {
              u.val(_oname);
              u.select();
            }
            break; 
          default: 
            if (current == _oname || current == '') {
              u.val(_name);
              u.select();
            }
        }

        switch (this.value) {
          case "0": u.addClass("openid"); break;
          case "1": u.addClass("lj"); break;
          default: u.addClass("other"); break;
        }

        u.focus();
      });
  }
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
  var id = P.attr("id");
  if (!id) return;
  var W = e.parents(".cw");
  if (!W) return;

  $.postJSON("/notes/comments/%(id)".replace("%(id)", id), {}, function(data) {
      var C = $('<div class="cwl"><div class="ba"></div></div>');
      var CS = $('<div class="cs"></div>');
      C.append(CS);
      $.each(data, function(i, item) {
          var user = item.comment.user_name != null ? item.comment.user_name : '<a href="%(url)">%(name)</a>'.replace('%(url)', item.comment.user.identity_url).replace('%(name)', item.comment.user.presentable_name);
          CS.append('<div class="c"><span>%(text)</span><span class="author ll">&nbsp;&#151;&nbsp;%(user)</span></div>'.replace('%(text)', item.comment.text).replace('%(user)', user));
        });

      CS.append('<div class="c add ll"><a href="#" class="l_comment">Добавить комментарий</a></div>');
      
      W.replaceWith(C);
  });
};
