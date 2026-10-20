# Run the improved P1–P5 notebook

Notebook: **FYP_P1_P5_Kaggle_IMPROVED_2_Hours.ipynb**

1. Create a fresh Kaggle notebook and import this file.
2. Add the same private **fyp-dataset** used for the successful balanced run.
3. Select **GPU T4 ×2**. No internet access is required.
4. Use **Save Version → Save & Run All** once.

No mode or model selection is needed. Leave the first cell unchanged for automatic dataset discovery. If a previous interactive session still owns the GPUs, stop it before starting this fresh run.

The main phase has twenty nine-minute jobs, with two running at a time. That is approximately 90 minutes of training-job time, followed by final all-five weights and results export. Target total: roughly **100–115 minutes**, with notebook safeguards at 118 minutes. This is a planned budget, not a measured Kaggle runtime. Kaggle queue and output publishing time are outside notebook control.

The method combines a four-second temporal CNN with frequency-band features, conditional action/sign heads, balancing over classes/people/sources/events, cross-person contrastive loss and moving-average weights. Each outer test uses a four-model cross-fit ensemble; each member fits three other people and validates on the fourth. Best validation checkpoints are retained. No test-person calibration or training on the laptop is used.

The notebook automatically reports gains and regressions against the balanced baseline if the dataset fingerprint and all test event IDs match. More compute does not guarantee an improved result, especially with only five people and two-person seated/cooking coverage.

Download these completed Output files:

- **FYP_Improved_All5_Model.zip** — compact inference weights, preprocessing scale, class order, model card and code.
- **FYP_all_checkpoints_and_results.zip** — evaluation weights, recoverable training checkpoints, histories, predictions, class graphs and comparisons.

Models are saved atomically during training. `run_completion.json` identifies completed tests and model status. `model_card.json` states whether final refits reached their selected epoch target. A failed worker or incomplete ensemble is not presented as a successful full evaluation. The all-five deployment refit does not have its own independent score.

Local delivery checks passed using CPU forward passes, synthetic loss checks, fixtures, saved random-weight loading and report/archive integration. GPU execution and actual accuracy have not been verified before your Kaggle run. No model was fitted locally.
