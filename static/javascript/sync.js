var socket = io();
var latest;
var timer;
let interval = 100;
var shadow;
var editor = new SimpleMDE({ element: document.getElementById("msgdoc") });
editor.codemirror.on('keyup', function() {
  clearTimeout(timer);
  timer = setTimeout(emit_patch, interval);
});

editor.codemirror.on('keydown', function() {
  clearTimeout(timer);
});

let dmp = new diff_match_patch();

socket.on('connect', function(){console.log('Connected to server')});
socket.on('disconnect', function(){console.log('Disconnected from server')});
socket.on('dump', function(contents) {
  editor.value(contents);
  shadow = contents;
});
socket.on('patch', function(patch){
  var patchOb = dmp.patch_fromText(patch);
  var oldpos = editor.codemirror.indexFromPos(editor.codemirror.getCursor());
  var newpos = oldpos; // Hold new offset
  var processed = 0; // Hold number of chars iterated through in the patches
  for (var i=0; i < patchOb.length; i++) {
    newpos += patchOb[i].length2 - patchOb[i].length1;
    processed += patchOb[i].length1;
    if (processed >= oldpos) {
      break;
    }
  }
  res = dmp.patch_apply(patchOb, editor.value());
  editor.value(res[0]);
  res = dmp.patch_apply(patchOb, shadow);
  shadow = res[0];
  editor.codemirror.setCursor(editor.codemirror.posFromIndex(newpos));
});

function emit_patch(patch) {
  var diff = dmp.patch_make(shadow, editor.value());
  var patch = dmp.patch_toText(diff);
  shadow = editor.value();
  socket.emit('patch', patch);
}