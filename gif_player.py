from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog as fd
import threading, time, sys

MAX_HEIGHT = 950
class GIFPlayer(tk.Tk):
    def __init__(self, files):
        super().__init__()
        self.files = list(files)
        
        self.auto = tk.BooleanVar(value = False)
        self.speed = tk.DoubleVar(value = 1.0)
        self.new(self.files.pop(0))

    def new(self, path):
        self.geometry(f'{300}x{80}+0+0')        
        self.lock = True
        self.path = path
        imageObject = Image.open(self.path)
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

        self.title(f'Play '+self.path.replace('\\','/').split('/')[-1])
        self.geometry(f'{max(self.size[0], 300)}x{self.size[1]+80}+0+0')
        self.focus_force()

        self.build()
        self.setup()

    def build(self):
        self.index = tk.IntVar(value=0)
        self.index.trace_add('write', self.setup)
        self.step = tk.IntVar(value=max(1, round((self.max_frame+1)/100)))
        self.time = tk.StringVar(value = "")
        self.index_text = tk.StringVar(value = f'out of {str(self.max_frame):<5}')

        self.img_l = tk.Label()
        self.img_l.grid(row=0, column = 0, columnspan=6)

        minus_b = tk.Button(self, text='-'.center(15), command=self.minus)
        index_e = tk.Entry(self, textvariable=self.index, width=7,
                        validate = 'key', validatecommand=(self.register(self.nums), '%P'))
        index_l = tk.Label(textvariable=self.index_text)
        step_l = tk.Label(text=f'step=')
        step_e = tk.Entry(self, textvariable=self.step, width=7,
                        validate = 'key', validatecommand=(self.register(self.nums), '%P'))
        plus_b = tk.Button(self, text='+'.center(15), command=self.plus)

        minus_b.grid(row=1, column=0)
        index_e.grid(row=1, column=1, sticky='E')
        index_l.grid(row=1, column=2, sticky='W')
        step_l.grid(row=1, column=3, sticky='E')
        step_e.grid(row=1, column=4, sticky='W')
        plus_b.grid(row=1, column=5)

        auto_l = tk.Label(text=f'autoplay')
        auto_c = tk.Checkbutton(self, variable=self.auto, onvalue=True, offvalue=False)
        time_l = tk.Label(textvariable = self.time)
        speed_l = tk.Label(text=f'speed=')
        speed_e = tk.Entry(self, textvariable=self.speed, width=7,
                        validate = 'key', validatecommand=(self.register(self.floats), '%P'))

        auto_l.grid(row=2, column=0, sticky='E')
        auto_c.grid(row=2, column=1, sticky='W')
        time_l.grid(row=2, column=2, columnspan=2)
        speed_l.grid(row=2, column=4, sticky='E')
        speed_e.grid(row=2, column=5, sticky='W')

        self.bind('<Left>', self.minus)
        self.bind('<Right>', self.plus)
        self.bind('<Up>', self.step_plus)
        self.bind('<Down>', self.step_minus)
        self.bind('<Escape>', lambda *_:self.kill())
        self.bind('<Delete>', lambda *_:self.kill())
        self.bind('a', lambda *_:self.auto.set(not self.auto.get()))
        self.bind('s', lambda *_:self.speed.set(1.0))
        self.bind('d', lambda *_:self.speed.set(2.0))
        self.bind('f', lambda *_:self.speed.set(5.0))
        self.bind('h', lambda *_:self.speed.set(0.5))

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
        self.img_l.forget()
        _label = tk.Label(image=imgTk)
        _label.grid(row=0, column=0, columnspan=6)
        self.update_time(_index, time.time()*1000, self.imgs[_index]['len'])
        time.sleep(0.01)
        self.img_l.forget()
        self.img_l = _label

        self.after_idle(self.unlock)

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
            if idx < 0 or idx >= (imageObject.n_frames if hasattr(imageObject, 'n_frames') else 1):
                return
            imageObject.seek(idx)
            self.imgs[idx]['img'] = imageObject.resize(self.size)
            self.imgs[idx]['len'] = imageObject.info.get('duration', 0)
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
        self.after(100,lambda: self.update_time(index, start, length))

    def kill(self):
        self.img_l.destroy()
        if self.files:
            self.new(self.files.pop(0))
        else:
            self.destroy()

if __name__ == '__main__':
    GP = None
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
            files = fd.askopenfilenames(filetypes=[('GIF', '.gif'), ('Any', '*')])
        GP = GIFPlayer(files)
        GP.mainloop()
    except Exception as e:
        input(e)
    finally:
        if 0 and not GP is None:
            GP.destroy()
