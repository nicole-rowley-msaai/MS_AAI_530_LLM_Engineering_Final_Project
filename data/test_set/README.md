# Test set

`evaluation/run_eval.py` reads `pairs.csv` from this folder. The file is not
included yet. Create it with one row per resume and job-posting pair and
these columns:

| Column | Contents |
|---|---|
| `pair_id` | A short unique ID, for example `P01` |
| `resume` | The full resume text |
| `job_posting` | The full job posting text |

Extra columns (job category, match type, gold-set flag) are allowed and are
ignored by the script.

Use only the public Kaggle sample data here. Do not add real resumes that
contain personal information.
