#!/usr/bin/env python3
"""
Comprehensive Data Science Interview Q&A Scraper & Database Seeder
==================================================================
Sources:
  1. github.com/alexeygrigorev/data-science-interviews   (theory.md)
  2. github.com/youssefHosni/Data-Science-Interview-Questions-Answers  (5 topic files)
  3. github.com/iamtodor/data-science-interview-questions-and-answers  (README.md)
  4. github.com/kojino/120-Data-Science-Interview-Questions            (7 topic files)
  5. roadmap.sh/questions/data-science                                  (web page)
  6. Hand-curated supplemental Q&As (SQL, Python, Stats, DL, NLP, MLOps)
"""

import sys, os, re, json, time, hashlib
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import requests
from bs4 import BeautifulSoup
from database.connection import SessionLocal
from crud.questions import create_question
from schemas.question import QuestionCreate
from services.keyword_extractor import extract_keywords

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

ROLE = "Data Scientist"
REQUEST_DELAY = 1.2  # polite delay between requests (seconds)

DIFFICULTY_EMOJI_MAP = {
    "👶":   "easy",
    "⭐️":  "medium",
    "‍⭐️": "medium",
    "🚀":   "expert",
}

DIFFICULTY_TO_LEVEL = {
    "easy":   "fresher",
    "medium": "junior",
    "hard":   "junior",
    "expert": "senior",
}

DIFFICULTY_TO_QTYPE = {
    "easy":   "Theoretical",
    "medium": "Technical",
    "hard":   "Technical",
    "expert": "Technical",
}

TOPIC_MAP = {
    "supervised machine learning":         "Machine Learning",
    "linear regression":                   "Machine Learning",
    "validation":                          "Machine Learning",
    "classification":                      "Machine Learning",
    "regularization":                      "Machine Learning",
    "feature selection":                   "Machine Learning",
    "feature engineering":                 "Machine Learning",
    "decision trees":                      "Machine Learning",
    "decision tree":                       "Machine Learning",
    "random forest":                       "Machine Learning",
    "gradient boosting":                   "Machine Learning",
    "ensemble":                            "Machine Learning",
    "parameter tuning":                    "Machine Learning",
    "hyperparameter":                      "Machine Learning",
    "neural networks":                     "Deep Learning",
    "neural network":                      "Deep Learning",
    "optimization in neural networks":     "Deep Learning",
    "optimization":                        "Deep Learning",
    "neural networks for computer vision": "Deep Learning",
    "computer vision":                     "Deep Learning",
    "cnn":                                 "Deep Learning",
    "convolutional":                       "Deep Learning",
    "rnn":                                 "Deep Learning",
    "lstm":                                "Deep Learning",
    "recurrent":                           "Deep Learning",
    "text classification":                 "NLP",
    "nlp":                                 "NLP",
    "natural language":                    "NLP",
    "word embedding":                      "NLP",
    "transformer":                         "NLP",
    "bert":                                "NLP",
    "clustering":                          "Machine Learning",
    "unsupervised":                        "Machine Learning",
    "dimensionality reduction":            "Machine Learning",
    "pca":                                 "Machine Learning",
    "ranking and search":                  "Machine Learning",
    "recommender":                         "Machine Learning",
    "time series":                         "Machine Learning",
    "arima":                               "Machine Learning",
    "statistics":                          "Statistics",
    "probability":                         "Statistics",
    "a/b testing":                         "Statistics",
    "ab testing":                          "Statistics",
    "hypothesis":                          "Statistics",
    "statistical inference":               "Statistics",
    "confidence interval":                 "Statistics",
    "p-value":                             "Statistics",
    "bayes":                               "Statistics",
    "sql":                                 "Data Engineering",
    "python":                              "Programming",
    "programming":                         "Programming",
    "data analysis":                       "Data Analysis",
    "exploratory":                         "Data Analysis",
    "predictive modeling":                 "Machine Learning",
    "product metrics":                     "Product Analytics",
    "communication":                       "Soft Skills",
    "machine learning":                    "Machine Learning",
    "deep learning":                       "Deep Learning",
    "data preprocessing":                  "Data Engineering",
    "model evaluation":                    "Machine Learning",
    "svm":                                 "Machine Learning",
    "support vector":                      "Machine Learning",
    "logistic regression":                 "Machine Learning",
    "bias":                                "Machine Learning",
    "variance":                            "Machine Learning",
    "overfitting":                         "Machine Learning",
    "cross-validation":                    "Machine Learning",
    "missing":                             "Data Engineering",
    "outlier":                             "Data Engineering",
    "imbalanced":                          "Machine Learning",
}

_SEEN_HASHES: set = set()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_raw(url: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=25, headers={
                "User-Agent": "Mozilla/5.0 (compatible; DS-Interview-Scraper/2.0)"
            })
            r.raise_for_status()
            return r.text
        except Exception as exc:
            print(f"  [attempt {attempt+1}] fetch error: {exc}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return ""


def _strip_for_hash(text: str) -> str:
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'[*_`#>]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()


def is_duplicate(q_text: str) -> bool:
    key = hashlib.md5(_strip_for_hash(q_text)[:200].encode()).hexdigest()
    if key in _SEEN_HASHES:
        return True
    _SEEN_HASHES.add(key)
    return False


def clean_answer(raw: str) -> str:
    raw = re.sub(r'!\[.*?\]\((https?://[^)]+)\)', '[Diagram available in source]', raw)
    raw = re.sub(r'\[([^\]]+)\]\(https?://[^)]+\)', r'\1', raw)
    raw = re.sub(r'https?://\S{70,}', '', raw)
    raw = re.sub(r'\n{3,}', '\n\n', raw)
    return raw.strip()


def infer_difficulty(q: str, default: str = "medium") -> str:
    t = q.lower()
    if any(w in t for w in ["implement ", "write code", "design a system", "mathematical proof", "derive "]):
        return "expert"
    if any(w in t for w in ["what is ", "define ", "what are ", "list ", "name the", "name three"]):
        return "easy"
    return default


def infer_code_expected(q: str) -> bool:
    t = q.lower()
    return any(w in t for w in ["implement", "write code", "python code", "code snippet",
                                  "write a function", "write an algorithm", "sql query"])


def resolve_topic(raw: str) -> str:
    key = raw.lower().strip()
    if key in TOPIC_MAP:
        return TOPIC_MAP[key]
    for k, v in TOPIC_MAP.items():
        if k in key:
            return v
    return "Data Science"


_STUB_PHRASES = (
    'answer here', 'ask someone for more details',
    'refer to the above answer', 'refer to source material',
    'for specifics, refer to the above',
)

def build_question(
    question_text: str,
    ideal_answer:  str,
    topic:         str,
    difficulty:    str = "medium",
    code_expected: bool = False,
) -> QuestionCreate | None:
    question_text = question_text.strip()
    ideal_answer  = clean_answer(ideal_answer).strip()
    if not question_text or len(question_text) < 8:
        return None
    # Reject stub or empty answers — they produce useless feedback scores
    if len(ideal_answer) < 40 or any(p in ideal_answer.lower() for p in _STUB_PHRASES):
        return None
    if is_duplicate(question_text):
        return None
    if code_expected or infer_code_expected(question_text):
        code_expected = True
    kw_src = (question_text + " " + ideal_answer)[:1500]
    try:
        kws = extract_keywords(kw_src)
    except Exception:
        kws = []
    return QuestionCreate(
        role=ROLE,
        topic=topic,
        difficulty=difficulty,
        experience_level=DIFFICULTY_TO_LEVEL.get(difficulty, "junior"),
        question_type=DIFFICULTY_TO_QTYPE.get(difficulty, "Technical"),
        question_text=question_text,
        ideal_answer=ideal_answer or None,
        keywords=", ".join(kws),
        code_expected=code_expected,
    )


def _guess_topic(text: str, fallback_t: str, fallback_s: str) -> str:
    t = text.lower()
    for k, v in TOPIC_MAP.items():
        if k in t:
            return v
    return fallback_t


def _guess_diff(text: str, fallback: str = "medium") -> str:
    return infer_difficulty(text, fallback)


# ═══════════════════════════════════════════════════════════════════════════════
# SCRAPER 1 – alexeygrigorev/data-science-interviews (theory.md)
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_alexeygrigorev(md: str) -> list:
    """
    Format:
      ## Section Header
      **Question text 👶/⭐️/🚀**
      answer paragraph(s)
      <br/>
    """
    questions = []
    current_topic = "Machine Learning"
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            current_topic = resolve_topic(line[3:].strip())
            i += 1
            continue
        bold = re.match(r'\*\*(.+?)\*\*\s*$', line.strip())
        if bold:
            q_raw = bold.group(1).strip()
            difficulty = "medium"
            for emoji, lvl in DIFFICULTY_EMOJI_MAP.items():
                if emoji in q_raw:
                    difficulty = lvl
                    q_raw = q_raw.replace(emoji, "").strip()
                    break
            else:
                difficulty = infer_difficulty(q_raw)
            answer_parts, j = [], i + 1
            while j < len(lines):
                nxt = lines[j]
                if nxt.startswith("## ") or re.match(r'\*\*.+\*\*', nxt.strip()):
                    break
                if nxt.strip() and nxt.strip() not in ("<br/>", "<br>"):
                    answer_parts.append(nxt)
                j += 1
            ideal = "\n".join(answer_parts).strip()
            q = build_question(q_raw, ideal, current_topic, difficulty)
            if q:
                questions.append(q)
            i = j
            continue
        i += 1
    return questions


def scrape_alexeygrigorev() -> list:
    print("→ [Source 1] alexeygrigorev/data-science-interviews …")
    url = "https://raw.githubusercontent.com/alexeygrigorev/data-science-interviews/master/theory.md"
    md = fetch_raw(url)
    qs = _parse_alexeygrigorev(md) if md else []
    print(f"  ✓ {len(qs)} questions")
    return qs


# ═══════════════════════════════════════════════════════════════════════════════
# SCRAPER 2 – youssefHosni/Data-Science-Interview-Questions-Answers (5 files)
# ═══════════════════════════════════════════════════════════════════════════════

_YOUSSEFHOSNI_BASE = (
    "https://raw.githubusercontent.com/youssefHosni/"
    "Data-Science-Interview-Questions-Answers/main/"
)
_YOUSSEFHOSNI_FILES = [
    ("Machine%20Learning%20Interview%20Questions%20%26%20Answers%20for%20Data%20Scientists.md",
     "Machine Learning", "General ML",          "medium"),
    ("Statistics%20Interview%20Questions%20%26%20Answers%20for%20Data%20Scientists.md",
     "Statistics",       "General Statistics",  "medium"),
    ("Probability%20Interview%20Questions%20%26%20Answers%20for%20Data%20Scientists.md",
     "Statistics",       "Probability",         "medium"),
    ("Python%20Interview%20Questions%20%26%20Answers%20for%20Data%20Scientists.md",
     "Programming",      "Python",              "medium"),
    # Actual filename has no 'Interview' word
    ("Deep%20Learning%20Questions%20%26%20Answers%20for%20Data%20Scientists.md",
     "Deep Learning",    "General DL",          "medium"),
    ("SQL%20%26%20DB%20Interview%20Questions%20%26%20Answers%20for%20Data%20Scientists.md",
     "Data Engineering", "SQL",                 "medium"),
]


def _parse_youssefhosni(md: str, def_t: str, def_s: str, def_d: str) -> list:
    """
    Format:  ### Q1: Question text ###
             Answer: / Answers:
             body…
    """
    questions = []
    blocks = re.split(r'\n###\s+Q\d+[:\s]', "\n" + md)
    for block in blocks[1:]:
        block = block.strip()
        if not block:
            continue
        first_line = block.splitlines()[0].rstrip('#').strip()
        rest = "\n".join(block.splitlines()[1:]).strip()
        # strip answer label
        rest = re.sub(r'^(?:Answer[s]?:?\s*)', '', rest, flags=re.IGNORECASE).strip()
        # trim redirect notices
        rest = re.sub(
            r'\n?The rest of the answer is\s*\[here\].*',
            '', rest, flags=re.IGNORECASE
        ).strip()
        topic = _guess_topic(first_line, def_t, def_s)
        diff = _guess_diff(first_line, def_d)
        q = build_question(first_line, rest, topic, diff)
        if q:
            questions.append(q)
    return questions


def scrape_youssefhosni() -> list:
    print("→ [Source 2] youssefHosni/Data-Science-Interview-Questions-Answers …")
    all_qs = []
    for fname, t, s, d in _YOUSSEFHOSNI_FILES:
        url = _YOUSSEFHOSNI_BASE + fname
        md = fetch_raw(url)
        if md:
            qs = _parse_youssefhosni(md, t, s, d)
            print(f"  ✓ {len(qs):3d} Qs  ← {fname[:55]}")
            all_qs.extend(qs)
        time.sleep(REQUEST_DELAY)
    print(f"  ✓ {len(all_qs)} total")
    return all_qs


# ═══════════════════════════════════════════════════════════════════════════════
# SCRAPER 3 – iamtodor/data-science-interview-questions-and-answers
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_iamtodor(md: str) -> list:
    """
    Format:  ## 1. Question heading
             Answer paragraphs / sub-headers / bullets / code
    """
    questions = []
    blocks = re.split(r'\n## \d+\. ', "\n" + md)
    for block in blocks[1:]:
        lines = block.strip().splitlines()
        if not lines:
            continue
        q_text = lines[0].strip()
        answer = "\n".join(lines[1:]).strip()
        topic = _guess_topic(q_text, "Machine Learning", "General ML")
        diff = _guess_diff(q_text)
        q = build_question(q_text, answer, topic, diff)
        if q:
            questions.append(q)
    return questions


def scrape_iamtodor() -> list:
    print("→ [Source 3] iamtodor/data-science-interview-questions-and-answers …")
    url = ("https://raw.githubusercontent.com/iamtodor/"
           "data-science-interview-questions-and-answers/master/README.md")
    md = fetch_raw(url)
    qs = _parse_iamtodor(md) if md else []
    print(f"  ✓ {len(qs)} questions")
    return qs


# ═══════════════════════════════════════════════════════════════════════════════
# SCRAPER 4 – kojino/120-Data-Science-Interview-Questions (7 files)
# ═══════════════════════════════════════════════════════════════════════════════

_KOJINO_BASE  = "https://raw.githubusercontent.com/kojino/120-Data-Science-Interview-Questions/master/"
_KOJINO_FILES = [
    ("probability.md",           "Statistics",        "Probability"),
    ("statistical-inference.md", "Statistics",        "Statistical Inference"),
    ("data-analysis.md",         "Data Analysis",     "EDA"),
    ("predictive-modeling.md",   "Machine Learning",  "Predictive Modeling"),
    ("programming.md",           "Programming",       "General Programming"),
    ("product-metrics.md",       "Product Analytics", "Product Metrics"),
    ("communication.md",         "Soft Skills",       "Communication"),
]


def _parse_kojino(md: str, topic: str, subtopic: str) -> list:
    """
    Format:  #### 1. Question text
               - answer bullet
               - answer bullet
    """
    questions = []
    blocks = re.split(r'\n#### \d+\.? ', "\n" + md)
    for block in blocks[1:]:
        lines = block.strip().splitlines()
        if not lines:
            continue
        q_text = lines[0].strip()
        answer_lines = []
        for ln in lines[1:]:
            s = ln.strip()
            if s:
                answer_lines.append(s)
        answer = "\n".join(answer_lines).strip() or "Refer to source material for a detailed answer."
        diff = _guess_diff(q_text)
        q = build_question(q_text, answer, topic, diff)
        if q:
            questions.append(q)
    return questions


def scrape_kojino() -> list:
    print("→ [Source 4] kojino/120-Data-Science-Interview-Questions …")
    all_qs = []
    for fname, topic, subtopic in _KOJINO_FILES:
        url = _KOJINO_BASE + fname
        md = fetch_raw(url)
        if md:
            qs = _parse_kojino(md, topic, subtopic)
            print(f"  ✓ {len(qs):3d} Qs  ← {fname}")
            all_qs.extend(qs)
        time.sleep(REQUEST_DELAY)
    print(f"  ✓ {len(all_qs)} total")
    return all_qs


# ═══════════════════════════════════════════════════════════════════════════════
# SCRAPER 5 – roadmap.sh/questions/data-science
# ═══════════════════════════════════════════════════════════════════════════════

def scrape_roadmap() -> list:
    print("→ [Source 5] roadmap.sh/questions/data-science …")
    url  = "https://roadmap.sh/questions/data-science"
    html = fetch_raw(url)
    if not html:
        print("  ⚠ Could not fetch – skipping")
        return []
    soup = BeautifulSoup(html, "html.parser")
    questions = []
    # Try accordion pattern
    for item in soup.select("div.accordion-item, div[data-question], article"):
        q_el = item.select_one("h2, h3, .question-title, button")
        a_el = item.select_one("div.accordion-body, div.answer, p")
        if not q_el or not a_el:
            continue
        q_text = q_el.get_text(separator=" ", strip=True)
        a_text = a_el.get_text(separator="\n", strip=True)
        if len(q_text) < 10:
            continue
        topic = _guess_topic(q_text, "Data Science", "General")
        diff = _guess_diff(q_text)
        q = build_question(q_text, a_text, topic, diff)
        if q:
            questions.append(q)
    # Try __NEXT_DATA__ JSON
    if not questions:
        nd = soup.find("script", {"id": "__NEXT_DATA__"})
        if nd and nd.string:
            try:
                data = json.loads(nd.string)
                def _walk(obj):
                    if isinstance(obj, dict):
                        if "question" in obj and "answer" in obj:
                            yield obj
                        for v in obj.values():
                            yield from _walk(v)
                    elif isinstance(obj, list):
                        for item in obj:
                            yield from _walk(item)
                for item in _walk(data):
                    q_text = item.get("question", "").strip()
                    a_text = item.get("answer", "").strip()
                    if not q_text:
                        continue
                    topic = _guess_topic(q_text, "Data Science", "General")
                    diff = _guess_diff(q_text)
                    q = build_question(q_text, a_text, topic, diff)
                    if q:
                        questions.append(q)
            except Exception:
                pass
    print(f"  ✓ {len(questions)} questions")
    return questions


# ═══════════════════════════════════════════════════════════════════════════════
# SUPPLEMENTAL – hand-curated Q&As for key gaps (SQL, Python, Stats, DL, NLP)
# ═══════════════════════════════════════════════════════════════════════════════

_SUPPLEMENTAL = [
    # ── SQL ──────────────────────────────────────────────────────────────────
    {"question": "What is the difference between INNER JOIN, LEFT JOIN, RIGHT JOIN, and FULL OUTER JOIN?",
     "answer": (
         "INNER JOIN returns only rows with matching values in both tables.\n\n"
         "LEFT JOIN returns all rows from the left table plus matched rows from the right; "
         "unmatched right-side columns are NULL.\n\n"
         "RIGHT JOIN returns all rows from the right table plus matched rows from the left; "
         "unmatched left-side columns are NULL.\n\n"
         "FULL OUTER JOIN returns all rows when there is a match in either table; "
         "rows without a match contain NULLs for the other table's columns."
     ), "topic": "Data Engineering", "subtopic": "SQL", "difficulty": "easy"},

    {"question": "Explain the difference between WHERE and HAVING in SQL.",
     "answer": (
         "WHERE filters individual rows before any grouping. It cannot use aggregate functions.\n\n"
         "HAVING filters groups after a GROUP BY has been applied and can reference aggregates.\n\n"
         "```sql\n"
         "SELECT department, COUNT(*) AS cnt\n"
         "FROM employees\n"
         "WHERE salary > 50000\n"
         "GROUP BY department\n"
         "HAVING COUNT(*) > 5;\n"
         "```"
     ), "topic": "Data Engineering", "subtopic": "SQL", "difficulty": "easy"},

    {"question": "What are SQL window functions? Demonstrate ROW_NUMBER(), RANK(), and LAG().",
     "answer": (
         "Window functions perform calculations across a set of related rows without collapsing them, "
         "using the OVER() clause.\n\n"
         "```sql\n"
         "SELECT\n"
         "  emp_id, dept, salary,\n"
         "  ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC) AS row_num,\n"
         "  RANK()       OVER (PARTITION BY dept ORDER BY salary DESC) AS rank_in_dept,\n"
         "  LAG(salary)  OVER (PARTITION BY dept ORDER BY hire_date)  AS prev_salary\n"
         "FROM employees;\n"
         "```\n\n"
         "ROW_NUMBER: unique sequential integer per row.\n"
         "RANK: same rank for ties, gaps after ties.\n"
         "LAG/LEAD: access a value from a preceding/following row."
     ), "topic": "Data Engineering", "subtopic": "SQL", "difficulty": "medium"},

    {"question": "What is a CTE in SQL and when would you use it?",
     "answer": (
         "A Common Table Expression (CTE) is a named temporary result set defined with WITH, "
         "scoped to a single query. It improves readability and enables recursive queries.\n\n"
         "```sql\n"
         "WITH regional_sales AS (\n"
         "    SELECT region, SUM(amount) AS total\n"
         "    FROM orders GROUP BY region\n"
         ")\n"
         "SELECT region, total\n"
         "FROM regional_sales\n"
         "WHERE total > 100000;\n"
         "```\n\n"
         "Use CTEs for: breaking complex queries into readable steps, reusing a subquery, "
         "or writing recursive tree-traversal queries."
     ), "topic": "Data Engineering", "subtopic": "SQL", "difficulty": "medium"},

    {"question": "What is database indexing and what are the trade-offs?",
     "answer": (
         "An index is a data structure (commonly B-tree) that speeds up row retrieval at the cost "
         "of extra storage and slower INSERT/UPDATE/DELETE.\n\n"
         "Use indexes on: columns in WHERE, JOIN ON, or ORDER BY; foreign keys; high-cardinality columns.\n\n"
         "Avoid on: rarely queried columns; very low cardinality (boolean); small tables.\n\n"
         "Types: B-tree (general purpose), Hash (equality), GIN (full-text/array), Partial (subset rows).\n\n"
         "Trade-off: read performance ↑ vs. write overhead ↑ and storage ↑."
     ), "topic": "Data Engineering", "subtopic": "SQL", "difficulty": "medium"},

    {"question": "How do you find duplicate rows in a SQL table?",
     "answer": (
         "```sql\n"
         "SELECT email, COUNT(*) AS cnt\n"
         "FROM users\n"
         "GROUP BY email\n"
         "HAVING COUNT(*) > 1;\n"
         "```\n\n"
         "To retrieve the full rows for duplicates:\n"
         "```sql\n"
         "SELECT *\n"
         "FROM users u\n"
         "WHERE u.id NOT IN (\n"
         "    SELECT MIN(id) FROM users GROUP BY email\n"
         ");\n"
         "```\n\n"
         "Or using ROW_NUMBER():\n"
         "```sql\n"
         "WITH ranked AS (\n"
         "    SELECT *, ROW_NUMBER() OVER (PARTITION BY email ORDER BY id) AS rn\n"
         "    FROM users\n"
         ")\n"
         "SELECT * FROM ranked WHERE rn > 1;\n"
         "```"
     ), "topic": "Data Engineering", "subtopic": "SQL", "difficulty": "medium"},

    # ── Python ───────────────────────────────────────────────────────────────
    {"question": "What is the difference between a list and a tuple in Python?",
     "answer": (
         "Lists are mutable (modifiable) using square brackets []. "
         "Tuples are immutable using parentheses ().\n\n"
         "Key differences:\n"
         "- Mutability: list → can change; tuple → cannot\n"
         "- Performance: tuples are faster to access and use less memory\n"
         "- Hashability: tuples can be dictionary keys; lists cannot\n"
         "- Use case: lists for changing collections; tuples for fixed records\n\n"
         "```python\n"
         "my_list[0] = 10    # OK\n"
         "my_tuple[0] = 10   # TypeError: 'tuple' object does not support item assignment\n"
         "```"
     ), "topic": "Programming", "subtopic": "Python", "difficulty": "easy"},

    {"question": "What is the difference between shallow copy and deep copy in Python?",
     "answer": (
         "Shallow copy: new outer object, but nested objects are shared (referenced).\n"
         "Deep copy: completely independent copy, including all nested objects.\n\n"
         "```python\n"
         "import copy\n"
         "original = [[1, 2], [3, 4]]\n"
         "shallow  = copy.copy(original)\n"
         "deep     = copy.deepcopy(original)\n\n"
         "shallow[0][0] = 99   # also changes original[0][0]\n"
         "deep[0][0]    = 99   # does NOT affect original\n"
         "```\n"
         "Use deep copy when nested mutable data must be fully independent."
     ), "topic": "Programming", "subtopic": "Python", "difficulty": "medium"},

    {"question": "What are Python decorators and how do they work? Give an example.",
     "answer": (
         "A decorator wraps a function to extend its behaviour without modifying it permanently, "
         "using the @ syntax as sugar for func = decorator(func).\n\n"
         "```python\n"
         "import functools, time\n\n"
         "def timer(func):\n"
         "    @functools.wraps(func)\n"
         "    def wrapper(*args, **kwargs):\n"
         "        t0 = time.perf_counter()\n"
         "        result = func(*args, **kwargs)\n"
         "        print(f'{func.__name__}: {time.perf_counter()-t0:.3f}s')\n"
         "        return result\n"
         "    return wrapper\n\n"
         "@timer\n"
         "def compute(): ...\n"
         "```\n"
         "Common built-in decorators: @staticmethod, @classmethod, @property, @functools.lru_cache."
     ), "topic": "Programming", "subtopic": "Python", "difficulty": "medium"},

    {"question": "What is the difference between *args and **kwargs in Python?",
     "answer": (
         "*args collects any number of positional arguments into a tuple.\n"
         "**kwargs collects any number of keyword arguments into a dict.\n\n"
         "```python\n"
         "def example(*args, **kwargs):\n"
         "    print(args)   # (1, 2, 3)\n"
         "    print(kwargs) # {'name': 'Alice'}\n\n"
         "example(1, 2, 3, name='Alice')\n"
         "```\n"
         "They are useful in wrapper functions, decorators, and highly flexible APIs."
     ), "topic": "Programming", "subtopic": "Python", "difficulty": "easy"},

    {"question": "What is NumPy broadcasting? Provide an example.",
     "answer": (
         "Broadcasting is NumPy's mechanism to perform arithmetic on arrays with different shapes "
         "by virtually expanding the smaller array.\n\n"
         "Rules:\n"
         "1. Prepend 1s to shape of smaller array.\n"
         "2. Dimensions of size 1 are stretched to match the larger.\n"
         "3. Incompatible shapes (neither 1) raise ValueError.\n\n"
         "```python\n"
         "import numpy as np\n"
         "a = np.array([[1, 2, 3], [4, 5, 6]])  # shape (2,3)\n"
         "b = np.array([10, 20, 30])              # shape (3,) → (1,3) → (2,3)\n"
         "print(a + b)  # [[11,22,33],[14,25,36]]\n"
         "```"
     ), "topic": "Programming", "subtopic": "Python", "difficulty": "medium"},

    {"question": "Explain Python's GIL and its implications for concurrency.",
     "answer": (
         "The Global Interpreter Lock (GIL) is a mutex in CPython that allows only one thread "
         "to execute Python bytecode at a time, even on multi-core hardware.\n\n"
         "Implications:\n"
         "- CPU-bound tasks: threading gives NO speed-up → use multiprocessing\n"
         "- I/O-bound tasks: threading IS effective (GIL released during I/O waits)\n\n"
         "Workarounds:\n"
         "- multiprocessing / ProcessPoolExecutor (separate processes, each with own GIL)\n"
         "- NumPy / C extensions (release GIL for native operations)\n"
         "- asyncio for I/O-bound concurrency\n"
         "- Alternative runtimes (PyPy, Jython) without a GIL"
     ), "topic": "Programming", "subtopic": "Python", "difficulty": "expert"},

    {"question": "What is the difference between generators and regular functions in Python?",
     "answer": (
         "A generator function uses yield instead of return, producing values lazily one at a time "
         "without materialising the whole sequence in memory.\n\n"
         "```python\n"
         "def fibonacci():\n"
         "    a, b = 0, 1\n"
         "    while True:\n"
         "        yield a\n"
         "        a, b = b, a + b\n\n"
         "gen = fibonacci()\n"
         "print(next(gen), next(gen), next(gen))  # 0 1 1\n"
         "```\n\n"
         "Advantages:\n"
         "- Memory efficient: only one value in memory at a time\n"
         "- Can represent infinite sequences\n"
         "- Enables pipeline processing with generator expressions"
     ), "topic": "Programming", "subtopic": "Python", "difficulty": "medium"},

    # ── Statistics ────────────────────────────────────────────────────────────
    {"question": "What is Bayes' theorem? Give a practical example.",
     "answer": (
         "Bayes' theorem: P(A|B) = P(B|A) × P(A) / P(B)\n\n"
         "Example – Medical test:\n"
         "- Disease prevalence P(D) = 0.01\n"
         "- Test sensitivity P(+|D) = 0.99\n"
         "- False positive rate P(+|¬D) = 0.05\n"
         "- P(+) = 0.99×0.01 + 0.05×0.99 ≈ 0.0594\n"
         "- P(D|+) ≈ 0.0099 / 0.0594 ≈ 0.167 (only 17%!)\n\n"
         "Despite 99% sensitivity, a positive result means only ~17% chance of disease "
         "— base rate dominates. This is called the base-rate fallacy."
     ), "topic": "Statistics", "subtopic": "Probability", "difficulty": "medium"},

    {"question": "What is the difference between Type I and Type II errors?",
     "answer": (
         "Type I error (false positive α): rejecting H₀ when it is true.\n"
         "Type II error (false negative β): failing to reject H₀ when it is false.\n"
         "Statistical power = 1 − β.\n\n"
         "Medical example:\n"
         "- Type I: diagnosing a healthy patient as sick (false alarm)\n"
         "- Type II: missing a disease in an actual patient (missed detection)\n\n"
         "Trade-off: reducing α (stricter threshold) increases β unless sample size grows."
     ), "topic": "Statistics", "subtopic": "Hypothesis Testing", "difficulty": "easy"},

    {"question": "What is the Central Limit Theorem and why is it important?",
     "answer": (
         "The CLT states that the distribution of the sample mean of n independent, identically "
         "distributed random variables approaches N(μ, σ²/n) as n → ∞, regardless of the "
         "original population distribution.\n\n"
         "Importance:\n"
         "- Justifies z-tests and t-tests even for non-normal populations (with large n)\n"
         "- Enables confidence interval construction\n"
         "- Foundation for many statistical inference procedures\n\n"
         "Practical conditions:\n"
         "- Random sampling\n"
         "- Independence between observations\n"
         "- Sample size ≥ 30 (rough rule; more for skewed distributions)"
     ), "topic": "Statistics", "subtopic": "General Statistics", "difficulty": "medium"},

    {"question": "What is the difference between correlation and causation?",
     "answer": (
         "Correlation: statistical association between two variables (they co-vary).\n"
         "Causation: one variable directly produces change in another.\n\n"
         "Correlation ≠ Causation because:\n"
         "- A confounding variable may cause both\n"
         "- Direction of causality may be reversed\n"
         "- The correlation may be coincidental (spurious)\n\n"
         "Classic example: ice cream sales correlate with drowning rates. "
         "Confounder: hot weather drives both.\n\n"
         "To establish causation:\n"
         "- Randomized controlled experiments / A/B tests\n"
         "- Instrumental variables\n"
         "- Difference-in-differences\n"
         "- Regression discontinuity"
     ), "topic": "Statistics", "subtopic": "General Statistics", "difficulty": "easy"},

    {"question": "What is the difference between the z-test and t-test?",
     "answer": (
         "Both test whether a sample mean differs from a hypothesised value, but differ in when they apply.\n\n"
         "z-test:\n"
         "- Use when population variance σ² is known\n"
         "- Or when n ≥ 30 (CLT applies, sample variance approximates σ²)\n"
         "- Test statistic: z = (x̄ − μ₀) / (σ / √n)\n\n"
         "t-test:\n"
         "- Use when population variance is unknown (estimated from sample)\n"
         "- Especially important for small samples (n < 30)\n"
         "- Test statistic: t = (x̄ − μ₀) / (s / √n), df = n−1\n\n"
         "As n → ∞, the t-distribution approaches the z/normal distribution."
     ), "topic": "Statistics", "subtopic": "Hypothesis Testing", "difficulty": "medium"},

    # ── Machine Learning ──────────────────────────────────────────────────────
    {"question": "What is cross-entropy loss and when is it used?",
     "answer": (
         "Cross-entropy measures the difference between the predicted probability distribution "
         "and the true distribution.\n\n"
         "Binary: L = −[y·log(p) + (1−y)·log(1−p)]\n"
         "Categorical: L = −Σ y_i · log(p_i)\n\n"
         "Properties:\n"
         "- Penalises confident wrong predictions severely (log(p)→−∞ as p→0)\n"
         "- Differentiable → compatible with gradient-based optimisation\n"
         "- Equivalent to MLE under Bernoulli / Categorical distribution\n\n"
         "Used for: logistic regression, softmax neural networks, any probabilistic classifier."
     ), "topic": "Machine Learning", "subtopic": "Model Evaluation", "difficulty": "medium"},

    {"question": "What is the difference between bagging and boosting?",
     "answer": (
         "Both combine multiple weak learners into a stronger model.\n\n"
         "Bagging (Bootstrap Aggregating):\n"
         "- Trains models in parallel on random data subsets (with replacement)\n"
         "- Combines by averaging / majority vote\n"
         "- Reduces variance (prevents overfitting)\n"
         "- Example: Random Forest\n\n"
         "Boosting:\n"
         "- Trains models sequentially; each corrects errors of the previous\n"
         "- Reduces bias (improves underfitting)\n"
         "- Prone to overfitting on noisy data\n"
         "- Examples: AdaBoost, Gradient Boosting, XGBoost, LightGBM, CatBoost\n\n"
         "Key: Bagging = parallel + variance↓; Boosting = sequential + bias↓."
     ), "topic": "Machine Learning", "subtopic": "Ensemble Methods", "difficulty": "medium"},

    {"question": "What is SHAP and how does it help explain ML models?",
     "answer": (
         "SHAP (SHapley Additive exPlanations) uses game theory to assign each feature a "
         "contribution value for a specific prediction.\n\n"
         "SHAP value φᵢ = average marginal contribution of feature i across all feature orderings.\n\n"
         "Properties:\n"
         "- Local accuracy: Σφᵢ + expected output = model output\n"
         "- Consistency: if feature impact increases in new model, its SHAP value also increases\n"
         "- Missingness: zero-impact features get zero SHAP value\n\n"
         "Use cases:\n"
         "- Explain individual predictions ('why was this loan denied?')\n"
         "- Global feature importance via SHAP summary plots\n"
         "- Model debugging, bias detection\n\n"
         "TreeSHAP runs in O(TLD²) for tree models vs O(2^M) for brute force."
     ), "topic": "Machine Learning", "subtopic": "Model Interpretability", "difficulty": "expert"},

    {"question": "Explain the difference between generative and discriminative models.",
     "answer": (
         "Discriminative models: directly model P(y|x) — the conditional probability of "
         "the label given the input.\n"
         "Examples: Logistic Regression, SVM, Neural Networks, Random Forest.\n\n"
         "Generative models: model the joint P(x,y) = P(x|y)·P(y), then derive P(y|x) via Bayes.\n"
         "Examples: Naïve Bayes, HMMs, GANs, VAEs, LDA.\n\n"
         "Comparison:\n"
         "- Discriminative: usually higher classification accuracy with enough data\n"
         "- Generative: can generate new samples, handle missing data, work with less labelled data\n"
         "- Generative models make stronger distributional assumptions"
     ), "topic": "Machine Learning", "subtopic": "General ML", "difficulty": "medium"},

    {"question": "What is SMOTE and why is it used for imbalanced datasets?",
     "answer": (
         "SMOTE (Synthetic Minority Over-sampling Technique) creates synthetic examples of the "
         "minority class by interpolating between existing minority samples and their k-nearest neighbours.\n\n"
         "Algorithm:\n"
         "1. Select a random minority sample x.\n"
         "2. Find its k nearest minority neighbours.\n"
         "3. Randomly pick one neighbour x'.\n"
         "4. Generate: x_new = x + λ(x' − x) where λ ∈ [0,1] uniformly.\n\n"
         "Advantages over simple oversampling:\n"
         "- Creates diverse synthetic examples (not exact duplicates)\n"
         "- Reduces overfitting of the minority class\n\n"
         "Use with: random forest, SVM, logistic regression on imbalanced classification tasks.\n"
         "Variants: SMOTE-NC (for mixed features), ADASYN (adaptive density), Borderline-SMOTE."
     ), "topic": "Machine Learning", "subtopic": "Classification", "difficulty": "medium"},

    # ── Deep Learning ─────────────────────────────────────────────────────────
    {"question": "What is the vanishing gradient problem and how is it addressed?",
     "answer": (
         "Vanishing gradients occur when gradients become extremely small as they propagate "
         "back through many layers, causing early layers to learn very slowly.\n\n"
         "Causes:\n"
         "- Sigmoid / tanh saturate near 0 or 1 where gradient ≈ 0\n"
         "- Many layers multiply gradients; small values → exponentially small product\n\n"
         "Solutions:\n"
         "1. ReLU / Leaky ReLU / GELU — do not saturate for positive values\n"
         "2. Batch Normalisation — keeps activations in a healthy range\n"
         "3. Residual / skip connections (ResNet) — gradients flow directly\n"
         "4. LSTM / GRU gating — preserve long-range gradients in RNNs\n"
         "5. Careful weight initialisation (He for ReLU, Glorot for sigmoid)\n"
         "6. Gradient clipping — cap gradient norm during training"
     ), "topic": "Deep Learning", "subtopic": "Optimization", "difficulty": "medium"},

    {"question": "What is Batch Normalisation and why does it help training?",
     "answer": (
         "Batch Normalisation (BN) normalises the inputs to each layer using the batch mean (μ_B) "
         "and variance (σ²_B), then applies learnable parameters γ (scale) and β (shift):\n\n"
         "x̂ = (x − μ_B) / √(σ²_B + ε)\n"
         "y = γ·x̂ + β\n\n"
         "Benefits:\n"
         "1. Reduces internal covariate shift → more stable training\n"
         "2. Allows higher learning rates → faster convergence\n"
         "3. Acts as a mild regulariser (reduces dropout need)\n"
         "4. Mitigates vanishing/exploding gradients\n\n"
         "At inference: uses running mean/variance tracked during training, not batch statistics."
     ), "topic": "Deep Learning", "subtopic": "Optimization", "difficulty": "medium"},

    {"question": "What is the attention mechanism in Transformers?",
     "answer": (
         "Attention allows the model to weigh the importance of different input positions "
         "when producing each output position.\n\n"
         "Scaled Dot-Product Attention:\n"
         "Attention(Q, K, V) = softmax(QKᵀ / √d_k) · V\n\n"
         "Q (queries), K (keys), V (values) are linear projections of the input.\n\n"
         "Multi-Head Attention runs h parallel attention heads, concatenates their outputs:\n"
         "MH = Concat(head₁, …, headₕ) · W^O\n\n"
         "Advantages over RNNs:\n"
         "- Parallelisable (O(1) sequential operations vs O(n) for RNNs)\n"
         "- Direct long-range dependencies regardless of sequence length\n\n"
         "Positional encodings are added because self-attention is permutation-invariant."
     ), "topic": "Deep Learning", "subtopic": "Transformers", "difficulty": "expert"},

    # ── NLP ───────────────────────────────────────────────────────────────────
    {"question": "What is the difference between stemming and lemmatization?",
     "answer": (
         "Stemming: rule-based, chops word endings → fast but may produce non-words.\n"
         "Example: 'running' → 'run', 'better' → 'bett' (Porter stemmer)\n\n"
         "Lemmatization: uses vocabulary + morphological analysis → returns real dictionary base form.\n"
         "Example: 'better' → 'good', 'running' → 'run' (requires POS tagging)\n\n"
         "Choice:\n"
         "- Stemming: when speed matters and rough normalisation is enough\n"
         "- Lemmatization: when grammatical correctness and real words matter\n\n"
         "Libraries: NLTK (both), spaCy (lemmatization), Snowball (stemming)."
     ), "topic": "NLP", "subtopic": "Text Preprocessing", "difficulty": "easy"},

    {"question": "What is the difference between Word2Vec CBOW and Skip-gram?",
     "answer": (
         "Both learn word embeddings via a shallow neural network.\n\n"
         "CBOW (Continuous Bag-of-Words):\n"
         "- Input: surrounding context words → Predicts: target word\n"
         "- Faster training; better for frequent words\n\n"
         "Skip-gram:\n"
         "- Input: target/centre word → Predicts: surrounding context words\n"
         "- Slower but better for rare words and small datasets\n\n"
         "Negative sampling (SGNS) makes training tractable by updating only k random "
         "negative examples per positive sample.\n\n"
         "In practice, Skip-gram with negative sampling produces higher quality embeddings "
         "and is more widely cited."
     ), "topic": "NLP", "subtopic": "Word Embeddings", "difficulty": "medium"},

    # ── MLOps / Production ────────────────────────────────────────────────────
    {"question": "What is model drift and how do you detect and handle it?",
     "answer": (
         "Model drift: a deployed model's performance degrades because real-world data changes.\n\n"
         "Types:\n"
         "- Data drift (covariate shift): input feature distributions change\n"
         "- Concept drift: relationship between inputs and target changes\n"
         "- Label drift: target distribution changes\n\n"
         "Detection:\n"
         "- Monitor prediction distributions (PSI, KL divergence)\n"
         "- Statistical tests on features (KS test, chi-squared)\n"
         "- Track model performance metrics over rolling windows\n\n"
         "Handling:\n"
         "- Periodic retraining on recent data\n"
         "- Online / continual learning\n"
         "- Feature engineering to reduce sensitivity to distribution shift\n"
         "- Alerting pipelines with drift thresholds"
     ), "topic": "Machine Learning", "subtopic": "MLOps", "difficulty": "medium"},

    # ── Feature Engineering / Data Prep ──────────────────────────────────────
    {"question": "What are different strategies for handling missing data?",
     "answer": (
         "Deletion:\n"
         "- Listwise: remove rows with any missing (safe only for MCAR data)\n"
         "- Pairwise: use available data per computation\n\n"
         "Imputation:\n"
         "- Mean / median / mode: simple but ignores correlations\n"
         "- Forward / backward fill: for time-series\n"
         "- KNN imputation: use k nearest neighbours to estimate\n"
         "- MICE (Multiple Imputation by Chained Equations): iterative, preserves uncertainty\n"
         "- Model-based: train a predictor for each missing column\n\n"
         "Model-aware:\n"
         "- Tree models (XGBoost, LightGBM) handle missing natively\n"
         "- Add a binary 'was_missing' indicator feature\n\n"
         "Always analyse missingness pattern (MCAR / MAR / MNAR) before choosing strategy."
     ), "topic": "Data Engineering", "subtopic": "Data Preprocessing", "difficulty": "medium"},

    {"question": "Explain the difference between normalization and standardization.",
     "answer": (
         "Normalization (Min-Max):\n"
         "x' = (x − x_min) / (x_max − x_min) → [0, 1]\n"
         "Sensitive to outliers. Use for neural networks, image pixels.\n\n"
         "Standardization (Z-score):\n"
         "x' = (x − μ) / σ → mean 0, std 1\n"
         "Robust to scale differences. Use for SVM, PCA, linear models with regularisation.\n\n"
         "Neither is needed for tree-based models (scale-invariant).\n\n"
         "Rule of thumb: standardise when using L1/L2 regularisation "
         "(ensures equal penalisation across features)."
     ), "topic": "Machine Learning", "subtopic": "Feature Engineering", "difficulty": "easy"},

    {"question": "What is target encoding and when should you use it?",
     "answer": (
         "Target encoding replaces each category with the mean of the target variable for that category.\n\n"
         "```python\n"
         "# Example: encode 'city' with mean salary\n"
         "means = df.groupby('city')['salary'].mean()\n"
         "df['city_encoded'] = df['city'].map(means)\n"
         "```\n\n"
         "Advantages over one-hot encoding:\n"
         "- Handles high-cardinality categoricals without dimensionality explosion\n"
         "- Captures ordinal relationship with target\n\n"
         "Risk: target leakage and overfitting.\n\n"
         "Mitigations:\n"
         "- Use cross-validation to compute target stats out-of-fold\n"
         "- Add smoothing: encode = (n·mean_cat + m·mean_global) / (n + m) where m is regularisation\n\n"
         "Use when: high-cardinality categoricals, tree-based models, and large datasets."
     ), "topic": "Machine Learning", "subtopic": "Feature Engineering", "difficulty": "medium"},
]


def get_supplemental_questions() -> list:
    qs = []
    for item in _SUPPLEMENTAL:
        q = build_question(
            question_text=item["question"],
            ideal_answer=item["answer"],
            topic=item["topic"],
            difficulty=item.get("difficulty", "medium"),
        )
        if q:
            qs.append(q)
    print(f"  ✓ {len(qs)} supplemental curated questions")
    return qs


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE SEEDING
# ═══════════════════════════════════════════════════════════════════════════════

def seed(questions: list) -> int:
    db     = SessionLocal()
    seeded = skipped = 0
    try:
        for q in questions:
            try:
                create_question(db, q)
                seeded += 1
            except Exception as exc:
                db.rollback()
                skipped += 1
                if skipped <= 5:
                    print(f"  ⚠ DB ({type(exc).__name__}): {str(exc)[:80]}")
    finally:
        db.close()
    print(f"  ✓ Seeded {seeded} | Skipped/Errors {skipped}")
    return seeded


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 62)
    print("  Comprehensive DS Interview Q&A Scraper + DB Seeder")
    print("═" * 62 + "\n")

    all_questions = []

    all_questions.extend(scrape_alexeygrigorev())
    time.sleep(REQUEST_DELAY)

    all_questions.extend(scrape_youssefhosni())
    time.sleep(REQUEST_DELAY)

    all_questions.extend(scrape_iamtodor())
    time.sleep(REQUEST_DELAY)

    all_questions.extend(scrape_kojino())
    time.sleep(REQUEST_DELAY)

    all_questions.extend(scrape_roadmap())

    print("\n→ Loading supplemental curated Q&As …")
    all_questions.extend(get_supplemental_questions())

    print(f"\n{'─'*62}")
    print(f"  Total unique questions collected: {len(all_questions)}")
    print(f"{'─'*62}\n")

    print("→ Seeding to Neon database …")
    total_seeded = seed(all_questions)

    print(f"\n✅  Done — {total_seeded} questions seeded to Neon database.\n")
    return all_questions


if __name__ == "__main__":
    main()