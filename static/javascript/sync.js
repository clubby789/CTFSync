var socket = io();
var timer;
var interval = 100;
var shadow;
var config = {
                element: document.getElementById("msgdoc"),
                spellChecker: false,
                autofocus: true,
                renderingConfig: {
                  singleLineBreaks: true,
                  codeSyntaxHighlighting: true
                },
                tabSize: 4
              };
var editor = new SimpleMDE({
                 element: document.getElementById("msgdoc"),
                 spellChecker: false,
                 autofocus: true
             });
var currentDoc = -1;
var docs = [];

editor.codemirror.on("keyup", function() {
  clearTimeout(timer);
  timer = setTimeout(emit_patch, interval);
});

editor.codemirror.on("keydown", function() {
  clearTimeout(timer);
});

var dmp = new diff_match_patch();

socket.on("connect", function(){
  console.log("Connected to server");
  socket.emit("listdocs");
});
socket.on("disconnect", function(){console.log("Disconnected from server");});

socket.on("doclist", function(contents) {
  var filelist = document.getElementById("filelist");
  filelist.innerHTML = "";
  // Clear previous file list
  docs = JSON.parse(contents);
  for (var i = 0; i < docs.length; i++) {
    var node = document.createElement("div");
    node.classList = "document";
    var link = document.createElement("a");
    link.href = "#";
    if (i == currentDoc) {
      link.style = "color: #f1f1f1;";
    }
    link.setAttribute("onclick", `javascript:getDoc(${i});`);
    link.innerText = docs[i];
    node.appendChild(link);

    var closeBtn = document.createElement("button");
    closeBtn.classList = "close-btn";
    closeBtn.innerText = "X";
    closeBtn.setAttribute("onclick", `javascript:delete_file(${i});`);
    node.appendChild(closeBtn);
    filelist.appendChild(node);
  }
});

socket.on("dump", function(contents) {
  editor.value(contents);
  shadow = contents;
});

socket.on("patch", function(patch){
  var data = JSON.parse(patch);
  var patchOb = dmp.patch_fromText(data.patch);
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
  var cursor = editor.codemirror.posFromIndex(data.cursor.pos);
  var cursorCoords =  editor.codemirror.cursorCoords(cursor);
  var cursorElement = document.createElement("span");
  cursorElement.style.borderLeftStyle = "solid";
  cursorElement.style.borderLeftWidth = "2px";
  cursorElement.style.borderLeftColor = data.cursor.colour;
  cursorElement.style.height = `${(cursorCoords.bottom - cursorCoords.top)}px`;
  cursorElement.style.padding = 0;
  cursorElement.style.zIndex = 0;

  marker = editor.codemirror.setBookmark(cursor, {widget: cursorElement});
  setTimeout(fade_and_delete, 1000, cursorElement);
});

function fade_and_delete(element) {
  var seconds = 2;
  element.style.transition = "opacity "+seconds+"s ease";
  element.style.opacity = 0;
  setTimeout(function() {
    element.parentNode.removeChild(element);
}, 200);
}

function emit_patch(patch) {
  if (currentDoc == -1) {
    return;
  }
  var diff = dmp.patch_make(shadow, editor.value());
  patch = dmp.patch_toText(diff);
  shadow = editor.value();
  var broadPatch = {
    "patch": patch,
    "doc": currentDoc,
    "pos": editor.codemirror.indexFromPos(editor.codemirror.getCursor())
  }
  socket.emit("patch", JSON.stringify(broadPatch));
}

function getDoc(index) {
  currentDoc = index;
  socket.emit("get_doc", index);
  socket.emit("listdocs");
}

const regular = setInterval(function() {
  socket.emit("listdocs");
}, 10000);

function addfile() {
  var filename = prompt("Add a new file", "filename.txt");
  socket.emit("addfile", filename);
  socket.emit("listdocs");
}

function delete_file(index) {
  socket.emit("delete_doc", index);
}
