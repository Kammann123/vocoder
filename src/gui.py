# Third-Party Libraries
from ttkthemes import ThemedTk

# Native-Python Libraries
import tkinter as tk
from tkinter import ttk
import threading

# https://stackoverflow.com/a/1835036
class App(threading.Thread):
    def __init__(self, start_callback, stop_callback, volume_queue, threshold_queue, 
                input_list, output_list,midi_list, source_list,
                default_input = '(Seleccionar)', default_output = '(Seleccionar)'):
        threading.Thread.__init__(self)

        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.volume_queue = volume_queue
        self.threshold_queue = threshold_queue

        self.input_list = input_list
        self.output_list = output_list
        self.midi_list = midi_list
        self.source_list = source_list

        self.default_input = default_input
        self.default_output = default_output

        self.volume_db = -100
        self.threshold_db = -40

    def callback(self):
        self.root.quit()

    def run(self):
        self.root = ThemedTk(theme="equilux", themebg=True)
        self.root.protocol("WM_DELETE_WINDOW", self.callback)

        self.root.geometry("600x300")
        self.root.title("Vocoder")

        self.root.columnconfigure(0, weight=1, minsize=200)
        self.root.columnconfigure(1, weight=1, minsize=200)
        self.root.rowconfigure(0, weight=1, minsize=75)
        self.root.rowconfigure(1, weight=1, minsize=75)
        self.root.rowconfigure(2, weight=1, minsize=75)
        self.root.rowconfigure(3, weight=1, minsize=75)

        frame = ttk.Frame(self.root)
        frame.grid(row=0, column=0)

        self.lbl_input = ttk.Label(master=frame, text=f"Entrada de micrófono: ")
        self.lbl_input.pack()

        self.str_input = tk.StringVar(self.root)
        self.str_input.set(self.default_input)
        self.cb_input = ttk.Combobox(frame, textvariable=self.str_input, state="readonly", values=self.input_list)
        self.cb_input.config(width=40)
        self.cb_input.pack()


        frame = ttk.Frame(self.root)
        frame.grid(row=1, column=0)

        self.lbl_output = ttk.Label(master=frame, text=f"Salida de audio: ")
        self.lbl_output.pack()

        self.str_output = tk.StringVar(self.root)
        self.str_output.set(self.default_output)
        self.cb_output = ttk.Combobox(frame, textvariable=self.str_output, state="readonly", values=self.output_list)
        self.cb_output.config(width=40)
        self.cb_output.pack()


        frame = ttk.Frame(self.root)
        frame.grid(row=2, column=0)

        self.lbl_midi = ttk.Label(master=frame, text=f"Entrada MIDI: ")
        self.lbl_midi.pack()

        self.str_midi = tk.StringVar(self.root)
        self.str_midi.set("(Seleccionar)" if len(self.midi_list) == 0 else self.midi_list[0])
        self.cb_midi = ttk.Combobox(frame, textvariable=self.str_midi, state="readonly", values=self.midi_list)
        self.cb_midi.config(width=40)
        self.cb_midi.pack()


        frame = ttk.Frame(self.root)
        frame.grid(row=3, column=0)

        self.lbl_source = ttk.Label(master=frame, text=f"Entrada de fuente de audio: ")
        self.lbl_source.pack()

        self.str_source = tk.StringVar(self.root)
        self.str_source.set(self.default_input)
        self.cb_source = ttk.Combobox(frame, textvariable=self.str_source, state="readonly", values=self.source_list)
        self.cb_source.config(width=40, state='disable')
        self.cb_source.pack()


        frame = ttk.Frame(self.root)
        frame.grid(row=0, column=1)

        self.btn_toggle_run = ttk.Button(frame, text="Iniciar", width=30, command=self.toggle_run)
        self.btn_toggle_run.pack()


        frame = ttk.Frame(self.root)
        frame.grid(row=1, column=1)

        self.btn_toggle_source = ttk.Button(frame, text="Cambiar a fuente de audio", width=30, command=self.toggle_audio_source)
        self.btn_toggle_source.pack()


        frame = ttk.Frame(self.root)
        frame.grid(row=2, column=1)
        frame.columnconfigure(0, weight=1, minsize=160)
        frame.columnconfigure(1, weight=1, minsize=40)

        self.pb_frame = ttk.Frame(frame)
        self.pb_frame.grid(row=0, column=0)
        self.lbl_frame = ttk.Frame(frame)
        self.lbl_frame.grid(row=0, column=1)

        self.pb_input_vol = ttk.Progressbar(
            self.pb_frame,
            orient='horizontal',
            mode='determinate',
            length=150
        )
        self.pb_input_vol.pack(anchor="w")

        self.lbl_input_vol = ttk.Label(master=self.lbl_frame, text="  00 dB")
        self.lbl_input_vol.pack(anchor="w")


        frame = ttk.Frame(self.root)
        frame.grid(row=3, column=1)
        frame.columnconfigure(0, weight=1, minsize=160)
        frame.columnconfigure(1, weight=1, minsize=40)

        self.scl_frame = ttk.Frame(frame)
        self.scl_frame.grid(row=0, column=0)
        self.lbl_frame = ttk.Frame(frame)
        self.lbl_frame.grid(row=0, column=1)

        self.lbl_threshold = ttk.Label(master=self.lbl_frame, text=f'  {self.threshold_db} dB')

        self.scl_threshold = ttk.Scale(
            self.scl_frame,
            from_=-100,
            to=0,
            orient=tk.HORIZONTAL,
            length=150,
            command=lambda v: setattr(self, 'threshold_db', round(float(v)))
        )
        self.scl_threshold.set(self.threshold_db)
        self.scl_threshold.pack()
        self.lbl_threshold.pack()

        self.root.after(100, self.periodicCall)
        self.root.mainloop()

    def periodicCall(self):
        self.threshold_queue.put(self.threshold_db)
        self.lbl_threshold.config(text=f'  {self.threshold_db} dB')

        while not self.volume_queue.empty():
            self.volume_db = int(self.volume_queue.get())
        self.set_input_volume(self.volume_db)
        self.root.after(100, self.periodicCall)

    def toggle_audio_source(self):
        if self.btn_toggle_source.config('text')[-1] == 'Cambiar a entrada MIDI':
            self.btn_toggle_source.config(text='Cambiar a fuente de audio')
            self.cb_midi.config(state='readonly')
            self.cb_source.config(state='disable')
        else:
            self.btn_toggle_source.config(text='Cambiar a entrada MIDI')
            self.cb_midi.config(state='disable')
            self.cb_source.config(state='readonly')

    def toggle_run(self):
        if self.btn_toggle_run.config('text')[-1] == 'Detener':
            self.btn_toggle_run.config(text='Iniciar')
            self.cb_input.config(state='readonly')
            self.cb_output.config(state='readonly')
            self.btn_toggle_source.config(state='enable')
            if self.btn_toggle_source.config('text')[-1] == 'Cambiar a entrada MIDI':
                self.cb_midi.config(state='disable')
                self.cb_source.config(state='readonly')
            else:
                self.cb_midi.config(state='readonly')
                self.cb_source.config(state='disable')

            self.stop_callback()
        else:
            self.btn_toggle_run.config(text='Detener')
            self.btn_toggle_source.config(state='disable')
            self.cb_input.config(state='disable')
            self.cb_output.config(state='disable')
            self.cb_midi.config(state='disable')
            self.cb_source.config(state='disable')

            self.start_callback(self.str_input.get(), self.str_output.get(), self.str_midi.get())

    def set_input_volume(self, volume_db):
        self.lbl_input_vol.config(text=f'  {volume_db} dB')
        self.pb_input_vol.config(value=100+volume_db)

    def get_input_name(self):
        return self.str_input

    def get_output_name(self):
        return self.str_output
        
    def get_midi_name(self):
        return self.str_midi

    def get_source_name(self):
        return self.str_source
