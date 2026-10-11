"""
EduPath backend (API only -- the React front end lives in ../frontend).
Run:  python app.py      (serves http://127.0.0.1:5000)

  POST /api/rank                    -> ML model ranks the 15 fields
  GET  /api/career-questions?field= -> follow-up questions for a field
  POST /api/career                  -> rule-based (if/else) career pick, no ML
  GET  /api/health, /api/model-info
"""
import json
from flask import Flask, jsonify, request
import predictor
import careers

app = Flask(__name__)
meta = json.load(open("model_meta.json"))

@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "fields": len(predictor.CLASSES)})

@app.post("/api/rank")
def rank():
    answers = request.get_json(force=True) or {}
    probs = predictor.predict_proba(answers)
    ranking = sorted(({"field": c, "score": round(p * 100, 1)} for c, p in zip(predictor.CLASSES, probs)),
                     key=lambda r: -r["score"])
    for i, r in enumerate(ranking, 1):
        r["rank"] = i
    return jsonify({"ranking": ranking})

@app.get("/api/career-questions")
def career_questions():
    q = careers.get_questions(request.args.get("field", ""))
    if q is None:
        return jsonify({"error": "unknown field"}), 400
    return jsonify({"questions": q})

@app.post("/api/career")
def career():
    body = request.get_json(force=True) or {}
    field, answers = body.get("field"), body.get("answers", {})
    qs = careers.get_questions(field)
    if qs is None:
        return jsonify({"error": "unknown field"}), 400
    missing = [q["id"] for q in qs if q["id"] not in answers]
    if missing:
        return jsonify({"error": f"missing answers: {missing}"}), 400
    return jsonify(careers.recommend_career(field, answers))

@app.get("/api/model-info")
def model_info():
    return jsonify({k: meta[k] for k in ("n_fields", "holdout_logreg", "cv5_logreg", "biggest_class_rate", "n_train_rows")})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
