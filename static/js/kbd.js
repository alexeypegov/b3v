// (c) alexey pegov (spleaner@gmail.com) 2009-2010

$.extend({
  keyCodes: {8: 'BACKSPACE', 9: 'TAB', 13: 'ENTER', 16: 'SHIFT', 17: 'CONTROL', 18: 'ALT', 27: 'ESCAPE',
              33: 'PG_UP', 34: 'PG_DN', 35: 'END', 36: 'HOME', 37: 'LEFT', 38: 'UP', 39: 'RIGHT', 40: 'DOWN',
              46: 'DELETE', 91: 'META', 0: 'UNKNOWN'},
  repeatKeys: [ 37, 38, 39, 40 ],

  controlKey: function(code) {
    return !$.undef($.keyCodes[code])
  },

  inputmap: function(stroke, callback) {
    var H = $('html');
    $._updatemap(H, stroke, callback)
  },
  
  _updatemap: function(element, stroke, callback) {
    var handlers = element.data(stroke);
    if (!handlers) {
      handlers = [];
      element.data(stroke, handlers);
    }
    
    handlers.push(callback);
  },
  
  _swap: function(e, v) {
    // fix repeat in some browsers
    // alert($.repeatKeys[]);
    return ($.repeatKeys.indexOf(e.keyCode) != -1) && ($.browser.opera || $.browser.mozilla) 
      && e.type == v ? (v == "keydown" ? "typed" : "pressed") : (v == "keydown" ? "pressed" : "typed");
  },
  
  stroke: function(e) {
    var stroke = $.modifier(e);

    var mouse_event = e.type == "click";
    switch(e.type) {
      case "keydown": stroke += $._swap(e, "keydown"); break;
      case "keyup": stroke += "released"; break;
      case "keypress": stroke += $._swap(e, "keypress"); break;
      case "click": stroke += "clicked"; break;
      default: stroke += e.type; break;
    }
    
    if (mouse_event) {
      stroke += " LEFT"; // other buttons?
    } else {
      // alert(e.keyCode + ', char: ' + e.charCode);
      var keycode = $.keyCodes[e.keyCode];
      if ($.undef(keycode)) keycode = String.fromCharCode(e.keyCode);
      stroke += " " + (e.charCode == 0 || $.undef(e.charCode) ? keycode : String.fromCharCode(e.charCode));
    }
    
    $("#debug").html("<pre>" + stroke + " (" + (e.charCode == 0 ? e.keyCode : e.charCode) + ")</pre>");
    
    return stroke;
  },
  
  modifier: function(e) {
    if (e.altKey) return "ALT ";
    if (e.shiftKey && e.charCode != 0) return "";
    if (e.shiftKey) return "SHIFT ";
    if (e.ctrlKey) return "CONTROL ";
    else if (e.metaKey) return "META "; // meta is triggered with control on macs too!
    
    return "";
  },
  
  event_handler: function(e) {
    var result = true;
    var S = $.stroke(e);
    var P = $(e.target);
    
    var focused = $(':focus');
    if (focused.length == 1) {
      P = focused;
    } else {
      var popups = $(':popup(:visible)');
      if (popups.length > 0) {
        var sorted = popups.sort(function(a, b) {
          var az = a.normz();
          var bz = b.normz();
          return az == bz ? 0 : az > bz ? 1 : -1;
        });

        P = $(sorted[0]);
      }
    }    
    
    while (P.length == 1) {
      var handlers = P.data(S);
      if (handlers) {
        for (var j = 0; j < handlers.length; j++) {
          var R = handlers[j](P);
          if (R || $.undef(R)) { // will also stop if no return value
            result = false;
            break;
          }
        }
      }
      
      if (!result) break;
      P = P.parent();
    }
    
    return result;
  },
  
  init_input: function() {
    $(document).click($.event_handler);
    $(document).keydown($.event_handler);
    $(document).keypress($.event_handler)
  }
});

$.fn.extend({
  inputmap: function(stroke, callback) {
    $._updatemap(this, stroke, callback)
  },
  
  normz: function() {
    var z = $(this).css('z-index');
    return isNaN(z) ? 0 : parseInt(z);
  }
});

$.extend($.expr[':'], {
  popup: function(a, i, m) {
    $this = $(a);
    return $this.hasClass('popup') && (!m[3] || $this.is(m[3]));
  }
});