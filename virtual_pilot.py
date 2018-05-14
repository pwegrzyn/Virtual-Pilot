# Programowanie w jezyku Python 2018
# Autor: Wegrzyn Patryk

import yaml
import sys
import socket
import tkinter as tk
from tkinter import font
from functools import partial

# Kontroler wirtualnego pilota
class VPController(tk.Tk):
    
    def __init__(self, vp_config):
        tk.Tk.__init__(self)
        self.config = vp_config     # Obiekt reprezentujący konfigurację
        self.send_address = "255.255.255.255"
        self.send_port = 2018
        
        # Zabezpieczenie przed granicznymi przypadkami danych wejściowych
        if not self.config:
            print("Zły format pliku YAML!")
            exit()
        for key in self.config:
            if not self.config[key]:
                self.config[key] = dict()
        self.device_state = {key: False for devices in self.config.values() for key in devices}     # Stany urządzeń
        self.title("Wirtualny Pilot")
        self.title_font = font.Font(size=12, weight="bold")
        
        # Utworzenie kontenera na wykorzystywane panele
        frame_container = tk.Frame(self)
        frame_container.pack(side="top", fill="both", expand=True)
        frame_container.grid_rowconfigure(index=0, weight=1)
        frame_container.grid_columnconfigure(index=0, weight=1)
        
        # Słownik zawierający odwołania do wytworzonych paneli
        self.frames = dict()
        for group_name in self.config:
            if not self.config[group_name]:
                continue
            frame = GroupPage(parent=frame_container, controller=self, group=group_name)
            self.frames[group_name] = frame
            frame.grid(row=0, column=0, sticky="news")
        frame = StartPage(parent=frame_container, controller=self)
        self.frames["StartPage"] = frame
        frame.grid(row=0, column=0, sticky="news")
        
        # Na końcu wyświetlamy panel startowy
        self.show_frame("StartPage")

    # Wywołuje dany panel na front
    def show_frame(self, page_name):
        self.frames[page_name].tkraise()

    # Wysyła dany pakiet UDP do danego hosta
    def send_package(self, content):
        UDP_IP = self.send_address
        UDP_PORT = self.send_port
        dest = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)     # Type socketa
        dest.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)      # Flaga broadcastowania
        dest.sendto(bytes(content, "utf-8"), (UDP_IP, UDP_PORT))    # Wysłanie strumienia bajtów

    # Wysyła powiadomienie o wyłączeniu, zapamiętuje stan oraz wyłącza przycisk OFF
    def turnoff_device(self, key, buttonOn, buttonOff):
        if not self.device_state[key]:      # Jeśli urządzenie jest już wyłączone to nic nie rób
            return
        self.device_state[key] = False      # W przeciwnym wypaku je wyłącz
        self.send_package("off " + key)
        buttonOn.config(state="normal")
        buttonOff.config(state="disabled")

    # Analogicznie do turnoff_device
    def turnon_device(self, key, buttonOn, buttonOff):
        if self.device_state[key]:
            return
        self.device_state[key] = True
        self.send_package("on " + key)
        buttonOn.config(state="disabled")
        buttonOff.config(state="normal")

    # Zmienia adres na który wysyłane są pakiety
    def change_destination(self, new_addr, new_port):
        self.send_address = new_addr
        self.send_port = new_port

    # Uruchamia główną pętlę programu
    def run(self):
        self.mainloop()


# Reprezentuje stronę główną GUI aplikacji
class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Proszę wybrać grupę", 
                         font=controller.title_font, bg="white")
        label.pack(side="top", fill="x", pady=10)
        
        # Stwórz listę przycisków na grupy
        group_buttons = list()
        for group in self.controller.config:
            if not self.controller.config[group]:
                continue
            new_button = tk.Button(self, text=group, width=10, 
                                   command=partial(controller.show_frame, group))
            group_buttons.append(new_button)
        for button in group_buttons:
            button.pack(side="top", pady=10)
    

# Reprezentuję stronę grupy (np. kuchni albo wentylatorów)
class GroupPage(tk.Frame):

    def __init__(self, parent, controller, group):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text=group, font=controller.title_font)
        label.grid(row=0, columnspan=3, pady=10)
        
        # Stwórz listę przycisków uruchamiania i wyłączania urządzeń wraz z etykietami
        devices = list()
        for key in self.controller.config[group]:
            label = tk.Label(self, text=self.controller.config[group][key], 
                             width=20, pady=10, anchor='w')
            buttonOn = tk.Button(self, text="Włącz", width=8, state="normal")
            buttonOff = tk.Button(self, text="Wyłącz", width=8, state="disabled")
            buttonOn.config(command=partial(controller.turnon_device, key, buttonOn, buttonOff))
            buttonOff.config(command=partial(controller.turnoff_device, key, buttonOn, buttonOff))
            devices.append((label, buttonOn, buttonOff))
        
        # W przeciwieńswie do StartPage tutaj korzystam z funkcji grid w celu
        # łatwiejszej pracy z tabelą
        for i,dev in enumerate(devices):
            dev[0].grid(row=i+1, column=0, sticky="w")
            dev[1].grid(row=i+1, column=1, sticky="e")
            dev[2].grid(row=i+1, column=2, sticky="e")
        back_button = tk.Button(self, text="Wróć do wyboru grupy", 
                                command=lambda: controller.show_frame("StartPage"))
        back_button.grid(columnspan=3)


# Klasa odpowiedzialna za parsowanie pliku konfiguracyjnego YAML
class ConfigParser:
    
    def __init__(self, input_file):
        self.source = input_file

    # Parsuje plik YAML (bezpiecznie), zwraca złożony obiekt Python'owy
    def parse(self):
        with open(self.source) as input:
            content = input.read()
        return yaml.safe_load(content)


# Główna funkcja aplikacji (parameter linii komend to ścieżka do pliku konfiguracyjnego)
def main():
    if len(sys.argv) < 2:
        print("Proszę podać ścieżkę do pliku konfiguracyjnego YAML")
        exit(1)
    parser = ConfigParser(sys.argv[1])
    vp_config = parser.parse()
    VPController(vp_config).run()

if __name__ == "__main__":
    main()