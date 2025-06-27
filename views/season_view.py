import tkinter as tk
from tkinter import ttk, messagebox
import threading # Importar o módulo threading

from api_client import ApiClient
from ui_elements import LabeledEntry, show_info, show_error, show_warning, ask_yes_no, \
    COLOR_PRIMARY_ACCENT, COLOR_SUCCESS_ACCENT, COLOR_BACKGROUND_DARK, COLOR_FOREGROUND_LIGHT, \
    COLOR_BUTTON_TEXT, COLOR_BACKGROUND_MEDIUM, COLOR_FOREGROUND_DARK, COLOR_BACKGROUND_LIGHT, \
    format_date_display, format_date_api, AppHeaderFrame


class SeasonListView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.seasons = []

        self.create_widgets()
        # REMOVIDO: A chamada inicial da API foi movida para on_show()
        # self.load_seasons()

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Lista de Temporadas")
        header.pack(fill="x", pady=(0, 10))

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Adicionar Nova Temporada", command=self.add_season, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        # O botão "Atualizar Lista" agora chamará o método que inicia o carregamento assíncrono
        ttk.Button(button_frame, text="Atualizar Lista", command=self.load_seasons, style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)
        
        # Container para o indicador de carregamento e o Treeview
        self.content_container = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        self.content_container.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Indicador de Carregamento
        self.loading_label = ttk.Label(self.content_container, text="Carregando temporadas...", 
                                       background=COLOR_BACKGROUND_DARK, foreground=COLOR_FOREGROUND_LIGHT,
                                       font=("Arial", 12, "bold"))
        
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background=COLOR_BACKGROUND_LIGHT, foreground=COLOR_FOREGROUND_LIGHT)
        style.configure("Treeview", font=("Arial", 10), rowheight=28, background=COLOR_BACKGROUND_MEDIUM, foreground=COLOR_FOREGROUND_LIGHT, fieldbackground=COLOR_BACKGROUND_MEDIUM)
        style.map('Treeview', background=[('selected', COLOR_PRIMARY_ACCENT)], foreground=[('selected', 'white')])

        self.tree = ttk.Treeview(self.content_container, columns=("ID", "Ano", "Data Início", "Descrição"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Ano", text="Ano")
        self.tree.heading("Data Início", text="Data Início")
        self.tree.heading("Descrição", text="Descrição")

        self.tree.column("ID", width=50, anchor=tk.CENTER)
        self.tree.column("Ano", width=80, anchor=tk.CENTER)
        self.tree.column("Data Início", width=120, anchor=tk.CENTER)
        self.tree.column("Descrição", width=300)

        # self.tree será empacotado/desempacotado dinamicamente
        self.tree.bind("<Double-1>", self.on_double_click)

        action_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        action_frame.pack(pady=10)
        ttk.Button(action_frame, text="Editar Selecionado", command=self.edit_season, style="Accent.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="Excluir Selecionado", command=self.delete_season, style="Delete.TButton").pack(side=tk.LEFT, padx=10)

        ttk.Button(self, text="Voltar à Tela Inicial", command=lambda: self.controller.show_frame("WelcomeView"), 
                   style="Monochromatic.TButton").pack(pady=20)

    # NOVO: Método chamado pelo Controller quando esta tela é exibida
    def on_show(self, **kwargs):
        """Carrega os dados das temporadas quando a SeasonListView é exibida."""
        self.load_seasons()

    # ATUALIZADO: Este método agora inicia o carregamento em uma thread separada
    def load_seasons(self):
        # 1. Esconde o treeview e mostra o indicador de carregamento
        self.tree.pack_forget()
        self.loading_label.pack(pady=10)
        
        # 2. Inicia a operação da API em uma nova thread
        threading.Thread(target=self._fetch_seasons_async, daemon=True).start()

    def _fetch_seasons_async(self):
        """Método para buscar as temporadas da API em uma thread separada."""
        response = self.api_client.get_seasons()
        # 3. Usa self.after para agendar a atualização da UI na thread principal do Tkinter
        self.after(0, lambda: self._handle_seasons_response(response))

    def _handle_seasons_response(self, response):
        """Método para processar a resposta da API e atualizar a UI na thread principal."""
        # 4. Esconde o indicador de carregamento
        self.loading_label.pack_forget()

        # 5. Limpa o treeview antes de popular com novos dados
        for item in self.tree.get_children():
            self.tree.delete(item)

        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao carregar temporadas."))
        elif response is not None:
            self.seasons = response
            for season in self.seasons:
                start_date_display = format_date_display(season.get("start_date", ""))
                self.tree.insert("", tk.END, values=(
                    season.get("id"),
                    season.get("year"),
                    start_date_display,
                    season.get("description")
                ))
            # 6. Empacota o treeview de volta após carregar os dados
            self.tree.pack(fill=tk.BOTH, expand=True)
        else:
            show_error("Erro", "Resposta inesperada da API.")

    def add_season(self):
        self.controller.show_frame("AddSeasonView")

    def edit_season(self):
        selected_item = self.tree.focus()
        if not selected_item:
            show_warning("Nenhuma Seleção", "Por favor, selecione uma temporada para editar.")
            return

        season_id = self.tree.item(selected_item, "values")[0]
        self.controller.show_frame("EditSeasonView", season_id=season_id)

    def delete_season(self):
        selected_item = self.tree.focus()
        if not selected_item:
            show_warning("Nenhuma Seleção", "Por favor, selecione uma temporada para excluir.")
            return

        season_id = self.tree.item(selected_item, "values")[0]
        if ask_yes_no("Confirmar Exclusão", f"Tem certeza que deseja excluir a temporada ID {season_id}?"):
            response = self.api_client.delete_season(season_id)
            if response is True:
                show_info("Sucesso", "Temporada excluída com sucesso!")
                self.load_seasons() # Recarrega a lista após exclusão
            else:
                show_error("Erro", response.get("error", "Falha ao excluir temporada."))

    def on_double_click(self, event):
        self.edit_season()


class AddSeasonView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.create_widgets()

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Adicionar Nova Temporada")
        header.pack(fill="x", pady=(0, 10))

        form_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        form_frame.pack(pady=10, padx=20, fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        self.year_entry = LabeledEntry(form_frame, "Ano:")
        self.year_entry.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        self.start_date_entry = LabeledEntry(form_frame, "Data de Início (DD/MM/AAAA):")
        self.start_date_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.description_entry = LabeledEntry(form_frame, "Descrição (opcional):")
        self.description_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Salvar", command=self.save_season, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancelar", command=lambda: self.controller.show_frame("SeasonListView"), style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)
    
    # NOVO: Método on_show para limpar campos ao exibir
    def on_show(self, **kwargs):
        """Limpa os campos do formulário quando a AddSeasonView é exibida."""
        self.year_entry.set("")
        self.start_date_entry.set("")
        self.description_entry.set("")

    def save_season(self):
        start_date_input = self.start_date_entry.get()
        start_date_api_format = format_date_api(start_date_input)

        data = {
            "year": self.year_entry.get(),
            "start_date": start_date_api_format,
            "description": self.description_entry.get() or None,
        }

        if not data["year"]:
            show_warning("Erro de Entrada", "O Ano é obrigatório.")
            return
        if not start_date_input:
            show_warning("Erro de Entrada", "A Data de Início é obrigatória.")
            return

        try:
            data["year"] = int(data["year"])
            if data["year"] < 1950:
                show_warning("Erro de Entrada", "O Ano deve ser 1950 ou maior.")
                return
        except ValueError:
            show_warning("Erro de Entrada", "O Ano deve ser um número inteiro.")
            return

        # Validação da data
        if start_date_input and start_date_api_format is None: 
            show_warning("Erro de Entrada", "A Data de Início deve estar no formato DD/MM/AAAA.")
            return

        response = self.api_client.add_season(data)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao adicionar temporada."))
        else:
            show_info("Sucesso", "Temporada adicionada com sucesso!")
            self.controller.show_frame("SeasonListView")

class EditSeasonView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.season_id = None
        self.create_widgets()

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Editar Temporada")
        header.pack(fill="x", pady=(0, 10))

        form_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        form_frame.pack(pady=10, padx=20, fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        self.year_entry = LabeledEntry(form_frame, "Ano:")
        self.year_entry.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        self.start_date_entry = LabeledEntry(form_frame, "Data de Início (DD/MM/AAAA):")
        self.start_date_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.description_entry = LabeledEntry(form_frame, "Descrição (opcional):")
        self.description_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Salvar Alterações", command=self.save_changes, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancelar", command=lambda: self.controller.show_frame("SeasonListView"), style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

    # NOVO: Método on_show para carregar dados de edição
    def on_show(self, season_id=None, **kwargs):
        """Carrega os dados da temporada para edição quando a EditSeasonView é exibida."""
        if season_id:
            self.load_season_data(season_id)
        else:
            show_error("Erro", "ID da temporada não fornecido para edição.")
            self.controller.show_frame("SeasonListView") # Volta para a lista se não houver ID

    def load_season_data(self, season_id):
        self.season_id = season_id
        response = self.api_client.get_season(season_id)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao carregar dados da temporada."))
            self.controller.show_frame("SeasonListView")
        elif response is not None:
            self.year_entry.set(str(response.get("year", ""))) # Garante que seja string
            start_date_display_format = format_date_display(response.get("start_date", ""))
            self.start_date_entry.set(start_date_display_format)
            self.description_entry.set(response.get("description", "") or "")
        else:
            show_error("Erro", "Resposta inesperada ao carregar dados da temporada.")
            self.controller.show_frame("SeasonListView")

    def save_changes(self):
        start_date_input = self.start_date_entry.get()
        start_date_api_format = format_date_api(start_date_input)

        data = {
            "year": self.year_entry.get(),
            "start_date": start_date_api_format,
            "description": self.description_entry.get() or None,
        }

        if not data["year"]:
            show_warning("Erro de Entrada", "O Ano é obrigatório.")
            return
        if not start_date_input:
            show_warning("Erro de Entrada", "A Data de Início é obrigatória.")
            return

        try:
            data["year"] = int(data["year"])
            if data["year"] < 1950:
                show_warning("Erro de Entrada", "O Ano deve ser 1950 ou maior.")
                return
        except ValueError:
            show_warning("Erro de Entrada", "O Ano deve ser um número inteiro.")
            return

        # Validação da data
        if start_date_input and start_date_api_format is None:
            show_warning("Erro de Entrada", "A Data de Início deve estar no formato DD/MM/AAAA.")
            return

        response = self.api_client.update_season(self.season_id, data)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao atualizar temporada."))
        else:
            show_info("Sucesso", "Temporada atualizada com sucesso!")
            self.controller.show_frame("SeasonListView")

class DriverStandingsView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.season_id = None
        self.create_widgets()
        # REMOVIDO: Carregamento do __init__
        # self.load_standings_data(self.season_id)

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Classificação de Pilotos")
        header.pack(fill="x", pady=(0, 10))

        # Container para o indicador de carregamento e o Treeview
        self.content_container = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        self.content_container.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Indicador de Carregamento
        self.loading_label = ttk.Label(self.content_container, text="Carregando classificação de pilotos...", 
                                       background=COLOR_BACKGROUND_DARK, foreground=COLOR_FOREGROUND_LIGHT,
                                       font=("Arial", 12, "bold"))
        
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background=COLOR_BACKGROUND_LIGHT, foreground=COLOR_FOREGROUND_LIGHT)
        style.configure("Treeview", font=("Arial", 10), rowheight=28, background=COLOR_BACKGROUND_MEDIUM, foreground=COLOR_FOREGROUND_LIGHT, fieldbackground=COLOR_BACKGROUND_MEDIUM)
        style.map('Treeview', background=[('selected', COLOR_PRIMARY_ACCENT)], foreground=[('selected', 'white')])

        self.tree = ttk.Treeview(self.content_container, columns=("ID do Piloto", "Nome Completo", "Pontos"), show="headings")
        self.tree.heading("ID do Piloto", text="ID do Piloto")
        self.tree.heading("Nome Completo", text="Nome Completo")
        self.tree.heading("Pontos", text="Pontos")

        self.tree.column("ID do Piloto", width=80, anchor=tk.CENTER)
        self.tree.column("Nome Completo", width=200)
        self.tree.column("Pontos", width=100, anchor=tk.CENTER)

        # self.tree será empacotado/desempacotado dinamicamente

        ttk.Button(self, text="Voltar às Temporadas", command=lambda: self.controller.show_frame("SeasonListView"), style="Monochromatic.TButton").pack(pady=20)

    # NOVO: Método on_show para carregar dados
    def on_show(self, season_id=None, **kwargs):
        """Carrega a classificação de pilotos para a temporada especificada."""
        if season_id:
            self.season_id = season_id
            self.load_standings_data() # Inicia o carregamento assíncrono
        else:
            show_error("Erro", "ID da temporada não fornecido para classificação de pilotos.")
            self.controller.show_frame("SeasonListView") # Volta para a lista de temporadas

    # ATUALIZADO: load_standings_data agora coordena o carregamento assíncrono
    def load_standings_data(self):
        if self.season_id is None:
            # Garante que o indicador esteja escondido e a treeview limpa
            self.loading_label.pack_forget()
            self.tree.pack_forget()
            for item in self.tree.get_children(): self.tree.delete(item)
            self.tree.insert("", tk.END, values=("", "Nenhuma temporada selecionada", ""))
            self.tree.pack(fill=tk.BOTH, expand=True) # Re-pack para mostrar a mensagem
            return

        # 1. Esconde o treeview e mostra o indicador de carregamento
        self.tree.pack_forget()
        self.loading_label.pack(pady=10)
        
        # 2. Inicia a operação da API em uma nova thread
        threading.Thread(target=self._fetch_driver_standings_async, 
                         args=(self.season_id,), daemon=True).start()

    def _fetch_driver_standings_async(self, season_id):
        """Busca a classificação de pilotos da API em uma thread separada."""
        response = self.api_client.get_driver_standings(season_id)
        # 3. Usa self.after para agendar a atualização da UI na thread principal do Tkinter
        self.after(0, lambda: self._handle_driver_standings_response(response))

    def _handle_driver_standings_response(self, response):
        """Método para processar a resposta da API e atualizar a UI na thread principal."""
        # 4. Esconde o indicador de carregamento
        self.loading_label.pack_forget()

        # 5. Limpa o treeview antes de popular com novos dados
        for item in self.tree.get_children():
            self.tree.delete(item)

        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", f"Falha ao carregar classificações de pilotos para a temporada {self.season_id}."))
            self.tree.insert("", tk.END, values=("", "Erro ao carregar classificações", ""))
        elif response is not None:
            if not response: # Se não houver dados, exibe uma mensagem
                self.tree.insert("", tk.END, values=("", "Nenhuma classificação de piloto encontrada para esta temporada", ""))
            for standing in response:
                self.tree.insert("", tk.END, values=(
                    standing.get("driver_id"),
                    standing.get("full_name"),
                    standing.get("points")
                ))
            # 6. Empacota o treeview de volta após carregar os dados
            self.tree.pack(fill=tk.BOTH, expand=True)
        else:
            show_error("Erro", "Resposta inesperada para classificações de pilotos.")
            self.tree.insert("", tk.END, values=("", "Resposta inesperada da API", ""))

class TeamStandingsView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.season_id = None
        self.create_widgets()
        # REMOVIDO: Carregamento do __init__
        # self.load_standings_data(self.season_id)

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Classificação de Equipes")
        header.pack(fill="x", pady=(0, 10))

        # Container para o indicador de carregamento e o Treeview
        self.content_container = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        self.content_container.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Indicador de Carregamento
        self.loading_label = ttk.Label(self.content_container, text="Carregando classificação de equipes...", 
                                       background=COLOR_BACKGROUND_DARK, foreground=COLOR_FOREGROUND_LIGHT,
                                       font=("Arial", 12, "bold"))
        
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background=COLOR_BACKGROUND_LIGHT, foreground=COLOR_FOREGROUND_LIGHT)
        style.configure("Treeview", font=("Arial", 10), rowheight=28, background=COLOR_BACKGROUND_MEDIUM, foreground=COLOR_FOREGROUND_LIGHT, fieldbackground=COLOR_BACKGROUND_MEDIUM)
        style.map('Treeview', background=[('selected', COLOR_PRIMARY_ACCENT)], foreground=[('selected', 'white')])

        self.tree = ttk.Treeview(self.content_container, columns=("ID da Equipe", "Nome", "Pontos"), show="headings")
        self.tree.heading("ID da Equipe", text="ID da Equipe")
        self.tree.heading("Nome", text="Nome")
        self.tree.heading("Pontos", text="Pontos")

        self.tree.column("ID da Equipe", width=80, anchor=tk.CENTER)
        self.tree.column("Nome", width=200)
        self.tree.column("Pontos", width=100, anchor=tk.CENTER)

        # self.tree será empacotado/desempacotado dinamicamente

        ttk.Button(self, text="Voltar às Temporadas", command=lambda: self.controller.show_frame("SeasonListView"), style="Monochromatic.TButton").pack(pady=20)

    # NOVO: Método on_show para carregar dados
    def on_show(self, season_id=None, **kwargs):
        """Carrega a classificação de equipes para a temporada especificada."""
        if season_id:
            self.season_id = season_id
            self.load_standings_data() # Inicia o carregamento assíncrono
        else:
            show_error("Erro", "ID da temporada não fornecido para classificação de equipes.")
            self.controller.show_frame("SeasonListView") # Volta para a lista de temporadas

    # ATUALIZADO: load_standings_data agora coordena o carregamento assíncrono
    def load_standings_data(self):
        if self.season_id is None:
            # Garante que o indicador esteja escondido e a treeview limpa
            self.loading_label.pack_forget()
            self.tree.pack_forget()
            for item in self.tree.get_children(): self.tree.delete(item)
            self.tree.insert("", tk.END, values=("", "Nenhuma temporada selecionada", ""))
            self.tree.pack(fill=tk.BOTH, expand=True) # Re-pack para mostrar a mensagem
            return

        # 1. Esconde o treeview e mostra o indicador de carregamento
        self.tree.pack_forget()
        self.loading_label.pack(pady=10)
        
        # 2. Inicia a operação da API em uma nova thread
        threading.Thread(target=self._fetch_team_standings_async, 
                         args=(self.season_id,), daemon=True).start()

    def _fetch_team_standings_async(self, season_id):
        """Busca a classificação de equipes da API em uma thread separada."""
        response = self.api_client.get_team_standings(season_id)
        # 3. Usa self.after para agendar a atualização da UI na thread principal do Tkinter
        self.after(0, lambda: self._handle_team_standings_response(response))

    def _handle_team_standings_response(self, response):
        """Método para processar a resposta da API e atualizar a UI na thread principal."""
        # 4. Esconde o indicador de carregamento
        self.loading_label.pack_forget()

        # 5. Limpa o treeview antes de popular com novos dados
        for item in self.tree.get_children():
            self.tree.delete(item)

        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", f"Falha ao carregar classificações de equipes para a temporada {self.season_id}."))
            self.tree.insert("", tk.END, values=("", "Erro ao carregar classificações", ""))
        elif response is not None:
            if not response: # Se não houver dados, exibe uma mensagem
                self.tree.insert("", tk.END, values=("", "Nenhuma classificação de equipe encontrada para esta temporada", ""))
            for standing in response:
                self.tree.insert("", tk.END, values=(
                    standing.get("team_id"),
                    standing.get("name"),
                    standing.get("points")
                ))
            # 6. Empacota o treeview de volta após carregar os dados
            self.tree.pack(fill=tk.BOTH, expand=True)
        else:
            show_error("Erro", "Resposta inesperada para classificações de equipes.")
            self.tree.insert("", tk.END, values=("", "Resposta inesperada da API", ""))