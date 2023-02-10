from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog as fd
import threading, time, sys, os

def plus(*_):
    global index
    if lock: return
    if int(index.get()) == imageObject.n_frames:
        index.set('1')
    else:
        val = min(int(index.get()) + int(step.get()), imageObject.n_frames)
        index.set(str(val))

def minus(*_):
    global index
    if lock: return
    if index.get() == '1':
        index.set(str(imageObject.n_frames + 1))
    else:
        val = max(int(index.get()) - int(step.get()), 1)
        index.set(str(val))

def step_minus(*_):
    global step
    step.set(str(max(int(step.get()) - 1, 1)))

def step_plus(*_):
    global step
    step.set(str(int(step.get()) + 1))

def setup(*args):
    global imgs, label, imgTk, lock
    if '' in (index.get(), step.get()) or \
      int(index.get()) > imageObject.n_frames:
        return
    lock = True
    
    int_index = int(index.get())-1
    int_step = int(step.get())

    save_frame(
        [int_index,
         int_index + int_step,
         int_index + int_step*2,
         int_index - int_step,
         int_index + int_step*3])
    if not (thread := imgs[int_index]['thread']) is None:
        thread.join()
    imgs[int_index]['thread'] = None
    imgTk = ImageTk.PhotoImage(imgs[int_index]['img'])
    _label = tk.Label(image=imgTk)
    _label.grid(row=1, column=0, columnspan=6)
    time.sleep(0.01)
    label.forget()
    label = _label
    root.after_idle(unlock)

def unlock():
    global lock
    lock = False

def save_frame(idxs):
    global imgs
    for i in idxs:
        if not i in imgs:
            imgs[i] = {'img'    : None,
                       'thread' : threading.Thread(target=save_thread,
                                                   args=(path, i))}
            imgs[i]['thread'].start()

def save_thread(path, idx):
    try:
        imageObject = Image.open(path)
        if idx < 0 or idx >= imageObject.n_frames:
            return
        imageObject.seek(idx)
        imgs[idx]['img'] = imageObject.resize(size)
        time.sleep(0.01)
    except Exception as e:
        print(f'Frame {idx} failed: {e}')

def nums(value):
    return value == '' or value.isdigit()

def build():
    global root, index, step, label
    root = tk.Tk()
    root.title(f'Play '+path.replace('\\','/').split('/')[-1])
    root.geometry(f'{max(size[0], 300)}x{size[1]+40}+0+0')
    root.focus_force()
    
    root.bind('<Left>', minus)
    root.bind('<Right>', plus)
    root.bind('<Up>', step_plus)
    root.bind('<Down>', step_minus)
    root.bind('<Escape>', lambda *_:root.destroy())
    root.bind('0', lambda *_:root.destroy())

    label = tk.Label()
    label.grid(row=1, column = 0, columnspan=6)
    step = tk.StringVar()
    step.set(str(max(1, round(imageObject.n_frames/100))))
    index = tk.StringVar()
    index.set('1')
    index.trace_add('write', setup)

    minus_b = tk.Button(root, text='-'.center(20), command=minus)
    index_e = tk.Entry(root, textvariable=index, width=10,
                       validate = 'key', validatecommand=(root.register(nums), '%P'))
    index_l = tk.Label(text=f'out of {imageObject.n_frames}')
    step_l = tk.Label(text=f'step=')
    step_e = tk.Entry(root, textvariable=step, width=5,
                       validate = 'key', validatecommand=(root.register(nums), '%P'))
    plus_b = tk.Button(root, text='+'.center(20), command=plus)
    minus_b.grid(row=5, column=0)
    index_e.grid(row=5, column=1, sticky='E')
    index_l.grid(row=5, column=2, sticky='W')
    step_l.grid(row=5, column=3, sticky='E')
    step_e.grid(row=5, column=4, sticky='W')
    plus_b.grid(row=5, column=5)

def main(_path):
    global path, imageObject, imgs, size
    path = _path
    imageObject = Image.open(path)
    imgs = {}

    size = [imageObject.width, imageObject.height]
    if size[1] > 980:
        size[0] = round(size[0] / (size[1]/980))
        size[1] = 980

    build()
    setup()

    root.mainloop()

print('''
## TODO ##
# add mp4 (/video) mode
# add better multi-file support
# add auto play
#   fixed Frame-langth (x Frames per sec)
#   orginal Frame-langth (longer & shorter frames) ?exists?
#   multiplier for both (2x speed)
''')
try:
    if len(sys.argv) > 1:
        for i in range(1,len(sys.argv)):#range(2,
            main(sys.argv[i])
            #os.spawnv(1, __file__, [sys.argv[i],])
        #main(sys.argv[1])
    else:
        main(fd.askopenfilename(filetypes=[('GIF', '.gif')]))
except Exception as e:
    input(e)
