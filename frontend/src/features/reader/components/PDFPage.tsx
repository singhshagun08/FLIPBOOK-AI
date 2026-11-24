import { Page } from "react-pdf";

interface PDFPageProps {
  pageNumber: number;
  scale: number;
}

export default function PDFPage({ pageNumber, scale }: PDFPageProps) {
  return (
    <div className="flex justify-center py-5">
      <Page
        pageNumber={pageNumber}
        scale={scale}
        renderTextLayer
        renderAnnotationLayer
        loading={
          <div className="p-10 text-sm text-slate-500">
            Rendering PDF page...
          </div>
        }
        error={
          <div className="p-10 text-sm text-red-500">
            Unable to render this PDF page.
          </div>
        }
      />
    </div>
  );
}
