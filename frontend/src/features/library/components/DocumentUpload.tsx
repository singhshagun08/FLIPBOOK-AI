
import { useRef, useState, type ChangeEvent, type DragEvent } from "react";
import {
  Upload,
  FileText,
  X,
  CheckCircle2,
  AlertCircle,
  LoaderCircle,
} from "lucide-react";

import { getApiErrorMessage } from "../../../services/api/client";
import documentsApi from "../../../services/api/documents.api";

interface DocumentUploadProps {
  onUploadSuccess?: () => void;
}

const MAX_FILE_SIZE = 50 * 1024 * 1024;
const ACCEPTED_TYPE = "application/pdf";

export default function DocumentUpload({
  onUploadSuccess,
}: DocumentUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // ----------------------------------------------------------
  // VALIDATE PDF
  // ----------------------------------------------------------

  const validateFile = (file: File): boolean => {
    setError("");
    setSuccess("");

    const hasPdfExtension = file.name.toLowerCase().endsWith(".pdf");

    if (file.type !== ACCEPTED_TYPE && !hasPdfExtension) {
      setError("Only PDF files are supported.");
      return false;
    }

    if (!hasPdfExtension) {
      setError("Please select a file with a .pdf extension.");
      return false;
    }

    if (file.size === 0) {
      setError("The selected file is empty.");
      return false;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError("File size cannot exceed 50 MB.");
      return false;
    }

    setSelectedFile(file);
    setTitle(file.name.replace(/\.pdf$/i, ""));
    return true;
  };

  // ----------------------------------------------------------
  // FILE INPUT
  // ----------------------------------------------------------

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (file) {
      validateFile(file);
    }

    event.target.value = "";
  };

  // ----------------------------------------------------------
  // DRAG AND DROP
  // ----------------------------------------------------------

  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);

    const file = event.dataTransfer.files?.[0];

    if (file) {
      validateFile(file);
    }
  };

  // ----------------------------------------------------------
  // REMOVE SELECTED FILE
  // ----------------------------------------------------------

  const removeSelectedFile = () => {
    setSelectedFile(null);
    setTitle("");
    setDescription("");
    setError("");
    setSuccess("");
    setUploadProgress(0);
  };

  // ----------------------------------------------------------
  // UPLOAD AND AUTOMATICALLY PROCESS PDF
  // ----------------------------------------------------------

  const handleUpload = async () => {
    if (!selectedFile || isUploading || isProcessing) return;

    if (!title.trim()) {
      setError("Please enter a document title.");
      return;
    }

    setError("");
    setSuccess("");
    setIsUploading(true);
    setUploadProgress(0);

    let uploadedDocumentId: number | null = null;

    try {
      // STEP 1: Upload PDF
      const uploadResponse = await documentsApi.upload(
        {
          file: selectedFile,
          title: title.trim(),
          description: description.trim() || undefined,
        },
        (percentage) => {
          setUploadProgress(percentage);
        }
      );

      uploadedDocumentId = uploadResponse.data.id;

      setUploadProgress(100);
      setIsUploading(false);
      setIsProcessing(true);

      // STEP 2: Automatically process PDF
      setSuccess("PDF uploaded. Extracting text and creating AI index...");

      await documentsApi.process(uploadedDocumentId);

      // STEP 3: Processing completed
      setSuccess(
        "PDF uploaded and processed successfully! It is now ready for AI Assistant."
      );

      setSelectedFile(null);
      setTitle("");
      setDescription("");
      setUploadProgress(0);

      // STEP 4: Refresh Library
      onUploadSuccess?.();

    } catch (uploadError) {
      console.error("Document upload or processing failed:", uploadError);

      const message = getApiErrorMessage(uploadError);

      if (uploadedDocumentId !== null) {
        setError(
          `The PDF was uploaded, but processing failed: ${message}. You can retry processing from the Library.`
        );

        // Refresh Library because the PDF may already exist.
        onUploadSuccess?.();
      } else {
        setError(message);
      }
    } finally {
      setIsUploading(false);
      setIsProcessing(false);
    }
  };

  // ----------------------------------------------------------
  // FORMAT FILE SIZE
  // ----------------------------------------------------------

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }

    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  // ----------------------------------------------------------
  // UI
  // ----------------------------------------------------------

  const busy = isUploading || isProcessing;

  return (
    <section className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">
          Upload a document
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Add PDF documents to your personal knowledge library.
        </p>
      </div>

      {/* Error message */}
      {error && (
        <div
          role="alert"
          className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"
        >
          <AlertCircle size={19} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Success message */}
      {success && (
        <div
          role="status"
          className="flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700"
        >
          <CheckCircle2 size={19} className="mt-0.5 shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {/* Drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => {
          if (!busy) fileInputRef.current?.click();
        }}
        onKeyDown={(event) => {
          if (!busy && (event.key === "Enter" || event.key === " ")) {
            event.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        role="button"
        tabIndex={busy ? -1 : 0}
        aria-label="Choose or drop a PDF file"
        className={`flex min-h-[220px] cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-10 text-center transition ${
          isDragging
            ? "border-violet-500 bg-violet-50"
            : "border-slate-300 bg-slate-50 hover:border-violet-400 hover:bg-violet-50/50"
        } ${busy ? "cursor-not-allowed opacity-60" : ""}`}
      >
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-100 text-violet-600">
          <Upload size={27} />
        </div>

        <p className="font-semibold text-slate-800">
          Drag and drop your PDF here
        </p>

        <p className="mt-2 text-sm text-slate-500">
          or click to browse files
        </p>

        <p className="mt-3 text-xs text-slate-400">
          PDF files only · Maximum size 50 MB
        </p>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileChange}
          className="hidden"
          disabled={busy}
        />
      </div>

      {/* Selected file */}
      {selectedFile && (
        <div className="space-y-5 rounded-2xl border border-slate-200 bg-white p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-red-50 text-red-600">
              <FileText size={25} />
            </div>

            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-slate-800">
                {selectedFile.name}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {formatFileSize(selectedFile.size)}
              </p>
            </div>

            <button
              type="button"
              onClick={removeSelectedFile}
              disabled={busy}
              aria-label="Remove selected file"
              className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
            >
              <X size={19} />
            </button>
          </div>

          {/* Document title */}
          <div>
            <label
              htmlFor="document-title"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Document title
            </label>

            <input
              id="document-title"
              type="text"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              maxLength={255}
              placeholder="Enter document title"
              className="form-control"
              disabled={busy}
            />
          </div>

          {/* Description */}
          <div>
            <label
              htmlFor="document-description"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Description (optional)
            </label>

            <textarea
              id="document-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={3}
              placeholder="Add a short description..."
              className="form-control resize-y"
              disabled={busy}
            />
          </div>

          {/* Upload progress */}
          {isUploading && (
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-medium text-slate-600">
                <span>Uploading document...</span>
                <span>{uploadProgress}%</span>
              </div>

              <div
                className="h-2 overflow-hidden rounded-full bg-slate-100"
                role="progressbar"
                aria-valuenow={uploadProgress}
                aria-valuemin={0}
                aria-valuemax={100}
              >
                <div
                  className="h-full rounded-full bg-violet-600 transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Processing indicator */}
          {isProcessing && (
            <div className="flex items-center gap-3 rounded-xl bg-violet-50 p-4 text-sm text-violet-700">
              <LoaderCircle size={20} className="shrink-0 animate-spin" />
              <div>
                <p className="font-semibold">Processing your PDF...</p>
                <p className="mt-1 text-xs">
                  Extracting text, creating chunks, generating embeddings and
                  indexing your document. Please wait.
                </p>
              </div>
            </div>
          )}

          {/* Upload button */}
          <button
            type="button"
            onClick={handleUpload}
            disabled={busy}
            className="flex min-h-[46px] w-full items-center justify-center gap-2 rounded-xl bg-violet-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isUploading ? (
              <>
                <LoaderCircle size={18} className="animate-spin" />
                Uploading...
              </>
            ) : isProcessing ? (
              <>
                <LoaderCircle size={18} className="animate-spin" />
                Processing PDF...
              </>
            ) : (
              <>
                <Upload size={18} />
                Upload and Process PDF
              </>
            )}
          </button>
        </div>
      )}
    </section>
  );
}
