# Freelancer Time Tracker
### Written by Clair J. Sullivan, PhD
#### clair@clairsullivan.com
#### Last updated: 2025-01-08

To run:

```bash
conda create -n time_tracker python=3.11
conda activate time_tracker
pip install streamlit pandas numpy
streamlit run time_tracker.py
```

(There is a pyarrow error, but it can be ignored.)

This will create a series of CSV files on first run.  These can be edited directly in the event of an error in adding time entries or clients.
