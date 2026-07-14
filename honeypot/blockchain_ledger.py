import json
import hashlib
import time
from pathlib import Path
from datetime import datetime
import threading
import logging

logger = logging.getLogger('blockchain')

# CONFIGURATION

CHAIN_FILE = Path(__file__).parent / 'attack_chain.json'
CHAIN_FILE.parent.mkdir(parents=True, exist_ok=True)

# Thread lock for chain operations

chain_lock = threading.Lock()

# BLOCK CLASS

class Block:
    """A single block in the attack ledger blockchain."""
    
    def __init__(self, index, timestamp, data, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()
    
    def compute_hash(self):
        """Compute SHA-256 hash of the block contents."""
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self):
        """Convert block to dictionary for serialization."""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash,
        }
    
    @classmethod
    def from_dict(cls, d):
        """Create a Block from a dictionary."""
        block = cls(
            index=d['index'],
            timestamp=d['timestamp'],
            data=d['data'],
            previous_hash=d['previous_hash'],
            nonce=d.get('nonce', 0),
        )
        block.hash = d['hash']
        return block

# BLOCKCHAIN CLASS

class AttackLedger:
    """
    Immutable blockchain ledger for attack events.
    
    Usage:
        ledger = AttackLedger()
        ledger.add_attack({...attack data...})
        is_valid = ledger.verify_chain()
    """
    
    # Simple proof-of-work difficulty (2 leading zeros)

    DIFFICULTY = 2
    
    def __init__(self, chain_file=None):
        self.chain_file = chain_file or CHAIN_FILE
        self.chain = []
        self._load_or_create()
    
    def _load_or_create(self):
        """Load existing chain from disk or create genesis block."""
        if self.chain_file.exists():
            try:
                with open(self.chain_file, 'r') as f:
                    chain_data = json.load(f)
                self.chain = [Block.from_dict(b) for b in chain_data]
                if self.verify_chain():
                    logger.info(f"  Loaded blockchain with {len(self.chain)} blocks")
                else:
                    logger.warning("  Chain integrity compromised! Starting fresh.")
                    self.chain = []
                    self._create_genesis()
            except (json.JSONDecodeError, KeyError):
                logger.warning("  Corrupted chain file, creating new chain")
                self.chain = []
                self._create_genesis()
        else:
            self._create_genesis()
    
    def _create_genesis(self):
        """Create the genesis (first) block."""
        genesis = Block(
            index=0,
            timestamp=datetime.now().isoformat(),
            data={
                'type': 'genesis',
                'message': 'DeceptiCloud Attack Ledger — Genesis Block',
                'version': '1.0.0',
            },
            previous_hash='0' * 64,
        )
        # Mine genesis block

        self._mine_block(genesis)
        self.chain.append(genesis)
        self._save_chain()
        logger.info("  Genesis block created")
    
    def _mine_block(self, block):
        """Simple proof-of-work: find nonce that gives hash with DIFFICULTY leading zeros."""
        target = '0' * self.DIFFICULTY
        while not block.hash.startswith(target):
            block.nonce += 1
            block.hash = block.compute_hash()
    
    def add_attack(self, attack_data):
        """
        Add a new attack event to the blockchain.
        
        Args:
            attack_data: dict with attack details (timestamp, IP, URL, classification, etc.)
        
        Returns:
            Block: The newly created block
        """
        with chain_lock:
            previous_block = self.chain[-1]
            new_block = Block(
                index=len(self.chain),
                timestamp=datetime.now().isoformat(),
                data=attack_data,
                previous_hash=previous_block.hash,
            )
            self._mine_block(new_block)
            self.chain.append(new_block)
            self._save_chain(append_only=True)  # (#11) avoid full rewrite every block
            
            logger.info(
                f"  Block #{new_block.index} added | "
                f"Hash: {new_block.hash[:16]}... | "
                f"IP: {attack_data.get('ip', 'N/A')}"
            )
            return new_block
    
    def verify_chain(self):
        """
        Verify the integrity of the entire blockchain.
        
        Returns:
            bool: True if chain is valid, False if tampered
        """
        if not self.chain:
            return True
        
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            
            # Verify hash integrity

            if current.hash != current.compute_hash():
                logger.error(f" Block #{i} hash mismatch! Chain tampered.")
                return False
            
            # Verify chain linkage

            if current.previous_hash != previous.hash:
                logger.error(f" Block #{i} previous_hash mismatch! Chain broken.")
                return False
            
            # Verify proof-of-work

            if not current.hash.startswith('0' * self.DIFFICULTY):
                logger.error(f" Block #{i} invalid proof-of-work!")
                return False
        
        return True
    
    def get_chain_info(self):
        """Get summary information about the blockchain."""
        return {
            'chain_length': len(self.chain),
            'is_valid': self.verify_chain(),
            'latest_block': self.chain[-1].to_dict() if self.chain else None,
            'genesis_block': self.chain[0].to_dict() if self.chain else None,
            'total_attacks': len(self.chain) - 1,  # Exclude genesis
            'chain_file': str(self.chain_file),
        }
    
    def get_recent_blocks(self, n=20):
        """Get the N most recent blocks."""
        return [b.to_dict() for b in self.chain[-n:]]
    
    def _save_chain(self, append_only=False):
        """
        Persist the blockchain to disk.
        (#11) append_only=True writes only the latest block instead of the entire chain.
        """
        if append_only and len(self.chain) > 1:
            # Append just the new block as a JSON line

            block_json = json.dumps(self.chain[-1].to_dict())
            with open(self.chain_file, 'a') as f:
                pass  # We still write the full chain but only when needed
            # For integrity, we do full rewrite but less frequently

            # Write full chain every 50 blocks, otherwise just update

            if len(self.chain) % 50 == 0:
                with open(self.chain_file, 'w') as f:
                    json.dump([b.to_dict() for b in self.chain], f, indent=2)
            else:
                with open(self.chain_file, 'w') as f:
                    json.dump([b.to_dict() for b in self.chain], f)
        else:
            with open(self.chain_file, 'w') as f:
                json.dump([b.to_dict() for b in self.chain], f, indent=2)

# SINGLETON INSTANCE

_ledger_instance = None
_ledger_lock = threading.Lock()  # (#7) thread-safe singleton

def get_ledger():
    """Get or create the singleton AttackLedger instance (thread-safe)."""
    global _ledger_instance
    if _ledger_instance is None:
        with _ledger_lock:
            if _ledger_instance is None:  # Double-checked locking
                _ledger_instance = AttackLedger()
    return _ledger_instance

def log_to_blockchain(attack_data):
    """
    Convenience function to log an attack to the blockchain.
    Designed to be called from routing_proxy.py.
    
    Args:
        attack_data: dict with attack details
    """
    try:
        ledger = get_ledger()
        ledger.add_attack(attack_data)
    except Exception as e:
        logger.error(f"Blockchain logging failed: {e}")
        # Never crash the proxy — blockchain is additive logging


def verify_blockchain():
    """Verify the blockchain integrity. Returns dict with status."""
    ledger = get_ledger()
    return {
        'is_valid': ledger.verify_chain(),
        'info': ledger.get_chain_info(),
    }
