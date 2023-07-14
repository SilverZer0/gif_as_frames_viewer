from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog as fd
import threading, time, sys

MAX_HEIGHT = 950
class GIFPlayer:
    def __init__(self, path):
        self.lock = True
        self.path = path
        imageObject = Image.open(path)
        if hasattr(imageObject, 'n_frames'):
            self.max_frame = imageObject.n_frames - 1
        else:
            self.max_frame = 0
        self.size = [imageObject.width, imageObject.height]
        if self.size[1] > MAX_HEIGHT:
            self.size[0] = round(self.size[0] / (self.size[1]/MAX_HEIGHT))
            self.size[1] = MAX_HEIGHT
        self.imgs = {
            -1 : {
                'img': Image.open(r"gif_end.png").resize(self.size),
                'thread': None,
                'len': 60000
            }
        }

        self.root = tk.Tk()
        self.build()
        self.setup()

    def build(self):
        self.root.title(f'Play '+self.path.replace('\\','/').split('/')[-1])
        self.root.geometry(f'{max(self.size[0], 300)}x{self.size[1]+80}+0+0')
        self.root.focus_force()
        
        self.index = tk.IntVar(value=0)
        self.index.trace_add('write', self.setup)
        self.step = tk.IntVar(value=max(1, round((self.max_frame+1)/100)))
        self.auto = tk.BooleanVar(value = False)
        self.time = tk.StringVar(value = "")
        self.speed = tk.DoubleVar(value = 1.0)

        self.img_l = tk.Label()
        self.img_l.grid(row=1, column = 0, columnspan=6)

        minus_b = tk.Button(self.root, text='-'.center(15), command=self.minus)
        index_e = tk.Entry(self.root, textvariable=self.index, width=7,
                        validate = 'key', validatecommand=(self.root.register(self.nums), '%P'))
        index_l = tk.Label(text=f'out of {self.max_frame}')
        step_l = tk.Label(text=f'step=')
        step_e = tk.Entry(self.root, textvariable=self.step, width=7,
                        validate = 'key', validatecommand=(self.root.register(self.nums), '%P'))
        plus_b = tk.Button(self.root, text='+'.center(15), command=self.plus)

        minus_b.grid(row=5, column=0)
        index_e.grid(row=5, column=1, sticky='E')
        index_l.grid(row=5, column=2, sticky='W')
        step_l.grid(row=5, column=3, sticky='E')
        step_e.grid(row=5, column=4, sticky='W')
        plus_b.grid(row=5, column=5)

        auto_l = tk.Label(text=f'autoplay')
        auto_c = tk.Checkbutton(self.root, variable=self.auto, onvalue=True, offvalue=False)
        time_l = tk.Label(textvariable = self.time)
        speed_l = tk.Label(text=f'speed=')
        speed_e = tk.Entry(self.root, textvariable=self.speed, width=7,
                        validate = 'key', validatecommand=(self.root.register(self.floats), '%P'))

        auto_l.grid(row=6, column=0, sticky='E')
        auto_c.grid(row=6, column=1, sticky='W')
        time_l.grid(row=6, column=2, columnspan=2)
        speed_l.grid(row=6, column=4, sticky='E')
        speed_e.grid(row=6, column=5, sticky='W')

        self.root.bind('<Left>', self.minus)
        self.root.bind('<Right>', self.plus)
        self.root.bind('<Up>', self.step_plus)
        self.root.bind('<Down>', self.step_minus)
        self.root.bind('<Escape>', lambda *_:self.root.destroy())
        self.root.bind('<Delete>', lambda *_:self.root.destroy())
        self.root.bind('a', lambda *_:self.auto.set(not self.auto.get()))
        self.root.bind('s', lambda *_:self.speed.set(1.0))
        self.root.bind('d', lambda *_:self.speed.set(2.0))
        self.root.bind('f', lambda *_:self.speed.set(5.0))
        self.root.bind('h', lambda *_:self.speed.set(0.5))

    def setup(self,*_):
        global imgTk #this needes to be global (why?)
        if (_index := self.index.get()) > self.max_frame:
            return
        _step = self.step.get()
        self.lock = True

        self.save_frame(
            [_index,
            _index + _step,
            _index + _step*2,
            _index - _step,
            _index + _step*3])
        if not (thread := self.imgs[_index]['thread']) is None:
            thread.join()
        self.imgs[_index]['thread'] = None
        imgTk = ImageTk.PhotoImage(self.imgs[_index]['img'])
        time.sleep(0.03)
        _label = tk.Label(image=imgTk)
        _label.grid(row=1, column=0, columnspan=6)
        self.update_time(_index, time.time()*1000, self.imgs[_index]['len'])
        time.sleep(0.01)
        self.img_l.forget()
        self.img_l = _label

        self.root.after_idle(self.unlock)

    def plus(self, *_):
        if self.lock: return
        if self.index.get() == -1:
            time.sleep(0.5)
            self.index.set(0)
        elif self.index.get() >= self.max_frame:
            self.index.set(-1)
        else:
            val = self.index.get() + self.auto.get()\
                + self.step.get()*(not self.auto.get()) 
            self.index.set(str(val if val <= self.max_frame else -1))

    def minus(self,*_):
        if self.lock: return
        if self.index.get() == -1:
            time.sleep(0.5)
            self.index.set(self.max_frame-1)
        else:
            self.index.set(max(
                self.index.get() - self.auto.get()
                - self.step.get()*(not self.auto.get()), -1
            ))

    def step_plus(self,*_):
        self.step.set(self.step.get() + 1)

    def step_minus(self,*_):
        self.step.set(max(self.step.get() - 1, 1))

    def unlock(self):
        self.lock = False

    def save_frame(self,idxs):
        for i in idxs:
            if not i in self.imgs and i >= 0:
                self.imgs[i] = {
                    'img'    : None,
                    'thread' : threading.Thread(
                        target=self.save_frame_thread,
                        args=(self.path, i)
                    ),
                    'len' : 0
                }
                self.imgs[i]['thread'].start()

    def save_frame_thread(self, path, idx):
        try:
            imageObject = Image.open(path)
            if not (hasattr(imageObject, 'n_frames') or idx == 0) \
            or idx < 0 or idx >= imageObject.n_frames:
                return
            imageObject.seek(idx)
            self.imgs[idx]['img'] = imageObject.resize(self.size)
            self.imgs[idx]['len'] = imageObject.info['duration']
            time.sleep(0.01)
        except Exception as e:
            print(f'Frame {idx} failed: {e}')

    def nums(self, value):
        return value in '-1' or value.isdigit()
    
    def floats(self, value):
        try:
            float(value)
            return True
        except Exception:
            return False

    def update_time(self, index, start, length):
        if index != self.index.get(): 
            return
        x = round(time.time()*1000 - start) * self.speed.get()
        y = length
        if y-x < 0:
            self.time.set(f'      0 of {str(y):>6} ( 100.00%)')
            if self.auto.get():
                self.plus()
            return
        self.time.set(f'{str(y-x):>7} of {str(y):>6} ({f"{(x)/(y or 1)*100:0.2f}":>7}%)')
        self.root.after(100,lambda: self.update_time(index, start, length))

if __name__ == '__main__':
    print('''
## TODO ##
# add mp4 (/video) mode
# add? auto play: fixed Frame-langth (x Frames per sec)
    '''.strip())
    try:
        '''
        import win32api
        win32api.DragQueryFile(12)
        print(win32api.DragQueryFile(12))
        '''
        if len(sys.argv) > 1:
            files = sys.argv[1:]
        else:
            files = fd.askopenfilenames(filetypes=[('GIF', '.gif')])
        for i in files:
            GP = GIFPlayer(i)
            GP.root.mainloop()
    except Exception as e:
        input(e)
