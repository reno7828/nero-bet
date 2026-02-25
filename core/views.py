from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from .models import Profile
import requests
import re
from datetime import datetime, timedelta
from django.contrib import messages
from functools import wraps

# --- CONFIGURATION ---
LEAGUES = {
    "FL1": {"name": "Ligue 1", "flag": "🇫🇷", "country": "FRANCE"},
    "PL": {"name": "Premier League", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "country": "UK"},
    "PD": {"name": "La Liga", "flag": "🇪🇸", "country": "SPAIN"},
}


def home(request):
    return render(request, 'core/index.html')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            login(request, user)
            messages.success(request, f"Bienvenue {user.username} ! Votre compte a été créé.")
            return redirect('setup_api')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})


@login_required
def setup_api(request):
    profile = request.user.profile
    if request.method == 'POST':
        mistral_input = request.POST.get('mistral_key')
        football_input = request.POST.get('football_key')

        if mistral_input:
            profile.mistral_key = mistral_input
            messages.success(request, "Clé Mistral mise à jour.")
        if football_input:
            profile.football_key = football_input
            messages.success(request, "Clé Football mise à jour.")

        profile.save()
        return redirect('dashboard')

    return render(request, 'core/setup_api.html', {
        'has_mistral': bool(profile.mistral_key_encrypted),
        'has_football': bool(profile.football_key_encrypted),
    })


def beta_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.profile.is_beta_tester:
            return view_func(request, *args, **kwargs)
        return redirect('beta_waitlist')

    return _wrapped_view


@login_required
@beta_required
def dashboard(request):
    profile = request.user.profile
    if not profile.mistral_key or not profile.football_key:
        return redirect('setup_api')

    league_id = request.GET.get('league')
    context = {"leagues": LEAGUES, "active_league": None}

    if league_id in LEAGUES:
        context["active_league"] = LEAGUES[league_id]
        context["active_id"] = league_id
        headers = {'X-Auth-Token': profile.football_key}

        try:
            # --- FIX: RÉCUPÉRATION PAR DATE POUR NE RIEN RATER ---
            today = datetime.now().date()
            future = today + timedelta(days=10)
            date_from = today.strftime('%Y-%m-%d')
            date_to = future.strftime('%Y-%m-%d')

            # Standings (Classement)
            s_res = requests.get(f"https://api.football-data.org/v4/competitions/{league_id}/standings",
                                 headers=headers).json()

            # Matches avec filtre de date pour voir TOUS les matchs de la semaine (Lille-Nantes inclus)
            m_url = f"https://api.football-data.org/v4/competitions/{league_id}/matches?dateFrom={date_from}&dateTo={date_to}"
            m_res = requests.get(m_url, headers=headers).json()

            pos_map = {t['team']['name']: t for t in s_res['standings'][0]['table']}

            matches_data = []
            best_bets = []

            # On parcourt tous les matchs trouvés dans la plage de dates
            for m in m_res.get('matches', []):
                h_n, a_n = m['homeTeam']['name'], m['awayTeam']['name']
                h, a = pos_map.get(h_n), pos_map.get(a_n)

                if h and a:
                    date_str = m.get('utcDate')
                    dt_display = "Date inconnue"
                    if date_str:
                        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=1)
                        dt_display = dt.strftime("%d/%m à %H:%M")

                    # Analyse Mistral
                    analysis = call_mistral(profile.mistral_key, h_n, a_n, h['position'], a['position'])
                    clean_report = re.sub(r"GAGNANT:.*", "", analysis['full'], flags=re.IGNORECASE).strip()

                    match_info = {
                        "h_name": h_n, "a_name": a_n,
                        "h_rank": h['position'], "a_rank": a['position'],
                        "h_logo": m['homeTeam'].get('crest'),
                        "a_logo": m['awayTeam'].get('crest'),
                        "date": dt_display,
                        "report": clean_report,
                        "conf": analysis['conf']
                    }
                    matches_data.append(match_info)

                    if analysis['conf'] >= 75:  # Seuil Golden Ticket à 75%
                        best_bets.append({
                            "match": f"{h_n} vs {a_n}",
                            "pick": analysis['winner'],
                            "conf": analysis['conf']
                        })

            context["matches"] = matches_data
            context["best_bets"] = best_bets

        except Exception as e:
            print(f"Erreur Dashboard: {e}")
            context["error"] = "Erreur de connexion aux API."

    return render(request, 'core/dashboard.html', context)


def call_mistral(api_key, h_team, a_team, h_pos, a_pos):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    prompt = (f"Expert foot. Match: {h_team} ({h_pos}e) vs {a_team} ({a_pos}e). "
              f"Analyse tactique courte, score probable et confiance en %. "
              f"Termine par 'GAGNANT: [Nom de l'équipe]'")
    try:
        r = requests.post(url, json={
            "model": "mistral-small-latest",
            "messages": [{"role": "user", "content": prompt}]
        }, headers=headers, timeout=12)
        txt = r.json()['choices'][0]['message']['content']
        nums = re.findall(r'(\d+)\s*%', txt)
        conf = int(nums[0]) if nums else 50
        winner_match = re.search(r"GAGNANT:\s*(.*)", txt, re.IGNORECASE)
        winner = winner_match.group(1).strip() if winner_match else h_team
        return {"full": txt, "conf": conf, "winner": winner}
    except:
        return {"full": "Analyse indisponible.", "conf": 0, "winner": "N/A"}


def mentions_legales(request):
    return render(request, 'core/mentions.html')


def conditions(request):
    return render(request, 'core/conditions.html')


@login_required
def contact(request):
    if request.method == 'POST':
        messages.success(request, "Votre message a été transmis à Nerodia Lab.")
        return redirect('dashboard')
    return render(request, 'core/contact.html')


def beta_waitlist(request):
    if request.user.is_authenticated and request.user.profile.is_beta_tester:
        return redirect('dashboard')
    return render(request, 'core/beta_waitlist.html')