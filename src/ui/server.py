"""
Student & Teacher Web Application Server.
Provides an interactive evaluation UI using Python's standard library HTTP server.
Requires zero external dependencies.
"""

import http.server
import json
import logging
import os
import socketserver
import urllib.parse

from repository.question_repo import QuestionRepository
from evaluation.evaluator import AnswerEvaluationService
from evaluation.models import EvaluationRequest
from evaluation.storage import EvaluationStorage

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Answer Evaluation System — CBSE Class 9 History</title>
  <style>
    :root {
      --primary: #1e3a8a;
      --primary-light: #3b82f6;
      --accent: #d97706;
      --bg: #0f172a;
      --card-bg: #1e293b;
      --card-border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding: 24px;
    }
    .container { max-width: 1000px; margin: 0 auto; }
    header {
      text-align: center;
      margin-bottom: 28px;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--card-border);
    }
    h1 { font-size: 26px; color: #60a5fa; margin-bottom: 6px; }
    .subtitle { color: var(--text-muted); font-size: 14px; }
    .badge {
      display: inline-block;
      padding: 3px 9px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .badge-cbse { background: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid #3b82f6; }
    .badge-verified { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid #10b981; }
    .badge-unverified { background: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid #f59e0b; }
    
    .grid { display: grid; grid-template-columns: 1fr; gap: 20px; }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 22px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .card-title {
      font-size: 16px;
      font-weight: 600;
      color: #93c5fd;
      margin-bottom: 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 6px; color: var(--text-muted); }
    select, textarea, input {
      width: 100%;
      padding: 10px 12px;
      background: #0f172a;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      color: var(--text);
      font-size: 14px;
      outline: none;
      transition: border-color 0.2s;
    }
    select:focus, textarea:focus { border-color: var(--primary-light); }
    textarea { min-height: 140px; resize: vertical; line-height: 1.5; font-family: inherit; }
    
    .btn {
      background: #2563eb;
      color: white;
      border: none;
      border-radius: 8px;
      padding: 12px 20px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      width: 100%;
      margin-top: 14px;
      transition: background 0.2s;
    }
    .btn:hover { background: #1d4ed8; }
    .btn:disabled { background: #475569; cursor: not-allowed; }
    
    .question-box {
      background: #131d31;
      border-left: 4px solid #3b82f6;
      padding: 14px;
      border-radius: 6px;
      margin: 12px 0;
      font-size: 15px;
    }
    .meta-pills { display: flex; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
    .meta-pill { font-size: 12px; color: var(--text-muted); background: #0f172a; padding: 3px 8px; border-radius: 4px; }
    
    /* Results formatting */
    .result-section { display: none; margin-top: 20px; }
    .score-banner {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: #172554;
      border: 1px solid #1e40af;
      padding: 16px 20px;
      border-radius: 10px;
      margin-bottom: 18px;
    }
    .score-number { font-size: 28px; font-weight: 700; color: #60a5fa; }
    .criteria-table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }
    .criteria-table th, .criteria-table td { padding: 10px 12px; border-bottom: 1px solid var(--card-border); text-align: left; }
    .criteria-table th { background: #131d31; color: var(--text-muted); font-weight: 600; }
    
    .tag-list { display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }
    .tag-item { padding: 8px 12px; border-radius: 6px; font-size: 13px; }
    .tag-correct { background: rgba(16, 185, 129, 0.15); border-left: 3px solid #10b981; }
    .tag-missing { background: rgba(245, 158, 11, 0.15); border-left: 3px solid #f59e0b; }
    .tag-error { background: rgba(239, 68, 68, 0.15); border-left: 3px solid #ef4444; }
    
    .model-answer { background: #0b1526; border: 1px dashed #334155; padding: 14px; border-radius: 8px; font-size: 13px; margin-top: 10px; }
    .alert-review { background: rgba(245, 158, 11, 0.2); border: 1px solid #f59e0b; color: #fde68a; padding: 10px 14px; border-radius: 6px; margin-bottom: 14px; font-size: 13px; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="meta-pills" style="justify-content: center; margin-bottom: 8px;">
        <span class="badge badge-cbse">CBSE</span>
        <span class="badge badge-cbse">Class 9</span>
        <span class="badge badge-cbse">History</span>
      </div>
      <h1>AI-Powered Answer Evaluation System</h1>
      <p class="subtitle">Curriculum-aligned subjective grading with rubrics and deterministic score verification</p>
    </header>

    <div class="grid">
      <!-- Question Selection Card -->
      <div class="card">
        <div class="card-title">
          <span>1. Select Assessment Question</span>
          <span id="rubricStatusBadge" class="badge badge-verified">Verified Rubric</span>
        </div>
        <label for="questionSelect">Select a question from the CBSE question bank:</label>
        <select id="questionSelect" onchange="onQuestionChange()"></select>

        <div class="question-box" id="questionText">Loading question...</div>
        <div class="meta-pills">
          <span class="meta-pill" id="maxMarksPill">Max Marks: -</span>
          <span class="meta-pill" id="chapterPill">Chapter: -</span>
          <span class="meta-pill" id="topicPill">Topic: -</span>
          <span class="meta-pill" id="sourcePill">Source: -</span>
        </div>
      </div>

      <!-- Student Input Card -->
      <div class="card">
        <div class="card-title">2. Student Written Answer</div>
        <label for="studentAnswerInput">Type or paste the student's answer below:</label>
        <textarea id="studentAnswerInput" placeholder="Enter student response here..."></textarea>
        <button class="btn" id="evaluateBtn" onclick="submitEvaluation()">Evaluate Answer</button>
      </div>

      <!-- Results Card -->
      <div class="card result-section" id="resultsCard">
        <div class="card-title">
          <span>Evaluation Outcome</span>
          <span id="statusBadge" class="badge badge-verified">Evaluated</span>
        </div>

        <div id="reviewAlert" class="alert-review" style="display: none;">
          ⚠️ <strong>Teacher Review Required:</strong> <span id="reviewReason">Unverified rubric in use.</span>
        </div>

        <div class="score-banner">
          <div>
            <div style="font-size: 13px; color: #94a3b8;">Awarded Marks</div>
            <div class="score-number" id="awardedScore">0 / 0</div>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 13px; color: #94a3b8;">Evaluation Confidence</div>
            <div style="font-size: 18px; font-weight: 600; color: #38bdf8;" id="confidenceScore">90%</div>
          </div>
        </div>

        <div style="margin-bottom: 16px;">
          <h4 style="font-size: 14px; color: #93c5fd; margin-bottom: 4px;">Examiner Feedback</h4>
          <p id="feedbackText" style="font-size: 14px; color: #e2e8f0;"></p>
        </div>

        <div style="margin-bottom: 16px;" id="criteriaSection">
          <h4 style="font-size: 14px; color: #93c5fd; margin-bottom: 6px;">Criterion-Wise Rubric Scoring</h4>
          <table class="criteria-table">
            <thead>
              <tr>
                <th>Marking Point</th>
                <th>Max</th>
                <th>Awarded</th>
                <th>Examiner Rationale</th>
              </tr>
            </thead>
            <tbody id="criteriaTableBody"></tbody>
          </table>
        </div>

        <div style="margin-bottom: 16px;">
          <h4 style="font-size: 14px; color: #34d399; margin-bottom: 4px;">✔ Correct Historical Concepts Identified</h4>
          <div class="tag-list" id="correctTags"></div>
        </div>

        <div style="margin-bottom: 16px;" id="missingSection">
          <h4 style="font-size: 14px; color: #fbbf24; margin-bottom: 4px;">⚠ Missing Key Points</h4>
          <div class="tag-list" id="missingTags"></div>
        </div>

        <div style="margin-bottom: 16px;" id="errorSection">
          <h4 style="font-size: 14px; color: #f87171; margin-bottom: 4px;">✖ Historical Inaccuracies & Evidence-Based Corrections</h4>
          <div class="tag-list" id="errorTags"></div>
        </div>

        <div id="modelAnswerSection" style="margin-bottom: 16px;">
          <h4 style="font-size: 14px; color: #93c5fd; margin-bottom: 4px;">Verified Model Answer</h4>
          <div class="model-answer" id="modelAnswerText"></div>
        </div>

        <div>
          <h4 style="font-size: 14px; color: #60a5fa; margin-bottom: 4px;">Suggestions for Improvement</h4>
          <ul id="suggestionsList" style="padding-left: 20px; font-size: 13px; color: #cbd5e1;"></ul>
        </div>

        <div style="margin-top: 20px; padding-top: 14px; border-top: 1px solid var(--card-border); text-align: right;">
          <button class="btn" style="width: auto; background: #334155; padding: 8px 16px; margin: 0;" onclick="resetForNewAnswer()">Submit Another Answer</button>
        </div>
      </div>

      <!-- Past Submissions History Card -->
      <div class="card" id="historyCard" style="margin-top: 10px;">
        <div class="card-title">
          <span>Submission History for Selected Question</span>
          <span style="font-size: 12px; color: var(--text-muted);" id="historyCount">0 attempts recorded</span>
        </div>
        <table class="criteria-table" style="font-size: 12px;">
          <thead>
            <tr>
              <th>Evaluation ID</th>
              <th>Score</th>
              <th>Status</th>
              <th>Teacher Review</th>
            </tr>
          </thead>
          <tbody id="historyTableBody">
            <tr><td colspan="4" style="color: var(--text-muted); text-align: center;">No previous submissions recorded for this question.</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <script>
    let questionsData = [];

    async function loadQuestions() {
      try {
        const res = await fetch('/api/questions');
        questionsData = await res.json();
        const sel = document.getElementById('questionSelect');
        sel.innerHTML = '';
        questionsData.forEach((q, idx) => {
          const opt = document.createElement('option');
          opt.value = q.question_id;
          opt.textContent = `[${q.question_id}] ${q.chapter} — Max Marks: ${q.maximum_marks}`;
          sel.appendChild(opt);
        });
        onQuestionChange();
      } catch (e) {
        console.error('Failed to load questions:', e);
      }
    }

    async function onQuestionChange() {
      const qId = document.getElementById('questionSelect').value;
      const q = questionsData.find(item => item.question_id === qId);
      if (!q) return;

      document.getElementById('questionText').textContent = q.question_text;
      document.getElementById('maxMarksPill').textContent = `Max Marks: ${q.maximum_marks}`;
      document.getElementById('chapterPill').textContent = `Chapter: ${q.chapter}`;
      document.getElementById('topicPill').textContent = `Topic: ${q.topic || 'General'}`;
      document.getElementById('sourcePill').textContent = `Source: ${q.source_reference || 'NCERT'}`;

      const badge = document.getElementById('rubricStatusBadge');
      if (q.rubric_status === 'VERIFIED') {
        badge.textContent = 'Verified Rubric';
        badge.className = 'badge badge-verified';
      } else {
        badge.textContent = 'Unverified Rubric';
        badge.className = 'badge badge-unverified';
      }

      loadQuestionHistory(qId);
    }

    async function loadQuestionHistory(qId) {
      try {
        const res = await fetch(`/api/history?question_id=${encodeURIComponent(qId)}`);
        const history = await res.json();
        const tbody = document.getElementById('historyTableBody');
        const count = document.getElementById('historyCount');
        count.textContent = `${history.length} attempt(s) recorded`;
        tbody.innerHTML = '';

        if (history.length === 0) {
          tbody.innerHTML = '<tr><td colspan="4" style="color: var(--text-muted); text-align: center;">No previous submissions for this question.</td></tr>';
          return;
        }

        history.forEach(item => {
          const row = document.createElement('tr');
          const rev = item.teacher_review_required ? '<span style="color:#f59e0b;">Required</span>' : '<span style="color:#10b981;">No</span>';
          row.innerHTML = `
            <td><code>${item.evaluation_id}</code></td>
            <td><strong>${item.awarded_marks} / ${item.maximum_marks}</strong></td>
            <td><span class="badge ${item.evaluation_status === 'EVALUATED' ? 'badge-verified' : 'badge-unverified'}">${item.evaluation_status}</span></td>
            <td>${rev}</td>
          `;
          tbody.appendChild(row);
        });
      } catch (e) {
        console.error('Failed to load history:', e);
      }
    }

    function resetForNewAnswer() {
      document.getElementById('studentAnswerInput').value = '';
      document.getElementById('resultsCard').style.display = 'none';
      document.getElementById('studentAnswerInput').focus();
    }

    async function submitEvaluation() {
      const qId = document.getElementById('questionSelect').value;
      const answer = document.getElementById('studentAnswerInput').value;
      const btn = document.getElementById('evaluateBtn');
      btn.disabled = true;
      btn.textContent = 'Evaluating with AI Engine...';

      try {
        const res = await fetch('/api/evaluate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question_id: qId, student_answer: answer })
        });
        const data = await res.json();
        displayResults(data);
        loadQuestionHistory(qId);
      } catch (err) {
        alert('Evaluation failed: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.textContent = 'Evaluate Answer';
      }
    }

    function displayResults(data) {
      document.getElementById('resultsCard').style.display = 'block';
      document.getElementById('awardedScore').textContent = `${data.awarded_marks} / ${data.maximum_marks}`;
      document.getElementById('confidenceScore').textContent = `${Math.round(data.confidence_score * 100)}%`;
      document.getElementById('feedbackText').textContent = data.feedback;

      // Review alert
      const alertBox = document.getElementById('reviewAlert');
      if (data.teacher_review_required) {
        alertBox.style.display = 'block';
        document.getElementById('reviewReason').textContent = data.review_reason || 'Manual review required.';
      } else {
        alertBox.style.display = 'none';
      }

      // Status badge
      const statusBadge = document.getElementById('statusBadge');
      statusBadge.textContent = data.evaluation_status;
      if (data.evaluation_status === 'EVALUATED') {
        statusBadge.className = 'badge badge-verified';
      } else {
        statusBadge.className = 'badge badge-unverified';
      }

      // Criteria table
      const tbody = document.getElementById('criteriaTableBody');
      tbody.innerHTML = '';
      if (data.criterion_wise_marks && data.criterion_wise_marks.length > 0) {
        document.getElementById('criteriaSection').style.display = 'block';
        data.criterion_wise_marks.forEach(c => {
          const row = document.createElement('tr');
          row.innerHTML = `
            <td><strong>${c.criterion}</strong></td>
            <td>${c.maximum_marks}</td>
            <td style="color: #60a5fa; font-weight: bold;">${c.awarded_marks}</td>
            <td>${c.feedback || c.evidence || '-'}</td>
          `;
          tbody.appendChild(row);
        });
      } else {
        document.getElementById('criteriaSection').style.display = 'none';
      }

      // Correct tags
      const correctBox = document.getElementById('correctTags');
      correctBox.innerHTML = '';
      (data.correct_concepts_identified || []).forEach(pt => {
        const item = document.createElement('div');
        item.className = 'tag-item tag-correct';
        item.textContent = pt;
        correctBox.appendChild(item);
      });

      // Missing tags
      const missingBox = document.getElementById('missingTags');
      missingBox.innerHTML = '';
      if (data.missing_concepts && data.missing_concepts.length > 0) {
        document.getElementById('missingSection').style.display = 'block';
        data.missing_concepts.forEach(pt => {
          const item = document.createElement('div');
          item.className = 'tag-item tag-missing';
          item.textContent = pt;
          missingBox.appendChild(item);
        });
      } else {
        document.getElementById('missingSection').style.display = 'none';
      }

      // Errors
      const errBox = document.getElementById('errorTags');
      errBox.innerHTML = '';
      if (data.factual_errors && data.factual_errors.length > 0) {
        document.getElementById('errorSection').style.display = 'block';
        data.factual_errors.forEach(fe => {
          const item = document.createElement('div');
          item.className = 'tag-item tag-error';
          item.innerHTML = `<strong>Claim:</strong> ${fe.student_claim} <br><strong>Correction:</strong> ${fe.correction}`;
          errBox.appendChild(item);
        });
      } else {
        document.getElementById('errorSection').style.display = 'none';
      }

      // Model answer
      const modelBox = document.getElementById('modelAnswerSection');
      if (data.model_answer) {
        modelBox.style.display = 'block';
        document.getElementById('modelAnswerText').textContent = data.model_answer;
      } else {
        modelBox.style.display = 'none';
      }

      // Suggestions
      const suggBox = document.getElementById('suggestionsList');
      suggBox.innerHTML = '';
      (data.improvement_suggestions || []).forEach(s => {
        const li = document.createElement('li');
        li.textContent = s;
        suggBox.appendChild(li);
      });

      // Scroll to results
      document.getElementById('resultsCard').scrollIntoView({ behavior: 'smooth' });
    }

    window.onload = loadQuestions;
  </script>
</body>
</html>
"""


class AssessmentRequestHandler(http.server.SimpleHTTPRequestHandler):
    """
    HTTP Handler providing both static single-page application and JSON evaluation APIs.
    """

    repo = QuestionRepository()
    service = AnswerEvaluationService(repository=repo)
    storage = EvaluationStorage()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif parsed.path == "/api/questions":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            questions = [q.model_dump() for q in self.repo.list_all_questions()]
            self.wfile.write(json.dumps(questions).encode("utf-8"))
        elif parsed.path == "/api/history":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            qid = params.get("question_id", [None])[0]
            if qid:
                history = [r.model_dump() for r in self.storage.list_results_for_question(qid)]
            else:
                history = [r.model_dump() for r in self.storage.list_all_results()]
            self.wfile.write(json.dumps(history).encode("utf-8"))
        else:
            self.send_error(404, "Endpoint not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/evaluate":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(body)
                req = EvaluationRequest(
                    question_id=payload.get("question_id", ""),
                    student_answer=payload.get("student_answer", ""),
                )
                result = self.service.evaluate(req)
                self.storage.save_result(result)

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(result.model_dump_json().encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_error(404, "Endpoint not found")


def start_server(port: int = 8000):
    server_address = ("127.0.0.1", port)
    with socketserver.TCPServer(server_address, AssessmentRequestHandler) as httpd:
        print(f"\n[INFO] Assessment Web Application running at: http://127.0.0.1:{port}")
        print("[INFO] Press Ctrl+C in terminal to stop server.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down web server.")
