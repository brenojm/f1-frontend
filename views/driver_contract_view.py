import tkinter as tk
from tkinter import ttk, messagebox
from api_client import ApiClient
from ui_elements import LabeledEntry, LabeledCombobox, LabeledSpinbox, show_info, show_error, show_warning, ask_yes_no, \
    COLOR_PRIMARY_ACCENT, COLOR_SUCCESS_ACCENT, COLOR_BACKGROUND_DARK, COLOR_FOREGROUND_LIGHT, \
    COLOR_BUTTON_TEXT, COLOR_BACKGROUND_MEDIUM, COLOR_FOREGROUND_DARK, COLOR_BACKGROUND_LIGHT, AppHeaderFrame # Importar AppHeaderFrame

class ContractListView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.contracts = []
        self.seasons_map = {}
        self.teams_map = {}
        self.drivers_map = {}
        self._load_relations_data()

        self.create_widgets()
        self.load_contracts()

    def _load_relations_data(self):
        seasons_resp = self.api_client.get_seasons()
        if isinstance(seasons_resp, dict) and "error" in seasons_resp:
            show_error("Erro", seasons_resp.get("error", "Falha ao carregar temporadas para exibição."))
        elif seasons_resp is not None:
            self.seasons_map = {s["id"]: s["year"] for s in seasons_resp}
        else:
            show_error("Erro", "Resposta inesperada para temporadas.")

        teams_resp = self.api_client.get_teams()
        if isinstance(teams_resp, dict) and "error" in teams_resp:
            show_error("Erro", teams_resp.get("error", "Falha ao carregar equipes para exibição."))
        elif teams_resp is not None:
            self.teams_map = {t["id"]: t["name"] for t in teams_resp}
        else:
            show_error("Erro", "Resposta inesperada para equipes.")

        drivers_resp = self.api_client.get_drivers()
        if isinstance(drivers_resp, dict) and "error" in drivers_resp:
            show_error("Erro", drivers_resp.get("error", "Falha ao carregar pilotos para exibição."))
        elif drivers_resp is not None:
            self.drivers_map = {d["id"]: d["full_name"] for d in drivers_resp}
        else:
            show_error("Erro", "Resposta inesperada para pilotos.")

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Lista de Contratos de Pilotos")
        header.pack(fill="x", pady=(0, 10))

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Adicionar Novo Contrato", command=self.add_contract, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Atualizar Lista", command=self.load_contracts, style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background=COLOR_BACKGROUND_LIGHT, foreground=COLOR_FOREGROUND_LIGHT)
        style.configure("Treeview", font=("Arial", 10), rowheight=28, background=COLOR_BACKGROUND_MEDIUM, foreground=COLOR_FOREGROUND_LIGHT, fieldbackground=COLOR_BACKGROUND_MEDIUM)
        style.map('Treeview', background=[('selected', COLOR_PRIMARY_ACCENT)], foreground=[('selected', 'white')])

        self.tree = ttk.Treeview(self, columns=("ID", "Temporada", "Equipe", "Piloto", "Número", "Salário (MUSD)"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Temporada", text="Temporada")
        self.tree.heading("Equipe", text="Equipe")
        self.tree.heading("Piloto", text="Piloto")
        self.tree.heading("Número", text="Número")
        self.tree.heading("Salário (MUSD)", text="Salário (MUSD)")

        self.tree.column("ID", width=50, anchor=tk.CENTER)
        self.tree.column("Temporada", width=80, anchor=tk.CENTER)
        self.tree.column("Equipe", width=120, anchor=tk.CENTER)
        self.tree.column("Piloto", width=150, anchor=tk.CENTER)
        self.tree.column("Número", width=80, anchor=tk.CENTER)
        self.tree.column("Salário (MUSD)", width=100, anchor=tk.CENTER)

        self.tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        self.tree.bind("<Double-1>", self.on_double_click)

        action_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        action_frame.pack(pady=10)
        ttk.Button(action_frame, text="Editar Selecionado", command=self.edit_contract, style="Accent.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="Excluir Selecionado", command=self.delete_contract, style="Delete.TButton").pack(side=tk.LEFT, padx=10)
        
        ttk.Button(self, text="Voltar à Tela Inicial", command=lambda: self.controller.show_frame("WelcomeView"), 
                   style="Monochromatic.TButton").pack(pady=20)

    def load_contracts(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        response = self.api_client.get_contracts()
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao carregar contratos."))
        elif response is not None:
            self.contracts = response
            for contract in self.contracts:
                season_year = self.seasons_map.get(contract.get("season_id"), "N/A")
                team_name = self.teams_map.get(contract.get("team_id"), "N/A")
                driver_name = self.drivers_map.get(contract.get("driver_id"), "N/A")
                self.tree.insert("", tk.END, values=(
                    contract.get("id"),
                    season_year,
                    team_name,
                    driver_name,
                    contract.get("number"),
                    contract.get("salary_musd")
                ))
        else:
            show_error("Erro", "Resposta inesperada da API.")

    def add_contract(self):
        self.controller.show_frame("AddContractView")

    def edit_contract(self):
        selected_item = self.tree.focus()
        if not selected_item:
            show_warning("Nenhuma Seleção", "Por favor, selecione um contrato para editar.")
            return

        contract_id = self.tree.item(selected_item, "values")[0]
        self.controller.show_frame("EditContractView", contract_id=contract_id)

    def delete_contract(self):
        selected_item = self.tree.focus()
        if not selected_item:
            show_warning("Nenhuma Seleção", "Por favor, selecione um contrato para excluir.")
            return

        contract_id = self.tree.item(selected_item, "values")[0]
        if ask_yes_no("Confirmar Exclusão", f"Tem certeza que deseja excluir o contrato ID {contract_id}?"):
            response = self.api_client.delete_contract(contract_id)
            if response is True:
                show_info("Sucesso", "Contrato excluído com sucesso!")
                self.load_contracts()
            else:
                show_error("Erro", response.get("error", "Falha ao excluir contrato."))

    def on_double_click(self, event):
        self.edit_contract()

class AddContractView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.seasons_data = {}
        self.teams_data = {}
        self.drivers_data = {}
        self._load_relations_data()
        self.create_widgets()

    def _load_relations_data(self):
        seasons_resp = self.api_client.get_seasons()
        if isinstance(seasons_resp, dict) and "error" in seasons_resp:
            show_error("Erro", seasons_resp.get("error", "Falha ao carregar temporadas para seleção."))
        elif seasons_resp is not None:
            self.seasons_data = {s["id"]: s["year"] for s in seasons_resp}
        else:
            show_error("Erro", "Resposta inesperada para temporadas.")

        teams_resp = self.api_client.get_teams()
        if isinstance(teams_resp, dict) and "error" in teams_resp:
            show_error("Erro", teams_resp.get("error", "Falha ao carregar equipes para seleção."))
        elif teams_resp is not None:
            self.teams_data = {t["id"]: t["name"] for t in teams_resp}
        else:
            show_error("Erro", "Resposta inesperada para equipes.")

        drivers_resp = self.api_client.get_drivers()
        if isinstance(drivers_resp, dict) and "error" in drivers_resp:
            show_error("Erro", drivers_resp.get("error", "Falha ao carregar pilotos para seleção."))
        elif drivers_resp is not None:
            self.drivers_data = {d["id"]: d["full_name"] for d in drivers_resp}
        else:
            show_error("Erro", "Resposta inesperada para pilotos.")

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Adicionar Novo Contrato de Piloto")
        header.pack(fill="x", pady=(0, 10))

        form_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        form_frame.pack(pady=10, padx=20, fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        self.season_combobox = LabeledCombobox(form_frame, "Temporada:", self.seasons_data)
        self.season_combobox.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        self.team_combobox = LabeledCombobox(form_frame, "Equipe:", self.teams_data)
        self.team_combobox.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.driver_combobox = LabeledCombobox(form_frame, "Piloto:", self.drivers_data)
        self.driver_combobox.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)

        self.number_spinbox = LabeledSpinbox(form_frame, "Número do Carro (1-99):", from_=1, to=99)
        self.number_spinbox.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        self.salary_entry = LabeledEntry(form_frame, "Salário (MUSD, opcional):")
        self.salary_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Salvar", command=self.save_contract, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancelar", command=lambda: self.controller.show_frame("ContractListView"), style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

    def save_contract(self):
        season_id = self.season_combobox.get_id()
        team_id = self.team_combobox.get_id()
        driver_id = self.driver_combobox.get_id()

        if season_id is None or team_id is None or driver_id is None:
            show_warning("Erro de Entrada", "Por favor, selecione uma Temporada, Equipe e Piloto válidos.")
            return

        data = {
            "season_id": season_id,
            "team_id": team_id,
            "driver_id": driver_id,
            "number": self.number_spinbox.get(),
            "salary_musd": self.salary_entry.get() or None,
        }

        if data["salary_musd"]:
            try:
                data["salary_musd"] = float(data["salary_musd"])
                if data["salary_musd"] < 0:
                    show_warning("Erro de Entrada", "O Salário deve ser positivo.")
                    return
            except ValueError:
                show_warning("Erro de Entrada", "O Salário deve ser um número.")
                return

        response = self.api_client.add_contract(data)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao adicionar contrato."))
        else:
            show_info("Sucesso", "Contrato adicionado com sucesso!")
            self.controller.show_frame("ContractListView")

class EditContractView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.contract_id = None
        self.seasons_data = {}
        self.teams_data = {}
        self.drivers_data = {}
        self._load_relations_data()
        self.create_widgets()

    def _load_relations_data(self):
        seasons_resp = self.api_client.get_seasons()
        if isinstance(seasons_resp, dict) and "error" in seasons_resp:
            show_error("Erro", seasons_resp.get("error", "Falha ao carregar temporadas para exibição."))
        elif seasons_resp is not None:
            self.seasons_data = {s["id"]: s["year"] for s in seasons_resp}
        else:
            show_error("Erro", "Resposta inesperada para temporadas.")

        teams_resp = self.api_client.get_teams()
        if isinstance(teams_resp, dict) and "error" in teams_resp:
            show_error("Erro", teams_resp.get("error", "Falha ao carregar equipes para exibição."))
        elif teams_resp is not None:
            self.teams_data = {t["id"]: t["name"] for t in teams_resp}
        else:
            show_error("Erro", "Resposta inesperada para equipes.")

        drivers_resp = self.api_client.get_drivers()
        if isinstance(drivers_resp, dict) and "error" in drivers_resp:
            show_error("Erro", drivers_resp.get("error", "Falha ao carregar pilotos para exibição."))
        elif drivers_resp is not None:
            self.drivers_data = {d["id"]: d["full_name"] for d in drivers_resp}
        else:
            show_error("Erro", "Resposta inesperada para pilotos.")

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Editar Contrato de Piloto")
        header.pack(fill="x", pady=(0, 10))

        form_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        form_frame.pack(pady=10, padx=20, fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        self.season_display = LabeledEntry(form_frame, "Temporada (Imutável):", readonly=True)
        self.season_display.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)

        self.team_display = LabeledEntry(form_frame, "Equipe (Imutável):", readonly=True)
        self.team_display.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)

        self.driver_display = LabeledEntry(form_frame, "Piloto (Imutável):", readonly=True)
        self.driver_display.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)

        self.number_spinbox = LabeledSpinbox(form_frame, "Número do Carro (1-99):", from_=1, to=99)
        self.number_spinbox.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        self.salary_entry = LabeledEntry(form_frame, "Salário (MUSD, opcional):")
        self.salary_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Salvar Alterações", command=self.save_changes, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancelar", command=lambda: self.controller.show_frame("ContractListView"), style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

    def load_contract_data(self, contract_id):
        self.contract_id = contract_id
        response = self.api_client.get_contract(contract_id)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao carregar dados do contrato."))
            self.controller.show_frame("ContractListView")
        elif response is not None:
            self.season_display.set(self.seasons_data.get(response.get("season_id"), "N/A"))
            self.team_display.set(self.teams_data.get(response.get("team_id"), "N/A"))
            self.driver_display.set(self.drivers_data.get(response.get("driver_id"), "N/A"))

            self.number_spinbox.set(response.get("number", ""))
            self.salary_entry.set(response.get("salary_musd", "") or "")
        else:
            show_error("Erro", "Resposta inesperada ao carregar dados do contrato.")

    def save_changes(self):
        data = {
            "number": self.number_spinbox.get(),
            "salary_musd": self.salary_entry.get() or None,
        }

        if data["salary_musd"]:
            try:
                data["salary_musd"] = float(data["salary_musd"])
                if data["salary_musd"] < 0:
                    show_warning("Erro de Entrada", "O Salário deve ser positivo.")
                    return
            except ValueError:
                show_warning("Erro de Entrada", "O Salário deve ser um número.")
                return

        response = self.api_client.update_contract(self.contract_id, data)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao atualizar contrato."))
        else:
            show_info("Sucesso", "Contrato atualizado com sucesso!")
            self.controller.show_frame("ContractListView")