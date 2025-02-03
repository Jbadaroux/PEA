import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from dataclasses import dataclass, field
from typing import List, Optional

# --- Simulation et modélisation ---

@dataclass
class SimulationResult:
    capital_final_brut: float      # Capital final net après impôts
    net_investi: float             # Somme totale investie
    mois_plafond: Optional[int]    # Mois où le plafond a été atteint (None si jamais)
    historique: List[float] = field(default_factory=list)  # Évolution mensuelle du capital

def simulate_pea(
    duree_annees: float,
    taux_annuel_percent: float,
    capital_initial: float,
    versement_mensuel: float,
    plafond_pea: float,
    frais_annuels_percent: float = 0.0,
    taux_impot_percent: float = 17.2,
    inflation_percent: float = 0.0,
) -> SimulationResult:
    """
    Simule un investissement mensuel sur un PEA en tenant compte du plafond, des frais, de l'inflation et de la fiscalité.
    Le taux effectif est corrigé par l'inflation.
    Retourne un objet SimulationResult contenant notamment l'historique mensuel.
    """
    nb_mois = int(duree_annees * 12)
    # Calcul du taux mensuel effectif après correction d'inflation
    r_m = ((taux_annuel_percent - inflation_percent) / 100) / 12
    # Les frais annuels sont appliqués mensuellement (en fraction)
    frais_mensuel = (frais_annuels_percent / 100) / 12

    capital = 0.0
    net_investi = 0.0
    mois_plafond = None
    leftover = plafond_pea
    historique = []

    # Dépôt initial (ou partiel si nécessaire pour respecter le plafond)
    if leftover > 0:
        deposit_init = min(capital_initial, leftover)
        capital += deposit_init
        net_investi += deposit_init
        leftover -= deposit_init
        if leftover <= 1e-9:
            mois_plafond = 0
    historique.append(capital)

    # Boucle mensuelle
    for mois in range(1, nb_mois + 1):
        # 1) Capitalisation mensuelle
        capital *= (1 + r_m)
        # 2) Application des frais mensuels sur le capital
        if frais_mensuel > 0:
            capital *= (1 - frais_mensuel)
        # 3) Versement mensuel (si le plafond n'est pas atteint)
        if leftover > 1e-9:
            deposit = min(versement_mensuel, leftover)
            capital += deposit
            net_investi += deposit
            leftover -= deposit
            if leftover <= 1e-9 and mois_plafond is None:
                mois_plafond = mois
        historique.append(capital)

    # Calcul de l'impôt sur les gains (appliqué sur les intérêts bruts)
    interets_bruts = max(capital - net_investi, 0.0)
    impots = (taux_impot_percent / 100.0) * interets_bruts
    capital_net = capital - impots

    return SimulationResult(
        capital_final_brut=capital_net,
        net_investi=net_investi,
        mois_plafond=mois_plafond,
        historique=historique
    )

def format_duree_mois(nb_mois: int) -> str:
    """Formate un nombre de mois en chaîne du type 'X ans et Y mois'."""
    annees = nb_mois // 12
    mois = nb_mois % 12
    if annees == 0:
        return f"{mois} mois"
    elif annees == 1:
        return f"1 an{' et ' + str(mois) + ' mois' if mois else ''}"
    else:
        return f"{annees} ans{' et ' + str(mois) + ' mois' if mois else ''}"

def calcul_scenarios(
    duree_annees: float,
    capital_initial: float,
    versement_mensuel: float,
    plafond_pea: float,
    rates: List[float],
    frais: float = 0.0,
    inflation: float = 0.0,
    taux_impot: float = 17.2,
) -> (str, List[dict]):
    """
    Calcule et renvoie un rapport comparatif (texte) pour trois scénarios correspondant aux taux passés dans 'rates'.
    Le rapport présente côte à côte des indicateurs comme le capital final brut, les intérêts bruts, les impôts, etc.
    Retourne également la liste des données simulées (pour affichage graphique, par exemple).
    """
    if len(rates) != 3:
        return "ERREUR : Veuillez renseigner exactement 3 taux.", []
    scenarios_data = []
    for taux in rates:
        sim = simulate_pea(
            duree_annees, taux, capital_initial, versement_mensuel, plafond_pea,
            frais_annuels_percent=frais, inflation_percent=inflation, taux_impot_percent=taux_impot
        )
        interets_bruts = max(sim.historique[-1] - sim.net_investi, 0.0)
        duree_str = format_duree_mois(sim.mois_plafond) if sim.mois_plafond is not None else "non atteint"
        scenarios_data.append({
            "taux_str": f"{taux}%",
            "plafond_atteint": duree_str,
            "capital_final_brut": f"{sim.historique[-1]:,.2f} €",
            "interets_bruts": f"{interets_bruts:,.2f} €",
            "impots": f"{(taux_impot/100)*interets_bruts:,.2f} €",
            "capital_final_net": f"{sim.capital_final_brut:,.2f} €",
            "historique": sim.historique,
        })

    lines = []
    lines.append("=== COMPARATIF PEA (SIMULATION AVEC OPTIONS) : AFFICHAGE COLONNES ===")
    lines.append(f"- Durée max : {duree_annees} an(s)")
    lines.append(f"- Plafond PEA : {plafond_pea:,.2f} €")
    lines.append(f"- Capital initial : {capital_initial:,.2f} €")
    lines.append(f"- Versement mensuel : {versement_mensuel:,.2f} €")
    if frais:
        lines.append(f"- Frais annuels : {frais}%")
    if inflation:
        lines.append(f"- Inflation : {inflation}%")
    lines.append("")
    # En-tête des colonnes (une par taux)
    header = f"{'':<25}"
    for data in scenarios_data:
        header += f"{data['taux_str']:>18}"
    lines.append(header)
    # Les métriques à afficher
    metrics = [
        ("Plafond atteint", "plafond_atteint"),
        ("Capital final brut", "capital_final_brut"),
        ("Intérêts bruts", "interets_bruts"),
        ("Impôts", "impots"),
        ("Capital final net", "capital_final_net"),
    ]
    for (label, key) in metrics:
        row = f"{label:<25}"
        for data in scenarios_data:
            row += f"{data[key]:>18}"
        lines.append(row)
    rapport = "\n".join(lines)
    return rapport, scenarios_data

# --- Interface graphique avec tkinter et matplotlib ---

class PEASimulatorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulation PEA Mensuelle")
        self.geometry("900x700")
        self.create_widgets()

    def create_widgets(self):
        # Cadre pour les paramètres d'entrée
        frame_inputs = ttk.LabelFrame(self, text="Paramètres d'entrée")
        frame_inputs.pack(padx=10, pady=10, fill="x")

        # Durée (années)
        ttk.Label(frame_inputs, text="Durée (années) :").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.var_duree = tk.DoubleVar(value=10.0)
        ttk.Entry(frame_inputs, textvariable=self.var_duree).grid(row=0, column=1, padx=5, pady=5)

        # Capital initial
        ttk.Label(frame_inputs, text="Capital initial (€) :").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.var_capital = tk.DoubleVar(value=10000.0)
        ttk.Entry(frame_inputs, textvariable=self.var_capital).grid(row=1, column=1, padx=5, pady=5)

        # Versement mensuel
        ttk.Label(frame_inputs, text="Versement mensuel (€) :").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.var_versement = tk.DoubleVar(value=1000.0)
        ttk.Entry(frame_inputs, textvariable=self.var_versement).grid(row=2, column=1, padx=5, pady=5)

        # Plafond PEA (choix radio)
        ttk.Label(frame_inputs, text="Plafond PEA :").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.var_plafond = tk.DoubleVar(value=150000.0)
        frame_plafond = ttk.Frame(frame_inputs)
        frame_plafond.grid(row=3, column=1, padx=5, pady=5)
        ttk.Radiobutton(frame_plafond, text="150 000 € (personne seule)", variable=self.var_plafond, value=150000.0).pack(anchor="w")
        ttk.Radiobutton(frame_plafond, text="300 000 € (couple)", variable=self.var_plafond, value=300000.0).pack(anchor="w")

        # Trois taux annuels (une case par taux)
        ttk.Label(frame_inputs, text="Taux annuel 1 (%) :").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.var_rate1 = tk.DoubleVar(value=6.0)
        ttk.Entry(frame_inputs, textvariable=self.var_rate1).grid(row=4, column=1, padx=5, pady=5)
        ttk.Label(frame_inputs, text="Taux annuel 2 (%) :").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.var_rate2 = tk.DoubleVar(value=8.0)
        ttk.Entry(frame_inputs, textvariable=self.var_rate2).grid(row=5, column=1, padx=5, pady=5)
        ttk.Label(frame_inputs, text="Taux annuel 3 (%) :").grid(row=6, column=0, sticky="w", padx=5, pady=5)
        self.var_rate3 = tk.DoubleVar(value=10.0)
        ttk.Entry(frame_inputs, textvariable=self.var_rate3).grid(row=6, column=1, padx=5, pady=5)

        # Cadre pour les paramètres avancés
        frame_advanced = ttk.LabelFrame(self, text="Paramètres avancés")
        frame_advanced.pack(padx=10, pady=10, fill="x")
        ttk.Label(frame_advanced, text="Frais annuels (%) :").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.var_frais = tk.DoubleVar(value=0.0)
        ttk.Entry(frame_advanced, textvariable=self.var_frais).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(frame_advanced, text="Inflation (%) :").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.var_inflation = tk.DoubleVar(value=0.0)
        ttk.Entry(frame_advanced, textvariable=self.var_inflation).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(frame_advanced, text="Taux d'impôt (%) :").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.var_taux_impot = tk.DoubleVar(value=17.2)
        ttk.Entry(frame_advanced, textvariable=self.var_taux_impot).grid(row=2, column=1, padx=5, pady=5)

        # Bouton de lancement de la simulation
        self.btn_simulate = ttk.Button(self, text="Lancer la simulation", command=self.run_simulation)
        self.btn_simulate.pack(pady=10)

        # Cadre pour les résultats (texte et graphique)
        frame_result = ttk.LabelFrame(self, text="Résultats")
        frame_result.pack(padx=10, pady=10, fill="both", expand=True)
        self.text_result = tk.Text(frame_result, wrap="word", height=10)
        self.text_result.pack(padx=5, pady=5, fill="both", expand=True)
        # Intégration de matplotlib dans l'interface
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_result)
        self.canvas.get_tk_widget().pack(padx=5, pady=5, fill="both", expand=True)

        # Bouton pour quitter l'application
        self.btn_quit = ttk.Button(self, text="Quitter", command=self.quit)
        self.btn_quit.pack(pady=5)

    def run_simulation(self):
        try:
            duree = self.var_duree.get()
            capital_initial = self.var_capital.get()
            versement = self.var_versement.get()
            plafond = self.var_plafond.get()
            rate1 = self.var_rate1.get()
            rate2 = self.var_rate2.get()
            rate3 = self.var_rate3.get()
            frais = self.var_frais.get()
            inflation = self.var_inflation.get()
            taux_impot = self.var_taux_impot.get()
        except tk.TclError:
            messagebox.showerror("Erreur", "Veuillez vérifier les valeurs saisies.")
            return
        rates = [rate1, rate2, rate3]
        rapport, scenarios = calcul_scenarios(duree, capital_initial, versement, plafond, rates, frais, inflation, taux_impot)
        self.text_result.delete("1.0", tk.END)
        self.text_result.insert(tk.END, rapport)
        # Affichage graphique : tracer l'évolution du capital pour chaque scénario
        self.ax.clear()
        months = list(range(len(scenarios[0]['historique'])))
        for data in scenarios:
            self.ax.plot(months, data['historique'], label=f"Taux {data['taux_str']}")
        self.ax.set_xlabel("Mois")
        self.ax.set_ylabel("Capital (€)")
        self.ax.set_title("Évolution du capital dans le temps")
        self.ax.legend()
        self.canvas.draw()

def main():
    app = PEASimulatorGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
