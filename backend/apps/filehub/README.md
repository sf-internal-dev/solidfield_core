# App: Filehub

## Description
Responsible for managing, storing, and processing user-uploaded files on the SolidField platform. This includes execution photos, digital signatures, PDF documents, and other attachments related to Service Orders.

## Key Features

- File uploads by field technicians (via Mobile or Web)
- Client digital signature uploads
- Image processing and optimization (e.g., compression, resizing, timestamp watermarking)
- Secure file storage via Wasabi (using `django-storages` + `boto3`)
- Upload traceability control (who uploaded, when, from which device)
- Hardware API integration (e.g., mobile camera capture)
- Attachment linking and access control for Service Orders
- Generation of secure signed URLs for file downloads (when applicable)
- Validation of file types, sizes, and metadata during upload (e.g., blocking invalid formats)

## Notes

This app works closely with the **Service Order** and **Operational Dashboard** apps, ensuring full traceability of uploaded files.

- Users with **Execution** or **Coordination** permissions have restricted access to uploads and can only view files linked to their own Service Orders.
- Users with **Full Control** permissions have administrative access to all company files.
