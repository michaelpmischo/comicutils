# 📚 Comic Book Utilities Package

A lightweight Python GUI/CLI tool for reading, organizing, renaming, and converting digital comic book archives and epub documents (.cbz, .cbr, .cbt, .cb7, .epub, .pdf) with more to come.

## ✨ Features

* **ComicViewer:** A GUI based tkinter application for reading files and accessing other tools.
* **ComicMaker:** A CLI tool for batch creating large number of directory separated image files into comic archive with the direcotyr name.
* **ComicConverter:** Batch convert comic archive. epubs, pdf between the varying formats.
* **ComicInfo:** Scrape issue details, cover art, and summaries via the ComicVine API.

## 🛠️ Installation

### Prerequisites
* Python 3.9 or higher
* Required System Tools: unrar (linux), WinRAR (win), or 7zip if handling .cbr or .cb7 files.

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com[your-username]/[repo-name].git
   cd [repo-name]
   execute ComicViewer.py, ComicMaker.py, ComicConverter.py, etc...
   ```

## 🚀 Usage

[Provide a quick example of how to run your script or import your library.]

### Command Line Example
```bash
```

### Python Library Example
```python
from comicutils.comics import Comic
comic = Comic("Batman_001.cbr")
comic.extract()
```

## 🗺️ Roadmap

- [x] Basic CBZ/CBR file parsing
- [x] GUI interface
- [X] epub/pdf support
- [ ] Automatic series folder organization

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues](https://github.com/michaelpmischo/comicutils/issues).

## 📄 License

Distributed under the [GPL3.0] License. See `LICENSE` for more information.
