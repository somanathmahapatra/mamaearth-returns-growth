\# Mamaearth Returns \& Growth Intelligence Pipeline



\## Project Overview



This project analyzes Mamaearth order, revenue, and returns data using SQLite and Python. It produces SQL-based business reports, performs data cleaning and exploratory data analysis (EDA), generates visualizations, and creates a business narrative from verified findings.



The pipeline uses:



\* \*\*SQLite\*\* for data storage and SQL reporting

\* \*\*Python, Pandas and Matplotlib\*\* for analysis and visualization

\* \*\*Gemini API\*\* for AI-generated business narratives, with a deterministic offline fallback



\## Prerequisites



Install the following before running the pipeline:



\* Python 3

\* SQLite command-line tool (`sqlite3`)

\* Python packages required by the project scripts



If the repository contains a `requirements.txt` file, install the dependencies from the project root:



```bash

python -m pip install -r requirements.txt

```



Verify that SQLite is available:



```bash

sqlite3 --version

```



\## Step 1 — Create the Database and Run SQL Reports



Run all commands from the repository root.



\### 1.1 Create and initialize the database



Execute the schema script to create the required tables:



```bash

sqlite3 mamaearth.db ".read sql/schema.sql"

```



\### 1.2 Load the seed data



Populate the tables with the supplied data:



```bash

sqlite3 mamaearth.db ".read sql/seed\_data.sql"

```



\### 1.3 Generate SQL reports



Run the reporting queries against the initialized database:



```bash

sqlite3 mamaearth.db ".read sql/reports.sql"

```



Review the query results in the terminal. These reports provide the SQL-level results used in the subsequent analysis.



\*\*Important:\*\* Use the same database file throughout the pipeline. If the project scripts reference a different database filename, use that filename consistently in these commands.



\## Step 2 — Clean the Data, Perform EDA, and Generate Visualizations



\### 2.1 Run data cleaning and exploratory analysis



Execute:



```bash

python analysis/clean\_and\_eda.py

```



This stage prepares the data for analysis, handles the cleaning and validation steps implemented in the script, and produces the EDA outputs.



\### 2.2 Generate visualizations



After the cleaning and EDA stage completes successfully, run:



```bash

python analysis/visualize.py

```



This stage generates the project's visualizations from the analysis data.



\### 2.3 Generate the verified findings



Complete \*\*Part 2, Task 5\*\* to generate:



```text

narrator/findings.json

```



This JSON file contains the verified findings used by the narrative generator. Confirm that the file exists and contains the latest results before proceeding.



The intended execution order is:



1\. `analysis/clean\_and\_eda.py`

2\. `analysis/visualize.py`

3\. Part 2, Task 5 — generate `narrator/findings.json`



Do not run the narrative generator using missing or outdated findings.



\## Step 3 — Generate the Business Narrative



The narrative generator reads the verified findings from `narrator/findings.json` and writes the business narrative to:



```text

narrator/sample\_output.txt

```



Run the generator from the repository root:



```bash

python narrator/generate\_narrative.py

```



\### Option A — Run with the Gemini API



Set your Gemini API key as an environment variable before running the script. Obtain the key through Google AI Studio.



\*\*Windows PowerShell:\*\*



```powershell

$env:GEMINI\_API\_KEY = "YOUR\_GEMINI\_API\_KEY"

python narrator/generate\_narrative.py

```



\*\*Windows Command Prompt:\*\*



```cmd

set GEMINI\_API\_KEY=YOUR\_GEMINI\_API\_KEY

python narrator/generate\_narrative.py

```



\*\*macOS/Linux:\*\*



```bash

export GEMINI\_API\_KEY="YOUR\_GEMINI\_API\_KEY"

python narrator/generate\_narrative.py

```



Replace the placeholder with your actual key. Keep the key private, and never commit it to GitHub.



When a valid key is configured and the Gemini request succeeds, the script generates the narrative using the configured Gemini model. If the request fails, the script uses the offline fallback implemented in the generator.



\### Option B — Run without a Gemini API key



The pipeline also supports offline narrative generation. No API key is required for this path.



In Windows PowerShell, remove the key from the current session if it was previously set:



```powershell

Remove-Item Env:GEMINI\_API\_KEY -ErrorAction SilentlyContinue

python narrator/generate\_narrative.py

```



In Windows Command Prompt:



```cmd

set GEMINI\_API\_KEY=

python narrator/generate\_narrative.py

```



On macOS/Linux:



```bash

unset GEMINI\_API\_KEY

python narrator/generate\_narrative.py

```



When `GEMINI\_API\_KEY` is not configured, the generator uses `generate\_offline\_narrative()` to produce the narrative from the supplied findings. The resulting narrative is saved to the same output file:



```text

narrator/sample\_output.txt

```



The offline path does not require a Gemini API request. Both paths should use the verified findings rather than independently inventing or recalculating business figures.



\## Step 4 — Validate the Results



After the pipeline finishes, check the generated SQL reports, analysis outputs, findings JSON, and narrative.



The current numeric accuracy checklist expects the following verified results:



| Metric                             | Expected result |

| ---------------------------------- | --------------: |

| Cleaned revenue                    |      ₹97,358.30 |

| COD return rate                    |           44.4% |

| Highest-risk segment: COD + Tier-2 |           54.5% |

| Revenue reconciliation delta       |       ₹2,501.90 |

| Peak revenue month                 |      March 2026 |

| Peak-month revenue                 |      ₹20,318.90 |



The narrative accuracy checker should report `PASS` for all five numeric checks and an overall `PASS` when the expected values are present.



A successful text-matching check confirms that the expected figures appear in the narrative; it does not independently prove that every claim is factually correct. For stronger validation, compare the generated narrative against `narrator/findings.json` and the underlying SQL results.



\## End-to-End Execution Order



From the repository root, follow these stages in sequence:



1\. Initialize the SQLite database using `sql/schema.sql`.

2\. Load the data using `sql/seed\_data.sql`.

3\. Execute the reports in `sql/reports.sql`.

4\. Run `analysis/clean\_and\_eda.py`.

5\. Run `analysis/visualize.py`.

6\. Complete Part 2, Task 5 to write `narrator/findings.json`.

7\. Run `narrator/generate\_narrative.py` with a Gemini API key or without one.

8\. Review `narrator/sample\_output.txt` and validate the numeric results.



Following this sequence ensures that the business narrative is generated from the findings produced by the analysis pipeline and that the results can be reviewed and reproduced.



