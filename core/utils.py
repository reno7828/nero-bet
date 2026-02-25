import requests
import re


def get_nero_analysis(api_key, h_team, a_team, h_pos, a_pos):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    prompt = f"Expert foot : {h_team} vs {a_team}. Verdict court, score probable, confiance %."

    try:
        response = requests.post(url, json={
            "model": "mistral-small-latest",
            "messages": [{"role": "user", "content": prompt}]
        }, headers=headers)
        txt = response.json()['choices'][0]['message']['content']

        conf_val = 50
        nums = re.findall(r'(\d+)\s*%', txt)
        if nums: conf_val = int(nums[0])

        return {"full": txt, "conf": conf_val}
    except:
        return {"full": "Erreur API Mistral", "conf": 0}