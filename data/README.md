# Data Directory

This project keeps dataset pointers in version control and leaves large or third-party raw datasets local by default.

- `data/raw/public/abc-dataset/SOURCE.txt`: official ABC Dataset entry point.
- `data/raw/public/trview2cad/SOURCE.txt`: TriView2CAD source pointer.
- `data/raw/public/trview2cad/DOWNLOAD_ERROR.txt`: local download note for the current source.
- `data/raw/public/deepcad/`: downloaded locally for experimentation, ignored by Git until redistribution terms are reviewed.

For internal drawings and checklist labels, use:

```text
data/raw/internal/
data/processed/
```

Do not commit confidential drawings, supplier data, or licensed standards text.
