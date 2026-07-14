# 📦 Full Project ZIP (Including venv)

The complete project archive (including Python virtual environment) has been split into 2 parts due to GitHub's 2 GB per-file limit.

## Files
| File | Size |
|------|------|
| `Ahmed Fype-II.zip.partaa` | ~1.4 GB |
| `Ahmed Fype-II.zip.partab` | ~1.4 GB |

## ⬇️ How to Restore the ZIP

After cloning the repo, run the following command to merge the parts back into a single ZIP:

### Linux / macOS
```bash
cat Ahmed\ Fype-II.zip.parta* > Ahmed\ Fype-II.zip
unzip Ahmed\ Fype-II.zip
```

### Windows (PowerShell)
```powershell
cmd /c "copy /b Ahmed` Fype-II.zip.partaa + Ahmed` Fype-II.zip.partab Ahmed` Fype-II.zip"
Expand-Archive -Path "Ahmed Fype-II.zip" -DestinationPath "."
```

## 📝 Notes
- The ZIP contains the **full project including the Python venv**
- If you don't need the venv, recreate it with: `pip install -r requirements.txt`
- Datasets are **not included** in the source code tree (too large for GitHub)
