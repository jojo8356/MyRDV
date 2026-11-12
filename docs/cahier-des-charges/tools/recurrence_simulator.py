#!/usr/bin/env python3
"""
recurrence_simulator.py — Implémentation de référence (normative) du moteur de
rendez-vous récurrents hebdomadaires décrit dans le cahier des charges MyRDV.

Ce script n'a AUCUNE dépendance externe (Python >= 3.9, zoneinfo).
Il sert de :
  1. spécification exécutable (les règles R1..R12 du document 06 sont codées ici) ;
  2. oracle de test : `--vectors` produit les jeux de tests du document 06 ;
  3. brique de prototypage : la même sémantique doit être portée côté serveur.

Usage :
    python3 recurrence_simulator.py --demo
    python3 recurrence_simulator.py --vectors
    python3 recurrence_simulator.py --self-test

Codes de sortie : 0 = OK, 2 = violation d'une règle métier (SER_xxx).
"""

from __future__ import annotations

import calendar
import json
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable, Optional
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# Constantes / garde-fous (paramétrables par plan tarifaire — voir doc 06 §9)
# ---------------------------------------------------------------------------
MIN_INTERVAL_WEEKS = 1
MAX_INTERVAL_WEEKS = 8
MAX_OCCURRENCES_HARD = 104          # plafond absolu, tous plans confondus
MAX_HORIZON_MONTHS_HARD = 12        # aucun RDV matérialisé au-delà de 12 mois
DEFAULT_HORIZON_DAYS = 90           # fenêtre glissante pour les séries SANS fin (NEVER)
MIN_LEAD_TIME_HOURS = 2             # délai minimum avant la 1re occurrence
DEFAULT_CONFLICT_SKIP_BUDGET = 5    # nb max d'occurrences ignorées pour conflit
MAX_CONSECUTIVE_CONFLICT_SKIPS = 3  # garde-fou anti-boucle infinie


class SeriesError(Exception):
    """Erreur métier. `code` est stable et destiné à l'API (cf. doc 07 §8)."""

    def __init__(self, code: str, message: str, details: Optional[dict] = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.details = details or {}


# ---------------------------------------------------------------------------
# Modèle de la règle de récurrence (sous-ensemble RFC 5545 + extensions MyRDV)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class WeeklyRule:
    """FREQ=WEEKLY ; INTERVAL=nW ; BYDAY=MO,TU,..."""

    by_weekday: tuple[int, ...]           # 0 = lundi … 6 = dimanche
    interval: int = 1

    def to_rrule(self) -> str:
        codes = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
        return f"FREQ=WEEKLY;INTERVAL={self.interval};BYDAY={','.join(codes[d] for d in sorted(self.by_weekday))}"


@dataclass
class EndCondition:
    """
    mode = AFTER_COUNT | ON_DATE | AFTER_DURATION | NEVER
      - AFTER_COUNT   : `count` occurrences planifiées (1..MAX_OCCURRENCES)
      - ON_DATE       : dernière occurrence <= `until` (incluse)
      - AFTER_DURATION: `months` ou `weeks` à partir de la date de début,
                        date de fin calculée puis traitée comme ON_DATE
      - NEVER         : limité par les garde-fous (horizon, plafond du plan)
    """

    mode: str = "AFTER_COUNT"
    count: Optional[int] = None
    until: Optional[date] = None
    months: Optional[int] = None
    weeks: Optional[int] = None


@dataclass
class SeriesSpec:
    series_id: str
    start_date: date
    start_time: time
    duration_min: int
    timezone: str
    rule: WeeklyRule
    end: EndCondition
    # Options avancées
    pre_buffer_min: int = 0
    post_buffer_min: int = 0
    conflict_policy: str = "SKIP"     # FAIL | SKIP | SHIFT_SAME_DAY
    shift_tolerance_min: int = 240    # ±4 h pour SHIFT_SAME_DAY
    date_shift_free: frozenset[date] = frozenset()   # jours fériés / congés
    date_shift_policy: str = "SKIP"   # SKIP | SHIFT_FORWARD | KEEP
    rdates: tuple[date, ...] = ()
    exdates: tuple[date, ...] = ()
    horizon_days: int = DEFAULT_HORIZON_DAYS
    conflict_skip_budget: int = DEFAULT_CONFLICT_SKIP_BUDGET
    max_count_plan: int = MAX_OCCURRENCES_HARD


@dataclass
class Occurrence:
    index: int                  # 1-based, suite planifiée
    local_start: datetime        # heure murale, tz de la série
    local_end: datetime
    start_utc: datetime
    end_utc: datetime
    origin: str                  # RULE | RDATE
    shifted_min: int = 0
    status: str = "SCHEDULED"

    def key(self, series_id: str) -> str:
        """Clé d'occurrence stable et idempotente (doc 06 §2)."""
        return f"{series_id}@{self.local_start.strftime('%Y%m%dT%H%M')}"


@dataclass
class GenerationReport:
    occurrences: list[Occurrence] = field(default_factory=list)
    skipped_conflict: list[date] = field(default_factory=list)
    skipped_blackout: list[date] = field(default_factory=list)
    removed_exdate: list[date] = field(default_factory=list)
    limit_reason: str = ""
    effective_until: Optional[date] = None
    warnings: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.occurrences)


# ---------------------------------------------------------------------------
# Arithmétique de calendrier
# ---------------------------------------------------------------------------
def add_months(d: date, months: int) -> date:
    """Ajout de mois avec écrêtage au dernier jour du mois (R5).

    2026-01-31 + 3 mois -> 2026-04-30 ; 2026-11-16 + 3 mois -> 2027-02-16.
    """
    if months == 0:
        return d
    total = (d.year * 12 + (d.month - 1)) + months
    year, month0 = divmod(total, 12)
    month = month0 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def resolve_local(d: date, t: time, tz: ZoneInfo, gap_policy: str = "SHIFT_TO_FIRST_VALID",
                  ambiguity_policy: str = "EARLIER") -> datetime:
    """Résolution d'une heure murale inexistante (DST) ou ambiguë (R6).

    - trou (spring forward) : 02:30 n'existe pas -> 03:00 (SHIFT_TO_FIRST_VALID, R-06)
    - doublon (fall back)   : 02:30 existe 2x -> premier passage (EARLIER)
    """
    naive = datetime.combine(d, t)
    first = naive.replace(tzinfo=tz, fold=0)
    second = naive.replace(tzinfo=tz, fold=1)
    valid_first = first.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) == naive
    valid_second = second.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) == naive

    if not valid_first and not valid_second:  # heure inexistante
        if gap_policy == "KEEP_DURATION":
            return naive.replace(tzinfo=tz, fold=0)  # toléré, normalisé plus bas
        shift = 0
        while shift <= 180:
            cand = naive + timedelta(minutes=shift)
            c = cand.replace(tzinfo=tz, fold=0)
            if c.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) == cand:
                return c
            shift += 1
        raise SeriesError("SER_011_INVALID_LOCAL_TIME", f"Heure locale non résoluble : {naive}")
    if valid_first and valid_second:  # ambiguïté
        return first if ambiguity_policy == "EARLIER" else second
    return first if valid_first else second


# ---------------------------------------------------------------------------
# Moteur
# ---------------------------------------------------------------------------
def validate(spec: SeriesSpec) -> None:
    r = spec.rule
    if not r.by_weekday:
        raise SeriesError("SER_001_NO_WEEKDAY", "Sélectionnez au moins un jour de la semaine.")
    if any(d < 0 or d > 6 for d in r.by_weekday):
        raise SeriesError("SER_002_BAD_WEEKDAY", "Jour de semaine invalide (0..6).")
    if not (MIN_INTERVAL_WEEKS <= r.interval <= MAX_INTERVAL_WEEKS):
        raise SeriesError("SER_003_BAD_INTERVAL",
                          f"L'intervalle doit être compris entre {MIN_INTERVAL_WEEKS} et "
                          f"{MAX_INTERVAL_WEEKS} semaines.")
    if spec.duration_min <= 0 or spec.duration_min > 480:
        raise SeriesError("SER_004_BAD_DURATION", "Durée invalide (1..480 min).")
    if spec.start_date.weekday() not in r.by_weekday:
        raise SeriesError("SER_005_START_WEEKDAY_MISMATCH",
                          "La date de début ne correspond à aucun jour sélectionné.",
                          {"start_weekday": spec.start_date.weekday()})
    e = spec.end
    if e.mode == "AFTER_COUNT":
        if e.count is None or e.count < 1:
            raise SeriesError("SER_006_BAD_COUNT", "Le nombre de répétitions doit être >= 1.")
        if e.count > spec.max_count_plan:
            raise SeriesError("SER_007_COUNT_OVER_CAP",
                              f"Votre offre autorise au maximum {spec.max_count_plan} occurrences par série.",
                              {"max": spec.max_count_plan, "requested": e.count})
    elif e.mode == "ON_DATE":
        if e.until is None or e.until < spec.start_date:
            raise SeriesError("SER_008_BAD_UNTIL", "La date de fin doit être postérieure au début.")
    elif e.mode == "AFTER_DURATION":
        if not e.months and not e.weeks:
            raise SeriesError("SER_009_BAD_DURATION_END", "Durée de répétition manquante.")
        if (e.months or 0) > MAX_HORIZON_MONTHS_HARD or (e.weeks or 0) > 52:
            raise SeriesError("SER_010_DURATION_OVER_CAP",
                              f"La durée maximale d'une série est de {MAX_HORIZON_MONTHS_HARD} mois.")
    elif e.mode != "NEVER":
        raise SeriesError("SER_012_BAD_END_MODE", f"Mode de fin inconnu : {e.mode}")

    if spec.conflict_policy not in ("FAIL", "SKIP", "SHIFT_SAME_DAY"):
        raise SeriesError("SER_013_BAD_CONFLICT_POLICY", "Politique de conflit inconnue.")
    if spec.date_shift_policy not in ("SKIP", "SHIFT_FORWARD", "KEEP"):
        raise SeriesError("SER_014_BAD_SHIFT_POLICY", "Politique de jour férié inconnue.")


def effective_end(spec: SeriesSpec, now: Optional[datetime] = None) -> tuple[Optional[date], str]:
    """Date de fin effective (R1/R2).

    - une série à fin explicite (count / until / durée) est matérialisée jusqu'à sa
      borne réelle, plafonnée par MAX_HORIZON_MONTHS_HARD ;
    - une série « sans fin » est plafonnée par la fenêtre glissante de matérialisation
      (DEFAULT_HORIZON_DAYS), réévaluée à chaque réveil du planificateur.
    """
    tz = ZoneInfo(spec.timezone)
    now = now or datetime.now(tz)
    hard_end = add_months(spec.start_date, MAX_HORIZON_MONTHS_HARD)
    candidates: list[tuple[date, str]] = [(hard_end, "SAFETY_BOUND_12M")]

    e = spec.end
    if e.mode == "ON_DATE" and e.until:
        candidates.append((e.until, "RULE_UNTIL"))
    elif e.mode == "AFTER_DURATION":
        if e.months:
            candidates.append((add_months(spec.start_date, e.months), "RULE_DURATION_MONTHS"))
        if e.weeks:
            candidates.append((spec.start_date + timedelta(weeks=e.weeks), "RULE_DURATION_WEEKS"))
    elif e.mode == "NEVER":
        candidates.append((now.date() + timedelta(days=spec.horizon_days),
                           "MATERIALIZATION_WINDOW"))

    return min(candidates, key=lambda c: (c[0], c[1]))


def _candidates(spec: SeriesSpec, until: Optional[date], max_candidates: int = 2000) -> Iterable[date]:
    """Itère les dates candidates de la règle (avant exceptions). (R3)"""
    r = spec.rule
    week_start = spec.start_date - timedelta(days=spec.start_date.weekday())
    produced = 0
    if spec.end.mode == "NEVER" and until is None:
        raise SeriesError("SER_015_NEVER_WITHOUT_CAP", "Série sans fin refusée sans plafond.")
    hard_stop = until or add_months(spec.start_date, MAX_HORIZON_MONTHS_HARD)
    while True:
        for wd in sorted(r.by_weekday):
            d = week_start + timedelta(days=wd)
            if d < spec.start_date:
                continue
            if d > hard_stop:
                return
            yield d
            produced += 1
            if produced >= max_candidates:
                return
        week_start += timedelta(weeks=r.interval)


def _busy_overlaps(spec: SeriesSpec, busy: list[tuple[datetime, datetime]],
                   s_utc: datetime, e_utc: datetime) -> bool:
    footprint_s = s_utc - timedelta(minutes=spec.pre_buffer_min)
    footprint_e = e_utc + timedelta(minutes=spec.post_buffer_min)
    return any(footprint_s < b_end and footprint_e > b_start for b_start, b_end in busy)


def generate(spec: SeriesSpec, busy: Optional[list[tuple[datetime, datetime]]] = None,
             now: Optional[datetime] = None) -> GenerationReport:
    """Génère les occurrences d'une série. Sémantique normative : doc 06 §6."""
    validate(spec)
    busy = busy or []
    tz = ZoneInfo(spec.timezone)
    report = GenerationReport()
    end_date, reason = effective_end(spec, now)
    report.effective_until = end_date
    report.limit_reason = reason

    # Garde-fou R8 : délai minimum avant la première occurrence
    first_start = resolve_local(spec.start_date, spec.start_time, tz)
    if now is not None:
        delta_h = (first_start - now.astimezone(tz)).total_seconds() / 3600
        if delta_h < MIN_LEAD_TIME_HOURS:
            raise SeriesError("SER_016_LEAD_TIME",
                              f"Le premier rendez-vous doit être à plus de {MIN_LEAD_TIME_HOURS} h.")

    excluded = set(spec.exdates)
    rule_dates = [d for d in _candidates(spec, end_date) if d not in excluded]
    all_dates = sorted(set(rule_dates) | {d for d in spec.rdates
                                          if d not in excluded and d >= spec.start_date})
    report.removed_exdate = sorted(excluded)

    # --- Exception DATES : jours fériés / congés (R7) ---
    normalized: list[date] = []
    taken: set[date] = set()
    for d in all_dates:
        if d not in spec.date_shift_free:
            normalized.append(d)
            taken.add(d)
            continue
        if spec.date_shift_policy == "KEEP":
            normalized.append(d)
            taken.add(d)
        elif spec.date_shift_policy == "SKIP":
            report.skipped_blackout.append(d)
        else:  # SHIFT_FORWARD : premier jour disponible suivant
            nd, guard = d + timedelta(days=1), 0
            while (nd in spec.date_shift_free or nd in excluded or nd in taken) and guard < 60:
                nd += timedelta(days=1)
                guard += 1
            if nd > end_date or guard >= 60:
                report.skipped_blackout.append(d)
                continue
            normalized.append(nd)
            taken.add(nd)

    # --- Placement + politique de conflit (R4) ---
    conflict_skips = consecutive_skips = 0
    for d in normalized:
        if d > end_date:
            continue
        local_start = resolve_local(d, spec.start_time, tz)
        local_end = local_start + timedelta(minutes=spec.duration_min)
        s_utc, e_utc = local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)
        shifted = 0

        if _busy_overlaps(spec, busy, s_utc, e_utc):
            if spec.conflict_policy == "FAIL":
                raise SeriesError("SER_017_SLOT_CONFLICT",
                                  "Au moins une occurrence est en conflit : série refusée (tout ou rien).",
                                  {"date": d.isoformat()})
            if spec.conflict_policy == "SKIP":
                conflict_skips += 1
                consecutive_skips += 1
                report.skipped_conflict.append(d)
                if conflict_skips > spec.conflict_skip_budget:
                    raise SeriesError("SER_018_CONFLICT_BUDGET",
                                      "Trop de conflits : réduisez la portée de la série.",
                                      {"budget": spec.conflict_skip_budget, "date": d.isoformat()})
                if consecutive_skips > MAX_CONSECUTIVE_CONFLICT_SKIPS:
                    raise SeriesError("SER_019_CONSECUTIVE_CONFLICTS",
                                      "Trop de créneaux consécutifs indisponibles.",
                                      {"date": d.isoformat()})
                continue
            # SHIFT_SAME_DAY : même jour, ±15 min par pas, tolérance configurable
            placed = False
            for delta in range(15, spec.shift_tolerance_min + 1, 15):
                for sign in (1, -1):
                    cand = local_start + timedelta(minutes=sign * delta)
                    if cand.date() != d:
                        continue
                    c_end = cand + timedelta(minutes=spec.duration_min)
                    c_s, c_e = cand.astimezone(timezone.utc), c_end.astimezone(timezone.utc)
                    if not _busy_overlaps(spec, busy, c_s, c_e):
                        local_start, local_end, s_utc, e_utc = cand, c_end, c_s, c_e
                        shifted, placed = sign * delta, True
                        break
                if placed:
                    break
            if not placed:
                report.skipped_conflict.append(d)
                conflict_skips += 1
                if conflict_skips > spec.conflict_skip_budget:
                    raise SeriesError("SER_018_CONFLICT_BUDGET",
                                      "Trop de conflits : réduisez la portée de la série.",
                                      {"budget": spec.conflict_skip_budget, "date": d.isoformat()})
                continue

        consecutive_skips = 0
        report.occurrences.append(Occurrence(
            len(report.occurrences) + 1, local_start, local_end, s_utc, e_utc,
            "RDATE" if d in spec.rdates else "RULE", shifted))
        if spec.end.mode == "AFTER_COUNT" and report.count >= (spec.end.count or 0):
            break

    if report.occurrences:
        report.effective_until = report.occurrences[-1].local_start.date()
        report.limit_reason = "LAST_OCCURRENCE"
    if spec.end.mode == "AFTER_COUNT" and report.count < (spec.end.count or 0):
        report.warnings.append(
            f"Seules {report.count} occurrences ont pu être planifiées sur {spec.end.count} "
            f"demandées (borne de fin / conflits).")
    return report


# ---------------------------------------------------------------------------
# Affichage / jeux de tests
# ---------------------------------------------------------------------------
def _fmt(r: GenerationReport) -> str:
    lines = [f"fin effective = {r.effective_until} (motif : {r.limit_reason})",
             f"occurrences = {r.count}"]
    for o in r.occurrences:
        extra = f" (+{o.shifted_min} min)" if o.shifted_min else ""
        lines.append(f"  #{o.index:02d} {o.local_start:%Y-%m-%d %H:%M} → {o.local_end:%H:%M} "
                     f"[{o.start_utc:%H:%M}Z]{extra}")
    if r.skipped_conflict:
        lines.append("conflits ignorés : " + ", ".join(d.isoformat() for d in r.skipped_conflict))
    if r.skipped_blackout:
        lines.append(f"jours fériés retirés ({len(r.skipped_blackout)})")
    for w in r.warnings:
        lines.append("⚠ " + w)
    return "\n".join(lines)


def demo() -> int:
    print("=== Exemple de l'énoncé : 1 fois par semaine, 3 mois ===")
    spec = SeriesSpec(
        series_id="demo-1", start_date=date(2026, 11, 16), start_time=time(9, 0),
        duration_min=60, timezone="Europe/Paris",
        rule=WeeklyRule(by_weekday=(0,)), end=EndCondition(mode="AFTER_DURATION", months=3),
    )
    print(_fmt(generate(spec)))

    print("\n=== Même série, mardi et jeudi, toutes les 2 semaines, 8 occurrences ===")
    spec2 = SeriesSpec(
        series_id="demo-2", start_date=date(2026, 11, 17), start_time=time(14, 30),
        duration_min=45, timezone="Europe/Paris",
        rule=WeeklyRule(by_weekday=(1, 3), interval=2),
        end=EndCondition(mode="AFTER_COUNT", count=8),
    )
    print(_fmt(generate(spec2)))
    return 0


def vectors() -> int:
    """Produit les vecteurs de test au format JSON (annexe vecteurs-test-recurrence.json)."""
    out = []

    def case(name, spec, busy=None):
        rep = generate(spec, busy=busy)
        out.append({
            "case": name,
            "rrule": spec.rule.to_rrule(),
            "start": f"{spec.start_date} {spec.start_time:%H:%M}",
            "end_mode": spec.end.mode,
            "end_params": {k: (v.isoformat() if hasattr(v, "isoformat") else v)
                           for k, v in vars(spec.end).items()
                           if k != "mode" and v is not None},
            "effective_until": str(rep.effective_until),
            "limit_reason": rep.limit_reason,
            "count": rep.count,
            "dates": [o.local_start.strftime("%Y-%m-%dT%H:%M") for o in rep.occurrences],
        })

    case("3 mois hebdo lundi 09:00",
         SeriesSpec("t1", date(2026, 11, 16), time(9, 0), 60, "Europe/Paris",
                    WeeklyRule((0,)), EndCondition("AFTER_DURATION", months=3)))
    case("count 5 bi-hebdo",
         SeriesSpec("t2", date(2026, 11, 17), time(14, 30), 45, "Europe/Paris",
                    WeeklyRule((1,), 2), EndCondition("AFTER_COUNT", count=5)))
    case("until incluse",
         SeriesSpec("t3", date(2026, 11, 16), time(10, 0), 60, "Europe/Paris",
                    WeeklyRule((0,)), EndCondition("ON_DATE", until=date(2026, 12, 14))))
    case("multi-jours lun+mer+ven",
         SeriesSpec("t4", date(2026, 11, 16), time(8, 0), 60, "Europe/Paris",
                    WeeklyRule((0, 2, 4)), EndCondition("AFTER_COUNT", count=7)))
    case("DST printemps Europe/Paris 02:30",
         SeriesSpec("t5", date(2027, 3, 21), time(2, 30), 60, "Europe/Paris",
                    WeeklyRule((6,)), EndCondition("AFTER_COUNT", count=4)))
    case("DST automne Europe/Paris 02:30",
         SeriesSpec("t6", date(2026, 10, 18), time(2, 30), 60, "Europe/Paris",
                    WeeklyRule((6,)), EndCondition("AFTER_COUNT", count=4)))
    case("fin de mois écourtée",
         SeriesSpec("t7", date(2026, 1, 31), time(11, 0), 30, "Europe/Paris",
                    WeeklyRule((5,)), EndCondition("AFTER_DURATION", months=1)))
    case("conflit SKIP",
         SeriesSpec("t8", date(2026, 11, 16), time(9, 0), 60, "Europe/Paris",
                    WeeklyRule((0,)), EndCondition("AFTER_COUNT", count=4)),
         busy=[(datetime(2026, 11, 23, 8, 0, tzinfo=timezone.utc),
                datetime(2026, 11, 23, 9, 0, tzinfo=timezone.utc))])
    case("conflit SHIFT_SAME_DAY",
         SeriesSpec("t9", date(2026, 11, 16), time(9, 0), 60, "Europe/Paris",
                    WeeklyRule((0,)), EndCondition("AFTER_COUNT", count=3),
                    conflict_policy="SHIFT_SAME_DAY"),
         busy=[(datetime(2026, 11, 16, 8, 0, tzinfo=timezone.utc),
                datetime(2026, 11, 16, 9, 0, tzinfo=timezone.utc))])
    case("jour férié SHIFT_FORWARD",
         SeriesSpec("t10", date(2026, 12, 21), time(9, 0), 60, "Europe/Paris",
                    WeeklyRule((0,)), EndCondition("AFTER_COUNT", count=3),
                    date_shift_free=frozenset({date(2026, 12, 28)}),
                    date_shift_policy="SHIFT_FORWARD"))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def self_test() -> int:
    """Invariants (propriétés) vérifiés sur un échantillon aléatoire déterministe."""
    import random
    rnd = random.Random(20261112)
    zones = ["Europe/Paris", "America/Montreal", "America/Toronto", "Asia/Tokyo", "UTC"]
    checked = 0
    for _ in range(400):
        tz = rnd.choice(zones)
        weekdays = tuple(sorted(rnd.sample(range(7), rnd.randint(1, 3))))
        start = date(2026, rnd.randint(1, 6), rnd.randint(1, 28))
        # aligner la date de début sur un jour sélectionné (contrainte SER_005)
        delta = (weekdays[0] - start.weekday()) % 7
        start = start + timedelta(days=delta)
        spec = SeriesSpec(
            "p", start, time(rnd.choice([0, 2, 8, 9, 14, 23]), rnd.choice([0, 15, 30, 45])),
            rnd.choice([15, 30, 45, 60, 90]), tz,
            WeeklyRule(weekdays, rnd.randint(1, 4)),
            rnd.choice([EndCondition("AFTER_COUNT", count=rnd.randint(1, 60)),
                        EndCondition("AFTER_DURATION", months=rnd.randint(1, 6)),
                        EndCondition("ON_DATE", until=start + timedelta(days=rnd.randint(7, 300)))]),
        )
        rep = generate(spec)
        starts = [o.start_utc for o in rep.occurrences]
        assert starts == sorted(starts), "ordre chronologique"
        assert len(set(starts)) == len(starts), "pas de doublon"
        assert all(o.local_end > o.local_start for o in rep.occurrences), "durée positive"
        assert all(o.local_start.date() <= rep.effective_until for o in rep.occurrences), "borne de fin"
        if spec.end.mode == "AFTER_COUNT":
            assert rep.count <= spec.end.count, "count respecté"
        # idempotence : deux exécutions identiques -> même résultat
        rep2 = generate(spec)
        assert [o.key(spec.series_id) for o in rep.occurrences] == \
               [o.key(spec.series_id) for o in rep2.occurrences], "idempotence"
        # intervalle : au moins `interval` semaines entre deux semaines utilisées
        weeks = sorted({(o.local_start.date().toordinal() - 1) // 7 for o in rep.occurrences})
        steps = [b - a for a, b in zip(weeks, weeks[1:])]
        assert all(s % spec.rule.interval == 0 for s in steps), "intervalle respecté"
        checked += 1
    print(f"OK — {checked} séries aléatoires, 6 invariants vérifiés.")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "--demo"
    try:
        if cmd == "--demo":
            sys.exit(demo())
        if cmd == "--vectors":
            sys.exit(vectors())
        if cmd == "--self-test":
            sys.exit(self_test())
        print(__doc__)
        sys.exit(1)
    except SeriesError as exc:
        print(f"Erreur métier {exc.code} — {exc.message}", file=sys.stderr)
        sys.exit(2)
