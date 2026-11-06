# Growth Strategy Analyzer

A Python tool that automates the analysis of Méliuz cashback A/B tests. It reads one or more datasets, consolidates the key indicators per variant, recommends which group to scale and generates a presentable HTML report. It also keeps a local CSV history and, when credentials are configured, logs the result directly to the spreadsheet set in `.env`.

> The datasets and the user-facing labels in the report and in the spreadsheet are in Portuguese, as in the original take-home assignment.

## What it does

For each CSV in the `input/` folder, the application:

1. converts dates and currency values to proper types;
2. computes effective cashback and commission rates, buyers, sales, net value and per-buyer indicators for each group;
3. compares growth and economic return using deterministic, explainable rules;
4. recommends the variant with the best sustainable balance within the test;
5. generates an HTML report with the executive decision, trade-offs, a comparison table, a chart and a per-group breakdown;
6. logs the analysis to the first tab of a Google Sheets spreadsheet;
7. appends the result to a local CSV history, whether or not Google Sheets is configured.

Net value, used in the decision, is calculated as:

```text
net value = commission - cashback
```

Consolidated rates use the ratio between totals, not the simple average of daily percentages:

```text
effective cashback = total cashback / total sales
effective commission = total commission / total sales
```

## Architecture decisions

The solution is deterministic and has no mandatory AI dependency.

Analysis and recommendation run in Python to ensure:

- reproducibility;
- transparency;
- ease of testing;
- independence from any LLM vendor.

Tools such as Claude Code, Cursor or ChatGPT can trigger the pipeline later without changing the analytical engine.

## Prerequisites

- [Git](https://git-scm.com/)
- Python 3.11 or later (Python 3.13 recommended)
- Internet access to install dependencies
- Internet access when opening the report, since charts load Chart.js from a CDN
- Optional: a Google Cloud account and a Service Account to log results to Google Sheets

## Clone and install

Clone the repository and enter the project folder:

```bash
git clone https://github.com/victrauguxto/growth-strategy-analyzer.git
cd growth-strategy-analyzer
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On Linux or macOS:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Usage

### 1. Add the datasets

Create the `input/` folder if it doesn't exist and put the files to analyze in it:

```text
input/
├── dataset_01_parceiroA.csv
├── dataset_02_parceiroB.csv
└── dataset_03_parceiroC.csv
```

In a single run, the program processes every file matching `dataset*.csv`. Following the `dataset_XX_partnerName.csv` pattern is recommended, since the name shown in the report comes from the file name.

Each CSV must be UTF-8, comma-separated and contain exactly these columns (the column names are in Portuguese and must match exactly):

| Column | Expected type | Description |
| --- | --- | --- |
| `Data` | `YYYY-MM-DD` | Observation date |
| `Grupos de usuários` | text | Test variant, such as `Grupo 1` |
| `Parceiro` | text | Partner being analyzed |
| `compradores` | integer | Unique users who bought that day |
| `comissão` | BRL amount | Commission paid by the partner to Méliuz |
| `cashback` | BRL amount | Cashback paid out to users |
| `vendas totais` | BRL amount | GMV for the day |

Example:

```csv
Data,Grupos de usuários,Parceiro,compradores,comissão,cashback,vendas totais
2011-01-01,Grupo 1,Parceiro A,196,R$ 10.273,R$ 3.267,R$ 93.390
```

Currency values must follow the Brazilian format the project accepts, such as `R$ 10.273` or `R$ 10.273,50`.

### 2. Configure result logging

The recommended way to use the project is to log each analysis directly to Google Sheets. The `.env.example` file already contains the link to the original tracking spreadsheet: https://docs.google.com/spreadsheets/d/1zpI995GmocupeSbYQv2i5GeHXnf2U1fyVpIWSK7aPVM/edit?usp=sharing. To enable the integration, provide a Service Account JSON key with edit access to that spreadsheet and set the key's path in `.env`.

Regardless of the integration, each analysis is also appended to the local history at `data/test_results/test_results.csv`.

#### Recommended: write to the original spreadsheet

1. Put the Service Account JSON credentials file in the `credentials/` folder. For example:

   ```text
   credentials/credenciais-google.json
   ```

2. Copy the example configuration file.

   On Windows PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

   On Linux or macOS:

   ```bash
   cp .env.example .env
   ```

3. In `.env`, replace only the value of `GOOGLE_APPLICATION_CREDENTIALS` with the path to the JSON file. Keep `GOOGLE_SHEETS_SPREADSHEET_URL` with the link that came in `.env.example`:

   ```dotenv
   GOOGLE_APPLICATION_CREDENTIALS=credentials/credenciais-google.json
   GOOGLE_SHEETS_SPREADSHEET_URL=<link already provided in .env.example>
   ```

4. Make sure the e-mail in the key's `client_email` field has edit permission on the spreadsheet.

5. Run `python main.py`. For each processed dataset, the system appends a new row to the first tab of the spreadsheet set in `GOOGLE_SHEETS_SPREADSHEET_URL`.

The first tab must contain these headers (in Portuguese):

```text
Nome do teste | Data / Hora Execução | Descrição | Resultado | Decisão tomada
```

To use another spreadsheet, replace `GOOGLE_SHEETS_SPREADSHEET_URL`, share the new spreadsheet with the Service Account's `client_email` and keep the same headers.

To create your own credentials, create a Service Account in Google Cloud and enable the Google Sheets and Google Drive APIs. The key must be in JSON format.

Never publish `.env` or the Service Account JSON key. The `credentials/` folder, `.env` and JSON files are excluded from Git.

#### Alternative: local CSV only

No `.env` file is needed. Run the application and the CSV history is created automatically. Later runs append new rows to the same file without deleting previous results.

### 3. Run the analysis

From the project root, with the virtual environment active, run:

```bash
python main.py
```

Example terminal output:

```text
Processed: dataset_01_parceiroA.csv

Recommendation: Grupo 1
Decision: Growth economicamente caro
Confidence: High

Growth trade-off vs baseline:
Evaluated variant: Grupo 3
Buyers: +18.45%
Net value: -34.70%
Effective cashback: +3.26 pp

Report saved at:
C:\...\growth-strategy-analyzer\output\dataset_01_parceiroA_report.html
Open report:
file:///C:/.../growth-strategy-analyzer/output/dataset_01_parceiroA_report.html
```

The `file:///` address is clickable in modern terminals. To also open the reports automatically in the browser, use:

```bash
python main.py --open-report
```

Without the flag, no browser is opened.

### 4. Check the results

Reports are written to:

```text
output/<dataset_name>_report.html
```

Open the HTML file in a browser. Each report contains:

- an executive summary of the test;
- the recommended variant, decision type and confidence;
- a comparison between buyer response and economic result;
- buyer uplift and net value change against the baseline;
- a comparison of consolidated KPIs per group;
- a relative performance chart;
- a breakdown and notes per variant.

Each locally run test appends a row to:

```text
data/test_results/test_results.csv
```

The header is created only on the first run, and previous results are kept. When Google Sheets is configured and reachable, the same row is also appended to the first tab of the spreadsheet; the local history is still kept.

## Project structure

```text
growth-strategy-analyzer/
├── main.py                    # Orchestrates the analysis of all datasets
├── requirements.txt           # Python dependencies
├── .env.example               # Example Google Sheets configuration
├── input/                     # CSVs to analyze
├── output/                    # Generated HTML reports
├── data/test_results/         # Cumulative CSV history of runs
├── credentials/               # Local Google keys (not versioned)
├── utils/
│   ├── csv_reader.py          # Reading, cleaning and KPI calculation
│   ├── decision_engine.py     # Deterministic decision rules
│   ├── graph_builder.py       # Interactive Chart.js chart
│   ├── html_generator.py      # Executive report generation
│   └── sheets_client.py       # Persistence to Sheets or CSV
```

## Recommendation criteria

Each dataset is analyzed on its own. Different partners are never compared with each other.

The engine uses as the **baseline variant** the group with the lowest effective cashback rate. It is not called a control, because the dataset does not formally identify a control group.

The system identifies:

- economic winner: highest net value;
- growth winner: most buyers;
- efficiency winner: highest net value per buyer.

The decision follows explicit rules:

1. recommend a variant that leads in both buyers and net value;
2. when results are practically tied, prefer lower cashback and higher efficiency;
3. accept a growth variant with at least 5% more buyers when the net value loss does not exceed 10% and is proportionally smaller than the buyer gain;
4. reject growth when an economic loss above 10% is disproportionate to the uplift;
5. reject higher cashback when it produces no material buyer gain and reduces net value;
6. otherwise, keep the economic winner.

The engine returns a deterministic confidence of `high`, `medium` or `low`, along with the summary, reasons, trade-offs and comparisons against the baseline.

The main indicators shown are:

- effective cashback and commission rates over sales;
- total buyers;
- total sales and sales per buyer;
- total net value;
- net value per buyer.

The dataset does not include exposed users or traffic allocation. Buyers are therefore treated as the observed growth response, not as a conversion rate. The report does not compute statistical significance; the decision uses aggregated results and reproducible business rules. The recommendation should not be read as a linear projection to 100% of traffic.

## Troubleshooting

### No CSV was found

Make sure the files are in the `input/` folder, start with `dataset` and end with `.csv`.

### Error reading the columns

Check the UTF-8 encoding, the comma separator and the exact column names in the schema section. Accents are part of the expected names.

### The result was not sent to Sheets

The application automatically keeps the result in the local CSV history. Check:

- both `.env` variables;
- the path to the JSON key;
- whether the spreadsheet was shared with the Service Account's `client_email`;
- whether the Google Sheets and Google Drive APIs are enabled;
- whether the Service Account has edit permission.

### The chart doesn't show in the report

Connect to the internet when opening the HTML, since Chart.js is loaded from `cdn.jsdelivr.net`.
