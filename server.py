from aiohttp import web
import socketio
from diff_match_patch import diff_match_patch
import threading
import glob

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)
dmp = diff_match_patch()


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
        with open('data/' + self.filename, 'w') as f:
            f.write(self.contents)


docs = [Document("example.md")]


def save_all_loop():
    for doc in docs:
        doc.save()
    threading.Timer(5, save_all_loop).start()


def init_docs():
    for filename in glob.glob('data/*'):
        docs.append(Document(filename))
    save_all_loop()


async def index(request):
    """Serve the client-side application."""
    with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')


@sio.on('connect', namespace='/chat')
async def connect(sid, environ):
    print("connect", sid)
    await sio.emit('dump', docs[0].contents, namespace='/chat', to=sid)


@sio.on('chat message', namespace='/chat')
async def message(sid, data):
    docs[0].apply_diff(data)
    await sio.emit('patch', data, namespace='/chat',
                   broadcast=True, skip_sid=sid)


@sio.on('disconnect', namespace='/chat')
def disconnect(sid):
    print('disconnect', sid)


app.router.add_static('/static/', 'static', name='static')
app.router.add_get('/', index)

if __name__ == '__main__':
    init_docs()
    web.run_app(app)
