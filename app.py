import os
import uuid
import shutil
import glob
import sys
import tempfile
from flask import Flask, request, jsonify, send_from_directory, send_file
import fitz  # PyMuPDF
from PIL import Image, ImageWin, ImageOps
import win32print
import win32ui
import win32con
import win32file

app = Flask(__name__, static_folder=".")
app.secret_key = "xevo_kiosk_secret_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_DIR = os.path.join(BASE_DIR, "kiosk_sessions")

if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

# Helper to format file sizes
def format_size(bytes_size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

# Ensure session cleanup on startup
try:
    if os.path.exists(SESSION_DIR):
        shutil.rmtree(SESSION_DIR)
    os.makedirs(SESSION_DIR)
except Exception as e:
    print("Warning during startup session cleanup:", e)

# ----------------- STATIC ROUTING -----------------
@app.route('/')
def index():
    return send_from_directory('.', 'welcome.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# ----------------- SESSION APIs -----------------
@app.route('/api/session/start', methods=['POST'])
def start_session():
    session_id = str(uuid.uuid4())[:8]
    session_path = os.path.join(SESSION_DIR, f"session_{session_id}")
    os.makedirs(session_path, exist_ok=True)
    return jsonify({"success": True, "session_id": session_id})

@app.route('/api/session/abort', methods=['POST'])
def abort_session():
    data = request.json or {}
    session_id = data.get('session_id')
    if session_id:
        session_path = os.path.join(SESSION_DIR, f"session_{session_id}")
        if os.path.exists(session_path):
            try:
                shutil.rmtree(session_path)
            except Exception as e:
                return jsonify({"success": False, "error": str(e)})
    return jsonify({"success": True})

# ----------------- PRINTERS API -----------------
@app.route('/api/printers', methods=['GET'])
def list_printers():
    try:
        printers_info = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )
        printers = [p[2] for p in printers_info]
        try:
            default_printer = win32print.GetDefaultPrinter()
        except:
            default_printer = printers[0] if printers else ""
        return jsonify({"success": True, "printers": printers, "default": default_printer})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ----------------- USB DRIVE API -----------------
@app.route('/api/usb/detect', methods=['GET'])
def detect_usb():
    drives = []
    # Scan drive letters
    for letter in 'DEFGHIJKLMNOPQRSTUVWXYZ':
        drive_path = f"{letter}:\\"
        try:
            drive_type = win32file.GetDriveType(drive_path)
            if drive_type == win32file.DRIVE_REMOVABLE:
                drives.append(drive_path)
        except:
            pass

    if not drives:
        return jsonify({"success": True, "detected": False, "files": []})

    # List files in detected drives (limit depth to avoid long searches)
    usb_files = []
    supported_exts = {'.pdf', '.jpg', '.jpeg', '.png'}
    
    for drive in drives:
        try:
            # List root files
            for entry in os.scandir(drive):
                if entry.is_file():
                    ext = os.path.splitext(entry.name)[1].lower()
                    if ext in supported_exts:
                        stat = entry.stat()
                        usb_files.append({
                            "drive": drive,
                            "name": entry.name,
                            "path": entry.path,
                            "size": stat.st_size,
                            "formatted_size": format_size(stat.st_size)
                        })
            
            # List files 1-level deep in folders
            for entry in os.scandir(drive):
                if entry.is_dir() and not entry.name.startswith('.'):
                    try:
                        for sub_entry in os.scandir(entry.path):
                            if sub_entry.is_file():
                                ext = os.path.splitext(sub_entry.name)[1].lower()
                                if ext in supported_exts:
                                    stat = sub_entry.stat()
                                    usb_files.append({
                                        "drive": drive,
                                        "name": f"{entry.name}/{sub_entry.name}",
                                        "path": sub_entry.path,
                                        "size": stat.st_size,
                                        "formatted_size": format_size(stat.st_size)
                                    })
                    except:
                        pass
        except Exception as e:
            print(f"Error scanning drive {drive}: {e}")
            
    return jsonify({
        "success": True,
        "detected": True,
        "drives": drives,
        "files": usb_files
    })

# ----------------- UPLOAD / IMPORT FILE -----------------
@app.route('/api/upload', methods=['POST'])
def upload_file():
    session_id = request.form.get('session_id')
    if not session_id:
        return jsonify({"success": False, "error": "No session ID provided"})
        
    session_path = os.path.join(SESSION_DIR, f"session_{session_id}")
    if not os.path.exists(session_path):
        os.makedirs(session_path, exist_ok=True)

    # 1. Check if files uploaded via form
    if 'files' in request.files:
        files = request.files.getlist('files')
        saved_files = []
        for file in files:
            if file.filename:
                file_id = str(uuid.uuid4())[:8]
                ext = os.path.splitext(file.filename)[1].lower()
                safe_name = f"{file_id}{ext}"
                dest_path = os.path.join(session_path, safe_name)
                file.save(dest_path)
                
                # Get metadata
                page_count = get_page_count(dest_path)
                saved_files.append({
                    "id": file_id,
                    "original_name": file.filename,
                    "size": os.path.getsize(dest_path),
                    "formatted_size": format_size(os.path.getsize(dest_path)),
                    "pages": page_count
                })
        return jsonify({"success": True, "files": saved_files})

    # 2. Check if importing from local path (USB copy)
    data = request.json or {}
    source_path = data.get('source_path')
    if source_path and os.path.exists(source_path):
        filename = os.path.basename(source_path)
        file_id = str(uuid.uuid4())[:8]
        ext = os.path.splitext(filename)[1].lower()
        safe_name = f"{file_id}{ext}"
        dest_path = os.path.join(session_path, safe_name)
        try:
            shutil.copy2(source_path, dest_path)
            page_count = get_page_count(dest_path)
            return jsonify({
                "success": True,
                "files": [{
                    "id": file_id,
                    "original_name": filename,
                    "size": os.path.getsize(dest_path),
                    "formatted_size": format_size(os.path.getsize(dest_path)),
                    "pages": page_count
                }]
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})

    return jsonify({"success": False, "error": "No file contents or source path found"})

def get_page_count(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.pdf':
        try:
            doc = fitz.open(filepath)
            count = doc.page_count
            doc.close()
            return count
        except:
            return 1
    return 1  # Images are 1 page

# ----------------- PREVIEW API -----------------
@app.route('/api/session/preview/<session_id>/<file_id>/<int:page_num>', methods=['GET'])
def get_preview(session_id, file_id, page_num):
    session_path = os.path.join(SESSION_DIR, f"session_{session_id}")
    # Find the file with matches file_id
    pattern = os.path.join(session_path, f"{file_id}.*")
    matches = glob.glob(pattern)
    if not matches:
        return "File not found", 404
        
    filepath = matches[0]
    ext = os.path.splitext(filepath)[1].lower()
    
    # Cache previews inside session folder
    preview_dir = os.path.join(session_path, "previews")
    os.makedirs(preview_dir, exist_ok=True)
    preview_path = os.path.join(preview_dir, f"{file_id}_{page_num}.jpg")
    
    if os.path.exists(preview_path):
        return send_file(preview_path, mimetype='image/jpeg')

    try:
        if ext == '.pdf':
            doc = fitz.open(filepath)
            if page_num < 0 or page_num >= doc.page_count:
                doc.close()
                return "Page out of bounds", 400
                
            page = doc[page_num]
            # Zoom factor to speed up rendering while retaining readability
            zoom = 1.5  # 150% scaling
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Save pixmap as jpeg
            pix.save(preview_path, "jpeg")
            doc.close()
            return send_file(preview_path, mimetype='image/jpeg')
        else:
            # It's an image. Just copy/save as jpeg for preview
            img = Image.open(filepath)
            # Handle orientation/EXIF rotation if any
            img = ImageOps.exif_transpose(img)
            img.convert('RGB').save(preview_path, 'JPEG')
            return send_file(preview_path, mimetype='image/jpeg')
    except Exception as e:
        return f"Error rendering preview: {str(e)}", 500

# ----------------- PRINT API -----------------
@app.route('/api/session/print', methods=['POST'])
def print_document():
    data = request.json or {}
    session_id = data.get('session_id')
    file_id = data.get('file_id')
    printer_name = data.get('printer_name')
    copies = int(data.get('copies', 1))
    paper_size = data.get('paper_size', 'A4')
    orientation = data.get('orientation', 'portrait')  # portrait or landscape
    color_mode = data.get('color_mode', 'bw')  # color or bw

    if not session_id or not file_id or not printer_name:
        return jsonify({"success": False, "error": "Missing print parameters"})

    session_path = os.path.join(SESSION_DIR, f"session_{session_id}")
    pattern = os.path.join(session_path, f"{file_id}.*")
    matches = glob.glob(pattern)
    if not matches:
        return jsonify({"success": False, "error": "File not found"})

    filepath = matches[0]
    ext = os.path.splitext(filepath)[1].lower()

    # Load printer
    try:
        hprinter = win32print.OpenPrinter(printer_name)
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to open printer: {e}"})

    try:
        # Configure printer DevMode
        info = win32print.GetPrinter(hprinter, 2)
        devmode = info["pDevMode"]
        
        # Set Copies
        devmode.Copies = copies
        
        # Set Orientation: 1 = PORTRAIT, 2 = LANDSCAPE
        devmode.Orientation = 2 if orientation == 'landscape' else 1
        
        # Set Color: 1 = MONOCHROME (B&W), 2 = COLOR
        devmode.Color = 1 if color_mode == 'bw' else 2
        
        # Set Paper Size (Optional, Win32 constant map)
        if paper_size == 'A4':
            devmode.PaperSize = win32con.DMPAPER_A4
        elif paper_size == 'Letter':
            devmode.PaperSize = win32con.DMPAPER_LETTER
        elif paper_size == 'A3':
            devmode.PaperSize = win32con.DMPAPER_A3

        # Update printer properties
        win32print.SetPrinter(hprinter, 2, info, 0)
        
        # Start Print Spooler DC
        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(printer_name)
        
        # Document Title
        doc_title = f"XEVO Kiosk Print Job - {file_id}"
        hdc.StartDoc(doc_title)
        
        # Get printable dimensions
        printable_width = hdc.GetDeviceCaps(win32con.HORZRES)
        printable_height = hdc.GetDeviceCaps(win32con.VERTRES)

        # Print logic based on file type
        if ext == '.pdf':
            doc = fitz.open(filepath)
            for page_num in range(doc.page_count):
                hdc.StartPage()
                
                # Render page to high-quality image in temp file
                page = doc[page_num]
                # High DPI (300) for sharp print quality
                zoom = 300 / 72.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                    tmp_name = tmp.name
                
                try:
                    pix.save(tmp_name)
                    img = Image.open(tmp_name)
                    img = ImageOps.exif_transpose(img)
                    
                    # Convert to grayscale if B&W to ensure printer registers monochrome
                    if color_mode == 'bw':
                        img = img.convert('L')
                    else:
                        img = img.convert('RGB')
                        
                    # Scale image to fill printable area maintaining aspect ratio
                    img_w, img_h = img.size
                    
                    # Aspect fit fitting
                    ratio = min(printable_width / img_w, printable_height / img_h)
                    new_w = int(img_w * ratio)
                    new_h = int(img_h * ratio)
                    
                    # Center page
                    offset_x = (printable_width - new_w) // 2
                    offset_y = (printable_height - new_h) // 2
                    
                    dib = ImageWin.Dib(img)
                    dib.draw(hdc.GetHandleOutput(), (offset_x, offset_y, offset_x + new_w, offset_y + new_h))
                finally:
                    # Clean up temp file
                    if os.path.exists(tmp_name):
                        try:
                            os.remove(tmp_name)
                        except:
                            pass
                
                hdc.EndPage()
            doc.close()
        else:
            # Image file
            hdc.StartPage()
            img = Image.open(filepath)
            img = ImageOps.exif_transpose(img)
            
            if color_mode == 'bw':
                img = img.convert('L')
            else:
                img = img.convert('RGB')
                
            img_w, img_h = img.size
            ratio = min(printable_width / img_w, printable_height / img_h)
            new_w = int(img_w * ratio)
            new_h = int(img_h * ratio)
            
            offset_x = (printable_width - new_w) // 2
            offset_y = (printable_height - new_h) // 2
            
            dib = ImageWin.Dib(img)
            dib.draw(hdc.GetHandleOutput(), (offset_x, offset_y, offset_x + new_w, offset_y + new_h))
            hdc.EndPage()
            
        hdc.EndDoc()
        hdc.DeleteDC()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": f"Printing failed: {str(e)}"})
    finally:
        win32print.ClosePrinter(hprinter)

if __name__ == '__main__':
    # Running locally on port 5000
    print("XEVO Print Kiosk backend initialized.")
    app.run(host='0.0.0.0', port=5000, debug=True)
