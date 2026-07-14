import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
import string
import logging
import json
import threading
from pathlib import Path
import sys

# Central config

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
from config import (
    GAN_WATERMARK_DECIMAL, GAN_WATERMARK_RATIO, GAN_DEFAULT_EPOCHS,
    GAN_MODE_COLLAPSE_CHECK_INTERVAL, GAN_MODE_COLLAPSE_STD_THRESHOLD,
)

logger = logging.getLogger('gan_generator')

# CONFIGURATION

LATENT_DIM = 32        # Dimension of noise vector
HIDDEN_DIM = 128       # Hidden layer width
OUTPUT_DIM = 4         # [Balance, CreditScore, Age, TransactionCount]
WATERMARK_DECIMAL = GAN_WATERMARK_DECIMAL
WATERMARK_RATIO = GAN_WATERMARK_RATIO  # (#28) Only watermark 30% of users

# Training hyperparameters

DEFAULT_EPOCHS = GAN_DEFAULT_EPOCHS
CRITIC_ITERS = 5           # Train critic 5x per generator step
LEARNING_RATE = 1e-4       # Adam LR (standard for WGAN-GP)
BETA1, BETA2 = 0.0, 0.9   # Adam betas (WGAN-GP standard)
GP_LAMBDA = 10.0           # Gradient penalty coefficient
BATCH_SIZE = 32            # Batch size

# Mode collapse detection

COLLAPSE_CHECK_INTERVAL = GAN_MODE_COLLAPSE_CHECK_INTERVAL
COLLAPSE_STD_THRESHOLD = GAN_MODE_COLLAPSE_STD_THRESHOLD

# Paths

MODEL_DIR = Path(__file__).parent / 'models'

# MODEL ARCHITECTURE (WGAN-GP)

class Generator(nn.Module):
    """
    Generator Network: Latent Noise → User Profile Numerics
    Uses LayerNorm for stable CPU training.
    """
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(LATENT_DIM, HIDDEN_DIM),
            nn.LayerNorm(HIDDEN_DIM),
            nn.LeakyReLU(0.2),
            nn.Linear(HIDDEN_DIM, HIDDEN_DIM),
            nn.LayerNorm(HIDDEN_DIM),
            nn.LeakyReLU(0.2),
            nn.Linear(HIDDEN_DIM, HIDDEN_DIM // 2),
            nn.LayerNorm(HIDDEN_DIM // 2),
            nn.LeakyReLU(0.2),
            nn.Linear(HIDDEN_DIM // 2, OUTPUT_DIM),
        )

    def forward(self, z):
        return self.net(z)

class Critic(nn.Module):
    """
    Critic Network (WGAN): User Profile → Realness Score
    No sigmoid — outputs unbounded Wasserstein distance estimate.
    Uses Dropout for regularization.
    """
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(OUTPUT_DIM, HIDDEN_DIM),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.1),
            nn.Linear(HIDDEN_DIM, HIDDEN_DIM),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.1),
            nn.Linear(HIDDEN_DIM, HIDDEN_DIM // 2),
            nn.LeakyReLU(0.2),
            nn.Linear(HIDDEN_DIM // 2, 1),
        )

    def forward(self, x):
        return self.net(x)

# GRADIENT PENALTY

def compute_gradient_penalty(critic, real_data, fake_data):
    """
    Calculates the gradient penalty for WGAN-GP.
    Enforces the 1-Lipschitz constraint on the critic.
    """
    batch_size = real_data.size(0)
    alpha = torch.rand(batch_size, 1)
    alpha = alpha.expand_as(real_data)

    # Interpolate between real and fake

    interpolated = alpha * real_data + (1 - alpha) * fake_data
    interpolated.requires_grad_(True)

    # Critic score on interpolated

    d_interpolated = critic(interpolated)

    # Compute gradients

    gradients = torch.autograd.grad(
        outputs=d_interpolated,
        inputs=interpolated,
        grad_outputs=torch.ones_like(d_interpolated),
        create_graph=True,
        retain_graph=True,
    )[0]

    # Gradient penalty

    gradients = gradients.view(batch_size, -1)
    gradient_norm = gradients.norm(2, dim=1)
    penalty = GP_LAMBDA * ((gradient_norm - 1) ** 2).mean()
    return penalty

# DATA NORMALIZATION

class DataNormalizer:
    """Normalizes/denormalizes data to [-1, 1] range for stable GAN training."""

    def __init__(self):
        self.min_vals = None
        self.max_vals = None

    def fit(self, data):
        """Learn min/max from training data."""
        self.min_vals = data.min(axis=0)
        self.max_vals = data.max(axis=0)
        # Avoid division by zero

        self.range = self.max_vals - self.min_vals
        self.range[self.range == 0] = 1.0

    def transform(self, data):
        """Normalize to [-1, 1]."""
        return 2 * (data - self.min_vals) / self.range - 1

    def inverse_transform(self, data):
        """Denormalize from [-1, 1] back to original range."""
        return (data + 1) / 2 * self.range + self.min_vals

    def save(self, path):
        """Save normalizer parameters."""
        np.savez(path, min_vals=self.min_vals, max_vals=self.max_vals, range=self.range)

    def load(self, path):
        """Load normalizer parameters."""
        d = np.load(path)
        self.min_vals = d['min_vals']
        self.max_vals = d['max_vals']
        self.range = d['range']

# SYNTHETIC USER FACTORY

class SyntheticUserFactory:
    """
    Main class for training the GAN and generating synthetic users.
    Supports model persistence and proper WGAN-GP training.
    """

    def __init__(self, model_name='default'):
        self.generator = Generator()
        self.critic = Critic()
        self.normalizer = DataNormalizer()
        self.is_trained = False
        self.model_name = model_name
        self.training_history = {'critic_loss': [], 'generator_loss': [], 'wasserstein_dist': []}

    def _prepare_training_data(self, seed_data):
        """
        Converts seed data tuples into normalized tensors.
        seed_data format: [(username, password, email, name, role, balance), ...]
        """
        real_samples = []
        for user in seed_data:
            balance = float(user[5]) if len(user) > 5 else random.uniform(500, 50000)
            credit_score = min(850, max(300, 600 + (balance / 1000) + random.gauss(0, 30)))
            age = random.randint(22, 70)
            tx_count = max(1, int(random.gauss(25, 15)))
            real_samples.append([balance, credit_score, age, tx_count])

        raw_data = np.array(real_samples, dtype=np.float32)

        # (#29) Fit normalizer on RAW data first, THEN augment

        self.normalizer.fit(raw_data)

        # Augment the data by adding noise to increase training set size

        augmented = []
        for _ in range(max(1, 200 // len(raw_data))):  # Ensure at least 200 samples
            noisy = raw_data + np.random.normal(0, 0.02 * raw_data.std(axis=0), raw_data.shape)
            augmented.append(noisy)
        augmented_data = np.concatenate(augmented, axis=0)

        # Transform using normalizer fitted on raw data

        normalized = self.normalizer.transform(augmented_data)

        # (#27) Store raw training tensor for validation

        self._training_data_raw = raw_data.copy()

        return torch.tensor(normalized, dtype=torch.float32)

    def train(self, seed_data, epochs=DEFAULT_EPOCHS, verbose=True):
        """
        Full WGAN-GP training loop.
        
        Args:
            seed_data: List of user tuples from db_seeder
            epochs: Number of training epochs (default: 2000)
            verbose: Print progress every 100 epochs
        """
        if not seed_data:
            logger.warning("No seed data provided. Cannot train GAN.")
            return

        real_tensor = self._prepare_training_data(seed_data)
        n_samples = real_tensor.size(0)

        # Optimizers (WGAN-GP standard: Adam with β1=0, β2=0.9)

        opt_G = optim.Adam(self.generator.parameters(), lr=LEARNING_RATE, betas=(BETA1, BETA2))
        opt_C = optim.Adam(self.critic.parameters(), lr=LEARNING_RATE, betas=(BETA1, BETA2))

        if verbose:
            logger.info(f" Training WGAN-GP on {n_samples} samples for {epochs} epochs...")
            print(f"   Training WGAN-GP on {n_samples} samples for {epochs} epochs...")

        self.generator.train()
        self.critic.train()

        for epoch in range(epochs):
            # Train Critic (5 iterations per generator step)

            critic_losses = []
            for _ in range(CRITIC_ITERS):
                # Sample real batch

                idx = torch.randint(0, n_samples, (min(BATCH_SIZE, n_samples),))
                real_batch = real_tensor[idx]

                # Generate fake batch

                z = torch.randn(real_batch.size(0), LATENT_DIM)
                fake_batch = self.generator(z).detach()

                # Critic scores

                real_score = self.critic(real_batch).mean()
                fake_score = self.critic(fake_batch).mean()

                # Gradient penalty

                gp = compute_gradient_penalty(self.critic, real_batch, fake_batch)

                # Wasserstein loss + GP

                critic_loss = fake_score - real_score + gp

                opt_C.zero_grad()
                critic_loss.backward()
                opt_C.step()

                critic_losses.append(critic_loss.item())

            # Train Generator

            z = torch.randn(min(BATCH_SIZE, n_samples), LATENT_DIM)
            fake_batch = self.generator(z)
            gen_loss = -self.critic(fake_batch).mean()

            opt_G.zero_grad()
            gen_loss.backward()
            opt_G.step()

            # Logging

            wasserstein_d = real_score.item() - fake_score.item()
            mean_critic_loss = np.mean(critic_losses)

            self.training_history['critic_loss'].append(mean_critic_loss)
            self.training_history['generator_loss'].append(gen_loss.item())
            self.training_history['wasserstein_dist'].append(wasserstein_d)

            if verbose and (epoch + 1) % 200 == 0:
                print(f"    Epoch {epoch + 1}/{epochs}  C_loss: {mean_critic_loss:.4f} "
                      f" G_loss: {gen_loss.item():.4f}  W_dist: {wasserstein_d:.4f}")

            # (#31) Mode collapse detection

            if (epoch + 1) % COLLAPSE_CHECK_INTERVAL == 0:
                with torch.no_grad():
                    test_z = torch.randn(50, LATENT_DIM)
                    test_samples = self.generator(test_z).numpy()
                    std_per_feature = np.std(test_samples, axis=0)
                    if np.any(std_per_feature < COLLAPSE_STD_THRESHOLD):
                        collapsed_features = [i for i, s in enumerate(std_per_feature) if s < COLLAPSE_STD_THRESHOLD]
                        logger.warning(
                            f" Mode collapse detected at epoch {epoch+1}! "
                            f"Features {collapsed_features} have near-zero variance. Stopping early."
                        )
                        print(f"     Mode collapse at epoch {epoch+1} — stopping early")
                        break

        self.is_trained = True

        if verbose:
            print(f"   GAN training complete — {epochs} epochs")
            logger.info(f" GAN training complete after {epochs} epochs")

    def save_model(self, name=None):
        """Save trained model weights and normalizer to disk."""
        name = name or self.model_name
        save_dir = MODEL_DIR / name
        save_dir.mkdir(parents=True, exist_ok=True)

        torch.save(self.generator.state_dict(), save_dir / 'generator.pt')
        torch.save(self.critic.state_dict(), save_dir / 'critic.pt')
        self.normalizer.save(save_dir / 'normalizer.npz')

        # Save training history

        with open(save_dir / 'history.json', 'w') as f:
            json.dump(self.training_history, f)

        logger.info(f" Model saved to {save_dir}")
        return save_dir

    def load_model(self, name=None):
        """Load pre-trained model weights from disk."""
        name = name or self.model_name
        load_dir = MODEL_DIR / name

        if not (load_dir / 'generator.pt').exists():
            return False

        self.generator.load_state_dict(torch.load(load_dir / 'generator.pt', weights_only=True))
        self.critic.load_state_dict(torch.load(load_dir / 'critic.pt', weights_only=True))
        self.normalizer.load(load_dir / 'normalizer.npz')

        self.is_trained = True
        logger.info(f" Model loaded from {load_dir}")
        return True

    def generate_users(self, count=50):
        """
        Generate N synthetic user profiles with watermarked financial data.
        Returns list of dicts ready for database insertion.
        """
        if not self.is_trained:
            logger.warning("Generator is not trained. Results may be poor.")

        self.generator.eval()
        with torch.no_grad():
            z = torch.randn(count, LATENT_DIM)
            raw_output = self.generator(z).numpy()

        # Denormalize if normalizer is fitted

        if self.normalizer.min_vals is not None:
            raw_output = self.normalizer.inverse_transform(raw_output)

        # (#32) Expanded name pools for diversity (200+ entries each)

        first_names = [
            'James', 'Mary', 'Robert', 'Patricia', 'John', 'Jennifer', 'Michael',
            'Linda', 'David', 'Elizabeth', 'William', 'Barbara', 'Richard', 'Susan',
            'Joseph', 'Jessica', 'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher',
            'Lisa', 'Daniel', 'Nancy', 'Matthew', 'Betty', 'Anthony', 'Margaret',
            'Mark', 'Sandra', 'Steven', 'Ashley', 'Andrew', 'Kimberly', 'Paul', 'Emily',
            'Joshua', 'Donna', 'Kenneth', 'Michelle', 'Kevin', 'Carol', 'Brian', 'Amanda',
            'George', 'Dorothy', 'Timothy', 'Melissa', 'Ronald', 'Deborah', 'Edward', 'Stephanie',
            'Jason', 'Rebecca', 'Jeffrey', 'Sharon', 'Ryan', 'Laura', 'Jacob', 'Cynthia',
            'Gary', 'Kathleen', 'Nicholas', 'Amy', 'Dennis', 'Angela', 'Jerry', 'Shirley',
            'Tyler', 'Anna', 'Aaron', 'Brenda', 'Jose', 'Pamela', 'Nathan', 'Emma',
            'Adam', 'Nicole', 'Henry', 'Helen', 'Douglas', 'Samantha', 'Peter', 'Katherine',
            'Zachary', 'Christine', 'Kyle', 'Debra', 'Noah', 'Rachel', 'Ethan', 'Carolyn',
            'Jeremy', 'Janet', 'Walter', 'Catherine', 'Dylan', 'Maria', 'Brandon', 'Heather',
            'Roy', 'Diane', 'Ralph', 'Ruth', 'Eugene', 'Julie', 'Russell', 'Olivia',
            'Bobby', 'Joyce', 'Mason', 'Virginia', 'Philip', 'Victoria', 'Harry', 'Kelly',
            'Vincent', 'Lauren', 'Albert', 'Christina', 'Wayne', 'Joan', 'Louis', 'Evelyn',
            'Alexander', 'Judith', 'Oscar', 'Megan', 'Carl', 'Andrea', 'Alan', 'Cheryl',
            'Elijah', 'Hannah', 'Samuel', 'Jacqueline', 'Benjamin', 'Martha', 'Raymond', 'Gloria',
            'Gregory', 'Teresa', 'Frank', 'Ann', 'Patrick', 'Sara', 'Jack', 'Madison',
            'Roger', 'Frances', 'Gerald', 'Kathryn', 'Scott', 'Janice', 'Arthur', 'Jean',
            'Liam', 'Abigail', 'Adrian', 'Alice', 'Cody', 'Judy', 'Aiden', 'Sophia',
            'Luke', 'Grace', 'Connor', 'Denise', 'Owen', 'Amber', 'Chase', 'Doris',
            'Marcus', 'Marilyn', 'Wesley', 'Danielle', 'Cole', 'Beverly', 'Jared', 'Isabella',
            'Ivan', 'Theresa', 'Victor', 'Diana', 'Hugo', 'Natalie', 'Felix', 'Brittany',
            'Dominick', 'Charlotte', 'Grant', 'Marie', 'Trevor', 'Kayla', 'Derek', 'Alexis',
            'Miles', 'Lori', 'Nolan', 'Allison', 'Tristan', 'Mia', 'Max', 'Aubrey',
        ]
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
            'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
            'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
            'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark',
            'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young', 'Allen', 'King',
            'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores', 'Green',
            'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell',
            'Carter', 'Roberts', 'Gomez', 'Phillips', 'Evans', 'Turner', 'Diaz',
            'Parker', 'Cruz', 'Edwards', 'Collins', 'Reyes', 'Stewart', 'Morris',
            'Morales', 'Murphy', 'Cook', 'Rogers', 'Gutierrez', 'Ortiz', 'Morgan',
            'Cooper', 'Peterson', 'Bailey', 'Reed', 'Kelly', 'Howard', 'Ramos',
            'Kim', 'Cox', 'Ward', 'Richardson', 'Watson', 'Brooks', 'Chavez',
            'Wood', 'James', 'Bennett', 'Gray', 'Mendoza', 'Ruiz', 'Hughes',
            'Price', 'Alvarez', 'Castillo', 'Sanders', 'Patel', 'Myers', 'Long',
            'Ross', 'Foster', 'Jimenez', 'Powell', 'Jenkins', 'Perry', 'Russell',
            'Sullivan', 'Bell', 'Coleman', 'Butler', 'Henderson', 'Barnes', 'Gonzales',
            'Fisher', 'Vasquez', 'Simmons', 'Graham', 'Murray', 'Ford', 'Freeman',
            'Dixon', 'Stone', 'Lambert', 'Hawkins', 'Hicks', 'Dunn', 'Reynolds',
            'Fields', 'Burns', 'Carr', 'Hunt', 'Spencer', 'Schneider', 'Olson',
            'Knight', 'Marshall', 'Webb', 'Tucker', 'Hoffman', 'Hart', 'Chen',
        ]
        email_domains = [
            'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com',
            'protonmail.com', 'icloud.com', 'mail.com', 'aol.com'
        ]

        users = []
        for row in raw_output:
            balance = abs(float(row[0]))

            # (#28) Watermark only WATERMARK_RATIO% of users (not all)

            if random.random() < WATERMARK_RATIO:
                balance_int = int(balance * 10)
                balance = (balance_int * 10 + WATERMARK_DECIMAL) / 100
            else:
                balance = round(balance, 2)

            credit_score = int(np.clip(float(row[1]), 300, 850))
            age = int(np.clip(float(row[2]), 18, 85))

            first = random.choice(first_names)
            last = random.choice(last_names)
            suffix = random.randint(10, 999)
            domain = random.choice(email_domains)
            username = f"{first.lower()}.{last.lower()}{suffix}"
            email = f"{username}@{domain}"

            users.append({
                'username': username,
                'password': ''.join(random.choices(string.ascii_letters + string.digits, k=16)),
                'email': email,
                'full_name': f"[GAN] {first} {last}",  # (#26) Detectable marker
                'role': random.choices(['user', 'admin', 'manager'], weights=[0.85, 0.05, 0.1])[0],
                'balance': round(balance, 2),
                'credit_score': credit_score,
                'age': age,
            })

        return users

    def validate(self, seed_data=None, n_samples=100):
        """
        (#27) Validates the generator by comparing against the ACTUAL training data,
        not a re-randomized version. Falls back to seed_data if training data unavailable.
        """
        # Use actual training data if available

        if hasattr(self, '_training_data_raw') and self._training_data_raw is not None:
            real_arr = self._training_data_raw
        elif seed_data:
            # Fallback: reconstruct from seed_data (same logic as _prepare_training_data)

            raw_real = []
            for user in seed_data:
                balance = float(user[5]) if len(user) > 5 else 0
                credit_score = min(850, max(300, 600 + (balance / 1000) + random.gauss(0, 30)))
                age = random.randint(22, 70)
                tx_count = max(1, int(random.gauss(25, 15)))
                raw_real.append([balance, credit_score, age, tx_count])
            real_arr = np.array(raw_real, dtype=np.float32)
        else:
            return {'error': 'No training data available for validation'}

        # Generate synthetic samples

        fake_users = self.generate_users(n_samples)
        fake_arr = np.array([[u['balance'], u['credit_score'], u['age'], 0] for u in fake_users], dtype=np.float32)

        feature_names = ['Balance', 'CreditScore', 'Age']
        metrics = {}
        for i, name in enumerate(feature_names):
            real_vals = real_arr[:, i]
            fake_vals = fake_arr[:, i]
            metrics[name] = {
                'real_mean': float(np.mean(real_vals)),
                'fake_mean': float(np.mean(fake_vals)),
                'real_std': float(np.std(real_vals)),
                'fake_std': float(np.std(fake_vals)),
                'mean_diff_pct': float(abs(np.mean(real_vals) - np.mean(fake_vals)) / (np.mean(real_vals) + 1e-8) * 100),
            }

        # Check watermark integrity (should be ~WATERMARK_RATIO of users)

        watermarked = sum(1 for u in fake_users if round(u['balance'] * 100) % 10 == WATERMARK_DECIMAL)
        expected_pct = WATERMARK_RATIO * 100
        actual_pct = watermarked / n_samples * 100
        metrics['watermark_integrity'] = {
            'watermarked_count': watermarked,
            'total': n_samples,
            'actual_pct': round(actual_pct, 1),
            'expected_pct': round(expected_pct, 1),
            'status': 'OK' if abs(actual_pct - expected_pct) < 15 else 'DRIFT',
        }

        return metrics

# SINGLETON / FACTORY

_factory_instance = None
_factory_lock = threading.Lock()  # (#33) thread-safe singleton

def get_gan_factory(model_name='default'):
    """Get or create a singleton SyntheticUserFactory (thread-safe)."""
    global _factory_instance
    if _factory_instance is None:
        with _factory_lock:
            if _factory_instance is None:  # Double-checked locking
                _factory_instance = SyntheticUserFactory(model_name=model_name)
    return _factory_instance
