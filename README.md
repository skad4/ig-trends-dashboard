# LCS – IDEAs for Posting

Instagram trends intelligence for Limerick & Ireland · **Developer: Ed Trigueros**

Live app: https://ig-trends-limerick.streamlit.app

A free, self-updating, "Creative Center"-style dashboard for Instagram:

- **Trending Audio**: weekly Reels sounds (Heat score, momentum, reel counts), the Spotify Ireland weekly chart as a regional proxy, and "best for your business" use cases.
- **Hashtags**: curated sets for 9 categories (Education first) by reach tier, the AI's picks for the week, and a one-click hashtag set builder.
- **Limerick Local**: Limerick plus a 50 km radius (Ennis, Shannon, Nenagh, Adare...), with local and seasonal tags and ready-to-use copies.
- **Overview**: AI weekly summary and an **Opportunity matrix** (Heat vs saturation).
- **What to Post**: a ready brief per category, the next best posting slots (Irish time), a best-time heatmap (Buffer 2026 data), a downloadable 5-post weekly plan and upcoming key dates.
- **Video Examples**: real Reels that use this week's trending sounds, matched to each category and embedded in the page.
- **Script & Copy Studio**: type an idea and get hooks, a shot-by-shot script or carousel slides, a caption, hashtags, an audio pick and the best time to post. Includes a **Caption checker** that scores 0–100.
- Design uses the Limerick Christian School palette (navy `#0b3767`, gold `#fdbc59`, burgundy `#530100`) with EB Garamond + Manrope.

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
