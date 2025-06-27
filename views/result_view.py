import tkinter as tk
from tkinter import ttk, messagebox
import threading # Importar o módulo threading

from api_client import ApiClient
from ui_elements import LabeledEntry, LabeledCombobox, LabeledSpinbox, LabeledCheckbutton, show_info, show_error, show_warning, ask_yes_no, \
    COLOR_PRIMARY_ACCENT, COLOR_SUCCESS_ACCENT, COLOR_BACKGROUND_DARK, COLOR_FOREGROUND_LIGHT, \
    COLOR_BUTTON_TEXT, COLOR_BACKGROUND_MEDIUM, COLOR_FOREGROUND_DARK, COLOR_BACKGROUND_LIGHT, AppHeaderFrame

class ResultListView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.results = []
        self.races_map = {}
        self.teams_map = {}
        self.drivers_map = {}
        
        # REMOVIDO: Carregamento de dados de relação e resultados do __init__
        # self._load_relations_data()
        # self.load_results()

        self.create_widgets()

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Lista de Resultados de Corridas")
        header.pack(fill="x", pady=(0, 10))

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Adicionar Novo Resultado", command=self.add_result, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        # O botão "Atualizar Lista" agora chamará o método que inicia o carregamento assíncrono
        ttk.Button(button_frame, text="Atualizar Lista", command=self.load_results, style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

        # Container para o indicador de carregamento e o Treeview
        self.content_container = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        self.content_container.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Indicador de Carregamento
        self.loading_label = ttk.Label(self.content_container, text="Carregando resultados...", 
                                       background=COLOR_BACKGROUND_DARK, foreground=COLOR_FOREGROUND_LIGHT,
                                       font=("Arial", 12, "bold"))
        
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background=COLOR_BACKGROUND_LIGHT, foreground=COLOR_FOREGROUND_LIGHT)
        style.configure("Treeview", font=("Arial", 10), rowheight=28, background=COLOR_BACKGROUND_MEDIUM, foreground=COLOR_FOREGROUND_LIGHT, fieldbackground=COLOR_BACKGROUND_MEDIUM)
        style.map('Treeview', background=[('selected', COLOR_PRIMARY_ACCENT)], foreground=[('selected', 'white')])

        self.tree = ttk.Treeview(self.content_container, columns=("ID", "Corrida", "Equipe", "Piloto", "Posição", "Pontos", "Volta Mais Rápida"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Corrida", text="Corrida")
        self.tree.heading("Equipe", text="Equipe")
        self.tree.heading("Piloto", text="Piloto")
        self.tree.heading("Posição", text="Posição")
        self.tree.heading("Pontos", text="Pontos")
        self.tree.heading("Volta Mais Rápida", text="Volta Mais Rápida")

        self.tree.column("ID", width=50, anchor=tk.CENTER)
        self.tree.column("Corrida", width=120, anchor=tk.CENTER)
        self.tree.column("Equipe", width=100, anchor=tk.CENTER)
        self.tree.column("Piloto", width=120, anchor=tk.CENTER)
        self.tree.column("Posição", width=70, anchor=tk.CENTER)
        self.tree.column("Pontos", width=70, anchor=tk.CENTER)
        self.tree.column("Volta Mais Rápida", width=100, anchor=tk.CENTER)

        # self.tree será empacotado/desempacotado dinamicamente
        self.tree.bind("<Double-1>", self.on_double_click)

        action_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        action_frame.pack(pady=10)
        ttk.Button(action_frame, text="Editar Selecionado", command=self.edit_result, style="Accent.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="Excluir Selecionado", command=self.delete_result, style="Delete.TButton").pack(side=tk.LEFT, padx=10)
        
        ttk.Button(self, text="Voltar à Tela Inicial", command=lambda: self.controller.show_frame("WelcomeView"), 
                   style="Monochromatic.TButton").pack(pady=20)

    # NOVO: Método chamado pelo Controller quando esta tela é exibida
    def on_show(self, **kwargs):
        """Carrega os dados de relações e resultados quando a ResultListView é exibida."""
        self.load_results()

    # ATUALIZADO: Este método agora coordena o carregamento assíncrono
    def load_results(self):
        # 1. Esconde o treeview e mostra o indicador de carregamento
        self.tree.pack_forget()
        self.loading_label.pack(pady=10)
        
        # 2. Inicia o carregamento das relações e resultados em threads separadas
        self.relations_loaded_event = threading.Event()
        
        threading.Thread(target=self._fetch_all_data_async, daemon=True).start()

    def _fetch_all_data_async(self):
        """Busca todas as dependências (corridas, equipes, pilotos) e resultados em threads separadas."""
        # Busca relações
        races_resp = self.api_client.get_races()
        teams_resp = self.api_client.get_teams()
        drivers_resp = self.api_client.get_drivers()

        # Atualiza os mapas na thread principal e sinaliza que as relações estão carregadas
        self.after(0, lambda: self._update_relations_maps_and_signal(races_resp, teams_resp, drivers_resp))
        
        # Aguarda que as relações sejam processadas na thread principal antes de buscar resultados
        self.relations_loaded_event.wait() 

        # Busca resultados
        results_resp = self.api_client.get_results()
        
        # Atualiza o Treeview na thread principal
        self.after(0, lambda: self._handle_results_response(results_resp))

    def _update_relations_maps_and_signal(self, races_resp, teams_resp, drivers_resp):
        """Atualiza os mapas de relações e sinaliza que terminaram."""
        if isinstance(races_resp, dict) and "error" in races_resp:
            show_error("Erro", races_resp.get("error", "Falha ao carregar corridas para exibição."))
        elif races_resp is not None:
            self.races_map = {r["id"]: r["name"] for r in races_resp}
        else:
            show_error("Erro", "Resposta inesperada para corridas.")

        if isinstance(teams_resp, dict) and "error" in teams_resp:
            show_error("Erro", teams_resp.get("error", "Falha ao carregar equipes para exibição."))
        elif teams_resp is not None:
            self.teams_map = {t["id"]: t["name"] for t in teams_resp}
        else:
            show_error("Erro", "Resposta inesperada para equipes.")

        if isinstance(drivers_resp, dict) and "error" in drivers_resp:
            show_error("Erro", drivers_resp.get("error", "Falha ao carregar pilotos para exibição."))
        elif drivers_resp is not None:
            self.drivers_map = {d["id"]: d["full_name"] for d in drivers_resp}
        else:
            show_error("Erro", "Resposta inesperada para pilotos.")
        
        self.relations_loaded_event.set() # Sinaliza que as relações foram carregadas e mapas atualizados

    def _handle_results_response(self, response):
        """Método para processar a resposta da API de resultados e atualizar a UI na thread principal."""
        # 4. Esconde o indicador de carregamento
        self.loading_label.pack_forget()

        # 5. Limpa o treeview antes de popular com novos dados
        for item in self.tree.get_children():
            self.tree.delete(item)

        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao carregar resultados."))
        elif response is not None:
            self.results = response
            for result in self.results:
                race_name = self.races_map.get(result.get("race_id"), "N/A")
                team_name = self.teams_map.get(result.get("team_id"), "N/A")
                driver_name = self.drivers_map.get(result.get("driver_id"), "N/A")
                self.tree.insert("", tk.END, values=(
                    result.get("id"),
                    race_name,
                    team_name,
                    driver_name,
                    result.get("position"),
                    result.get("points"),
                    result.get("fastest_lap")
                ))
            # 6. Empacota o treeview de volta após carregar os dados
            self.tree.pack(fill=tk.BOTH, expand=True)
        else:
            show_error("Erro", "Resposta inesperada da API.")

    def add_result(self):
        self.controller.show_frame("AddResultView")

    def edit_result(self):
        selected_item = self.tree.focus()
        if not selected_item:
            show_warning("Nenhuma Seleção", "Por favor, selecione um resultado para editar.")
            return

        result_id = self.tree.item(selected_item, "values")[0]
        self.controller.show_frame("EditResultView", result_id=result_id)

    def delete_result(self):
        selected_item = self.tree.focus()
        if not selected_item:
            show_warning("Nenhuma Seleção", "Por favor, selecione um resultado para excluir.")
            return

        result_id = self.tree.item(selected_item, "values")[0]
        if ask_yes_no("Confirmar Exclusão", f"Tem certeza que deseja excluir o resultado ID {result_id}?"):
            response = self.api_client.delete_result(result_id)
            if response is True:
                show_info("Sucesso", "Resultado excluído com sucesso!")
                self.load_results() # Recarrega a lista após exclusão
            else:
                show_error("Erro", response.get("error", "Falha ao excluir resultado."))

    def on_double_click(self, event):
        self.edit_result()

class AddResultView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.races_data = {}
        self.teams_data = {}
        self.drivers_data = {}
        # REMOVIDO: Carregamento de dados de relação do __init__
        # self._load_relations_data()
        self.create_widgets()

    # ATUALIZADO: Método assíncrono para carregar dados de relações e popular comboboxes
    def _fetch_and_populate_relations_async(self):
        """Busca e popula os dados das comboboxes em uma thread separada."""
        races_resp = self.api_client.get_races()
        teams_resp = self.api_client.get_teams()
        drivers_resp = self.api_client.get_drivers()

        self.after(0, lambda: self._populate_comboboxes(races_resp, teams_resp, drivers_resp))

    def _populate_comboboxes(self, races_resp, teams_resp, drivers_resp):
        """Popula as comboboxes na thread principal."""
        if isinstance(races_resp, dict) and "error" in races_resp:
            show_error("Erro", races_resp.get("error", "Falha ao carregar corridas para seleção."))
        elif races_resp is not None:
            self.races_data = {r["id"]: r["name"] for r in races_resp}
            self.race_combobox.set_options(self.races_data)
        else:
            show_error("Erro", "Resposta inesperada para corridas.")

        if isinstance(teams_resp, dict) and "error" in teams_resp:
            show_error("Erro", teams_resp.get("error", "Falha ao carregar equipes para seleção."))
        elif teams_resp is not None:
            self.teams_data = {t["id"]: t["name"] for t in teams_resp}
            self.team_combobox.set_options(self.teams_data)
        else:
            show_error("Erro", "Resposta inesperada para equipes.")

        if isinstance(drivers_resp, dict) and "error" in drivers_resp:
            show_error("Erro", drivers_resp.get("error", "Falha ao carregar pilotos para seleção."))
        elif drivers_resp is not None:
            self.drivers_data = {d["id"]: d["full_name"] for d in drivers_resp}
            self.driver_combobox.set_options(self.drivers_data)
        else:
            show_error("Erro", "Resposta inesperada para pilotos.")

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Adicionar Novo Resultado de Corrida")
        header.pack(fill="x", pady=(0, 10))

        form_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        form_frame.pack(pady=10, padx=20, fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        # As comboboxes são criadas vazias no __init__
        self.race_combobox = LabeledCombobox(form_frame, "Corrida:", {})
        self.race_combobox.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        self.team_combobox = LabeledCombobox(form_frame, "Equipe:", {})
        self.team_combobox.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.driver_combobox = LabeledCombobox(form_frame, "Piloto:", {})
        self.driver_combobox.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)

        self.position_spinbox = LabeledSpinbox(form_frame, "Posição (1-20):", from_=1, to=20)
        self.position_spinbox.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        self.points_spinbox = LabeledSpinbox(form_frame, "Pontos (0-25):", from_=0, to=25)
        self.points_spinbox.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)
        self.fastest_lap_check = LabeledCheckbutton(form_frame, "Volta Mais Rápida:")
        self.fastest_lap_check.grid(row=5, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Salvar", command=self.save_result, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancelar", command=lambda: self.controller.show_frame("ResultListView"), style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

    # NOVO: Método on_show para carregar relações e limpar campos
    def on_show(self, **kwargs):
        """Carrega dados para as comboboxes e limpa os campos ao exibir."""
        self.race_combobox.set("")
        self.team_combobox.set("")
        self.driver_combobox.set("")
        self.position_spinbox.set(1) # Valor padrão
        self.points_spinbox.set(0)   # Valor padrão
        self.fastest_lap_check.set(False) # Valor padrão
        
        # Inicia o carregamento assíncrono das relações
        threading.Thread(target=self._fetch_and_populate_relations_async, daemon=True).start()

    def save_result(self):
        race_id = self.race_combobox.get_id()
        team_id = self.team_combobox.get_id()
        driver_id = self.driver_combobox.get_id()

        if race_id is None or team_id is None or driver_id is None:
            show_warning("Erro de Entrada", "Por favor, selecione uma Corrida, Equipe e Piloto válidos.")
            return

        data = {
            "race_id": race_id,
            "team_id": team_id,
            "driver_id": driver_id,
            "position": self.position_spinbox.get(),
            "points": self.points_spinbox.get(),
            "fastest_lap": self.fastest_lap_check.get(),
        }

        if not (1 <= data["position"] <= 20):
            show_warning("Erro de Entrada", "A Posição deve estar entre 1 e 20.")
            return
        if not (0 <= data["points"] <= 25):
            show_warning("Erro de Entrada", "Os Pontos devem estar entre 0 e 25.")
            return

        response = self.api_client.add_result(data)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao adicionar resultado."))
        else:
            show_info("Sucesso", "Resultado adicionado com sucesso!")
            self.controller.show_frame("ResultListView")

class EditResultView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.result_id = None
        self._original_race_id = None # Armazena o ID original da corrida
        self.races_data = {}
        self.teams_data = {}
        self.drivers_data = {}
        # REMOVIDO: Carregamento de dados de relação do __init__
        # self._load_relations_data()
        self.create_widgets()

    # ATUALIZADO: Método assíncrono para carregar dados de relações
    def _fetch_relations_data_for_display_async(self, result_id):
        """Busca dados de corridas, equipes e pilotos em uma thread separada para display."""
        races_resp = self.api_client.get_races()
        teams_resp = self.api_client.get_teams()
        drivers_resp = self.api_client.get_drivers()

        # Usar self.after para atualizar os maps na thread principal e carregar o resultado
        self.after(0, lambda: self._update_relations_maps_and_load_result(races_resp, teams_resp, drivers_resp, result_id))

    def _update_relations_maps_and_load_result(self, races_resp, teams_resp, drivers_resp, result_id):
        """Atualiza os mapas de relações e então carrega os dados do resultado na thread principal."""
        if isinstance(races_resp, dict) and "error" in races_resp:
            show_error("Erro", races_resp.get("error", "Falha ao carregar corridas para exibição."))
        elif races_resp is not None:
            self.races_data = {r["id"]: r["name"] for r in races_resp}
        else:
            show_error("Erro", "Resposta inesperada para corridas.")

        if isinstance(teams_resp, dict) and "error" in teams_resp:
            show_error("Erro", teams_resp.get("error", "Falha ao carregar equipes para exibição."))
        elif teams_resp is not None:
            self.teams_data = {t["id"]: t["name"] for t in teams_resp}
            # Atualiza as opções do combobox para a edição
            self.team_combobox.set_options(self.teams_data)
        else:
            show_error("Erro", "Resposta inesperada para equipes.")

        if isinstance(drivers_resp, dict) and "error" in drivers_resp:
            show_error("Erro", drivers_resp.get("error", "Falha ao carregar pilotos para exibição."))
        elif drivers_resp is not None:
            self.drivers_data = {d["id"]: d["full_name"] for d in drivers_resp}
            # Atualiza as opções do combobox para a edição
            self.driver_combobox.set_options(self.drivers_data)
        else:
            show_error("Erro", "Resposta inesperada para pilotos.")
        
        # Agora que os mapas e comboboxes estão atualizados, carregue os dados do resultado
        self._load_result_data_sync(result_id)

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Editar Resultado de Corrida")
        header.pack(fill="x", pady=(0, 10))

        form_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        form_frame.pack(pady=10, padx=20, fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        self.race_display = LabeledEntry(form_frame, "Corrida (Imutável):", readonly=True)
        self.race_display.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)

        # As comboboxes são criadas vazias no __init__ e populadas em on_show
        self.team_combobox = LabeledCombobox(form_frame, "Equipe:", {})
        self.team_combobox.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)

        self.driver_combobox = LabeledCombobox(form_frame, "Piloto:", {})
        self.driver_combobox.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)

        self.position_spinbox = LabeledSpinbox(form_frame, "Posição (1-20):", from_=1, to=20)
        self.position_spinbox.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        self.points_spinbox = LabeledSpinbox(form_frame, "Pontos (0-25):", from_=0, to=25)
        self.points_spinbox.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)
        self.fastest_lap_check = LabeledCheckbutton(form_frame, "Volta Mais Rápida:")
        self.fastest_lap_check.grid(row=5, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Salvar Alterações", command=self.save_changes, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancelar", command=lambda: self.controller.show_frame("ResultListView"), style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

    # Renomeado para indicar que é chamado sincronicamente após _update_relations_maps_and_load_result
    def _load_result_data_sync(self, result_id):
        self.result_id = result_id
        response = self.api_client.get_result(result_id)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao carregar dados do resultado."))
            self.controller.show_frame("ResultListView")
        elif response is not None:
            # A corrida é imutável, apenas exibe o nome
            self._original_race_id = response.get("race_id")
            self.race_display.set(self.races_data.get(self._original_race_id, "N/A")) 
            
            self.team_combobox.set_by_id(response.get("team_id"))
            self.driver_combobox.set_by_id(response.get("driver_id"))
            self.position_spinbox.set(response.get("position", ""))
            self.points_spinbox.set(response.get("points", ""))
            self.fastest_lap_check.set(response.get("fastest_lap", False))
        else:
            show_error("Erro", "Resposta inesperada ao carregar dados do resultado.")

    def save_changes(self):
        team_id = self.team_combobox.get_id()
        driver_id = self.driver_combobox.get_id()

        if team_id is None or driver_id is None:
            show_warning("Erro de Entrada", "Por favor, selecione uma Equipe e Piloto válidos.")
            return

        data = {
            "team_id": team_id,
            "driver_id": driver_id,
            "race_id": self._original_race_id, # Usar o ID da corrida original, pois ela é imutável
            "position": self.position_spinbox.get(),
            "points": self.points_spinbox.get(),
            "fastest_lap": self.fastest_lap_check.get(),
        }

        if not (1 <= data["position"] <= 20):
            show_warning("Erro de Entrada", "A Posição deve estar entre 1 e 20.")
            return
        if not (0 <= data["points"] <= 25):
            show_warning("Erro de Entrada", "Os Pontos devem estar entre 0 e 25.")
            return

        response = self.api_client.update_result(self.result_id, data)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao atualizar resultado."))
        else:
            show_info("Sucesso", "Resultado atualizado com sucesso!")
            self.controller.show_frame("ResultListView")