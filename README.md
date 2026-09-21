# QueryMind - Learning-Based Query Optimizer

A lightweight, research-oriented query optimizer in Python that explores how machine learning can assist and complement traditional database query optimization.

---

## 📌 Overview

Traditional database query optimizers estimate query execution costs using static heuristics, system statistics, and mathematical cost formulas. However, imprecise cardinality estimates-especially on complex multi-join queries or skewed data distributions-can lead optimizers to select suboptimal execution plans.

**QueryMind** investigates whether machine learning models (such as Random Forest, Gradient Boosting, or Neural Networks) can accurately predict cardinalities and execution runtimes to select more efficient execution plans.

---

## 🏛️ High-Level Architecture

```
                       SQL Query
                           │
                           ▼
                  ┌─────────────────┐
                  │   SQL Parser    │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Logical Plan   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Plan Enumerator │
                  └────────┬────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
      Plan A            Plan B            Plan C
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │Feature Extractor│
                  └────────┬────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐
    │ Traditional CBO  │      │ ML Cost & Card   │
    │ Cost Estimator   │      │    Estimator     │
    └─────────┬────────┘      └─────────┬────────┘
              │                         │
              └────────────┬────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Plan Selection  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  SQLite Engine  │
                  └─────────────────┘
```

---

## 🚀 Quick Setup & Execution

QueryMind includes automated setup scripts for both **Linux/macOS** (`run.sh`) and **Windows** (`run.ps1`). These scripts automatically create a Python virtual environment (`.venv`), install required dependencies, and launch the CLI.

### 1. Linux / macOS Setup (`run.sh`)

#### Standard Run (Demo Query Optimization):
```bash
./run.sh
```

#### Train the ML Models with Epochs:
To train the Cardinality and Cost models on synthetic workload data:
```bash
./run.sh -Train -Epochs 50
```

#### Run Unit Tests & Experimental Evaluation Benchmark:
```bash
./run.sh --test
```

#### Optimize a Specific Custom SQL Query:
```bash
./run.sh --query "SELECT * FROM students s JOIN enrollments e ON s.id = e.student_id WHERE s.cgpa > 8.0;"
```

---

### 2. Windows PowerShell Setup (`run.ps1`)

#### Standard Run (Demo Query Optimization):
```powershell
.\run.ps1
```

#### Train the ML Models with Epochs:
```powershell
.\run.ps1 -Train -Epochs 50
```
*(or using PowerShell parameter syntax: `.\run.ps1 -Train -Epochs 50`)*

#### Run Unit Tests & Benchmark:
```powershell
.\run.ps1 --test
```

#### Optimize a Specific Query:
```powershell
.\run.ps1 -Query "SELECT * FROM students s JOIN enrollments e ON s.id = e.student_id WHERE s.cgpa > 8.0;"
```

---

## 📂 Project Structure

```
SQL_optimizer/
├── README.md               # Detailed project documentation
├── requirements.txt        # Python dependency list
├── pyproject.toml          # Package configuration
├── run.sh                  # Linux/macOS automated setup & runner script
├── run.ps1                 # Windows PowerShell setup & runner script
├── cli.py                  # CLI entrypoint for training, testing, & optimization
│
├── src/                    # Core source code
│   ├── parser/             # SQL parser & Relational Algebra AST
│   │   ├── ast.py          # AST Node classes (Selection, Projection, Join, TableScan)
│   │   └── sql_parser.py   # SQL query string parser
│   ├── planner/            # Logical & Physical planners
│   │   ├── logical_plan.py # Selection pushdown & rewrite rules
│   │   ├── physical_plan.py# Physical operators (SeqScan, IndexScan, HashJoin, NLJ)
│   │   └── join_enumerator.py # Candidate physical plan space generator
│   ├── features/           # Feature engineering & Database statistics
│   │   ├── statistics.py   # Catalog statistics (row counts, histograms, distincts)
│   │   └── query_features.py# Plan & query feature vectorizer
│   ├── executor/           # SQLite database engine & workload generator
│   │   └── database.py     # SQLite database harness & synthetic workloads
│   ├── optimizer/          # Query optimizers
│   │   ├── cost_model.py   # Traditional CBO cost model implementation
│   │   ├── baseline.py     # Traditional CBO baseline optimizer
│   │   └── ml_optimizer.py # ML-guided query optimizer
│   ├── models/             # Machine Learning models
│   │   ├── cardinality.py  # ML Cardinality estimator model
│   │   └── cost_predictor.py# ML Cost & runtime predictor model
│   └── evaluation/         # Experimental evaluation
│       ├── metrics.py      # Q-Error, Regret, Latency percentiles
│       └── benchmark.py    # Benchmark suite comparing Baseline vs ML
│
├── data/                   # Data storage
│   ├── raw/
│   ├── processed/          # Generated training datasets (workload_dataset.csv)
│   └── workloads/
│
├── models/                 # Saved trained model artifacts (.pkl files)
└── tests/                  # Pytest unit test suite
    ├── test_parser.py
    ├── test_planner.py
    ├── test_cost_model.py
    └── test_optimizer.py
```

---

## 🧮 Core Concepts & Experimental Metrics

### 1. Relational Algebra Representation
Queries are converted into relational algebra trees:
- Selection ($\sigma$)
- Projection ($\pi$)
- Join ($\bowtie$)
- Table Scan

### 2. Candidate Plan Enumeration
For a given SQL query, QueryMind explores permutations of join orderings and physical operator choices:
- `(A ⋈ B) ⋈ C` vs `(B ⋈ C) ⋈ A`
- `SeqScan` vs `IndexScan`
- `NestedLoopJoin` vs `HashJoin`

### 3. Key Evaluation Metrics
- **Q-Error**: Quantifies cardinality estimation quality independent of scale:
  $$\text{Q-Error} = \max\left(\frac{\text{Actual}}{\text{Predicted}}, \frac{\text{Predicted}}{\text{Actual}}\right)$$
- **Regret (%)**: Measures how much slower the selected plan is compared to the optimal execution plan:
  $$\text{Regret} = \frac{\text{Latency}_{\text{Selected}} - \text{Latency}_{\text{Optimal}}}{\text{Latency}_{\text{Optimal}}} \times 100\%$$
- **Plan Selection Accuracy (%)**: Percentage of queries where the optimizer selects the best plan.
- **P50 / P95 / P99 Latency**: Percentiles of execution runtimes across workloads.

---

## 🔬 Research Questions Explored

1. Can ML predict cardinality more accurately than a simple statistical baseline?
2. Does better cardinality estimation translate directly to faster query execution?
3. How does ML optimizer performance scale as query join depth increases?
4. What is the inference latency overhead of running ML models during query compilation?

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
