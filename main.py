import argparse

import numpy as np
import torch

from dataset import GenomeDataset, pbmc_definition
from utils import sparse_mx_to_torch_sparse
from models import VariationalAutoEncoder, GMVariationalAutoEncoder, GMVariationalAutoEncoder_transformers
from training import Trainer
def main():

    parser = argparse.ArgumentParser(description="This script processes command line arguments.")
    
    parser.add_argument('--model-name', type=str, help="The model you want to use", default="GMVariationalAutoEncoder")
    parser.add_argument('--epochs', type=int, help="Number of epoch", default=5)
    parser.add_argument('--lr', type=int, help="Learning Rate", default=0.0001)
    parser.add_argument('--dataset', type=str, help="Dataset on which you wish to experiment", default="pbmc")
    parser.add_argument('--n_layers', type=int, help="Number of hidden layers", default=2)
    parser.add_argument('--hidden_dim', type=int, help="Hidden dimension", default=1000)
    parser.add_argument('--latent_dim', type=int, help="Latent dimension", default=100)
    parser.add_argument('--n_heads', type=int, help="Number of heads", default=8)
    parser.add_argument('--nb_classes', type=int, help="Number of classes", default=9)
    parser.add_argument('--batch_size', type=int, help="Batch size", default=100)
    parser.add_argument('--seed', type=int, help="Seed", default=42)
    parser.add_argument('--likelihood_distrib', type=str, help="Distrubtion prior used for the loss function", default="Poisson")
    parser.add_argument('--optimizer', type=str, help="Optimizer used for training", default="Adam")

    
    # Parse the arguments
    args = parser.parse_args()

    np.random.seed(args.seed)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Hyperparameters
    epochs = args.epochs
    batch_size = args.batch_size

    dataset_name = args.dataset
    if dataset_name == "pbmc":
        # Load dataset
        G = GenomeDataset(pbmc_definition, download=True, small=True)
        X = G.data
        y = G.labels
    if dataset_name == "brain_large":
        # Load dataset
        G = GenomeDataset(pbmc_definition, download=True, small=True)
        X = G.data
        y = G.labels

    X_torch = sparse_mx_to_torch_sparse(X).to(device)

    n_layers_encoder = args.n_layers
    latent_dim = args.latent_dim
    hidden_dim_encoder = args.hidden_dim   
    hidden_dim_decoder = args.hidden_dim
    n_layers_decoder = args.n_layers
    nb_classes = args.nb_classes
    input_feats = X_torch.shape[1]

    model_name = args.model_name
    if model_name == "VariationalAutoEncoder":
        # Initialize autoencoder
        autoencoder = VariationalAutoEncoder(input_feats, hidden_dim_encoder, hidden_dim_decoder, latent_dim, n_layers_encoder, n_layers_decoder).to(device)
    elif model_name == "GMVariationalAutoEncoder":
        # Initialize autoencoder
        autoencoder = GMVariationalAutoEncoder(input_feats, hidden_dim_encoder, hidden_dim_decoder, latent_dim, n_layers_encoder, n_layers_decoder, nb_classes).to(device)
    elif model_name == "GMVariationalAutoEncoder_transformers":
        autoencoder = GMVariationalAutoEncoder_transformers(input_feats, hidden_dim_encoder, hidden_dim_decoder, latent_dim, n_layers_encoder, n_layers_decoder, nb_classes).to(device)

    optimizer_name = args.optimizer
    if optimizer_name == "Adam":
        optimizer = torch.optim.Adam(autoencoder.parameters(), lr=args.lr)
    elif optimizer_name == "AdamW":
        optimizer = torch.optim.AdamW(autoencoder.parameters(), lr=args.lr)
    elif optimizer_name == "SGD":
        optimizer = torch.optim.SGD(autoencoder.parameters(), lr=args.lr)


    distribution_name = args.likelihood_distrib
    if distribution_name == "Poisson":
        distribution = torch.distributions.Poisson 
    if distribution_name == "NegativeBinomial":
        distribution = torch.distributions.NegativeBinomial
    if distribution_name == "ZeroInflatedPoisson":
        distribution = torch.distributions.ZeroInflatedPoisson
    if distribution_name == "ZeroInflatedNegativeBinomial":
        distribution = torch.distributions.ZeroInflatedNegativeBinomial

    idx = np.random.default_rng(seed=args.seed).permutation(len(X_torch))

    trainer = Trainer(X_torch, idx, autoencoder, optimizer, device)

    trainer.train(distribution, epochs, batch_size)

    # Save model
    torch.save(autoencoder.state_dict(), f'{args.model_name}.pth')

if __name__ == "__main__":
    main()