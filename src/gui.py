# Third-Party Libraries
from ttkthemes import ThemedTk

# Native-Python Libraries
import tkinter as tk
from tkinter import ttk
import threading

# https://stackoverflow.com/a/1835036
class App(threading.Thread):
    def __init__(self, start_callback, stop_callback,
                volume_queue, threshold_queue, amplitude_queue, 
                input_list, output_list,midi_list, source_list,
                default_input = '(Seleccionar)', default_output = '(Seleccionar)'):
        threading.Thread.__init__(self)

        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.volume_queue = volume_queue
        self.threshold_queue = threshold_queue
        self.amplitude_queue = amplitude_queue

        self.input_list = input_list
        self.output_list = output_list
        self.midi_list = midi_list
        self.source_list = source_list

        self.default_input = default_input
        self.default_output = default_output

        self.volume_db = -100
        self.threshold_db = -40
        self.amplitude = 5

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
        frame.grid(row=0, column=1)

        self.btn_toggle_run = ttk.Button(frame, text="Iniciar", width=30, command=self.toggle_run)
        self.btn_toggle_run.pack()


        frame = ttk.Frame(self.root)
        frame.grid(row=1, column=1)
        frame.columnconfigure(0, weight=1, minsize=160)
        frame.columnconfigure(1, weight=1, minsize=40)

        title_frame = ttk.Frame(frame)
        title_frame.grid(row=0, column=0)

        self.lbl_title_threshold = ttk.Label(title_frame, text=f"Umbral de volúmen de entrada:")
        self.lbl_title_threshold.pack()

        scl_frame = ttk.Frame(frame)
        scl_frame.grid(row=1, column=0)
        lbl_frame = ttk.Frame(frame)
        lbl_frame.grid(row=1, column=1)

        self.lbl_threshold = ttk.Label(lbl_frame, text=f'  {self.threshold_db} dB')

        self.scl_threshold = ttk.Scale(
            scl_frame,
            from_=-100,
            to=0,
            orient=tk.HORIZONTAL,
            length=150,
            command=lambda v: setattr(self, 'threshold_db', round(float(v)))
        )
        self.scl_threshold.set(self.threshold_db)
        self.scl_threshold.pack()
        self.lbl_threshold.pack()

        pb_frame = ttk.Frame(frame)
        pb_frame.grid(row=2, column=0)
        lbl_frame = ttk.Frame(frame)
        lbl_frame.grid(row=2, column=1)

        self.pb_input_vol = ttk.Progressbar(
            pb_frame,
            orient='horizontal',
            mode='determinate',
            length=150
        )
        self.pb_input_vol.pack(anchor="w")

        self.lbl_input_vol = ttk.Label(master=lbl_frame, text="  00 dB")
        self.lbl_input_vol.pack(anchor="w")


        frame = ttk.Frame(self.root)
        frame.grid(row=2, column=1)
        frame.columnconfigure(0, weight=1, minsize=160)
        frame.columnconfigure(1, weight=1, minsize=40)

        title_frame = ttk.Frame(frame)
        title_frame.grid(row=0, column=0)

        lbl_title_amplitude = ttk.Label(title_frame, text=f"Volúmen de salida:")
        lbl_title_amplitude.pack()

        scl_frame = ttk.Frame(frame)
        scl_frame.grid(row=1, column=0)
        lbl_frame = ttk.Frame(frame)
        lbl_frame.grid(row=1, column=1)

        self.lbl_amplitude = ttk.Label(master=lbl_frame, text=f'  {self.amplitude}')

        self.amplitude = tk.IntVar()
        self.scl_amplitude = ttk.Scale(
            scl_frame,
            from_=0,
            to=10,
            value=5,
            orient=tk.HORIZONTAL,
            length=150,
            variable=self.amplitude
        )
        self.scl_amplitude.set(5)
        self.scl_amplitude.pack()
        self.lbl_amplitude.pack()

        self.root.after(100, self.periodicCall)
        self.root.mainloop()

    def periodicCall(self):
        self.threshold_queue.put(self.threshold_db)
        self.amplitude_queue.put(self.amplitude.get())
        self.lbl_threshold.config(text=f'  {self.threshold_db} dB')
        self.lbl_amplitude.config(text=f'  {self.amplitude.get()}')

        while not self.volume_queue.empty():
            self.volume_db = int(self.volume_queue.get())
        self.set_input_volume(self.volume_db)
        self.root.after(100, self.periodicCall)

    def toggle_run(self):
        self.btn_toggle_run.config(text='Corriendo...')
        self.btn_toggle_run.config(state='disable')
        self.cb_input.config(state='disable')
        self.cb_output.config(state='disable')
        self.cb_midi.config(state='disable')

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
