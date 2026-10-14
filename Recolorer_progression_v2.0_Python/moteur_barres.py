# -*- coding: utf-8 -*-
"""
Moteur « barres » — recoloration des images de barre de progression
(remplissage, reste de la barre, contour, fond). Utilisé par recolorer_progression.py.
Copyright © 2026 Mamadou Bâ Neige

Ce programme est un logiciel libre : vous pouvez le redistribuer et/ou le modifier
selon les termes de la GNU General Public License version 3 publiée par la Free
Software Foundation. Il est distribué SANS AUCUNE GARANTIE. Voir le fichier LICENSE.
This program is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License version 3 as published by the Free Software
Foundation. It is distributed WITHOUT ANY WARRANTY. See the LICENSE file.
"""

import re
from pathlib import Path

import numpy as np
from PIL import Image


# ------------------------------------------------- Jeux de couleurs
# Couleurs proposées à l'ouverture (bouton « Vert / beige ») et en ligne de commande
COULEURS_DEFAUT = {
    "remplissage": "#00FF00",   # partie remplie (le pourcentage)
    "reste":       "#E8D6B0",   # partie vide de la barre (beige)
    "contour":     "#FFFFFF",   # bordure de la barre
    "fond":        "#000000",   # autour de la barre
}
EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}



def _dans_rect_arrondi(x, y, x0, y0, x1, y1, r):
    """Points (x, y) dans le rectangle arrondi [x0,x1]×[y0,y1] de rayon r."""
    if x1 <= x0 or y1 <= y0:
        return np.zeros(np.broadcast(x, y).shape, bool)
    r = max(0.0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    dedans = (x >= x0) & (x <= x1) & (y >= y0) & (y <= y1)
    if r > 0:
        cx = np.clip(x, x0 + r, x1 - r)
        cy = np.clip(y, y0 + r, y1 - r)
        dedans &= (x - cx) ** 2 + (y - cy) ** 2 <= r * r
    return dedans


def _grille(h, w, ss):
    o = (np.arange(ss) + 0.5) / ss
    ys = (np.arange(h)[:, None] + o[None, :]).reshape(-1)
    xs = (np.arange(w)[:, None] + o[None, :]).reshape(-1)
    return np.meshgrid(xs, ys)


_cache_cov = {}


def couvertures(h, w, geom, xf, ss=4):
    """Part de chaque pixel occupée par : fond, contour, remplissage, reste."""
    m, t, r = geom
    cle = (h, w, m, t, r, round(float(xf), 3), ss)
    if cle in _cache_cov:
        return _cache_cov[cle]
    X, Y = _grille(h, w, ss)
    ext = _dans_rect_arrondi(X, Y, m, m, w - m, h - m, r)
    inte = _dans_rect_arrondi(X, Y, m + t, m + t, w - m - t, h - m - t, r - t)
    rempli = inte & (X < xf)

    def red(b):
        return b.reshape(h, ss, w, ss).mean(axis=(1, 3))

    res = (1 - red(ext), red(ext & ~inte), red(rempli), red(inte & ~rempli))
    if len(_cache_cov) > 300:
        _cache_cov.clear()
    _cache_cov[cle] = res
    return res


def _moindres_carres(parts, a):
    """Couleurs qui expliquent le mieux l'image, connaissant les parts."""
    A = np.stack([p.ravel() for p in parts], 1)
    Y = a.reshape(-1, 3)
    cols = np.clip(np.linalg.lstsq(A, Y, rcond=None)[0], 0, 255)   # couleurs réelles
    err = float(((A @ cols - Y) ** 2).mean())
    return cols, err


def ajuster_geometrie(a, rempli=True):
    """Marge, épaisseur du contour et rayon des coins, mesurés sur une image
    dont l'intérieur est d'une seule couleur (barre pleine ou vide)."""
    h, w, _ = a.shape
    xf = w if rempli else -1
    k = 2 if rempli else 3          # indice de la part intérieure

    def essai(geom, ss):
        X, Y = _grille(h, w, ss)
        m, t, r = geom
        ext = _dans_rect_arrondi(X, Y, m, m, w - m, h - m, r)
        inte = _dans_rect_arrondi(X, Y, m + t, m + t, w - m - t, h - m - t, r - t)

        def red(b):
            return b.reshape(h, ss, w, ss).mean(axis=(1, 3))
        parts = [1 - red(ext), red(ext & ~inte), red(inte)]
        return _moindres_carres(parts, a)

    rmax = min(h, w) / 2
    meilleur = None
    for m in np.arange(0, min(3, h / 4) + 1e-9, 0.5):
        for t in np.arange(0, min(4, h / 3) + 1e-9, 0.5):
            for r in np.arange(0, rmax + 1e-9, 1.0):
                _, e = essai((m, t, r), 2)
                if meilleur is None or e < meilleur[0]:
                    meilleur = (e, (m, t, r))
    _, (m0, t0, r0) = meilleur
    meilleur = None
    for m in np.arange(max(0, m0 - 0.5), m0 + 0.51, 0.25):
        for t in np.arange(max(0, t0 - 0.5), t0 + 0.51, 0.25):
            for r in np.arange(max(0, r0 - 1), r0 + 1.01, 0.25):
                cols, e = essai((m, t, r), 4)
                if meilleur is None or e < meilleur[0]:
                    meilleur = (e, (float(m), float(t), float(r)), cols)
    return meilleur   # (erreur, géométrie, couleurs fond/contour/intérieur)


def _ordre_naturel(f):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", f.name)]


def lister_images(dossier, avec_ignorees=False):
    """Images horizontales du dossier (les barres) ; les autres sont ignorées."""
    retenues, ignorees = [], []
    for f in sorted(Path(dossier).iterdir(), key=_ordre_naturel):
        if not (f.is_file() and f.suffix.lower() in EXTENSIONS):
            continue
        try:
            with Image.open(f) as im:
                ok = im.width >= 2 * im.height
        except Exception:
            ok = False
        (retenues if ok else ignorees).append(f)
    return (retenues, ignorees) if avec_ignorees else retenues


def pourcentages_serie(fichiers):
    fichiers = list(fichiers)
    nums = []
    for f in fichiers:
        t = re.findall(r"\d+", f.stem)
        nums.append(int(t[0]) if t else None)
    if fichiers and None not in nums and len(set(nums)) == len(nums) \
            and max(nums) - min(nums) == 100:
        base = min(nums)
        return {f: n - base for f, n in zip(fichiers, nums)}
    if len(fichiers) == 101:
        return {f: i for i, f in enumerate(fichiers)}
    return {}


def _lire(f):
    with Image.open(f) as im:
        return np.asarray(im.convert("RGB")).astype(np.float64)


def analyser_serie(fichiers, pcts=None):
    """Géométrie et couleurs d'origine de la série (mesurées une fois).
    Renvoie {(largeur, hauteur): infos}."""
    fichiers = list(fichiers)
    pcts = pcts if pcts is not None else pourcentages_serie(fichiers)
    par_taille = {}
    for f in fichiers:
        try:
            with Image.open(f) as im:
                par_taille.setdefault(im.size, []).append(f)
        except Exception:
            pass
    serie = {}
    for taille, fs in par_taille.items():
        if pcts:
            plein = max(fs, key=lambda f: pcts.get(f, -1))
            vide = min(fs, key=lambda f: pcts.get(f, 101))
        else:
            plein, vide = fs[-1], fs[0]
        a_plein = _lire(plein)
        _, geom, cols = ajuster_geometrie(a_plein, rempli=True)
        fond, contour, remp = cols
        a_vide = _lire(vide)
        h, w, _ = a_vide.shape
        parts = couvertures(h, w, geom, -1)
        cv, _ = _moindres_carres([parts[0], parts[1], parts[3]], a_vide)
        reste = cv[2]
        # couleur exacte = médiane des pixels entièrement couverts par la partie
        def pure(img, part, defaut):
            sel = part > 0.98
            return np.median(img[sel], axis=0) if sel.sum() >= 3 else defaut
        pp = couvertures(a_plein.shape[0], a_plein.shape[1], geom, a_plein.shape[1] + 1)
        fond = pure(a_plein, pp[0], fond)
        contour = pure(a_plein, pp[1], contour)
        remp = pure(a_plein, pp[2], remp)
        reste = pure(a_vide, parts[3], reste)
        serie[taille] = dict(geom=geom, fond=fond, contour=contour,
                             remplissage=remp, reste=reste)
    return serie


def couleurs_origine(serie):
    """Couleurs mesurées (en #RRVVBB) de la première taille de la série."""
    if not serie:
        return None
    inf = next(iter(serie.values()))
    return {k: "#%02X%02X%02X" % tuple(int(round(v)) for v in np.clip(inf[k], 0, 255))
            for k in ("remplissage", "reste", "contour", "fond")}


def fin_remplissage(a, inf, pct=None):
    """Abscisse (en pixels, avec décimales) où s'arrête le remplissage."""
    h, w, _ = a.shape
    m, t, _ = inf["geom"]
    x0, x1 = m + t, w - m - t
    F, E = np.asarray(inf["remplissage"]), np.asarray(inf["reste"])
    D = F - E
    if float(D @ D) >= 20 ** 2:
        i0, i1 = int(np.ceil(x0)), int(np.floor(x1))
        ligne = a[h // 2, i0:i1]
        f = np.clip(((ligne - E) * D).sum(1) / float(D @ D), 0, 1)
        xf = i0 + f.sum() if f.sum() > 0.05 else x0
        return float(np.clip(xf, x0, x1))
    if pct is not None:
        return x0 + pct / 100 * (x1 - x0)
    return x1


def recolorer(img, couleurs, serie=None, pct=None):
    """Recolore une barre de progression ; la taille est conservée."""
    alpha = img.getchannel("A") if "A" in img.getbands() else None
    a = np.asarray(img.convert("RGB")).astype(np.float64)
    h, w, _ = a.shape
    inf = (serie or {}).get((w, h))
    if inf is None:                                 # image seule : on l'analyse
        _, geom, cols = ajuster_geometrie(a, rempli=True)
        inf = dict(geom=geom, fond=cols[0], contour=cols[1],
                   remplissage=cols[2], reste=cols[2])
    # Couleurs inchangées : l'image d'origine est rendue telle quelle
    if all(hex_vers_rgb(couleurs[k]) == tuple(int(round(v)) for v in np.clip(inf[k], 0, 255))
           for k in ("fond", "contour", "remplissage", "reste")):
        return img.copy()
    xf = fin_remplissage(a, inf, pct)
    fo, co, rp, rs = couvertures(h, w, inf["geom"], xf)
    p = [x[..., None] for x in (fo, co, rp, rs)]
    modele = (p[0] * inf["fond"] + p[1] * inf["contour"]
              + p[2] * inf["remplissage"] + p[3] * inf["reste"])
    # Ce que le modèle n'explique pas (légers dégradés, nuances des bords) est
    # conservé, mais limité pour ne pas laisser de traces des anciennes couleurs
    detail = np.clip(a - modele, -32, 32)
    n = {k: np.array(hex_vers_rgb(couleurs[k]), float)
         for k in ("fond", "contour", "remplissage", "reste")}
    out = p[0] * n["fond"] + p[1] * n["contour"] + p[2] * n["remplissage"] \
        + p[3] * n["reste"] + detail
    res = Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), "RGB")
    if alpha is not None:
        res.putalpha(alpha)
    return res


def hex_vers_rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(f"Couleur invalide : #{h}")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def traiter(entree, sortie, couleurs=None, progression=None):
    """Recolore toutes les barres du dossier d'entrée vers le dossier de sortie."""
    couleurs = {**COULEURS_DEFAUT, **(couleurs or {})}
    sortie = Path(sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    fichiers = lister_images(entree)
    pcts = pourcentages_serie(fichiers)
    serie = analyser_serie(fichiers, pcts)
    for i, f in enumerate(fichiers, 1):
        with Image.open(f) as img:
            taille = img.size
            res = recolorer(img, couleurs, serie, pcts.get(f))
        assert res.size == taille  # la taille est conservée
        if f.suffix.lower() in (".jpg", ".jpeg"):
            res.convert("RGB").save(sortie / f.name, quality=95, subsampling=0)
        else:
            res.save(sortie / f.name)
        if progression:
            progression(i, len(fichiers), f.name)
    return len(fichiers)
