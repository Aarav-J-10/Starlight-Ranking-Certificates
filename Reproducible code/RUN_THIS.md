# Reproduce and verify

From the folder `Machine Learning Benchmarks`:

```bash
python -m pip install -r 03_Reproducible_Code/requirements.txt
python 03_Reproducible_Code/verify_headlines.py
```

To rerun the simulation, change to `03_Reproducible_Code`:

```bash
python run_benchmark.py --train-tasks 1800 --val-tasks 750 --train-pairs 400 --test-pairs 700 --reps 100 --seed 20261121 --out rerun_final
```

`run_benchmark.py` was copied unmodified from the original benchmark bundle. Script runs may take appreciable CPU time and depend on installed package/platform versions. Do not overwrite original benchmark results.

**Study boundary:** This code implements an *authored synthetic terminal steering-error model*, not the published Starlight robot mission simulator.
