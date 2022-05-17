import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk

def toggle_audio_source():
    if btn_toggle_source.config('text')[-1] == 'Cambiar a entrada MIDI':
        btn_toggle_source.config(text='Cambiar a fuente de audio')
        cb_midi.config(state='readonly')
        cb_source.config(state='disable')
    else:
        btn_toggle_source.config(text='Cambiar a entrada MIDI')
        cb_midi.config(state='disable')
        cb_source.config(state='readonly')

def toggle_run():
    if btn_toggle_run.config('text')[-1] == 'Detener':
        btn_toggle_run.config(text='Iniciar')
        cb_input.config(state='readonly')
        cb_output.config(state='readonly')
        btn_toggle_source.config(state='enable')
        if btn_toggle_source.config('text')[-1] == 'Cambiar a entrada MIDI':
            cb_midi.config(state='disable')
            cb_source.config(state='readonly')
        else:
            cb_midi.config(state='readonly')
            cb_source.config(state='disable')
    else:
        btn_toggle_run.config(text='Detener')
        btn_toggle_source.config(state='disable')
        cb_input.config(state='disable')
        cb_output.config(state='disable')
        cb_midi.config(state='disable')
        cb_source.config(state='disable')

def set_input_volume(volume_db):
    lbl_input_vol.config(text=f'  {volume_db} dB')
    pb_input_vol.config(value=100-volume_db)
    
def set_source_volume(volume_db):
    lbl_source_vol.config(text=f'  {volume_db} dB')
    pb_source_vol.config(value=100-volume_db)

window = ThemedTk(theme="equilux", themebg=True)
window.geometry("450x300")
window.title("Vocoder")

window.columnconfigure(0, weight=1, minsize=75)
window.columnconfigure(1, weight=1, minsize=75)
window.rowconfigure(0, weight=1, minsize=50)
window.rowconfigure(1, weight=1, minsize=50)
window.rowconfigure(2, weight=1, minsize=50)
window.rowconfigure(3, weight=1, minsize=50)


frame = ttk.Frame(window)
frame.grid(row=0, column=0)

lbl_input = ttk.Label(master=frame, text=f"Entrada de micrófono: ")
lbl_input.pack()

str_input = tk.StringVar(window)
str_input.set("(Seleccionar)") # default value
cb_input = ttk.Combobox(frame, textvariable=str_input, state="readonly", values=["one", "two", "three"])
cb_input.config(width=20)
cb_input.pack()


frame = ttk.Frame(window)
frame.grid(row=1, column=0)

lbl_output = ttk.Label(master=frame, text=f"Salida de audio: ")
lbl_output.pack()

str_output = tk.StringVar(window)
str_output.set("(Seleccionar)") # default value
cb_output = ttk.Combobox(frame, textvariable=str_output, state="readonly", values=["one", "two", "three"])
cb_output.config(width=20)
cb_output.pack()


frame = ttk.Frame(window)
frame.grid(row=2, column=0)

lbl_midi = ttk.Label(master=frame, text=f"Entrada MIDI: ")
lbl_midi.pack()

str_midi = tk.StringVar(window)
str_midi.set("(Seleccionar)") # default value
cb_midi = ttk.Combobox(frame, textvariable=str_midi, state="readonly", values=["one", "two", "three"])
cb_midi.config(width=20)
cb_midi.pack()


frame = ttk.Frame(window)
frame.grid(row=3, column=0)

lbl_source = ttk.Label(master=frame, text=f"Entrada de fuente de audio: ")
lbl_source.pack()

str_source = tk.StringVar(window)
str_source.set("(Seleccionar)") # default value
cb_source = ttk.Combobox(frame, textvariable=str_source, state="readonly", values=["one", "two", "three"])
cb_source.config(width=20, state='disable')
cb_source.pack()


frame = ttk.Frame(window)
frame.grid(row=0, column=1)

btn_toggle_run = ttk.Button(frame, text="Iniciar", width=30, command=toggle_run)
btn_toggle_run.pack()


frame = ttk.Frame(window)
frame.grid(row=1, column=1)

btn_toggle_source = ttk.Button(frame, text="Cambiar a fuente de audio", width=30, command=toggle_audio_source)
btn_toggle_source.pack()


frame = ttk.Frame(window)
frame.grid(row=2, column=1)

pb_frame = ttk.Frame(frame)
pb_frame.grid(row=0, column=0)
lbl_frame = ttk.Frame(frame)
lbl_frame.grid(row=0, column=1)

pb_input_vol = ttk.Progressbar(
    pb_frame,
    orient='horizontal',
    mode='determinate',
    length=150
)
pb_input_vol.pack()

lbl_input_vol = ttk.Label(master=lbl_frame, text=f"  0 dB")
lbl_input_vol.pack()


frame = ttk.Frame(window)
frame.grid(row=3, column=1)

pb_frame = ttk.Frame(frame)
pb_frame.grid(row=0, column=0)
lbl_frame = ttk.Frame(frame)
lbl_frame.grid(row=0, column=1)

pb_source_vol = ttk.Progressbar(
    pb_frame,
    orient='horizontal',
    mode='determinate',
    length=150
)
pb_source_vol.pack()

lbl_source_vol = ttk.Label(master=lbl_frame, text=f"  0 dB")
lbl_source_vol.pack()

window.mainloop()