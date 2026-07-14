#!/usr/bin/env python3

import sys
import os
import time
import argparse
import json
from pathlib import Path

# Add project root to path

BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR / 'websites'))

from gan_data_generator import SyntheticUserFactory, DEFAULT_EPOCHS

# SEED DATA EXTRACTION (from db_seeder patterns)

def get_seed_data_for_site(site_type):
    """
    Extracts seed data from db_seeder for a given site type.
    Returns list of user tuples: (username, password, email, name, role, balance)
    """
    from shared.db_seeder import SITE_DATA

    if site_type in SITE_DATA:
        return SITE_DATA[site_type]['honeypot']['users']
    else:
        # Fallback to banking

        return SITE_DATA['banking']['honeypot']['users']

# TRAINING

def train_model(site_type, epochs, verbose=True):
    """
    Trains a GAN model for a specific site type.
    Returns the trained factory and elapsed time.
    """
    seed_data = get_seed_data_for_site(site_type)

    if verbose:
        print(f"\n{'='*60}")
        print(f"  TRAINING GAN FOR: {site_type.upper()}")
        print(f"  Seed data: {len(seed_data)} users")
        print(f"  Epochs: {epochs}")
        print(f"{'='*60}")

    factory = SyntheticUserFactory(model_name=site_type)

    start = time.time()
    factory.train(seed_data, epochs=epochs, verbose=verbose)
    elapsed = time.time() - start

    # Save model

    save_path = factory.save_model()

    if verbose:
        print(f"   Model saved to {save_path}")
        print(f"    Training time: {elapsed:.1f}s")

    return factory, elapsed

# VALIDATION

def validate_model(site_type, verbose=True):
    """
    Loads a trained model and validates generated data quality.
    """
    factory = SyntheticUserFactory(model_name=site_type)
    loaded = factory.load_model()

    if not loaded:
        print(f"   No trained model found for '{site_type}'")
        return None

    seed_data = get_seed_data_for_site(site_type)
    metrics = factory.validate(seed_data, n_samples=100)

    if verbose:
        print(f"\n{'='*60}")
        print(f"  VALIDATION REPORT: {site_type.upper()}")
        print(f"{'='*60}")
        print(f"  {'Feature':<15} {'Real Mean':>12} {'Fake Mean':>12} {'Diff%':>8}")
        print(f"  {''*50}")
        for feature, vals in metrics.items():
            if isinstance(vals, dict):
                print(f"  {feature:<15} {vals['real_mean']:>12.2f} {vals['fake_mean']:>12.2f} "
                      f"{vals['mean_diff_pct']:>7.1f}%")
        print(f"\n   Watermark Integrity: {metrics.get('watermark_integrity', 'N/A')}")

    # Generate sample users for inspection

    sample_users = factory.generate_users(5)
    if verbose:
        print(f"\n  {''*50}")
        print(f"  SAMPLE GENERATED USERS:")
        print(f"  {''*50}")
        for u in sample_users:
            print(f"  {u['full_name']:<20} | {u['email']:<35} | "
                  f"${u['balance']:>10,.2f} | Score: {u['credit_score']} | Age: {u['age']}")

    return metrics

# MAIN

def main():
    parser = argparse.ArgumentParser(
        description='Train WGAN-GP for DeceptiCloud synthetic data generation'
    )
    parser.add_argument('--site', type=str, default='all',
                        choices=['all', 'banking', 'ecommerce', 'healthcare',
                                 'blog', 'api_service', 'corporate', 'admin_panel'],
                        help='Site type to train for (default: all)')
    parser.add_argument('--epochs', type=int, default=DEFAULT_EPOCHS,
                        help=f'Number of training epochs (default: {DEFAULT_EPOCHS})')
    parser.add_argument('--validate', action='store_true',
                        help='Only validate existing trained model(s), do not train')
    args = parser.parse_args()

    print("\n" + "" * 60)
    print("  DeceptiCloud — GAN Training Pipeline")
    print("  WGAN-GP (Wasserstein GAN with Gradient Penalty)")
    print("" * 60)

    all_sites = ['banking', 'ecommerce', 'healthcare', 'blog',
                 'api_service', 'corporate', 'admin_panel']
    sites = all_sites if args.site == 'all' else [args.site]

    if args.validate:
        print(f"\n  Mode: VALIDATION ONLY")
        for site in sites:
            validate_model(site)
        print(f"\n{'='*60}")
        print(f"   Validation complete")
        print(f"{'='*60}\n")
        return

    # Training

    total_start = time.time()
    results = {}

    for site in sites:
        factory, elapsed = train_model(site, args.epochs)
        results[site] = {
            'training_time': elapsed,
        }

        # Validate immediately after training

        metrics = validate_model(site)
        if metrics:
            results[site]['validation'] = metrics

    total_elapsed = time.time() - total_start

    # Summary

    print(f"\n{''*60}")
    print(f"  TRAINING COMPLETE")
    print(f"{''*60}")
    print(f"  Sites trained: {len(sites)}")
    print(f"  Epochs per site: {args.epochs}")
    print(f"  Total time: {total_elapsed:.1f}s")
    print(f"\n  Per-site breakdown:")
    for site, info in results.items():
        print(f"    {site:<15} → {info['training_time']:.1f}s")
    print(f"{''*60}\n")

if __name__ == '__main__':
    main()
