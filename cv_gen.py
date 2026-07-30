# Improved CV Generator (tkinter)
# - Dataclasses for structured data
# - HTML-escaping of user input
# - Completed HTML/CSS template (no truncation placeholders)
# - Edit / Delete / Move Up / Move Down for experiences and projects
# - Robust list normalization for skills, languages, interests
# - URL normalization (adds scheme if missing)
# - Uses Path.as_uri() when opening generated file

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import html
import webbrowser
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
import re
import os


def ensure_url_scheme(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        return url
    return "https://" + url


def normalize_list(s: str) -> List[str]:
    # Split on comma and semicolon, strip, filter empty
    if not s:
        return []
    parts = re.split(r"[;,]", s)
    return [p.strip() for p in parts if p and p.strip()]


@dataclass
class Experience:
    titre: str
    entreprise: str
    dates: str = ""
    missions: List[str] = field(default_factory=list)

    def to_html(self) -> str:
        # Escape content for HTML safety
        titre = html.escape(self.titre)
        entreprise = html.escape(self.entreprise)
        dates = html.escape(self.dates)
        missions_html = ""
        if self.missions:
            li = "".join(f"<li>{html.escape(m)}</li>" for m in self.missions)
            missions_html = f"<ul>{li}</ul>"
        return (
            f"<div class='item'>"
            f"  <div class='upper-row'>"
            f"    <h3 class='job-title'>{titre}</h3>"
            f"    <span class='time'>{dates}</span>"
            f"  </div>"
            f"  <div class='company'>{entreprise}</div>"
            f"  {missions_html}"
            f"</div>"
        )


@dataclass
class Project:
    titre: str
    desc: str = ""

    def to_badge(self) -> str:
        titre = html.escape(self.titre)
        desc = html.escape(self.desc)
        if desc:
            return f'<span class="tag" title="{desc}">{titre}</span>'
        return f'<span class="tag">{titre}</span>'


class ResumeApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Générateur de CV")
        self.root.geometry("900x920")

        # Style
        self.style = ttk.Style(self.root)
        self.style.configure("TNotebook.Tab", padding=[15, 5], font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), foreground="#2980b9")

        # Storage
        self.experiences: List[Experience] = []
        self.projets: List[Project] = []

        self.setup_ui()

    def setup_ui(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=15, pady=10)

        # Tab 1: Info
        self.tab_info = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_info, text="1. Coordonnées")
        self.setup_info_tab()

        # Tab 2: Experiences
        self.tab_exp = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_exp, text="2. Expériences")
        self.setup_exp_tab()

        # Tab 3: Skills & Misc
        self.tab_misc = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_misc, text="3. Compétences & Divers")
        self.setup_misc_tab()

        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.pack(fill="x")
        ttk.Separator(bottom_frame, orient="horizontal").pack(fill="x", pady=5)
        self.btn_gen = ttk.Button(bottom_frame, text="🚀 GÉNÉRER MON CV (HTML)", command=self.generate)
        self.btn_gen.pack(side="right", padx=5)
        ttk.Button(bottom_frame, text="Quitter", command=self.root.quit).pack(side="right")

    def setup_info_tab(self) -> None:
        container = ttk.Frame(self.tab_info, padding="25")
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="Informations Générales", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        fields = [
            ("Nom Complet *", "nom"), ("Email *", "email"), ("Téléphone *", "phone"),
            ("Adresse ", "adresse"), ("Lien LinkedIn", "linkedin"), ("Lien GitHub", "github"),
            ("Diplôme Principal *", "edu")
        ]

        self.info_vars = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(container, text=label).grid(row=i+1, column=0, sticky="w", pady=5)
            var = tk.StringVar()
            ttk.Entry(container, textvariable=var, width=55).grid(row=i+1, column=1, sticky="w", padx=15)
            self.info_vars[key] = var

        ttk.Label(container, text="Résumé / Accroche").grid(row=9, column=0, sticky="nw", pady=15)
        self.resume_text = tk.Text(container, height=8, width=60, font=("Segoe UI", 10), padx=5, pady=5)
        self.resume_text.grid(row=9, column=1, sticky="w", padx=15, pady=15)

    def setup_exp_tab(self) -> None:
        container = ttk.Frame(self.tab_exp, padding="20")
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="Parcours Professionnel", style="Header.TLabel").pack(anchor="w", pady=(0, 10))

        list_container = ttk.LabelFrame(container, text=" Vos Expériences ", padding=10)
        list_container.pack(fill="both", expand=True)

        self.canvas_exp = tk.Canvas(list_container, highlightthickness=0)
        self.scrollbar_exp = ttk.Scrollbar(list_container, orient="vertical", command=self.canvas_exp.yview)
        self.exp_list_frame = ttk.Frame(self.canvas_exp)

        self.exp_list_frame.bind("<Configure>", lambda e: self.canvas_exp.configure(scrollregion=self.canvas_exp.bbox("all")))
        self.canvas_exp.create_window((0, 0), window=self.exp_list_frame, anchor="nw")
        self.canvas_exp.configure(yscrollcommand=self.scrollbar_exp.set)
        self.canvas_exp.pack(side="left", fill="both", expand=True)
        self.scrollbar_exp.pack(side="right", fill="y")

        ttk.Button(container, text="+ Ajouter une expérience", command=lambda: self.add_exp_dialog()).pack(pady=15)

    def add_exp_dialog(self, index: Optional[int] = None) -> None:
        """
        Add or edit an experience. If index is provided, prefill fields and update on save.
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("Détails de l'expérience")
        dialog.geometry("520x700")
        dialog.grab_set()

        main_f = ttk.Frame(dialog, padding=20)
        main_f.pack(fill="both", expand=True)

        ttk.Label(main_f, text="Poste occupé * :").pack(anchor="w")
        titre = ttk.Entry(main_f, width=60); titre.pack(fill="x", pady=5)
        ttk.Label(main_f, text="Entreprise * :").pack(anchor="w")
        ent = ttk.Entry(main_f, width=60); ent.pack(fill="x", pady=5)
        ttk.Label(main_f, text="Dates :").pack(anchor="w")
        dates = ttk.Entry(main_f, width=60); dates.pack(fill="x", pady=5)
        ttk.Label(main_f, text="Missions (une par ligne) :").pack(anchor="w", pady=(10, 0))
        miss = tk.Text(main_f, height=14, width=60, font=("Segoe UI", 10)); miss.pack(fill="both", expand=True, pady=5)

        # If editing, prefill fields
        if index is not None and 0 <= index < len(self.experiences):
            exp = self.experiences[index]
            titre.insert(0, exp.titre)
            ent.insert(0, exp.entreprise)
            dates.insert(0, exp.dates)
            miss.insert("1.0", "\n".join(exp.missions))

        def save():
            t = titre.get().strip()
            e = ent.get().strip()
            if not t or not e:
                messagebox.showwarning("Incomplet", "Poste et entreprise requis.")
                return
            m_list = [l.strip() for l in miss.get("1.0", "end").splitlines() if l.strip()]
            new_exp = Experience(titre=t, entreprise=e, dates=dates.get().strip(), missions=m_list)
            if index is None:
                self.experiences.append(new_exp)
            else:
                self.experiences[index] = new_exp
            self.refresh_exp_list()
            dialog.destroy()

        ttk.Button(main_f, text="Valider", command=save).pack(pady=12)

    def refresh_exp_list(self) -> None:
        for widget in self.exp_list_frame.winfo_children():
            widget.destroy()
        if not self.experiences:
            ttk.Label(self.exp_list_frame, text="Aucune expérience ajoutée.", font=("Arial", 9, "italic")).pack(pady=20)
            return
        for i, exp in enumerate(self.experiences):
            f = ttk.Frame(self.exp_list_frame, padding=5); f.pack(fill="x", expand=True)
            ttk.Label(f, text=f"• {exp.titre} @ {exp.entreprise} ({exp.dates})", font=("Segoe UI", 10)).pack(side="left", padx=5)
            btn_frame = ttk.Frame(f)
            btn_frame.pack(side="right")
            ttk.Button(btn_frame, text="▲", width=3, command=lambda idx=i: self.move_exp_up(idx)).pack(side="left", padx=2)
            ttk.Button(btn_frame, text="▼", width=3, command=lambda idx=i: self.move_exp_down(idx)).pack(side="left", padx=2)
            ttk.Button(btn_frame, text="Éditer", width=8, command=lambda idx=i: self.add_exp_dialog(idx)).pack(side="left", padx=2)
            ttk.Button(btn_frame, text="Supprimer", width=10, command=lambda idx=i: self.remove_exp(idx)).pack(side="left", padx=2)
            ttk.Separator(self.exp_list_frame, orient="horizontal").pack(fill="x", pady=4)

    def remove_exp(self, idx: int) -> None:
        if messagebox.askyesno("Confirmation", "Supprimer cette expérience ?"):
            self.experiences.pop(idx)
            self.refresh_exp_list()

    def move_exp_up(self, idx: int) -> None:
        if idx <= 0: return
        self.experiences[idx-1], self.experiences[idx] = self.experiences[idx], self.experiences[idx-1]
        self.refresh_exp_list()

    def move_exp_down(self, idx: int) -> None:
        if idx >= len(self.experiences) - 1: return
        self.experiences[idx+1], self.experiences[idx] = self.experiences[idx], self.experiences[idx+1]
        self.refresh_exp_list()

    def setup_misc_tab(self) -> None:
        container = ttk.Frame(self.tab_misc, padding="25")
        container.pack(fill="both", expand=True)

        # Hard Skills
        ttk.Label(container, text="Compétences Techniques (Hard Skills)", style="Header.TLabel").pack(anchor="w")
        ttk.Label(container, text="Logiciels, langages, outils (ex: Python, Excel, SQL)", font=("Arial", 8)).pack(anchor="w")
        self.hard_skills_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.hard_skills_var, width=85).pack(pady=(5, 15))

        # Soft Skills
        ttk.Label(container, text="Compétences Générales (Soft Skills)", style="Header.TLabel").pack(anchor="w")
        ttk.Label(container, text="Qualités humaines (ex: Autonomie, Travail d'équipe, Rigueur)", font=("Arial", 8)).pack(anchor="w")
        self.soft_skills_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.soft_skills_var, width=85).pack(pady=(5, 15))

        # Languages & Interests
        grid_f = ttk.Frame(container); grid_f.pack(fill="x", pady=10)
        ttk.Label(grid_f, text="Langues :", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.lang_var = tk.StringVar(); ttk.Entry(grid_f, textvariable=self.lang_var, width=40).grid(row=0, column=1, sticky="w", padx=10, pady=5)
        ttk.Label(grid_f, text="Intérêts :", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w")
        self.interest_var = tk.StringVar(); ttk.Entry(grid_f, textvariable=self.interest_var, width=40).grid(row=1, column=1, sticky="w", padx=10, pady=5)

        ttk.Separator(container, orient="horizontal").pack(fill="x", pady=20)
        ttk.Label(container, text="Projets & Portfolios", style="Header.TLabel").pack(anchor="w")
        self.proj_list_frame = ttk.Frame(container); self.proj_list_frame.pack(fill="both", expand=True, pady=5)
        ttk.Button(container, text="+ Ajouter un projet", command=lambda: self.add_proj_dialog()).pack(pady=5)

    def add_proj_dialog(self, index: Optional[int] = None) -> None:
        dialog = tk.Toplevel(self.root); dialog.title("Détails du projet"); dialog.geometry("480x260"); dialog.grab_set()
        f = ttk.Frame(dialog, padding=20); f.pack(fill="both", expand=True)
        ttk.Label(f, text="Nom du projet :").pack(anchor="w")
        name = ttk.Entry(f, width=60); name.pack(pady=5)
        ttk.Label(f, text="Description courte :").pack(anchor="w")
        desc = ttk.Entry(f, width=60); desc.pack(pady=5)

        if index is not None and 0 <= index < len(self.projets):
            p = self.projets[index]
            name.insert(0, p.titre)
            desc.insert(0, p.desc)

        def save():
            n = name.get().strip()
            if not n:
                messagebox.showwarning("Incomplet", "Nom du projet requis.")
                return
            new_p = Project(titre=n, desc=desc.get().strip())
            if index is None:
                self.projets.append(new_p)
            else:
                self.projets[index] = new_p
            self.refresh_proj_list()
            dialog.destroy()

        ttk.Button(f, text="Ajouter / Mettre à jour", command=save).pack(pady=12)

    def refresh_proj_list(self) -> None:
        for widget in self.proj_list_frame.winfo_children():
            widget.destroy()
        for i, p in enumerate(self.projets):
            f = ttk.Frame(self.proj_list_frame); f.pack(fill="x", pady=2)
            ttk.Label(f, text=f"📂 {p.titre} - {p.desc}", font=("Arial", 9)).pack(side="left")
            btn_frame = ttk.Frame(f); btn_frame.pack(side="right")
            ttk.Button(btn_frame, text="▲", width=3, command=lambda idx=i: self.move_proj_up(idx)).pack(side="left", padx=2)
            ttk.Button(btn_frame, text="▼", width=3, command=lambda idx=i: self.move_proj_down(idx)).pack(side="left", padx=2)
            ttk.Button(btn_frame, text="Éditer", width=8, command=lambda idx=i: self.add_proj_dialog(idx)).pack(side="left", padx=2)
            ttk.Button(btn_frame, text="X", width=3, command=lambda idx=i: self.remove_proj(idx)).pack(side="left", padx=2)

    def remove_proj(self, idx: int) -> None:
        self.projets.pop(idx)
        self.refresh_proj_list()

    def move_proj_up(self, idx: int) -> None:
        if idx <= 0: return
        self.projets[idx-1], self.projets[idx] = self.projets[idx], self.projets[idx-1]
        self.refresh_proj_list()

    def move_proj_down(self, idx: int) -> None:
        if idx >= len(self.projets) - 1: return
        self.projets[idx+1], self.projets[idx] = self.projets[idx], self.projets[idx+1]
        self.refresh_proj_list()

    def generate(self) -> None:
        nom = self.info_vars['nom'].get().strip()
        email = self.info_vars['email'].get().strip()
        if not nom or "@" not in email:
            messagebox.showerror("Champs requis", "Nom et Email valide requis.")
            return

        data = {
            'nom': nom,
            'email': email,
            'phone': self.info_vars['phone'].get().strip(),
            'adresse': self.info_vars['adresse'].get().strip(),
            'linkedin': ensure_url_scheme(self.info_vars['linkedin'].get()),
            'github': ensure_url_scheme(self.info_vars['github'].get()),
            'education': self.info_vars['edu'].get().strip(),
            'resume': self.resume_text.get("1.0", "end-1c").strip(),
            'experiences': self.experiences,
            'projets': self.projets,
            'hard_skills': normalize_list(self.hard_skills_var.get()),
            'soft_skills': normalize_list(self.soft_skills_var.get()),
            'langues': normalize_list(self.lang_var.get()),
            'interets': normalize_list(self.interest_var.get())
        }

        html_content = self.create_html_template(data)
        default_name = f"CV_{nom.replace(' ', '_')}.html"
        initial_dir = Path.home()
        file_path = filedialog.asksaveasfilename(initialdir=str(initial_dir), initialfile=default_name, defaultextension=".html", filetypes=[("HTML", "*.html")])
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            if messagebox.askyesno("Succès", "CV généré ! Ouvrir le fichier ?"):
                # Use Path.as_uri for correct file:// uri
                webbrowser.open_new_tab(Path(file_path).as_uri())

    def create_html_template(self, data: dict) -> str:
        # Links
        links = []
        if data.get('linkedin'): links.append(f'<a href="{html.escape(data["linkedin"])}" target="_blank">LinkedIn</a>')
        if data.get('github'): links.append(f'<a href="{html.escape(data["github"])}" target="_blank">GitHub</a>')
        links_str = (" | " + " | ".join(links)) if links else ""

        # Experiences HTML
        exp_html = ""
        for exp in data['experiences']:
            exp_html += exp.to_html()

        def get_badges(items: List[str], color_class: str = "tag") -> str:
            return "".join([f'<span class="{color_class}">{html.escape(i)}</span>' for i in items if i and i.strip()])

        # Template (completed CSS & structure)
        html_doc = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CV - {html.escape(data['nom'])}</title>
    <style>
        :root {{ --main-blue: #2c3e50; --accent-blue: #3498db; --soft-gray: #7f8c8d; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.5; color: #333; max-width: 850px; margin: 40px auto; padding: 0 20px; background: #f4f7f6; }}
        .cv-container {{ background: #fff; padding: 50px; border-radius: 8px; box-shadow: 0 5px 25px rgba(0,0,0,0.1); border-top: 12px solid var(--main-blue); }}
        header {{ border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 25px; }}
        h1 {{ margin: 0; color: var(--main-blue); font-size: 2.2em; }}
        .contacts {{ color: var(--soft-gray); font-size: 0.9em; margin-top: 8px; }}
        .contacts a {{ color: var(--accent-blue); text-decoration: none; font-weight: 500; }}
        h2 {{ color: var(--accent-blue); border-bottom: 1px solid #d6eaf8; padding-bottom: 5px; margin-top: 35px; text-transform: uppercase; font-size: 1em; letter-spacing: 1px; }}
        .item {{ margin-bottom: 20px; }}
        .upper-row {{ display: flex; justify-content: space-between; align-items: baseline; gap: 10px; }}
        .job-title {{ margin: 0; color: #333; font-size: 1.1em; }}
        .time {{ color: #95a5a6; font-size: 0.85em; font-weight: 600; }}
        .company {{ color: var(--accent-blue); font-weight: 700; margin-top: 2px; }}
        ul {{ margin-top: 8px; padding-left: 20px; color: #444; }}
        .tag {{ display: inline-block; background: #ebf5fb; color: #2c3e50; padding: 5px 12px; border-radius: 4px; margin: 3px; font-size: 0.85em; font-weight: 600; border: 1px solid #d6eaf8; }}
        .tag-soft {{ display: inline-block; background: #f4f7f6; color: #7f8c8d; padding: 5px 12px; border-radius: 4px; margin: 3px; font-size: 0.85em; font-weight: 600; border: 1px solid #eee; }}
        .profile {{ background: #fdfdfd; padding: 15px; border-left: 5px solid var(--accent-blue); font-style: italic; color: #555; margin: 20px 0; }}
        a.badge-link {{ text-decoration: none; }}
        @media (max-width: 720px) {{
            body {{ padding: 15px; margin: 20px; }}
            .cv-container {{ padding: 25px; }}
            h1 {{ font-size: 1.6em; }}
            .upper-row {{ flex-direction: column; align-items: flex-start; gap: 4px; }}
        }}
    </style>
</head>
<body>
    <div class="cv-container">
        <header>
            <h1>{html.escape(data['nom'])}</h1>
            <div class="contacts">{html.escape(data['email'])} | {html.escape(data['phone'])} | {html.escape(data['adresse'])}{links_str}</div>
        </header>
        {f'<div class="profile">{html.escape(data["resume"]).replace(chr(10), "<br>")}</div>' if data.get('resume') else ''}
        <h2>Formation</h2><div class="item"><strong>{html.escape(data.get('education',''))}</strong></div>
        {f'<h2>Parcours Professionnel</h2>{exp_html}' if exp_html else ''}
        {f'<h2>Projets</h2><div>{ "".join(p.to_badge() for p in data.get("projets", [])) }</div>' if data.get('projets') else ''}
        <h2>Compétences Techniques</h2><div>{get_badges(data.get('hard_skills', []))}</div>
        {f'<h2>Compétences Générales</h2><div>{get_badges(data.get("soft_skills", []), "tag-soft")}</div>' if any(x.strip() for x in data.get('soft_skills', [])) else ''}
        {f'<h2>Langues</h2><div>{get_badges(data.get("langues", []))}</div>' if any(x.strip() for x in data.get('langues', [])) else ''}
        {f'<h2>Centres d intérêt</h2><div>{get_badges(data.get("interets", []), "tag-soft")}</div>' if any(x.strip() for x in data.get('interets', [])) else ''}
    </div>
</body>
</html>
"""
        return html_doc


if __name__ == "__main__":
    root = tk.Tk()
    app = ResumeApp(root)
    root.mainloop()
