import tkinter as tk
from tkinter import ttk, messagebox
import threading

from api_client import ApiClient
from ui_elements import LabeledEntry, LabeledCombobox, LabeledSpinbox, show_info, show_error, show_warning, ask_yes_no, \
    COLOR_PRIMARY_ACCENT, COLOR_SUCCESS_ACCENT, COLOR_BACKGROUND_DARK, COLOR_FOREGROUND_LIGHT, \
    COLOR_BUTTON_TEXT, COLOR_BACKGROUND_MEDIUM, COLOR_FOREGROUND_DARK, COLOR_DANGER_ACCENT, COLOR_BACKGROUND_LIGHT, \
    format_date_display, format_date_api, AppHeaderFrame

class RaceListView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.races = []
        self.seasons_map = {}
        self.circuits_map = {}
        
        self.create_widgets()

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Lista de Corridas")
        header.pack(fill="x", pady=(0, 10))

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Adicionar Nova Corrida", command=self.add_race, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Atualizar Lista", command=self.load_races, style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

        self.content_container = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        self.content_container.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        self.loading_label = ttk.Label(self.content_container, text="Carregando corridas...", 
                                        background=COLOR_BACKGROUND_DARK, foreground=COLOR_FOREGROUND_LIGHT,
                                        font=("Arial", 12, "bold"))
        
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background=COLOR_BACKGROUND_LIGHT, foreground=COLOR_FOREGROUND_LIGHT)
        style.configure("Treeview", font=("Arial", 10), rowheight=28, background=COLOR_BACKGROUND_MEDIUM, foreground=COLOR_FOREGROUND_LIGHT, fieldbackground=COLOR_BACKGROUND_MEDIUM)
        style.map('Treeview', background=[('selected', COLOR_PRIMARY_ACCENT)], foreground=[('selected', 'white')])

        self.tree = ttk.Treeview(self.content_container, columns=("ID", "Nome", "Data", "Temporada", "Circuito", "Voltas", "Clima"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nome", text="Nome")
        self.tree.heading("Data", text="Data")
        self.tree.heading("Temporada", text="Temporada")
        self.tree.heading("Circuito", text="Circuito")
        self.tree.heading("Voltas", text="Voltas")
        self.tree.heading("Clima", text="Clima")

        self.tree.column("ID", width=50, anchor=tk.CENTER)
        self.tree.column("Nome", width=150)
        self.tree.column("Data", width=100, anchor=tk.CENTER)
        self.tree.column("Temporada", width=80, anchor=tk.CENTER)
        self.tree.column("Circuito", width=120, anchor=tk.CENTER)
        self.tree.column("Voltas", width=60, anchor=tk.CENTER)
        self.tree.column("Clima", width=80, anchor=tk.CENTER)

        self.tree.bind("<Double-1>", self.on_double_click)

        action_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        action_frame.pack(pady=10)
        ttk.Button(action_frame, text="Editar Selecionado", command=self.edit_race, style="Accent.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="Excluir Selecionado", command=self.delete_race, style="Delete.TButton").pack(side=tk.LEFT, padx=10)
        
        ttk.Button(self, text="Voltar à Tela Inicial", command=lambda: self.controller.show_frame("WelcomeView"), 
                   style="Monochromatic.TButton").pack(pady=20)

    def on_show(self, **kwargs):
        self.load_races()

    def load_races(self):
        self.tree.pack_forget()
        self.loading_label.pack(pady=10)
        
        self.relations_loaded_event = threading.Event()
        
        threading.Thread(target=self._fetch_all_data_async, daemon=True).start()

    def _fetch_all_data_async(self):
        seasons_resp = self.api_client.get_seasons()
        circuits_resp = self.api_client.get_circuits()

        self.after(0, lambda: self._update_relations_maps_and_signal(seasons_resp, circuits_resp))
        
        self.relations_loaded_event.wait() 

        races_resp = self.api_client.get_races()
        
        self.after(0, lambda: self._handle_races_response(races_resp))

    def _update_relations_maps_and_signal(self, seasons_resp, circuits_resp):
        if isinstance(seasons_resp, dict) and "error" in seasons_resp:
            show_error("Erro", seasons_resp.get("error", "Falha ao carregar temporadas para exibição."))
        elif seasons_resp is not None:
            self.seasons_map = {s["id"]: s["year"] for s in seasons_resp}
        else:
            show_error("Erro", "Resposta inesperada para temporadas.")

        if isinstance(circuits_resp, dict) and "error" in circuits_resp:
            show_error("Erro", circuits_resp.get("error", "Falha ao carregar circuitos para exibição."))
        elif circuits_resp is not None:
            self.circuits_map = {c["id"]: c["name"] for c in circuits_resp}
        else:
            show_error("Erro", "Resposta inesperada para circuitos.")
        
        self.relations_loaded_event.set()

    def _handle_races_response(self, response):
        self.loading_label.pack_forget()

        for item in self.tree.get_children():
            self.tree.delete(item)

        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao carregar corridas."))
        elif response is not None:
            self.races = response
            for race in self.races:
                season_year = self.seasons_map.get(race.get("season_id"), "N/A")
                circuit_name = self.circuits_map.get(race.get("circuit_id"), "N/A")
                
                race_date_display = format_date_display(race.get("race_date", ""))
                self.tree.insert("", tk.END, values=(
                    race.get("id"),
                    race.get("name"),
                    race_date_display,
                    season_year,
                    circuit_name,
                    race.get("laps"),
                    race.get("weather")
                ))
            self.tree.pack(fill=tk.BOTH, expand=True)
        else:
            show_error("Erro", "Resposta inesperada da API.")

    def add_race(self):
        self.controller.show_frame("AddRaceView")

    def edit_race(self):
        selected_item = self.tree.focus()
        if not selected_item:
            show_warning("Nenhuma Seleção", "Por favor, selecione uma corrida para editar.")
            return

        race_id = self.tree.item(selected_item, "values")[0]
        self.controller.show_frame("EditRaceView", race_id=race_id)

    def delete_race(self):
        selected_item = self.tree.focus()
        if not selected_item:
            show_warning("Nenhuma Seleção", "Por favor, selecione uma corrida para excluir.")
            return

        race_id = self.tree.item(selected_item, "values")[0]
        if ask_yes_no("Confirmar Exclusão", f"Tem certeza que deseja excluir a corrida ID {race_id}?"):
            response = self.api_client.delete_race(race_id)
            if response is True:
                show_info("Sucesso", "Corrida excluída com sucesso!")
                self.load_races()
            else:
                show_error("Erro", response.get("error", "Falha ao excluir corrida."))

    def on_double_click(self, event):
        self.edit_race()

class AddRaceView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.seasons_data = {}
        self.circuits_data = {}
        self.create_widgets()

    def _fetch_and_populate_relations_async(self):
        seasons_resp = self.api_client.get_seasons()
        circuits_resp = self.api_client.get_circuits()

        self.after(0, lambda: self._populate_comboboxes(seasons_resp, circuits_resp))

    def _populate_comboboxes(self, seasons_resp, circuits_resp):
        if isinstance(seasons_resp, dict) and "error" in seasons_resp:
            show_error("Erro", seasons_resp.get("error", "Falha ao carregar temporadas para seleção."))
        elif seasons_resp is not None:
            self.seasons_data = {s["id"]: s["year"] for s in seasons_resp}
            self.season_combobox.update_options(self.seasons_data) # Use update_options
        else:
            show_error("Erro", "Resposta inesperada para temporadas.")

        if isinstance(circuits_resp, dict) and "error" in circuits_resp:
            show_error("Erro", circuits_resp.get("error", "Falha ao carregar circuitos para seleção."))
        elif circuits_resp is not None:
            self.circuits_data = {c["id"]: c["name"] for c in circuits_resp}
            self.circuit_combobox.update_options(self.circuits_data) # Use update_options
        else:
            show_error("Erro", "Resposta inesperada para circuitos.")

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Adicionar Nova Corrida")
        header.pack(fill="x", pady=(0, 10))

        form_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        form_frame.pack(pady=10, padx=20, fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        self.name_entry = LabeledEntry(form_frame, "Nome:")
        self.name_entry.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        self.race_date_entry = LabeledEntry(form_frame, "Data da Corrida (DD/MM/AAAA):")
        self.race_date_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)

        self.season_combobox = LabeledCombobox(form_frame, "Temporada:", {})
        self.season_combobox.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)

        self.circuit_combobox = LabeledCombobox(form_frame, "Circuito:", {})
        self.circuit_combobox.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)

        self.laps_entry = LabeledEntry(form_frame, "Voltas (opcional):")
        self.laps_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)
        self.weather_combobox = LabeledCombobox(form_frame, "Clima (opcional):", {"Seco": "Dry", "Molhado": "Wet", "Misto": "Mixed", "": ""})
        self.weather_combobox.grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Salvar", command=self.save_race, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancelar", command=lambda: self.controller.show_frame("RaceListView"), style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

    def on_show(self, **kwargs):
        self.name_entry.set("")
        self.race_date_entry.set("")
        self.season_combobox.set_by_name("") # Corrected: use set_by_name
        self.circuit_combobox.set_by_name("") # Corrected: use set_by_name
        self.laps_entry.set("")
        self.weather_combobox.set_by_name("")
        
        threading.Thread(target=self._fetch_and_populate_relations_async, daemon=True).start()

    def save_race(self):
        season_id = self.season_combobox.get_id()
        circuit_id = self.circuit_combobox.get_id()

        if season_id is None or circuit_id is None:
            show_warning("Erro de Entrada", "Por favor, selecione uma Temporada e um Circuito válidos.")
            return

        race_date_api_format = format_date_api(self.race_date_entry.get()) if self.race_date_entry.get() else None

        data = {
            "name": self.name_entry.get(),
            "race_date": race_date_api_format,
            "season_id": season_id,
            "circuit_id": circuit_id,
            "laps": self.laps_entry.get() or None,
            "weather": self.weather_combobox.get_name() or None,
        }

        if not data["name"]:
            show_warning("Erro de Entrada", "O Nome é obrigatório.")
            return
        if not self.race_date_entry.get():
            show_warning("Erro de Entrada", "A Data da Corrida é obrigatória.")
            return

        if self.race_date_entry.get() and race_date_api_format is None:
            show_warning("Erro de Entrada", "A Data da Corrida deve estar no formato DD/MM/AAAA.")
            return

        if data["laps"]:
            try:
                data["laps"] = int(data["laps"])
                if data["laps"] <= 0:
                    show_warning("Erro de Entrada", "As Voltas devem ser um número positivo.")
                    return
            except ValueError:
                show_warning("Erro de Entrada", "As Voltas devem ser um número inteiro.")
                return

        response = self.api_client.add_race(data)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao adicionar corrida."))
        else:
            show_info("Sucesso", "Corrida adicionada com sucesso!")
            self.controller.show_frame("RaceListView")

class EditRaceView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.race_id = None
        self._original_season_id = None
        self._original_circuit_id = None
        self.seasons_data = {}
        self.circuits_data = {}
        self.create_widgets()

    def _fetch_relations_data_for_display_async(self, race_id):
        seasons_resp = self.api_client.get_seasons()
        circuits_resp = self.api_client.get_circuits()

        self.after(0, lambda: self._update_relations_maps_and_load_race(seasons_resp, circuits_resp, race_id))

    def _update_relations_maps_and_load_race(self, seasons_resp, circuits_resp, race_id):
        if isinstance(seasons_resp, dict) and "error" in seasons_resp:
            show_error("Erro", seasons_resp.get("error", "Falha ao carregar temporadas para exibição."))
        elif seasons_resp is not None:
            self.seasons_data = {s["id"]: s["year"] for s in seasons_resp}
            self.season_combobox.update_options(self.seasons_data) # Use update_options
        else:
            show_error("Erro", "Resposta inesperada para temporadas.")

        if isinstance(circuits_resp, dict) and "error" in circuits_resp:
            show_error("Erro", circuits_resp.get("error", "Falha ao carregar circuitos para exibição."))
        elif circuits_resp is not None:
            self.circuits_data = {c["id"]: c["name"] for c in circuits_resp}
            self.circuit_combobox.update_options(self.circuits_data) # Use update_options
        else:
            show_error("Erro", "Resposta inesperada para circuitos.")
        
        self._load_race_data_sync(race_id)

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Editar Corrida")
        header.pack(fill="x", pady=(0, 10))

        form_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        form_frame.pack(pady=10, padx=20, fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        self.name_entry = LabeledEntry(form_frame, "Nome:")
        self.name_entry.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        self.race_date_entry = LabeledEntry(form_frame, "Data da Corrida (DD/MM/AAAA):")
        self.race_date_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)

        self.season_combobox = LabeledCombobox(form_frame, "Temporada:", {})
        self.season_combobox.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)

        self.circuit_combobox = LabeledCombobox(form_frame, "Circuito:", {})
        self.circuit_combobox.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)

        self.laps_entry = LabeledEntry(form_frame, "Voltas (opcional):")
        self.laps_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)
        self.weather_combobox = LabeledCombobox(form_frame, "Clima (opcional):", {"Seco": "Dry", "Molhado": "Wet", "Misto": "Mixed", "": ""})
        self.weather_combobox.grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Salvar Alterações", command=self.save_changes, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancelar", command=lambda: self.controller.show_frame("RaceListView"), style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

    def on_show(self, race_id=None, **kwargs):
        if race_id:
            self.race_id = race_id
            threading.Thread(target=self._fetch_relations_data_for_display_async, args=(race_id,), daemon=True).start()
        else:
            show_error("Erro", "ID da corrida não fornecido para edição.")
            self.controller.show_frame("RaceListView")

    def _load_race_data_sync(self, race_id):
        self.race_id = race_id
        response = self.api_client.get_race(race_id)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao carregar dados da corrida."))
            self.controller.show_frame("RaceListView")
        elif response is not None:
            self.name_entry.set(response.get("name", ""))
            
            race_date_display_format = format_date_display(response.get("race_date", ""))
            self.race_date_entry.set(race_date_display_format)
            
            self._original_season_id = response.get("season_id")
            self._original_circuit_id = response.get("circuit_id")
            
            self.season_combobox.set_by_id(self._original_season_id)
            self.circuit_combobox.set_by_id(self._original_circuit_id)

            self.laps_entry.set(str(response.get("laps", "") or ""))
            self.weather_combobox.set_by_name(response.get("weather", "") or "")
        else:
            show_error("Erro", "Resposta inesperada ao carregar dados da corrida.")

    def save_changes(self):
        race_date_api_format = format_date_api(self.race_date_entry.get()) if self.race_date_entry.get() else None

        season_id = self.season_combobox.get_id()
        circuit_id = self.circuit_combobox.get_id()

        if season_id is None:
            show_warning("Erro de Entrada", "Por favor, selecione uma Temporada válida.")
            return
        if circuit_id is None:
            show_warning("Erro de Entrada", "Por favor, selecione um Circuito válido.")
            return

        data = {
            "name": self.name_entry.get(),
            "race_date": race_date_api_format,
            "season_id": season_id,
            "circuit_id": circuit_id,
            "laps": self.laps_entry.get() or None,
            "weather": self.weather_combobox.get_name() or None,
        }

        if not data["name"]:
            show_warning("Erro de Entrada", "O Nome é obrigatório.")
            return
        if not self.race_date_entry.get():
            show_warning("Erro de Entrada", "A Data da Corrida é obrigatória.")
            return

        if self.race_date_entry.get() and race_date_api_format is None:
            show_warning("Erro de Entrada", "A Data da Corrida deve estar no formato DD/MM/AAAA.")
            return

        if data["laps"]:
            try:
                data["laps"] = int(data["laps"])
                if data["laps"] <= 0:
                    show_warning("Erro de Entrada", "As Voltas devem ser um número positivo.")
                    return
            except ValueError:
                show_warning("Erro de Entrada", "As Voltas devem ser um número inteiro.")
                return

        response = self.api_client.update_race(self.race_id, data)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao atualizar corrida."))
        else:
            show_info("Sucesso", "Corrida atualizada com sucesso!")
            self.controller.show_frame("RaceListView")