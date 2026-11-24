import { useEffect, useRef, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import type { PDFDocumentProxy } from "pdfjs-dist";
import {
  ArrowLeft,
  AlertCircle,
  BookOpen,
  Loader2,
  RefreshCw,
} from "lucide-react";

import { Document as PDFDocument } from "react-pdf";

import apiClient, { getApiErrorMessage } from "../../../services/api/client";

import PDFToolbar from "../components/PDFToolbar";
import PDFPage from "../components/PDFPage";
import PageNavigation from "../components/PageNavigation";
import PDFThumbnailSidebar from "../components/PDFThumbnailSidebar";

import "react-pdf/dist/Page/TextLayer.css";
import "react-pdf/dist/Page/AnnotationLayer.css";

type FitMode = "width" | "page" | null;

export default function PDFReaderPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const documentId = searchParams.get("id");
  const documentTitle = searchParams.get("title") || "PDF Document";

  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfDocument, setPdfDocument] = useState<PDFDocumentProxy | null>(null);

  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [zoom, setZoom] = useState(1);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [fitMode, setFitMode] = useState<FitMode>(null);

  const readerContainerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<HTMLDivElement>(null);

  const loadPDF = async () => {
    if (!documentId || !/^\d+$/.test(documentId)) {
      setError("Invalid document ID. Please open a PDF from your Library.");
      setLoading(false);
      return;
    }

    let generatedUrl: string | null = null;

    try {
      setLoading(true);
      setError("");
      setPdfDocument(null);
      setCurrentPage(1);
      setTotalPages(0);
      setZoom(1);
      setFitMode(null);

      const response = await apiClient.get(
        `/documents/${documentId}/download`,
        {
          responseType: "blob",
        },
      );

      const contentType = response.headers["content-type"];

      if (
        typeof contentType === "string" &&
        !contentType.toLowerCase().includes("application/pdf")
      ) {
        throw new Error("The server did not return a valid PDF file.");
      }

      const pdfBlob = new Blob([response.data], {
        type: "application/pdf",
      });

      generatedUrl = URL.createObjectURL(pdfBlob);
      setPdfUrl(generatedUrl);
    } catch (err) {
      if (generatedUrl) {
        URL.revokeObjectURL(generatedUrl);
      }

      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadPDF();

    return () => {
      setPdfUrl((previousUrl) => {
        if (previousUrl) {
          URL.revokeObjectURL(previousUrl);
        }

        return null;
      });
    };
  }, [documentId]);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(
        document.fullscreenElement === readerContainerRef.current,
      );
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);

    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
    };
  }, []);

  // Calculate fit-to-width and fit-to-page zoom.
  useEffect(() => {
    if (!pdfDocument || !viewerRef.current || !fitMode) return;

    let cancelled = false;

    const calculateFit = async () => {
      try {
        const page = await pdfDocument.getPage(currentPage);
        const viewport = page.getViewport({ scale: 1 });

        const viewer = viewerRef.current;
        if (!viewer || cancelled) return;

        const availableWidth = viewer.clientWidth - 64;
        const availableHeight = viewer.clientHeight - 64;

        if (availableWidth <= 0 || availableHeight <= 0) return;

        const widthScale = availableWidth / viewport.width;
        const heightScale = availableHeight / viewport.height;

        const calculatedZoom =
          fitMode === "width" ? widthScale : Math.min(widthScale, heightScale);

        if (!cancelled) {
          setZoom(Math.min(3, Math.max(0.1, calculatedZoom)));
        }
      } catch {
        if (!cancelled) {
          setError("Unable to calculate the PDF page dimensions.");
        }
      }
    };

    void calculateFit();

    const observer = new ResizeObserver(() => {
      void calculateFit();
    });

    if (viewerRef.current) {
      observer.observe(viewerRef.current);
    }

    return () => {
      cancelled = true;
      observer.disconnect();
    };
  }, [pdfDocument, currentPage, fitMode]);

  const zoomIn = () => {
    setFitMode(null);
    setZoom((current) => Math.min(Number((current + 0.1).toFixed(2)), 3));
  };

  const zoomOut = () => {
    setFitMode(null);
    setZoom((current) => Math.max(Number((current - 0.1).toFixed(2)), 0.5));
  };

  const resetZoom = () => {
    setFitMode(null);
    setZoom(1);
  };

  const fitToWidth = () => {
    setFitMode("width");
  };

  const fitToPage = () => {
    setFitMode("page");
  };

  const toggleFullscreen = async () => {
    try {
      if (!readerContainerRef.current) return;

      if (!document.fullscreenElement) {
        await readerContainerRef.current.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch {
      setError("Unable to change fullscreen mode.");
    }
  };

  const changePage = (page: number) => {
    if (page < 1 || page > totalPages) return;

    setCurrentPage(page);
  };

  const handlePDFLoadSuccess = (pdf: PDFDocumentProxy) => {
    setPdfDocument(pdf);
    setTotalPages(pdf.numPages);
    setCurrentPage(1);
    setError("");
  };

  const handlePDFLoadError = () => {
    setError(
      "Unable to render this PDF. The file may be damaged or unsupported.",
    );
  };

  const goToLibrary = () => {
    navigate("/library");
  };

  return (
    <div
      ref={readerContainerRef}
      className="flex min-h-[calc(100vh-120px)] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white"
    >
      {/* READER HEADER */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-5 py-4">
        <div className="flex min-w-0 items-center gap-3">
          <button
            onClick={goToLibrary}
            className="rounded-lg border border-slate-200 p-2 text-slate-600 hover:bg-slate-100"
            title="Back to Library"
          >
            <ArrowLeft size={19} />
          </button>

          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-violet-100 text-violet-600">
            <BookOpen size={20} />
          </div>

          <div className="min-w-0">
            <h1 className="truncate text-base font-semibold text-slate-900">
              {documentTitle}
            </h1>

            <p className="text-xs text-slate-500">FLIPBOOK-AI PDF Reader</p>
          </div>
        </div>

        {totalPages > 0 && (
          <div className="rounded-lg bg-violet-50 px-3 py-2 text-xs font-medium text-violet-700">
            {totalPages} pages
          </div>
        )}
      </div>

      {/* PDF TOOLBAR */}
      <PDFToolbar
        zoom={zoom}
        isFullscreen={isFullscreen}
        onZoomIn={zoomIn}
        onZoomOut={zoomOut}
        onResetZoom={resetZoom}
        onToggleFullscreen={toggleFullscreen}
        onFitWidth={fitToWidth}
        onFitPage={fitToPage}
      />

      {/* PDF VIEWER */}
      <div className="relative flex min-h-[600px] flex-1 overflow-hidden bg-slate-100">
        {loading && (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 p-10">
            <Loader2 size={32} className="animate-spin text-violet-600" />
            <p className="text-sm font-medium text-slate-600">
              Loading your PDF...
            </p>
          </div>
        )}

        {!loading && error && (
          <div className="flex flex-1 flex-col items-center justify-center p-8 text-center">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-red-50 text-red-500">
              <AlertCircle size={28} />
            </div>

            <h2 className="font-semibold text-slate-900">Unable to open PDF</h2>

            <p className="mt-2 max-w-md text-sm text-slate-500">{error}</p>

            <button
              onClick={() => void loadPDF()}
              className="mt-5 flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-violet-700"
            >
              <RefreshCw size={16} />
              Try again
            </button>
          </div>
        )}

        {!loading && !error && pdfUrl && (
          <>
            {totalPages > 0 && (
              <PDFThumbnailSidebar
                pdfUrl={pdfUrl}
                totalPages={totalPages}
                currentPage={currentPage}
                onPageChange={changePage}
              />
            )}

            <div
              ref={viewerRef}
              className="flex min-w-0 flex-1 justify-center overflow-auto p-4 sm:p-8"
            >
              <PDFDocument
                file={pdfUrl}
                onLoadSuccess={handlePDFLoadSuccess}
                onLoadError={handlePDFLoadError}
                loading={
                  <div className="flex items-center gap-2 p-10 text-sm text-slate-500">
                    <Loader2 size={18} className="animate-spin" />
                    Preparing PDF pages...
                  </div>
                }
                error={
                  <div className="p-10 text-sm text-red-500">
                    PDF rendering failed.
                  </div>
                }
              >
                <PDFPage pageNumber={currentPage} scale={zoom} />
              </PDFDocument>
            </div>
          </>
        )}
      </div>

      {/* PAGE NAVIGATION */}
      {!loading && !error && totalPages > 0 && (
        <PageNavigation
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={changePage}
        />
      )}
    </div>
  );
}
