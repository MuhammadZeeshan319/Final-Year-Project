# EduPath – Field & Career recommendation (integrated with the team front end)

```
edupath-app/
  backend/    Flask API: ML field ranking + rule-based career step (only Flask is needed to run)
  frontend/   Your team's React + Vite + Tailwind app, with the new /app section added
```

## Run it (two terminals)

**1. Backend** (port 5000)
```
cd backend
pip install -r requirements.txt
python app.py
```
**2. Front end** (port 5173; it forwards /api to the backend, see vite.config.js)
```
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 . Login -> questions -> ranked fields + left menu -> career.

## What was added to the front end
| File | What it does |
|---|---|
| `src/App.jsx` | Your file + the `/app` routes (your `/login` route is untouched) |
| `src/components/AppShell.jsx` | Top bar, Log out, and the left sidebar (shown only after a field is recommended) |
| `src/components/Sidebar.jsx` | Selected field + feature menu (Field recommendation, Career guidance, then "Soon" placeholders) |
| `src/components/Questionnaire.jsx` | 4-step questions that call the model |
| `src/components/RankingResults.jsx` | Ranked fields (top 6, "Show all 15") |
| `src/pages/CareerPage.jsx` | 3 follow-up questions -> one career (hard-coded if/else rules in the backend) |
| `src/pages/ComingSoon.jsx` | Placeholder page for the other modules |
| `src/constants.js` | Question lists and the sidebar feature list (add new features here) |
| `src/context/*` | Shared state. Any module can read the student's data with `useEduPath()` |
| `src/api.js` | The three backend calls |
| `src/index.css` | Your file + colour tokens appended at the bottom |
| `vite.config.js` | Your file + the `/api` proxy |

## IMPORTANT when merging into your real project
* `src/pages/Login.jsx` in this zip is only a **placeholder** so the project runs alone. **Keep your own Login.jsx.**
  In your real Login, after a successful login add:  `const navigate = useNavigate();  navigate("/app");`
* `/app` is not protected: anyone can open the URL directly. Add a login check in `AppShell.jsx` when your real auth exists.

## For teammates adding a feature
1. Build your page in `src/pages/`.
2. In `src/constants.js` change its entry in `FEATURES` from `status: "soon"` to `"ready"`, and in `src/App.jsx` replace its `ComingSoon` route with your page.
3. Read the student's data with `const { selectedField, ranking, form } = useEduPath();`
   `selectedField` is one of the 15 field names exactly as the backend returns them.

## Retraining the model (needs scikit-learn, e.g. on Google Colab)
`python train_model.py hsls.csv` -> copy the new `model_lr.json` into `backend/`.
