import {
  ZoomIn,
  ZoomOut,
  Maximize,
  Minimize,
  RotateCcw,
  Maximize2,
  RectangleHorizontal,
} from "lucide-react";

interface PDFToolbarProps {
  zoom: number;
  isFullscreen: boolean;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetZoom: () => void;
  onToggleFullscreen: () => void;
  onFitWidth: () => void;
  onFitPage: () => void;
}

export default function PDFToolbar({
  zoom,
  isFullscreen,
  onZoomIn,
  onZoomOut,
  onResetZoom,
  onToggleFullscreen,
  onFitWidth,
  onFitPage,
}: PDFToolbarProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 py-3">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onZoomOut}
          disabled={zoom <= 0.5}
          title="Zoom out"
          className="rounded-lg border border-slate-200 p-2 hover:bg-slate-100 disabled:opacity-40"
        >
          <ZoomOut size={18} />
        </button>

        <span className="min-w-14 text-center text-sm font-medium text-slate-700">
          {Math.round(zoom * 100)}%
        </span>

        <button
          type="button"
          onClick={onZoomIn}
          disabled={zoom >= 3}
          title="Zoom in"
          className="rounded-lg border border-slate-200 p-2 hover:bg-slate-100 disabled:opacity-40"
        >
          <ZoomIn size={18} />
        </button>

        <button
          type="button"
          onClick={onResetZoom}
          title="Reset zoom"
          className="rounded-lg border border-slate-200 p-2 hover:bg-slate-100"
        >
          <RotateCcw size={17} />
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={onFitWidth}
          title="Fit PDF to width"
          className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium hover:bg-violet-50"
        >
          <RectangleHorizontal size={16} />
          Fit Width
        </button>

        <button
          type="button"
          onClick={onFitPage}
          title="Fit entire page"
          className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium hover:bg-violet-50"
        >
          <Maximize2 size={16} />
          Fit Page
        </button>

        <button
          type="button"
          onClick={onToggleFullscreen}
          title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
          className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm hover:bg-slate-100"
        >
          {isFullscreen ? <Minimize size={17} /> : <Maximize size={17} />}
          {isFullscreen ? "Exit fullscreen" : "Fullscreen"}
        </button>
      </div>
    </div>
  );
}
