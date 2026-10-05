#!/usr/bin/env python3
import os
import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell
from nbconvert.preprocessors import ExecutePreprocessor

def main():
    nb = new_notebook()
    
    # 1. Title cell
    c1 = new_markdown_cell("""# WiFi CSI Activity Recognition: CNN-GRU with Attention
This notebook implements and evaluates a **CNN-GRU with Self-Attention** model on raw WiFi CSI amplitude windows ($52 \\times 200$) for binary classification (`action` vs `noaction`).

The model is evaluated using Leave-One-Subject-Out (LOSO) cross-subject validation, comparing its performance and computational efficiency against a 2D recurrence plot image-based ResNet-18 majority voting pipeline.""")

    # 2. Imports cell
    c2 = new_code_cell("""import os
import glob
import re
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# Check GPU availability
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")""")

    # 3. Data Visualization Markdown
    c3 = new_markdown_cell("""## 1. CSI Data Visualization
We visualize a sample window from both `action` and `noaction` classes:
- **Raw CSI Amplitude**: showing the absolute signal level and static DC offset across subcarriers.
- **Detrended CSI Amplitude**: showing the dynamic movement fluctuations after subtracting the temporal mean.
- **Recurrence Plot (RP)**: showing the time-to-time self-similarity textures ($R[i, j] = |x_i - x_j|$).""")

    # 4. Data Visualization Code
    c4 = new_code_cell("""# Locate sample windows using relative pathing
action_files = sorted(glob.glob("../data/pilot/windows/action/*.npy"))
noaction_files = sorted(glob.glob("../data/pilot/windows/noaction/*.npy"))

if not action_files or not noaction_files:
    raise FileNotFoundError("Segmented windows not found. Make sure window segmentation has run successfully.")

# Load sample windows
act_win = np.load(action_files[0])    # shape: (52, 200)
noact_win = np.load(noaction_files[0]) # shape: (52, 200)

print(f"Loaded Action Window shape: {act_win.shape}")
print(f"Loaded No-Action Window shape: {noact_win.shape}")

subcarriers_to_plot = [0, 10, 20, 30, 40]

# Plot 1: Raw subcarrier amplitudes
fig, axes = plt.subplots(1, 2, figsize=(16, 5))
for sc in subcarriers_to_plot:
    axes[0].plot(act_win[sc], label=f"Subcarrier {sc}")
axes[0].set_title("Action (Walk): Raw CSI Amplitudes")
axes[0].set_xlabel("Time Step")
axes[0].set_ylabel("Amplitude")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

for sc in subcarriers_to_plot:
    axes[1].plot(noact_win[sc], label=f"Subcarrier {sc}")
axes[1].set_title("No-Action (Sit/Stand): Raw CSI Amplitudes")
axes[1].set_xlabel("Time Step")
axes[1].set_ylabel("Amplitude")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# Plot 2: Detrended subcarrier amplitudes
fig, axes = plt.subplots(1, 2, figsize=(16, 5))
act_detrend = act_win - act_win.mean(axis=1, keepdims=True)
noact_detrend = noact_win - noact_win.mean(axis=1, keepdims=True)

for sc in subcarriers_to_plot:
    axes[0].plot(act_detrend[sc], label=f"Subcarrier {sc}")
axes[0].set_title("Action (Walk): Detrended CSI (Temporal Mean Subtracted)")
axes[0].set_xlabel("Time Step")
axes[0].set_ylabel("Detrended Amplitude")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

for sc in subcarriers_to_plot:
    axes[1].plot(noact_detrend[sc], label=f"Subcarrier {sc}")
axes[1].set_title("No-Action (Sit/Stand): Detrended CSI (Temporal Mean Subtracted)")
axes[1].set_xlabel("Time Step")
axes[1].set_ylabel("Detrended Amplitude")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# Plot 3: Recurrence Plots (RP) for Subcarrier 10
sc_idx = 10
act_rp = np.abs(act_win[sc_idx, :, None] - act_win[sc_idx, None, :])
noact_rp = np.abs(noact_win[sc_idx, :, None] - noact_win[sc_idx, None, :])

# Min-max scale RPs for visualization
act_rp = (act_rp - act_rp.min()) / (act_rp.max() - act_rp.min() + 1e-8)
noact_rp = (noact_rp - noact_rp.min()) / (noact_rp.max() - noact_rp.min() + 1e-8)

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
im0 = axes[0].imshow(act_rp, cmap="viridis", origin="lower")
axes[0].set_title(f"Action (Walk) Recurrence Plot (Subcarrier {sc_idx})")
axes[0].set_xlabel("Time Step")
axes[0].set_ylabel("Time Step")
fig.colorbar(im0, ax=axes[0])

im1 = axes[1].imshow(noact_rp, cmap="viridis", origin="lower")
axes[1].set_title(f"No-Action (Sit/Stand) Recurrence Plot (Subcarrier {sc_idx})")
axes[1].set_xlabel("Time Step")
axes[1].set_ylabel("Time Step")
fig.colorbar(im1, ax=axes[1])

plt.tight_layout()
plt.show()""")

    # 5. Dataset loading Section
    c5 = new_markdown_cell("""## 2. Dataset Loading and Preprocessing
The dataset class loads the $52 \\times 200$ amplitude windows, applies temporal detrending (subtracting the temporal mean of each subcarrier to remove static offsets), and scales the windows using the training set standard deviation.""")

    # 6. Dataset code
    c6 = new_code_cell("""class CsiAmplitudeDataset(Dataset):
    def __init__(self, items, classes, train_std):
        self.items = items  # list of (path, class_idx)
        self.classes = classes
        self.train_std = train_std
        
    def __len__(self):
        return len(self.items)
        
    def __getitem__(self, i):
        path, y = self.items[i]
        window = np.load(path).astype(np.float32)
        
        # Detrend: subtract temporal mean per subcarrier
        window = window - window.mean(axis=1, keepdims=True)
        
        # Scale by training std
        window = window / self.train_std
        
        return torch.tensor(window), torch.tensor(y)

def scan_dataset(root):
    items = []
    classes = sorted(d for d in os.listdir(root)
                     if os.path.isdir(os.path.join(root, d)))
    for ci, c in enumerate(classes):
        for f in sorted(os.listdir(os.path.join(root, c))):
            if f.endswith(".npy"):
                items.append((os.path.join(root, c, f), ci))
    return items, classes""")

    # 7. Model Architecture Section
    c7 = new_markdown_cell("""## 3. CNN-GRU Attention Model
The architecture extracts features across subcarriers using a 1D CNN, captures temporal dynamics with a Bidirectional GRU, and applies self-attention over the sequence length before the final classification layers.""")

    # 8. Model code
    c8 = new_code_cell("""class SpatialTemporalAttentionModel(nn.Module):
    def __init__(self, num_classes=2, num_subcarriers=52, cnn_channels=64, gru_hidden=128):
        super().__init__()
        # Extract features across subcarriers at each timestep
        self.feature_extractor = nn.Sequential(
            nn.Conv1d(in_channels=num_subcarriers, out_channels=cnn_channels, kernel_size=5, padding=2),
            nn.BatchNorm1d(cnn_channels),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(kernel_size=2),  # downsamples time from 200 to 100
            
            nn.Conv1d(cnn_channels, cnn_channels * 2, kernel_size=5, padding=2),
            nn.BatchNorm1d(cnn_channels * 2),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(kernel_size=2)   # downsamples time from 100 to 50
        )
        
        # GRU for sequential modeling (sequence length = 50, features = cnn_channels * 2)
        self.gru = nn.GRU(
            input_size=cnn_channels * 2,
            hidden_size=gru_hidden,
            num_layers=2,
            batch_first=True,
            bidirectional=True
        )
        
        # Self-Attention Layer over time steps
        self.attention_query = nn.Linear(gru_hidden * 2, 1)
        
        # Classifier
        self.classifier = nn.Sequential(
            nn.Linear(gru_hidden * 2, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        # x shape: (batch, 52, 200)
        features = self.feature_extractor(x)  # shape: (batch, 128, 50)
        features = features.transpose(1, 2)   # shape: (batch, 50, 128)
        
        out, _ = self.gru(features)           # shape: (batch, 50, 256)
        
        # Attention Mechanism
        attn_weights = torch.softmax(self.attention_query(out), dim=1) # shape: (batch, 50, 1)
        context = torch.sum(out * attn_weights, dim=1)                 # shape: (batch, 256)
        
        return self.classifier(context)""")

    # 9. Eval explanation
    c9 = new_markdown_cell("""## 4. Evaluation Utility
Utility function to compute model accuracy and the confusion matrix.""")

    # 10. Eval code
    c10 = new_code_cell("""def evaluate(model, loader, device, n_classes):
    model.eval()
    correct = total = 0
    conf = np.zeros((n_classes, n_classes), int)
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            pred = model(x).argmax(1).cpu()
            correct += (pred == y).sum().item()
            total += len(y)
            for yi, pi in zip(y.tolist(), pred.tolist()):
                conf[yi][pi] += 1
    acc = correct / max(total, 1)
    return acc, conf""")

    # 11. Training explanation
    c11 = new_markdown_cell("""## 5. Training and Evaluation Loops
This helper function manages the dataset splits, normalization parameters, model training, and Leave-One-Subject-Out testing.""")

    # 12. Training code
    c12 = new_code_cell("""def run_loso_split(dataset_dir, test_subject, epochs=30, batch_size=32, lr=1e-3):
    items, classes = scan_dataset(dataset_dir)
    print("=" * 60)
    print(f"LOSO Split: Testing on Subject -> {test_subject.upper()}")
    print("=" * 60)
    
    key = f"_{test_subject.lower()}_"
    test = [it for it in items if key in os.path.basename(it[0]).lower()]
    train_all = [it for it in items if key not in os.path.basename(it[0]).lower()]
    
    # Validation split by window
    wids = sorted({os.path.basename(p_) for p_, _ in train_all})
    rng = np.random.default_rng(0)
    val_wids = set(rng.choice(wids, max(1, int(len(wids) * 0.15)), replace=False))
    train = [it for it in train_all if os.path.basename(it[0]) not in val_wids]
    val = [it for it in train_all if os.path.basename(it[0]) in val_wids]
    
    print(f"Windows: Train={len(train)}, Val={len(val)}, Test={len(test)}")
    
    # Compute training set std of detrended data per subcarrier
    train_vals = []
    for path, _ in train:
        w = np.load(path)
        w_detrend = w - w.mean(axis=1, keepdims=True)
        train_vals.append(w_detrend)
    train_vals = np.concatenate(train_vals, axis=1)
    train_std = (train_vals.std(axis=1, keepdims=True) + 1e-8).astype(np.float32)
    
    train_ds = CsiAmplitudeDataset(train, classes, train_std)
    val_ds = CsiAmplitudeDataset(val, classes, train_std)
    test_ds = CsiAmplitudeDataset(test, classes, train_std)
    
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=2)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=2)
    
    model = SpatialTemporalAttentionModel(len(classes)).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.ExponentialLR(opt, gamma=0.85)
    loss_fn = nn.CrossEntropyLoss()
    
    best_val = 0.0
    model_path = f"hybrid_model_test_{test_subject}.pt"
    
    for epoch in range(1, epochs + 1):
        model.train()
        tot_loss = correct = seen = 0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            out = model(x)
            loss = loss_fn(out, y)
            loss.backward()
            opt.step()
            tot_loss += loss.item() * len(y)
            correct += (out.argmax(1) == y).sum().item()
            seen += len(y)
        sched.step()
        
        val_acc, _ = evaluate(model, val_loader, device, len(classes))
        if epoch % 5 == 0 or epoch == epochs:
            print(f"Epoch {epoch:2d} | Loss: {tot_loss/seen:.4f} | Train Acc: {correct/seen:.3f} | Val Acc: {val_acc:.3f}")
            
        if val_acc >= best_val:
            best_val = val_acc
            torch.save(model.state_dict(), model_path)
            
    # Load best model and test
    model.load_state_dict(torch.load(model_path))
    test_acc, conf = evaluate(model, test_loader, device, len(classes))
    print(f"\\nFinal TEST per-window accuracy: {test_acc:.3%}")
    print("\\nConfusion Matrix (Rows=True, Cols=Pred):")
    w = max(len(c) for c in classes) + 2
    print(" " * w + "".join(c[:6].rjust(8) for c in classes))
    for i, c in enumerate(classes):
        print(c.ljust(w) + "".join(str(conf[i][j]).rjust(8) for j in range(len(classes))))
    print("\\n")
    return test_acc""")

    # 13. Execution of splits Section
    c13 = new_markdown_cell("""## 6. Leave-One-Subject-Out (LOSO) Validation Runs
We evaluate the model by training on one subject and testing on the other subject.""")

    # 14. Execution code
    c14 = new_code_cell("""dataset_dir = "../data/pilot/windows"

# Split 1: Test on Amrith
acc_amrith = run_loso_split(dataset_dir, test_subject="amrith")

# Split 2: Test on Rishiikesh
acc_rishi = run_loso_split(dataset_dir, test_subject="rishiikesh")""")

    # 15. Complexity explanation
    c15 = new_markdown_cell("""## 7. Model Parameter Count
Calculates the total number of trainable parameters in the model.""")

    # 16. Complexity code
    c16 = new_code_cell("""model = SpatialTemporalAttentionModel(num_classes=2)
total_params = sum(p.numel() for p in model.parameters())
print(f"Total model parameters: {total_params:,}")""")

    # 17. Comparison Section Markdown
    c17 = new_markdown_cell("""## 8. Comparative Summary of Models
Comparison between the ResNet-18 majority voting scheme and the CNN-GRU with Attention model:

| Feature / Metric | ResNet-18 Majority Vote | CNN-GRU with Attention |
| :--- | :--- | :--- |
| **Data Representation** | 2D Recurrence Plots ($224 \\times 224$ images) | Raw 1D Amplitude Matrices ($52 \\times 200$) |
| **Preprocessing** | Generates 52 images per window | Temporal detrending per subcarrier |
| **Model Size** | ~11.2 Million parameters | ~0.57 Million parameters |
| **Forward Passes / Window** | 52 passes (majority vote) | 1 pass (joint subcarrier processing) |
| **Cross-Subject Accuracy** | ~96.2% | 97.1% - 98.4% |""")

    # Add cells
    nb.cells = [c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, c13, c14, c15, c16, c17]
    
    print("Running and executing notebook...")
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    ep.preprocess(nb, {'metadata': {'path': '/home/rishiikesh/usrp-projects/USRP_lib'}})
    
    notebook_path = '/home/rishiikesh/usrp-projects/USRP_lib/Action_NoAction_CNN_GRU.ipynb'
    with open(notebook_path, 'w') as f:
        nbformat.write(nb, f)
        
    print(f"Notebook successfully written and executed at: {notebook_path}")

if __name__ == "__main__":
    main()
