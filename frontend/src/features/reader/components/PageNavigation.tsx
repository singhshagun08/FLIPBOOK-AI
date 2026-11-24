import { ChevronLeft, ChevronRight } from "lucide-react";

interface PageNavigationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function PageNavigation({
  currentPage,
  totalPages,
  onPageChange,
}: PageNavigationProps) {
  return (
    <div className="flex items-center justify-center gap-4 border-t border-slate-200 bg-white px-4 py-3">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage <= 1}
        className="rounded-lg border border-slate-200 p-2 hover:bg-slate-100 disabled:opacity-40"
        title="Previous page"
      >
        <ChevronLeft size={18} />
      </button>

      <div className="flex items-center gap-2 text-sm text-slate-700">
        <input
          type="number"
          min={1}
          max={totalPages}
          value={currentPage}
          onChange={(event) => {
            const page = Number(event.target.value);

            if (Number.isInteger(page) && page >= 1 && page <= totalPages) {
              onPageChange(page);
            }
          }}
          className="w-16 rounded-lg border border-slate-200 px-2 py-1.5 text-center"
        />

        <span>of {totalPages}</span>
      </div>

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage >= totalPages}
        className="rounded-lg border border-slate-200 p-2 hover:bg-slate-100 disabled:opacity-40"
        title="Next page"
      >
        <ChevronRight size={18} />
      </button>
    </div>
  );
}
