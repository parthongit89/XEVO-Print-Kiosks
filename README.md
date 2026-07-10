# XEVO – Smart Xerox Printing Kiosk System

![Version](https://img.shields.io/badge/version-1.0-blue)
![React](https://img.shields.io/badge/React-Frontend-61DAFB)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-Styling-38BDF8)
![Electron](https://img.shields.io/badge/Electron-Kiosk_Mode-47848F)
![License](https://img.shields.io/badge/license-MIT-green)

## Overview

XEVO is a modern self-service Xerox printing kiosk system designed for print shops, libraries, colleges, cyber cafés, and commercial printing centers.

The platform provides a touchscreen-based multilingual printing experience that allows users to upload documents through USB or Type-C devices, preview files, configure print settings, and print using the system's default print dialog.

XEVO focuses on simplicity, accessibility, automation, and professional kiosk-grade usability.

---

## Key Features

### Multilingual Support
- English
- हिंदी
- मराठी

### Smart Printing Workflow
- Guided printing process
- Voice assistant support
- Document preview
- Print settings management
- Session-based workflow

### Upload Methods
- USB Device
- Type-C Device
- Local Storage

### Supported File Formats
- PDF
- DOCX
- PPT
- JPG
- PNG

### Printing Features
- Print Preview
- Copies Selection
- Paper Size Selection
- Orientation Selection
- Color / Black & White Mode
- Queue Status Simulation

### System Integration
- System Print Dialog
- Acrobat Reader Compatibility
- Windows Printing Support
- Local Printer Integration

### Security Features
- Automatic Session Expiry
- File Cleanup After Session
- Abort Session Protection
- Kiosk Mode Restrictions

---

## User Workflow

### 1. Welcome Screen
Users begin by pressing:

START SESSION

---

### 2. Language Selection

Available Languages:

- English
- हिंदी
- मराठी

The selected language is applied throughout the session.

---

### 3. Upload Method

Users choose:

- USB
- TYPE-C

The system provides visual guidance and voice instructions.

---

### 4. Upload Files

Users can:

- Drag & Drop Files
- Select Files
- Upload Multiple Documents

Supported formats include PDF, DOCX, PPT, JPG, and PNG.

---

### 5. Print Preview

Before printing users can:

- Review documents
- Change copies
- Change paper size
- Select orientation
- Choose color mode

---

### 6. Print Process

When the PRINT button is clicked:

1. Files are validated.
2. Print settings are applied.
3. Print preview is generated.
4. The default system print dialog is launched.

Example:

```javascript
window.print();
```

If Adobe Acrobat Reader is configured as the default PDF application, the operating system may route printing through Acrobat.

---

### 7. Completion

After printing:

> Your copies were collected by the owner. Please complete payment and collect your documents.

The user is redirected to the Thank You screen.

---

## Session Management

### Automatic Timeout

Session expires after:

- 5 minutes of inactivity

Users are redirected back to the home screen.

### Abort Session

If the user chooses:

ABORT SESSION

The system:

- Deletes uploaded files
- Clears temporary data
- Returns to home screen

---

## Accessibility

XEVO is designed for users of all ages.

Features include:

- Large buttons
- High contrast design
- Touchscreen optimization
- Voice assistance
- Simple instructions
- Clear navigation

---

## Technology Stack

### Frontend
- React
- TypeScript
- Tailwind CSS
- Framer Motion

### Desktop Kiosk (Optional)
- Electron.js

### Backend (Optional)
- Node.js
- Express.js

### Database (Optional)
- PostgreSQL
- SQLite

---

## Commercial Deployment

Recommended Environment:

### Hardware
- Touchscreen Monitor
- Thermal Printer
- Laser Printer
- USB Ports
- Type-C Ports

### Software
- Windows 11
- Adobe Acrobat Reader
- Electron Kiosk Application

---

## Future Roadmap

### Planned Features

- QR Code Upload
- Mobile Device Transfer
- Cloud Printing
- AI Voice Assistant
- Printer Health Monitoring
- Print Analytics Dashboard
- Payment Gateway Integration
- UPI Support
- Receipt Generation
- Multi-Printer Management

---

## Security

- Automatic Session Cleanup
- User Data Isolation
- Temporary File Removal
- Secure Printing Workflow
- Kiosk Mode Protection

---

## Project Vision

XEVO aims to modernize traditional Xerox centers by providing a smart, automated, multilingual, and user-friendly self-service printing experience.

The goal is to reduce operator workload, improve customer convenience, and deliver a professional commercial-grade printing solution suitable for educational institutions, libraries, offices, and public printing centers.

---

## Author

**Parth Sonavane**

AI Developer | Python Developer | Automation Enthusiast

Building practical technology solutions focused on automation, productivity, and real-world problem solving.

---

## License

MIT License

Copyright © 2026 Parth Sonavane

Permission is hereby granted to use, modify, and distribute this software for educational and commercial purposes subject to the terms of the MIT License.
