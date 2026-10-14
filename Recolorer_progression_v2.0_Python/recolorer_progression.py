#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recolorer les indicateurs de progression / Progress Indicator Recolorer
Cercles et barres de progression — progress circles and progress bars
Copyright © 2026 Mamadou Bâ Neige

Ce programme est un logiciel libre : vous pouvez le redistribuer et/ou le modifier
selon les termes de la GNU General Public License version 3 publiée par la Free
Software Foundation. Il est distribué SANS AUCUNE GARANTIE. Voir le fichier LICENSE.
This program is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License version 3 as published by the Free Software
Foundation. It is distributed WITHOUT ANY WARRANTY. See the LICENSE file.

FR  Au lancement, choisissez le type d'images (cercles ou barres), puis les
    couleurs ; la taille des images est conservée.
    Fenêtre : python recolorer_progression.py   (ou double-clic)
    Ligne de commande :
        python recolorer_progression.py [cercles|barres] ENTREE [SORTIE] [--lang fr|en]

EN  On launch, choose the image type (circles or bars), then the colors;
    the image size is kept.
    Window: python recolorer_progression.py   (or double-click)
    Command line:
        python recolorer_progression.py [circles|bars] INPUT [OUTPUT] [--lang fr|en]

Fichiers / Files: recolorer_progression.py, moteur_cercles.py, moteur_barres.py,
                  aide/ (manuels / manuals), icone.ico
Dépendances / Requirements: pip install pillow numpy  (tkinter ships with Python)
"""

import sys
import os
import json
import locale
import webbrowser
from pathlib import Path

from PIL import Image, ImageDraw

import moteur_cercles as mc
import moteur_barres as mb

# ------------------------------------------------------- Auteur et contacts
VERSION = "2.0"
AUTEUR = "Mamadou Bâ Neige"
ANNEE = "2026"
# Remplissez vos contacts ; les lignes laissées vides ne sont pas affichées.
CONTACTS = {
    "E-mail": "mamadou.ba@ugb.edu.sn",
    "Téléphone": "+221 77 645 14 45",
    "YouTube": "https://www.youtube.com/@mamadoubapassioninformatique",
    "Site web": "https://neigeba.com/",
}

# ============================================================ Langues / i18n
TEXTES = {
    "fr": {
        "nom": "Recolorer les indicateurs de progression",
        "droits": "Licence GNU GPL v3.",
        # écran d'accueil
        "accueil_titre": "Quel type d'images voulez-vous recolorer ?",
        "accueil_sous": "Vous pourrez changer de type à tout moment avec le bouton « Changer de type ».",
        "type_cercles": "Cercles de progression",
        "type_barres": "Barres de progression",
        "desc_cercles": "Arc, reste du cercle, texte au milieu, fond.\nEx. : écran de l'Ender-3 V3 SE.",
        "desc_barres": "Remplissage, reste de la barre, contour, fond.\nBarres horizontales.",
        "changer_type": "◀ Changer de type",
        "titre_cercles": "Cercles de progression",
        "titre_barres": "Barres de progression",
        # dossiers
        "dossiers": "Dossiers",
        "entree": "Entrée :",
        "sortie": "Sortie :",
        "parcourir": "Parcourir…",
        "dlg_entree": "Dossier contenant les images",
        "dlg_sortie": "Dossier de sortie",
        # couleurs
        "couleurs": "Couleurs",
        "arc": "Arc (pourcentage)",
        "piste": "Reste du cercle",
        "texte": "Texte au milieu",
        "remplissage": "Remplissage (pourcentage)",
        "reste": "Reste de la barre",
        "contour": "Contour",
        "fond": "Fond",
        "choisir": "Choisir…",
        "btn_creality": "Couleurs originales Creality",
        "btn_origine": "Couleurs d'origine",
        "btn_vb": "Vert / beige",
        "note_cercles": "Pour l'arc, « {o} » garde le dégradé bleu de Creality "
                        "(vous pouvez aussi le taper vous-même).",
        "note_barres": "« Couleurs d'origine » reprend les couleurs mesurées sur "
                       "les images du dossier d'entrée.",
        "mot_origine": "Origine",
        "m_pas_dossier": "Choisissez d'abord le dossier des images : les couleurs "
                         "d'origine sont mesurées sur ses images.",
        # aperçu et statut
        "apercu": "Aperçu (avant / après)",
        "recolorer": "Recolorer toutes les images",
        "aide": "Aide (F1)",
        "a_propos": "À propos",
        "contacts": "Contacts :",
        "E-mail": "E-mail",
        "Téléphone": "Téléphone",
        "YouTube": "YouTube",
        "Site web": "Site web",
        "st_choisir": "Choisissez le dossier des images.",
        "st_analyse": "Analyse de la série…",
        "st_trouvees": "{n} image(s) trouvée(s).",
        "st_ignorees_cercles": "{n} image(s) trouvée(s), {m} ignorée(s) (non carrées).",
        "st_ignorees_barres": "{n} image(s) trouvée(s), {m} ignorée(s) (pas en largeur).",
        "st_aucune_cercles": "Aucune image de cercle dans ce dossier.",
        "st_aucune_barres": "Aucune image de barre dans ce dossier.",
        "st_apercu_err": "Erreur d'aperçu : {e}",
        "st_progres": "{i}/{n}  {nom}",
        "st_termine": "Terminé : {n} image(s).",
        # messages
        "t_manquant": "Dossier manquant",
        "m_entree": "Choisissez le dossier d'entrée.",
        "m_sortie": "Choisissez le dossier de sortie.",
        "t_couleur": "Couleur invalide",
        "m_couleur": "{part} : « {val} » n'est pas une couleur valide (format #RRVVBB).",
        "m_couleur_arc": " Pour l'arc, « {o} » est aussi accepté.",
        "t_attention": "Attention",
        "m_meme": "Le dossier de sortie est le même que le dossier d'entrée.\n"
                  "Les images d'origine seront remplacées. Continuer ?",
        "t_termine": "Terminé",
        "m_termine": "{n} image(s) recolorée(s) dans :\n{d}",
        "t_erreur": "Erreur",
        "t_aide": "Aide",
        "m_aide_absente": "Manuel introuvable :\n{p}\n\nPlacez le dossier « aide » "
                          "à côté du programme.",
        "apropos_desc": "Recoloration des images de progression :\n"
                        "cercles (ex. écran Creality Ender-3 V3 SE) et barres.\n\n"
                        "Logiciel libre sous licence GNU GPL version 3 (fichier LICENSE),\n"
                        "fourni SANS AUCUNE GARANTIE.",
        "version": "version",
        "cli_ok": "{n} image(s) enregistrée(s) dans : {d}",
        "cli_aucune": "Aucune image trouvée dans {d}",
        "suffixe": "_recolore",
        "manuel": "recolorer_progression_manuel_fr.html",
    },
    "en": {
        "nom": "Progress Indicator Recolorer",
        "droits": "Licensed under the GNU GPL v3.",
        "accueil_titre": "Which type of images do you want to recolor?",
        "accueil_sous": "You can switch type at any time with the \u201cChange type\u201d button.",
        "type_cercles": "Progress circles",
        "type_barres": "Progress bars",
        "desc_cercles": "Arc, rest of the circle, center text, background.\nE.g. Ender-3 V3 SE display.",
        "desc_barres": "Fill, rest of the bar, border, background.\nHorizontal bars.",
        "changer_type": "◀ Change type",
        "titre_cercles": "Progress circles",
        "titre_barres": "Progress bars",
        "dossiers": "Folders",
        "entree": "Input:",
        "sortie": "Output:",
        "parcourir": "Browse…",
        "dlg_entree": "Folder containing the images",
        "dlg_sortie": "Output folder",
        "couleurs": "Colors",
        "arc": "Arc (percentage)",
        "piste": "Rest of the circle",
        "texte": "Center text",
        "remplissage": "Fill (percentage)",
        "reste": "Rest of the bar",
        "contour": "Border",
        "fond": "Background",
        "choisir": "Choose…",
        "btn_creality": "Original Creality colors",
        "btn_origine": "Original colors",
        "btn_vb": "Green / beige",
        "note_cercles": "For the arc, \u201c{o}\u201d keeps Creality's blue gradient "
                        "(you can also type it yourself).",
        "note_barres": "\u201cOriginal colors\u201d restores the colors measured on "
                       "the images of the input folder.",
        "mot_origine": "Original",
        "m_pas_dossier": "Choose the image folder first: the original colors are "
                         "measured on its images.",
        "apercu": "Preview (before / after)",
        "recolorer": "Recolor all images",
        "aide": "Help (F1)",
        "a_propos": "About",
        "contacts": "Contacts:",
        "E-mail": "E-mail",
        "Téléphone": "Phone",
        "YouTube": "YouTube",
        "Site web": "Website",
        "st_choisir": "Choose the image folder.",
        "st_analyse": "Analyzing the series…",
        "st_trouvees": "{n} image(s) found.",
        "st_ignorees_cercles": "{n} image(s) found, {m} skipped (not square).",
        "st_ignorees_barres": "{n} image(s) found, {m} skipped (not landscape).",
        "st_aucune_cercles": "No circle images in this folder.",
        "st_aucune_barres": "No progress bar images in this folder.",
        "st_apercu_err": "Preview error: {e}",
        "st_progres": "{i}/{n}  {nom}",
        "st_termine": "Done: {n} image(s).",
        "t_manquant": "Missing folder",
        "m_entree": "Choose the input folder.",
        "m_sortie": "Choose the output folder.",
        "t_couleur": "Invalid color",
        "m_couleur": "{part}: \u201c{val}\u201d is not a valid color (#RRGGBB format).",
        "m_couleur_arc": " For the arc, \u201c{o}\u201d is also accepted.",
        "t_attention": "Warning",
        "m_meme": "The output folder is the same as the input folder.\n"
                  "The original images will be replaced. Continue?",
        "t_termine": "Done",
        "m_termine": "{n} image(s) recolored in:\n{d}",
        "t_erreur": "Error",
        "t_aide": "Help",
        "m_aide_absente": "Manual not found:\n{p}\n\nPut the \"aide\" folder "
                          "next to the program.",
        "apropos_desc": "Recoloring of progress images:\n"
                        "circles (e.g. Creality Ender-3 V3 SE display) and bars.\n\n"
                        "Free software under the GNU GPL version 3 (LICENSE file),\n"
                        "provided WITHOUT ANY WARRANTY.",
        "version": "version",
        "cli_ok": "{n} image(s) saved in: {d}",
        "cli_aucune": "No images found in {d}",
        "suffixe": "_recolored",
        "manuel": "recolorer_progression_manual_en.html",
    },
}

_langue = {"code": "fr"}


def tr(cle, **kw):
    txt = TEXTES[_langue["code"]].get(cle, TEXTES["fr"].get(cle, cle))
    return txt.format(**kw) if kw else txt


def copyright_txt():
    return f"© {ANNEE} {AUTEUR}. {tr('droits')}"


def langue_systeme():
    """'fr' si le système est en français, sinon 'en'."""
    try:
        if sys.platform == "win32":
            import ctypes
            return "fr" if (ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0xFF) == 0x0C else "en"
    except Exception:
        pass
    for v in (os.environ.get("LANG"), os.environ.get("LC_ALL"), (locale.getlocale() or [None])[0]):
        if v:
            return "fr" if v.lower().startswith("fr") else "en"
    return "en"


def _fichier_config():
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "recolorer_progression.json"


def lire_langue():
    try:
        code = json.loads(_fichier_config().read_text(encoding="utf-8")).get("langue")
        if code in TEXTES:
            return code
    except Exception:
        pass
    return langue_systeme()


def enregistrer_langue(code):
    try:
        _fichier_config().write_text(json.dumps({"langue": code}), encoding="utf-8")
    except Exception:
        pass


def dossier_programme():
    """Dossier du programme (fonctionne aussi une fois empaqueté en .exe)."""
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def chemin_manuel(code=None):
    code = code or _langue["code"]
    return dossier_programme() / "aide" / TEXTES[code]["manuel"]


# ============================================================ Types d'images
TYPES = {
    "cercles": dict(moteur=mc, parties=["arc", "piste", "texte", "fond"],
                    case=(276, 276), empiler=False),
    "barres": dict(moteur=mb, parties=["remplissage", "reste", "contour", "fond"],
                   case=(520, 104), empiler=True),
}
ALIAS_TYPES = {"cercles": "cercles", "cercle": "cercles", "circles": "cercles",
               "circle": "cercles", "barres": "barres", "barre": "barres",
               "bars": "barres", "bar": "barres"}


def detecter_type(dossier):
    """Devine le type d'après la forme des images : carrées → cercles,
    en largeur → barres."""
    carres = len(mc.lister_images(dossier))
    larges = len(mb.lister_images(dossier))
    return "barres" if larges > carres else "cercles"


def vignette(type_, taille=(150, 150)):
    """Petite illustration du type, dessinée en grand puis réduite."""
    S = 4
    W, H = taille[0] * S, taille[1] * S
    im = Image.new("RGB", (W, H), (0, 8, 8))
    d = ImageDraw.Draw(im)
    vert, beige = (0, 255, 0), (232, 214, 176)
    if type_ == "cercles":
        m, e = int(0.12 * H), int(0.11 * H)
        bb = [(W - H) // 2 + m, m, (W + H) // 2 - m, H - m]
        d.ellipse(bb, outline=beige, width=e)
        d.arc(bb, start=-90, end=150, fill=vert, width=e)
    else:
        y0, y1 = int(0.36 * H), int(0.64 * H)
        x0, x1 = int(0.08 * W), int(0.92 * W)
        r = (y1 - y0) // 3
        d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=(255, 255, 255))
        c = 3 * S
        d.rounded_rectangle([x0 + c, y0 + c, x1 - c, y1 - c], radius=max(r - c, 0), fill=beige)
        xf = x0 + int(0.62 * (x1 - x0))
        d.rounded_rectangle([x0 + c, y0 + c, xf, y1 - c], radius=max(r - c, 0), fill=vert)
        d.rectangle([xf - r, y0 + c, xf, y1 - c], fill=vert)
    return im.resize(taille, Image.LANCZOS)


# =================================================================== Fenêtre
def lancer_interface():
    import tkinter as tk
    from tkinter import ttk, filedialog, colorchooser, messagebox
    from PIL import ImageTk

    root = tk.Tk()
    root.resizable(False, False)
    try:
        icone = dossier_programme() / "icone.ico"
        if icone.exists():
            root.iconbitmap(default=str(icone))
    except Exception:
        pass

    traduits = []          # (widget, clé, option) : retraduits au changement de langue
    a_retraduire = []      # fonctions supplémentaires à appeler au changement de langue

    def T(widget, cle, option="text"):
        traduits.append((widget, cle, option))
        widget.config(**{option: tr(cle)})
        return widget

    def bouton_colore(parent, cle, commande, fond, texte, survol,
                      police=("Segoe UI", 9, "bold"), padx=10, pady=3):
        """Bouton aux couleurs choisies (les boutons ttk ne se colorent pas)."""
        b = tk.Button(parent, command=commande, bg=fond, fg=texte,
                      activebackground=survol, activeforeground=texte,
                      disabledforeground="#555555", font=police, relief="flat",
                      bd=0, padx=padx, pady=pady, cursor="hand2",
                      highlightthickness=0)
        b.bind("<Enter>", lambda e: b.config(bg=survol) if str(b["state"]) == "normal" else None)
        b.bind("<Leave>", lambda e: b.config(bg=fond))
        return T(b, cle)

    v_statut = tk.StringVar()
    statut = {"cle": "st_choisir", "kw": {}}

    def set_statut(cle, **kw):
        statut["cle"], statut["kw"] = cle, kw
        v_statut.set(tr(cle, **kw))

    # ---------- Barre du haut : titre, changer de type, aide, langue
    haut = tk.Frame(root)
    haut.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 0))
    lbl_titre = tk.Label(haut, font=("Segoe UI", 12, "bold"), fg="#1C2433")
    lbl_titre.pack(side="left")
    zone_langue = tk.Frame(haut, bg="#1F5FBF", padx=1, pady=1)
    zone_langue.pack(side="right")
    btn_langue = {}

    def ouvrir_aide(event=None):
        p = chemin_manuel()
        if not p.exists():
            autre = chemin_manuel("en" if _langue["code"] == "fr" else "fr")
            if autre.exists():
                p = autre
            else:
                messagebox.showerror(tr("t_aide"), tr("m_aide_absente", p=p), parent=root)
                return "break"
        webbrowser.open(p.as_uri())
        return "break"

    bouton_colore(haut, "aide", ouvrir_aide, fond="#1F5FBF", texte="#FFFFFF",
                  survol="#3B7BDB").pack(side="right", padx=(0, 10))
    root.bind_all("<F1>", ouvrir_aide)
    bouton_type = bouton_colore(haut, "changer_type", lambda: afficher_accueil(),
                                fond="#E4E7EC", texte="#1C2433", survol="#D0D5DD")

    # Zone centrale : accueil ou écran de travail (reconstruit à chaque type)
    centre = tk.Frame(root)
    centre.grid(row=1, column=0, sticky="nsew")
    ecran = {"type": None}

    def vider_centre():
        for w in centre.winfo_children():
            w.destroy()
        # on oublie les widgets détruits dans la liste des traductions
        traduits[:] = [(w, c, o) for (w, c, o) in traduits if w.winfo_exists()]
        a_retraduire.clear()

    # ---------- Écran d'accueil : choix du type
    def afficher_accueil():
        vider_centre()
        ecran["type"] = None
        bouton_type.pack_forget()
        lbl_titre.config(text=tr("nom"))
        cadre = tk.Frame(centre, padx=30, pady=20)
        cadre.pack(fill="both", expand=True)
        T(tk.Label(cadre, font=("Segoe UI", 14, "bold"), fg="#1C2433"),
          "accueil_titre").pack(pady=(10, 4))
        T(tk.Label(cadre, fg="#555555", font=("Segoe UI", 9)), "accueil_sous").pack(pady=(0, 18))
        cartes = tk.Frame(cadre)
        cartes.pack()
        photos = []
        for col, type_ in enumerate(("cercles", "barres")):
            carte = tk.Frame(cartes, bg="#FFFFFF", highlightthickness=2,
                             highlightbackground="#C9CED6", cursor="hand2", padx=18, pady=14)
            carte.grid(row=0, column=col, padx=14)
            ph = ImageTk.PhotoImage(vignette(type_, (220, 150)))
            photos.append(ph)
            lb_img = tk.Label(carte, image=ph, bg="#FFFFFF", cursor="hand2")
            lb_img.pack()
            lb_t = T(tk.Label(carte, bg="#FFFFFF", fg="#1C2433", cursor="hand2",
                              font=("Segoe UI", 12, "bold")), "type_" + type_)
            lb_t.pack(pady=(10, 2))
            lb_d = T(tk.Label(carte, bg="#FFFFFF", fg="#555555", cursor="hand2",
                              justify="center", font=("Segoe UI", 9)), "desc_" + type_)
            lb_d.pack()
            for w in (carte, lb_img, lb_t, lb_d):
                w.bind("<Button-1>", lambda e, t=type_: afficher_travail(t))
                w.bind("<Enter>", lambda e, c=carte: c.config(highlightbackground="#1F5FBF"))
                w.bind("<Leave>", lambda e, c=carte: c.config(highlightbackground="#C9CED6"))
        cadre.photos = photos       # garde les images en mémoire
        root.title(f"{tr('nom')} — {copyright_txt()}")

    # ---------- Écran de travail (cercles ou barres)
    def afficher_travail(type_):
        vider_centre()
        ecran["type"] = type_
        prof = TYPES[type_]
        mot = prof["moteur"]
        PARTIES = prof["parties"]
        CL, CH = prof["case"]
        bouton_type.pack(side="right", padx=(0, 10))

        def maj_titre():
            lbl_titre.config(text=f"{tr('nom')} — {tr('titre_' + type_)}")
        maj_titre()
        a_retraduire.append(maj_titre)

        v_entree = tk.StringVar()
        v_sortie = tk.StringVar()
        v_couleurs = {k: tk.StringVar(value=mot.COULEURS_DEFAUT[k]) for k in PARTIES}
        etat = {"fichiers": [], "index": 0, "photos": [], "sortie_auto": True}
        set_statut("st_choisir")

        # Dossiers
        cadre_d = T(ttk.LabelFrame(centre, padding=8), "dossiers")
        cadre_d.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(6, 5))

        def choisir_entree():
            d = filedialog.askdirectory(title=tr("dlg_entree"), parent=root)
            if not d:
                return
            v_entree.set(d)
            if not v_sortie.get() or etat["sortie_auto"]:
                v_sortie.set(str(Path(d).with_name(Path(d).name + tr("suffixe"))))
                etat["sortie_auto"] = True
            retenues, ignorees = mot.lister_images(d, avec_ignorees=True)
            etat["fichiers"], etat["index"] = retenues, 0
            root.config(cursor="watch")
            set_statut("st_analyse")
            root.update_idletasks()
            etat["pcts"] = mot.pourcentages_serie(retenues)
            try:
                if type_ == "cercles":
                    etat["refs"] = mc.references_dossier(retenues)
                else:
                    etat["serie"] = mb.analyser_serie(retenues, etat["pcts"]) if retenues else {}
                    etat["origine"] = mb.couleurs_origine(etat["serie"])
            except Exception:
                etat["refs"], etat["serie"], etat["origine"] = None, {}, None
            root.config(cursor="")
            if not retenues:
                set_statut("st_aucune_" + type_)
            elif ignorees:
                set_statut("st_ignorees_" + type_, n=len(retenues), m=len(ignorees))
            else:
                set_statut("st_trouvees", n=len(retenues))
            maj_apercu()

        def choisir_sortie():
            d = filedialog.askdirectory(title=tr("dlg_sortie"), parent=root,
                                        initialdir=v_entree.get() or None)
            if d:
                v_sortie.set(d)
                etat["sortie_auto"] = False

        for r, (cle, var, cmd) in enumerate([("entree", v_entree, choisir_entree),
                                             ("sortie", v_sortie, choisir_sortie)]):
            T(ttk.Label(cadre_d), cle).grid(row=r, column=0, sticky="w")
            ttk.Entry(cadre_d, textvariable=var, width=60).grid(row=r, column=1, padx=5, pady=2)
            T(ttk.Button(cadre_d, command=cmd), "parcourir").grid(row=r, column=2)

        # Palette
        cadre_c = T(ttk.LabelFrame(centre, padding=8), "couleurs")
        cadre_c.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=5)
        pastilles = {}

        def valider(cle):
            val = v_couleurs[cle].get()
            if type_ == "cercles" and cle == "arc" and mc.est_origine(val):
                v_couleurs[cle].set(tr("mot_origine"))
                pastilles[cle].config(bg=mc.APERCU_BLEU)
                return True
            try:
                mot.hex_vers_rgb(val)
                pastilles[cle].config(bg="#" + val.strip().lstrip("#")[:6])
                return True
            except ValueError:
                return False

        def choisir_couleur(cle):
            actuelle = v_couleurs[cle].get()
            if type_ == "cercles" and mc.est_origine(actuelle):
                actuelle = mc.APERCU_BLEU
            _, hx = colorchooser.askcolor(color=actuelle, title=tr(cle), parent=root)
            if hx:
                v_couleurs[cle].set(hx.upper())
                valider(cle)
                maj_apercu()

        def saisie(cle):
            if valider(cle):
                maj_apercu()

        for r, cle in enumerate(PARTIES):
            T(ttk.Label(cadre_c), cle).grid(row=r, column=0, sticky="w", pady=4)
            p = tk.Label(cadre_c, width=4, relief="solid", bd=1, cursor="hand2")
            p.grid(row=r, column=1, padx=6)
            p.bind("<Button-1>", lambda e, c=cle: choisir_couleur(c))
            pastilles[cle] = p
            e = ttk.Entry(cadre_c, textvariable=v_couleurs[cle], width=9)
            e.grid(row=r, column=2)
            e.bind("<Return>", lambda ev, c=cle: saisie(c))
            e.bind("<FocusOut>", lambda ev, c=cle: saisie(c))
            T(ttk.Button(cadre_c, command=lambda c=cle: choisir_couleur(c)),
              "choisir").grid(row=r, column=3, padx=(6, 0))
            valider(cle)

        def appliquer(jeu):
            for cle in PARTIES:
                v_couleurs[cle].set(jeu[cle])
                valider(cle)
            maj_apercu()

        boutons = ttk.Frame(cadre_c)
        boutons.grid(row=len(PARTIES), column=0, columnspan=4, pady=(10, 0), sticky="w")
        if type_ == "cercles":
            bord = tk.Frame(boutons, bg="#358BDE", padx=2, pady=2)
            bord.pack(side="left")
            bouton_colore(bord, "btn_creality", lambda: appliquer(mc.COULEURS_CREALITY),
                          fond="#101C20", texte="#FFC64A", survol="#1E3038").pack()
        else:
            def couleurs_d_origine():
                if not etat.get("origine"):
                    messagebox.showinfo(tr("btn_origine"), tr("m_pas_dossier"), parent=root)
                    return
                appliquer(etat["origine"])
            bord = tk.Frame(boutons, bg="#555555", padx=2, pady=2)
            bord.pack(side="left")
            bouton_colore(bord, "btn_origine", couleurs_d_origine,
                          fond="#1C2433", texte="#FFFFFF", survol="#2E3A50").pack()
        bord_vb = tk.Frame(boutons, bg="#00C800", padx=2, pady=2)
        bord_vb.pack(side="left", padx=8)
        bouton_colore(bord_vb, "btn_vb", lambda: appliquer(mot.COULEURS_DEFAUT),
                      fond="#E8D6B0", texte="#2B2416", survol="#F3E6C8").pack()
        lbl_note = ttk.Label(cadre_c, foreground="#555555", wraplength=300, justify="left")
        lbl_note.grid(row=len(PARTIES) + 1, column=0, columnspan=4, sticky="w", pady=(8, 0))

        def maj_note():
            ancien = TEXTES["en" if _langue["code"] == "fr" else "fr"]["mot_origine"]
            if type_ == "cercles":
                lbl_note.config(text=tr("note_cercles", o=tr("mot_origine")))
                if v_couleurs["arc"].get() == ancien or mc.est_origine(v_couleurs["arc"].get()):
                    v_couleurs["arc"].set(tr("mot_origine"))
            else:
                lbl_note.config(text=tr("note_barres"))
        maj_note()
        a_retraduire.append(maj_note)

        # Aperçu
        cadre_a = T(ttk.LabelFrame(centre, padding=8), "apercu")
        cadre_a.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=5)
        cases = []
        for i in (0, 1):
            case = tk.Frame(cadre_a, width=CL, height=CH, bg="#cccccc")
            if prof["empiler"]:
                case.grid(row=i, column=0, columnspan=2, pady=3)
            else:
                case.grid(row=0, column=i, padx=3)
            case.grid_propagate(False)
            case.pack_propagate(False)          # la case garde toujours sa taille
            lbl = tk.Label(case, bg="#cccccc", bd=0)
            lbl.place(relx=0.5, rely=0.5, anchor="center")
            cases.append(lbl)
        lbl_avant, lbl_apres = cases
        nav = ttk.Frame(cadre_a)
        nav.grid(row=2, column=0, columnspan=2, pady=(6, 0))
        v_nom = tk.StringVar(value="—")

        def changer(delta):
            if etat["fichiers"]:
                etat["index"] = (etat["index"] + delta) % len(etat["fichiers"])
                maj_apercu()

        ttk.Button(nav, text="◀", width=3, command=lambda: changer(-1)).pack(side="left")
        ttk.Label(nav, textvariable=v_nom, width=26, anchor="center").pack(side="left", padx=5)
        ttk.Button(nav, text="▶", width=3, command=lambda: changer(1)).pack(side="left")

        def couleurs_actuelles():
            return {k: v.get() for k, v in v_couleurs.items()}

        def ajuster_a_la_case(im):
            """Adapte l'image à la case d'aperçu en gardant ses proportions."""
            echelle = min(CL / im.width, CH / im.height)
            if echelle >= 1:
                z = int(echelle)
                return im.resize((im.width * z, im.height * z), Image.NEAREST)
            taille = (max(1, round(im.width * echelle)), max(1, round(im.height * echelle)))
            return im.resize(taille, Image.LANCZOS)

        def recolorer_une(img, f):
            pct = etat.get("pcts", {}).get(f)
            if type_ == "cercles":
                return mc.recolorer(img, couleurs_actuelles(), etat.get("refs"), pct)
            return mb.recolorer(img, couleurs_actuelles(), etat.get("serie"), pct)

        def maj_apercu():
            if not etat["fichiers"]:
                return
            for cle in PARTIES:
                if not valider(cle):
                    return
            f = etat["fichiers"][etat["index"]]
            try:
                with Image.open(f) as img:
                    img.load()
                    apres = recolorer_une(img, f)
                    avant = img.convert("RGBA")
            except Exception as ex:
                set_statut("st_apercu_err", e=ex)
                return
            etat["photos"] = [ImageTk.PhotoImage(ajuster_a_la_case(avant)),
                              ImageTk.PhotoImage(ajuster_a_la_case(apres.convert("RGBA")))]
            lbl_avant.config(image=etat["photos"][0])
            lbl_apres.config(image=etat["photos"][1])
            v_nom.set(f"{f.name}  ({etat['index'] + 1}/{len(etat['fichiers'])})")

        # Lancement
        bas = ttk.Frame(centre, padding=(10, 5, 10, 10))
        bas.grid(row=2, column=0, columnspan=2, sticky="ew")
        barre = ttk.Progressbar(bas, length=380, mode="determinate")
        barre.pack(side="left")
        ttk.Label(bas, textvariable=v_statut, width=42).pack(side="left", padx=8)

        def lancer():
            entree, sortie = v_entree.get(), v_sortie.get()
            if not entree or not Path(entree).is_dir():
                messagebox.showwarning(tr("t_manquant"), tr("m_entree"), parent=root)
                return
            if not sortie:
                messagebox.showwarning(tr("t_manquant"), tr("m_sortie"), parent=root)
                return
            for cle in PARTIES:
                if not valider(cle):
                    msg = tr("m_couleur", part=tr(cle), val=v_couleurs[cle].get())
                    if type_ == "cercles" and cle == "arc":
                        msg += tr("m_couleur_arc", o=tr("mot_origine"))
                    messagebox.showerror(tr("t_couleur"), msg, parent=root)
                    return
            if Path(sortie).resolve() == Path(entree).resolve():
                if not messagebox.askyesno(tr("t_attention"), tr("m_meme"), parent=root):
                    return

            def prog(i, n, nom):
                barre["maximum"] = n
                barre["value"] = i
                set_statut("st_progres", i=i, n=n, nom=nom)
                root.update_idletasks()

            bouton.config(state="disabled")
            try:
                n = mot.traiter(entree, sortie, couleurs_actuelles(), prog)
            except Exception as ex:
                messagebox.showerror(tr("t_erreur"), str(ex), parent=root)
                return
            finally:
                bouton.config(state="normal")
            set_statut("st_termine", n=n)
            messagebox.showinfo(tr("t_termine"), tr("m_termine", n=n, d=sortie), parent=root)

        bouton = bouton_colore(bas, "recolorer", lancer,
                               fond="#00FF00", texte="#000000", survol="#5CFF5C",
                               police=("Segoe UI", 11, "bold"), padx=16, pady=6)
        bouton.pack(side="right")

    # ---------- Copyright et contacts
    ttk.Separator(root).grid(row=2, column=0, sticky="ew", padx=10)
    pied = tk.Frame(root)
    pied.grid(row=3, column=0, sticky="ew", padx=10, pady=(4, 2))
    lbl_copy = tk.Label(pied, fg="#444444", font=("Segoe UI", 9))
    lbl_copy.pack(side="left")

    def lien(cle, val):
        if cle == "E-mail":
            return "mailto:" + val
        if cle in ("YouTube", "Site web"):
            return val if val.startswith("http") else "https://" + val
        return None

    contacts = [(k, v.strip()) for k, v in CONTACTS.items() if v.strip()]
    ligne2 = tk.Frame(root)
    lbls_contacts = []
    if contacts:
        ligne2.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 8))
        T(tk.Label(ligne2, fg="#444444", font=("Segoe UI", 9)), "contacts").grid(
            row=0, column=0, sticky="nw")
    for i, (cle, val) in enumerate(contacts):
        url = lien(cle, val)
        court = val.split("://", 1)[-1]
        court = court[4:] if court.startswith("www.") else court
        court = court.rstrip("/")
        l = tk.Label(ligne2, font=("Segoe UI", 9, "underline" if url else ""),
                     fg="#1F5FBF" if url else "#444444", cursor="hand2" if url else "")
        if url:
            l.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
        l.grid(row=i // 2, column=1 + i % 2, sticky="w", padx=(10, 10))
        lbls_contacts.append((l, cle, court))

    def a_propos():
        sep = " : " if _langue["code"] == "fr" else ": "
        lignes = [f"{tr('nom')}  —  {tr('version')} {VERSION}", "",
                  tr("apropos_desc"), "", copyright_txt()]
        if contacts:
            lignes += ["", tr("contacts")] + [f"   {tr(k)}{sep}{v}" for k, v in contacts]
        messagebox.showinfo(tr("a_propos"), "\n".join(lignes), parent=root)

    T(tk.Button(pied, command=a_propos, relief="flat", bd=0, fg="#1F5FBF",
                cursor="hand2", font=("Segoe UI", 9)), "a_propos").pack(side="left", padx=12)

    # ---------- Changement de langue
    def changer_langue(code):
        _langue["code"] = code
        enregistrer_langue(code)
        traduits[:] = [(w, c, o) for (w, c, o) in traduits if w.winfo_exists()]
        for w, cle, opt in traduits:
            w.config(**{opt: tr(cle)})
        root.title(f"{tr('nom')} — {copyright_txt()}")
        if ecran["type"] is None:
            lbl_titre.config(text=tr("nom"))
        for f in list(a_retraduire):
            f()
        lbl_copy.config(text=f"{tr('nom')} v{VERSION}  —  {copyright_txt()}")
        sep = " : " if code == "fr" else ": "
        for l, cle, val in lbls_contacts:
            l.config(text=f"{tr(cle)}{sep}{val}")
        v_statut.set(tr(statut["cle"], **statut["kw"]))
        for c, b in btn_langue.items():
            actif = c == code
            b.config(bg="#1F5FBF" if actif else "#FFFFFF",
                     fg="#FFFFFF" if actif else "#1F5FBF")

    for code in ("fr", "en"):
        b = tk.Button(zone_langue, text=code.upper(), width=3, relief="flat", bd=0,
                      font=("Segoe UI", 9, "bold"), cursor="hand2",
                      activebackground="#3B7BDB", activeforeground="#FFFFFF",
                      highlightthickness=0, command=lambda c=code: changer_langue(c))
        b.pack(side="left")
        btn_langue[code] = b

    afficher_accueil()
    changer_langue(_langue["code"])
    root.mainloop()


def main():
    # Programme .exe sans console : les messages texte n'ont nulle part où aller
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    args = sys.argv[1:]
    code = None
    if "--lang" in args:
        i = args.index("--lang")
        if i + 1 < len(args):
            code = args[i + 1].lower()[:2]
            del args[i:i + 2]
        else:
            del args[i]
    _langue["code"] = code if code in TEXTES else lire_langue()

    if args:
        print(f"{tr('nom')} v{VERSION} — {copyright_txt()}")
        type_ = ALIAS_TYPES.get(args[0].lower())
        if type_:
            args = args[1:]
        if not args:
            print(tr("m_entree"))
            return
        entree = Path(args[0])
        type_ = type_ or detecter_type(entree)
        sortie = (Path(args[1]) if len(args) > 1
                  else entree.with_name(entree.name + tr("suffixe")))
        n = TYPES[type_]["moteur"].traiter(
            entree, sortie, progression=lambda i, t, nom: print(f"OK  {nom}"))
        print(f"[{tr('titre_' + type_)}]")
        print("\n" + tr("cli_ok", n=n, d=sortie) if n else tr("cli_aucune", d=entree))
    else:
        lancer_interface()


if __name__ == "__main__":
    main()
