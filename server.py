from aiohttp import web
import socketio
from diff_match_patch import diff_match_patch
import threading
import glob


dmp = diff_match_patch()
sio = socketio.AsyncServer()


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


docs = []


def save_all_loop():
    for doc in docs:
        doc.save()
    # Janky event loop solution
    threading.Timer(5, save_all_loop).start()


def init_docs():
    if len(glob.glob('data/*')) == 0:
        open('data/example.md', 'a').close()
        # If there are no files, create a dummy one
    for filename in glob.glob('data/*'):
        docs.append(Document(filename))
    save_all_loop()


async def index(request):
    """Serve the client-side application."""
    with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')


@sio.on('connect')
async def connect(sid, environ):
    print("connect", sid)
    await sio.emit('dump', docs[0].contents, to=sid)


@sio.on('patch')
async def message(sid, data):
    docs[0].apply_diff(data)
    await sio.emit('patch', data,
                   broadcast=True, skip_sid=sid)


@sio.on('disconnect')
def disconnect(sid):
    print('disconnect', sid)


def start_notes(port=8080):
    init_docs()
    app = web.Application()
    app.router.add_static('/static/', 'static', name='static')
    app.router.add_get('/', index)
    sio.attach(app)
    web.run_app(app, port=port)
