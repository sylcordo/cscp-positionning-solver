# 1) Exécute: pip install
!pip install --quiet ortools gspread oauth2client pandas

# 2) Imports & auth
from ortools.sat.python import cp_model
import pandas as pd
import math, time
import gspread
from google.colab import auth
from google.auth import default # Import default credentials
auth.authenticate_user()
creds, project = default() # Get credentials from Colab environment
gc = gspread.authorize(creds) # Authorize gspread with these credentials

# 3) EDITE ICI: mettre l'URL de ta Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/1KfjiK2tzClSa6Gno4H3B9kia6UWODO2IQ98pppB7OsA/edit?gid=0#gid=0"  # <-- remplace par l'URL

# 4) ouvre la sheet et lit les onglets
SHEET = gc.open_by_url(SHEET_URL)
CHOR_SHEET = SHEET.worksheet("Choristes")
PARAMS_SHEET = SHEET.worksheet("Paramètres")

# 5) lecture en DataFrame
df = pd.DataFrame(CHOR_SHEET.get_all_records())
params = pd.DataFrame(PARAMS_SHEET.get_all_records())

# Add an 'ID' column if it doesn't exist, using the DataFrame index
if 'ID' not in df.columns:
   df['ID'] = df.index

# détecte colonnes musiques (commencent par 'M' ou 'm')
music_cols = [c for c in df.columns if str(c).upper().startswith("M")]
music_cols = sorted(music_cols, key=lambda s: int(''.join(filter(str.isdigit,str(s))) or 0))

# récupère rangs & capacités depuis Params (s'attend à colonnes Rang, Capacité)
# normalise en minuscules pour la clé
params.columns = [c.strip() for c in params.columns]
if 'Rang' in params.columns and ('Capacite' in params.columns or 'Capacité' in params.columns):
 cap_col = 'Capacite' if 'Capacite' in params.columns else 'Capacité'
 RANGS = params['Rang'].astype(str).str.lower().tolist()
 CAPACITES = dict(zip(params['Rang'].astype(str).str.lower(), params[cap_col].astype(int)))
else:
 raise Exception("L'onglet Params doit contenir les colonnes 'Rang' et 'Capacite' (ou 'Capacité').")

# tolérance pour bornes pupitre (modifiable)
TOLERANCE = 1

# pré-calculs
N = len(df)
pupitres = df['Pupitre'].dropna().unique().tolist()
total_by_pup = df['Pupitre'].value_counts().to_dict()

def pupitre_bounds_for_rank(rank, cap, total_by_pup, N_total, tolerance=TOLERANCE):
 bounds = {}
 for p, tot in total_by_pup.items():
   ideal = tot / N_total * cap if N_total>0 else 0
   mn = max(0, math.floor(ideal - tolerance))
   mx = min(cap, math.ceil(ideal + tolerance))
   bounds[p] = (mn, mx)
 return bounds

# stockage des résultats et violations
assign_results = []   # will keep per-person-per-music rows (old style for internal checks)
violations = []

# We'll also build a "Resultats sheet" identical to Choristes but with music columns replaced by assigned ranks.
results_sheet_df = df.copy()  # we'll add/overwrite the music columns in this df for final write

# Solveur: on résout musique par musique (plus simple et rapide)
# Objective: minimize heavy penalty on slacks + light penalty on "preference distance"
SLACK_WEIGHT = 1000  # ensure slack minimization is prioritized
PREF_WEIGHT = 1      # small weight for preference violations

try:
  # compute helpful quantities
  M = len(music_cols)
  if M == 0:
    raise ValueError("Aucune colonne musique détectée ('M1..Mn').")

  # total slots for rank across all musics = cap_r * M
  total_slots_per_rank = {r: CAPACITES.get(r, 0) * M for r in RANGS}
  # target per person per rank (rounded)
  target_per_person_rank = {}
  for r in RANGS:
    target_per_person_rank[r] = int(round(total_slots_per_rank[r] / max(1, N)))

  # Build model
  model = cp_model.CpModel()

  # variables x[(i,r,mi)] : person i assigned to rank r for music index mi
  x = {}
  for i in range(N):
    for r in RANGS:
      for mi in range(M):
        x[(i,r,mi)] = model.NewBoolVar(f"x_i{i}_r{r}_m{mi}")

  # each person exactly one rank per music
  for i in range(N):
    for mi in range(M):
      model.Add(sum(x[(i,r,mi)] for r in RANGS) == 1)

  # Read & normalize preferences per music
  pref_list_per_music = []
  for mi, mus in enumerate(music_cols):
    pref_list = []
    for i in range(N):
      raw = df.loc[i, mus]
      if pd.isna(raw):
        pref = "peu importe"
      else:
        s = str(raw).strip().lower()
        if s in ['devant','avant','front','frontale','frontier']:
          pref = 'devant'
        elif s in ['derriere','arriere','arrière','arriere','back','behind']:
          pref = 'derriere'
        elif s in ['peu importe','peuimporte','any','indifferent','indifférent','indifferent','0','none','n/a','na','']:
          pref = 'peu importe'
        elif s in ['1']:
          pref = 'derriere'
        elif s in ['0']:
          pref = 'peu importe'
        else:
          if 'dev' in s:
            pref = 'devant'
          elif 'der' in s or 'arri' in s:
            pref = 'derriere'
          else:
            pref = 'peu importe'
      pref_list.append(pref)
    pref_list_per_music.append(pref_list)

  # capacities per music & rank with slacks (store slacks in a list for objective)
  capacity_slacks = []
  capacity_slack_map = {}  # (r,mi)->slackvar for reporting
  for mi in range(M):
    for r in RANGS:
      cap = CAPACITES.get(r, 0)
      s_exceed = model.NewIntVar(0, N * M, f"slack_cap_exceed_{r}_m{mi}")
      capacity_slacks.append(s_exceed)
      capacity_slack_map[(r,mi)] = s_exceed
      model.Add(sum(x[(i,r,mi)] for i in range(N)) <= cap + s_exceed)

  # pupitre balance per rank per music with slacks
  pup_slacks = []
  for mi in range(M):
    for r in RANGS:
      cap = CAPACITES.get(r, 0)
      bounds = pupitre_bounds_for_rank(r, cap, total_by_pup, N)
      for p in pupitres:
        idxs = [i for i in range(N) if df.loc[i,'Pupitre']==p]
        if len(idxs) == 0:
          continue
        mn, mx = bounds.get(p,(0,cap))
        s_low = model.NewIntVar(0, N * M, f"slack_low_{r}_{p}_m{mi}")
        s_high = model.NewIntVar(0, N * M, f"slack_high_{r}_{p}_m{mi}")
        pup_slacks.extend([s_low, s_high])
        model.Add(sum(x[(i,r,mi)] for i in idxs) + s_low >= mn)
        model.Add(sum(x[(i,r,mi)] for i in idxs) - s_high <= mx)

  # Preference costs
  PREF_WEIGHT = 1
  pref_terms = []
  for mi in range(M):
    pref_list = pref_list_per_music[mi]
    for i in range(N):
      pref = pref_list[i]
      if pref == 'devant':
        desired_order = [r for r in ['devant','milieu','derriere'] if r in RANGS]
      elif pref == 'derriere':
        desired_order = [r for r in ['derriere','milieu','devant'] if r in RANGS]
      else:
        desired_order = [r for r in ['devant','milieu','derriere'] if r in RANGS]
      for r in RANGS:
        if r in desired_order:
          cost = desired_order.index(r)
        else:
          cost = len(desired_order)
        if cost != 0:
          pref_terms.append((PREF_WEIGHT * cost, x[(i,r,mi)]))

  # FAIRNESS: per person per rank deviation variables
  FAIR_WEIGHT = 50
  dev_vars = []
  for i in range(N):
    for r in RANGS:
      count_ir = model.NewIntVar(0, M, f"count_{i}_{r}")
      model.Add(count_ir == sum(x[(i,r,mi)] for mi in range(M)))
      target = target_per_person_rank[r]
      dev = model.NewIntVar(0, M, f"dev_{i}_{r}")
      dev_vars.append(dev)
      model.Add(count_ir - target <= dev)
      model.Add(target - count_ir <= dev)

  # Build objective: weighted sum
  SLACK_WEIGHT = 1000
  all_slacks = list(capacity_slack_map.values()) + pup_slacks
  obj_terms = []
  for s in all_slacks:
    obj_terms.append((SLACK_WEIGHT, s))
  for d in dev_vars:
    obj_terms.append((FAIR_WEIGHT, d))
  for coef, var in pref_terms:
    obj_terms.append((coef, var))
  model.Minimize(sum(coef * var for coef, var in obj_terms))

  # Solve
  solver = cp_model.CpSolver()
  solver.parameters.max_time_in_seconds = 120.0
  solver.parameters.num_search_workers = 1   # 🔒 déterminisme
  solver.parameters.random_seed = 42          # 🔒 reproductibilité


  status = solver.Solve(model)

  # Prepare outputs
  assign_results = []
  results_sheet_df = df.copy()
  for mus in music_cols:
    results_sheet_df[mus] = None

  if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    for mi, mus in enumerate(music_cols):
      assigned_for_m = []
      for i in range(N):
        assigned_rank = None
        for r in RANGS:
          if solver.Value(x[(i,r,mi)]) == 1:
            assigned_rank = r
            break
        if assigned_rank is None:
          assigned_rank = "UNASSIGNED"
        assign_results.append({'Musique': mus, 'ID': df.loc[i,'ID'], 'Nom': df.loc[i,'Nom'],
                               'Pupitre': df.loc[i,'Pupitre'], 'Rang': assigned_rank})
        assigned_for_m.append(assigned_rank)
      results_sheet_df[mus] = assigned_for_m

    # Build violations per music by summing capacity slacks for that music
    violations = []
    for mi, mus in enumerate(music_cols):
      slack_sum = 0
      for r in RANGS:
        slack_sum += int(solver.Value(capacity_slack_map[(r,mi)]))
      # optionally add pup slack aggregation if needed (skipped for simplicity)
      violations.append({'Musique': mus, 'Slack_total': int(slack_sum)})

  else:
    # fallback: mark UNASSIGNED for everything and collect empty violations
    assign_results = []
    results_sheet_df = df.copy()
    for mus in music_cols:
      results_sheet_df[mus] = ['UNASSIGNED'] * N
      for i in range(N):
        assign_results.append({'Musique': mus, 'ID': df.loc[i,'ID'], 'Nom': df.loc[i,'Nom'],
                               'Pupitre': df.loc[i,'Pupitre'], 'Rang': 'UNASSIGNED'})
    violations = [{'Musique': mus, 'Slack_total': None} for mus in music_cols]

except Exception as e:
  # Catch any unexpected error, prepare fallback outputs and surface the error to logs
  import traceback, sys
  tb = traceback.format_exc()
  print("ERREUR lors de l'optimisation globale :", str(e))
  print(tb)
  # fallback: mark UNASSIGNED for everything
  assign_results = []
  results_sheet_df = df.copy()
  for mus in music_cols:
    results_sheet_df[mus] = ['UNASSIGNED'] * N
    for i in range(N):
      assign_results.append({'Musique': mus, 'ID': df.loc[i,'ID'], 'Nom': df.loc[i,'Nom'],
                             'Pupitre': df.loc[i,'Pupitre'], 'Rang': 'UNASSIGNED'})
  violations = [{'Musique': mus, 'Slack_total': None} for mus in music_cols]


# --------- écrire les résultats dans la Google Sheet ----------
# helper pour (re)créer onglet
def write_df_to_sheet(sht_name, df_to_write):
 try:
   ws = SHEET.worksheet(sht_name)
   SHEET.del_worksheet(ws)
 except Exception:
   pass
 ws = SHEET.add_worksheet(title=sht_name, rows=str(len(df_to_write)+5), cols=str(len(df_to_write.columns)+2))
 ws.update([df_to_write.columns.values.tolist()] + df_to_write.values.tolist())

# 1) Resultats: identical structure to Choristes but with assigned ranks in M* columns
# Supprime la colonne ID si présente (demandé)
if 'ID' in results_sheet_df.columns:
    results_sheet_df = results_sheet_df.drop(columns=['ID'])

# Ajout des colonnes de comptage par choriste
results_sheet_df['count_devant'] = 0
results_sheet_df['count_milieu'] = 0
results_sheet_df['count_derriere'] = 0

for idx in range(len(results_sheet_df)):
    vals = results_sheet_df.loc[idx, music_cols].astype(str).str.lower()
    results_sheet_df.at[idx, 'count_devant'] = int((vals == 'devant').sum())
    results_sheet_df.at[idx, 'count_milieu'] = int((vals == 'milieu').sum())
    results_sheet_df.at[idx, 'count_derriere'] = int((vals == 'derrière').sum())

write_df_to_sheet('Resultats', results_sheet_df)

# 2) Stats PIVOTÉES (musiques en colonnes)
sub = pd.DataFrame(assign_results)

# Dictionnaire {indicateur: {musique: valeur}}
stats_dict = {}

for mus in music_cols:
  sub_m = sub[sub['Musique'] == mus]

  # Totaux par rang
  for r in RANGS:
    key = f'total_{r}'
    stats_dict.setdefault(key, {})[mus] = int((sub_m['Rang'] == r).sum())

  # Totaux par rang x pupitre
  for r in RANGS:
    for p in pupitres:
      key = f'count_{r}_{p}'
      stats_dict.setdefault(key, {})[mus] = int(
        ((sub_m['Rang'] == r) & (sub_m['Pupitre'] == p)).sum()
      )

  # Unassigned
  stats_dict.setdefault('unassigned', {})[mus] = int(
    (sub_m['Rang'] == 'UNASSIGNED').sum()
  )

# Construction du DataFrame pivoté
stats_df = pd.DataFrame.from_dict(stats_dict, orient='index')
stats_df.insert(0, 'Indicateur', stats_df.index)
stats_df.reset_index(drop=True, inplace=True)

write_df_to_sheet('Stats', stats_df)


viol_df = pd.DataFrame(violations)
write_df_to_sheet('Violations', viol_df)

print("Terminé ✅")
print("Regarde les onglets 'Resultats', 'Stats' et 'Violations' dans ta Google Sheet.")