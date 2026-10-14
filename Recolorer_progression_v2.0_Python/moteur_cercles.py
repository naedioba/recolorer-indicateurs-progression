# -*- coding: utf-8 -*-
"""
Moteur « cercles » — recoloration des images circulaires de progression
(arc, reste du cercle, texte, fond). Utilisé par recolorer_progression.py.
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
ORIGINE = "Origine"   # pour l'arc : garde le dégradé bleu d'origine
MOTS_ORIGINE = {"origine", "original", "origin"}   # acceptés en saisie

# Couleurs initiales de Creality (bouton « Couleurs originales Creality »)
COULEURS_CREALITY = {
    "arc":   ORIGINE,     # dégradé bleu d'origine
    "piste": "#101C20",   # gris foncé
    "texte": "#FFC64A",   # orange
    "fond":  "#000808",   # noir
}

# Couleurs proposées à l'ouverture et utilisées en ligne de commande
COULEURS_DEFAUT = {
    "arc":   "#00FF00",   # partie qui indique le pourcentage
    "piste": "#E8D6B0",   # reste du cercle (beige)
    "texte": "#FFC64A",   # texte du pourcentage (orange d'origine)
    "fond":  "#000808",   # fond (noir d'origine)
}
APERCU_BLEU = "#358BDE"   # pastille affichée quand l'arc est sur « Origine »

# ------------------------------- Géométrie et couleurs Creality (mesurées)
FOND_ORIGINE = (0, 8, 8)
PISTE_ORIGINE = (16, 28, 32)
TEXTE_ORIGINE = (255, 198, 74)
ARC_HAUT = (57, 172, 222)     # dégradé bleu Creality : haut du cercle ...
ARC_BAS = (49, 99, 222)       # ... et bas du cercle
ANNEAU_INT, ANNEAU_EXT = 0.758, 1.0   # bords de l'anneau Creality (secours)
EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}


def est_origine(v):
    return str(v).strip().lower() in MOTS_ORIGINE


def hex_vers_rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(f"Couleur invalide : #{h}")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _degrade_creality(yn):
    """Couleur de l'arc Creality selon la hauteur (0 = haut, 1 = bas)."""
    yn = np.clip(yn, 0, 1)[..., None]
    return np.array(ARC_HAUT, float) * (1 - yn) + np.array(ARC_BAS, float) * yn


_cache_couv = {}


def _couverture_anneau(h, w, r_int=ANNEAU_INT, r_ext=ANNEAU_EXT, sur=4):
    """Part de chaque pixel couverte par l'anneau (anti-crénelage géométrique)."""
    cle = (h, w, round(r_int, 4), round(r_ext, 4))
    if cle not in _cache_couv:
        if len(_cache_couv) > 20:
            _cache_couv.clear()
        demi = min(w, h) / 2
        o = (np.arange(sur) + 0.5) / sur - 0.5
        yy, xx = np.mgrid[:h, :w]
        tot = np.zeros((h, w))
        for dy in o:
            for dx in o:
                d = np.hypot(xx + dx - (w - 1) / 2, yy + dy - (h - 1) / 2) / demi
                tot += (d >= r_int) & (d <= r_ext)
        _cache_couv[cle] = tot / sur ** 2
    return _cache_couv[cle]


def _ecart(c1, c2):
    return np.sqrt(((np.asarray(c1, float) - np.asarray(c2, float)) ** 2).sum(-1))


def _rayons_anneau(a, d_px, demi, fond):
    """Mesure les bords intérieur et extérieur de l'anneau sur l'image même
    (en fraction du demi-côté). Renvoie les valeurs Creality en cas d'échec."""
    e = _ecart(a, fond)
    pas = 0.5
    k = np.floor(d_px / pas).astype(int)
    nmax = int(demi / pas) + 2
    prof = np.zeros(nmax)
    for b in range(nmax):
        v = e[k == b]
        prof[b] = np.percentile(v, 90) if v.size else 0
    rr = (np.arange(nmax) + 0.5) * pas
    zone = rr > 0.35 * demi
    if not zone.any() or prof[zone].max() < 15:
        return ANNEAU_INT, ANNEAU_EXT
    seuil = 0.5 * prof[zone].max()
    dessus = zone & (prof > seuil)
    j_ext = np.nonzero(dessus)[0].max()           # bande la plus extérieure
    j_int = j_ext
    while j_int - 1 >= 0 and dessus[j_int - 1]:
        j_int -= 1
    seuil = 0.5 * np.median(prof[j_int:j_ext + 1])

    def croisement(j0, j1):   # rayon où le profil passe le seuil entre j0 et j1
        p0, p1 = prof[j0], prof[j1]
        t = 0.5 if p1 == p0 else np.clip((seuil - p0) / (p1 - p0), 0, 1)
        return rr[j0] + t * (rr[j1] - rr[j0])

    r_int = croisement(j_int - 1, j_int) if j_int > 0 else rr[j_int]
    r_ext = croisement(j_ext, j_ext + 1) if j_ext + 1 < nmax else rr[j_ext]
    r_int, r_ext = r_int / demi, r_ext / demi
    if not (0.2 < r_int < r_ext <= 1.1) or r_ext - r_int < 0.04:
        return ANNEAU_INT, ANNEAU_EXT
    return float(r_int), float(r_ext)


def _analyser(a, references=None, pourcentage=None):
    """Retrouve la géométrie et les couleurs actuelles d'une image,
    quelles que soient ses couleurs et sa taille.
    references : couleurs d'arc et de piste typiques du dossier (facultatif),
    utilisées pour les cercles d'une seule couleur (0 % ou 100 %)."""
    h, w, _ = a.shape
    yy, xx = np.mgrid[:h, :w]
    cx, cy = (w - 1) / 2, (h - 1) / 2
    demi = min(w, h) / 2
    d_px = np.hypot(xx - cx, yy - cy)
    d = d_px / demi
    angle = (np.degrees(np.arctan2(xx - cx, -(yy - cy))) + 360) % 360  # 0 = haut
    yn = yy / max(h - 1, 1)

    # Fond : les coins de l'image, hors du cercle
    coins0 = d > 1.02
    fond = np.median(a[coins0], axis=0) if coins0.sum() >= 4 else np.array(FOND_ORIGINE, float)

    # Bords réels de l'anneau, mesurés sur l'image
    r_int, r_ext = _rayons_anneau(a, d_px, demi, fond)
    marge = 1.5 / demi
    ep = r_ext - r_int
    anneau = (d >= r_int - marge) & (d <= r_ext + marge)
    centre = d < r_int - marge
    coeur = (d >= r_int + 0.25 * ep) & (d <= r_ext - 0.25 * ep)

    # Couleur du cœur de l'anneau par tranches de 5°
    nb = 72
    tranche = np.minimum((angle // (360 / nb)).astype(int), nb - 1)
    coul = np.array([np.median(a[coeur & (tranche == k)], axis=0)
                     if (coeur & (tranche == k)).any() else fond for k in range(nb)])
    ybin = np.array([np.median(yn[coeur & (tranche == k)])
                     if (coeur & (tranche == k)).any() else 0.5 for k in range(nb)])

    # L'arc part du haut et tourne dans le sens horaire jusqu'à l'angle du
    # pourcentage ; la piste occupe le reste. On cherche la coupure qui explique
    # le mieux les couleurs : arc = dégradé vertical possible, piste = uniforme.
    def ajuste_bins(k):
        c, y = coul[:k], ybin[:k]
        if k >= 3 and np.ptp(y) > 0.15:
            X = np.stack([np.ones(k), y], 1)
            coef = np.linalg.lstsq(X, c, rcond=None)[0]
            return lambda yy_, c_=coef: c_[0] + np.asarray(yy_)[..., None] * c_[1]
        m = c.mean(0)
        return lambda yy_, m_=m: np.broadcast_to(m_, np.shape(yy_) + (3,))

    def cout(k):
        f = ajuste_bins(k)
        ca = float(((coul[:k] - f(ybin[:k])) ** 2).sum())
        cp = coul[k:]
        return ca + float(((cp - cp.mean(0)) ** 2).sum())

    couts = np.array([cout(k) for k in range(1, nb)])
    k_best = int(np.argmin(couts)) + 1
    bruit = np.sqrt(couts[k_best - 1] / (nb * 3))
    f_arc = ajuste_bins(k_best)
    contraste = float(np.mean(_ecart(coul[k_best:], f_arc(ybin[k_best:]))))
    deux = contraste > max(20.0, 4 * bruit)

    theta = k_best * 360 / nb           # angle de fin de l'arc (degrés)
    refs_ok = bool(references) and references.get("arc") is not None \
        and references.get("piste") is not None
    if refs_ok:
        # Avec les couleurs de référence du dossier, on cherche la fin de l'arc
        # degré par degré : cela repère aussi les tout petits écarts (95–99 %).
        nf = 360
        tf = np.minimum(angle.astype(int), nf - 1)
        est_a, poids = np.zeros(nf), np.zeros(nf)
        for kf in range(nf):
            mk = coeur & (tf == kf)
            if mk.any():
                cm = np.median(a[mk], axis=0)
                est_a[kf] = 1.0 if _ecart(cm, references["arc"]) < _ecart(cm, references["piste"]) else -1.0
                poids[kf] = 1.0
        # coupure qui minimise les désaccords (arc avant, piste après)
        cum_p = np.concatenate([[0], np.cumsum((est_a < 0) * poids)])   # piste avant k
        cum_a = np.concatenate([[0], np.cumsum((est_a > 0) * poids)])
        err = cum_p + (cum_a[-1] - cum_a)                              # erreurs
        kf = int(np.argmin(err))
        n_arc_ok = cum_a[kf] - 0
        n_piste_ok = (cum_p[-1] - cum_p[kf])
        if n_arc_ok >= 1 and n_piste_ok >= 1:
            deux, theta = True, float(kf)

    g_arc = np.zeros(nb, bool)
    if deux:
        a_arc = a_piste = True
    else:
        # Une seule couleur : 0 % (tout piste) ou 100 % (tout arc)
        unie = np.median(coul, axis=0)
        if pourcentage is not None:
            # la place de l'image dans la série donne le pourcentage
            est_arc = pourcentage >= 50
        elif refs_ok:
            est_arc = _ecart(unie, references["arc"]) < _ecart(unie, references["piste"])
        else:
            # sans référence : « 100% » a un texte plus large que « 0% »
            m_txt = centre & (_ecart(a, fond) > 0.5 * max(_ecart(a[centre], fond).max(), 1))
            xs = np.nonzero(m_txt)[1]
            est_arc = xs.size and (xs.max() - xs.min()) / w > 0.28
        a_arc, a_piste = bool(est_arc), not est_arc
        theta = 360.0 if est_arc else 0.0

    pix_arc = coeur & (angle < theta)
    pix_piste = coeur & (angle >= theta)

    # Couleur de l'arc (dégradé vertical possible) et de la piste, affinées
    # en écartant les pixels de transition entre les deux
    def ajuster(masque):
        ys, cs = yn[masque], a[masque]
        if masque.sum() >= 6 and np.ptp(ys) > 0.2:
            X = np.stack([np.ones_like(ys), ys], 1)
            coef = np.linalg.lstsq(X, cs, rcond=None)[0]
            return lambda y, c=coef: c[0] + np.asarray(y)[..., None] * c[1]
        moy = np.median(cs, axis=0)
        return lambda y, m=moy: np.broadcast_to(m, np.shape(y) + (3,)).astype(float)

    arc = ajuster(pix_arc) if a_arc and pix_arc.sum() >= 3 else None
    piste = np.median(a[pix_piste], axis=0) if a_piste and pix_piste.any() else None
    if arc is not None and piste is not None:
        pur_arc = pix_arc
        for _ in range(3):
            d_arc = _ecart(a, arc(yn))
            d_piste = _ecart(a, piste)
            pur_arc = pix_arc & (d_arc < d_piste)
            pur_piste = pix_piste & (d_piste < d_arc)
            if pur_arc.sum() >= 3:
                arc = ajuster(pur_arc)
            if pur_piste.any():
                piste = np.median(a[pur_piste], axis=0)
        pix_arc = pur_arc if pur_arc.sum() >= 3 else pix_arc

    # Cercle d'une seule couleur : l'autre couleur vient des références du
    # dossier, pour traiter aussi les petites encoches (99 %, 1 %…)
    if refs_ok:
        if piste is None:
            piste = np.asarray(references["piste"], float)
        if arc is None:
            ref_a = np.asarray(references["arc"], float)
            arc = lambda y, m=ref_a: np.broadcast_to(m, np.shape(y) + (3,)).astype(float)

    ecart_creality = (float(np.median(_ecart(a[pix_arc], _degrade_creality(yn[pix_arc]))))
                      if arc is not None and pix_arc.any() else 0.0)
    arc_moyen = np.median(a[pix_arc], axis=0) if arc is not None and pix_arc.any() else None

    # Couleur du texte : pixels du centre les plus éloignés du fond
    texte = None
    if centre.any():
        e = _ecart(a[centre], fond)
        if e.max() > 20:
            texte = np.median(a[centre][e >= 0.95 * e.max()], axis=0)

    return dict(fond=fond, arc=arc, piste=piste, texte=texte, yn=yn,
                ecart_creality=ecart_creality, arc_moyen=arc_moyen, deux=deux,
                anneau=anneau, centre=centre, r_int=r_int, r_ext=r_ext)


def pourcentages_serie(fichiers):
    """Pourcentage de chaque image d'après sa place dans la série :
    - si les noms contiennent des numéros qui couvrent exactement 101 valeurs
      (ex. 0…100, ou 2527…2627 pour Creality), numéro − plus petit numéro ;
    - sinon, si le dossier contient 101 images, leur rang (0 à 100).
    Renvoie {} si le dossier ne ressemble pas à une série complète."""
    import re
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


def references_dossier(fichiers, maxi=30):
    """Couleurs typiques de l'arc et de la piste dans un dossier, mesurées sur
    les cercles qui montrent les deux (sert pour 0 % et 100 %)."""
    if not fichiers:
        return None
    pas = max(1, len(fichiers) // maxi)
    arcs, pistes = [], []
    for f in list(fichiers)[::pas]:
        try:
            with Image.open(f) as im:
                inf = _analyser(np.asarray(im.convert("RGB")).astype(np.float64))
        except Exception:
            continue
        if inf["deux"] and inf["arc_moyen"] is not None and inf["piste"] is not None:
            arcs.append(inf["arc_moyen"])
            pistes.append(inf["piste"])
    if not arcs:
        return None
    return {"arc": np.median(arcs, axis=0), "piste": np.median(pistes, axis=0)}


def recolorer(img, couleurs=None, references=None, pourcentage=None):
    """Recolore une image PIL et renvoie une nouvelle image de même taille.
    L'image d'entrée peut être d'origine Creality, déjà recolorée, ou d'une
    autre taille. references : voir references_dossier()."""
    couleurs = {**COULEURS_DEFAUT, **(couleurs or {})}
    alpha = img.getchannel("A") if "A" in img.getbands() else None
    a = np.asarray(img.convert("RGB")).astype(np.float64)
    inf = _analyser(a, references, pourcentage)
    yn = inf["yn"]
    B = inf["fond"]

    arc_origine = est_origine(couleurs["arc"])
    n_fond = np.array(hex_vers_rgb(couleurs["fond"]), float)
    n_piste = np.array(hex_vers_rgb(couleurs["piste"]), float)
    n_texte = np.array(hex_vers_rgb(couleurs["texte"]), float)

    # Image déjà aux couleurs Creality et couleurs Creality demandées : inchangée
    if arc_origine and all(hex_vers_rgb(couleurs[k]) == hex_vers_rgb(COULEURS_CREALITY[k])
                           for k in ("piste", "texte", "fond")):
        ok = _ecart(B, FOND_ORIGINE) < 12
        ok &= inf["piste"] is None or _ecart(inf["piste"], PISTE_ORIGINE) < 12
        ok &= inf["texte"] is None or _ecart(inf["texte"], TEXTE_ORIGINE) < 12
        ok &= inf["ecart_creality"] < 12
        if ok:
            return img.copy()

    out = np.empty_like(a)
    out[:] = n_fond

    # --- Anneau : chaque pixel = fond + c·(mélange arc/piste − fond), où c est la
    # part du pixel couverte par l'anneau (calculée par la géométrie) et w la part
    # d'arc dans le mélange (bords arrondis de l'arc)
    m = inf["anneau"]
    c = _couverture_anneau(*a.shape[:2], inf["r_int"], inf["r_ext"])[m]
    q = B + (a[m] - B) / np.maximum(c, 0.05)[:, None]   # couleur sous la couverture
    if inf["arc"] is None:
        w = np.zeros(len(q))
    elif inf["piste"] is None:
        w = np.ones(len(q))
    else:
        A = inf["arc"](yn[m])
        D = A - inf["piste"]
        w = np.clip(((q - inf["piste"]) * D).sum(1) / np.maximum((D * D).sum(1), 1e-6), 0, 1)
    n_arc = (_degrade_creality(yn[m]) if arc_origine
             else np.array(hex_vers_rgb(couleurs["arc"]), float))
    melange = w[:, None] * n_arc + (1 - w[:, None]) * n_piste
    out[m] = n_fond + c[:, None] * (melange - n_fond)

    # --- Centre : fond + t·(texte − fond)
    m = inf["centre"]
    if inf["texte"] is not None:
        T = inf["texte"] - B
        t = np.clip(((a[m] - B) * T).sum(1) / max((T * T).sum(), 1e-6), 0, 1)
        out[m] = n_fond + t[:, None] * (n_texte - n_fond)

    res = Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), "RGB")
    if alpha is not None:
        res.putalpha(alpha)
    return res


def _ordre_naturel(f):
    """Trie 2.png avant 10.png (ordre des nombres, pas des caractères)."""
    import re
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", f.name)]


def lister_images(dossier, avec_ignorees=False):
    """Images carrées du dossier (les cercles) ; les autres sont ignorées."""
    retenues, ignorees = [], []
    for f in sorted(Path(dossier).iterdir(), key=_ordre_naturel):
        if not (f.is_file() and f.suffix.lower() in EXTENSIONS):
            continue
        try:
            with Image.open(f) as im:
                carre = im.width == im.height
        except Exception:
            carre = False
        (retenues if carre else ignorees).append(f)
    return (retenues, ignorees) if avec_ignorees else retenues


def traiter(entree, sortie, couleurs=None, progression=None):
    sortie = Path(sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    fichiers = lister_images(entree)
    refs = references_dossier(fichiers)
    pcts = pourcentages_serie(fichiers)
    for i, f in enumerate(fichiers, 1):
        with Image.open(f) as img:
            taille = img.size
            res = recolorer(img, couleurs, refs, pcts.get(f))
        assert res.size == taille  # la taille est conservée
        if f.suffix.lower() in (".jpg", ".jpeg"):
            res.convert("RGB").save(sortie / f.name, quality=95, subsampling=0)
        else:
            res.save(sortie / f.name)
        if progression:
            progression(i, len(fichiers), f.name)
    return len(fichiers)
