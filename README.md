# LCS – IDEAs for Posting

Social media planning dashboard for **Limerick Christian School** (primary & secondary), built for the Principal.
**Developer: Ed Trigueros** · Live app: https://ig-trends-limerick.streamlit.app

- **This week**: LCS Instagram numbers vs Limerick schools, three posts to publish with dates and times, best posting hours (Instagram / Facebook).
- **How we compare**: Instagram benchmark of LCS vs 6 Limerick schools and 3 leading Irish schools (followers, engagement rate, frequency, what content works, Reels vs photos, best posts).
- **Post ideas**: idea bank for primary and secondary, filtered by goal and format, built on LCS strengths.
- **Calendar**: 2026/27 school year, faith calendar and enrolment windows, with what to post for each key moment.
- **Trends**: trending sounds (auto-updated every Friday), songs climbing in Ireland, hashtag sets for schools.
- **Caption builder**: ready-to-post captions and hashtags per platform, with a quality score.

Data: `data/benchmark.json` (Instagram snapshot of Irish schools, refreshed on request), `config/edu.json` (ideas, calendar, hashtags), `data/latest.json` (weekly trends).

Everything refreshes automatically **every Friday** through GitHub Actions. The total cost is €0.

## Project structure

```
app.py                         Streamlit dashboard
ui.py / insights.py / studio.py  Design system, derived insights, Script & Copy Studio
config/insights.json           Posting times, key dates, audio→category keywords
pipeline/gemini.py             Gemini client (shared)
pipeline/collect.py            Scrapers (CreatorDB, SocialPilot, Kworb Ireland)
pipeline/analyze.py            Gemini weekly analysis
pipeline/run_weekly.py         Orchestrator: collect → analyse → save
config/hashtags.json           Curated hashtag sets + Limerick region (edit freely)
data/latest.json               Current week's data (read by the app)
data/history/YYYY-MM-DD.json   Weekly snapshots (week selector + week-over-week)
.github/workflows/weekly-update.yml   Automatic weekly update
```

## Setup (about 15 minutes)

1. **Create the GitHub repo.** Make a new repository (for example `ig-trends-dashboard`) and upload all of these files, including the hidden `.github` and `.streamlit` folders.
2. **Get a free Gemini key.** Go to https://aistudio.google.com/apikey and create an API key.
3. **Add the key to GitHub.** Open the repo, then go to *Settings → Secrets and variables → Actions → New repository secret*. Use the name `GEMINI_API_KEY` and paste your key as the value.
   - Optional: under the *Variables* tab, add `GEMINI_MODEL` to change the model. The default is `gemini-2.5-flash`.
4. **Allow the workflow to push.** Go to *Settings → Actions → General → Workflow permissions* and select **Read and write permissions**.
5. **Run the first update.** In the *Actions* tab, open **Weekly Instagram trends update** and click **Run workflow**. Check the log to confirm that every source says `updated`.
6. **Deploy for free.** Go to https://share.streamlit.io, choose *Create app*, pick your repo, and set the main file to `app.py`. You'll get a public link.
   Every time the workflow commits new data, Streamlit Cloud redeploys the app automatically.
7. **Turn on the AI Studio.** In Streamlit Cloud, open your app, go to *Settings → Secrets*, and paste:
   ```toml
   GEMINI_API_KEY = "your-key"
   ```
   Without it, the Studio still works in template mode.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
# refresh data manually (needs internet; GEMINI_API_KEY optional)
GEMINI_API_KEY=xxx python -m pipeline.run_weekly
```

## How the update stays reliable

- If a source changes its layout or fails, the pipeline **keeps last week's data for that source** and reports it under *Sources → status*. The dashboard never breaks.
- If Gemini fails or the key is missing, the previous analysis stays in place.
- If a scraper stops parsing, adjust the matching function in `pipeline/collect.py`. Each source has its own function.

## Notes and limits

- Instagram has no public "trending" API. Audio data comes from public weekly charts (CreatorDB, SocialPilot), and the Ireland view uses Spotify streaming (Kworb) as a proxy.
- Hashtag sets are curated rather than measured. To get real post volumes, an Apify hashtag scraper (paid, low cost) can be added to `collect.py`.
- Many major-label songs are restricted for Business accounts, so always check availability in the app before filming.
- Respect each source's terms of use. The pipeline makes 3 requests per week.

## Weekly update (every Monday)

GitHub Actions runs `pipeline/run_weekly.py` every Monday at 06:23 UTC:
- trending sounds and Irish chart: always updated;
- Instagram numbers for LCS and every school in `data/benchmark.json`: appended to `data/ig_history.csv`.
  Instagram blocks anonymous requests from GitHub's servers, so this step needs the official API connection below.

## Connect the Instagram API (free, one-time, done by the LCS account owner)

1. Make sure the LCS Instagram is a **Professional (Business)** account linked to the LCS **Facebook Page**.
2. At https://developers.facebook.com create an app (type *Business*) and add the **Instagram Graph API** product.
3. In the Graph API Explorer, generate a token with `instagram_basic`, `instagram_manage_insights`, `pages_show_list`, `pages_read_engagement`,
   then exchange it for a **long-lived token** (60 days; renew it before it expires).
4. Find the Instagram business account ID: `GET /me/accounts?fields=instagram_business_account`.
5. In GitHub, go to *Settings → Secrets and variables → Actions* and add `IG_ACCESS_TOKEN` and `IG_USER_ID`.

From then on, every Monday the dashboard refreshes automatically:
- **Competitors (Business Discovery):** followers, posts, average likes + comments and Reels share for every school.
- **LCS insights:** reach, profile visits, website clicks, follower cities/ages and per-post reach, saves and shares.
