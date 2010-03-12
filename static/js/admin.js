// (c) alexey pegov (spleaner@gmail.com) 2009-2010

show_editor = function() {
  $('body').append(_('#editor', function(cb) {
    cb(_('.top', 'Новая заметка:'));
    cb(_('textarea'));
    cb(_('.tags', 'Теги: ' + _('span.new', _('input[type=text]'))));
    cb(_('.bottom', 
      _('label', _('input[type=checkbox,value=publish]') + 'Опубликовать') + 
      _('input[type=button,value=Сохранить]') + 
      _('a.l_cancel[href=#]', 'Отменить')))
  }));
  
  var E = $('#editor');
  E.find('input[type=button]').click(function() {
    do_save();
  });
  
  $('#editor > .tags > .new > input[type=text]').inputmap('pressed ENTER', function(e) {
    var T = $(_('span.tag', e.val()));
    T.click(function() { $(this).remove(); });
    $('#editor > .tags > .new').before(T);
    e.val('').focus();
  });
  
  $('#editor > textarea').focus();
  append_tags();
};

append_tags = function() {  
};

do_save = function() {
  var E = $('#editor');
  if (!E.is(':visible')) return;
  
  var T = E.find('textarea').val();
  
  var TG = [];
  E.find('.tag').each(function() {
    TG.push($(this).text());
  });
  
  $.save(-1, T, TG, E.find(':checkbox').is(':checked'));
};