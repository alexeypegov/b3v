// (c) Alexey Pegov (spleaner@gmail.com) 2009-2010

$.extend({
  undef: function(E) {
    return E === undefined;
  },
  
  undefv: function(E, D) {
    return $.undef(E) ? D : E;
  },
  
  _ajax: function(url, type, data, callback, progress) {
    $.ajax({
      type: type, 
      url: url, 
      dataType: "json", 
      data: (data), 
      global: false,
      beforeSend: function(xhr) { if (progress) progress(true) },
      success: function(msg) { callback(msg) }, 
      error: function(request, textStatus, exception) { alert('AJAX ERROR!') },
      complete: function(request, textStatus) { if (progress) progress(false) } 
    });
  },
  
  get: function(url, data, callback, progress) {
    $._ajax(url, "GET", data, callback, progress);
  },
  
  post: function(url, data, callback, progress) {
    $._ajax(url, "POST", data, callback, progress);
  }
  
});

_ = function(text, content) {
  var result = "", id = false, cls = false,  p = false, tag = false;
  
  var b = "";
  for (var i = 0; i < text.length; i++) {
    var ch = text.charAt(i);
    if (ch == '#' && !p) {
      result = b.length > 0 ? '<' + b + ' id="': '<div id="';
      tag = b.length > 0 ? b : 'div';
      b = "";
      id = true;
      continue;
    } else if (ch == '.') {
      result += id ? b + '" class="' : cls ? b + ' ' : b.length > 0 ? '<' + b + ' class="' : '<div class="';
      tag = !id && !tag ? (b.length > 0 ? b : 'div')  : tag;
      b = "";
      id = false;
      cls = true;
      continue;
    } else if (ch == '[') {
      result += id ? b + '"' : cls ? b + '"' : '<' + b;
      tag = !id && !cls && !tag ? (b.length > 0 ? b : 'div') : tag;
      id = false;
      cls = false;
      p = true;
      b = "";
      continue;
    } else if (ch == '=') {
      result += ' ' + b + '="';
      b = "";
      continue;
    } else if (ch == ',') {
      result += b + '"';
      b = "";
      continue;
    } else if (ch == ']') {
      result += b + '"';
      p = false;
      b = "";
      continue;
    }
    
    b += ch;
  }
  
  tag = !tag && !id && !cls ? b : tag;
  result = (b.length > 0 ? (id || cls ? result + b + '"' : '<' + b) : result);
  
  if ($.undef(content)) {
    result += '/>';
  } else {
    if (typeof content == "function") {
      result += '>';
      content(function(text) { result += text });
      result += '</' + tag + '>';
    } else {
      result += '>' + content + '</' + tag + '>';
    }
  }

  return result;
}