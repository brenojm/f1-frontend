import tkinter as tk
from tkinter import ttk

from api_client import ApiClient

from views.welcome_view import WelcomeView
from views.driver_view import DriverListView, AddDriverView, EditDriverView
from views.team_view import TeamListView, AddTeamView, EditTeamView
from views.season_view import SeasonListView, AddSeasonView, EditSeasonView, DriverStandingsView, TeamStandingsView
from views.circuit_view import CircuitListView, AddCircuitView, EditCircuitView
from views.race_view import RaceListView, AddRaceView, EditRaceView
from views.driver_contract_view import ContractListView, AddContractView, EditContractView
from views.result_view import ResultListView, AddResultView, EditResultView
from views.overall_standings_view import OverallStandingsView

from ui_elements import COLOR_PRIMARY_ACCENT, COLOR_SUCCESS_ACCENT, COLOR_BACKGROUND_DARK, COLOR_FOREGROUND_LIGHT, \
    COLOR_BUTTON_TEXT, COLOR_DANGER_ACCENT, COLOR_BACKGROUND_MEDIUM, COLOR_BACKGROUND_LIGHT, COLOR_FOREGROUND_DARK, \
    COLOR_BORDER_FOCUS

class F1App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestão da F1")
        self.geometry("1280x720")
        self.configure(bg=COLOR_BACKGROUND_DARK)

        self._apply_styles()
        self.api_client = ApiClient()

        # Mapeamento de nomes de views para suas classes
        self.view_classes = {
            "WelcomeView": WelcomeView,
            "DriverListView": DriverListView,
            "AddDriverView": AddDriverView,
            "EditDriverView": EditDriverView,
            "TeamListView": TeamListView,
            "AddTeamView": AddTeamView,
            "EditTeamView": EditTeamView,
            "SeasonListView": SeasonListView,
            "AddSeasonView": AddSeasonView,
            "EditSeasonView": EditSeasonView,
            "DriverStandingsView": DriverStandingsView,
            "TeamStandingsView": TeamStandingsView,
            "OverallStandingsView": OverallStandingsView,
            "CircuitListView": CircuitListView,
            "AddCircuitView": AddCircuitView,
            "EditCircuitView": EditCircuitView,
            "RaceListView": RaceListView,
            "AddRaceView": AddRaceView,
            "EditRaceView": EditRaceView,
            "ContractListView": ContractListView,
            "AddContractView": AddContractView,
            "EditContractView": EditContractView,
            "ResultListView": ResultListView,
            "AddResultView": AddResultView,
            "EditResultView": EditResultView,
        }
        self._view_instances = {} # Armazenará as instâncias das views já criadas

        self._setup_container() # O container para as views
        self.show_frame("WelcomeView")

    def _apply_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')

        style.configure("TFrame", background=COLOR_BACKGROUND_DARK)
        style.configure("TLabel", background=COLOR_BACKGROUND_DARK, foreground=COLOR_FOREGROUND_LIGHT)
        style.configure("Monochromatic.TLabel", background=COLOR_BACKGROUND_DARK, foreground=COLOR_FOREGROUND_LIGHT)
        
        style.configure("TEntry", fieldbackground=COLOR_BACKGROUND_LIGHT, foreground=COLOR_FOREGROUND_LIGHT, insertbackground=COLOR_PRIMARY_ACCENT, relief="flat", borderwidth=1, padding=5)
        style.map("TEntry", fieldbackground=[('readonly', COLOR_BACKGROUND_MEDIUM)], foreground=[('readonly', COLOR_FOREGROUND_DARK)])
        style.configure("Monochromatic.TEntry", fieldbackground=COLOR_BACKGROUND_LIGHT, foreground=COLOR_FOREGROUND_LIGHT, insertbackground=COLOR_PRIMARY_ACCENT, relief="flat", borderwidth=1, padding=5)

        style.configure("TCombobox", fieldbackground=COLOR_BACKGROUND_LIGHT, foreground=COLOR_FOREGROUND_LIGHT, selectbackground=COLOR_PRIMARY_ACCENT, selectforeground="white", relief="flat", borderwidth=1, padding=5)
        style.map("TCombobox", fieldbackground=[('readonly', COLOR_BACKGROUND_LIGHT)], selectbackground=[('readonly', COLOR_PRIMARY_ACCENT)], selectforeground=[('readonly', "white")])
        style.configure("Monochromatic.TCombobox", fieldbackground=COLOR_BACKGROUND_LIGHT, foreground=COLOR_FOREGROUND_LIGHT, selectbackground=COLOR_PRIMARY_ACCENT, selectforeground="white", relief="flat", borderwidth=1, padding=5)
        style.configure("TCombobox", arrowsize=15)

        style.configure("TButton",
                        font=("Arial", 10, "bold"),
                        foreground=COLOR_BUTTON_TEXT,
                        background=COLOR_PRIMARY_ACCENT,
                        relief="flat",
                        padding=10,
                        anchor="center")
        style.map("TButton",
                    background=[("active", COLOR_SUCCESS_ACCENT)],
                    foreground=[("active", COLOR_BUTTON_TEXT)])

        style.configure("Primary.TButton", background=COLOR_PRIMARY_ACCENT)
        style.map("Primary.TButton", background=[("active", COLOR_SUCCESS_ACCENT)])

        style.configure("Accent.TButton", background=COLOR_SUCCESS_ACCENT)
        style.map("Accent.TButton", background=[("active", COLOR_PRIMARY_ACCENT)])

        style.configure("Delete.TButton", background=COLOR_DANGER_ACCENT)
        style.map("Delete.TButton", background=[("active", "#c0392b")])

        style.configure("Monochromatic.TButton",
                        background=COLOR_BACKGROUND_MEDIUM,
                        foreground=COLOR_FOREGROUND_LIGHT,
                        bordercolor=COLOR_PRIMARY_ACCENT,
                        borderwidth=1)
        style.map("Monochromatic.TButton",
                    background=[("active", COLOR_PRIMARY_ACCENT)],
                    foreground=[("active", COLOR_BUTTON_TEXT)])
        
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background=COLOR_BACKGROUND_LIGHT, foreground=COLOR_FOREGROUND_LIGHT, padding=5)
        style.configure("Treeview", font=("Arial", 10), rowheight=28, background=COLOR_BACKGROUND_MEDIUM, foreground=COLOR_FOREGROUND_LIGHT, fieldbackground=COLOR_BACKGROUND_MEDIUM, borderwidth=0)
        style.map('Treeview', background=[('selected', COLOR_PRIMARY_ACCENT)], foreground=[('selected', 'white')])
        
        style.configure("Treeview.Dark.Heading", font=("Arial", 10, "bold"), background=COLOR_BACKGROUND_LIGHT, foreground=COLOR_FOREGROUND_LIGHT)
        style.configure("Treeview.Dark", font=("Arial", 10), rowheight=28, background=COLOR_BACKGROUND_MEDIUM, foreground=COLOR_FOREGROUND_LIGHT, fieldbackground=COLOR_BACKGROUND_MEDIUM, borderwidth=0)
        style.map("Treeview.Dark", background=[('selected', COLOR_PRIMARY_ACCENT)], foreground=[('selected', 'white')])
        style.layout("Treeview.Dark", style.layout("Treeview")) 

        style.configure("TCheckbutton", background=COLOR_BACKGROUND_DARK, foreground=COLOR_FOREGROUND_LIGHT)
        style.configure("Monochromatic.TCheckbutton", background=COLOR_BACKGROUND_DARK, foreground=COLOR_FOREGROUND_LIGHT)

        style.configure("TNotebook", background=COLOR_BACKGROUND_DARK, borderwidth=0)
        style.configure("TNotebook.Tab", background=COLOR_BACKGROUND_MEDIUM, foreground=COLOR_FOREGROUND_LIGHT, padding=[10, 5], font=("Arial", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", COLOR_PRIMARY_ACCENT)], foreground=[("selected", "white")])

        style.configure("CardTitle.TLabel", background=COLOR_BACKGROUND_MEDIUM, foreground=COLOR_PRIMARY_ACCENT)
        style.configure("CardDetail.TLabel", background=COLOR_BACKGROUND_MEDIUM, foreground=COLOR_FOREGROUND_LIGHT)

    def _setup_container(self):
        self.container = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

    def show_frame(self, page_name, **kwargs):
        # Esconde todas as views atualmente visíveis
        for frame in self._view_instances.values():
            frame.grid_remove()

        # Cria a instância da view se ainda não existir
        if page_name not in self._view_instances:
            ViewClass = self.view_classes.get(page_name)
            if ViewClass:
                self._view_instances[page_name] = ViewClass(parent=self.container, controller=self)
                self._view_instances[page_name].grid(row=0, column=0, sticky="nsew")
            else:
                print(f"Erro: View '{page_name}' não encontrada.")
                return

        frame = self._view_instances[page_name]
        frame.grid(row=0, column=0, sticky="nsew")
        frame.tkraise()

        # Chama o método on_show da view, passando todos os kwargs
        # Cada view será responsável por interpretar esses kwargs e carregar seus próprios dados
        if hasattr(frame, 'on_show') and callable(getattr(frame, 'on_show')):
            frame.on_show(**kwargs)
        
        return frame

if __name__ == "__main__":
    app = F1App()
    app.mainloop()