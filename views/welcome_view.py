import tkinter as tk
from tkinter import ttk
from ui_elements import COLOR_PRIMARY_ACCENT, COLOR_BACKGROUND_DARK, COLOR_FOREGROUND_LIGHT, \
    COLOR_SUCCESS_ACCENT, load_icon, AppHeaderFrame

class WelcomeView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.icons = {}
        self._load_icons()
        self.create_widgets()

    def _load_icons(self):
        self.icons["driver"] = load_icon("driver", size=(24,24))
        self.icons["team"] = load_icon("team", size=(24,24))
        self.icons["season"] = load_icon("season", size=(24,24))
        self.icons["circuit"] = load_icon("circuit", size=(24,24))
        self.icons["race"] = load_icon("race", size=(24,24))
        self.icons["contract"] = load_icon("contract", size=(24,24))
        self.icons["result"] = load_icon("result", size=(24,24))
        self.icons["standings"] = load_icon("standings", size=(24,24))

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Sistema de Gestão da F1")
        header.pack(fill="x", pady=(0, 20))

        tk.Label(self, text="Selecione uma entidade para gerenciar:",
                                  font=("Arial", 16),
                                  bg=COLOR_BACKGROUND_DARK, fg=COLOR_FOREGROUND_LIGHT).pack(pady=20)

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=20)

        buttons_info = [
            ("Pilotos", "DriverListView", "driver"),
            ("Equipes", "TeamListView", "team"),
            ("Temporadas", "SeasonListView", "season"),
            ("Circuitos", "CircuitListView", "circuit"),
            ("Corridas", "RaceListView", "race"),
            ("Contratos", "ContractListView", "contract"),
            ("Resultados", "ResultListView", "result"),
            ("Classificações", "OverallStandingsView", "standings")
        ]

        row, col = 0, 0
        for text, frame_name, icon_key in buttons_info:
            icon = self.icons.get(icon_key)
            btn = ttk.Button(button_frame, text=text,
                             command=lambda fn=frame_name: self.controller.show_frame(fn),
                             style="Welcome.TButton",
                             image=icon,
                             compound=tk.LEFT if icon else tk.NONE)

            btn.grid(row=row, column=col, padx=15, pady=10, sticky="ew")
            col += 1
            if col > 2:
                col = 0
                row += 1