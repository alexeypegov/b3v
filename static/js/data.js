// (c) alexey pegov (spleaner@gnail.com) 2009-2010

$.extend({
  req: function(cmd, params, fun) {
  params['name'] = cmd;
  // $("#debug").html("<pre>queue: " + $.dump(params) + "</pre>");
  $.post("/data", {'json': JSON.stringify(params)}, function(data) {
    // $("#debug").append("<pre>response: " + $.dump(data) + "</pre>");
    if (!$.undef(data.status) && data.status == false) {
      alert(data.error);
    } else fun(data)
  }, function(start) {
    // TBD
  });
  },
  
  save: function(id, text, tags, publish) {
    $.req('note:save', {'id': parseInt(id), 'text': text, 'tags': tags, 'publish': publish});
  }
});