"""
GULP — GDDP Unified Loader & Processor
PyQt6 GUI  |  v1.0.0  — Redesigned
"""

import os
import re
import sys
import xml.etree.ElementTree as ET
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QSize, QTimer, QPropertyAnimation,
    QEasingCurve, QAbstractTableModel, QModelIndex, QSortFilterProxyModel,
    QRect,
)
from PyQt6.QtGui import (
    QColor, QFont, QFontDatabase, QPalette, QIcon, QPixmap,
    QPainter, QLinearGradient, QBrush, QPen, QPainterPath,
    QWheelEvent, QKeySequence, QShortcut,
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QTableView, QHeaderView, QProgressBar, QTextEdit, QFileDialog,
    QFrame, QSplitter, QStackedWidget, QCheckBox, QSpinBox,
    QAbstractItemView, QSizePolicy, QScrollArea, QStatusBar,
    QDialog, QDialogButtonBox, QMessageBox, QGroupBox,
    QGraphicsOpacityEffect,
)

# ─────────────────────────────────────────────
#  S3 / Backend constants
# ─────────────────────────────────────────────
BUCKET = "nex-gddp-cmip6"
BASE_URL = f"https://{BUCKET}.s3.us-west-2.amazonaws.com"
ROOT_PREFIX = "NEX-GDDP-CMIP6/"
XML_NS = "http://s3.amazonaws.com/doc/2006-03-01/"
DEFAULT_DIR = str(Path.home() / "NEX_GDDP")
APP_VERSION = "1.0.0"

# ─────────────────────────────────────────────
#  Palette — Light orange with dark contrasting borders
# ─────────────────────────────────────────────
C = {
    "bg":         "#FFF3E0",   # warm light orange background
    "panel":      "#FFE0B2",   # slightly deeper orange for panels
    "card":       "#FFFFFF",   # white cards
    "border":     "#6D4C41",   # thick dark brown border
    "border2":    "#8D6E63",   # medium brown
    "accent":     "#E65100",   # deep orange accent
    "accent2":    "#BF360C",   # darker orange for hover
    "accent_dim": "#FFCCBC",   # light accent bg
    "green":      "#1B5E20",   # dark green for download
    "green2":     "#2E7D32",   # medium green
    "yellow":     "#F57F17",   # amber
    "red":        "#B71C1C",   # dark red
    "text":       "#1A0A00",   # very dark brown/black text
    "text2":      "#4E342E",   # medium dark brown
    "text3":      "#795548",   # medium brown
    "hover":      "#FFCCBC",   # hover light orange
    "selected":   "#FFAB91",   # selected orange
    "progress":   "#E65100",
    "sidebar_border": "#3E2723",  # very dark brown for sidebar border
}

# ─────────────────────────────────────────────
#  Global stylesheet — Light orange theme
# ─────────────────────────────────────────────
QSS = f"""
QWidget {{
    background: {C['bg']};
    color: {C['text']};
    font-family: 'Consolas', 'JetBrains Mono', 'Courier New', monospace;
    font-size: 17px;
}}
QMainWindow, QDialog {{
    background: {C['bg']};
}}

/* ── Sidebar ── */
#Sidebar {{
    background: {C['panel']};
    border-right: 4px solid {C['sidebar_border']};
}}
#SideBtn {{
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    text-align: left;
    color: {C['text2']};
    font-size: 17px;
}}
#SideBtn:hover {{ background: {C['hover']}; color: {C['text']}; }}
#SideBtn[active="true"] {{
    background: {C['accent_dim']};
    color: {C['accent']};
    border-left: 4px solid {C['accent']};
}}

/* ── Cards / Panels ── */
#Card {{
    background: {C['card']};
    border: 3px solid {C['border']};
    border-radius: 8px;
}}
#SectionTitle {{
    color: {C['text2']};
    font-size: 15px;
    letter-spacing: 2px;
    font-weight: bold;
}}

/* ── Lists ── */
QListWidget {{
    background: {C['card']};
    border: 3px solid {C['border']};
    border-radius: 6px;
    outline: none;
    padding: 4px;
    font-size: 17px;
}}
QListWidget::item {{
    padding: 6px 10px;
    border-radius: 4px;
    color: {C['text']};
}}
QListWidget::item:hover {{ background: {C['hover']}; }}
QListWidget::item:selected {{
    background: {C['selected']};
    color: {C['accent2']};
}}

/* ── Table ── */
QTableView {{
    background: {C['card']};
    border: 3px solid {C['border']};
    border-radius: 6px;
    gridline-color: {C['border2']};
    outline: none;
    selection-background-color: {C['selected']};
    selection-color: {C['accent2']};
    font-size: 17px;
}}
QHeaderView::section {{
    background: {C['panel']};
    color: {C['text']};
    border: none;
    border-bottom: 3px solid {C['border']};
    border-right: 1px solid {C['border2']};
    padding: 8px 10px;
    font-size: 15px;
    letter-spacing: 1px;
    font-weight: bold;
}}
QTableView::item {{ padding: 4px 10px; }}
QTableView::item:selected {{
    background: {C['selected']};
    color: {C['accent2']};
}}

/* ── Buttons ── */
#PrimaryBtn {{
    background: {C['accent']};
    color: white;
    border: 3px solid {C['accent2']};
    border-radius: 6px;
    padding: 9px 20px;
    font-size: 17px;
    font-weight: bold;
}}
#PrimaryBtn:hover {{ background: {C['accent2']}; border-color: {C['sidebar_border']}; }}
#PrimaryBtn:disabled {{
    background: {C['border2']};
    color: {C['card']};
    border-color: {C['border']};
}}
#SecondaryBtn {{
    background: {C['card']};
    color: {C['text2']};
    border: 3px solid {C['border']};
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 17px;
}}
#SecondaryBtn:hover {{
    background: {C['hover']};
    color: {C['text']};
    border-color: {C['accent']};
}}
#DangerBtn {{
    background: {C['card']};
    color: {C['red']};
    border: 3px solid {C['red']};
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 17px;
    font-weight: bold;
}}
#DangerBtn:hover {{ background: #FFCDD2; }}

/* ── Download button — green ── */
#DownloadBtn {{
    background: {C['green']};
    color: white;
    border: 3px solid {C['green2']};
    border-radius: 6px;
    padding: 9px 24px;
    font-size: 17px;
    font-weight: bold;
}}
#DownloadBtn:hover {{ background: {C['green2']}; }}
#DownloadBtn:disabled {{
    background: {C['border2']};
    color: {C['card']};
    border-color: {C['border']};
}}

/* ── Inputs ── */
QSpinBox {{
    background: {C['card']};
    border: 3px solid {C['border']};
    border-radius: 5px;
    padding: 5px 8px;
    color: {C['text']};
    font-size: 17px;
}}
QSpinBox:focus {{ border-color: {C['accent']}; }}
QSpinBox::up-button, QSpinBox::down-button {{
    background: {C['panel']};
    border: 1px solid {C['border2']};
    width: 18px;
}}

/* ── CheckBox ── */
QCheckBox {{
    spacing: 8px;
    color: {C['text']};
    font-size: 17px;
}}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border: 3px solid {C['border']};
    border-radius: 3px;
    background: {C['card']};
}}
QCheckBox::indicator:checked {{
    background: {C['accent']};
    border-color: {C['accent2']};
}}

/* ── Progress ── */
QProgressBar {{
    background: {C['panel']};
    border: 2px solid {C['border']};
    border-radius: 4px;
    height: 10px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {C['accent']}, stop:1 {C['yellow']});
    border-radius: 3px;
}}

/* ── Log ── */
QTextEdit {{
    background: {C['card']};
    border: 3px solid {C['border']};
    border-radius: 6px;
    color: {C['text']};
    font-family: 'Consolas', monospace;
    font-size: 16px;
    padding: 8px;
    selection-background-color: {C['accent_dim']};
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: {C['panel']};
    width: 10px;
    margin: 0;
    border: 1px solid {C['border2']};
}}
QScrollBar::handle:vertical {{
    background: {C['border2']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {C['accent']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {C['panel']};
    height: 10px;
    border: 1px solid {C['border2']};
}}
QScrollBar::handle:horizontal {{
    background: {C['border2']};
    border-radius: 4px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Splitter ── */
QSplitter::handle {{
    background: {C['border']};
    width: 3px;
    height: 3px;
}}

/* ── Status bar ── */
QStatusBar {{
    background: {C['panel']};
    color: {C['text2']};
    border-top: 3px solid {C['border']};
    font-size: 16px;
    padding: 2px 8px;
    font-weight: bold;
}}

/* ── Tooltips ── */
QToolTip {{
    background: {C['card']};
    color: {C['text']};
    border: 3px solid {C['border']};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 16px;
}}

/* ── Group box ── */
QGroupBox {{
    border: 3px solid {C['border']};
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 10px;
    color: {C['text']};
    font-size: 15px;
    font-weight: bold;
    letter-spacing: 1px;
    background: {C['card']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    background: {C['panel']};
    border: 2px solid {C['border']};
    border-radius: 3px;
}}
"""

# ─────────────────────────────────────────────
#  S3 backend (pure functions, no Qt)
# ─────────────────────────────────────────────


def s3_list(prefix, delimiter="/"):
    common_prefixes, object_keys = [], []
    continuation = None
    while True:
        params = {"list-type": "2", "prefix": prefix,
                  "delimiter": delimiter, "max-keys": "1000"}
        if continuation:
            params["continuation-token"] = continuation
        try:
            r = requests.get(BASE_URL, params=params, timeout=60)
            r.raise_for_status()
            root = ET.fromstring(r.content)
        except Exception:
            break
        ns = {"s3": XML_NS}
        for cp in root.findall("s3:CommonPrefixes/s3:Prefix", ns):
            common_prefixes.append(cp.text)
        for obj in root.findall("s3:Contents/s3:Key", ns):
            object_keys.append(obj.text)
        trunc = root.find("s3:IsTruncated", ns)
        if trunc is not None and trunc.text.lower() == "true":
            tok = root.find("s3:NextContinuationToken", ns)
            continuation = tok.text if tok else None
            if not continuation:
                break
        else:
            break
    return common_prefixes, object_keys


def get_models():
    prefixes, _ = s3_list(ROOT_PREFIX)
    return sorted({p.rstrip("/").split("/")[-1] for p in prefixes if p.rstrip("/").split("/")[-1]})


def list_folders(prefix):
    prefixes, _ = s3_list(prefix)
    return sorted({p.rstrip("/").split("/")[-1] for p in prefixes if p.rstrip("/").split("/")[-1]})


def list_nc_files(prefix):
    _, keys = s3_list(prefix)
    return [k.split("/")[-1] for k in keys if k.endswith(".nc")]


def extract_version(fname):
    m = re.search(r"_v(\d+\.\d+)\.nc$", fname)
    return ("v" + m.group(1)) if m else "base"


def scan_model(model, progress_cb=None):
    result, model_prefix = [], f"{ROOT_PREFIX}{model}/"
    scenarios = list_folders(model_prefix)
    for si, scenario in enumerate(scenarios):
        scen_prefix = f"{model_prefix}{scenario}/"
        for realization in list_folders(scen_prefix):
            real_prefix = f"{scen_prefix}{realization}/"
            for variable in list_folders(real_prefix):
                var_prefix = f"{real_prefix}{variable}/"
                files = list_nc_files(var_prefix)
                versions = {extract_version(f) for f in files} or {"base"}
                for version in versions:
                    result.append({"model": model, "scenario": scenario,
                                   "realization": realization,
                                   "variable": variable, "version": version})
        if progress_cb:
            progress_cb(si + 1, len(scenarios))
    return result


def collect_files(selection):
    files = []
    for item in selection:
        prefix = (f"{ROOT_PREFIX}{item['model']}/{item['scenario']}/"
                  f"{item['realization']}/{item['variable']}/")
        for f in list_nc_files(prefix):
            if extract_version(f) == item["version"]:
                files.append({"url": f"{BASE_URL}/{prefix}{f}",
                              "model": item["model"], "scenario": item["scenario"],
                              "variable": item["variable"], "file": f})
    return files


def download_file(url, out_file):
    if os.path.exists(out_file):
        return True, out_file, "skipped"
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    try:
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(out_file, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)
        return True, out_file, "ok"
    except Exception as e:
        return False, out_file, str(e)

# ─────────────────────────────────────────────
#  Worker threads
# ─────────────────────────────────────────────


class ModelLoaderThread(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def run(self):
        try:
            models = get_models()
            if not models:
                self.error.emit(
                    "Could not retrieve model list.\nCheck your network connection.")
            else:
                self.finished.emit(models)
        except Exception as e:
            self.error.emit(str(e))


class ScanThread(QThread):
    log = pyqtSignal(str)
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, models):
        super().__init__()
        self.models = models

    def run(self):
        master = []
        try:
            for i, model in enumerate(self.models):
                self.log.emit(f"Scanning  {model} ...")

                def cb(done, total, m=model):
                    self.log.emit(f"  {m}  —  scenario {done}/{total}")
                result = scan_model(model, cb)
                master.extend(result)
                self.progress.emit(i + 1, len(self.models))
                self.log.emit(f"✓  {model}  →  {len(result)} combinations")
            self.finished.emit(master)
        except Exception as e:
            self.error.emit(str(e))


class DownloadThread(QThread):
    file_done = pyqtSignal(int, int, bool, str)
    log = pyqtSignal(str)
    finished = pyqtSignal(int, int)

    def __init__(self, tasks, max_workers=16):
        super().__init__()
        self.tasks = tasks
        self.max_workers = max_workers
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        ok_count = failed_count = done = 0
        total = len(self.tasks)
        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            futures = {ex.submit(download_file, url, out): (url, out)
                       for url, out in self.tasks}
            for fut in as_completed(futures):
                if self._stop:
                    break
                done += 1
                success, path, msg = fut.result()
                fname = os.path.basename(path)
                if success:
                    ok_count += 1
                    status = "skipped" if msg == "skipped" else "✓"
                    self.log.emit(f"{status}  {fname}")
                else:
                    failed_count += 1
                    self.log.emit(f"✗  {fname}  —  {msg}")
                self.file_done.emit(done, total, success, fname)
        self.finished.emit(ok_count, failed_count)


# ─────────────────────────────────────────────
#  Table model for combinations
# ─────────────────────────────────────────────
COLS = ["Model", "Scenario", "Realization", "Variable", "Version"]


class CombinationModel(QAbstractTableModel):
    def __init__(self, data=None):
        super().__init__()
        self._data = data or []

    def rowCount(self, parent=QModelIndex()): return len(self._data)
    def columnCount(self, parent=QModelIndex()): return len(COLS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return COLS[section].upper()
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = self._data[index.row()]
        keys = ["model", "scenario", "realization", "variable", "version"]
        if role == Qt.ItemDataRole.DisplayRole:
            return row[keys[index.column()]]
        if role == Qt.ItemDataRole.ForegroundRole:
            if index.column() == 1:
                s = row["scenario"]
                if "historical" in s:
                    return QColor(C["green"])
                if "ssp" in s:
                    return QColor(C["yellow"])
            if index.column() == 4:
                return QColor(C["text2"])
        return None

    def set_data(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def get_row(self, row): return self._data[row]

# ─────────────────────────────────────────────
#  Reusable UI atoms
# ─────────────────────────────────────────────


def label(text, color=None, size=None, bold=False):
    l = QLabel(text)
    style = ""
    if color:
        style += f"color: {color};"
    if size:
        style += f"font-size: {size}px;"
    if bold:
        style += "font-weight: bold;"
    if style:
        l.setStyleSheet(style)
    return l


def section_title(text):
    l = QLabel(text.upper())
    l.setObjectName("SectionTitle")
    return l


def hline():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(
        f"color: {C['border']}; background: {C['border']}; min-height: 3px; max-height: 3px;")
    return f


def primary_btn(text, icon=None):
    b = QPushButton(text)
    b.setObjectName("PrimaryBtn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if icon:
        b.setIcon(icon)
    return b


def secondary_btn(text):
    b = QPushButton(text)
    b.setObjectName("SecondaryBtn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def danger_btn(text):
    b = QPushButton(text)
    b.setObjectName("DangerBtn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def download_btn(text):
    b = QPushButton(text)
    b.setObjectName("DownloadBtn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def stat_card(value, label_text, color=None):
    card = QFrame()
    card.setObjectName("Card")
    lay = QVBoxLayout(card)
    lay.setContentsMargins(16, 12, 16, 12)
    lay.setSpacing(2)
    vl = QLabel(str(value))
    vl.setStyleSheet(
        f"font-size: 28px; font-weight: bold; color: {color or C['accent']}; border: none;")
    ll = QLabel(label_text.upper())
    ll.setStyleSheet(
        f"font-size: 12px; color: {C['text3']}; letter-spacing: 2px; border: none;")
    lay.addWidget(vl)
    lay.addWidget(ll)
    return card, vl


# ─────────────────────────────────────────────
#  Logo widget (drawn, no file needed) — warm orange theme
# ─────────────────────────────────────────────
# ── Shared logo pixmap cache (loaded once from assets/) ──────────────────
_LOGO_PIXMAP_CACHE: dict = {}


def _get_logo_pixmap(size: int) -> QPixmap:
    """Return a QPixmap of the GULP logo at `size`x`size`.
    Loads from assets/gulp.ico or gulp.png; falls back to drawn teardrop."""
    if size in _LOGO_PIXMAP_CACHE:
        return _LOGO_PIXMAP_CACHE[size]

    assets = Path(__file__).parent.parent / "assets"
    pix = None
    for candidate in [assets / "gulp.ico", assets / "gulp.png", assets / "gulp.bmp"]:
        if candidate.exists():
            loaded = QPixmap(str(candidate))
            if not loaded.isNull():
                pix = loaded.scaled(
                    size, size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                break

    if pix is None or pix.isNull():
        # Drawn fallback — teardrop shape
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, size, size)
        grad.setColorAt(0, QColor("#E65100"))
        grad.setColorAt(1, QColor("#BF360C"))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor(C["sidebar_border"]), max(1, size // 18)))
        p.drawEllipse(1, 1, size - 2, size - 2)
        p.setBrush(QBrush(QColor("white")))
        p.setPen(Qt.PenStyle.NoPen)
        cx, tip, bot, bulge = size*0.5, size*0.12, size*0.85, size*0.30
        drop = QPainterPath()
        drop.moveTo(cx, tip)
        drop.cubicTo(cx+bulge*1.1, size*0.38, cx +
                     bulge*0.95, size*0.72, cx, bot)
        drop.cubicTo(cx-bulge*0.95, size*0.72, cx -
                     bulge*1.1, size*0.38, cx, tip)
        drop.closeSubpath()
        p.drawPath(drop)
        p.end()

    _LOGO_PIXMAP_CACHE[size] = pix
    return pix


class LogoWidget(QLabel):
    """Displays the GULP logo image (from assets/) scaled to `size`x`size`."""

    def __init__(self, size=36):
        super().__init__()
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background: transparent; border: none;")
        self.setPixmap(_get_logo_pixmap(size))


# ─────────────────────────────────────────────
#  Animated Download Button (green, pulsing arrow)
# ─────────────────────────────────────────────
class AnimatedDownloadBtn(QPushButton):
    def __init__(self, text="⬇  Download"):
        super().__init__(text)
        self.setObjectName("DownloadBtn")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim_offset = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)
        self._enabled_state = True

    def _tick(self):
        if self._enabled_state and self.isEnabled():
            self._anim_offset = (self._anim_offset + 0.15) % (2 * 3.14159)
        else:
            self._anim_offset = 0.0
        self.update()

    def setEnabled(self, enabled):
        self._enabled_state = enabled
        super().setEnabled(enabled)

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.isEnabled():
            return
        import math
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Draw a small animated bouncing arrow on the right side
        bounce = int(math.sin(self._anim_offset) * 4)
        r = self.rect()
        arrow_x = r.right() - 28
        arrow_y = r.center().y() + bounce
        p.setPen(QPen(QColor("white"), 2))
        p.drawLine(arrow_x, arrow_y - 5, arrow_x, arrow_y + 5)
        p.drawLine(arrow_x - 4, arrow_y + 1, arrow_x, arrow_y + 5)
        p.drawLine(arrow_x + 4, arrow_y + 1, arrow_x, arrow_y + 5)
        p.end()


# ─────────────────────────────────────────────
#  STEP 1 — Model Selection Page
# ─────────────────────────────────────────────
class ModelPage(QWidget):
    models_confirmed = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self._models = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # Header with logo
        hdr = QHBoxLayout()
        logo = LogoWidget(32)
        hdr.addWidget(logo)
        hdr.addSpacing(8)
        hdr.addWidget(label("SELECT MODELS", C["text2"], 15, bold=True))
        hdr.addStretch()
        self.refresh_btn = secondary_btn("⟳  Refresh")
        self.refresh_btn.clicked.connect(self.load_models)
        hdr.addWidget(self.refresh_btn)
        root.addLayout(hdr)

        root.addWidget(label(
            "Choose one or more CMIP6 models to scan for available datasets.",
            C["text3"], 16))

        self.list = QListWidget()
        self.list.setSelectionMode(
            QAbstractItemView.SelectionMode.MultiSelection)
        self.list.setMinimumHeight(300)
        root.addWidget(self.list)

        status_row = QHBoxLayout()
        self.status_lbl = label("Loading models…", C["text3"], 16)
        status_row.addWidget(self.status_lbl)
        status_row.addStretch()
        self.sel_lbl = label("0 selected", C["accent"], 16, bold=True)
        status_row.addWidget(self.sel_lbl)
        root.addLayout(status_row)

        self.load_progress = QProgressBar()
        self.load_progress.setRange(0, 0)
        self.load_progress.setFixedHeight(6)
        root.addWidget(self.load_progress)

        btn_row = QHBoxLayout()
        self.select_all_btn = secondary_btn("Select All")
        self.select_all_btn.clicked.connect(self.list.selectAll)
        self.clear_btn = secondary_btn("Clear")
        self.clear_btn.clicked.connect(self.list.clearSelection)
        self.next_btn = primary_btn("Scan Selected  →")
        self.next_btn.setEnabled(False)
        btn_row.addWidget(self.select_all_btn)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.next_btn)
        root.addLayout(btn_row)

        self.list.itemSelectionChanged.connect(self._on_selection)
        self.next_btn.clicked.connect(self._confirm)
        self.load_models()

    def load_models(self):
        self.list.clear()
        self.next_btn.setEnabled(False)
        self.load_progress.setVisible(True)
        self.status_lbl.setText("Contacting S3 bucket…")
        self.refresh_btn.setEnabled(False)
        self._thread = ModelLoaderThread()
        self._thread.finished.connect(self._on_loaded)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_loaded(self, models):
        self._models = models
        self.list.clear()
        for m in models:
            self.list.addItem(m)
        self.load_progress.setVisible(False)
        self.status_lbl.setText(f"{len(models)} models available")
        self.refresh_btn.setEnabled(True)

    def _on_error(self, msg):
        self.load_progress.setVisible(False)
        self.status_lbl.setText(f"Error: {msg}")
        self.status_lbl.setStyleSheet(f"color: {C['red']}; font-size: 16px;")
        self.refresh_btn.setEnabled(True)

    def _on_selection(self):
        n = len(self.list.selectedItems())
        self.sel_lbl.setText(f"{n} selected")
        self.next_btn.setEnabled(n > 0)

    def _confirm(self):
        selected = [item.text() for item in self.list.selectedItems()]
        if selected:
            self.models_confirmed.emit(selected)

# ─────────────────────────────────────────────
#  STEP 2 — Scan Page
# ─────────────────────────────────────────────


class ScanPage(QWidget):
    scan_done = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self._models = []
        self._thread = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        hdr = QHBoxLayout()
        logo = LogoWidget(32)
        hdr.addWidget(logo)
        hdr.addSpacing(8)
        hdr.addWidget(label("SCANNING DATASETS", C["text2"], 15, bold=True))
        hdr.addStretch()
        root.addLayout(hdr)

        self.scanning_lbl = label("", C["accent"], 16, bold=True)
        root.addWidget(self.scanning_lbl)

        prog_card = QFrame()
        prog_card.setObjectName("Card")
        prog_lay = QVBoxLayout(prog_card)
        prog_lay.setContentsMargins(16, 14, 16, 14)
        prog_lay.setSpacing(10)
        pr = QHBoxLayout()
        self.prog_lbl = label("", C["text2"], 16)
        self.prog_pct = label("0%", C["accent"], 16, bold=True)
        pr.addWidget(self.prog_lbl)
        pr.addStretch()
        pr.addWidget(self.prog_pct)
        self.progress = QProgressBar()
        self.progress.setFixedHeight(8)
        prog_lay.addLayout(pr)
        prog_lay.addWidget(self.progress)
        root.addWidget(prog_card)

        root.addWidget(section_title("Activity Log"))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(220)
        root.addWidget(self.log)

        row = QHBoxLayout()
        self.back_btn = secondary_btn("← Back")
        self.cancel_btn = danger_btn("Cancel")
        self.cancel_btn.setVisible(False)
        row.addWidget(self.back_btn)
        row.addWidget(self.cancel_btn)
        row.addStretch()
        root.addLayout(row)

    def start_scan(self, models):
        self._models = models
        self.scanning_lbl.setText(", ".join(models))
        self.log.clear()
        self.progress.setValue(0)
        self.progress.setRange(0, len(models))
        self.prog_lbl.setText(f"Scanning 0 / {len(models)} models")
        self.cancel_btn.setVisible(True)
        self.back_btn.setEnabled(False)

        self._thread = ScanThread(models)
        self._thread.log.connect(self._append_log)
        self._thread.progress.connect(self._on_progress)
        self._thread.finished.connect(self._on_done)
        self._thread.error.connect(self._on_error)
        self._thread.start()
        self.cancel_btn.clicked.connect(self._thread.terminate)

    def _append_log(self, msg):
        self.log.append(msg)

    def _on_progress(self, done, total):
        self.progress.setValue(done)
        self.prog_lbl.setText(f"Scanning {done} / {total} models")
        self.prog_pct.setText(f"{int(done/total*100)}%")

    def _on_done(self, master):
        self.cancel_btn.setVisible(False)
        self.back_btn.setEnabled(True)
        self._append_log(
            f"\n✓  Scan complete — {len(master)} combinations found.")
        self.scan_done.emit(master)

    def _on_error(self, msg):
        self._append_log(f"\n✗  ERROR: {msg}")
        self.cancel_btn.setVisible(False)
        self.back_btn.setEnabled(True)

# ─────────────────────────────────────────────
#  STEP 3 — Filter & Download Page (with zoom)
# ─────────────────────────────────────────────


class FilterDownloadPage(QWidget):
    go_back = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._master = []
        self._thread = None
        self._out_dir = DEFAULT_DIR
        self._zoom = 1.0
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        # ── Top: filters + table ──────────────────
        top = QWidget()
        top_lay = QVBoxLayout(top)
        top_lay.setContentsMargins(28, 20, 28, 12)
        top_lay.setSpacing(12)

        hdr = QHBoxLayout()
        logo = LogoWidget(28)
        hdr.addWidget(logo)
        hdr.addSpacing(8)
        hdr.addWidget(label("FILTER & SELECT", C["text2"], 15, bold=True))
        hdr.addStretch()
        # Zoom controls
        hdr.addWidget(label("Zoom:", C["text3"], 14))
        zoom_out = secondary_btn("−")
        zoom_out.setFixedSize(32, 32)
        zoom_out.clicked.connect(self._zoom_out)
        zoom_out.setToolTip("Zoom Out (Ctrl+-)")
        zoom_in = secondary_btn("+")
        zoom_in.setFixedSize(32, 32)
        zoom_in.clicked.connect(self._zoom_in)
        zoom_in.setToolTip("Zoom In (Ctrl+=)")
        hdr.addWidget(zoom_out)
        hdr.addWidget(zoom_in)
        top_lay.addLayout(hdr)

        self._filter_checks = {}
        self._filter_frames = {}
        filter_scroll = QScrollArea()
        filter_scroll.setWidgetResizable(True)
        filter_scroll.setFrameShape(QFrame.Shape.NoFrame)
        filter_scroll.setFixedHeight(140)
        filter_container = QWidget()
        self._filter_lay = QGridLayout(filter_container)
        self._filter_lay.setContentsMargins(0, 0, 0, 0)
        self._filter_lay.setSpacing(8)
        filter_scroll.setWidget(filter_container)
        top_lay.addWidget(filter_scroll)

        stats_row = QHBoxLayout()
        self._combo_card, self._combo_val = stat_card(0, "Combinations")
        self._files_card, self._files_val = stat_card(0, "Files", C["green"])
        self._size_card,  self._size_val = stat_card(
            "—", "Est. Size", C["yellow"])
        for c in [self._combo_card, self._files_card, self._size_card]:
            stats_row.addWidget(c)
        stats_row.addStretch()
        top_lay.addLayout(stats_row)

        self._table_model = CombinationModel()
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._table_model)
        self.table = QTableView()
        self.table.setModel(self._proxy)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(True)
        self.table.setMinimumHeight(180)
        top_lay.addWidget(self.table)

        splitter.addWidget(top)

        # ── Bottom: download panel ────────────────
        bot = QWidget()
        bot_lay = QVBoxLayout(bot)
        bot_lay.setContentsMargins(28, 12, 28, 20)
        bot_lay.setSpacing(12)

        bot_lay.addWidget(hline())

        cfg_row = QHBoxLayout()
        self.dir_lbl = label(self._out_dir, C["text2"], 16)
        self.dir_lbl.setWordWrap(True)
        dir_btn = secondary_btn("📁  Choose Folder")
        dir_btn.clicked.connect(self._pick_dir)
        workers_lbl = label("Workers:", C["text2"], 16)
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 32)
        self.workers_spin.setValue(16)
        self.workers_spin.setFixedWidth(70)
        cfg_row.addWidget(label("Output:", C["text3"], 14))
        cfg_row.addWidget(self.dir_lbl, 1)
        cfg_row.addWidget(dir_btn)
        cfg_row.addSpacing(20)
        cfg_row.addWidget(workers_lbl)
        cfg_row.addWidget(self.workers_spin)
        bot_lay.addLayout(cfg_row)

        prog_row = QHBoxLayout()
        self.dl_progress = QProgressBar()
        self.dl_progress.setFixedHeight(10)
        self.dl_pct = label("", C["green"], 16, bold=True)
        self.dl_count = label("", C["text2"], 16)
        prog_row.addWidget(self.dl_progress, 1)
        prog_row.addWidget(self.dl_pct)
        prog_row.addWidget(self.dl_count)
        bot_lay.addLayout(prog_row)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(120)
        bot_lay.addWidget(self.log)

        btn_row = QHBoxLayout()
        self.back_btn = secondary_btn("← Back")
        self.back_btn.clicked.connect(self.go_back)
        self.resolve_btn = secondary_btn("🔍  Resolve Files")
        self.resolve_btn.clicked.connect(self._resolve)
        self.dl_btn = AnimatedDownloadBtn("⬇  Download")
        self.dl_btn.setEnabled(False)
        self.stop_btn = danger_btn("■  Stop")
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self._stop_dl)
        btn_row.addWidget(self.back_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.resolve_btn)
        btn_row.addWidget(self.stop_btn)
        btn_row.addWidget(self.dl_btn)
        bot_lay.addLayout(btn_row)

        splitter.addWidget(bot)
        splitter.setSizes([420, 340])
        root.addWidget(splitter)

        self.dl_btn.clicked.connect(self._start_download)

    def _zoom_in(self):
        self._zoom = min(self._zoom + 0.1, 2.5)
        self._apply_zoom()

    def _zoom_out(self):
        self._zoom = max(self._zoom - 0.1, 0.5)
        self._apply_zoom()

    def _apply_zoom(self):
        base = 17
        size = int(base * self._zoom)
        font = self.table.font()
        font.setPointSize(max(8, size - 4))
        self.table.setFont(font)
        self.table.verticalHeader().setDefaultSectionSize(int(30 * self._zoom))

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self._zoom_in()
            else:
                self._zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def set_master(self, master):
        self._master = master
        self._files = []
        self._resolved = False
        self.dl_btn.setEnabled(False)
        self._build_filters(master)
        self._apply_filters()
        self.log.clear()

    def _build_filters(self, master):
        for i in reversed(range(self._filter_lay.count())):
            w = self._filter_lay.itemAt(i).widget()
            if w:
                w.deleteLater()
        self._filter_checks.clear()

        groups = {
            "Scenario":  sorted({x["scenario"] for x in master}),
            "Variable":  sorted({x["variable"] for x in master}),
            "Version":   sorted({x["version"] for x in master}),
        }
        col = 0
        for gname, values in groups.items():
            grp = QGroupBox(gname)
            grp_lay = QVBoxLayout(grp)
            grp_lay.setContentsMargins(8, 4, 8, 8)
            grp_lay.setSpacing(3)
            self._filter_checks[gname] = {}
            for v in values:
                cb = QCheckBox(v)
                cb.setChecked(True)
                cb.stateChanged.connect(self._apply_filters)
                grp_lay.addWidget(cb)
                self._filter_checks[gname][v] = cb
            self._filter_lay.addWidget(grp, 0, col)
            col += 1

    def _apply_filters(self):
        def checked(gname):
            return {v for v, cb in self._filter_checks.get(gname, {}).items() if cb.isChecked()}

        scens = checked("Scenario")
        vars_ = checked("Variable")
        vers = checked("Version")

        filtered = [
            x for x in self._master
            if x["scenario"] in scens
            and x["variable"] in vars_
            and x["version"] in vers
        ]
        self._table_model.set_data(filtered)
        self._combo_val.setText(str(len(filtered)))
        self._files_val.setText("—")
        self._size_val.setText("—")
        self._files = []
        self._resolved = False
        self.dl_btn.setEnabled(False)
        for i in range(len(COLS) - 1):
            self.table.resizeColumnToContents(i)

    def _resolve(self):
        filtered = self._table_model._data
        if not filtered:
            return
        self.log.append("Resolving file list from S3…")
        self.resolve_btn.setEnabled(False)
        self._res_thread = _ResolveThread(filtered)
        self._res_thread.done.connect(self._on_resolved)
        self._res_thread.start()

    def _on_resolved(self, files):
        self._files = files
        self._resolved = True
        self._files_val.setText(str(len(files)))
        self.log.append(f"✓  {len(files)} files found.")
        self.dl_btn.setEnabled(len(files) > 0)
        self.resolve_btn.setEnabled(True)

    def _pick_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", self._out_dir)
        if d:
            self._out_dir = d
            self.dir_lbl.setText(d)

    def _start_download(self):
        if not self._files:
            return
        tasks = [
            (f["url"],
             os.path.join(self._out_dir, f["model"], f["scenario"], f["variable"], f["file"]))
            for f in self._files
        ]
        self.dl_progress.setRange(0, len(tasks))
        self.dl_progress.setValue(0)
        self.dl_pct.setText("0%")
        self.dl_count.setText(f"0 / {len(tasks)}")
        self.dl_btn.setEnabled(False)
        self.stop_btn.setVisible(True)
        self.back_btn.setEnabled(False)
        self.log.append(
            f"\nStarting download of {len(tasks)} files → {self._out_dir}\n")

        self._thread = DownloadThread(tasks, self.workers_spin.value())
        self._thread.file_done.connect(self._on_file_done)
        self._thread.log.connect(self.log.append)
        self._thread.finished.connect(self._on_dl_done)
        self._thread.start()

    def _on_file_done(self, done, total, ok, name):
        self.dl_progress.setValue(done)
        pct = int(done / total * 100)
        self.dl_pct.setText(f"{pct}%")
        self.dl_count.setText(f"{done} / {total}")

    def _stop_dl(self):
        if self._thread:
            self._thread.stop()
        self.log.append("\n⚠  Download stopped by user.")
        self.stop_btn.setVisible(False)
        self.dl_btn.setEnabled(True)
        self.back_btn.setEnabled(True)

    def _on_dl_done(self, ok, failed):
        self.stop_btn.setVisible(False)
        self.dl_btn.setEnabled(True)
        self.back_btn.setEnabled(True)
        color = C["green"] if failed == 0 else C["yellow"]
        self.log.append(
            f'<span style="color:{color}">✓ Complete — {ok} ok, {failed} failed.</span>'
        )


class _ResolveThread(QThread):
    done = pyqtSignal(list)

    def __init__(self, selection):
        super().__init__()
        self.selection = selection

    def run(self):
        self.done.emit(collect_files(self.selection))


# ─────────────────────────────────────────────
#  Sidebar nav button
# ─────────────────────────────────────────────
class SideBtn(QPushButton):
    def __init__(self, icon_text, label_text, step_num):
        super().__init__()
        self.setObjectName("SideBtn")
        self._step = step_num
        self.setCheckable(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Fixed)
        self.setFixedHeight(52)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(10)
        num = QLabel(str(step_num))
        num.setFixedSize(26, 26)
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num.setStyleSheet(f"""
            background: {C['border2']};
            color: {C['card']};
            border-radius: 13px;
            font-size: 13px;
            font-weight: bold;
            border: 2px solid {C['border']};
        """)
        self._num = num
        ic = QLabel(icon_text)
        ic.setStyleSheet(
            f"font-size: 17px; color: {C['text2']}; background: transparent; border: none;")
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color: {C['text2']}; font-size: 17px;")
        self._lbl = lbl
        lay.addWidget(num)
        lay.addWidget(ic)
        lay.addWidget(lbl)
        lay.addStretch()

    def set_active(self, active):
        if active:
            self._num.setStyleSheet(f"""
                background: {C['accent']};
                color: white;
                border-radius: 13px;
                font-size: 13px;
                font-weight: bold;
                border: 2px solid {C['accent2']};
            """)
            self._lbl.setStyleSheet(
                f"color: {C['accent']}; font-size: 17px; font-weight: bold;")
            self.setProperty("active", "true")
        else:
            self._num.setStyleSheet(f"""
                background: {C['border2']};
                color: {C['card']};
                border-radius: 13px;
                font-size: 13px;
                font-weight: bold;
                border: 2px solid {C['border']};
            """)
            self._lbl.setStyleSheet(f"color: {C['text2']}; font-size: 17px;")
            self.setProperty("active", "false")
        self.style().unpolish(self)
        self.style().polish(self)

# ─────────────────────────────────────────────
#  Main Window  (with close warning)
# ─────────────────────────────────────────────


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            f"GULP — GDDP Unified Loader & Processor  v{APP_VERSION}")
        self.setMinimumSize(1000, 680)
        self.resize(1200, 760)
        self._master = []
        self._downloading = False
        self._build()
        # Keyboard zoom shortcuts
        QShortcut(QKeySequence("Ctrl+="), self, self._page_dl._zoom_in)
        QShortcut(QKeySequence("Ctrl++"), self, self._page_dl._zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, self._page_dl._zoom_out)

    def closeEvent(self, event):
        """Show warning before closing."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirm Exit")
        msg.setIcon(QMessageBox.Icon.Warning)
        if self._downloading:
            msg.setText("A download is currently in progress!")
            msg.setInformativeText(
                "Closing now will interrupt the download and may leave incomplete files.\n\n"
                "Are you sure you want to quit GULP?"
            )
        else:
            msg.setText("Are you sure you want to quit GULP?")
            msg.setInformativeText("Any unsaved progress will be lost.")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background: {C['bg']};
                font-size: 17px;
            }}
            QLabel {{
                color: {C['text']};
                font-size: 17px;
            }}
            QPushButton {{
                background: {C['card']};
                color: {C['text']};
                border: 3px solid {C['border']};
                border-radius: 5px;
                padding: 6px 18px;
                font-size: 17px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {C['hover']}; }}
        """)
        result = msg.exec()
        if result == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──────────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(210)
        sb_lay = QVBoxLayout(sidebar)
        sb_lay.setContentsMargins(0, 0, 0, 0)
        sb_lay.setSpacing(0)

        # Logo / title
        logo_area = QWidget()
        logo_area.setFixedHeight(80)
        logo_area.setStyleSheet(
            f"background: {C['panel']}; border-bottom: 4px solid {C['sidebar_border']};")
        ll = QHBoxLayout(logo_area)
        ll.setContentsMargins(14, 0, 14, 0)
        logo = LogoWidget(40)
        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        t1 = QLabel("GULP")
        t1.setStyleSheet(
            f"color: {C['text']}; font-size: 20px; font-weight: bold; letter-spacing: 4px; border: none; background: transparent;")
        t2 = QLabel(f"v{APP_VERSION}")
        t2.setStyleSheet(
            f"color: {C['text3']}; font-size: 13px; border: none; background: transparent;")
        title_col.addWidget(t1)
        title_col.addWidget(t2)
        ll.addWidget(logo)
        ll.addSpacing(10)
        ll.addLayout(title_col)
        ll.addStretch()
        sb_lay.addWidget(logo_area)
        sb_lay.addSpacing(8)

        self._nav_btns = []
        steps = [
            ("Models",   0),
            ("Scan",     1),
            ("Download", 2),
        ]
        for icon, lbl_text, idx in steps:
            btn = SideBtn(icon, lbl_text, idx + 1)
            btn.clicked.connect(lambda _, i=idx: self._maybe_goto(i))
            sb_lay.addWidget(btn)
            self._nav_btns.append(btn)

        sb_lay.addStretch()

        # Bottom logo repeat + info
        bottom_logo = LogoWidget(28)
        bottom_area = QWidget()
        bottom_area.setStyleSheet(f"background: transparent;")
        bl = QVBoxLayout(bottom_area)
        bl.setContentsMargins(14, 8, 14, 12)
        bl.setSpacing(4)
        brow = QHBoxLayout()
        brow.addWidget(bottom_logo)
        brow.addSpacing(6)
        binfo = QLabel("NASA NEX-GDDP-CMIP6\nAWS S3 Public Dataset")
        binfo.setStyleSheet(
            f"color: {C['text3']}; font-size: 12px; background: transparent; border: none;")
        binfo.setWordWrap(True)
        brow.addWidget(binfo)
        brow.addStretch()
        bl.addLayout(brow)
        sb_lay.addWidget(bottom_area)

        root.addWidget(sidebar)

        # ── Page stack ───────────────────────────
        self._stack = QStackedWidget()

        self._page_models = ModelPage()
        self._page_scan = ScanPage()
        self._page_dl = FilterDownloadPage()

        self._stack.addWidget(self._page_models)
        self._stack.addWidget(self._page_scan)
        self._stack.addWidget(self._page_dl)

        root.addWidget(self._stack, 1)

        # ── Connections ───────────────────────────
        self._page_models.models_confirmed.connect(self._start_scan)
        self._page_scan.back_btn.clicked.connect(lambda: self._goto(0))
        self._page_scan.scan_done.connect(self._on_scan_done)
        self._page_dl.go_back.connect(lambda: self._goto(0))

        # Track downloading state for close warning
        self._page_dl.dl_btn.clicked.connect(
            lambda: setattr(self, '_downloading', True))
        self._page_dl.stop_btn.clicked.connect(
            lambda: setattr(self, '_downloading', False))

        # ── Status bar ───────────────────────────
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready — Select models to begin.")

        self._goto(0)

    def _goto(self, idx):
        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_btns):
            btn.set_active(i == idx)

    def _maybe_goto(self, idx):
        if idx == 0:
            self._goto(0)
        elif idx == 1 and self._master:
            self._goto(1)
        elif idx == 2 and self._master:
            self._goto(2)

    def _start_scan(self, models):
        self._goto(1)
        self.status.showMessage(f"Scanning {len(models)} model(s)…")
        self._page_scan.start_scan(models)

    def _on_scan_done(self, master):
        self._master = master
        self._page_dl.set_master(master)
        self.status.showMessage(
            f"Scan complete — {len(master)} combinations across "
            f"{len({x['model'] for x in master})} model(s).")
        self._goto(2)


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────
def _make_fallback_icon():
    """Draw the GULP drop logo into a QIcon used when no .ico file exists."""
    pix = QPixmap(256, 256)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    grad = QLinearGradient(0, 0, 256, 256)
    grad.setColorAt(0, QColor("#E65100"))
    grad.setColorAt(1, QColor("#BF360C"))
    p.setBrush(QBrush(grad))
    p.setPen(QPen(QColor("#3E2723"), 8))
    p.drawEllipse(4, 4, 248, 248)
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    drop = QPainterPath()
    cx, tip, bot, bulge = 128.0, 30.0, 218.0, 76.0
    drop.moveTo(cx, tip)
    drop.cubicTo(cx+bulge*1.1, 97, cx+bulge*0.95, 184, cx, bot)
    drop.cubicTo(cx-bulge*0.95, 184, cx-bulge*1.1, 97, cx, tip)
    drop.closeSubpath()
    p.drawPath(drop)
    p.end()
    return QIcon(pix)


def main():
    # Tell Windows this is its own app so taskbar/title bar shows our icon
    # (without this, Windows uses the pythonw.exe icon instead)
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "GULP.GeoDataLoader.1.0"
        )
    except Exception:
        pass  # Non-Windows platform — ignore

    app = QApplication(sys.argv)
    app.setApplicationName("GULP")
    app.setApplicationVersion(APP_VERSION)
    app.setStyleSheet(QSS)

    # Load icon from assets/ — .ico has multi-resolution frames (best for Windows)
    assets = Path(__file__).parent.parent / "assets"
    app_icon = None
    for candidate in [assets / "gulp.ico", assets / "gulp.png", assets / "gulp.bmp"]:
        if candidate.exists():
            loaded = QIcon(str(candidate))
            if not loaded.isNull():
                app_icon = loaded
                break
    if app_icon is None:
        app_icon = _make_fallback_icon()

    app.setWindowIcon(app_icon)   # taskbar (Linux/macOS)

    win = MainWindow()
    win.setWindowIcon(app_icon)   # title bar + Windows taskbar
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
