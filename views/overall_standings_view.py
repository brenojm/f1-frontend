import tkinter as tk
from tkinter import ttk
import threading

from api_client import ApiClient
from ui_elements import LabeledCombobox, show_error, \
    COLOR_PRIMARY_ACCENT, COLOR_BACKGROUND_DARK, COLOR_FOREGROUND_LIGHT, \
    COLOR_SUCCESS_ACCENT, COLOR_BACKGROUND_MEDIUM, COLOR_BACKGROUND_LIGHT, AppHeaderFrame

class OverallStandingsView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.seasons_data = {} # {id: year}
        self.selected_season_id = None
        self.driver_standings_data = []
        self.team_standings_data = []

        self.create_widgets()
        
    def on_show(self, season_id=None, **kwargs):
        """Carrega as temporadas e, em seguida, as classificações."""
        # Limpa as treeviews antes de carregar novos dados
        for item in self.driver_tree.get_children(): self.driver_tree.delete(item)
        for item in self.team_tree.get_children(): self.team_tree.delete(item)
        
        # Armazena o season_id passado (se houver) como a 'sugestão' inicial de seleção
        self.selected_season_id = season_id 
        
        # Inicia o carregamento das temporadas de forma assíncrona
        self._load_seasons_for_dropdown() 

    def _load_seasons_for_dropdown(self):
        """Inicia o carregamento assíncrono das temporadas para o combobox."""
        self.show_loading_indicator("Carregando temporadas...")
        # Esconde o combobox de temporadas enquanto carrega
        if hasattr(self, 'season_combobox_container'):
            self.season_combobox_container.pack_forget()
        self.season_combobox_placeholder.pack(side=tk.LEFT, padx=10) # Mostra o placeholder

        threading.Thread(target=self._fetch_seasons_async, daemon=True).start()

    def _fetch_seasons_async(self):
        """Busca as temporadas da API em uma thread separada."""
        seasons_resp = self.api_client.get_seasons()
        self.after(0, lambda: self._handle_seasons_response(seasons_resp))

    def _handle_seasons_response(self, seasons_resp):
        """Processa a resposta das temporadas e atualiza o combobox na thread principal."""
        self.hide_loading_indicator() # Esconde o indicador de carregamento de classificações

        # Esconde o placeholder da combobox
        self.season_combobox_placeholder.pack_forget()

        # Se o combobox de temporadas já existe, destrua-o para recriar
        if hasattr(self, 'season_combobox') and self.season_combobox is not None:
            self.season_combobox.destroy()
            self.season_combobox = None # Garante que a referência seja limpa

        if isinstance(seasons_resp, list):
            sorted_seasons = sorted(seasons_resp, key=lambda s: s["year"], reverse=True)
            self.seasons_data = {s["id"]: s["year"] for s in sorted_seasons}

            if self.seasons_data:
                # 1. Crie uma NOVA instância do LabeledCombobox com as opções corretas
                self.season_combobox = LabeledCombobox(self.season_selector_frame, "Selecionar Temporada:", self.seasons_data)
                self.season_combobox.pack(side=tk.LEFT, padx=10)
                self.season_combobox.combobox.bind("<<ComboboxSelected>>", self._on_season_selected)
                
                # 2. Defina a temporada a ser selecionada:
                #    Se nenhuma foi pre-selecionada via on_show ou a pre-selecionada não é válida,
                #    define a mais recente (primeira no sorted_seasons) como padrão.
                if self.selected_season_id is None or self.selected_season_id not in self.seasons_data:
                    self.selected_season_id = list(self.seasons_data.keys())[0]
                
                # 3. Defina a seleção no combobox usando o ID
                self.season_combobox.set_by_id(self.selected_season_id)
                
                # 4. Carregue as classificações para a temporada selecionada
                # A carga deve acontecer sempre que a combobox de temporadas for populada
                # para garantir que os dados iniciais apareçam.
                self.load_standings() 
                
            else:
                self.selected_season_id = None
                # Se não houver dados, o combobox não é criado, apenas o placeholder permanece
                self.season_combobox = None # Garante que não haja referência a um combobox que não será criado
                self.driver_tree.insert("", tk.END, values=("", "Nenhuma temporada disponível", ""))
                self.team_tree.insert("", tk.END, values=("", "Nenhuma temporada disponível", ""))

        else:
            show_error("Erro", seasons_resp.get("error", "Falha ao carregar temporadas para seleção."))
            self.seasons_data = {}
            self.selected_season_id = None
            self.season_combobox = None # Garante que não haja referência
            self.driver_tree.insert("", tk.END, values=("", "Erro ao carregar temporadas", ""))
            self.team_tree.insert("", tk.END, values=("", "Erro ao carregar temporadas", ""))


    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Classificações Gerais por Temporada")
        header.pack(fill="x", pady=(0, 20))

        self.season_selector_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        self.season_selector_frame.pack(pady=10)
        
        # Placeholder para o LabeledCombobox enquanto carrega as temporadas
        self.season_combobox_placeholder = ttk.Label(self.season_selector_frame, text="Carregando seletor de temporada...",
                                                      background=COLOR_BACKGROUND_DARK, foreground=COLOR_FOREGROUND_LIGHT)
        # Não empacote ele aqui, será feito em _load_seasons_for_dropdown

        # O LabeledCombobox será criado dinamicamente em _handle_seasons_response
        self.season_combobox = None 

        ttk.Button(self.season_selector_frame, text="Ver Classificações", # Use season_selector_frame como pai
                   command=self.load_standings, style="Accent.TButton").pack(side=tk.LEFT, padx=10)

        self.standings_container = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        self.standings_container.pack(pady=20, fill=tk.BOTH, expand=True)
        
        self.standings_loading_label = ttk.Label(self.standings_container, text="Carregando classificações...", 
                                                  background=COLOR_BACKGROUND_DARK, foreground=COLOR_FOREGROUND_LIGHT,
                                                  font=("Arial", 12, "bold"))
        self.standings_loading_label.pack_forget()

        self.standings_display_frame = tk.Frame(self.standings_container, bg=COLOR_BACKGROUND_DARK)
        self.standings_display_frame.grid_columnconfigure(0, weight=1)
        self.standings_display_frame.grid_columnconfigure(1, weight=1)
        self.standings_display_frame.grid_rowconfigure(0, weight=1)

        driver_frame = tk.Frame(self.standings_display_frame, bg=COLOR_BACKGROUND_MEDIUM, relief="solid", bd=1)
        driver_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        tk.Label(driver_frame, text="Classificação de Pilotos", font=("Arial", 14, "bold"),
                 bg=COLOR_BACKGROUND_MEDIUM, fg=COLOR_FOREGROUND_LIGHT).pack(pady=10)
        self.driver_tree = self._create_standings_tree(driver_frame, ("ID do Piloto", "Nome Completo", "Pontos"))
        self.driver_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        team_frame = tk.Frame(self.standings_display_frame, bg=COLOR_BACKGROUND_MEDIUM, relief="solid", bd=1)
        team_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        tk.Label(team_frame, text="Classificação de Equipes", font=("Arial", 14, "bold"),
                 bg=COLOR_BACKGROUND_MEDIUM, fg=COLOR_FOREGROUND_LIGHT).pack(pady=10)
        self.team_tree = self._create_standings_tree(team_frame, ("ID da Equipe", "Nome", "Pontos"))
        self.team_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        ttk.Button(self, text="Voltar à Tela Inicial", command=lambda: self.controller.show_frame("WelcomeView"),
                   style="Monochromatic.TButton").pack(pady=20)

    def _create_standings_tree(self, parent, columns):
        style = ttk.Style()
        tree = ttk.Treeview(parent, columns=columns, show="headings", style="Treeview.Dark")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor=tk.CENTER if "ID" in col or "Pontos" in col else tk.W)
        return tree

    def _on_season_selected(self, event=None):
        # AQUI NÃO PRECISAMOS DE COMPARAÇÃO COM self.selected_season_id
        # Porque o combobox SEMPRE que for alterado manualmente, deve recarregar.
        # Apenas garante que self.selected_season_id esteja atualizado com a seleção do combobox.
        new_selected_id = self.season_combobox.get_id()
        self.selected_season_id = new_selected_id 
        self.load_standings()

    def load_standings(self):
        if self.selected_season_id is None:
            self.standings_loading_label.pack_forget()
            self.standings_display_frame.pack_forget()

            for item in self.driver_tree.get_children(): self.driver_tree.delete(item)
            for item in self.team_tree.get_children(): self.team_tree.delete(item)
            self.driver_tree.insert("", tk.END, values=("", "Selecione uma temporada", ""))
            self.team_tree.insert("", tk.END, values=("", "Selecione uma temporada", ""))
            self.standings_display_frame.pack(fill=tk.BOTH, expand=True)
            return

        self.standings_display_frame.pack_forget()
        self.standings_loading_label.pack(pady=10)
        
        threading.Thread(target=self._fetch_standings_async, 
                         args=(self.selected_season_id,), daemon=True).start()

    def _fetch_standings_async(self, season_id):
        driver_standings_resp = self.api_client.get_driver_standings(season_id)
        team_standings_resp = self.api_client.get_team_standings(season_id)
        
        self.after(0, lambda: self._handle_standings_response(driver_standings_resp, team_standings_resp))

    def _handle_standings_response(self, driver_standings_resp, team_standings_resp):
        self.standings_loading_label.pack_forget()
        self.standings_display_frame.pack(fill=tk.BOTH, expand=True)

        for item in self.driver_tree.get_children(): self.driver_tree.delete(item)
        for item in self.team_tree.get_children(): self.team_tree.delete(item)

        if isinstance(driver_standings_resp, dict) and "error" in driver_standings_resp:
            show_error("Erro", driver_standings_resp.get("error", "Falha ao carregar classificações de pilotos."))
            self.driver_tree.insert("", tk.END, values=("", "Erro ao carregar classificações de pilotos", ""))
        elif driver_standings_resp is not None:
            if not driver_standings_resp:
                self.driver_tree.insert("", tk.END, values=("", "Nenhuma classificação de piloto encontrada para esta temporada", ""))
            for standing in driver_standings_resp:
                self.driver_tree.insert("", tk.END, values=(
                    standing.get("driver_id"),
                    standing.get("full_name"),
                    standing.get("points")
                ))
        else:
            show_error("Erro", "Resposta inesperada para classificações de pilotos.")
            self.driver_tree.insert("", tk.END, values=("", "Resposta inesperada da API para pilotos", ""))

        if isinstance(team_standings_resp, dict) and "error" in team_standings_resp:
            show_error("Erro", team_standings_resp.get("error", "Falha ao carregar classificações de equipes."))
            self.team_tree.insert("", tk.END, values=("", "Erro ao carregar classificações de equipes", ""))
        elif team_standings_resp is not None:
            if not team_standings_resp:
                self.team_tree.insert("", tk.END, values=("", "Nenhuma classificação de equipe encontrada para esta temporada", ""))
            for standing in team_standings_resp:
                self.team_tree.insert("", tk.END, values=(
                    standing.get("team_id"),
                    standing.get("name"),
                    standing.get("points")
                ))
        else:
            show_error("Erro", "Resposta inesperada para classificações de equipes.")
            self.team_tree.insert("", tk.END, values=("", "Resposta inesperada da API para equipes", ""))

    def show_loading_indicator(self, message="Carregando..."):
        self.standings_loading_label.config(text=message)
        self.standings_loading_label.pack(pady=10)
        self.standings_display_frame.pack_forget()

    def hide_loading_indicator(self):
        self.standings_loading_label.pack_forget()