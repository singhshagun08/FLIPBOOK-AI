import { useState } from "react";
import { Document, Page } from "react-pdf";
import { ChevronLeft, ChevronRight, LoaderCircle } from "lucide-react";

interface PDFThumbnailSidebarProps {
  pdfUrl: string;
  totalPages: number;
  currentPage: number;
  onPageChange: (page: number) => void;
}

export default function PDFThumbnailSidebar({
  pdfUrl,
  totalPages,
  currentPage,
  onPageChange,
}: PDFThumbnailSidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <aside
      className={`relative flex shrink-0 flex-col border-r border-slate-200 bg-white transition-all duration-300 ${
        isCollapsed ? "w-12" : "w-56"
      }`}
    >
      <div className="flex items-center justify-between border-b border-slate-200 p-3">
        {!isCollapsed && (
          <h3 className="text-sm font-semibold text-slate-800">
            Pages ({totalPages})
          </h3>
        )}

        <button
          type="button"
          onClick={() => setIsCollapsed((current) => !current)}
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
          title={isCollapsed ? "Expand thumbnails" : "Collapse thumbnails"}
        >
          {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      {!isCollapsed && (
        <div className="flex-1 overflow-y-auto p-3">
          <Document
            file={pdfUrl}
            loading={
              <div className="flex justify-center py-6">
                <LoaderCircle
                  size={22}
                  className="animate-spin text-violet-600"
                />
              </div>
            }
          >
            <div className="space-y-4">
              {Array.from({ length: totalPages }, (_, index) => {
                const pageNumber = index + 1;
                const isActive = currentPage === pageNumber;

                return (
                  <button
                    key={pageNumber}
                    type="button"
                    onClick={() => onPageChange(pageNumber)}
                    className={`w-full rounded-xl border p-2 transition ${
                      isActive
                        ? "border-violet-500 bg-violet-50 ring-2 ring-violet-100"
                        : "border-slate-200 hover:border-violet-300"
                    }`}
                  >
                    <div className="flex justify-center overflow-hidden rounded-md bg-slate-100">
                      <Page
                        pageNumber={pageNumber}
                        width={155}
                        renderTextLayer={false}
                        renderAnnotationLayer={false}
                        loading={
                          <div className="flex h-36 items-center justify-center">
                            <LoaderCircle
                              size={18}
                              className="animate-spin text-slate-400"
                            />
                          </div>
                        }
                      />
                    </div>

                    <p
                      className={`mt-2 text-center text-xs font-medium ${
                        isActive ? "text-violet-700" : "text-slate-500"
                      }`}
                    >
                      Page {pageNumber}
                    </p>
                  </button>
                );
              })}
            </div>
          </Document>
        </div>
      )}

      {isCollapsed && (
        <div className="flex flex-1 flex-col items-center gap-3 pt-4">
          <span className="text-xs font-semibold text-slate-500 [writing-mode:vertical-rl]">
            PAGE THUMBNAILS
          </span>
        </div>
      )}
    </aside>
  );
}
