from dig.fairgraph.method import run
from dig.fairgraph.dataset import POKEC, NBA
import torch

# Load the dataset and split
pokec = POKEC(dataset_sample='pockec_z') # you may also choose 'pockec_n'

# Print the current working directory
import os
print("Current working directory:", os.getcwd())

# Train and evaluate
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
run_fairgraph = run()
run_fairgraph.run(device,dataset=pokec,model_type='Graphair',epochs=500,batch_size=1000,
            lr=1e-4,weight_decay=1e-5)