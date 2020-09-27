from aiohttp import web
import socketio
from diff_match_patch import diff_match_patch
import threading
import glob
import json
import os

dmp = diff_match_patch()
sio = socketio.AsyncServer()


class ConnectionManager:
    clients = {}
    colours = ['red', 'blue', 'green', 'yellow', 'magenta', 'cyan'][::-1]

    def add_client(self, client):
        self.clients[client.sid] = client
        client.colour = self.colours.pop()

    def remove_client(self, sid):
        self.colours.append(self.get_client(sid).colour)
        del self.clients[sid]

    def get_client(self, sid):
        return self.clients[sid]


class Client:
    def __init__(self, sid):
        self.sid = sid


class Document:
    def __init__(self, filename):
        self.filename = filename
        with open(self.filename, 'r') as f:
            self.contents = f.read()

    def apply_patch(self, patch):
        self.contents, err = dmp.patch_apply(patch, self.contents)

    def apply_diff(self, diff):
        patch = dmp.patch_fromText(diff)
        self.apply_patch(patch)

    def save(self):
        with open(self.filename, 'w') as f:
            f.write(self.contents)


class Folder:
    items = []

    def __init__(self, path):
        self.path = path
        self.contents = os.listdir(path)
        for item in glob.glob(path + "/*"):
            item = os.path.basename(item)
            if os.path.isfile(os.path.join(path, item)):
                self.items.append(File(os.path.join(path, item)))
            elif os.path.isdir(os.path.join(path, item)):
                self.items.append(Folder(os.path.join(path, item)))

    def __repr__(self):
        out = "<Folder "
        out += self.path
        out += ">"
        return out

    def __getitem__(self, n):
        return self.items[n]

    @property
    def name(self):
        return os.path.basename(self.path)

    @property
    def files(self):
        out = []
        for item in self.items:
            if type(item) == File:
                out.append(item)
        return out


class File:
    def __init__(self, path):
        self.path = path
        self.document = Document(path)

    def __repr__(self):
        return f"<File {self.path}>"

    @property
    def name(self):
        return os.path.basename(self.path)


docs = Folder('data')
conns = ConnectionManager()


def save_all_loop():
    for item in docs.items:
        if hasattr(item, 'document'):
            item.document.save()
    # Janky event loop solution
    threading.Timer(5, save_all_loop).start()


def init_docs():
    if len(glob.glob('data/*')) == 0:
        open('data/example.md', 'a').close()
    save_all_loop()


async def index(request):
    """Serve the client-side application."""
    with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')


@sio.on('connect')
async def connect(sid, environ):
    print("connect", sid)
    client = Client(sid)
    conns.add_client(client)


@sio.on('listdocs')
async def listdocs(sid):
    await sio.emit('doclist', json.dumps([x.name for x in docs.files]),
                   to=sid)


@sio.on('get_doc')
async def get_doc(sid, docid):
    await sio.emit('dump', docs.items[docid].document.contents, to=sid)


@sio.on('patch')
async def message(sid, data):
    data = json.loads(data)
    patch, doc, pos = data['patch'], data['doc'], data['pos']
    docs[doc].document.apply_diff(patch)
    broadPatch = {"patch": patch, "doc": doc, "cursor": {
                  "pos": pos, "colour": conns.get_client(sid).colour
                  }
                  }
    await sio.emit('patch', json.dumps(broadPatch),
                   broadcast=True, skip_sid=sid)


@sio.on('disconnect')
def disconnect(sid):
    conns.remove_client(sid)
    print('disconnect', sid)


def start_notes(port=8080):
    init_docs()
    app = web.Application()
    app.router.add_static('/static/', 'static', name='static')
    app.router.add_get('/', index)
    sio.attach(app)
    web.run_app(app, port=port)


if __name__ == "__main__":
    start_notes()
