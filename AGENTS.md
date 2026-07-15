# Instructions for AI tools

When the user asks to analyze a cashback A/B test:

1. Place or identify the CSV in `input/`.
2. Run:

   python main.py

3. Read the generated HTML report.
4. Return:
   - recommended group;
   - cashback percentage;
   - main reason;
   - report path.

Do not manually recalculate the KPIs.
Use the Python pipeline as the source of truth.